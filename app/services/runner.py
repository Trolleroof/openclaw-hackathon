import json
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import RUNS_DIR
from app.schemas.run import CompleteRunRequest, CreateRunRequest, RunResponse
from app.services.agentmail import send_report
from app.services.reports import build_run_report, read_report, report_path, write_report


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_dir(run_id: str) -> Path:
    return RUNS_DIR / run_id


def _metadata_path(run_id: str) -> Path:
    return _run_dir(run_id) / "metadata.json"


def _write_metadata(run_id: str, payload: dict) -> None:
    path = _metadata_path(run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def _read_metadata(run_id: str) -> Optional[dict]:
    path = _metadata_path(run_id)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _finalize_report(metadata: dict) -> dict:
    existing = read_report(metadata["run_id"])
    report = build_run_report(metadata)

    if existing and existing.delivery_status == "sent":
        report.agentmail_message_id = existing.agentmail_message_id
        report.agentmail_thread_id = existing.agentmail_thread_id
        report.delivery_status = existing.delivery_status
        report.delivery_error = existing.delivery_error
    else:
        result = send_report(report)
        report.agentmail_message_id = result.message_id
        report.agentmail_thread_id = result.thread_id
        report.delivery_status = result.delivery_status
        report.delivery_error = result.error

    if existing and existing.hermes_delivery_status == "posted":
        report.hermes_delivery_status = existing.hermes_delivery_status
        report.hermes_delivery_error = existing.hermes_delivery_error
    else:
        from app.services.hermes import post_lesson
        hermes_result = post_lesson(report)
        report.hermes_delivery_status = hermes_result.status
        report.hermes_delivery_error = hermes_result.error

    write_report(report)
    metadata["report_path"] = str(report_path(metadata["run_id"]))
    return metadata


def create_run(request: CreateRunRequest) -> RunResponse:
    from app.rl.baseline import evaluate_random_baseline
    from app.rl.eval import evaluate_policy
    from app.rl.train import train_policy

    run_id = f"run_{uuid.uuid4().hex[:10]}"
    started_at = _now_iso()
    run_dir = _run_dir(run_id)
    (run_dir / "model").mkdir(parents=True, exist_ok=True)
    (run_dir / "metrics").mkdir(parents=True, exist_ok=True)
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)

    config = request.model_dump()
    template = f"roomba.room-{request.room_size}.dirt-{request.dirt_count}"

    metadata = {
        "run_id": run_id,
        "status": "running",
        "started_at": started_at,
        "ended_at": None,
        "duration_sec": None,
        "config": config,
        "metrics": None,
        "model_path": None,
        "metrics_path": None,
        "error": None,
        "report_path": None,
        "nia_context": None,
    }
    _write_metadata(run_id, metadata)

    from app.services.hermes import query_nia
    nia_context = query_nia(template, config)
    if nia_context:
        metadata["nia_context"] = nia_context
        _write_metadata(run_id, metadata)

    try:
        model_path = train_policy(
            run_id=run_id,
            env_id=request.env_id,
            total_timesteps=request.total_timesteps,
            seed=request.seed,
            eval_seed_offset=request.eval_seed_offset,
            room_size=request.room_size,
            max_steps=request.max_steps,
            dirt_count=request.dirt_count,
            obstacle_count=request.obstacle_count,
            layout_mode=request.layout_mode,
            sensor_mode=request.sensor_mode,
            lidar_rays=request.lidar_rays,
            device=request.device,
        )

        eval_metrics = evaluate_policy(
            run_id=run_id,
            env_id=request.env_id,
            episodes=request.eval_episodes,
            room_size=request.room_size,
            max_steps=request.max_steps,
            dirt_count=request.dirt_count,
            seed=request.seed,
            eval_seed_offset=request.eval_seed_offset,
            obstacle_count=request.obstacle_count,
            layout_mode=request.layout_mode,
            sensor_mode=request.sensor_mode,
            lidar_rays=request.lidar_rays,
        )

        random_metrics = evaluate_random_baseline(
            env_id=request.env_id,
            episodes=request.eval_episodes,
            room_size=request.room_size,
            max_steps=request.max_steps,
            dirt_count=request.dirt_count,
            seed=request.seed,
            eval_seed_offset=request.eval_seed_offset,
            obstacle_count=request.obstacle_count,
            layout_mode=request.layout_mode,
            sensor_mode=request.sensor_mode,
            lidar_rays=request.lidar_rays,
        )

        metrics = {
            "ppo": eval_metrics,
            "random_baseline": random_metrics,
            "ppo_beats_random": (
                eval_metrics["success_rate"] >= random_metrics["random_success_rate"]
                and eval_metrics["avg_remaining_dirt"] <= random_metrics["random_avg_remaining_dirt"]
            ),
        }

        metrics_path = run_dir / "metrics" / "combined_metrics.json"
        metrics_path.write_text(json.dumps(metrics, indent=2))

        metadata.update(
            {
                "status": "completed",
                "ended_at": _now_iso(),
                "metrics": metrics,
                "model_path": str(model_path),
                "metrics_path": str(metrics_path),
                "error": None,
            }
        )
        metadata["duration_sec"] = (
            datetime.fromisoformat(metadata["ended_at"]) - datetime.fromisoformat(started_at)
        ).total_seconds()
        metadata = _finalize_report(metadata)
        _write_metadata(run_id, metadata)

    except Exception as exc:
        error_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        (run_dir / "logs" / "error.txt").write_text(error_text)

        metadata.update(
            {
                "status": "failed",
                "ended_at": _now_iso(),
                "error": str(exc),
            }
        )
        metadata["duration_sec"] = (
            datetime.fromisoformat(metadata["ended_at"]) - datetime.fromisoformat(started_at)
        ).total_seconds()
        metadata = _finalize_report(metadata)
        _write_metadata(run_id, metadata)

    return RunResponse(**metadata)


def complete_run(run_id: str, request: CompleteRunRequest) -> RunResponse:
    existing = _read_metadata(run_id) or {
        "run_id": run_id,
        "started_at": None,
    }
    metadata = {
        **existing,
        "run_id": run_id,
        "status": request.status,
        "ended_at": existing.get("ended_at") or _now_iso(),
        "config": request.config or existing.get("config") or {},
        "metrics": request.metrics,
        "model_path": request.model_path,
        "metrics_path": request.metrics_path,
        "error": request.error,
        "report_path": existing.get("report_path"),
    }
    if metadata.get("started_at"):
        metadata["duration_sec"] = (
            datetime.fromisoformat(metadata["ended_at"]) - datetime.fromisoformat(metadata["started_at"])
        ).total_seconds()
    else:
        metadata["duration_sec"] = existing.get("duration_sec")

    metadata = _finalize_report(metadata)
    _write_metadata(run_id, metadata)
    return RunResponse(**metadata)


def get_run(run_id: str) -> Optional[RunResponse]:
    metadata = _read_metadata(run_id)
    if metadata is None:
        return None
    return RunResponse(**metadata)


def list_runs():
    items = []
    for run_dir in sorted(RUNS_DIR.glob("run_*"), reverse=True):
        metadata = _read_metadata(run_dir.name)
        if metadata:
            items.append(metadata)
    return {"runs": items}
