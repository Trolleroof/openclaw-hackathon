import unittest

import numpy as np

from app.rl.envs.point_navigation import PointNavigationEnv
from app.rl.layouts import CircleObstacle


class PointNavigationEnvTests(unittest.TestCase):
    def test_target_is_randomized_by_seed(self):
        env = PointNavigationEnv(room_size=6.0, max_steps=20, obstacle_count=0)

        env.reset(seed=11)
        first_target = env.target.copy()
        env.reset(seed=12)
        second_target = env.target.copy()

        self.assertFalse(np.allclose(first_target, second_target))
        self.assertTrue(env.observation_space.contains(env._obs()))

    def test_moving_toward_target_improves_reward_over_turning_away(self):
        forward_env = PointNavigationEnv(
            room_size=6.0,
            max_steps=20,
            obstacle_count=0,
            turn_angle=0.5,
        )
        forward_env.reset(seed=7)
        forward_env.robot = np.array([1.0, 1.0], dtype=np.float32)
        forward_env.heading = 0.0
        forward_env.target = np.array([3.0, 1.0], dtype=np.float32)
        _, forward_reward, _, _, forward_info = forward_env.step(0)

        turn_env = PointNavigationEnv(
            room_size=6.0,
            max_steps=20,
            obstacle_count=0,
            turn_angle=0.5,
        )
        turn_env.reset(seed=7)
        turn_env.robot = np.array([1.0, 1.0], dtype=np.float32)
        turn_env.heading = 0.0
        turn_env.target = np.array([3.0, 1.0], dtype=np.float32)
        _, turn_reward, _, _, turn_info = turn_env.step(2)

        self.assertGreater(forward_reward, turn_reward)
        self.assertGreater(forward_info["reward_components"]["progress"], 0.0)
        self.assertLess(turn_info["reward_components"]["turn_penalty"], 0.0)

    def test_reaching_target_terminates_successfully(self):
        env = PointNavigationEnv(
            room_size=6.0,
            max_steps=20,
            obstacle_count=0,
            forward_step=0.3,
            target_radius=0.25,
        )
        env.reset(seed=7)
        env.robot = np.array([1.0, 1.0], dtype=np.float32)
        env.heading = 0.0
        env.target = np.array([1.2, 1.0], dtype=np.float32)

        _, reward, terminated, truncated, info = env.step(0)

        self.assertTrue(terminated)
        self.assertFalse(truncated)
        self.assertTrue(info["success"])
        self.assertGreater(info["reward_components"]["success"], 0.0)
        self.assertGreater(reward, 0.0)

    def test_collision_flags_are_surfaced(self):
        env = PointNavigationEnv(
            room_size=6.0,
            max_steps=20,
            obstacle_count=0,
            forward_step=0.3,
        )
        env.reset(seed=7)
        env.robot = np.array([1.0, 1.0], dtype=np.float32)
        env.heading = 0.0
        env.target = np.array([3.0, 1.0], dtype=np.float32)
        env.obstacles = [CircleObstacle(x=1.25, y=1.0, radius=0.2)]
        previous_robot = env.robot.copy()

        _, _, _, _, info = env.step(0)

        np.testing.assert_allclose(env.robot, previous_robot)
        self.assertTrue(info["hit_obstacle"])
        self.assertFalse(info["hit_wall"])
        self.assertIn("obstacle_penalty", info["reward_components"])
        self.assertLess(info["reward_components"]["obstacle_penalty"], 0.0)


if __name__ == "__main__":
    unittest.main()
