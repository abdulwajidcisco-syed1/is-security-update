"""Generate reviewable live-source artifacts without publishing them."""
import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

from .collect import collect_all
from .config import load_settings
from .editorial import generate_episode
from .run import write_json
from .selection import select_items, timestamp
from .site import build_site

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window-end", help="Timezone-aware ISO timestamp; defaults to current UTC time")
    parser.add_argument("--output", type=Path, default=Path("preview"))
    parser.add_argument("--show", type=Path, default=Path("config/show.yaml"))
    parser.add_argument("--sources", type=Path, default=Path("config/sources.live.yaml"))
    parser.add_argument("--model", default="openai/gpt-oss-20b")
    args = parser.parse_args()
    end = timestamp(args.window_end) if args.window_end else datetime.now(timezone.utc).replace(microsecond=0)
    start, edition = end - timedelta(hours=24), end.date().isoformat()
    settings = load_settings(args.show, args.sources)
    records, outcomes = collect_all(settings, start, end)
    selected, quarantine = select_items(records, settings, end)
    if not selected and quarantine:
        raise RuntimeError("All potentially relevant items were rejected")
    episode = generate_episode(selected, args.model, edition)
    directory = args.output / edition; directory.mkdir(parents=True, exist_ok=True)
    paths = {"selected.json": selected, "quarantine.json": quarantine, "episode.json": episode}
    for name, data in paths.items(): write_json(directory / name, data)
    transcript = [f'# {episode["title"]}', "", episode["summary"], ""]
    for segment in episode["segments"]:
        transcript += [f'## {segment["heading"]}', "", segment["narration"], "", "Sources:"] + [f'- {url}' for url in segment["source_urls"]] + [""]
    transcript += [episode["outro"], ""]
    (directory / "transcript.md").write_text("\n".join(transcript), encoding="utf-8")
    build_site(directory / "site", directory / "episode.json", edition)
    manifest = {"schema_version": 1, "mode": "live_preview", "publication": "disabled", "edition": edition, "window_start": start.isoformat(), "window_end": end.isoformat(), "source_outcomes": outcomes, "raw_count": len(records), "selected_count": len(selected), "quarantined_count": len(quarantine), "episode_status": episode["status"], "artifacts": {}}
    for path in directory.rglob("*"):
        if path.is_file() and path.name != "manifest.json": manifest["artifacts"][str(path.relative_to(directory)).replace("\\", "/")] = sha256(path.read_bytes()).hexdigest()
    write_json(directory / "manifest.json", manifest)
    print(json.dumps({"status": "preview_complete", "edition": edition, "selected": len(selected), "publication": "disabled"}))

if __name__ == "__main__": raise SystemExit(main())
