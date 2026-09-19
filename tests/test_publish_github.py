from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from pipeline.publish_github import PublishError, REQUIRED_ASSETS, local_assets, reconcile_assets


class GitHubPublishTests(unittest.TestCase):
    def make_edition(self, root):
        directory = Path(root) / "2026-09-19"; directory.mkdir()
        artifacts = {}
        for name in REQUIRED_ASSETS:
            if name == "manifest.json":
                continue
            path = directory / name; path.write_bytes((name + "\n").encode())
            artifacts[name] = sha256(path.read_bytes()).hexdigest()
        (directory / "manifest.json").write_text(json.dumps({"edition": directory.name, "publication": "disabled", "artifacts": artifacts}), encoding="utf-8")
        return directory

    def test_local_assets_require_manifest_checksums(self):
        with tempfile.TemporaryDirectory() as root:
            directory = self.make_edition(root)
            assets = local_assets(directory)
            self.assertEqual(set(assets), set(REQUIRED_ASSETS))
            (directory / "audio.mp3").write_bytes(b"changed")
            with self.assertRaisesRegex(PublishError, "checksum"):
                local_assets(directory)

    def test_reconcile_uploads_missing_and_reuses_exact_digest(self):
        local = {"audio.mp3": {"bytes": 4, "sha256": "a" * 64}, "video.mp4": {"bytes": 5, "sha256": "b" * 64}}
        remote = [{"name": "audio.mp3", "size": 4, "digest": "sha256:" + "a" * 64}]
        self.assertEqual(reconcile_assets(local, remote), (["video.mp4"], ["audio.mp3"]))

    def test_reconcile_blocks_ambiguous_existing_asset(self):
        local = {"audio.mp3": {"bytes": 4, "sha256": "a" * 64}}
        with self.assertRaisesRegex(PublishError, "does not match"):
            reconcile_assets(local, [{"name": "audio.mp3", "size": 4}])


if __name__ == "__main__":
    unittest.main()
