from __future__ import annotations

import json
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
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
    """List all registered Apollo Labs curriculum environments and their defaults."""
    return {"envs": list_registered_envs()}


def describe_env(env_id: str) -> dict[str, Any]:
    """Describe one Apollo Labs environment, including defaults, rewards, and metrics."""
    return describe_registered_env(env_id)


def start_training_run(config: dict[str, Any]) -> dict[str, Any]:
    """Start a validated Apollo Labs PPO training run from a run config."""
    request = CreateRunRequest(**config)
    captured, response = _capture_tool_output(lambda: create_run(request))
    payload = response.model_dump()
    _append_tool_log(payload["run_id"], "start_training_run", captured)
    return payload


def get_run_status(run_id: str) -> dict[str, Any]:
    """Return run status, known artifact availability, and resource URIs for polling."""
    metadata = _run_metadata(run_id)
    run_dir = RUNS_DIR / run_id
    artifacts_dir = run_dir / "artifacts"
    logs_dir = run_dir / "logs"

    gif_files = sorted(artifacts_dir.glob("*.gif")) if artifacts_dir.exists() else []
    log_files = sorted(path.name for path in logs_dir.glob("*") if path.is_file()) if logs_dir.exists() else []

    return {
        "run_id": run_id,
        "status": metadata.get("status"),
        "env_id": metadata.get("config", {}).get("env_id"),
        "started_at": metadata.get("started_at"),
        "ended_at": metadata.get("ended_at"),
        "duration_sec": metadata.get("duration_sec"),
        "error": metadata.get("error"),
        "metrics_path": metadata.get("metrics_path"),
        "model_path": metadata.get("model_path"),
        "report_path": metadata.get("report_path"),
        "artifacts": {
            "has_gif": bool(gif_files),
            "gif_files": [str(path) for path in gif_files],
            "log_files": log_files,
        },
        "resources": {
            "metadata": f"apollolabs://runs/{run_id}/metadata",
            "config": f"apollolabs://runs/{run_id}/config",
            "metrics": f"apollolabs://runs/{run_id}/metrics",
            "progress": f"apollolabs://runs/{run_id}/progress",
            "artifacts": f"apollolabs://runs/{run_id}/artifacts",
            "trajectory": f"apollolabs://runs/{run_id}/trajectory",
            "report": f"apollolabs://runs/{run_id}/report",
            "logs": f"apollolabs://runs/{run_id}/logs",
        },
    }


def start_eval_run(run_id: str, episodes: int = 20) -> dict[str, Any]:
    """Evaluate an existing trained run and write fresh evaluation metrics."""
    captured, payload = _capture_tool_output(lambda: evaluate_policy(run_id=run_id, episodes=episodes))
    _append_tool_log(run_id, "start_eval_run", captured)
    return payload


def generate_run_gif(run_id: str, episodes: int = 1) -> dict[str, Any]:
    """Generate rollout visualization artifacts for a trained Apollo Labs run."""
    captured, payload = _capture_tool_output(lambda: generate_run_artifacts(run_id=run_id, episodes=episodes))
    _append_tool_log(run_id, "generate_run_gif", captured)
    return payload


def summarize_reward_hacking(run_id: str) -> dict[str, Any]:
    """Summarize reward-hacking diagnostics from a run's evaluation metrics."""
    metrics = _read_run_json(run_id, "metrics/eval_metrics.json")
    reward_hacking = metrics.get("reward_hacking", {})
    flag_count = reward_hacking.get("flag_count", 0) or 0
    return {
        "run_id": run_id,
        "reward_hacking": reward_hacking,
        "summary": (
            "No reward-hacking flags were recorded."
            if flag_count == 0
            else f"{flag_count} reward-hacking flag(s) were recorded; inspect diagnostics before scaling this config."
        ),
        "success_rate": metrics.get("success_rate"),
        "avg_cleaned_dirt": metrics.get("avg_cleaned_dirt"),
        "avg_wall_hits": metrics.get("avg_wall_hits"),
        "avg_obstacle_hits": metrics.get("avg_obstacle_hits"),
    }


