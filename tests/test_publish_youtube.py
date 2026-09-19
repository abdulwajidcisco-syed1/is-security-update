import unittest
from unittest.mock import Mock

from pipeline.publish_youtube import edition_marker, ensure_playlist, find_existing, video_metadata
from pipeline.youtube import YouTubeError


EPISODE = {"title": "Security update", "summary": "Summary", "status": "approved", "segments": [{"source_urls": ["https://example.org/a", "https://example.org/a", "https://example.org/b"]}]}


class YouTubePublishTests(unittest.TestCase):
    def test_metadata_has_disclosure_unique_sources_and_marker(self):
        metadata = video_metadata(EPISODE, "2026-09-19")
        description = metadata["snippet"]["description"]
        self.assertIn("synthetic narration", description)
        self.assertEqual(description.count("https://example.org/a"), 1)
        self.assertIn(edition_marker("2026-09-19"), description)
        self.assertTrue(metadata["status"]["containsSyntheticMedia"])
        self.assertEqual(metadata["status"]["privacyStatus"], "private")

    def test_find_existing_requires_exact_marker(self):
        api = Mock()
        api.request.side_effect = [{"items": [{"id": {"videoId": "abc"}}]}, {"items": [{"id": "abc", "snippet": {"description": edition_marker("2026-09-19")}}]}]
        self.assertEqual(find_existing(api, "2026-09-19")["id"], "abc")

    def test_find_existing_rejects_duplicate_markers(self):
        api = Mock()
        api.request.side_effect = [{"items": [{"id": {"videoId": "a"}}, {"id": {"videoId": "b"}}]}, {"items": [{"id": "a", "snippet": {"description": edition_marker("2026-09-19")}}, {"id": "b", "snippet": {"description": edition_marker("2026-09-19")}}]}]
        with self.assertRaisesRegex(YouTubeError, "Multiple"):
            find_existing(api, "2026-09-19")

    def test_playlist_insertion_is_idempotent(self):
        api = Mock(); api.request.return_value = {"items": [{"id": "playlist-item"}]}
        self.assertEqual(ensure_playlist(api, "playlist", "video"), "reused")
        self.assertEqual(api.request.call_count, 1)


if __name__ == "__main__":
    unittest.main()
