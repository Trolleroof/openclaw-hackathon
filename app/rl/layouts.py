from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CircleObstacle:
    x: float
    y: float
    radius: float


@dataclass(frozen=True)
class LayoutConfig:
    mode: str = "preset"
    room_size: float = 10.0
    dirt_count: int = 3
    obstacle_count: int = 0
    min_clearance: float = 0.6
    randomize_start: bool = True


@dataclass(frozen=True)
class Layout:
    robot: np.ndarray
    heading: float
    dirt: np.ndarray
    obstacles: list[CircleObstacle]


PRESET_DIRT = np.array(
    [[8.0, 8.0], [2.0, 7.0], [7.0, 2.0], [5.0, 5.0], [8.0, 3.0], [3.0, 8.0]],
    dtype=np.float32,
)


def generate_layout(config: LayoutConfig, seed: int | None = None) -> Layout:
    if config.mode == "preset":
        dirt = PRESET_DIRT[: config.dirt_count].copy()
        dirt = np.clip(dirt, 0.5, config.room_size - 0.5).astype(np.float32)
        return Layout(
            robot=np.array([1.0, 1.0], dtype=np.float32),
            heading=0.0,
            dirt=dirt,
            obstacles=[],
        )
    if config.mode != "random":
        raise ValueError(f"Unsupported layout mode: {config.mode}")

    rng = np.random.default_rng(seed)
    robot = _sample_point(rng, config.room_size)
    heading = float(rng.uniform(-np.pi, np.pi)) if config.randomize_start else 0.0
    obstacles = [
        CircleObstacle(*_sample_point(rng, config.room_size), radius=float(rng.uniform(0.25, 0.75)))
        for _ in range(config.obstacle_count)
    ]
    dirt = []
    attempts = 0
    while len(dirt) < config.dirt_count:
        attempts += 1
        if attempts > config.dirt_count * 500:
            raise RuntimeError("Could not generate layout with requested clearance")
        point = _sample_point(rng, config.room_size)
        if np.linalg.norm(point - robot) < config.min_clearance:
            continue
        if any(np.linalg.norm(point - np.array([obs.x, obs.y])) < obs.radius + config.min_clearance for obs in obstacles):
            continue
        dirt.append(point)

    return Layout(
        robot=robot.astype(np.float32),
        heading=heading,
        dirt=np.array(dirt, dtype=np.float32),
        obstacles=obstacles,
    )


def _sample_point(rng: np.random.Generator, room_size: float) -> np.ndarray:
    return rng.uniform(0.5, room_size - 0.5, size=2).astype(np.float32)
