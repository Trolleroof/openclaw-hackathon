import argparse
import json

from app.rl.env import RoombaEnv
from app.rl.eval import _avg, _avg_optional, _avg_reward_components
from app.rl.telemetry import run_policy_episode


def evaluate_random_baseline(
    episodes: int = 50,
    room_size: float = 10.0,
    max_steps: int = 200,
    dirt_count: int = 3,
):
    env = RoombaEnv(
        room_size=room_size,
        max_steps=max_steps,
        dirt_count=dirt_count,
    )

    episode_summaries = []

    for episode_index in range(episodes):
        episode = run_policy_episode(model=None, env=env, seed=episode_index)
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
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--room-size", type=float, default=10.0)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--dirt-count", type=int, default=3)
    args = parser.parse_args()

    metrics = evaluate_random_baseline(
        episodes=args.episodes,
        room_size=args.room_size,
        max_steps=args.max_steps,
        dirt_count=args.dirt_count,
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
