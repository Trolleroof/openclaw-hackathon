from __future__ import annotations

from dataclasses import dataclass

import gymnasium as gym
from gymnasium.envs.registration import registry


@dataclass(frozen=True)
class ClawLabEnvSpec:
    id: str
    entry_point: str
    task: str
    description: str
    default_kwargs: dict
    reward_components: tuple[str, ...]
    metrics: tuple[str, ...]


COMMON_METRICS = (
    "success_rate",
    "timeout_rate",
    "avg_reward",
    "avg_steps",
    "avg_wall_hits",
    "avg_obstacle_hits",
    "avg_path_length",
    "reward_hacking",
)


CLAWLAB_ENVS: dict[str, ClawLabEnvSpec] = {
    "ClawLab/ObstacleAvoidance-v0": ClawLabEnvSpec(
        id="ClawLab/ObstacleAvoidance-v0",
        entry_point="app.rl.envs.obstacle_avoidance:ObstacleAvoidanceEnv",
        task="obstacle_avoidance",
        description="Avoid walls and circular obstacles while maintaining movement.",
        default_kwargs={"obstacle_count": 6, "lidar_rays": 16},
        reward_components=(
            "step_penalty",
            "forward_reward",
            "clearance_reward",
            "wall_penalty",
            "obstacle_penalty",
            "survival_bonus",
        ),
        metrics=COMMON_METRICS,
    ),
    "ClawLab/PointNavigation-v0": ClawLabEnvSpec(
        id="ClawLab/PointNavigation-v0",
        entry_point="app.rl.envs.point_navigation:PointNavigationEnv",
        task="point_navigation",
        description="Reach randomized point goals efficiently while avoiding obstacles.",
        default_kwargs={"obstacle_count": 2, "lidar_rays": 8},
        reward_components=(
            "step_penalty",
            "progress",
            "alignment",
            "turn_penalty",
            "wall_penalty",
            "obstacle_penalty",
            "success",
        ),
        metrics=COMMON_METRICS,
    ),
    "ClawLab/DirtSeeking-v0": ClawLabEnvSpec(
        id="ClawLab/DirtSeeking-v0",
        entry_point="app.rl.envs.dirt_seeking:DirtSeekingEnv",
        task="dirt_seeking",
        description="Use local dirt sensing to approach a visible dirt particle.",
        default_kwargs={"dirt_count": 3, "obstacle_count": 1, "lidar_rays": 8},
        reward_components=(
            "step_penalty",
            "dirt_visible",
            "dirt_progress",
            "found_dirt",
            "wall_penalty",
            "obstacle_penalty",
        ),
        metrics=COMMON_METRICS + ("avg_cleaned_dirt", "avg_first_clean_step"),
    ),
    "ClawLab/FullCleaning-v0": ClawLabEnvSpec(
        id="ClawLab/FullCleaning-v0",
        entry_point="app.rl.envs.full_cleaning:FullCleaningEnv",
        task="full_cleaning",
        description="Clean randomized dirt with local dirt sensing, LiDAR, and obstacles.",
        default_kwargs={"dirt_count": 6, "obstacle_count": 3, "lidar_rays": 16},
        reward_components=(
            "step_penalty",
            "progress",
            "alignment",
            "clean",
            "terminal",
            "turn_penalty",
            "wall_penalty",
            "obstacle_penalty",
        ),
        metrics=COMMON_METRICS + ("avg_cleaned_dirt", "avg_remaining_dirt"),
    ),
}


SCALED_VARIANTS: dict[str, tuple[str, dict, str]] = {
    "ClawLab/ObstacleAvoidanceEasy-v0": (
        "ClawLab/ObstacleAvoidance-v0",
        {"obstacle_count": 2, "max_steps": 120},
        "Easy obstacle avoidance with sparse obstacles.",
    ),
    "ClawLab/ObstacleAvoidanceDense-v0": (
        "ClawLab/ObstacleAvoidance-v0",
        {"obstacle_count": 10, "max_steps": 240},
        "Dense obstacle avoidance.",
    ),
    "ClawLab/PointNavigationOpen-v0": (
        "ClawLab/PointNavigation-v0",
        {"obstacle_count": 0},
        "Point navigation in an open room.",
    ),
    "ClawLab/PointNavigationObstacles-v0": (
        "ClawLab/PointNavigation-v0",
        {"obstacle_count": 4},
        "Point navigation with obstacles.",
    ),
    "ClawLab/DirtSeekingLocal-v0": (
        "ClawLab/DirtSeeking-v0",
        {"dirt_count": 1, "obstacle_count": 0, "dirt_sensor_radius": 5.0},
        "Local dirt seeking with one dirt particle.",
    ),
    "ClawLab/DirtSeekingSparse-v0": (
        "ClawLab/DirtSeeking-v0",
        {"dirt_count": 4, "obstacle_count": 3, "dirt_sensor_radius": 3.0},
        "Sparse dirt seeking with obstacles.",
    ),
    "ClawLab/FullCleaningEasy-v0": (
        "ClawLab/FullCleaning-v0",
        {"dirt_count": 3, "obstacle_count": 0},
        "Easy full cleaning without obstacles.",
    ),
    "ClawLab/FullCleaningRandom-v0": (
        "ClawLab/FullCleaning-v0",
        {"dirt_count": 6, "obstacle_count": 3},
        "Randomized full cleaning benchmark.",
    ),
    "ClawLab/FullCleaningDenseObstacles-v0": (
        "ClawLab/FullCleaning-v0",
        {"dirt_count": 6, "obstacle_count": 8, "max_steps": 260},
        "Full cleaning with dense obstacles.",
    ),
}


def _variant_spec(env_id: str, base_id: str, kwargs: dict, description: str) -> ClawLabEnvSpec:
    base = CLAWLAB_ENVS[base_id]
    merged_kwargs = {**base.default_kwargs, **kwargs}
    return ClawLabEnvSpec(
        id=env_id,
        entry_point=base.entry_point,
        task=base.task,
        description=description,
        default_kwargs=merged_kwargs,
        reward_components=base.reward_components,
        metrics=base.metrics,
    )


def all_env_specs() -> dict[str, ClawLabEnvSpec]:
    specs = dict(CLAWLAB_ENVS)
    for env_id, (base_id, kwargs, description) in SCALED_VARIANTS.items():
        specs[env_id] = _variant_spec(env_id, base_id, kwargs, description)
    return specs


def register_clawlab_envs() -> None:
    for spec in all_env_specs().values():
        if spec.id in registry:
            continue
        gym.register(
            id=spec.id,
            entry_point=spec.entry_point,
            kwargs=dict(spec.default_kwargs),
        )


def list_envs() -> list[dict]:
    return [
        {
            "id": spec.id,
            "task": spec.task,
            "description": spec.description,
            "default_kwargs": dict(spec.default_kwargs),
            "reward_components": list(spec.reward_components),
            "metrics": list(spec.metrics),
        }
        for spec in all_env_specs().values()
    ]


def describe_env(env_id: str) -> dict:
    specs = all_env_specs()
    if env_id not in specs:
        raise ValueError(f"Unknown ClawLab env_id: {env_id}")
    spec = specs[env_id]
    return {
        "id": spec.id,
        "task": spec.task,
        "description": spec.description,
        "default_kwargs": dict(spec.default_kwargs),
        "reward_components": list(spec.reward_components),
        "metrics": list(spec.metrics),
    }
