from __future__ import annotations

from app.rl.env import RoombaEnv


class FullCleaningEnv(RoombaEnv):
    """
    Full ClawLab cleaning task.

    This keeps the original RoombaEnv task mechanics for dirt removal,
    collision handling, reward components, and telemetry, while defaulting to
    the final random layout with lidar and obstacle-aware local dirt sensing.
    """

    def __init__(
        self,
        room_size: float = 10.0,
        max_steps: int = 200,
        dirt_count: int = 6,
        clean_radius: float = 0.5,
        forward_step: float = 0.3,
        turn_angle: float = 0.3,
        seed: int | None = None,
        render_mode: str | None = None,
        layout_mode: str = "random",
        sensor_mode: str = "lidar_local_dirt",
        obstacle_count: int = 3,
        lidar_rays: int = 16,
        dirt_sensor_radius: float = 4.0,
        eval_seed_offset: int = 10_000,
    ):
        super().__init__(
            room_size=room_size,
            max_steps=max_steps,
            dirt_count=dirt_count,
            clean_radius=clean_radius,
            forward_step=forward_step,
            turn_angle=turn_angle,
            seed=seed,
            render_mode=render_mode,
            layout_mode=layout_mode,
            sensor_mode=sensor_mode,
            obstacle_count=obstacle_count,
            lidar_rays=lidar_rays,
            dirt_sensor_radius=dirt_sensor_radius,
            eval_seed_offset=eval_seed_offset,
        )
