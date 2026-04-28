import json
import shutil
import unittest
from pathlib import Path

from app.mcp.apollolabs_server import (
    compare_runs,
    describe_env,
    get_run_status,
    list_envs,
    read_resource,
    summarize_reward_hacking,
)


class ApolloLabsMcpTests(unittest.TestCase):
    GENERATED_RUN_IDS = {
        "mcp_status_unittest",
        "mcp_compare_a",
        "mcp_compare_b",
        "mcp_compare_c",
        "mcp_resource_unittest",
    }

    def tearDown(self):
        for run_id in self.GENERATED_RUN_IDS:
            run_dir = Path("runs") / run_id
            if run_dir.is_dir():
                shutil.rmtree(run_dir)

    def test_list_envs_returns_apollolabs_ids(self):
        env_ids = {item["id"] for item in list_envs()["envs"]}

        self.assertIn("ApolloLabs/FullCleaning-v0", env_ids)

    def test_describe_env_returns_reward_components(self):
        payload = describe_env("ApolloLabs/FullCleaning-v0")

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
        payload = read_resource("apollolabs://envs")

        self.assertIn("envs", payload)

    def test_get_run_status_reads_metadata_and_artifact_locations(self):
        run_dir = Path("runs") / "mcp_status_unittest"
        if run_dir.exists():
            shutil.rmtree(run_dir)
        (run_dir / "metrics").mkdir(parents=True)
        (run_dir / "artifacts").mkdir()
        (run_dir / "logs").mkdir()
        (run_dir / "metadata.json").write_text(
            json.dumps(
                {
                    "run_id": "mcp_status_unittest",
                    "status": "completed",
                    "config": {"env_id": "ApolloLabs/FullCleaning-v0"},
                    "metrics_path": str(run_dir / "metrics" / "combined_metrics.json"),
                    "report_path": str(run_dir / "report.json"),
                    "model_path": str(run_dir / "model" / "roomba_policy.zip"),
                    "error": None,
                }
            )
        )
        (run_dir / "metrics" / "combined_metrics.json").write_text("{}")
        (run_dir / "artifacts" / "rollout.gif").write_bytes(b"GIF89a")
        (run_dir / "logs" / "error.txt").write_text("")

        status = get_run_status("mcp_status_unittest")

        self.assertEqual(status["status"], "completed")
        self.assertEqual(status["resources"]["metadata"], "apollolabs://runs/mcp_status_unittest/metadata")
        self.assertTrue(status["artifacts"]["has_gif"])

    def test_get_run_status_supports_direct_training_runs_without_metadata(self):
        run_dir = Path("runs") / "mcp_status_unittest"
        if run_dir.exists():
            shutil.rmtree(run_dir)
        (run_dir / "metrics").mkdir(parents=True)
        (run_dir / "model").mkdir()
        (run_dir / "rl_config.json").write_text(
            json.dumps({"env_id": "ApolloLabs/FullCleaning-v0", "total_timesteps": 1024})
        )
        (run_dir / "metrics" / "eval_metrics.json").write_text(
            json.dumps({"success_rate": 0.0})
        )
        (run_dir / "model" / "roomba_policy.zip").write_bytes(b"model")

        status = get_run_status("mcp_status_unittest")
        metadata = read_resource("apollolabs://runs/mcp_status_unittest/metadata")

        self.assertEqual(status["status"], "completed")
        self.assertEqual(status["env_id"], "ApolloLabs/FullCleaning-v0")
        self.assertEqual(metadata["config"]["total_timesteps"], 1024)
        self.assertTrue(status["model_path"].endswith("model/roomba_policy.zip"))

    def test_compare_runs_ranks_by_success_and_reward_hacking_flags(self):
        for run_id, success_rate, flag_count, remaining_dirt in [
            ("mcp_compare_a", 0.75, 0, 1.0),
            ("mcp_compare_b", 0.90, 2, 0.5),
            ("mcp_compare_c", 0.90, 0, 0.5),
        ]:
            run_dir = Path("runs") / run_id
            if run_dir.exists():
                shutil.rmtree(run_dir)
            (run_dir / "metrics").mkdir(parents=True)
            (run_dir / "metrics" / "eval_metrics.json").write_text(
                json.dumps(
                    {
                        "success_rate": success_rate,
                        "avg_reward": success_rate * 10,
                        "avg_remaining_dirt": remaining_dirt,
                        "avg_wall_hits": 0.0,
                        "avg_obstacle_hits": 0.0,
                        "reward_hacking": {"flag_count": flag_count},
                    }
                )
            )

        comparison = compare_runs(["mcp_compare_a", "mcp_compare_b", "mcp_compare_c"])

        self.assertEqual(comparison["best_run_id"], "mcp_compare_c")
        self.assertEqual(comparison["ranking"][0]["run_id"], "mcp_compare_c")
        self.assertIn("reward_hacking_flags asc", comparison["criteria"])

    def test_read_run_metadata_report_and_logs_resources(self):
        run_dir = Path("runs") / "mcp_resource_unittest"
        if run_dir.exists():
            shutil.rmtree(run_dir)
        (run_dir / "logs").mkdir(parents=True)
        (run_dir / "metadata.json").write_text(json.dumps({"run_id": "mcp_resource_unittest"}))
        (run_dir / "report.json").write_text(json.dumps({"run_id": "mcp_resource_unittest", "status": "completed"}))
        (run_dir / "logs" / "error.txt").write_text("example traceback")

        metadata = read_resource("apollolabs://runs/mcp_resource_unittest/metadata")
        report = read_resource("apollolabs://runs/mcp_resource_unittest/report")
        logs = read_resource("apollolabs://runs/mcp_resource_unittest/logs")

        self.assertEqual(metadata["run_id"], "mcp_resource_unittest")
        self.assertEqual(report["status"], "completed")
        self.assertIn("example traceback", logs["files"]["error.txt"])


if __name__ == "__main__":
    unittest.main()
