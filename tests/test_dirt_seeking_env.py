import unittest

import numpy as np

from app.rl.envs.dirt_seeking import DirtSeekingEnv
from app.rl.layouts import CircleObstacle


class DirtSeekingEnvTests(unittest.TestCase):
    def test_dirt_positions_change_with_random_seeds(self):
        env = DirtSeekingEnv(room_size=6.0, dirt_count=3, obstacle_count=1)

        env.reset(seed=11)
        first_dirt = env.dirt.copy()

        env.reset(seed=12)
        second_dirt = env.dirt.copy()

        self.assertFalse(np.allclose(first_dirt, second_dirt))

    def test_obstacle_blocks_dirt_proximity_signal(self):
        env = DirtSeekingEnv(room_size=6.0, dirt_count=1, obstacle_count=0)
        env.reset(seed=7)
        env.robot = np.array([1.0, 1.0], dtype=np.float32)
        env.heading = 0.0
        env.dirt = np.array([[3.0, 1.0]], dtype=np.float32)
        env.obstacles = [CircleObstacle(x=2.0, y=1.0, radius=0.35)]

        obs = env._obs()

        proximity = obs[3:6]
        np.testing.assert_allclose(proximity, np.zeros(3, dtype=np.float32))

    def test_reaching_dirt_emits_found_dirt_and_terminates(self):
        env = DirtSeekingEnv(room_size=6.0, dirt_count=1, obstacle_count=0)
        env.reset(seed=7)
        env.robot = np.array([1.0, 1.0], dtype=np.float32)
        env.heading = 0.0
        env.dirt = np.array([[1.2, 1.0]], dtype=np.float32)

        _, _, terminated, truncated, info = env.step(0)

        self.assertTrue(terminated)
        self.assertFalse(truncated)
        self.assertTrue(info["found_dirt"])
        self.assertEqual(info["remaining_dirt"], 0)
        self.assertGreater(info["reward_components"]["found_dirt"], 0.0)

    def test_moving_toward_visible_dirt_reward_exceeds_turning_away(self):
        toward_env = DirtSeekingEnv(room_size=6.0, dirt_count=1, obstacle_count=0)
        toward_env.reset(seed=7)
        toward_env.robot = np.array([1.0, 1.0], dtype=np.float32)
        toward_env.heading = 0.0
        toward_env.dirt = np.array([[3.0, 1.0]], dtype=np.float32)

        away_env = DirtSeekingEnv(room_size=6.0, dirt_count=1, obstacle_count=0)
        away_env.reset(seed=7)
        away_env.robot = toward_env.robot.copy()
        away_env.heading = toward_env.heading
        away_env.dirt = toward_env.dirt.copy()

        _, toward_reward, _, _, toward_info = toward_env.step(0)
        _, away_reward, _, _, away_info = away_env.step(1)

        self.assertGreater(toward_reward, away_reward)
        self.assertGreater(toward_info["reward_components"]["dirt_progress"], 0.0)
        self.assertEqual(away_info["reward_components"]["dirt_progress"], 0.0)


if __name__ == "__main__":
    unittest.main()
