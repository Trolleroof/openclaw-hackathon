import argparse
import json
from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env

from app.config import RUNS_DIR
from app.rl.config import RunConfig
from app.rl.env import RoombaEnv


DEFAULT_RUN_CONFIG = RunConfig()
DEFAULT_TOTAL_TIMESTEPS = DEFAULT_RUN_CONFIG.total_timesteps


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
    }
    (run_dir / "rl_config.json").write_text(json.dumps(config, indent=2))

    env = RoombaEnv(
        room_size=room_size,
        max_steps=max_steps,
        dirt_count=dirt_count,
        seed=seed,
        layout_mode=layout_mode,
        sensor_mode=sensor_mode,
        obstacle_count=obstacle_count,
        lidar_rays=lidar_rays,
        eval_seed_offset=eval_seed_offset,
    )

    check_env(env, warn=True)

    model = _create_ppo_model(env=env, seed=seed, device=device, verbose=verbose)

    model.learn(total_timesteps=total_timesteps)

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
    )
    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    main()
