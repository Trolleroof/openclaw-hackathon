import json
import shutil
import unittest
from pathlib import Path

import numpy as np
from stable_baselines3.common.env_checker import check_env

from app.config import RUNS_DIR
from app.rl.env import RoombaEnv
from app.rl.eval import evaluate_policy
from app.rl.layouts import CircleObstacle
from app.rl.train import DEFAULT_TOTAL_TIMESTEPS, train_policy
from app.rl.visualize import generate_run_artifacts
from app.schemas.run import CreateRunRequest


class Phase1RLTests(unittest.TestCase):
    def test_observation_exposes_normalized_navigation_features(self):
        env = RoombaEnv(room_size=10.0, max_steps=20, dirt_count=3, seed=7)
        obs, _ = env.reset(seed=7)

        self.assertEqual(obs.shape, (23,))
        self.assertTrue(np.all(obs >= -1.0))
        self.assertTrue(np.all(obs <= 1.0))

    def test_random_layout_env_changes_dirt_by_seed(self):
        a = RoombaEnv(layout_mode="random", seed=1)
        b = RoombaEnv(layout_mode="random", seed=2)
        a.reset(seed=1)
        b.reset(seed=2)

        self.assertFalse(np.allclose(a.dirt, b.dirt))

    def test_lidar_local_dirt_mode_removes_oracle_dirt_vectors(self):
        env = RoombaEnv(layout_mode="random", sensor_mode="lidar_local_dirt", lidar_rays=16, seed=1)
        obs, _ = env.reset(seed=1)

        self.assertEqual(obs.shape, (27,))
        self.assertTrue(np.all(obs >= -1.0))
        self.assertTrue(np.all(obs <= 1.0))

    def test_default_training_budget_is_scaled_for_2d_runs(self):
        self.assertEqual(DEFAULT_TOTAL_TIMESTEPS, 200_000)
        self.assertEqual(CreateRunRequest().total_timesteps, 200_000)
        self.assertEqual(CreateRunRequest().dirt_count, 6)

    def test_env_passes_stable_baselines_checker(self):
        env = RoombaEnv(room_size=6.0, max_steps=20, dirt_count=2, seed=7)

        check_env(env, warn=True)

    def test_rgb_array_render_returns_fixed_size_image(self):
        env = RoombaEnv(
            room_size=4.0,
            max_steps=20,
            dirt_count=1,
            seed=7,
            render_mode="rgb_array",
        )
        env.reset(seed=7)

        image = env.render()

        self.assertEqual(image.shape, (400, 400, 3))
        self.assertEqual(image.dtype, np.uint8)

    def test_moving_toward_nearest_dirt_gets_progress_reward(self):
        forward_env = RoombaEnv(room_size=10.0, max_steps=20, dirt_count=1, seed=7)
        forward_env.reset(seed=7)
        _, forward_reward, _, _, _ = forward_env.step(0)

        turning_env = RoombaEnv(room_size=10.0, max_steps=20, dirt_count=1, seed=7)
        turning_env.reset(seed=7)
        _, turn_reward, _, _, _ = turning_env.step(1)

        self.assertGreater(forward_reward, turn_reward)

    def test_turning_toward_nearest_dirt_gets_alignment_reward(self):
        toward_env = RoombaEnv(room_size=10.0, max_steps=20, dirt_count=1, seed=7)
        toward_env.reset(seed=7)
        _, toward_reward, _, _, _ = toward_env.step(1)

        away_env = RoombaEnv(room_size=10.0, max_steps=20, dirt_count=1, seed=7)
        away_env.reset(seed=7)
        _, away_reward, _, _, _ = away_env.step(2)

        self.assertGreater(toward_reward, away_reward)

    def test_step_info_includes_reward_breakdown(self):
        env = RoombaEnv(room_size=10.0, max_steps=20, dirt_count=1, seed=7)
        env.reset(seed=7)

        _, reward, _, _, info = env.step(0)

        components = info["reward_components"]
        self.assertIn("step_penalty", components)
        self.assertIn("progress", components)
        self.assertIn("alignment", components)
        self.assertAlmostEqual(sum(components.values()), reward)

    def test_oracle_observation_includes_obstacle_clearance(self):
        clear_env = RoombaEnv(room_size=10.0, max_steps=20, dirt_count=1, seed=7)
        clear_env.reset(seed=7)
        clear_env.robot = np.array([1.0, 1.0], dtype=np.float32)
        clear_env.heading = 0.0
        clear_obs = clear_env._obs()

        blocked_env = RoombaEnv(room_size=10.0, max_steps=20, dirt_count=1, seed=7)
        blocked_env.reset(seed=7)
        blocked_env.robot = np.array([1.0, 1.0], dtype=np.float32)
        blocked_env.heading = 0.0
        blocked_env.obstacles = [CircleObstacle(x=1.8, y=1.0, radius=0.25)]
        blocked_obs = blocked_env._obs()

        self.assertLess(blocked_obs[10], clear_obs[10])

    def test_wall_collision_blocks_forward_motion(self):
        env = RoombaEnv(room_size=10.0, max_steps=20, dirt_count=1, seed=7)
        env.reset(seed=7)
        env.robot = np.array([9.95, 1.0], dtype=np.float32)
        env.heading = 0.0
        previous_robot = env.robot.copy()

        _, _, _, _, info = env.step(0)

        np.testing.assert_allclose(env.robot, previous_robot)
        self.assertTrue(info["hit_wall"])
        self.assertLessEqual(info["reward_components"]["wall_penalty"], -3.0)

    def test_obstacle_collision_blocks_forward_motion(self):
        env = RoombaEnv(room_size=10.0, max_steps=20, dirt_count=1, seed=7)
        env.reset(seed=7)
        env.robot = np.array([1.0, 1.0], dtype=np.float32)
        env.heading = 0.0
        env.obstacles = [CircleObstacle(x=1.3, y=1.0, radius=0.25)]
        previous_robot = env.robot.copy()

        _, _, _, _, info = env.step(0)

        np.testing.assert_allclose(env.robot, previous_robot)
        self.assertTrue(info["hit_obstacle"])
        self.assertLessEqual(info["reward_components"]["obstacle_penalty"], -5.0)

    def test_short_train_and_eval_writes_phase1_artifacts(self):
        run_id = "phase1_unittest"
        run_dir = Path("runs") / run_id
        if run_dir.exists():
            shutil.rmtree(run_dir)

        model_path = train_policy(
            run_id=run_id,
            total_timesteps=1024,
            seed=3,
            room_size=5.0,
            max_steps=50,
            dirt_count=1,
            device="cpu",
            layout_mode="preset",
            sensor_mode="oracle",
            lidar_rays=0,
        )
        metrics = evaluate_policy(
            run_id=run_id,
            episodes=2,
        )

        self.assertTrue(model_path.exists())
        self.assertTrue((run_dir / "rl_config.json").exists())
        self.assertTrue((run_dir / "metrics" / "eval_metrics.json").exists())
        self.assertTrue((run_dir / "metrics" / "eval_episodes.json").exists())
        episodes = json.loads((run_dir / "metrics" / "eval_episodes.json").read_text())
        self.assertEqual(episodes[0]["seed"], 10_003)
        self.assertEqual(metrics["episodes"], 2)
        self.assertIn("success_rate", metrics)
        self.assertIn("avg_cleaned_dirt", metrics)
        self.assertIn("avg_reward_components", metrics)

    def test_training_writes_progress_telemetry(self):
        run_id = "phase1_progress_unittest"
        run_dir = Path("runs") / run_id
        if run_dir.exists():
            shutil.rmtree(run_dir)

        train_policy(
            run_id=run_id,
            total_timesteps=1024,
            seed=11,
            room_size=5.0,
            max_steps=50,
            dirt_count=1,
            device="cpu",
            verbose=0,
            layout_mode="preset",
            sensor_mode="oracle",
            lidar_rays=0,
            progress_eval_interval=512,
            progress_eval_episodes=1,
        )

        progress_path = run_dir / "metrics" / "train_progress.jsonl"
        self.assertTrue(progress_path.exists())
        snapshots = [
            json.loads(line)
            for line in progress_path.read_text().splitlines()
            if line.strip()
        ]
        self.assertGreaterEqual(len(snapshots), 2)
        self.assertIn("timesteps", snapshots[-1])
        self.assertIn("avg_cleaned_dirt", snapshots[-1])
        self.assertIn("avg_reward_components", snapshots[-1])
        self.assertIn("reward_hacking", snapshots[-1])
        self.assertIn("low_clean_high_reward", snapshots[-1]["reward_hacking"])

    def test_visualization_writes_gif_and_trajectory(self):
        run_id = "phase1_unittest"
        model_path = RUNS_DIR / run_id / "model" / "roomba_policy.zip"
        config_path = RUNS_DIR / run_id / "rl_config.json"
        if not model_path.exists() or not config_path.exists():
            train_policy(
                run_id=run_id,
                total_timesteps=1024,
                seed=3,
                room_size=5.0,
                max_steps=50,
                dirt_count=1,
                device="cpu",
                verbose=0,
                layout_mode="preset",
                sensor_mode="oracle",
                lidar_rays=0,
            )

        artifacts = generate_run_artifacts(
            run_id=run_id,
            seed=0,
            episodes=1,
            fps=6,
            hold_final_frames=3,
            room_size=5.0,
            max_steps=50,
            dirt_count=1,
            layout_mode="preset",
            sensor_mode="oracle",
            lidar_rays=0,
        )

        self.assertTrue(Path(artifacts["gif_paths"][0]).exists())
        self.assertTrue(Path(artifacts["trajectory_paths"][0]).exists())
        self.assertEqual(artifacts["fps"], 6)
        self.assertEqual(artifacts["hold_final_frames"], 3)
        self.assertEqual(artifacts["layout_mode"], "preset")
        self.assertEqual(artifacts["sensor_mode"], "oracle")

    def test_visualization_uses_saved_run_config_by_default(self):
        run_id = "phase1_unittest"
        model_path = RUNS_DIR / run_id / "model" / "roomba_policy.zip"
        config_path = RUNS_DIR / run_id / "rl_config.json"
        if not model_path.exists() or not config_path.exists():
            train_policy(
                run_id=run_id,
                total_timesteps=1024,
                seed=3,
                room_size=5.0,
                max_steps=50,
                dirt_count=1,
                device="cpu",
                verbose=0,
                layout_mode="preset",
                sensor_mode="oracle",
                lidar_rays=0,
            )

        artifacts = generate_run_artifacts(run_id=run_id, episodes=1, hold_final_frames=1)

        self.assertEqual(artifacts["seed"], 10_003)
        self.assertEqual(artifacts["layout_mode"], "preset")
        self.assertEqual(artifacts["sensor_mode"], "oracle")


if __name__ == "__main__":
    unittest.main()
