from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/daily-publish.yml"


class DailyWorkflowTests(unittest.TestCase):
    def test_schedule_is_gated_and_permissions_are_scoped(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("cron: '0 3 * * *'", text)
        self.assertIn("vars.PILOT_ENABLED == 'true'", text)
        self.assertIn('test "${{ inputs.confirmation }}" = RUN', text)
        self.assertIn("contents: write", text)
        self.assertIn("pages: write", text)
        self.assertIn("id-token: write", text)
        self.assertNotIn("permissions: write-all", text)

    def test_publication_resumes_and_verifies_all_destinations(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for required in (
            "gh release download",
            "pipeline.publish_github",
            "pipeline.publish_youtube",
            "pipeline.site",
            "actions/deploy-pages@v4",
            "gh release view",
            "curl --fail",
        ):
            self.assertIn(required, text)
        self.assertIn("concurrency:", text)
        self.assertIn("cancel-in-progress: false", text)


if __name__ == "__main__":
    unittest.main()
