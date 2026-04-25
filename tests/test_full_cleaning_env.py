import unittest

import numpy as np

from app.rl.diagnostics import summarize_episodes
from app.rl.envs.full_cleaning import FullCleaningEnv
from app.rl.layouts import CircleObstacle
from app.rl.telemetry import run_policy_episode


class AlwaysForwardPolicy:
    def predict(self, obs, deterministic=True):
        return 0, None


class WallCollisionEnv(FullCleaningEnv):
    def reset(self, seed=None, options=None):
        obs, info = super().reset(seed=seed, options=options)
        self.robot = np.array([self.size - 0.01, 1.0], dtype=np.float32)
        self.heading = 0.0
        return self._obs(), info


class FullCleaningEnvTests(unittest.TestCase):
    def test_cleaning_dirt_removes_it(self):
        env = FullCleaningEnv(
            room_size=6.0,
            max_steps=20,
            dirt_count=2,
            clean_radius=0.4,
            layout_mode="preset",
            obstacle_count=0,
            seed=7,
        )
        env.reset(seed=7)
        env.robot = env.dirt[0].copy()

        _, reward, terminated, _, info = env.step(1)

        self.assertFalse(terminated)
        self.assertEqual(info["cleaned_count"], 1)
        self.assertEqual(info["remaining_dirt"], 1)
        self.assertEqual(len(env.dirt), 1)
        self.assertGreater(info["reward_components"]["clean"], 0.0)
        self.assertAlmostEqual(sum(info["reward_components"].values()), reward)

    def test_all_dirt_cleaned_terminates_with_success_bonus(self):
        env = FullCleaningEnv(
            room_size=6.0,
            max_steps=20,
            dirt_count=1,
            clean_radius=0.4,
            layout_mode="preset",
            obstacle_count=0,
            seed=7,
        )
        env.reset(seed=7)
        env.robot = env.dirt[0].copy()

        _, _, terminated, truncated, info = env.step(1)

        self.assertTrue(terminated)
        self.assertFalse(truncated)
        self.assertEqual(info["remaining_dirt"], 0)
        self.assertGreaterEqual(info["reward_components"]["terminal"], 15.0)

    def test_forced_collision_abuse_appears_in_diagnostics_telemetry(self):
        env = WallCollisionEnv(
            room_size=6.0,
            max_steps=5,
            dirt_count=1,
            layout_mode="preset",
            obstacle_count=0,
            seed=7,
        )

        result = run_policy_episode(
            AlwaysForwardPolicy(),
            env,
            seed=7,
            include_steps=True,
        )
        metrics = summarize_episodes([result["summary"]])

        self.assertEqual(result["summary"]["wall_hits"], 5)
        self.assertTrue(metrics["reward_hacking"]["collision_abuse"])
        self.assertIn("wall_penalty", result["summary"]["reward_totals"])
        self.assertLess(result["summary"]["reward_totals"]["wall_penalty"], 0.0)
        self.assertTrue(all(step["hit_wall"] for step in result["steps"]))

    def test_lidar_local_dirt_observation_has_obstacle_aware_dirt_vector(self):
        clear_env = FullCleaningEnv(
            room_size=6.0,
            max_steps=20,
            dirt_count=1,
            dirt_sensor_radius=4.0,
            lidar_rays=4,
            obstacle_count=0,
            seed=7,
        )
        clear_env.reset(seed=7)
        clear_env.robot = np.array([2.0, 2.0], dtype=np.float32)
        clear_env.heading = 0.0
        clear_env.dirt = np.array([[4.0, 2.0]], dtype=np.float32)
        clear_obs = clear_env._obs()

        blocked_env = FullCleaningEnv(
            room_size=6.0,
            max_steps=20,
            dirt_count=1,
            dirt_sensor_radius=4.0,
            lidar_rays=4,
            obstacle_count=0,
            seed=7,
        )
        blocked_env.reset(seed=7)
        blocked_env.robot = np.array([2.0, 2.0], dtype=np.float32)
        blocked_env.heading = 0.0
        blocked_env.dirt = np.array([[4.0, 2.0]], dtype=np.float32)
        blocked_env.obstacles = [CircleObstacle(x=3.0, y=2.0, radius=0.3)]
        blocked_obs = blocked_env._obs()

        self.assertTrue(blocked_env.observation_space.contains(blocked_obs))
        self.assertGreater(clear_obs[4], 0.0)
        self.assertGreater(clear_obs[6], 0.0)
        np.testing.assert_allclose(blocked_obs[4:7], np.zeros(3), atol=1e-6)
        self.assertLess(blocked_obs[7], clear_obs[7])


if __name__ == "__main__":
    unittest.main()
