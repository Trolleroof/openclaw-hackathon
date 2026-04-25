import unittest

from app.rl.eval import evaluation_seed, summarize_generalization


class EvalDiagnosticsTests(unittest.TestCase):
    def test_generalization_summary_flags_train_eval_gap(self):
        summary = summarize_generalization(
            train_metrics={"success_rate": 1.0, "avg_cleaned_dirt": 3.0},
            heldout_metrics={"success_rate": 0.2, "avg_cleaned_dirt": 1.0},
        )
        self.assertEqual(summary["success_rate_gap"], 0.8)
        self.assertTrue(summary["possible_memorization"])

    def test_generalization_summary_allows_small_gap(self):
        summary = summarize_generalization(
            train_metrics={"success_rate": 0.9, "avg_cleaned_dirt": 2.8},
            heldout_metrics={"success_rate": 0.85, "avg_cleaned_dirt": 2.7},
        )
        self.assertFalse(summary["possible_memorization"])

    def test_evaluation_seed_includes_run_seed_and_offset(self):
        self.assertEqual(evaluation_seed(seed=7, eval_seed_offset=10_000, episode_index=3), 10_010)
