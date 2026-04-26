import unittest

from app.rl.config import RunConfig
from app.schemas.run import CreateRunRequest


class RunConfigTests(unittest.TestCase):
    def test_run_config_defaults_to_randomized_generalization_mode(self):
        config = RunConfig()
        self.assertEqual(config.total_timesteps, 60_000)
        self.assertEqual(config.layout_mode, "random")
        self.assertEqual(config.sensor_mode, "lidar_local_dirt")
        self.assertEqual(config.eval_seed_offset, 10_000)

    def test_api_request_exposes_layout_and_sensor_mode(self):
        request = CreateRunRequest()
        self.assertEqual(request.layout_mode, "random")
        self.assertEqual(request.sensor_mode, "lidar_local_dirt")


if __name__ == "__main__":
    unittest.main()
