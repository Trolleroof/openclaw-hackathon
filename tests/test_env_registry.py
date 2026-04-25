import unittest

import gymnasium as gym

import app.rl.envs
from app.rl.envs.registry import describe_env, list_envs


class EnvRegistryTests(unittest.TestCase):
    def test_clawlab_envs_can_be_made_by_id(self):
        env_ids = [
            "ClawLab/ObstacleAvoidance-v0",
            "ClawLab/PointNavigation-v0",
            "ClawLab/DirtSeeking-v0",
            "ClawLab/FullCleaning-v0",
        ]
        for env_id in env_ids:
            env = gym.make(env_id)
            obs, _ = env.reset(seed=123)
            self.assertTrue(env.observation_space.contains(obs), env_id)
            env.close()

    def test_scaled_variants_are_registered(self):
        env = gym.make("ClawLab/FullCleaningDenseObstacles-v0")
        obs, _ = env.reset(seed=123)

        self.assertTrue(env.observation_space.contains(obs))
        env.close()

    def test_registry_describes_envs(self):
        envs = list_envs()
        ids = {item["id"] for item in envs}

        self.assertIn("ClawLab/FullCleaning-v0", ids)
        description = describe_env("ClawLab/FullCleaning-v0")
        self.assertIn("clean", description["reward_components"])


if __name__ == "__main__":
    unittest.main()
