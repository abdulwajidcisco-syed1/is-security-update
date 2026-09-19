import unittest
from unittest.mock import patch

from pipeline.youtube import YouTubeError, preflight, refresh_access_token


class YouTubeTests(unittest.TestCase):
    @patch("pipeline.youtube.request_json")
    def test_refresh_requires_access_token(self, request_json):
        request_json.return_value = {}
        with self.assertRaisesRegex(YouTubeError, "access token"):
            refresh_access_token("client", "secret", "refresh")

    @patch("pipeline.youtube.request_json")
    @patch("pipeline.youtube.refresh_access_token", return_value="access")
    def test_preflight_returns_owned_playlist(self, _refresh, request_json):
        request_json.side_effect = [
            {"items": [{"id": "channel-1", "snippet": {"title": "Security Updates"}}]},
            {"items": [{"id": "playlist-1", "snippet": {"channelId": "channel-1", "title": "Daily"}, "status": {"privacyStatus": "private"}}]},
        ]
        result = preflight("client", "secret", "refresh", "playlist-1")
        self.assertEqual(result["channel_id"], "channel-1")
        self.assertEqual(result["playlist_privacy"], "private")

    @patch("pipeline.youtube.request_json")
    @patch("pipeline.youtube.refresh_access_token", return_value="access")
    def test_preflight_rejects_playlist_from_other_channel(self, _refresh, request_json):
        request_json.side_effect = [
            {"items": [{"id": "channel-1", "snippet": {"title": "Security Updates"}}]},
            {"items": [{"id": "playlist-1", "snippet": {"channelId": "channel-2"}}]},
        ]
        with self.assertRaisesRegex(YouTubeError, "different channel"):
            preflight("client", "secret", "refresh", "playlist-1")


if __name__ == "__main__":
    unittest.main()
