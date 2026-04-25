from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any

from app.rl.train import DEFAULT_TOTAL_TIMESTEPS


class CreateRunRequest(BaseModel):
    total_timesteps: int = Field(default=DEFAULT_TOTAL_TIMESTEPS, ge=1_000, le=2_000_000)
    eval_episodes: int = Field(default=50, ge=1, le=1_000)
    seed: int = Field(default=42)
    room_size: float = Field(default=10.0, gt=1.0)
    max_steps: int = Field(default=200, ge=20, le=5_000)
    dirt_count: int = Field(default=3, ge=1, le=100)
    device: str = Field(default="auto", pattern="^(auto|cpu|cuda|mps)$")


class RunResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    run_id: str
    status: str
    config: Dict[str, Any]
    metrics: Optional[Dict[str, Any]] = None
    model_path: Optional[str] = None
    metrics_path: Optional[str] = None
    error: Optional[str] = None
    report_path: Optional[str] = None


class CompleteRunRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: str = Field(pattern="^(completed|success|failed|early_stop)$")
    config: Dict[str, Any] = Field(default_factory=dict)
    metrics: Optional[Dict[str, Any]] = None
    model_path: Optional[str] = None
    metrics_path: Optional[str] = None
    error: Optional[str] = None


class RunReport(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    run_id: str
    status: str
    started_at: Optional[str] = None
    ended_at: str
    duration_sec: Optional[float] = None
    template: str
    algo: str
    config: Dict[str, Any]
    steps: Optional[int] = None
    episodes: Optional[int] = None
    mean_return: Optional[float] = None
    best_return: Optional[float] = None
    checkpoint_uri: Optional[str] = None
    artifact_links: Dict[str, str] = Field(default_factory=dict)
    error: Optional[str] = None
    model_summary: str
    markdown: str
    agentmail_message_id: Optional[str] = None
    agentmail_thread_id: Optional[str] = None
    delivery_status: str = "pending"
    delivery_error: Optional[str] = None
    created_at: str
