import unittest

from pipeline.benchmark import benchmark_episode


class BenchmarkTests(unittest.TestCase):
    def test_active_day_benchmark_is_safe_and_target_length(self):
        episode = benchmark_episode()
        self.assertEqual(episode["status"], "approved")
        self.assertGreaterEqual(episode["word_count"], 4_000)
        self.assertLessEqual(episode["word_count"], 5_500)
        narration = " ".join(
            [
                episode["title"],
                episode["summary"],
                *(segment["narration"] for segment in episode["segments"]),
                episode["outro"],
            ]
        )
        self.assertIn("synthetic", narration.casefold())
        self.assertEqual(len(episode["segments"]), 28)


if __name__ == "__main__":
    unittest.main()
