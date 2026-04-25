from __future__ import annotations

import numpy as np


CORE_INFO_KEYS = (
    "steps",
    "hit_wall",
    "hit_obstacle",
    "reward_components",
)


def normalize_heading(heading: float) -> float:
    return float(((heading + np.pi) % (2 * np.pi)) - np.pi)


def obstacle_hit(point: np.ndarray, obstacles: list) -> bool:
    for obstacle in obstacles:
        center = np.array([obstacle.x, obstacle.y], dtype=np.float32)
        if np.linalg.norm(point - center) <= obstacle.radius:
            return True
    return False
