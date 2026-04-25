import argparse
from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env

from app.config import RUNS_DIR
from app.rl.env import RoombaEnv


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
    total_timesteps: int = 30_000,
    seed: int = 42,
    room_size: float = 10.0,
    max_steps: int = 200,
    dirt_count: int = 3,
    device: str = "auto",
    verbose: int = 1,
) -> Path:
    run_dir = RUNS_DIR / run_id
    model_dir = run_dir / "model"
    model_dir.mkdir(parents=True, exist_ok=True)

    env = RoombaEnv(
        room_size=room_size,
        max_steps=max_steps,
        dirt_count=dirt_count,
        seed=seed,
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
    parser.add_argument("--total-timesteps", type=int, default=30_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--room-size", type=float, default=10.0)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--dirt-count", type=int, default=3)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda", "mps"])
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
    )
    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    main()