def compare_runs(run_ids: list[str]) -> dict[str, Any]:
    """Rank completed runs using success, reward-hacking, dirt, collision, and reward metrics."""
    summaries = []
    for run_id in run_ids:
        metrics = _read_run_json(run_id, "metrics/eval_metrics.json")
        summaries.append(
            {
                "run_id": run_id,
                "success_rate": metrics.get("success_rate"),
                "avg_reward": metrics.get("avg_reward"),
                "avg_cleaned_dirt": metrics.get("avg_cleaned_dirt"),
                "avg_remaining_dirt": metrics.get("avg_remaining_dirt"),
                "avg_wall_hits": metrics.get("avg_wall_hits"),
                "avg_obstacle_hits": metrics.get("avg_obstacle_hits"),
                "reward_hacking_flags": metrics.get("reward_hacking", {}).get("flag_count"),
            }
        )
    ranking = sorted(summaries, key=_run_rank_key)
    best_run_id = ranking[0]["run_id"] if ranking else None
    return {
        "best_run_id": best_run_id,
        "criteria": [
            "success_rate desc",
            "reward_hacking_flags asc",
            "avg_remaining_dirt asc",
            "avg_wall_hits asc",
            "avg_obstacle_hits asc",
            "avg_reward desc",
        ],
        "ranking": ranking,
        "runs": summaries,
        "recommendation": (
            f"Use {best_run_id} as the current best candidate and validate it across additional seeds."
            if best_run_id
            else "No comparable runs were provided."
        ),
    }


def read_resource(uri: str) -> dict[str, Any]:
    if uri == "apollolabs://envs":
        return list_envs()
    prefix = "apollolabs://runs/"
    if not uri.startswith(prefix):
        raise ValueError(f"Unsupported Apollo Labs resource URI: {uri}")

    path = uri[len(prefix) :]
    run_id, _, resource_name = path.partition("/")
    resource_map = {
        "config": "rl_config.json",
        "metrics": "metrics/eval_metrics.json",
        "progress": "metrics/train_progress.jsonl",
        "artifacts": "artifacts/manifest.json",
        "trajectory": "artifacts/episode_seed_10504_trajectory.json",
        "report": "report.json",
    }
    if resource_name == "metadata":
        return _run_metadata(run_id)
    if resource_name == "logs":
        return _read_logs_resource(run_id)
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


def _run_metadata(run_id: str) -> dict[str, Any]:
    run_dir = RUNS_DIR / run_id
    metadata_path = run_dir / "metadata.json"
    if metadata_path.exists():
        return json.loads(metadata_path.read_text())
    if not run_dir.exists():
        raise FileNotFoundError(str(run_dir))

    config_path = run_dir / "rl_config.json"
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    model_path = run_dir / "model" / "roomba_policy.zip"
    eval_metrics_path = run_dir / "metrics" / "eval_metrics.json"
    combined_metrics_path = run_dir / "metrics" / "combined_metrics.json"
    report_path = run_dir / "report.json"
    error_path = run_dir / "logs" / "error.txt"

    if error_path.exists():
        status = "failed"
    elif eval_metrics_path.exists() and model_path.exists():
        status = "completed"
    elif model_path.exists():
        status = "trained"
    else:
        status = "unknown"

    return {
        "run_id": run_id,
        "status": status,
        "config": config,
        "started_at": None,
        "ended_at": None,
        "duration_sec": None,
        "error": error_path.read_text(errors="replace") if error_path.exists() else None,
        "metrics_path": str(combined_metrics_path if combined_metrics_path.exists() else eval_metrics_path)
        if eval_metrics_path.exists() or combined_metrics_path.exists()
        else None,
        "model_path": str(model_path) if model_path.exists() else None,
        "report_path": str(report_path) if report_path.exists() else None,
    }


