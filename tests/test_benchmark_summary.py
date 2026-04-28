import unittest

from app.rl.benchmark import summarize_benchmark


class BenchmarkSummaryTests(unittest.TestCase):
    def test_summary_reports_best_run_and_reward_hacking_flags(self):
        summary = summarize_benchmark(
            [
                {
                    "run_id": "run_bad",
                    "env_id": "ApolloLabs/FullCleaning-v0",
                    "metrics": {
                        "success_rate": 0.5,
                        "avg_reward": 10.0,
                        "avg_cleaned_dirt": 3.0,
                        "avg_wall_hits": 0.0,
                        "avg_obstacle_hits": 0.0,
                        "reward_hacking": {
                            "reward_hacking_flag_count": 1,
                            "behavior_flag_count": 2,
                            "flag_count": 3,
                        },
                    },
                },
                {
                    "run_id": "run_good",
                    "env_id": "ApolloLabs/FullCleaning-v0",
                    "metrics": {
                        "success_rate": 1.0,
                        "avg_reward": 50.0,
                        "avg_cleaned_dirt": 6.0,
                        "avg_wall_hits": 0.0,
                        "avg_obstacle_hits": 0.0,
                        "reward_hacking": {
                            "reward_hacking_flag_count": 0,
                            "behavior_flag_count": 0,
                            "flag_count": 0,
                        },
                    },
                    "progress": [
                        {"timesteps": 100, "success_rate": 0.25, "avg_reward": 5.0},
                        {"timesteps": 200, "success_rate": 1.0, "avg_reward": 50.0},
                    ],
                },
            ]
        )

        self.assertEqual(summary["best_run_id"], "run_good")
        self.assertEqual(summary["runs"][0]["reward_hacking_flags"], 1)
        self.assertEqual(summary["runs"][0]["behavior_flags"], 2)
        self.assertEqual(summary["runs"][1]["avg_cleaned_dirt"], 6.0)
        self.assertEqual(summary["runs"][1]["progress"]["snapshots"], 2)
        self.assertEqual(summary["runs"][1]["progress"]["success_rate_delta"], 0.75)


if __name__ == "__main__":
    unittest.main()
