from __future__ import annotations

import numpy as np

from app.rl.layouts import CircleObstacle


def cast_lidar_rays(
    robot: np.ndarray,
    heading: float,
    room_size: float,
    obstacles: list[CircleObstacle],
    ray_count: int = 16,
    max_range: float = 5.0,
    step_size: float = 0.05,
) -> np.ndarray:
    readings = []
    for ray_index in range(ray_count):
        angle = heading + (2 * np.pi * ray_index / ray_count)
        direction = np.array([np.cos(angle), np.sin(angle)], dtype=np.float32)
        distance = _ray_distance(robot, direction, room_size, obstacles, max_range, step_size)
        readings.append(distance / max_range)
    return np.array(readings, dtype=np.float32)


def local_dirt_signal(robot: np.ndarray, dirt: np.ndarray, radius: float) -> float:
    if len(dirt) == 0:
        return 0.0
    return float(np.any(np.linalg.norm(dirt - robot, axis=1) <= radius))


def _ray_distance(
    robot: np.ndarray,
    direction: np.ndarray,
    room_size: float,
    obstacles: list[CircleObstacle],
    max_range: float,
    step_size: float,
) -> float:
    distance = 0.0
    while distance < max_range:
        point = robot + direction * distance
        if point[0] <= 0.0 or point[0] >= room_size or point[1] <= 0.0 or point[1] >= room_size:
            return distance
        for obstacle in obstacles:
            center = np.array([obstacle.x, obstacle.y], dtype=np.float32)
            if np.linalg.norm(point - center) <= obstacle.radius:
                return distance
        distance += step_size
    return max_range
