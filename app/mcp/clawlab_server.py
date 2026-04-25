from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import RUNS_DIR
from app.rl.envs.registry import describe_env as describe_registered_env
from app.rl.envs.registry import list_envs as list_registered_envs
from app.rl.eval import evaluate_policy
from app.rl.visualize import generate_run_artifacts
from app.schemas.run import CreateRunRequest
from app.services.runner import create_run


def list_envs() -> dict[str, Any]:
    return {"envs": list_registered_envs()}


def describe_env(env_id: str) -> dict[str, Any]:
    return describe_registered_env(env_id)


def start_training_run(config: dict[str, Any]) -> dict[str, Any]:
    request = CreateRunRequest(**config)
    response = create_run(request)
    return response.model_dump()


def start_eval_run(run_id: str, episodes: int = 20) -> dict[str, Any]:
    return evaluate_policy(run_id=run_id, episodes=episodes)


def generate_run_gif(run_id: str, episodes: int = 1) -> dict[str, Any]:
    return generate_run_artifacts(run_id=run_id, episodes=episodes)


def summarize_reward_hacking(run_id: str) -> dict[str, Any]:
    metrics = _read_run_json(run_id, "metrics/eval_metrics.json")
    return {
        "run_id": run_id,
        "reward_hacking": metrics.get("reward_hacking", {}),
        "success_rate": metrics.get("success_rate"),
        "avg_cleaned_dirt": metrics.get("avg_cleaned_dirt"),
        "avg_wall_hits": metrics.get("avg_wall_hits"),
        "avg_obstacle_hits": metrics.get("avg_obstacle_hits"),
    }


def compare_runs(run_ids: list[str]) -> dict[str, Any]:
    summaries = []
    for run_id in run_ids:
        metrics = _read_run_json(run_id, "metrics/eval_metrics.json")
        summaries.append(
            {
                "run_id": run_id,
                "success_rate": metrics.get("success_rate"),
                "avg_reward": metrics.get("avg_reward"),
                "avg_cleaned_dirt": metrics.get("avg_cleaned_dirt"),
                "reward_hacking_flags": metrics.get("reward_hacking", {}).get("flag_count"),
            }
        )
    return {"runs": summaries}


def read_resource(uri: str) -> dict[str, Any]:
    if uri == "clawlab://envs":
        return list_envs()
    prefix = "clawlab://runs/"
    if not uri.startswith(prefix):
        raise ValueError(f"Unsupported ClawLab resource URI: {uri}")

    path = uri[len(prefix) :]
    run_id, _, resource_name = path.partition("/")
    resource_map = {
        "config": "rl_config.json",
        "metrics": "metrics/eval_metrics.json",
        "progress": "metrics/train_progress.jsonl",
        "artifacts": "artifacts/manifest.json",
        "trajectory": "artifacts/episode_seed_10504_trajectory.json",
    }
    if resource_name not in resource_map:
        raise ValueError(f"Unsupported run resource: {resource_name}")

    resource_path = RUNS_DIR / run_id / resource_map[resource_name]
    if not resource_path.exists():
        raise FileNotFoundError(str(resource_path))
    if resource_path.suffix == ".jsonl":
        return {"run_id": run_id, "lines": resource_path.read_text().splitlines()}
    return json.loads(resource_path.read_text())


def _read_run_json(run_id: str, relative_path: str) -> dict[str, Any]:
    path = RUNS_DIR / run_id / relative_path
    if not path.exists():
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text())


def main() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise SystemExit(
            "The optional 'mcp' package is not installed. Install it to run the "
            "ClawLab MCP server process; direct Python helpers remain usable."
        ) from exc

    server = FastMCP("clawlab")
    server.tool()(list_envs)
    server.tool()(describe_env)
    server.tool()(start_training_run)
    server.tool()(start_eval_run)
    server.tool()(compare_runs)
    server.tool()(generate_run_gif)
    server.tool()(summarize_reward_hacking)
    server.run()


if __name__ == "__main__":
    main()
