"""Fast, non-publishing end-to-end smoke test for the FFmpeg renderer."""
import argparse
import math
from pathlib import Path
import struct
import wave

from . import media


def _synthetic_wav(_episode, output, _voice, _speed):
    sample_rate, duration = 24_000, 5.0
    cues = [
        media.Cue(0.0, 1.5, "Security media smoke test"),
        media.Cue(1.5, 3.5, "Database security CVE-2026-12345"),
        media.Cue(3.5, 5.0, "Smoke test complete"),
    ]
    with wave.open(str(output), "wb") as target:
        target.setparams((1, 2, sample_rate, 0, "NONE", "not compressed"))
        frames = (struct.pack("<h", round(5500 * math.sin(2 * math.pi * 220 * index / sample_rate))) for index in range(round(sample_rate * duration)))
        target.writeframes(b"".join(frames))
    return cues, duration


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("smoke-media"))
    args = parser.parse_args()
    episode = {
        "title": "Security media smoke test",
        "summary": "Synthetic renderer validation.",
        "segments": [{"heading": "Database security CVE-2026-12345", "narration": "Synthetic content.", "source_urls": ["https://example.org/smoke"]}],
        "outro": "Smoke test complete",
        "status": "approved",
    }
    original = media.synthesize_wav
    try:
        media.synthesize_wav = _synthetic_wav
        media.render_media(episode, args.output)
    finally:
        media.synthesize_wav = original


if __name__ == "__main__":
    raise SystemExit(main())
