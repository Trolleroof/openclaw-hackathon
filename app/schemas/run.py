from pydantic import BaseModel, Field
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
    run_id: str
    status: str
    config: Dict[str, Any]
    metrics: Optional[Dict[str, Any]] = None
    model_path: Optional[str] = None
    metrics_path: Optional[str] = None
    error: Optional[str] = None
