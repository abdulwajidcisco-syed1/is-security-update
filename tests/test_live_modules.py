from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline.collect import CollectionError, collect_feed, collect_all
from pipeline.config import Source, load_settings
from pipeline.editorial import EditorialError, evidence_packet, safety_findings, validate_episode
from pipeline.site import build_site, render

ROOT = Path(__file__).resolve().parents[1]

class LiveModuleTests(unittest.TestCase):
    def test_rss_normalization(self):
        source = Source("cisa-alerts", "https://www.cisa.gov/cybersecurity-advisories/all.xml", "rss", True, ("database-security",), 3, True)
        xml = b'<rss><channel><item><title>Database security update</title><link>https://www.cisa.gov/news</link><description>PostgreSQL advisory</description><pubDate>Fri, 19 Sep 2026 08:00:00 GMT</pubDate></item></channel></rss>'
        with patch("pipeline.collect.fetch", return_value=xml):
            rows = collect_feed(source, datetime(2026, 9, 19, 9, tzinfo=timezone.utc))
        self.assertEqual(rows[0]["source_id"], "cisa-alerts")
        self.assertEqual(rows[0]["published_at"], "2026-09-19T08:00:00+00:00")

    def test_all_source_failure_is_distinct(self):
        settings = load_settings(ROOT / "config/show.yaml", ROOT / "config/sources.live.yaml")
        with patch("pipeline.collect.collect_feed", side_effect=CollectionError()), patch("pipeline.collect.collect_nvd", side_effect=CollectionError()), patch("pipeline.collect.collect_hn", side_effect=CollectionError()):
            with self.assertRaises(CollectionError):
                collect_all(settings, datetime.now(timezone.utc), datetime.now(timezone.utc))

    def test_evidence_ids_and_unknown_citations(self):
        stories = [{"story_id": "s1", "title": "CVE-2026-12345", "content": "CVE-2026-12345 affects PostgreSQL", "topics": ["database-security"], "evidence": [{"source_id": "nvd", "url": "https://nvd.nist.gov/vuln/detail/CVE-2026-12345", "published_at": "2026-09-19T00:00:00+00:00", "excerpt": "CVE-2026-12345 affects PostgreSQL"}]}]
        _, claims, urls = evidence_packet(stories)
        valid = {"title": "Update", "summary": "Summary", "segments": [{"heading": "Advisory", "narration": "A supported claim.", "claim_ids": list(claims), "source_urls": list(urls), "is_case_study": False}], "outro": "Goodbye"}
        self.assertEqual(validate_episode(valid, claims, urls)["status"], "approved")
        invalid = json.loads(json.dumps(valid)); invalid["segments"][0]["claim_ids"] = ["invented"]
        with self.assertRaises(EditorialError): validate_episode(invalid, claims, urls)

    def test_safety_patterns(self):
        self.assertTrue(safety_findings("Here is a step-by-step exploit guide"))
        self.assertFalse(safety_findings("The vendor fixed the vulnerability."))

    def test_site_escapes_untrusted_text_and_keeps_sources(self):
        episode = {"title": "Test <script>", "summary": "Safe summary", "segments": [{"heading": "News", "narration": "Literal <b>text</b>", "claim_ids": ["c1"], "source_urls": ["https://example.org/?a=1&b=2"], "is_case_study": False}], "outro": "Bye", "status": "approved"}
        page = render(episode, "2026-09-19")
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;b&gt;text&lt;/b&gt;", page)
        self.assertIn("https://example.org/?a=1&amp;b=2", page)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); episode_path = root / "episode.json"
            episode_path.write_text(json.dumps(episode), encoding="utf-8")
            build_site(root / "site", episode_path, "2026-09-19")
            self.assertTrue((root / "site/episodes/2026-09-19/index.html").is_file())
            self.assertIn("2026-09-19", (root / "site/index.html").read_text(encoding="utf-8"))


    def test_site_packages_media_and_uses_youtube_when_available(self):
        episode = {"title": "Update", "summary": "Summary", "segments": [], "outro": "Bye", "status": "approved"}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); episode_path = root / "episode.json"
            episode_path.write_text(json.dumps(episode), encoding="utf-8")
            for name in ("audio.mp3", "video.mp4", "captions.srt"):
                (root / name).write_bytes(b"artifact")
            build_site(root / "site", episode_path, "2026-09-19", media_source=root, youtube_id="video123")
            page = (root / "site/episodes/2026-09-19/index.html").read_text(encoding="utf-8")
            self.assertIn("youtube-nocookie.com/embed/video123", page)
            self.assertIn("../../media/2026-09-19/audio.mp3", page)
            self.assertTrue((root / "site/media/2026-09-19/video.mp4").is_file())
            self.assertTrue((root / "site/.nojekyll").is_file())
    def test_editorial_schema_requires_evidence(self):
        from pipeline.editorial import schema
        segment = schema()["schema"]["properties"]["segments"]["items"]
        self.assertEqual(segment["properties"]["claim_ids"]["minItems"], 1)
        self.assertEqual(segment["properties"]["source_urls"]["minItems"], 1)

if __name__ == "__main__": unittest.main()
