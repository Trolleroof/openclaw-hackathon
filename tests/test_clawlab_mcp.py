import json
import shutil
import unittest
from pathlib import Path

from app.mcp.clawlab_server import describe_env, list_envs, read_resource, summarize_reward_hacking


class ClawLabMcpTests(unittest.TestCase):
    def test_list_envs_returns_clawlab_ids(self):
        env_ids = {item["id"] for item in list_envs()["envs"]}

        self.assertIn("ClawLab/FullCleaning-v0", env_ids)

    def test_describe_env_returns_reward_components(self):
        payload = describe_env("ClawLab/FullCleaning-v0")

        self.assertIn("clean", payload["reward_components"])

    def test_summarize_reward_hacking_reads_metrics(self):
        run_dir = Path("runs") / "mcp_unittest"
        if run_dir.exists():
            shutil.rmtree(run_dir)
        (run_dir / "metrics").mkdir(parents=True)
        (run_dir / "metrics" / "eval_metrics.json").write_text(
            json.dumps(
                {
                    "success_rate": 1.0,
                    "avg_cleaned_dirt": 6.0,
                    "avg_wall_hits": 0.0,
                    "avg_obstacle_hits": 0.0,
                    "reward_hacking": {"flag_count": 0},
                }
            )
        )

        summary = summarize_reward_hacking("mcp_unittest")

        self.assertEqual(summary["reward_hacking"]["flag_count"], 0)

    def test_read_env_resource(self):
        payload = read_resource("clawlab://envs")

        self.assertIn("envs", payload)


if __name__ == "__main__":
    unittest.main()
