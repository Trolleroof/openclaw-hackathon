from __future__ import annotations

import importlib
import inspect
from typing import Any

import gymnasium as gym

import app.rl.envs
from app.rl.env import RoombaEnv
from app.rl.envs.registry import all_env_specs


def make_env(env_id: str | None = None, render_mode: str | None = None, **config):
    if env_id:
        kwargs = _filter_env_kwargs(env_id, {**config, "render_mode": render_mode})
        return gym.make(env_id, **kwargs)

    kwargs = {
        "room_size": config.get("room_size", 10.0),
        "max_steps": config.get("max_steps", 200),
        "dirt_count": config.get("dirt_count", 3),
        "seed": config.get("seed"),
        "layout_mode": config.get("layout_mode", "preset"),
        "sensor_mode": config.get("sensor_mode", "oracle"),
        "obstacle_count": config.get("obstacle_count", 0),
        "lidar_rays": config.get("lidar_rays", 0),
        "eval_seed_offset": config.get("eval_seed_offset", 10_000),
        "render_mode": render_mode,
    }
    return RoombaEnv(**kwargs)


def _filter_env_kwargs(env_id: str, config: dict[str, Any]) -> dict[str, Any]:
    specs = all_env_specs()
    if env_id not in specs:
        raise ValueError(f"Unknown Apollo Labs env_id: {env_id}")

    constructor = _env_constructor(specs[env_id].entry_point)
    signature = inspect.signature(constructor.__init__)
    accepted = set(signature.parameters) - {"self"}
    return {
        key: value
        for key, value in config.items()
        if key in accepted and value is not None
    }


def _env_constructor(entry_point: str):
    module_name, class_name = entry_point.split(":")
    module = importlib.import_module(module_name)
    return getattr(module, class_name)
