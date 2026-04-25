import unittest
from unittest.mock import patch

from app.schemas.run import RunReport
from app.services.hermes import post_lesson


class HermesReportTests(unittest.TestCase):
    def test_lesson_uses_execution_status_and_real_env_id(self):
        report = RunReport(
            run_id="run_low_success",
            status="completed",
            ended_at="2026-04-25T20:02:00+00:00",
            template="ClawLab/FullCleaning-v0",
            algo="PPO",
            config={
                "env_id": "ClawLab/FullCleaning-v0",
                "total_timesteps": 1000,
                "room_size": 10.0,
                "max_steps": 200,
                "dirt_count": 6,
            },
            mean_return=-2.333,
            best_return=0.0,
            model_summary="low-success run",
            markdown="low-success run",
            created_at="2026-04-25T20:02:00+00:00",
        )

        with patch("app.services.hermes.config.SLACK_BOT_TOKEN", "token"), patch(
            "app.services.hermes.config.SLACK_CHANNEL_ID", "channel"
        ), patch("app.services.hermes._post_message", return_value="123.456") as post_message:
            result = post_lesson(report)

        self.assertEqual(result.status, "posted")
        blocks = post_message.call_args.kwargs["blocks"]
        fields = blocks[1]["fields"]
        self.assertEqual(fields[0]["text"], "*env_id*\n`ClawLab/FullCleaning-v0`")
        self.assertIn("completed | reward -2.333 | policy success 0%", fields[1]["text"])
        self.assertNotIn("result*\nsuccess |", fields[1]["text"])


if __name__ == "__main__":
    unittest.main()
