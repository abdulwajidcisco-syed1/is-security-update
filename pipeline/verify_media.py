"""Verify that approved text, captions, media duration, and artifact hashes agree."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from .media import caption_chunks, narration_sections

class VerificationError(RuntimeError):
    pass

def _srt_text(path):
    text = path.read_text(encoding="utf-8").replace(chr(13), "")
    return [" ".join(block.splitlines()[2:]) for block in text.strip().split(chr(10) * 2) if len(block.splitlines()) >= 3]

def verify(directory, minimum_seconds=0, maximum_seconds=0):
    directory = Path(directory)
    episode = json.loads((directory / "episode.json").read_text(encoding="utf-8"))
    media = json.loads((directory / "media.json").read_text(encoding="utf-8"))
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    expected = [chunk for section in narration_sections(episode) for chunk in caption_chunks(section)]
    actual = _srt_text(directory / "captions.srt")
    if actual != expected:
        raise VerificationError("Subtitle text does not exactly match the approved spoken chunks")
    duration = float(media.get("duration_seconds", 0))
    if minimum_seconds and duration < minimum_seconds:
        raise VerificationError(f"Media is shorter than {minimum_seconds} seconds")
    if maximum_seconds and duration > maximum_seconds:
        raise VerificationError(f"Media is longer than {maximum_seconds} seconds")
    for name, record in media.get("artifacts", {}).items():
        path = directory / name
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != record.get("sha256"):
            raise VerificationError(f"Media artifact hash mismatch: {name}")
    for name, expected_hash in manifest.get("artifacts", {}).items():
        path = directory / name
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != expected_hash:
            raise VerificationError(f"Manifest artifact hash mismatch: {name}")
    result = {"status": "verified", "word_count": episode.get("word_count"), "duration_seconds": duration, "caption_count": len(actual), "artifact_count": len(manifest.get("artifacts", {}))}
    (directory / "verification.json").write_text(json.dumps(result, indent=2) + chr(10), encoding="utf-8")
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--minimum-seconds", type=int, default=0)
    parser.add_argument("--maximum-seconds", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(verify(args.directory, args.minimum_seconds, args.maximum_seconds)))

if __name__ == "__main__":
    raise SystemExit(main())