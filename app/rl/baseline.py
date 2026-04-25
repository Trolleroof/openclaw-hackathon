import argparse
import json

from app.rl.config import RunConfig
from app.rl.eval import _avg, _avg_optional, _avg_reward_components, evaluation_seed
from app.rl.factory import make_env
from app.rl.telemetry import run_policy_episode

DEFAULT_RUN_CONFIG = RunConfig()


def evaluate_random_baseline(
    episodes: int = DEFAULT_RUN_CONFIG.eval_episodes,
    room_size: float = DEFAULT_RUN_CONFIG.room_size,
    max_steps: int = DEFAULT_RUN_CONFIG.max_steps,
    dirt_count: int = DEFAULT_RUN_CONFIG.dirt_count,
    seed: int = DEFAULT_RUN_CONFIG.seed,
    eval_seed_offset: int = DEFAULT_RUN_CONFIG.eval_seed_offset,
    obstacle_count: int = DEFAULT_RUN_CONFIG.obstacle_count,
    layout_mode: str = DEFAULT_RUN_CONFIG.layout_mode,
    sensor_mode: str = DEFAULT_RUN_CONFIG.sensor_mode,
    lidar_rays: int = DEFAULT_RUN_CONFIG.lidar_rays,
    env_id: str | None = None,
):
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

    episode_summaries = []

    for episode_index in range(episodes):
        episode = run_policy_episode(
            model=None,
            env=env,
            seed=evaluation_seed(seed, eval_seed_offset, episode_index),
        )
        episode_summaries.append(episode["summary"])

    cleaned_distribution = {}
    for item in episode_summaries:
        key = str(item["cleaned_dirt"])
        cleaned_distribution[key] = cleaned_distribution.get(key, 0) + 1

    return {
        "episodes": episodes,
        "random_success_rate": _avg(item["success"] for item in episode_summaries),
        "random_timeout_rate": _avg(item["timeout"] for item in episode_summaries),
        "random_avg_remaining_dirt": _avg(item["remaining_dirt"] for item in episode_summaries),
        "random_avg_cleaned_dirt": _avg(item["cleaned_dirt"] for item in episode_summaries),
        "random_cleaned_dirt_distribution": cleaned_distribution,
        "random_avg_reward": _avg(item["total_reward"] for item in episode_summaries),
        "random_avg_steps": _avg(item["steps"] for item in episode_summaries),
        "random_avg_wall_hits": _avg(item["wall_hits"] for item in episode_summaries),
        "random_avg_path_length": _avg(item["path_length"] for item in episode_summaries),
        "random_avg_forward_moves": _avg(item["forward_moves"] for item in episode_summaries),
        "random_avg_turns": _avg(item["turns"] for item in episode_summaries),
        "random_avg_turn_move_ratio": _avg(item["turn_move_ratio"] for item in episode_summaries),
        "random_avg_action_switches": _avg(item["action_switches"] for item in episode_summaries),
        "random_avg_max_turn_streak": _avg(item["max_turn_streak"] for item in episode_summaries),
        "random_avg_max_no_clean_streak": _avg(item["max_no_clean_streak"] for item in episode_summaries),
        "random_avg_first_clean_step": _avg_optional(item["first_clean_step"] for item in episode_summaries),
        "random_avg_final_clean_step": _avg_optional(item["final_clean_step"] for item in episode_summaries),
        "random_avg_reward_components": _avg_reward_components(episode_summaries),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=DEFAULT_RUN_CONFIG.eval_episodes)
    parser.add_argument("--room-size", type=float, default=DEFAULT_RUN_CONFIG.room_size)
    parser.add_argument("--max-steps", type=int, default=DEFAULT_RUN_CONFIG.max_steps)
    parser.add_argument("--dirt-count", type=int, default=DEFAULT_RUN_CONFIG.dirt_count)
    parser.add_argument("--seed", type=int, default=DEFAULT_RUN_CONFIG.seed)
    parser.add_argument("--eval-seed-offset", type=int, default=DEFAULT_RUN_CONFIG.eval_seed_offset)
    parser.add_argument("--obstacle-count", type=int, default=DEFAULT_RUN_CONFIG.obstacle_count)
    parser.add_argument("--layout-mode", default=DEFAULT_RUN_CONFIG.layout_mode, choices=["preset", "random"])
    parser.add_argument("--sensor-mode", default=DEFAULT_RUN_CONFIG.sensor_mode, choices=["oracle", "lidar_local_dirt"])
    parser.add_argument("--lidar-rays", type=int, default=DEFAULT_RUN_CONFIG.lidar_rays)
    parser.add_argument("--env-id")
    args = parser.parse_args()

    metrics = evaluate_random_baseline(
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
