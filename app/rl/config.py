from dataclasses import dataclass


@dataclass(frozen=True)
class RunConfig:
    total_timesteps: int = 200_000
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
