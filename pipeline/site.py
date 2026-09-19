"""Accessible static article and archive rendering."""
from html import escape
import json
from pathlib import Path

def render(episode, edition):
    sections = []
    for segment in episode.get("segments", []):
        links = "".join(f'<li><a href="{escape(url, quote=True)}" rel="noopener noreferrer">{escape(url)}</a></li>' for url in segment["source_urls"])
        sections.append(f'<section><h2>{escape(segment["heading"])}</h2><p>{escape(segment["narration"])}</p><h3>Sources</h3><ul>{links}</ul></section>')
    title = escape(episode["title"])
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><link rel="stylesheet" href="../../assets/site.css"></head><body><main><a href="../../">? Archive</a><article><h1>{title}</h1><time datetime="{escape(edition)}">{escape(edition)}</time><p>{escape(episode["summary"])}</p>{"".join(sections)}<p>{escape(episode["outro"])}</p></article></main></body></html>'

def build_site(output: Path, episode_path: Path, edition: str):
    episode = json.loads(episode_path.read_text(encoding="utf-8"))
    if episode.get("status") not in {"approved", "no_news"}:
        raise ValueError("Only approved content may be rendered")
    page = output / "episodes" / edition / "index.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(render(episode, edition), encoding="utf-8")
    assets = output / "assets"; assets.mkdir(parents=True, exist_ok=True)
    (assets / "site.css").write_text("body{font:18px/1.6 system-ui,sans-serif;margin:0;color:#172033;background:#f6f8fb}main{max-width:800px;margin:auto;padding:2rem}article{background:white;padding:clamp(1rem,4vw,3rem);border-radius:12px}a{color:#075fc4}h1,h2{line-height:1.2}", encoding="utf-8")
    dates = sorted((item.parent.name for item in (output / "episodes").glob("*/index.html")), reverse=True)
    links = "".join(f'<li><a href="episodes/{escape(date)}/">{escape(date)}</a></li>' for date in dates)
    (output / "index.html").write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>IS Security Update</title><link rel="stylesheet" href="assets/site.css"></head><body><main><h1>IS Security Update</h1><p>Daily database-security briefings.</p><ol>{links}</ol></main></body></html>', encoding="utf-8")
