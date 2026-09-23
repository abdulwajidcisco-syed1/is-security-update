import tempfile
import unittest
from pathlib import Path

from pipeline.media import Cue, MediaError, caption_chunks, narration_sections, visual_scenes, write_srt, write_visual_ass


EPISODE = {
    "title": "Daily security update",
    "summary": "Two public updates were reviewed.",
    "segments": [{"heading": "Database security", "narration": "Apply the vendor guidance after testing."}],
    "outro": "That is today's update.",
    "status": "approved",
}


class MediaTests(unittest.TestCase):
    def test_narration_contains_complete_approved_script(self):
        self.assertEqual(narration_sections(EPISODE), [EPISODE["title"], EPISODE["summary"], "Database security", "Apply the vendor guidance after testing.", EPISODE["outro"]])

    def test_unapproved_episode_is_rejected(self):
        with self.assertRaisesRegex(MediaError, "approved"):
            narration_sections({**EPISODE, "status": "draft"})

    def test_srt_uses_monotonic_actual_chunk_boundaries(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "captions.srt"
            write_srt([Cue(0, 1.25, "First"), Cue(1.25, 2.5, "Second")], path)
            text = path.read_text(encoding="utf-8")
            self.assertIn("00:00:00,000 --> 00:00:01,250", text)
            self.assertIn("00:00:01,250 --> 00:00:02,500", text)

    def test_overlapping_caption_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(MediaError, "monotonic"):
                write_srt([Cue(0, 2, "First"), Cue(1, 3, "Second")], Path(folder) / "bad.srt")

    def test_caption_chunks_are_readable_and_preserve_words(self):
        text = "First sentence is short. Second sentence contains several additional words for a readable subtitle cue."
        chunks = caption_chunks(text, maximum=45)
        self.assertTrue(all(len(chunk) <= 45 for chunk in chunks))
        self.assertEqual(" ".join(chunks), text)

    def test_visual_scenes_align_headings_and_extract_cves(self):
        episode = {**EPISODE, "segments": [{"heading": "Database security", "narration": "Review CVE-2026-12345 with the vendor.", "source_urls": ["https://example.org/advisory"]}]}
        cues = [Cue(0, 1, episode["title"]), Cue(1, 2, episode["summary"]), Cue(2, 3, "Database security"), Cue(3, 4, episode["segments"][0]["narration"]), Cue(4, 5, episode["outro"])]
        scenes = visual_scenes(episode, cues)
        self.assertEqual(scenes[1]["start"], 2)
        self.assertEqual(scenes[1]["identifiers"], ["CVE-2026-12345"])
        self.assertEqual(scenes[1]["label"], "DATABASE SECURITY")
        self.assertEqual(scenes[1]["source_count"], 1)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "visuals.ass"
            write_visual_ass(scenes, path)
            text = path.read_text(encoding="utf-8")
            self.assertIn("Database security", text)
            self.assertIn("CVE-2026-12345", text)


if __name__ == "__main__":
    unittest.main()
