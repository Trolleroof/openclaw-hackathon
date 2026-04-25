import json
import traceback
import uuid
from pathlib import Path
from typing import Optional

from app.config import RUNS_DIR
from app.schemas.run import CreateRunRequest, RunResponse
from app.rl.train import train_policy
from app.rl.eval import evaluate_policy
from app.rl.baseline import evaluate_random_baseline


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


def create_run(request: CreateRunRequest) -> RunResponse:
    run_id = f"run_{uuid.uuid4().hex[:10]}"
    run_dir = _run_dir(run_id)
    (run_dir / "model").mkdir(parents=True, exist_ok=True)
    (run_dir / "metrics").mkdir(parents=True, exist_ok=True)
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)

    config = request.model_dump()

    metadata = {
        "run_id": run_id,
        "status": "running",
        "config": config,
        "metrics": None,
        "model_path": None,
        "metrics_path": None,
        "error": None,
    }
    _write_metadata(run_id, metadata)

    try:
        model_path = train_policy(
            run_id=run_id,
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
                "metrics": metrics,
                "model_path": str(model_path),
                "metrics_path": str(metrics_path),
                "error": None,
            }
        )
        _write_metadata(run_id, metadata)

    except Exception as exc:
        error_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        (run_dir / "logs" / "error.txt").write_text(error_text)

        metadata.update(
            {
                "status": "failed",
                "error": str(exc),
            }
        )
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
