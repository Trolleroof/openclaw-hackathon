from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def summarize_benchmark(run_metrics: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    best = None
    for item in run_metrics:
        metrics = item["metrics"]
        progress = item.get("progress", [])
        reward_hacking = metrics.get("reward_hacking", {})
        row = {
            "run_id": item["run_id"],
            "env_id": item["env_id"],
            "success_rate": metrics.get("success_rate", 0.0),
            "avg_reward": metrics.get("avg_reward", 0.0),
            "avg_cleaned_dirt": metrics.get("avg_cleaned_dirt"),
            "avg_wall_hits": metrics.get("avg_wall_hits", 0.0),
            "avg_obstacle_hits": metrics.get("avg_obstacle_hits", 0.0),
            "reward_hacking_flags": reward_hacking.get(
                "reward_hacking_flag_count",
                reward_hacking.get("flag_count", 0),
            ),
            "behavior_flags": reward_hacking.get("behavior_flag_count", 0),
            "progress": _progress_summary(progress),
        }
        rows.append(row)
        if best is None or _score(row) > _score(best):
            best = row

    return {
        "runs": rows,
        "best_run_id": best["run_id"] if best else None,
        "best_env_id": best["env_id"] if best else None,
    }


def write_benchmark_summary(run_metrics: list[dict[str, Any]], path: Path) -> dict[str, Any]:
    summary = summarize_benchmark(run_metrics)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2))
    return summary


def read_progress_snapshots(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _progress_summary(progress: list[dict[str, Any]]) -> dict[str, Any]:
    if not progress:
        return {
            "snapshots": 0,
            "first_success_rate": None,
            "final_success_rate": None,
            "success_rate_delta": None,
            "first_avg_reward": None,
            "final_avg_reward": None,
            "avg_reward_delta": None,
        }

    first = progress[0]
    final = progress[-1]
    first_success = float(first.get("success_rate", 0.0))
    final_success = float(final.get("success_rate", 0.0))
    first_reward = float(first.get("avg_reward", 0.0))
    final_reward = float(final.get("avg_reward", 0.0))
    return {
        "snapshots": len(progress),
        "first_timestep": int(first.get("timesteps", 0)),
        "final_timestep": int(final.get("timesteps", 0)),
        "first_success_rate": first_success,
        "final_success_rate": final_success,
        "success_rate_delta": final_success - first_success,
        "first_avg_reward": first_reward,
        "final_avg_reward": final_reward,
        "avg_reward_delta": final_reward - first_reward,
    }


def _score(row: dict[str, Any]) -> float:
    return (
        float(row["success_rate"]) * 100.0
        + float(row.get("avg_cleaned_dirt") or 0.0)
        + float(row["avg_reward"]) * 0.01
        - float(row["avg_wall_hits"]) * 10.0
        - float(row["avg_obstacle_hits"]) * 10.0
        - float(row["reward_hacking_flags"]) * 100.0
        - float(row["behavior_flags"]) * 25.0
    )
