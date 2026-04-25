from fastapi import FastAPI, HTTPException

from app.schemas.run import CreateRunRequest, RunResponse
from app.services.runner import create_run, get_run, list_runs

app = FastAPI(
    title="Roomba RL FastAPI",
    description="Phase 1 MVP: train/evaluate a tiny 2D Roomba-style RL environment.",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/runs", response_model=RunResponse)
def create_training_run(request: CreateRunRequest):
    """
    Create and execute a training run.

    This is synchronous for Phase 1 simplicity.
    Later, this should become a background job queue.
    """
    return create_run(request)


@app.get("/api/runs")
def get_runs():
    return list_runs()


@app.get("/api/runs/{run_id}", response_model=RunResponse)
def get_training_run(run_id: str):
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
