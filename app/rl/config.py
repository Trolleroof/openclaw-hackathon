from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class RunConfig:
    total_timesteps: int = 60_000
    eval_episodes: int = 50
    seed: int = 42
    eval_seed_offset: int = 10_000
    room_size: float = 10.0
    max_steps: int = 200
    dirt_count: int = 6
    obstacle_count: int = 4
    layout_mode: str = "random"
    sensor_mode: str = "lidar_local_dirt"
    lidar_rays: int = 16
    device: str = "auto"


def load_saved_run_config(run_dir: Path) -> dict:
    config_path = run_dir / "rl_config.json"
    if config_path.exists():
        return json.loads(config_path.read_text())

    metadata_path = run_dir / "metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text())
        return metadata.get("config", {})

    return {}
