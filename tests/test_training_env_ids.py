import json
import shutil
import unittest
from pathlib import Path

from app.rl.eval import evaluate_policy
from app.rl.train import train_policy


class TrainingEnvIdTests(unittest.TestCase):
    def test_train_and_eval_with_clawlab_env_id(self):
        run_id = "clawlab_env_id_unittest"
        run_dir = Path("runs") / run_id
        if run_dir.exists():
            shutil.rmtree(run_dir)

        model_path = train_policy(
            run_id=run_id,
            env_id="ClawLab/ObstacleAvoidanceEasy-v0",
            total_timesteps=1024,
            seed=17,
            max_steps=40,
            device="cpu",
            verbose=0,
        )
        metrics = evaluate_policy(run_id=run_id, episodes=1)

        config = json.loads((run_dir / "rl_config.json").read_text())
        self.assertEqual(config["env_id"], "ClawLab/ObstacleAvoidanceEasy-v0")
        self.assertTrue(model_path.exists())
        self.assertEqual(metrics["episodes"], 1)
        self.assertIn("reward_hacking", metrics)


if __name__ == "__main__":
    unittest.main()
