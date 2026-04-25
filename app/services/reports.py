import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.config import HERMES_PUBLIC_BASE_URL, RUNS_DIR
from app.schemas.run import RunReport


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_dir(run_id: str) -> Path:
    return RUNS_DIR / run_id


def report_path(run_id: str) -> Path:
    return _run_dir(run_id) / "report.json"


def _safe_float(value: Any) -> Optional[float]:
    return float(value) if isinstance(value, (int, float)) else None


def _safe_int(value: Any) -> Optional[int]:
    return int(value) if isinstance(value, (int, float)) else None


def _metric(metadata: dict, key: str) -> Any:
    metrics = metadata.get("metrics") or {}
    ppo = metrics.get("ppo") or {}
    return ppo.get(key)


def _status_label(status: str) -> str:
    if status == "completed":
        return "success"
    return status


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


def list_reports() -> list[RunReport]:
    reports = []
    for path in sorted(RUNS_DIR.glob("run_*/report.json"), reverse=True):
        reports.append(RunReport(**json.loads(path.read_text())))
    return reports
