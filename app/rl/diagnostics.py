from __future__ import annotations


def avg(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def avg_optional(values):
    values = [value for value in values if value is not None]
    return avg(values) if values else None


def avg_reward_components(episode_summaries):
    keys = sorted({key for item in episode_summaries for key in item["reward_totals"]})
    return {
        key: avg(item["reward_totals"].get(key, 0.0) for item in episode_summaries)
        for key in keys
    }


def summarize_episodes(episode_summaries: list[dict]) -> dict:
    cleaned_distribution = {}
    for item in episode_summaries:
        key = str(item["cleaned_dirt"])
        cleaned_distribution[key] = cleaned_distribution.get(key, 0) + 1

    metrics = {
        "episodes": len(episode_summaries),
        "success_rate": avg(item["success"] for item in episode_summaries),
        "timeout_rate": avg(item["timeout"] for item in episode_summaries),
        "avg_reward": avg(item["total_reward"] for item in episode_summaries),
        "avg_steps": avg(item["steps"] for item in episode_summaries),
        "avg_remaining_dirt": avg(item["remaining_dirt"] for item in episode_summaries),
        "avg_cleaned_dirt": avg(item["cleaned_dirt"] for item in episode_summaries),
        "cleaned_dirt_distribution": cleaned_distribution,
        "wall_hits": sum(item["wall_hits"] for item in episode_summaries),
        "avg_wall_hits": avg(item["wall_hits"] for item in episode_summaries),
        "obstacle_hits": sum(item.get("obstacle_hits", 0) for item in episode_summaries),
        "avg_obstacle_hits": avg(item.get("obstacle_hits", 0) for item in episode_summaries),
        "avg_path_length": avg(item["path_length"] for item in episode_summaries),
        "avg_forward_moves": avg(item["forward_moves"] for item in episode_summaries),
        "avg_turns": avg(item["turns"] for item in episode_summaries),
        "avg_turn_move_ratio": avg(item["turn_move_ratio"] for item in episode_summaries),
        "avg_action_switches": avg(item["action_switches"] for item in episode_summaries),
        "avg_max_turn_streak": avg(item["max_turn_streak"] for item in episode_summaries),
        "avg_max_no_clean_streak": avg(item["max_no_clean_streak"] for item in episode_summaries),
        "avg_first_clean_step": avg_optional(item["first_clean_step"] for item in episode_summaries),
        "avg_final_clean_step": avg_optional(item["final_clean_step"] for item in episode_summaries),
        "avg_reward_components": avg_reward_components(episode_summaries),
    }
    metrics["reward_hacking"] = reward_hacking_flags(metrics)
    return metrics


def reward_hacking_flags(metrics: dict) -> dict:
    reward_components = metrics.get("avg_reward_components", {})
    clean_reward = float(reward_components.get("clean", 0.0))
    shaping_reward = float(reward_components.get("progress", 0.0)) + float(
        reward_components.get("alignment", 0.0)
    )
    avg_steps = max(float(metrics.get("avg_steps", 0.0)), 1.0)
    avg_path_length = float(metrics.get("avg_path_length", 0.0))
    avg_cleaned_dirt = float(metrics.get("avg_cleaned_dirt", 0.0))
    avg_reward = float(metrics.get("avg_reward", 0.0))
    avg_turn_move_ratio = float(metrics.get("avg_turn_move_ratio", 0.0))
    avg_max_no_clean_streak = float(metrics.get("avg_max_no_clean_streak", 0.0))
    avg_max_turn_streak = float(metrics.get("avg_max_turn_streak", 0.0))
    avg_wall_hits = float(metrics.get("avg_wall_hits", 0.0))
    avg_obstacle_hits = float(metrics.get("avg_obstacle_hits", 0.0))

    flags = {
        "low_clean_high_reward": avg_cleaned_dirt < 0.5 and avg_reward > 0.0,
        "shaping_dominates_cleaning": clean_reward <= 0.0 and shaping_reward > 1.0,
        "excessive_turning": avg_turn_move_ratio > 3.0 or avg_max_turn_streak > avg_steps * 0.4,
        "low_movement": avg_path_length < avg_steps * 0.05,
        "long_no_clean_streaks": avg_max_no_clean_streak > avg_steps * 0.75,
        "collision_abuse": avg_wall_hits + avg_obstacle_hits > 3.0,
    }
    flags["flag_count"] = sum(1 for value in flags.values() if value is True)
    return flags
