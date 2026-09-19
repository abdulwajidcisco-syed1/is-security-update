"""Obtain a YouTube refresh token locally and save it directly to GitHub Secrets."""
import argparse
import base64
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import secrets
import subprocess
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, urlopen
import webbrowser

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube"

class OAuthError(RuntimeError):
    pass

class Callback(BaseHTTPRequestHandler):
    result = None
    expected_state = None
    def do_GET(self):
        query = parse_qs(urlsplit(self.path).query)
        if query.get("state", [None])[0] != self.expected_state:
            self.send_response(400); self.end_headers(); self.wfile.write(b"State validation failed.")
            self.server.callback_error = "state_mismatch"; return
        if "error" in query:
            self.send_response(400); self.end_headers(); self.wfile.write(b"Authorization was not granted.")
            self.server.callback_error = query["error"][0]; return
        self.server.authorization_code = query.get("code", [None])[0]
        self.send_response(200); self.send_header("Content-Type", "text/plain; charset=utf-8"); self.end_headers()
        self.wfile.write(b"Authorization received. You can close this browser tab.")
    def log_message(self, *_):
        return

def exchange(client_id, client_secret, code, verifier, redirect_uri):
    body = urlencode({"client_id": client_id, "client_secret": client_secret, "code": code, "code_verifier": verifier, "grant_type": "authorization_code", "redirect_uri": redirect_uri}).encode()
    request = Request(TOKEN_URL, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urlopen(request, timeout=60) as response:
            payload = json.loads(response.read(1_000_000))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise OAuthError("Token exchange failed") from exc
    token = payload.get("refresh_token")
    if not token:
        raise OAuthError("Google did not return a refresh token; revoke prior consent and retry")
    return token

def save_secret(gh_path, repository, refresh_token):
    process = subprocess.run([gh_path, "secret", "set", "YOUTUBE_REFRESH_TOKEN", "--repo", repository], input=refresh_token, text=True, capture_output=True)
    if process.returncode:
        raise OAuthError("Could not save refresh token to GitHub Secrets")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="abdulwajidcisco-syed1/is-security-update")
    parser.add_argument("--gh", default="gh")
    parser.add_argument("--client-id", default=os.environ.get("YOUTUBE_CLIENT_ID"))
    parser.add_argument("--client-secret", default=os.environ.get("YOUTUBE_CLIENT_SECRET"))
    args = parser.parse_args()
    if not args.client_id or not args.client_secret:
        raise OAuthError("Client ID and client secret are required through arguments or environment")
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).decode().rstrip("=")
    challenge = base64.urlsafe_b64encode(sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = secrets.token_urlsafe(32)
    server = HTTPServer(("127.0.0.1", 0), Callback)
    server.authorization_code = None; server.callback_error = None
    Callback.expected_state = state
    redirect_uri = f"http://127.0.0.1:{server.server_port}/"
    query = urlencode({"client_id": args.client_id, "redirect_uri": redirect_uri, "response_type": "code", "scope": SCOPES, "access_type": "offline", "prompt": "consent", "state": state, "code_challenge": challenge, "code_challenge_method": "S256"})
    webbrowser.open(AUTH_URL + "?" + query)
    server.timeout = 300
    server.handle_request()
    server.server_close()
    if server.callback_error or not server.authorization_code:
        raise OAuthError("Authorization was not completed")
    token = exchange(args.client_id, args.client_secret, server.authorization_code, verifier, redirect_uri)
    try:
        save_secret(args.gh, args.repo, token)
    finally:
        token = None
    print("YOUTUBE_REFRESH_TOKEN saved to GitHub Secrets. The token was not printed or written to disk.")

if __name__ == "__main__": raise SystemExit(main())
