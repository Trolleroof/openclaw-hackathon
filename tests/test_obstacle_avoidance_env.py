import unittest

import numpy as np

from app.rl.envs.obstacle_avoidance import ObstacleAvoidanceEnv
from app.rl.layouts import CircleObstacle
from app.rl.telemetry import run_policy_episode


class ObstacleAvoidanceEnvTests(unittest.TestCase):
    def test_reset_returns_valid_observation(self):
        env = ObstacleAvoidanceEnv(room_size=6.0, max_steps=20, obstacle_count=3, seed=7)

        obs, info = env.reset(seed=7)

        self.assertTrue(env.observation_space.contains(obs))
        self.assertEqual(info["steps"], 0)
        self.assertEqual(len(env.dirt), 0)

    def test_forward_collision_is_blocked(self):
        env = ObstacleAvoidanceEnv(room_size=6.0, max_steps=20, obstacle_count=0, seed=7)
        env.reset(seed=7)
        env.robot = np.array([1.0, 1.0], dtype=np.float32)
        env.heading = 0.0
        env.obstacles = [CircleObstacle(x=1.25, y=1.0, radius=0.2)]
        previous_robot = env.robot.copy()

        _, _, _, _, info = env.step(0)

        np.testing.assert_allclose(env.robot, previous_robot)
        self.assertTrue(info["hit_obstacle"])

    def test_obstacle_collision_adds_negative_obstacle_penalty(self):
        env = ObstacleAvoidanceEnv(room_size=6.0, max_steps=20, obstacle_count=0, seed=7)
        env.reset(seed=7)
        env.robot = np.array([1.0, 1.0], dtype=np.float32)
        env.heading = 0.0
        env.obstacles = [CircleObstacle(x=1.25, y=1.0, radius=0.2)]

        _, reward, _, _, info = env.step(0)

        components = info["reward_components"]
        self.assertLess(components["obstacle_penalty"], 0.0)
        self.assertAlmostEqual(sum(components.values()), reward)

    def test_turning_in_place_until_timeout_is_not_success(self):
        env = ObstacleAvoidanceEnv(
            room_size=6.0,
            max_steps=3,
            obstacle_count=0,
            min_success_path_length=1.0,
            seed=7,
        )
        env.reset(seed=7)

        for _ in range(3):
            _, reward, terminated, _, info = env.step(1)

        self.assertTrue(terminated)
        self.assertFalse(info["success"])
        self.assertLess(info["reward_components"]["idle_penalty"], 0.0)
        self.assertLess(reward, 0.0)

    def test_survival_success_requires_real_movement(self):
        env = ObstacleAvoidanceEnv(
            room_size=6.0,
            max_steps=3,
            obstacle_count=0,
            min_success_path_length=0.5,
            seed=7,
        )
        env.reset(seed=7)
        env.robot = np.array([2.0, 2.0], dtype=np.float32)
        env.heading = 0.0

        for _ in range(3):
            _, _, terminated, _, info = env.step(0)

        self.assertTrue(terminated)
        self.assertTrue(info["success"])
        self.assertGreaterEqual(info["path_length"], 0.5)

    def test_random_policy_episode_produces_telemetry_keys(self):
        env = ObstacleAvoidanceEnv(room_size=6.0, max_steps=5, obstacle_count=2, seed=7)

        result = run_policy_episode(None, env, seed=7, include_steps=True)

        summary = result["summary"]
        self.assertIn("steps", summary)
        self.assertIn("obstacle_hits", summary)
        self.assertIn("reward_totals", summary)
        self.assertIn("clearance_reward", summary["reward_totals"])
        self.assertIn("survival_bonus", summary["reward_totals"])
        self.assertGreaterEqual(len(result["steps"]), 1)
        self.assertIn("hit_obstacle", result["steps"][0])


if __name__ == "__main__":
    unittest.main()
