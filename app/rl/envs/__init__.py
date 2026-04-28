from app.rl.envs.registry import (
    all_env_specs,
    describe_env,
    list_envs,
    register_apollolabs_envs,
)

register_apollolabs_envs()

__all__ = [
    "all_env_specs",
    "describe_env",
    "list_envs",
    "register_apollolabs_envs",
]
