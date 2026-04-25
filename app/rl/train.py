import argparse
import json
from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.env_checker import check_env

from app.config import RUNS_DIR
from app.rl.config import RunConfig
from app.rl.diagnostics import summarize_episodes
from app.rl.env import RoombaEnv
from app.rl.telemetry import run_policy_episode


DEFAULT_RUN_CONFIG = RunConfig()
DEFAULT_TOTAL_TIMESTEPS = DEFAULT_RUN_CONFIG.total_timesteps


class TrainingProgressCallback(BaseCallback):
    def __init__(
        self,
        metrics_path: Path,
        env_kwargs: dict,
        seed: int,
        eval_seed_offset: int,
        eval_interval: int,
        eval_episodes: int,
    ):
        super().__init__()
        self.metrics_path = metrics_path
        self.env_kwargs = env_kwargs
        self.seed = seed
        self.eval_seed_offset = eval_seed_offset
        self.eval_interval = int(eval_interval)
        self.eval_episodes = int(eval_episodes)
        self.last_eval_timestep = 0

    def _on_training_start(self) -> None:
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        self.metrics_path.write_text("")

    def _on_step(self) -> bool:
        if self.eval_interval <= 0 or self.eval_episodes <= 0:
            return True
        if self.num_timesteps - self.last_eval_timestep < self.eval_interval:
            return True
        self._write_snapshot()
        return True

    def _on_training_end(self) -> None:
        if self.eval_interval > 0 and self.eval_episodes > 0:
            self._write_snapshot()

    def _write_snapshot(self) -> None:
        if self.num_timesteps == self.last_eval_timestep:
            return
        self.last_eval_timestep = self.num_timesteps
        env = RoombaEnv(**self.env_kwargs)
        episode_summaries = []
        for episode_index in range(self.eval_episodes):
            episode_seed = self.seed + self.eval_seed_offset + episode_index
            episode = run_policy_episode(
                model=self.model,
                env=env,
                seed=episode_seed,
            )
            episode_summaries.append(episode["summary"])

        snapshot = summarize_episodes(episode_summaries)
        snapshot["timesteps"] = int(self.num_timesteps)
        with self.metrics_path.open("a") as handle:
            handle.write(json.dumps(snapshot) + "\n")


def _create_ppo_model(env: RoombaEnv, seed: int, device: str, verbose: int) -> PPO:
    model_kwargs = {
        "policy": "MlpPolicy",
        "env": env,
        "verbose": verbose,
        "learning_rate": 3e-4,
        "gamma": 0.99,
        "n_steps": 512,
        "batch_size": 64,
        "ent_coef": 0.01,
        "policy_kwargs": {"net_arch": [128, 128]},
        "seed": seed,
    }

    try:
        return PPO(**model_kwargs, device=device)
    except RuntimeError as exc:
        if device == "mps" and "MPS backend" in str(exc):
            print(f"MPS unavailable for PPO in this environment; falling back to CPU: {exc}")
            return PPO(**model_kwargs, device="cpu")
        raise


