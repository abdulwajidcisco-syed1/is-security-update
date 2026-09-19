"""Generate a synthetic, non-publishing active-day media capacity benchmark."""
import argparse
import json
from pathlib import Path

from .media import render_media
from .run import write_json


def benchmark_episode():
    sentences = (
        "The security team reviews public advisories, confirms each identifier against its cited source, and records uncertainty instead of guessing.",
        "Database owners compare the supported version information with their asset inventory before planning a controlled maintenance window.",
        "Defensive monitoring focuses on unusual privilege changes, unexpected administrative activity, and access patterns that require investigation.",
        "Operators preserve audit evidence, validate backups, test recovery procedures, and communicate changes through the approved operational process.",
        "This synthetic passage measures narration and caption capacity only; it contains no current vulnerability claim or operational instruction.",
    )
    segments = []
    for index in range(12):
        narration = " ".join(sentences * 2)
        segments.append({"heading": f"Synthetic benchmark section {index + 1}", "narration": narration, "claim_ids": [f"benchmark-{index + 1}"], "source_urls": ["https://example.org/synthetic-benchmark"], "is_case_study": False})
    episode = {"title": "Synthetic active-day media benchmark", "summary": "A non-publishing capacity test for narration, captions, and video encoding.", "segments": segments, "outro": "The synthetic media benchmark is complete.", "status": "approved"}
    text = " ".join([episode["title"], episode["summary"], *(segment["narration"] for segment in segments), episode["outro"]])
    episode["word_count"] = len(text.split())
    return episode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("benchmark-media"))
    parser.add_argument("--voice", default="af_heart")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    episode = benchmark_episode()
    if not 1800 <= episode["word_count"] <= 2700:
        raise ValueError("Synthetic benchmark must remain within the active-day word target")
    write_json(args.output / "episode.json", episode)
    metadata = render_media(episode, args.output, voice=args.voice)
    print(json.dumps({"status": "benchmark_complete", "word_count": episode["word_count"], "duration_seconds": metadata["duration_seconds"], "caption_count": metadata["caption_count"]}))


if __name__ == "__main__":
    raise SystemExit(main())
