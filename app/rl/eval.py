import argparse
import json

from stable_baselines3 import PPO

from app.config import RUNS_DIR
from app.rl.env import RoombaEnv
from app.rl.telemetry import run_policy_episode


def _avg(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _avg_optional(values):
    values = [value for value in values if value is not None]
    return _avg(values) if values else None


def _avg_reward_components(episode_summaries):
    keys = sorted({key for item in episode_summaries for key in item["reward_totals"]})
    return {
        key: _avg(item["reward_totals"].get(key, 0.0) for item in episode_summaries)
        for key in keys
    }


def evaluate_policy(
    run_id: str,
    episodes: int = 50,
    room_size: float = 10.0,
    max_steps: int = 200,
    dirt_count: int = 3,
):
    run_dir = RUNS_DIR / run_id
    model_path = run_dir / "model" / "roomba_policy.zip"
    metrics_dir = run_dir / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)

    env = RoombaEnv(
        room_size=room_size,
        max_steps=max_steps,
        dirt_count=dirt_count,
    )

    model = PPO.load(str(model_path))

    episode_summaries = []

    for episode_index in range(episodes):
        episode = run_policy_episode(model=model, env=env, seed=episode_index)
        episode_summaries.append(episode["summary"])

    cleaned_distribution = {}
    for item in episode_summaries:
        key = str(item["cleaned_dirt"])
        cleaned_distribution[key] = cleaned_distribution.get(key, 0) + 1

    metrics = {
        "episodes": episodes,
        "success_rate": _avg(item["success"] for item in episode_summaries),
        "timeout_rate": _avg(item["timeout"] for item in episode_summaries),
        "avg_reward": _avg(item["total_reward"] for item in episode_summaries),
        "avg_steps": _avg(item["steps"] for item in episode_summaries),
        "avg_remaining_dirt": _avg(item["remaining_dirt"] for item in episode_summaries),
        "avg_cleaned_dirt": _avg(item["cleaned_dirt"] for item in episode_summaries),
        "cleaned_dirt_distribution": cleaned_distribution,
        "wall_hits": sum(item["wall_hits"] for item in episode_summaries),
        "avg_wall_hits": _avg(item["wall_hits"] for item in episode_summaries),
        "avg_path_length": _avg(item["path_length"] for item in episode_summaries),
        "avg_forward_moves": _avg(item["forward_moves"] for item in episode_summaries),
        "avg_turns": _avg(item["turns"] for item in episode_summaries),
        "avg_turn_move_ratio": _avg(item["turn_move_ratio"] for item in episode_summaries),
        "avg_action_switches": _avg(item["action_switches"] for item in episode_summaries),
        "avg_max_turn_streak": _avg(item["max_turn_streak"] for item in episode_summaries),
        "avg_max_no_clean_streak": _avg(item["max_no_clean_streak"] for item in episode_summaries),
        "avg_first_clean_step": _avg_optional(item["first_clean_step"] for item in episode_summaries),
        "avg_final_clean_step": _avg_optional(item["final_clean_step"] for item in episode_summaries),
        "avg_reward_components": _avg_reward_components(episode_summaries),
    }

    metrics_path = metrics_dir / "eval_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2))
    episodes_path = metrics_dir / "eval_episodes.json"
    episodes_path.write_text(json.dumps(episode_summaries, indent=2))

    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--room-size", type=float, default=10.0)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--dirt-count", type=int, default=3)
    args = parser.parse_args()

    metrics = evaluate_policy(
        run_id=args.run_id,
        episodes=args.episodes,
        room_size=args.room_size,
        max_steps=args.max_steps,
        dirt_count=args.dirt_count,
    )

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