def train_policy(
    run_id: str,
    total_timesteps: int = DEFAULT_RUN_CONFIG.total_timesteps,
    seed: int = DEFAULT_RUN_CONFIG.seed,
    room_size: float = DEFAULT_RUN_CONFIG.room_size,
    max_steps: int = DEFAULT_RUN_CONFIG.max_steps,
    dirt_count: int = DEFAULT_RUN_CONFIG.dirt_count,
    device: str = DEFAULT_RUN_CONFIG.device,
    verbose: int = 1,
    eval_seed_offset: int = DEFAULT_RUN_CONFIG.eval_seed_offset,
    obstacle_count: int = DEFAULT_RUN_CONFIG.obstacle_count,
    layout_mode: str = DEFAULT_RUN_CONFIG.layout_mode,
    sensor_mode: str = DEFAULT_RUN_CONFIG.sensor_mode,
    lidar_rays: int = DEFAULT_RUN_CONFIG.lidar_rays,
    progress_eval_interval: int = 0,
    progress_eval_episodes: int = 0,
) -> Path:
    run_dir = RUNS_DIR / run_id
    model_dir = run_dir / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "total_timesteps": total_timesteps,
        "seed": seed,
        "eval_seed_offset": eval_seed_offset,
        "room_size": room_size,
        "max_steps": max_steps,
        "dirt_count": dirt_count,
        "obstacle_count": obstacle_count,
        "layout_mode": layout_mode,
        "sensor_mode": sensor_mode,
        "lidar_rays": lidar_rays,
        "device": device,
        "progress_eval_interval": progress_eval_interval,
        "progress_eval_episodes": progress_eval_episodes,
    }
    (run_dir / "rl_config.json").write_text(json.dumps(config, indent=2))

    env_kwargs = {
        "room_size": room_size,
        "max_steps": max_steps,
        "dirt_count": dirt_count,
        "seed": seed,
        "layout_mode": layout_mode,
        "sensor_mode": sensor_mode,
        "obstacle_count": obstacle_count,
        "lidar_rays": lidar_rays,
        "eval_seed_offset": eval_seed_offset,
    }
    env = RoombaEnv(**env_kwargs)

    check_env(env, warn=True)

    model = _create_ppo_model(env=env, seed=seed, device=device, verbose=verbose)

    progress_callback = None
    if progress_eval_interval > 0 and progress_eval_episodes > 0:
        progress_callback = TrainingProgressCallback(
            metrics_path=run_dir / "metrics" / "train_progress.jsonl",
            env_kwargs=env_kwargs,
            seed=seed,
            eval_seed_offset=eval_seed_offset,
            eval_interval=progress_eval_interval,
            eval_episodes=progress_eval_episodes,
        )

    model.learn(total_timesteps=total_timesteps, callback=progress_callback)

    model_path_without_suffix = model_dir / "roomba_policy"
    model.save(str(model_path_without_suffix))

    return model_dir / "roomba_policy.zip"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--total-timesteps", type=int, default=DEFAULT_RUN_CONFIG.total_timesteps)
    parser.add_argument("--seed", type=int, default=DEFAULT_RUN_CONFIG.seed)
    parser.add_argument("--eval-seed-offset", type=int, default=DEFAULT_RUN_CONFIG.eval_seed_offset)
    parser.add_argument("--room-size", type=float, default=DEFAULT_RUN_CONFIG.room_size)
    parser.add_argument("--max-steps", type=int, default=DEFAULT_RUN_CONFIG.max_steps)
    parser.add_argument("--dirt-count", type=int, default=DEFAULT_RUN_CONFIG.dirt_count)
    parser.add_argument("--obstacle-count", type=int, default=DEFAULT_RUN_CONFIG.obstacle_count)
    parser.add_argument("--layout-mode", default=DEFAULT_RUN_CONFIG.layout_mode, choices=["preset", "random"])
    parser.add_argument("--sensor-mode", default=DEFAULT_RUN_CONFIG.sensor_mode, choices=["oracle", "lidar_local_dirt"])
    parser.add_argument("--lidar-rays", type=int, default=DEFAULT_RUN_CONFIG.lidar_rays)
    parser.add_argument("--device", default=DEFAULT_RUN_CONFIG.device, choices=["auto", "cpu", "cuda", "mps"])
    parser.add_argument("--verbose", type=int, default=1)
    parser.add_argument("--progress-eval-interval", type=int, default=0)
    parser.add_argument("--progress-eval-episodes", type=int, default=0)
    args = parser.parse_args()

    model_path = train_policy(
        run_id=args.run_id,
        total_timesteps=args.total_timesteps,
        seed=args.seed,
        room_size=args.room_size,
        max_steps=args.max_steps,
        dirt_count=args.dirt_count,
        device=args.device,
        verbose=args.verbose,
        eval_seed_offset=args.eval_seed_offset,
        obstacle_count=args.obstacle_count,
        layout_mode=args.layout_mode,
        sensor_mode=args.sensor_mode,
        lidar_rays=args.lidar_rays,
        progress_eval_interval=args.progress_eval_interval,
        progress_eval_episodes=args.progress_eval_episodes,
    )
    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    main()
