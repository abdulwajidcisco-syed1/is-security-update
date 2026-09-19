"""Reconciled YouTube upload and playlist publisher."""
import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .run import write_json
from .youtube import YouTubeError, refresh_access_token


API = "https://www.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3/videos"


def edition_marker(edition):
    return f"IS-SECURITY-UPDATE-EDITION:{edition}"


def video_metadata(episode, edition, privacy="private"):
    if privacy not in {"private", "unlisted", "public"}:
        raise YouTubeError("Unsupported YouTube privacy setting")
    urls = []
    for segment in episode.get("segments", []):
        for url in segment.get("source_urls", []):
            if url not in urls:
                urls.append(url)
    disclosure = "This briefing uses AI-assisted research and synthetic narration. Verify operational decisions against the cited primary sources."
    description = "\n\n".join((episode.get("summary", ""), disclosure, "Sources:\n" + "\n".join(urls), edition_marker(edition))).strip()
    return {"snippet": {"title": episode["title"][:100], "description": description[:5000], "categoryId": "28", "defaultLanguage": "en"}, "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}}


class YouTubeAPI:
    def __init__(self, token):
        self.token = token

    def request(self, method, url, body=None, content_type="application/json", return_headers=False):
        data = json.dumps(body).encode() if isinstance(body, dict) else body
        request = Request(url, data=data, method=method, headers={"Authorization": "Bearer " + self.token, "Accept": "application/json", "Content-Type": content_type, "User-Agent": "is-security-update/0.1"})
        try:
            with urlopen(request, timeout=900) as response:
                content = response.read(50_000_000)
                value = json.loads(content) if content else {}
                return (value, response.headers) if return_headers else value
        except HTTPError as exc:
            raise YouTubeError(f"YouTube API request failed with HTTP {exc.code}") from exc
        except OSError as exc:
            raise YouTubeError("YouTube API request failed with an uncertain outcome") from exc


def find_existing(api, edition):
    query = urlencode({"part": "snippet", "forMine": "true", "type": "video", "q": edition, "maxResults": 25})
    search = api.request("GET", API + "/search?" + query)
    ids = [row.get("id", {}).get("videoId") for row in search.get("items", [])]
    ids = [value for value in ids if value]
    if not ids:
        return None
    details = api.request("GET", API + "/videos?" + urlencode({"part": "snippet,status", "id": ",".join(ids)}))
    matches = [row for row in details.get("items", []) if edition_marker(edition) in row.get("snippet", {}).get("description", "")]
    if len(matches) > 1:
        raise YouTubeError("Multiple videos contain the same edition marker")
    return matches[0] if matches else None


def upload_video(api, video, metadata):
    query = urlencode({"uploadType": "resumable", "part": "snippet,status", "notifySubscribers": "false"})
    _, headers = api.request("POST", UPLOAD + "?" + query, metadata, return_headers=True)
    location = headers.get("Location")
    if not location:
        raise YouTubeError("YouTube did not return a resumable upload URL")
    return api.request("PUT", location, Path(video).read_bytes(), "video/mp4")


def ensure_playlist(api, playlist_id, video_id):
    query = urlencode({"part": "snippet", "playlistId": playlist_id, "videoId": video_id, "maxResults": 1})
    existing = api.request("GET", API + "/playlistItems?" + query)
    if existing.get("items"):
        return "reused"
    api.request("POST", API + "/playlistItems?part=snippet", {"snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}})
    return "inserted"


def publish(directory, client_id, client_secret, refresh_token, playlist_id, privacy="private"):
    directory = Path(directory); episode_path, video = directory / "episode.json", directory / "video.mp4"
    if not episode_path.is_file() or not video.is_file() or not video.stat().st_size:
        raise YouTubeError("Validated episode and video artifacts are required")
    episode = json.loads(episode_path.read_text(encoding="utf-8")); edition = directory.name
    if episode.get("status") not in {"approved", "no_news"}:
        raise YouTubeError("Only approved content may be uploaded")
    api = YouTubeAPI(refresh_access_token(client_id, client_secret, refresh_token))
    existing = find_existing(api, edition)
    if existing:
        video_id, upload_state = existing["id"], "reconciled"
    else:
        result = upload_video(api, video, video_metadata(episode, edition, privacy))
        video_id, upload_state = result.get("id"), "uploaded"
        if not video_id:
            raise YouTubeError("YouTube upload response omitted the video ID")
    playlist_state = ensure_playlist(api, playlist_id, video_id)
    verified = api.request("GET", API + "/videos?" + urlencode({"part": "snippet,status,processingDetails", "id": video_id}))
    if len(verified.get("items", [])) != 1:
        raise YouTubeError("Uploaded video could not be verified")
    item = verified["items"][0]
    state = {"schema_version": 1, "edition": edition, "video_id": video_id, "video_url": "https://youtu.be/" + video_id, "upload_state": upload_state, "playlist_state": playlist_state, "privacy": item.get("status", {}).get("privacyStatus"), "processing_status": item.get("processingDetails", {}).get("processingStatus", "unknown"), "status": "published"}
    write_json(directory / "youtube.json", state)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--privacy", default="private", choices=("private", "unlisted", "public"))
    args = parser.parse_args()
    names = ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN", "YOUTUBE_PLAYLIST_ID")
    values = [os.environ.get(name, "") for name in names]
    if not all(values):
        raise YouTubeError("Required YouTube configuration is missing")
    print(json.dumps(publish(args.directory, *values, privacy=args.privacy)))


if __name__ == "__main__":
    raise SystemExit(main())
