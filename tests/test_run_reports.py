import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.schemas.run import CompleteRunRequest
from app.services.agentmail import AgentMailResult, get_inbox_message, list_inbox_messages, send_report
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


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def _historical_config(total_timesteps: int = 40000, seed: int = 1) -> dict:
    return {
        "total_timesteps": total_timesteps,
        "seed": seed,
        "eval_seed_offset": 10000,
        "room_size": 10.0,
        "max_steps": 220,
        "dirt_count": 6,
        "obstacle_count": 4,
        "layout_mode": "random",
        "sensor_mode": "lidar_local_dirt",
        "lidar_rays": 16,
        "device": "cpu",
    }


def _historical_eval(avg_reward: float, success_rate: float, episodes: int = 20) -> dict:
    return {
        "episodes": episodes,
        "success_rate": success_rate,
        "avg_reward": avg_reward,
        "avg_steps": 120.0,
        "avg_remaining_dirt": 0.5,
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

    def test_local_agentmail_feed_lists_seeded_historical_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            older_run = tmp_path / "matrix_random_oracle_40k"
            newer_run = tmp_path / "matrix_random_lidar_v2_60k"
            excluded_run = tmp_path / "integration_smoke_lidar"

            _write_json(older_run / "rl_config.json", _historical_config(total_timesteps=40000, seed=103))
            _write_json(older_run / "metrics" / "eval_metrics.json", _historical_eval(avg_reward=12.5, success_rate=0.7))
            _write_json(newer_run / "rl_config.json", _historical_config(total_timesteps=60000, seed=204))
            _write_json(newer_run / "metrics" / "eval_metrics.json", _historical_eval(avg_reward=33.2, success_rate=0.9))
            _write_json(excluded_run / "rl_config.json", _historical_config(total_timesteps=5000, seed=5))
            _write_json(excluded_run / "metrics" / "eval_metrics.json", _historical_eval(avg_reward=-2.4, success_rate=0.0, episodes=3))

            os.utime(older_run / "metrics" / "eval_metrics.json", (1_700_000_000, 1_700_000_000))
            os.utime(newer_run / "metrics" / "eval_metrics.json", (1_800_000_000, 1_800_000_000))

            with patch("app.services.reports.RUNS_DIR", tmp_path), patch(
                "app.services.reports.HISTORICAL_AGENTMAIL_RUN_IDS",
                ("matrix_random_oracle_40k", "matrix_random_lidar_v2_60k"),
            ):
                feed = list_inbox_messages(limit=10)

        self.assertEqual(feed.count, 2)
        self.assertEqual(
            [message.message_id for message in feed.messages],
            ["run:matrix_random_lidar_v2_60k", "run:matrix_random_oracle_40k"],
        )
        self.assertTrue(all(message.source == "historical_seed" for message in feed.messages))
        self.assertTrue(all("historical" in message.labels for message in feed.messages))

    def test_local_agentmail_detail_returns_rendered_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_dir = tmp_path / "matrix_random_lidar_v2_60k"
            _write_json(run_dir / "rl_config.json", _historical_config(total_timesteps=60000, seed=204))
            _write_json(run_dir / "metrics" / "eval_metrics.json", _historical_eval(avg_reward=33.2, success_rate=0.9))

            with patch("app.services.reports.RUNS_DIR", tmp_path), patch(
                "app.services.reports.HISTORICAL_AGENTMAIL_RUN_IDS",
                ("matrix_random_lidar_v2_60k",),
            ):
                detail = get_inbox_message("run:matrix_random_lidar_v2_60k")

        self.assertEqual(detail.run_id, "matrix_random_lidar_v2_60k")
        self.assertEqual(detail.source, "historical_seed")
        self.assertIn("Hermes Run Report: matrix_random_lidar_v2_60k", detail.html or "")
        self.assertIn("matrix_random_lidar_v2_60k", detail.text or "")

    def test_complete_run_creates_live_agentmail_feed_entry_when_delivery_is_skipped(self):
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

                complete_run("run_report_test", request)
                feed = list_inbox_messages(limit=10)
                detail = get_inbox_message("run:run_report_test")

        self.assertEqual(feed.count, 1)
        self.assertEqual(feed.messages[0].source, "run_report")
        self.assertIn("live", feed.messages[0].labels)
        self.assertIsNone(feed.messages[0].external_message_id)
        self.assertEqual(detail.raw["delivery_status"], "skipped")

    def test_complete_run_preserves_external_agentmail_ids_in_local_feed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with patch("app.services.runner.RUNS_DIR", tmp_path), patch("app.services.reports.RUNS_DIR", tmp_path), patch(
                "app.services.runner.send_report",
                return_value=AgentMailResult(
                    delivery_status="sent",
                    message_id="external-msg-123",
                    thread_id="external-thread-456",
                ),
            ):
                request = CompleteRunRequest(
                    status="completed",
                    config=_metadata()["config"],
                    metrics=_metadata()["metrics"],
                    model_path=_metadata()["model_path"],
                    metrics_path=_metadata()["metrics_path"],
                )

                complete_run("run_report_test", request)
                report = read_report("run_report_test")
                detail = get_inbox_message("run:run_report_test")

        self.assertIsNotNone(report)
        self.assertEqual(report.agentmail_message_id, "external-msg-123")
        self.assertEqual(report.agentmail_thread_id, "external-thread-456")
        self.assertEqual(detail.external_message_id, "external-msg-123")
        self.assertEqual(detail.external_thread_id, "external-thread-456")
        self.assertEqual(detail.source, "run_report")


if __name__ == "__main__":
    unittest.main()
