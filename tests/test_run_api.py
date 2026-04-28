import unittest
from unittest.mock import patch

from pydantic import ValidationError

from app.main import create_training_run, get_env, get_envs
from app.schemas.run import CreateRunRequest, RunResponse


class RunApiTests(unittest.TestCase):
    def test_create_run_request_validates_env_id(self):
        request = CreateRunRequest(env_id="ApolloLabs/PointNavigation-v0")

        self.assertEqual(request.env_id, "ApolloLabs/PointNavigation-v0")
        with self.assertRaises(ValidationError):
            CreateRunRequest(env_id="Unknown/Env-v0")

    def test_list_envs_endpoint(self):
        response = get_envs()

        env_ids = {item["id"] for item in response["envs"]}
        self.assertIn("ApolloLabs/FullCleaning-v0", env_ids)

    def test_describe_env_endpoint(self):
        payload = get_env("ApolloLabs/FullCleaning-v0")

        self.assertEqual(payload["id"], "ApolloLabs/FullCleaning-v0")
        self.assertIn("clean", payload["reward_components"])

    def test_create_run_metadata_includes_env_id(self):
        response_payload = RunResponse(
            run_id="run_test",
            status="completed",
            config={"env_id": "ApolloLabs/PointNavigation-v0"},
            metrics={},
            model_path="runs/run_test/model/roomba_policy.zip",
            metrics_path="runs/run_test/metrics/combined_metrics.json",
            error=None,
        )
        with patch("app.main.create_run", return_value=response_payload):
            response = create_training_run(
                CreateRunRequest(
                    env_id="ApolloLabs/PointNavigation-v0",
                    total_timesteps=1000,
                    eval_episodes=1,
                )
            )

        self.assertEqual(response.config["env_id"], "ApolloLabs/PointNavigation-v0")


if __name__ == "__main__":
    unittest.main()
