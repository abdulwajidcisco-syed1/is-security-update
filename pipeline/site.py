"""Accessible static article, archive rendering, and bounded archive preservation."""
import argparse
from html import escape
import json
from pathlib import Path
import re
import shutil
from urllib.error import HTTPError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

STYLE = """body{font:18px/1.6 system-ui,sans-serif;margin:0;color:#172033;background:#f6f8fb}main{max-width:900px;margin:auto;padding:2rem}article{background:white;padding:clamp(1rem,4vw,3rem);border-radius:12px}a{color:#075fc4}h1,h2{line-height:1.2}.media{width:100%;margin:1rem 0}.video{aspect-ratio:16/9;border:0}.notice{padding:1rem;background:#eaf2ff;border-left:4px solid #075fc4}time{color:#526176}"""
EDITION_LINK = re.compile(r'href=["\']episodes/(\d{4}-\d{2}-\d{2})/["\']')


def render(episode, edition, audio_url=None, video_url=None, youtube_url=None):
    sections = []
    for segment in episode.get("segments", []):
        links = "".join(f'<li><a href="{escape(url, quote=True)}" rel="noopener noreferrer">{escape(url)}</a></li>' for url in segment["source_urls"])
        sections.append(f'<section><h2>{escape(segment["heading"])}</h2><p>{escape(segment["narration"])}</p><h3>Sources</h3><ul>{links}</ul></section>')
    media = []
    if audio_url:
        safe = escape(audio_url, quote=True); media.append(f'<h2>Listen</h2><audio class="media" controls preload="metadata" src="{safe}">Download the <a href="{safe}">MP3 briefing</a>.</audio>')
    if youtube_url:
        media.append(f'<h2>Watch</h2><iframe class="media video" src="{escape(youtube_url, quote=True)}" title="IS Security Update video" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>')
    elif video_url:
        safe = escape(video_url, quote=True); media.append(f'<h2>Watch</h2><video class="media" controls preload="metadata" src="{safe}">Download the <a href="{safe}">MP4 briefing</a>.</video>')
    title = escape(episode["title"])
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><link rel="stylesheet" href="../../assets/site.css"></head><body><main><a href="../../">← Archive</a><article><h1>{title}</h1><time datetime="{escape(edition)}">{escape(edition)}</time><p>{escape(episode["summary"])}</p><p class="notice">This briefing uses AI-assisted research and synthetic narration. Verify operational decisions against the cited primary sources.</p>{"".join(media)}{"".join(sections)}<p>{escape(episode["outro"])}</p></article></main></body></html>'


def build_site(output: Path, episode_path: Path, edition: str, media_source: Path = None, youtube_id: str = None):
    episode = json.loads(episode_path.read_text(encoding="utf-8"))
    if episode.get("status") not in {"approved", "no_news"}:
        raise ValueError("Only approved content may be rendered")
    audio_url = video_url = None
    if media_source:
        destination = output / "media" / edition; destination.mkdir(parents=True, exist_ok=True)
        for name in ("audio.mp3", "video.mp4", "captions.srt"):
            source = Path(media_source) / name
            if not source.is_file() or not source.stat().st_size:
                raise ValueError(f"Required site media is missing: {name}")
            shutil.copy2(source, destination / name)
        audio_url, video_url = f"../../media/{edition}/audio.mp3", f"../../media/{edition}/video.mp4"
    youtube_url = f"https://www.youtube-nocookie.com/embed/{youtube_id}" if youtube_id else None
    page = output / "episodes" / edition / "index.html"; page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(render(episode, edition, audio_url, video_url, youtube_url), encoding="utf-8")
    assets = output / "assets"; assets.mkdir(parents=True, exist_ok=True); (assets / "site.css").write_text(STYLE, encoding="utf-8")
    dates = sorted((item.parent.name for item in (output / "episodes").glob("*/index.html")), reverse=True)
    links = "".join(f'<li><a href="episodes/{escape(date)}/">{escape(date)}</a></li>' for date in dates)
    (output / "index.html").write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>IS Security Update</title><link rel="stylesheet" href="assets/site.css"></head><body><main><h1>IS Security Update</h1><p>Daily database-security briefings with cited public sources.</p><ol>{links}</ol></main></body></html>', encoding="utf-8")
    (output / ".nojekyll").write_text("", encoding="utf-8")


def _fetch(url, maximum, missing_ok=False):
    request = Request(url, headers={"User-Agent": "is-security-update/0.1"})
    try:
        with urlopen(request, timeout=60) as response:
            data = response.read(maximum + 1)
    except HTTPError as exc:
        if missing_ok and exc.code == 404:
            return None
        raise
    if len(data) > maximum:
        raise ValueError("Existing site asset exceeds retention limit")
    return data


def sync_existing_site(base_url, output: Path, keep=30):
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Existing site URL must be a public HTTPS base URL")
    base = base_url.rstrip("/") + "/"
    index = _fetch(base, 5_000_000, missing_ok=True)
    if index is None:
        return []
    dates = sorted(set(EDITION_LINK.findall(index.decode("utf-8"))), reverse=True)[:keep]
    for edition in dates:
        page = _fetch(urljoin(base, f"episodes/{edition}/"), 5_000_000)
        destination = output / "episodes" / edition / "index.html"; destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(page)
        for name, maximum in (("audio.mp3", 50_000_000), ("video.mp4", 250_000_000), ("captions.srt", 2_000_000)):
            content = _fetch(urljoin(base, f"media/{edition}/{name}"), maximum, missing_ok=True)
            if content is not None:
                target = output / "media" / edition / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(content)
    return dates


def main():
    parser = argparse.ArgumentParser(description="Build a site from a validated edition checkpoint.")
    parser.add_argument("directory", type=Path)
    parser.add_argument("--existing-site-url")
    parser.add_argument("--retained-editions", type=int, default=30)
    args = parser.parse_args()
    if not 1 <= args.retained_editions <= 90:
        raise ValueError("Retained editions must be between 1 and 90")
    directory = args.directory
    output = directory / "site"
    if args.existing_site_url:
        sync_existing_site(args.existing_site_url, output, args.retained_editions)
    youtube_path = directory / "youtube.json"
    youtube_id = None
    if youtube_path.is_file():
        state = json.loads(youtube_path.read_text(encoding="utf-8"))
        if state.get("edition") != directory.name or state.get("status") != "published":
            raise ValueError("YouTube publication record is invalid")
        youtube_id = state.get("video_id")
    build_site(output, directory / "episode.json", directory.name, media_source=directory, youtube_id=youtube_id)
    print(json.dumps({"status": "site_built", "edition": directory.name, "youtube_embedded": bool(youtube_id)}))


if __name__ == "__main__":
    raise SystemExit(main())
