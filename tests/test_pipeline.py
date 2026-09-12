from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

import yaml

from pipeline.config import ConfigError, load_settings, public_url
from pipeline.run import RunError, edition_lock, execute
from pipeline.selection import canonical_url, select_items, timestamp


ROOT = Path(__file__).resolve().parents[1]
SHOW = ROOT / "config/show.yaml"
SOURCES = ROOT / "config/sources.yaml"
FIXTURE = ROOT / "tests/fixtures/news.json"
END = "2026-09-12T08:00:00Z"


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.settings = load_settings(SHOW, SOURCES)
        self.payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_filters_duplicates_old_and_missing_dates(self):
        selected, quarantine = select_items(self.payload["items"], self.settings, timestamp(END))
        self.assertEqual(len(selected), 2)
        self.assertEqual(len(quarantine), 1)
        self.assertIn("ciphertrust", selected[0]["topics"])
        self.assertEqual(len(selected[0]["evidence"]), 1)

    def test_half_open_window_and_timezone_conversion(self):
        base = self.payload["items"][0]
        records = []
        for index, date in enumerate(["2026-09-11T08:00:00Z", END, "2026-09-11T07:59:59Z", "2026-09-12T13:29:59+05:30"]):
            records.append({**base, "url": f"https://example.org/{index}", "content": f"CipherTrust test {index}", "published_at": date})
        selected, rejected = select_items(records, self.settings, timestamp(END))
        self.assertEqual({item["url"] for item in selected}, {"https://example.org/0", "https://example.org/3"})
        self.assertEqual(rejected, [])

    def test_naive_date_quarantined(self):
        row = {**self.payload["items"][0], "published_at": "2026-09-12T07:00:00"}
        selected, rejected = select_items([row], self.settings, timestamp(END))
        self.assertEqual(selected, [])
        self.assertEqual(len(rejected), 1)

    def test_material_update_requires_valid_ordered_dates(self):
        row = {**self.payload["items"][0], "published_at": "2026-09-01T00:00:00Z", "material_update": True, "updated_at": "2026-09-12T07:00:00Z"}
        selected, _ = select_items([row], self.settings, timestamp(END))
        self.assertEqual(selected[0]["evidence"][0]["timestamp_basis"], "updated_at")
        row["updated_at"] = "2026-08-01T00:00:00Z"
        self.assertEqual(len(select_items([row], self.settings, timestamp(END))[1]), 1)

    def test_content_duplicate_retains_both_sources(self):
        row = self.payload["items"][2]
        other = {**row, "url": "https://example.org/syndicated"}
        selected, _ = select_items([row, other], self.settings, timestamp(END))
        self.assertEqual(len(selected), 1)
        self.assertEqual(len(selected[0]["evidence"]), 2)

    def test_noise_and_ranking_limit(self):
        noise = {**self.payload["items"][0], "title": "Gardening", "content": "Growing tomatoes"}
        settings = replace(self.settings, max_items=1)
        selected, _ = select_items([noise] + self.payload["items"], settings, timestamp(END))
        self.assertEqual(len(selected), 1)
        self.assertIn("ciphertrust", selected[0]["topics"])

    def test_credential_and_local_urls_rejected(self):
        for url in ["http://example.org", "https://user:secret@example.org", "https://127.0.0.1/feed", "https://localhost/feed", "https://169.254.169.254/data"]:
            with self.subTest(url=url), self.assertRaises(ConfigError):
                public_url(url)
        self.assertEqual(canonical_url("https://example.org/x?utm_source=z&version=2#top"), "https://example.org/x?version=2")

    def test_configuration_rejects_publication_and_invalid_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "show.yaml"
            data = yaml.safe_load(SHOW.read_text(encoding="utf-8"))
            for field, value in [("publishing_enabled", True), ("max_items", True), ("timezone", "Asia/Kolkata")]:
                changed = {**data, field: value}
                path.write_text(yaml.safe_dump(changed), encoding="utf-8")
                with self.subTest(field=field), self.assertRaises(ConfigError):
                    load_settings(path, SOURCES)

    def test_topic_added_via_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            show = yaml.safe_load(SHOW.read_text(encoding="utf-8"))
            sources = yaml.safe_load(SOURCES.read_text(encoding="utf-8"))
            show["topics"].append({"id": "new-product", "aliases": ["New Product"], "weight": 2})
            sources["sources"][0]["topics"].append("new-product")
            a, b = Path(directory) / "show.yaml", Path(directory) / "sources.yaml"
            a.write_text(yaml.safe_dump(show), encoding="utf-8")
            b.write_text(yaml.safe_dump(sources), encoding="utf-8")
            settings = load_settings(a, b)
            row = {**self.payload["items"][0], "title": "New Product", "content": "New Product fixture"}
            self.assertEqual(select_items([row], settings, timestamp(END))[0][0]["topics"], ["new-product"])

    def test_resume_reuses_results_and_detects_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            first = execute(SHOW, SOURCES, FIXTURE, output, END)
            second = execute(SHOW, SOURCES, FIXTURE, output, END, resume=True)
            self.assertEqual(first, second)
            with self.assertRaises(RunError):
                execute(SHOW, SOURCES, FIXTURE, output, END)
            artifact = output / "is-security-update/2026-09-12/selected_items.json"
            artifact.write_text("[]", encoding="utf-8")
            with self.assertRaises(RunError):
                execute(SHOW, SOURCES, FIXTURE, output, END, resume=True)

    def test_resume_rejects_changed_window(self):
        with tempfile.TemporaryDirectory() as directory:
            execute(SHOW, SOURCES, FIXTURE, Path(directory), END)
            with self.assertRaises(RunError):
                execute(SHOW, SOURCES, FIXTURE, Path(directory), "2026-09-12T09:00:00Z", resume=True)

    def test_resume_rejects_missing_manifest_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            manifest = execute(SHOW, SOURCES, FIXTURE, output, END)
            manifest["artifacts"] = {}
            path = output / "is-security-update/2026-09-12/manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(RunError):
                execute(SHOW, SOURCES, FIXTURE, output, END, resume=True)

    def test_lock_blocks_concurrent_edition(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".lock"
            with edition_lock(path):
                with self.assertRaises(RunError):
                    with edition_lock(path):
                        self.fail("Second writer must not acquire lock")
            self.assertFalse(path.exists())

    def test_partial_all_failed_and_empty_are_distinct(self):
        for state in ["partial", "failed", "empty"]:
            with self.subTest(state=state), tempfile.TemporaryDirectory() as directory:
                payload = deepcopy(self.payload)
                if state in {"partial", "failed"}:
                    payload["source_outcomes"]["fixture-news"] = "failed"
                if state == "failed":
                    payload["source_outcomes"]["fixture-vendor"] = "failed"
                if state == "empty":
                    payload["items"] = []
                fixture = Path(directory) / "fixture.json"
                fixture.write_text(json.dumps(payload), encoding="utf-8")
                if state == "failed":
                    with self.assertRaises(RunError):
                        execute(SHOW, SOURCES, fixture, Path(directory) / "runs", END)
                else:
                    manifest = execute(SHOW, SOURCES, fixture, Path(directory) / "runs", END)
                    if state == "partial":
                        self.assertEqual(manifest["coverage"], "partial")
                        self.assertEqual(manifest["selected_count"], 1)
                    else:
                        self.assertEqual(manifest["selection_outcome"], "no_qualifying_items")
                    self.assertEqual(manifest["publication"], "disabled")


if __name__ == "__main__":
    unittest.main()
