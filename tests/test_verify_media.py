import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from pipeline.editorial import EditorialError, validate_episode
from pipeline.media import Cue, caption_chunks, narration_sections, write_srt
from pipeline.verify_media import VerificationError, verify


EPISODE = {
    "title": "Daily security update",
    "summary": "One public update was reviewed.",
    "segments": [{
        "heading": "Database security",
        "narration": "Review the cited vendor guidance.",
        "claim_ids": ["claim"],
        "source_urls": ["https://example.org/advisory"],
        "is_case_study": False,
    }],
    "outro": "That is today's update.",
    "status": "approved",
    "word_count": 16,
}


class ShortPreviewVerificationTests(unittest.TestCase):
    def test_maximum_words_is_enforced(self):
        with self.assertRaisesRegex(EditorialError, "longer"):
            validate_episode(dict(EPISODE), {"claim"}, {"https://example.org/advisory"}, maximum_words=5)

    def test_media_verifier_matches_script_captions_and_hashes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "episode.json").write_text(json.dumps(EPISODE), encoding="utf-8")
            chunks = [chunk for section in narration_sections(EPISODE) for chunk in caption_chunks(section)]
            write_srt([Cue(index, index + 1, chunk) for index, chunk in enumerate(chunks)], root / "captions.srt")
            for name, data in (("audio.mp3", b"audio"), ("video.mp4", b"video")):
                (root / name).write_bytes(data)
            media_artifacts = {
                name: {"sha256": hashlib.sha256((root / name).read_bytes()).hexdigest()}
                for name in ("audio.mp3", "video.mp4", "captions.srt")
            }
            (root / "media.json").write_text(json.dumps({"duration_seconds": 180, "artifacts": media_artifacts}), encoding="utf-8")
            manifest_artifacts = {
                name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                for name in ("episode.json", "captions.srt", "media.json", "audio.mp3", "video.mp4")
            }
            (root / "manifest.json").write_text(json.dumps({"artifacts": manifest_artifacts}), encoding="utf-8")
            self.assertEqual(verify(root, 150, 240)["status"], "verified")
            bad_caption = chr(10).join(("1", "00:00:00,000 --> 00:00:01,000", "Different text", ""))
            (root / "captions.srt").write_text(bad_caption, encoding="utf-8")
            with self.assertRaisesRegex(VerificationError, "Subtitle"):
                verify(root, 150, 240)


if __name__ == "__main__":
    unittest.main()