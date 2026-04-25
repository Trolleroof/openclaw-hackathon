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
        dirt = _preset_dirt(config)
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
    obstacles = _sample_obstacles(rng, config, robot)
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


def _preset_dirt(config: LayoutConfig) -> np.ndarray:
    dirt = [
        np.clip(point, 0.5, config.room_size - 0.5).astype(np.float32)
        for point in PRESET_DIRT[: min(config.dirt_count, len(PRESET_DIRT))]
    ]

    if len(dirt) >= config.dirt_count:
        return np.array(dirt, dtype=np.float32)

    robot = np.array([1.0, 1.0], dtype=np.float32)
    grid_size = max(4, int(np.ceil(np.sqrt(config.dirt_count * 2))))
    while len(dirt) < config.dirt_count:
        coords = np.linspace(0.5, config.room_size - 0.5, grid_size, dtype=np.float32)
        for x in coords:
            for y in coords:
                point = np.array([x, y], dtype=np.float32)
                if np.linalg.norm(point - robot) < config.min_clearance:
                    continue
                if any(np.linalg.norm(point - existing) < 0.05 for existing in dirt):
                    continue
                dirt.append(point)
                if len(dirt) == config.dirt_count:
                    break
            if len(dirt) == config.dirt_count:
                break
        grid_size *= 2

    return np.array(dirt, dtype=np.float32)


def _sample_obstacles(
    rng: np.random.Generator,
    config: LayoutConfig,
    robot: np.ndarray,
) -> list[CircleObstacle]:
    obstacles = []
    attempts = 0
    while len(obstacles) < config.obstacle_count:
        attempts += 1
        if attempts > max(config.obstacle_count, 1) * 500:
            raise RuntimeError("Could not generate obstacles with requested clearance")
        point = _sample_point(rng, config.room_size)
        radius = float(rng.uniform(0.25, 0.75))
        if np.linalg.norm(point - robot) < radius + config.min_clearance:
            continue
        obstacles.append(CircleObstacle(float(point[0]), float(point[1]), radius=radius))
    return obstacles