def _read_logs_resource(run_id: str) -> dict[str, Any]:
    logs_dir = RUNS_DIR / run_id / "logs"
    if not logs_dir.exists():
        raise FileNotFoundError(str(logs_dir))
    files: dict[str, str] = {}
    for path in sorted(logs_dir.iterdir()):
        if path.is_file():
            files[path.name] = path.read_text(errors="replace")
    return {"run_id": run_id, "files": files}


def _capture_tool_output(fn):
    buffer = StringIO()
    with redirect_stdout(buffer), redirect_stderr(buffer):
        result = fn()
    return buffer.getvalue(), result


def _append_tool_log(run_id: str, tool_name: str, content: str) -> None:
    if not content:
        return
    logs_dir = RUNS_DIR / run_id / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "mcp_tool_output.log"
    with log_path.open("a") as fh:
        fh.write(f"\n--- {tool_name} ---\n")
        fh.write(content)
        if not content.endswith("\n"):
            fh.write("\n")


def _run_rank_key(summary: dict[str, Any]) -> tuple:
    return (
        _desc(summary.get("success_rate")),
        _asc(summary.get("reward_hacking_flags")),
        _asc(summary.get("avg_remaining_dirt")),
        _asc(summary.get("avg_wall_hits")),
        _asc(summary.get("avg_obstacle_hits")),
        _desc(summary.get("avg_reward")),
    )


def _asc(value: Any) -> float:
    if value is None:
        return 1_000_000_000.0
    return float(value)


def _desc(value: Any) -> float:
    if value is None:
        return 1_000_000_000.0
    return -float(value)


def _resource_envs() -> dict[str, Any]:
    return read_resource("apollolabs://envs")


def _resource_run_metadata(run_id: str) -> dict[str, Any]:
    return read_resource(f"apollolabs://runs/{run_id}/metadata")


def _resource_run_config(run_id: str) -> dict[str, Any]:
    return read_resource(f"apollolabs://runs/{run_id}/config")


def _resource_run_metrics(run_id: str) -> dict[str, Any]:
    return read_resource(f"apollolabs://runs/{run_id}/metrics")


def _resource_run_progress(run_id: str) -> dict[str, Any]:
    return read_resource(f"apollolabs://runs/{run_id}/progress")


def _resource_run_artifacts(run_id: str) -> dict[str, Any]:
    return read_resource(f"apollolabs://runs/{run_id}/artifacts")


def _resource_run_trajectory(run_id: str) -> dict[str, Any]:
    return read_resource(f"apollolabs://runs/{run_id}/trajectory")


def _resource_run_report(run_id: str) -> dict[str, Any]:
    return read_resource(f"apollolabs://runs/{run_id}/report")


def _resource_run_logs(run_id: str) -> dict[str, Any]:
    return read_resource(f"apollolabs://runs/{run_id}/logs")


def main() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise SystemExit(
            "The optional 'mcp' package is not installed. Install it to run the "
            "Apollo Labs MCP server process; direct Python helpers remain usable."
        ) from exc

    server = FastMCP("apollolabs")
    server.tool()(list_envs)
    server.tool()(describe_env)
    server.tool()(start_training_run)
    server.tool()(get_run_status)
    server.tool()(start_eval_run)
    server.tool()(compare_runs)
    server.tool()(generate_run_gif)
    server.tool()(summarize_reward_hacking)

    server.resource("apollolabs://envs")(_resource_envs)
    server.resource("apollolabs://runs/{run_id}/metadata")(_resource_run_metadata)
    server.resource("apollolabs://runs/{run_id}/config")(_resource_run_config)
    server.resource("apollolabs://runs/{run_id}/metrics")(_resource_run_metrics)
    server.resource("apollolabs://runs/{run_id}/progress")(_resource_run_progress)
    server.resource("apollolabs://runs/{run_id}/artifacts")(_resource_run_artifacts)
    server.resource("apollolabs://runs/{run_id}/trajectory")(_resource_run_trajectory)
    server.resource("apollolabs://runs/{run_id}/report")(_resource_run_report)
    server.resource("apollolabs://runs/{run_id}/logs")(_resource_run_logs)
    server.run()


if __name__ == "__main__":
    main()
