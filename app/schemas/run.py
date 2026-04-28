from pydantic import BaseModel, Field, field_validator
from pydantic import ConfigDict
from typing import Optional, Dict, Any

from app.rl.config import RunConfig
from app.rl.envs.registry import all_env_specs


DEFAULT_RUN_CONFIG = RunConfig()


class CreateRunRequest(BaseModel):
    env_id: str = Field(default="ApolloLabs/FullCleaning-v0")
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

    @field_validator("env_id")
    @classmethod
    def validate_env_id(cls, value: str) -> str:
        if value not in all_env_specs():
            raise ValueError(f"Unknown Apollo Labs env_id: {value}")
        return value


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
    nia_context: Optional[str] = None


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
    hermes_delivery_status: str = "pending"
    hermes_delivery_error: Optional[str] = None
    created_at: str
