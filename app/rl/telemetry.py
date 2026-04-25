from __future__ import annotations

from typing import Any

import numpy as np


ACTION_NAMES = {
    0: "forward",
    1: "turn_left",
    2: "turn_right",
}


def run_policy_episode(
    model,
    env,
    seed: int,
    include_steps: bool = False,
    capture_frames: bool = False,
) -> dict[str, Any]:
    frames = []
    steps = []
    cleaned_events = []
    reward_totals: dict[str, float] = {}
    action_counts = {name: 0 for name in ACTION_NAMES.values()}
    action_switches = 0
    max_turn_streak = 0
    turn_streak = 0
    max_no_clean_streak = 0
    no_clean_streak = 0
    wall_hits = 0
    obstacle_hits = 0
    path_length = 0.0
    total_reward = 0.0
    previous_action = None

    obs, _ = env.reset(seed=seed)
    base_env = env.unwrapped if hasattr(env, "unwrapped") else env
    if model is None:
        env.action_space.seed(seed)
    previous_position = base_env.robot.copy()

    if capture_frames:
        frames.append(env.render())

    last_info = {
        "remaining_dirt": getattr(base_env, "dirt_count", 0),
        "cleaned_count": 0,
        "hit_wall": False,
        "hit_obstacle": False,
        "reward_components": {},
    }
    terminated = False
    truncated = False

    max_steps = int(getattr(base_env, "max_steps", 0))
    for step_index in range(max_steps):
        if model is None:
            action = int(env.action_space.sample())
        else:
            action, _ = model.predict(obs, deterministic=True)
            action = int(action)
        obs, reward, terminated, truncated, info = env.step(action)

        action_name = ACTION_NAMES[action]
        action_counts[action_name] += 1
        if previous_action is not None and action != previous_action:
            action_switches += 1
        previous_action = action

        if action in (1, 2):
            turn_streak += 1
        else:
            turn_streak = 0
        max_turn_streak = max(max_turn_streak, turn_streak)

        if info["cleaned_count"]:
            no_clean_streak = 0
        else:
            no_clean_streak += 1
        max_no_clean_streak = max(max_no_clean_streak, no_clean_streak)

        current_position = base_env.robot.copy()
        step_distance = float(np.linalg.norm(current_position - previous_position))
        path_length += step_distance
        previous_position = current_position

        total_reward += float(reward)
        wall_hits += int(info.get("hit_wall", False))
        obstacle_hits += int(info.get("hit_obstacle", False))
        for key, value in info.get("reward_components", {}).items():
            reward_totals[key] = reward_totals.get(key, 0.0) + float(value)

        step_number = step_index + 1
        if info["cleaned_count"]:
            cleaned_events.append(
                {
                    "step": step_number,
                    "cleaned_count": int(info["cleaned_count"]),
                    "remaining_dirt": int(info["remaining_dirt"]),
                    "robot_x": float(base_env.robot[0]),
                    "robot_y": float(base_env.robot[1]),
                    "reward": float(reward),
                    "reward_components": dict(info.get("reward_components", {})),
                }
            )

        if include_steps:
            steps.append(
                {
                    "step": step_number,
                    "action": action_name,
                    "action_id": action,
                    "robot_x": float(base_env.robot[0]),
                    "robot_y": float(base_env.robot[1]),
                    "heading": float(base_env.heading),
                    "reward": float(reward),
                    "reward_components": dict(info.get("reward_components", {})),
                    "remaining_dirt": int(info.get("remaining_dirt", 0)),
                    "cleaned_count": int(info.get("cleaned_count", 0)),
                    "hit_wall": bool(info.get("hit_wall", False)),
                    "hit_obstacle": bool(info.get("hit_obstacle", False)),
                    "nearest_dirt_distance": float(info.get("nearest_dirt_distance") or 0.0),
                    "heading_error": float(info.get("heading_error", 0.0)),
                    "step_distance": step_distance,
                }
            )

        if capture_frames:
            frames.append(env.render())

        last_info = info
        if terminated or truncated:
            break

    steps_taken = int(last_info.get("steps", max_steps))
    dirt_count = int(getattr(base_env, "dirt_count", 0))
    cleaned_dirt = int(dirt_count - int(last_info.get("remaining_dirt", 0)))
    first_clean_step = cleaned_events[0]["step"] if cleaned_events else None
    final_clean_step = cleaned_events[-1]["step"] if cleaned_events else None

    summary = {
        "seed": seed,
        "success": bool(last_info.get("success", False) or (last_info.get("remaining_dirt", 0) == 0 and terminated)),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "timeout": bool(truncated and last_info.get("remaining_dirt", 0) > 0),
        "steps": steps_taken,
        "total_reward": total_reward,
        "remaining_dirt": int(last_info.get("remaining_dirt", 0)),
        "cleaned_dirt": cleaned_dirt,
        "wall_hits": wall_hits,
        "obstacle_hits": obstacle_hits,
        "path_length": path_length,
        "action_counts": action_counts,
        "turns": action_counts["turn_left"] + action_counts["turn_right"],
        "forward_moves": action_counts["forward"],
        "turn_move_ratio": (action_counts["turn_left"] + action_counts["turn_right"])
        / max(action_counts["forward"], 1),
        "action_switches": action_switches,
        "max_turn_streak": max_turn_streak,
        "max_no_clean_streak": max_no_clean_streak,
        "first_clean_step": first_clean_step,
        "final_clean_step": final_clean_step,
        "cleaned_events": cleaned_events,
        "reward_totals": reward_totals,
    }

    result: dict[str, Any] = {"summary": summary}
    if include_steps:
        result["steps"] = steps
    if capture_frames:
        result["frames"] = frames
    return result
