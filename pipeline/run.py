"""Offline, non-publishing vertical slice with durable checksummed results."""

import argparse
from contextlib import contextmanager
from datetime import timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

from .config import ConfigError, load_settings
from .selection import select_items, timestamp
from . import __version__


class RunError(ValueError):
    pass


def write_json(path: Path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


@contextmanager
def edition_lock(path: Path):
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RunError("Edition is locked; inspect the run before removing a stale lock") from exc
    try:
        os.write(descriptor, str(os.getpid()).encode())
        os.close(descriptor)
        yield
    finally:
        path.unlink(missing_ok=True)


def execute(show: Path, sources: Path, fixture: Path, output: Path, window_end: str, resume=False):
    settings = load_settings(show, sources)
    end = timestamp(window_end)
    edition = end.date().isoformat()
    code_digest = sha256(b"".join(path.read_bytes() for path in sorted(Path(__file__).parent.glob("*.py")))).digest()
    fingerprint = sha256(code_digest + __version__.encode() + show.read_bytes() + sources.read_bytes() + fixture.read_bytes() + end.isoformat().encode()).hexdigest()
    directory = output / settings.show_id / edition
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = directory / "manifest.json"
    with edition_lock(directory / ".lock"):
        if manifest_path.exists():
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not resume:
                raise RunError("Edition already exists; use --resume")
            if previous.get("fingerprint") != fingerprint:
                raise RunError("Resume inputs/window changed; choose a separate output directory")
            if previous.get("status") == "selection_complete":
                if set(previous.get("artifacts", {})) != {"selected_items.json", "quarantine.json"}:
                    raise RunError("Resume manifest has incomplete artifact records")
                for name, expected in previous["artifacts"].items():
                    if name not in {"selected_items.json", "quarantine.json"}:
                        raise RunError("Unexpected manifest artifact")
                    artifact = directory / name
                    if not artifact.is_file() or sha256(artifact.read_bytes()).hexdigest() != expected:
                        raise RunError("Resume artifact checksum mismatch")
                return previous
        manifest = {"schema_version": 1, "pipeline_version": __version__, "edition": edition, "window_start": (end - timedelta(hours=24)).isoformat(), "window_end": end.isoformat(), "fingerprint": fingerprint, "mode": "offline_dry_run", "status": "running", "publication": "disabled", "stages": {"configuration": "succeeded", "collection": "pending", "selection": "pending"}, "artifacts": {}}
        write_json(manifest_path, manifest)
        try:
            payload = json.loads(fixture.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or payload.get("synthetic") is not True:
                raise RunError("Only explicitly synthetic fixture data is accepted")
            outcomes = payload.get("source_outcomes")
            records = payload.get("items")
            enabled = {s.id for s in settings.sources if s.enabled}
            if not isinstance(outcomes, dict) or set(outcomes) != enabled or any(v not in {"succeeded", "failed"} for v in outcomes.values()):
                raise RunError("Fixture must report every enabled source outcome")
            if not isinstance(records, list):
                raise RunError("Fixture items must be a list")
            manifest["source_outcomes"] = outcomes
            if all(value == "failed" for value in outcomes.values()):
                raise RunError("All source collection failed; this is not a quiet news day")
            usable = [row for row in records if not isinstance(row, dict) or outcomes.get(row.get("source_id")) != "failed"]
            manifest["stages"]["collection"] = "succeeded"
            manifest["stages"]["selection"] = "running"
            selected, quarantine = select_items(usable, settings, end)
            manifest["coverage"] = "partial" if "failed" in outcomes.values() else "complete"
            manifest["selection_outcome"] = "selected" if selected else ("metadata_rejected" if quarantine else "no_qualifying_items")
            for name, data in (("selected_items.json", selected), ("quarantine.json", quarantine)):
                write_json(directory / name, data)
                manifest["artifacts"][name] = sha256((directory / name).read_bytes()).hexdigest()
            manifest["selected_count"] = len(selected)
            manifest["quarantined_count"] = len(quarantine)
            manifest["stages"]["selection"] = "succeeded"
            manifest["status"] = "selection_complete"
        except (ValueError, OSError, TypeError) as exc:
            manifest["status"] = "failed"
            stage = "collection" if manifest["stages"]["collection"] != "succeeded" else "selection"
            manifest["stages"][stage] = "failed"
            manifest["error_type"] = type(exc).__name__
            write_json(manifest_path, manifest)
            raise RunError(f"Offline {stage} failed; inspect sanitized manifest") from exc
        write_json(manifest_path, manifest)
        return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show", type=Path, default=Path("config/show.yaml"))
    parser.add_argument("--sources", type=Path, default=Path("config/sources.yaml"))
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--window-end", required=True, help="Timezone-aware ISO timestamp; reused exactly on resume")
    parser.add_argument("--output", type=Path, default=Path("runs"))
    parser.add_argument("--dry-run", action="store_true", required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    try:
        result = execute(args.show, args.sources, args.fixture, args.output, args.window_end, args.resume)
    except (ConfigError, RunError, ValueError, OSError):
        print(json.dumps({"status": "failed", "message": "Invalid configuration, inputs, or run state; inspect manifest if present"}), file=sys.stderr)
        return 1
    print(json.dumps({"status": result["status"], "edition": result["edition"], "selected_count": result["selected_count"], "publication": "disabled"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
