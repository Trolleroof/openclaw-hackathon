import shutil
import unittest
from pathlib import Path

import numpy as np
from stable_baselines3.common.env_checker import check_env

from app.rl.env import RoombaEnv
from app.rl.eval import evaluate_policy
from app.rl.train import train_policy


class Phase1RLTests(unittest.TestCase):
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
        )
        metrics = evaluate_policy(
            run_id=run_id,
            episodes=2,
            room_size=5.0,
            max_steps=50,
            dirt_count=1,
        )

        self.assertTrue(model_path.exists())
        self.assertTrue((run_dir / "metrics" / "eval_metrics.json").exists())
        self.assertEqual(metrics["episodes"], 2)
        self.assertIn("success_rate", metrics)


if __name__ == "__main__":
    unittest.main()
