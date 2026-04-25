import argparse
import json

from stable_baselines3 import PPO

from app.config import RUNS_DIR
from app.rl.config import RunConfig, load_saved_run_config
from app.rl.diagnostics import avg, avg_optional, avg_reward_components, summarize_episodes
from app.rl.factory import make_env
from app.rl.telemetry import run_policy_episode

DEFAULT_RUN_CONFIG = RunConfig()
LEGACY_EVAL_CONFIG = {
    "eval_episodes": DEFAULT_RUN_CONFIG.eval_episodes,
    "seed": 0,
    "eval_seed_offset": 0,
    "room_size": 10.0,
    "max_steps": 200,
    "dirt_count": 3,
    "obstacle_count": 0,
    "layout_mode": "preset",
    "sensor_mode": "oracle",
    "lidar_rays": 0,
    "env_id": None,
}


_avg = avg
_avg_optional = avg_optional
_avg_reward_components = avg_reward_components


def evaluation_seed(seed: int, eval_seed_offset: int, episode_index: int) -> int:
    return seed + eval_seed_offset + episode_index


def _resolve(value, saved_config: dict, key: str, fallback):
    if value is not None:
        return value
    return saved_config.get(key, fallback)


def summarize_generalization(train_metrics: dict, heldout_metrics: dict) -> dict:
    success_rate_gap = float(train_metrics["success_rate"] - heldout_metrics["success_rate"])
    cleaned_dirt_gap = float(
        train_metrics["avg_cleaned_dirt"] - heldout_metrics["avg_cleaned_dirt"]
    )
    return {
        "train_success_rate": train_metrics["success_rate"],
        "heldout_success_rate": heldout_metrics["success_rate"],
        "success_rate_gap": success_rate_gap,
        "cleaned_dirt_gap": cleaned_dirt_gap,
        "possible_memorization": success_rate_gap >= 0.25 or cleaned_dirt_gap >= 1.0,
    }


def evaluate_policy(
    run_id: str,
    episodes: int | None = None,
    room_size: float | None = None,
    max_steps: int | None = None,
    dirt_count: int | None = None,
    seed: int | None = None,
    eval_seed_offset: int | None = None,
    obstacle_count: int | None = None,
    layout_mode: str | None = None,
    sensor_mode: str | None = None,
    lidar_rays: int | None = None,
    env_id: str | None = None,
):
    run_dir = RUNS_DIR / run_id
    model_path = run_dir / "model" / "roomba_policy.zip"
    metrics_dir = run_dir / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    saved_config = load_saved_run_config(run_dir)
    fallback_config = DEFAULT_RUN_CONFIG.__dict__ if saved_config else LEGACY_EVAL_CONFIG
    episodes = int(
        _resolve(episodes, saved_config, "eval_episodes", fallback_config["eval_episodes"])
    )
    room_size = float(_resolve(room_size, saved_config, "room_size", fallback_config["room_size"]))
    max_steps = int(_resolve(max_steps, saved_config, "max_steps", fallback_config["max_steps"]))
    dirt_count = int(_resolve(dirt_count, saved_config, "dirt_count", fallback_config["dirt_count"]))
    seed = int(_resolve(seed, saved_config, "seed", fallback_config["seed"]))
    eval_seed_offset = int(
        _resolve(
            eval_seed_offset,
            saved_config,
            "eval_seed_offset",
            fallback_config["eval_seed_offset"],
        )
    )
    obstacle_count = int(
        _resolve(obstacle_count, saved_config, "obstacle_count", fallback_config["obstacle_count"])
    )
    layout_mode = str(
        _resolve(layout_mode, saved_config, "layout_mode", fallback_config["layout_mode"])
    )
    sensor_mode = str(
        _resolve(sensor_mode, saved_config, "sensor_mode", fallback_config["sensor_mode"])
    )
    lidar_rays = int(_resolve(lidar_rays, saved_config, "lidar_rays", fallback_config["lidar_rays"]))
    env_id = _resolve(env_id, saved_config, "env_id", fallback_config.get("env_id"))

    env = make_env(
        env_id=env_id,
        room_size=room_size,
        max_steps=max_steps,
        dirt_count=dirt_count,
        seed=seed + eval_seed_offset,
        layout_mode=layout_mode,
        sensor_mode=sensor_mode,
        obstacle_count=obstacle_count,
        lidar_rays=lidar_rays,
        eval_seed_offset=eval_seed_offset,
    )

    model = PPO.load(str(model_path))
    if env.observation_space.shape != model.observation_space.shape:
        raise ValueError(
            "Evaluation env observation shape "
            f"{env.observation_space.shape} does not match model "
            f"{model.observation_space.shape}. Pass the run's layout and sensor flags."
        )

    episode_summaries = []

    for episode_index in range(episodes):
        episode = run_policy_episode(
            model=model,
            env=env,
            seed=evaluation_seed(seed, eval_seed_offset, episode_index),
        )
        episode_summaries.append(episode["summary"])

    metrics = summarize_episodes(episode_summaries)

    metrics_path = metrics_dir / "eval_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2))
    episodes_path = metrics_dir / "eval_episodes.json"
    episodes_path.write_text(json.dumps(episode_summaries, indent=2))

    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--episodes", type=int)
    parser.add_argument("--room-size", type=float)
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--dirt-count", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--eval-seed-offset", type=int)
    parser.add_argument("--obstacle-count", type=int)
    parser.add_argument("--layout-mode", choices=["preset", "random"])
    parser.add_argument("--sensor-mode", choices=["oracle", "lidar_local_dirt"])
    parser.add_argument("--lidar-rays", type=int)
    parser.add_argument("--env-id")
    args = parser.parse_args()

    metrics = evaluate_policy(
        run_id=args.run_id,
        episodes=args.episodes,
        room_size=args.room_size,
        max_steps=args.max_steps,
        dirt_count=args.dirt_count,
        seed=args.seed,
        eval_seed_offset=args.eval_seed_offset,
        obstacle_count=args.obstacle_count,
        layout_mode=args.layout_mode,
        sensor_mode=args.sensor_mode,
        lidar_rays=args.lidar_rays,
        env_id=args.env_id,
    )

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
