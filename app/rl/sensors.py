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


def dirt_proximity_vector(
    robot: np.ndarray,
    heading: float,
    dirt: np.ndarray,
    radius: float,
    obstacles: list[CircleObstacle] | None = None,
) -> np.ndarray:
    if len(dirt) == 0:
        return np.zeros(3, dtype=np.float32)

    obstacles = obstacles or []
    vectors = dirt - robot
    distances = np.linalg.norm(vectors, axis=1)
    visible_indices = [
        index
        for index, distance in enumerate(distances)
        if float(distance) <= radius
        and _line_of_sight_clear(robot, dirt[index], obstacles)
    ]
    if not visible_indices:
        return np.zeros(3, dtype=np.float32)

    nearest_index = min(visible_indices, key=lambda index: distances[index])
    nearest_distance = float(distances[nearest_index])
    if nearest_distance > radius:
        return np.zeros(3, dtype=np.float32)

    dx, dy = vectors[nearest_index]
    forward = (float(dx) * np.cos(heading)) + (float(dy) * np.sin(heading))
    left = (-float(dx) * np.sin(heading)) + (float(dy) * np.cos(heading))
    intensity = 1.0 - (nearest_distance / radius)
    return np.array(
        [
            np.clip(forward / radius, -1.0, 1.0),
            np.clip(left / radius, -1.0, 1.0),
            np.clip(intensity, 0.0, 1.0),
        ],
        dtype=np.float32,
    )


def _line_of_sight_clear(
    start: np.ndarray,
    end: np.ndarray,
    obstacles: list[CircleObstacle],
) -> bool:
    segment = end - start
    segment_length_squared = float(np.dot(segment, segment))
    if segment_length_squared == 0.0:
        return True

    for obstacle in obstacles:
        center = np.array([obstacle.x, obstacle.y], dtype=np.float32)
        t = float(np.dot(center - start, segment) / segment_length_squared)
        t = float(np.clip(t, 0.0, 1.0))
        closest = start + segment * t
        if np.linalg.norm(closest - center) <= obstacle.radius:
            return False
    return True


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
