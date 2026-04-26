import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.schemas.run import CreateRunRequest
from app.schemas.run import CompleteRunRequest
from app.services.agentmail import send_report
from app.services.reports import build_run_report, read_report
from app.services.runner import complete_run, create_run


def _metadata():
    return {
        "run_id": "run_report_test",
        "status": "completed",
        "started_at": "2026-04-25T20:00:00+00:00",
        "ended_at": "2026-04-25T20:02:00+00:00",
        "duration_sec": 120,
        "config": {
            "env_id": "ClawLab/FullCleaning-v0",
            "total_timesteps": 1024,
            "eval_episodes": 2,
            "room_size": 5.0,
            "dirt_count": 1,
        },
        "metrics": {
            "ppo": {
                "episodes": 2,
                "avg_reward": 42.5,
                "success_rate": 0.5,
            }
        },
        "model_path": "runs/run_report_test/model/roomba_policy.zip",
        "metrics_path": "runs/run_report_test/metrics/combined_metrics.json",
        "artifact_manifest_path": "runs/run_report_test/artifacts/manifest.json",
        "gif_paths": ["runs/run_report_test/artifacts/episode_seed_1.gif"],
        "trajectory_paths": ["runs/run_report_test/artifacts/episode_seed_1_trajectory.json"],
        "error": None,
    }


class RunReportTests(unittest.TestCase):
    def test_build_run_report_from_completed_metadata(self):
        report = build_run_report(_metadata())

        self.assertEqual(report.run_id, "run_report_test")
        self.assertEqual(report.status, "completed")
        self.assertEqual(report.template, "ClawLab/FullCleaning-v0")
        self.assertEqual(report.steps, 1024)
        self.assertEqual(report.episodes, 2)
        self.assertEqual(report.mean_return, 42.5)
        self.assertEqual(report.best_return, 0.5)
        self.assertIn("run_report_test", report.markdown)
        self.assertEqual(report.artifact_links["gif"], "runs/run_report_test/artifacts/episode_seed_1.gif")
        self.assertEqual(report.artifact_links["artifacts_manifest"], "runs/run_report_test/artifacts/manifest.json")

    def test_agentmail_send_is_skipped_without_configuration(self):
        report = build_run_report(_metadata())
        with patch("app.config.AGENTMAIL_API_KEY", ""), patch("app.config.AGENTMAIL_INBOX_ID", ""):
            result = send_report(report)

        self.assertEqual(result.delivery_status, "skipped")
        self.assertIn("not configured", result.error or "")

    def test_complete_run_writes_report_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with patch("app.services.runner.RUNS_DIR", tmp_path), patch("app.services.reports.RUNS_DIR", tmp_path):
                request = CompleteRunRequest(
                    status="completed",
                    config=_metadata()["config"],
                    metrics=_metadata()["metrics"],
                    model_path=_metadata()["model_path"],
                    metrics_path=_metadata()["metrics_path"],
                )

                with (
                    patch("app.config.AGENTMAIL_API_KEY", ""),
                    patch("app.config.AGENTMAIL_INBOX_ID", ""),
                    patch("app.config.SLACK_WEBHOOK_URL", ""),
                    patch("app.config.SLACK_BOT_TOKEN", ""),
                ):
                    first = complete_run("run_report_test", request)
                    second = complete_run("run_report_test", request)
                report = read_report("run_report_test")

        self.assertIsNotNone(first.report_path)
        self.assertEqual(second.report_path, first.report_path)
        self.assertIsNotNone(report)
        self.assertEqual(report.delivery_status, "skipped")

    def test_create_run_generates_default_gif_before_final_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            model_path = tmp_path / "run_auto_gif" / "model" / "roomba_policy.zip"
            metrics_path = tmp_path / "run_auto_gif" / "metrics" / "eval_metrics.json"
            manifest = {
                "manifest_path": str(tmp_path / "run_auto_gif" / "artifacts" / "manifest.json"),
                "gif_paths": [str(tmp_path / "run_auto_gif" / "artifacts" / "episode_seed_1.gif")],
                "trajectory_paths": [
                    str(tmp_path / "run_auto_gif" / "artifacts" / "episode_seed_1_trajectory.json")
                ],
            }

            def fake_train(run_id, **kwargs):
                nonlocal model_path
                model_path = tmp_path / run_id / "model" / "roomba_policy.zip"
                model_path.parent.mkdir(parents=True, exist_ok=True)
                model_path.write_bytes(b"model")
                return model_path

            def fake_eval(run_id, **kwargs):
                nonlocal metrics_path
                metrics_path = tmp_path / run_id / "metrics" / "eval_metrics.json"
                metrics_path.parent.mkdir(parents=True, exist_ok=True)
                metrics = {"episodes": 1, "success_rate": 1.0, "avg_reward": 2.0, "avg_remaining_dirt": 0.0}
                metrics_path.write_text("{}")
                return metrics

            def fake_baseline(**kwargs):
                return {"random_success_rate": 0.0, "random_avg_remaining_dirt": 1.0}

            with (
                patch("app.services.runner.RUNS_DIR", tmp_path),
                patch("app.services.reports.RUNS_DIR", tmp_path),
                patch("app.rl.train.train_policy", side_effect=fake_train),
                patch("app.rl.eval.evaluate_policy", side_effect=fake_eval),
                patch("app.rl.baseline.evaluate_random_baseline", side_effect=fake_baseline),
                patch("app.rl.visualize.generate_run_artifacts", return_value=manifest) as generate,
                patch("app.services.hermes.query_nia", return_value=""),
                patch("app.config.AGENTMAIL_API_KEY", ""),
                patch("app.config.AGENTMAIL_INBOX_ID", ""),
                patch("app.config.SLACK_WEBHOOK_URL", ""),
                patch("app.config.SLACK_BOT_TOKEN", ""),
            ):
                response = create_run(
                    CreateRunRequest(total_timesteps=1000, eval_episodes=1)
                )
                report = read_report(response.run_id)

        generate.assert_called_once_with(run_id=response.run_id, episodes=1)
        self.assertEqual(response.status, "completed")
        self.assertEqual(response.model_path, str(model_path))
        self.assertIsNotNone(report)
        self.assertEqual(report.artifact_links["gif"], manifest["gif_paths"][0])
        self.assertEqual(report.artifact_links["artifacts_manifest"], manifest["manifest_path"])


if __name__ == "__main__":
    unittest.main()
