import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.schemas.run import CompleteRunRequest
from app.services.agentmail import send_report
from app.services.reports import build_run_report, read_report
from app.services.runner import complete_run


def _metadata():
    return {
        "run_id": "run_report_test",
        "status": "completed",
        "started_at": "2026-04-25T20:00:00+00:00",
        "ended_at": "2026-04-25T20:02:00+00:00",
        "duration_sec": 120,
        "config": {
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
        "error": None,
    }


class RunReportTests(unittest.TestCase):
    def test_build_run_report_from_completed_metadata(self):
        report = build_run_report(_metadata())

        self.assertEqual(report.run_id, "run_report_test")
        self.assertEqual(report.status, "success")
        self.assertEqual(report.steps, 1024)
        self.assertEqual(report.episodes, 2)
        self.assertEqual(report.mean_return, 42.5)
        self.assertEqual(report.best_return, 0.5)
        self.assertIn("run_report_test", report.markdown)

    def test_agentmail_send_is_skipped_without_configuration(self):
        report = build_run_report(_metadata())
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

                first = complete_run("run_report_test", request)
                second = complete_run("run_report_test", request)
                report = read_report("run_report_test")

        self.assertIsNotNone(first.report_path)
        self.assertEqual(second.report_path, first.report_path)
        self.assertIsNotNone(report)
        self.assertEqual(report.delivery_status, "skipped")


if __name__ == "__main__":
    unittest.main()
