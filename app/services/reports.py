import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.config import HERMES_PUBLIC_BASE_URL, RUNS_DIR
from app.schemas.run import RunReport


HISTORICAL_AGENTMAIL_RUN_IDS = (
    "run_3b77938dc6",
    "run_ecb8069f9c",
    "matrix_preset_lidar_v2_40k",
    "matrix_preset_oracle_40k",
    "matrix_random_lidar_v2_60k",
    "matrix_random_lidar_v3_60k",
    "matrix_random_lidar_v5_60k",
    "matrix_random_oracle_40k",
    "matrix_random_oracle_no_obstacles_40k",
    "matrix_random_oracle_v2_60k",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_dir(run_id: str) -> Path:
    return RUNS_DIR / run_id


def report_path(run_id: str) -> Path:
    return _run_dir(run_id) / "report.json"


def _metadata_path(run_id: str) -> Path:
    return _run_dir(run_id) / "metadata.json"


def _rl_config_path(run_id: str) -> Path:
    return _run_dir(run_id) / "rl_config.json"


def _eval_metrics_path(run_id: str) -> Path:
    return _run_dir(run_id) / "metrics" / "eval_metrics.json"


def _combined_metrics_path(run_id: str) -> Path:
    return _run_dir(run_id) / "metrics" / "combined_metrics.json"


def _checkpoint_path(run_id: str) -> Path:
    return _run_dir(run_id) / "model" / "roomba_policy.zip"


def _safe_float(value: Any) -> Optional[float]:
    return float(value) if isinstance(value, (int, float)) else None


def _safe_int(value: Any) -> Optional[int]:
    return int(value) if isinstance(value, (int, float)) else None


def _read_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _iso_from_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def _fallback_timestamp(paths: list[Path]) -> str:
    existing = [path for path in paths if path.exists()]
    if not existing:
        return _now_iso()
    return _iso_from_timestamp(max(path.stat().st_mtime for path in existing))


def _metric(metadata: dict, key: str) -> Any:
    metrics = metadata.get("metrics") or {}
    ppo = metrics.get("ppo") or {}
    return ppo.get(key)


def _status_label(status: str) -> str:
    if status == "completed":
        return "success"
    return status


def _is_terminal_status(status: Optional[str]) -> bool:
    return status in {"completed", "success", "failed", "early_stop"}


def is_historical_agentmail_seed(run_id: str) -> bool:
    return run_id in HISTORICAL_AGENTMAIL_RUN_IDS


def _local_artifact_uri(path: Path, fallback: Optional[str] = None) -> Optional[str]:
    if path.exists():
        return str(path)
    return fallback


def _historical_timestamp(run_id: str) -> str:
    return _fallback_timestamp(
        [
            report_path(run_id),
            _metadata_path(run_id),
            _eval_metrics_path(run_id),
            _rl_config_path(run_id),
            _combined_metrics_path(run_id),
            _checkpoint_path(run_id),
        ]
    )


def _normalized_report(metadata: dict, *, run_id: str) -> RunReport:
    timestamp = metadata.get("ended_at") or metadata.get("started_at") or _historical_timestamp(run_id)
    report = build_run_report(
        {
            **metadata,
            "run_id": run_id,
            "ended_at": metadata.get("ended_at") or timestamp,
            "started_at": metadata.get("started_at"),
            "model_path": _local_artifact_uri(_checkpoint_path(run_id), metadata.get("model_path")),
            "metrics_path": _local_artifact_uri(_combined_metrics_path(run_id), metadata.get("metrics_path"))
            or _local_artifact_uri(_eval_metrics_path(run_id), metadata.get("metrics_path")),
        }
    )
    return report.model_copy(update={"created_at": timestamp})


def _historical_metadata(run_id: str) -> Optional[dict]:
    config = _read_json(_rl_config_path(run_id))
    eval_metrics = _read_json(_eval_metrics_path(run_id))
    if config is None or eval_metrics is None or not is_historical_agentmail_seed(run_id):
        return None

    checkpoint_uri = _local_artifact_uri(_checkpoint_path(run_id))
    metrics_path = _local_artifact_uri(_eval_metrics_path(run_id))
    timestamp = _historical_timestamp(run_id)

    return {
        "run_id": run_id,
        "status": "success",
        "started_at": timestamp,
        "ended_at": timestamp,
        "duration_sec": None,
        "config": config,
        "metrics": {"ppo": eval_metrics},
        "model_path": checkpoint_uri,
        "metrics_path": metrics_path,
        "error": None,
    }


def build_run_report(metadata: dict) -> RunReport:
    run_id = metadata["run_id"]
    config = metadata.get("config") or {}
    status = _status_label(metadata.get("status", "unknown"))
    ended_at = metadata.get("ended_at") or _now_iso()
    started_at = metadata.get("started_at")
    duration_sec = _safe_float(metadata.get("duration_sec"))
    mean_return = _safe_float(_metric(metadata, "avg_reward"))
    best_return = _safe_float(_metric(metadata, "success_rate"))
    episodes = _safe_int(_metric(metadata, "episodes") or config.get("eval_episodes"))
    steps = _safe_int(config.get("total_timesteps"))
    template = f"roomba.room-{config.get('room_size', 'unknown')}.dirt-{config.get('dirt_count', 'unknown')}"
    algo = "PPO"
    checkpoint_uri = metadata.get("model_path")
    metrics_path = metadata.get("metrics_path")
    dashboard_url = f"{HERMES_PUBLIC_BASE_URL.rstrip('/')}/runs/{run_id}"

    model_summary = (
        f"{algo} run {run_id} finished with status {status}. "
        f"Trained for {steps or 0:,} timesteps and evaluated across {episodes or 0} episodes. "
        f"Average reward: {mean_return:.3f}; success rate: {best_return:.3f}."
        if mean_return is not None and best_return is not None
        else f"{algo} run {run_id} finished with status {status}."
    )
    if metadata.get("error"):
        model_summary += f" Failure: {metadata['error']}"

    markdown = "\n".join(
        [
            f"# Hermes Run Report: {run_id}",
            "",
            f"- Status: `{status}`",
            f"- Template: `{template}`",
            f"- Timesteps: `{steps or 0}`",
            f"- Episodes: `{episodes or 0}`",
            f"- Average reward: `{mean_return if mean_return is not None else 'n/a'}`",
            f"- Success rate: `{best_return if best_return is not None else 'n/a'}`",
            f"- Checkpoint: `{checkpoint_uri or 'n/a'}`",
            f"- Dashboard: {dashboard_url}",
            "",
            model_summary,
        ]
    )

    return RunReport(
        run_id=run_id,
        status=status,
        started_at=started_at,
        ended_at=ended_at,
        duration_sec=duration_sec,
        template=template,
        algo=algo,
        config=config,
        steps=steps,
        episodes=episodes,
        mean_return=mean_return,
        best_return=best_return,
        checkpoint_uri=checkpoint_uri,
        artifact_links={
            "dashboard": dashboard_url,
            **({"metrics": metrics_path} if metrics_path else {}),
            **({"checkpoint": checkpoint_uri} if checkpoint_uri else {}),
        },
        error=metadata.get("error"),
        model_summary=model_summary,
        markdown=markdown,
        created_at=_now_iso(),
    )


def write_report(report: RunReport) -> RunReport:
    path = report_path(report.run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.model_dump(), indent=2))
    return report


def read_report(run_id: str) -> Optional[RunReport]:
    path = report_path(run_id)
    if not path.exists():
        return None
    return RunReport(**json.loads(path.read_text()))


def resolve_report(run_id: str) -> Optional[RunReport]:
    persisted = read_report(run_id)
    if persisted is not None:
        return persisted

    metadata = _read_json(_metadata_path(run_id))
    if metadata is not None and _is_terminal_status(metadata.get("status")):
        return _normalized_report(metadata, run_id=run_id)

    historical = _historical_metadata(run_id)
    if historical is not None:
        return _normalized_report(historical, run_id=run_id)

    return None


def list_agentmail_reports() -> list[RunReport]:
    run_ids = {run_dir.name for run_dir in RUNS_DIR.iterdir() if run_dir.is_dir()}
    reports = [report for run_id in run_ids if (report := resolve_report(run_id)) is not None]
    return sorted(
        reports,
        key=lambda report: (
            report.ended_at or report.created_at,
            report.created_at,
            report.run_id,
        ),
        reverse=True,
    )


def list_reports() -> list[RunReport]:
    reports = []
    for path in sorted(RUNS_DIR.glob("run_*/report.json"), reverse=True):
        reports.append(RunReport(**json.loads(path.read_text())))
    return reports
