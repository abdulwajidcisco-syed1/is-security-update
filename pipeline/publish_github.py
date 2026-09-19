"""Resumable, checksum-aware GitHub Release publisher."""
import argparse
from hashlib import sha256
import json
import mimetypes
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .run import write_json


class PublishError(RuntimeError):
    pass


REQUIRED_ASSETS = ("audio.mp3", "video.mp4", "transcript.md", "captions.srt", "episode.json", "media.json", "manifest.json")
EDITION = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def local_assets(directory):
    directory = Path(directory)
    if not EDITION.fullmatch(directory.name):
        raise PublishError("Edition directory must be named YYYY-MM-DD")
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        raise PublishError("Manifest is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("edition") != directory.name or manifest.get("publication") != "disabled":
        raise PublishError("Manifest edition or publication guard is invalid")
    result = {}
    for name in REQUIRED_ASSETS:
        path = directory / name
        if not path.is_file() or not path.stat().st_size:
            raise PublishError(f"Required release asset is missing: {name}")
        digest = sha256(path.read_bytes()).hexdigest()
        if name != "manifest.json" and manifest.get("artifacts", {}).get(name) != digest:
            raise PublishError(f"Manifest checksum mismatch: {name}")
        result[name] = {"path": path, "bytes": path.stat().st_size, "sha256": digest}
    return result


def reconcile_assets(local, remote):
    by_name = {asset["name"]: asset for asset in remote}
    upload, reused = [], []
    for name, item in local.items():
        existing = by_name.get(name)
        if not existing:
            upload.append(name); continue
        digest = existing.get("digest")
        if existing.get("size") != item["bytes"] or digest != "sha256:" + item["sha256"]:
            raise PublishError(f"Existing release asset does not match local checksum: {name}")
        reused.append(name)
    return upload, reused


class GitHubAPI:
    def __init__(self, repository, token):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise PublishError("Invalid GitHub repository identifier")
        if not token:
            raise PublishError("GH_TOKEN is required")
        self.repository, self.token = repository, token

    def request(self, method, path, body=None, content_type="application/json", allow_missing=False):
        url = path if path.startswith("https://") else "https://api.github.com" + path
        data = json.dumps(body).encode() if isinstance(body, dict) else body
        request = Request(url, data=data, method=method, headers={"Accept": "application/vnd.github+json", "Authorization": "Bearer " + self.token, "X-GitHub-Api-Version": "2022-11-28", "Content-Type": content_type, "User-Agent": "is-security-update/0.1"})
        try:
            with urlopen(request, timeout=120) as response:
                content = response.read(20_000_000)
                return json.loads(content) if content else {}
        except HTTPError as exc:
            if allow_missing and exc.code == 404:
                return None
            raise PublishError(f"GitHub API request failed with HTTP {exc.code}") from exc


def publish(directory, repository, token):
    directory = Path(directory); local = local_assets(directory)
    api = GitHubAPI(repository, token); tag = "episode-" + directory.name
    release = api.request("GET", f"/repos/{repository}/releases/tags/{quote(tag)}", allow_missing=True)
    if release is None:
        releases = api.request("GET", f"/repos/{repository}/releases?per_page=100")
        release = next((item for item in releases if item.get("tag_name") == tag), None)
    if release is None:
        release = api.request("POST", f"/repos/{repository}/releases", {"tag_name": tag, "name": f"IS Security Update — {directory.name}", "body": "Automated database-security briefing. Narration is generated from cited public sources.", "draft": True, "prerelease": False})
    upload, reused = reconcile_assets(local, release.get("assets", []))
    upload_base = release["upload_url"].split("{")[0]
    uploaded = []
    for name in upload:
        item = local[name]
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        result = api.request("POST", upload_base + "?name=" + quote(name), item["path"].read_bytes(), content_type)
        if result.get("digest") != "sha256:" + item["sha256"]:
            raise PublishError(f"GitHub did not confirm the uploaded checksum: {name}")
        uploaded.append(name)
    release = api.request("PATCH", f"/repos/{repository}/releases/{release['id']}", {"draft": False}) if release.get("draft") else release
    state = {"schema_version": 1, "edition": directory.name, "tag": tag, "release_id": release["id"], "release_url": release["html_url"], "uploaded": uploaded, "reused": reused, "status": "published"}
    write_json(directory / "github-release.json", state)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
    args = parser.parse_args()
    if not args.repository:
        raise PublishError("GITHUB_REPOSITORY is required")
    print(json.dumps(publish(args.directory, args.repository, os.environ.get("GH_TOKEN"))))


if __name__ == "__main__":
    raise SystemExit(main())
