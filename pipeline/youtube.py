"""YouTube OAuth and destination preflight utilities."""
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

class YouTubeError(RuntimeError):
    pass

def request_json(url, data=None, headers=None):
    request = Request(url, data=data, headers=headers or {})
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read(1_000_000))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise YouTubeError("YouTube API request failed") from exc

def refresh_access_token(client_id, client_secret, refresh_token):
    body = urlencode({"client_id": client_id, "client_secret": client_secret, "refresh_token": refresh_token, "grant_type": "refresh_token"}).encode()
    payload = request_json("https://oauth2.googleapis.com/token", body, {"Content-Type": "application/x-www-form-urlencoded"})
    token = payload.get("access_token")
    if not token:
        raise YouTubeError("OAuth refresh did not return an access token")
    return token

def preflight(client_id, client_secret, refresh_token, playlist_id):
    token = refresh_access_token(client_id, client_secret, refresh_token)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    channel = request_json("https://www.googleapis.com/youtube/v3/channels?part=id,snippet&mine=true", headers=headers)
    playlist = request_json("https://www.googleapis.com/youtube/v3/playlists?" + urlencode({"part": "snippet,status", "id": playlist_id}), headers=headers)
    channels, playlists = channel.get("items", []), playlist.get("items", [])
    if len(channels) != 1:
        raise YouTubeError("OAuth account has no unique YouTube channel")
    if len(playlists) != 1:
        raise YouTubeError("Configured playlist is unavailable to OAuth account")
    channel_id = channels[0]["id"]
    if playlists[0].get("snippet", {}).get("channelId") != channel_id:
        raise YouTubeError("Configured playlist belongs to a different channel")
    return {"channel_id": channel_id, "channel_title": channels[0].get("snippet", {}).get("title", ""), "playlist_id": playlists[0]["id"], "playlist_title": playlists[0].get("snippet", {}).get("title", ""), "playlist_privacy": playlists[0].get("status", {}).get("privacyStatus", "unknown")}

def main():
    names = ["YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN", "YOUTUBE_PLAYLIST_ID"]
    values = [os.environ.get(name, "") for name in names]
    if not all(values):
        raise YouTubeError("Required YouTube OAuth configuration is missing")
    print(json.dumps(preflight(*values), indent=2))

if __name__ == "__main__": raise SystemExit(main())
