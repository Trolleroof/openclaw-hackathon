from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from app.rl.config import RunConfig


DEFAULT_RUN_CONFIG = RunConfig()


class CreateRunRequest(BaseModel):
    total_timesteps: int = Field(default=DEFAULT_RUN_CONFIG.total_timesteps, ge=1_000, le=2_000_000)
    eval_episodes: int = Field(default=DEFAULT_RUN_CONFIG.eval_episodes, ge=1, le=1_000)
    seed: int = Field(default=DEFAULT_RUN_CONFIG.seed)
    eval_seed_offset: int = Field(default=DEFAULT_RUN_CONFIG.eval_seed_offset, ge=1)
    room_size: float = Field(default=DEFAULT_RUN_CONFIG.room_size, gt=1.0)
    max_steps: int = Field(default=DEFAULT_RUN_CONFIG.max_steps, ge=20, le=5_000)
    dirt_count: int = Field(default=DEFAULT_RUN_CONFIG.dirt_count, ge=1, le=100)
    obstacle_count: int = Field(default=DEFAULT_RUN_CONFIG.obstacle_count, ge=0, le=100)
    layout_mode: str = Field(default=DEFAULT_RUN_CONFIG.layout_mode, pattern="^(preset|random)$")
    sensor_mode: str = Field(default=DEFAULT_RUN_CONFIG.sensor_mode, pattern="^(oracle|lidar_local_dirt)$")
    lidar_rays: int = Field(default=DEFAULT_RUN_CONFIG.lidar_rays, ge=0, le=128)
    device: str = Field(default=DEFAULT_RUN_CONFIG.device, pattern="^(auto|cpu|cuda|mps)$")


class RunResponse(BaseModel):
    run_id: str
    status: str
    config: Dict[str, Any]
    metrics: Optional[Dict[str, Any]] = None
    model_path: Optional[str] = None
    metrics_path: Optional[str] = None
    error: Optional[str] = None
