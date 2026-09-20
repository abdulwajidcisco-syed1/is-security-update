from datetime import datetime, timezone
import json
from io import BytesIO
from urllib.error import HTTPError
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline.collect import CollectionError, collect_cisa_kev, collect_feed, collect_all, fetch
from pipeline.config import Source, load_settings
from pipeline.editorial import EditorialError, evidence_packet, generate_episode, safety_findings, validate_episode
from pipeline.site import build_site, render, sync_existing_site

ROOT = Path(__file__).resolve().parents[1]

class LiveModuleTests(unittest.TestCase):
    def test_rss_normalization(self):
        source = Source("cisa-alerts", "https://www.cisa.gov/cybersecurity-advisories/all.xml", "rss", True, ("database-security",), 3, True)
        xml = b'<rss><channel><item><title>Database security update</title><link>https://www.cisa.gov/news</link><description>PostgreSQL advisory</description><pubDate>Fri, 19 Sep 2026 08:00:00 GMT</pubDate></item></channel></rss>'
        with patch("pipeline.collect.fetch", return_value=xml):
            rows = collect_feed(source, datetime(2026, 9, 19, 9, tzinfo=timezone.utc))
        self.assertEqual(rows[0]["source_id"], "cisa-alerts")
        self.assertEqual(rows[0]["published_at"], "2026-09-19T08:00:00+00:00")


    def test_cisa_kev_normalization(self):
        source = Source("cisa-alerts", "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json", "cisa_kev", True, ("database-security",), 3, True)
        payload = {"vulnerabilities": [{"cveID": "CVE-2026-12345", "vendorProject": "Example", "product": "Database", "dateAdded": "2026-09-19", "shortDescription": "A database vulnerability.", "requiredAction": "Apply the vendor update."}]}
        with patch("pipeline.collect.fetch", return_value=json.dumps(payload).encode()):
            rows = collect_cisa_kev(source, datetime(2026, 9, 19, 9, tzinfo=timezone.utc))
        self.assertEqual(rows[0]["source_id"], "cisa-alerts")
        self.assertEqual(rows[0]["published_at"], "2026-09-19T00:00:00+00:00")
        self.assertIn("CVE-2026-12345", rows[0]["url"])
    def test_fetch_retries_rate_limit_with_bounded_backoff(self):
        class Response(BytesIO):
            def geturl(self):
                return "https://www.cisa.gov/feed"

        rejection = HTTPError("https://www.cisa.gov/feed", 429, "rate limited", {}, BytesIO())
        address = [(None, None, None, None, ("8.8.8.8", 443))]
        with patch("pipeline.collect.socket.getaddrinfo", return_value=address), patch("pipeline.collect.urlopen", side_effect=[rejection, Response(b"ok")]) as request, patch("pipeline.collect.time.sleep") as delay:
            self.assertEqual(fetch("https://www.cisa.gov/feed"), b"ok")
        self.assertEqual(request.call_count, 2)
        delay.assert_called_once_with(1)
    def test_all_source_failure_is_distinct(self):
        settings = load_settings(ROOT / "config/show.yaml", ROOT / "config/sources.live.yaml")
        with patch("pipeline.collect.collect_feed", side_effect=CollectionError()), patch("pipeline.collect.collect_cisa_kev", side_effect=CollectionError()), patch("pipeline.collect.collect_nvd", side_effect=CollectionError()), patch("pipeline.collect.collect_hn", side_effect=CollectionError()):
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

    def test_site_archive_sync_is_bounded_to_same_base(self):
        index = b'<a href="episodes/2026-09-18/">old</a>'
        page = b'<html>archived episode</html>'
        assets = {"audio.mp3": b"audio", "video.mp4": b"video", "captions.srt": b"captions"}

        def fetch(request, timeout=60):
            url = request.full_url
            if url.endswith("is-security-update/"):
                return BytesIO(index)
            if url.endswith("episodes/2026-09-18/"):
                return BytesIO(page)
            return BytesIO(assets[url.rsplit("/", 1)[-1]])

        with tempfile.TemporaryDirectory() as folder, patch("pipeline.site.urlopen", side_effect=fetch):
            root = Path(folder)
            dates = sync_existing_site("https://example.org/is-security-update/", root, keep=1)
            self.assertEqual(dates, ["2026-09-18"])
            self.assertEqual((root / "episodes/2026-09-18/index.html").read_bytes(), page)
            self.assertEqual((root / "media/2026-09-18/audio.mp3").read_bytes(), b"audio")
        with self.assertRaises(ValueError):
            sync_existing_site("http://example.org/", Path("unused"))
    def test_generation_retries_schema_rejection(self):
        stories = [{"story_id": "s1", "title": "Database update", "content": "A database update", "topics": ["database-security"], "evidence": [{"source_id": "vendor", "url": "https://example.org/update", "published_at": "2026-09-19T00:00:00+00:00", "excerpt": "A database update is available"}]}]
        _, claims, urls = evidence_packet(stories)
        episode = {"title": "Update", "summary": "Summary", "segments": [{"heading": "Advisory", "narration": "A database update is available.", "claim_ids": list(claims), "source_urls": list(urls), "is_case_study": False}], "outro": "Goodbye"}
        error_body = BytesIO(json.dumps({"error": {"message": "Generated JSON does not match the expected schema."}}).encode())
        rejection = HTTPError("https://api.groq.com", 400, "Bad Request", {}, error_body)
        success = BytesIO(json.dumps({"choices": [{"message": {"content": json.dumps(episode)}}]}).encode())
        with patch("pipeline.editorial.urlopen", side_effect=[rejection, success]) as request, patch("pipeline.editorial.time.sleep"):
            result = generate_episode(stories, "test-model", "2026-09-19", api_key="test-key")
        self.assertEqual(result["status"], "approved")
        self.assertEqual(request.call_count, 2)
    def test_generation_retries_validation_once_and_fails_closed(self):
        stories = [{"story_id": "s1", "title": "Database update", "content": "A database update", "topics": ["database-security"], "evidence": [{"source_id": "vendor", "url": "https://example.org/update", "published_at": "2026-09-19T00:00:00+00:00", "excerpt": "A database update is available"}]}]
        _, claims, urls = evidence_packet(stories)
        base = {"title": "Update", "summary": "Summary", "segments": [{"heading": "Advisory", "narration": "A database update is available.", "claim_ids": list(claims), "source_urls": list(urls), "is_case_study": False}], "outro": "Goodbye"}
        unsafe = json.loads(json.dumps(base)); unsafe["segments"][0]["narration"] = "Provide a working exploit payload"
        valid_response = lambda episode: BytesIO(json.dumps({"choices": [{"message": {"content": json.dumps(episode)}}]}).encode())
        with patch("pipeline.editorial.urlopen", side_effect=[valid_response(unsafe), valid_response(base)]) as request:
            result = generate_episode(stories, "test-model", "2026-09-19", api_key="test-key")
        self.assertEqual(result["status"], "approved")
        self.assertEqual(request.call_count, 2)
        with patch("pipeline.editorial.urlopen", side_effect=[valid_response(unsafe), valid_response(unsafe)]):
            with self.assertRaisesRegex(EditorialError, "corrective retry"):
                generate_episode(stories, "test-model", "2026-09-19", api_key="test-key")
    def test_editorial_schema_requires_evidence(self):
        from pipeline.editorial import schema
        segment = schema()["schema"]["properties"]["segments"]["items"]
        self.assertEqual(segment["properties"]["claim_ids"]["minItems"], 1)
        self.assertEqual(segment["properties"]["source_urls"]["minItems"], 1)

if __name__ == "__main__": unittest.main()
