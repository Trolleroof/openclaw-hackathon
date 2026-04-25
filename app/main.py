from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas.run import CompleteRunRequest, CreateRunRequest, RunResponse, RunReport
from app.services.reports import list_reports, read_report
from app.services.runner import complete_run, create_run, get_run, list_runs

app = FastAPI(
    title="Roomba RL FastAPI",
    description="Phase 1 MVP: train/evaluate a tiny 2D Roomba-style RL environment.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.post("/api/v1/runs/{run_id}/complete", response_model=RunResponse)
def complete_training_run(run_id: str, request: CompleteRunRequest):
    return complete_run(run_id, request)


@app.get("/api/v1/reports", response_model=list[RunReport])
def get_reports():
    return list_reports()


@app.get("/api/v1/runs/{run_id}/report", response_model=RunReport)
def get_run_report(run_id: str):
    report = read_report(run_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
