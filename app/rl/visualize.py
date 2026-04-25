import argparse
import json
from pathlib import Path

from PIL import Image
from stable_baselines3 import PPO

from app.config import RUNS_DIR
from app.rl.config import load_saved_run_config
from app.rl.factory import make_env
from app.rl.telemetry import run_policy_episode


LEGACY_VISUAL_CONFIG = {
    "seed": 0,
    "eval_seed_offset": 0,
    "room_size": 10.0,
    "max_steps": 200,
    "dirt_count": 3,
    "obstacle_count": 0,
    "layout_mode": "preset",
    "sensor_mode": "oracle",
    "lidar_rays": 0,
    "env_id": None,
}


def _resolve(value, config: dict, key: str):
    if value is not None:
        return value
    return config.get(key, LEGACY_VISUAL_CONFIG[key])


def _write_gif(frames, path: Path, fps: int, hold_final_frames: int = 0) -> None:
    images = [Image.fromarray(frame) for frame in frames if frame is not None]
    if not images:
        raise ValueError("No frames captured for GIF export")

    if hold_final_frames > 0:
        images.extend([images[-1].copy() for _ in range(hold_final_frames)])

    duration_ms = int(1000 / max(fps, 1))
    images[0].save(
        path,
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0,
    )


def generate_run_artifacts(
    run_id: str,
    seed: int | None = None,
    episodes: int = 1,
    fps: int = 6,
    hold_final_frames: int = 18,
    room_size: float | None = None,
    max_steps: int | None = None,
    dirt_count: int | None = None,
    obstacle_count: int | None = None,
    layout_mode: str | None = None,
    sensor_mode: str | None = None,
    lidar_rays: int | None = None,
    env_id: str | None = None,
) -> dict:
    run_dir = RUNS_DIR / run_id
    model_path = run_dir / "model" / "roomba_policy.zip"
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    saved_config = load_saved_run_config(run_dir)
    if seed is None:
        seed = int(saved_config.get("seed", LEGACY_VISUAL_CONFIG["seed"])) + int(
            saved_config.get("eval_seed_offset", LEGACY_VISUAL_CONFIG["eval_seed_offset"])
        )
    else:
        seed = int(seed)
    room_size = float(_resolve(room_size, saved_config, "room_size"))
    max_steps = int(_resolve(max_steps, saved_config, "max_steps"))
    dirt_count = int(_resolve(dirt_count, saved_config, "dirt_count"))
    obstacle_count = int(_resolve(obstacle_count, saved_config, "obstacle_count"))
    layout_mode = str(_resolve(layout_mode, saved_config, "layout_mode"))
    sensor_mode = str(_resolve(sensor_mode, saved_config, "sensor_mode"))
    lidar_rays = int(_resolve(lidar_rays, saved_config, "lidar_rays"))
    env_id = _resolve(env_id, saved_config, "env_id")

    model = PPO.load(str(model_path))
    gif_paths = []
    trajectory_paths = []

    for episode_index in range(episodes):
        episode_seed = seed + episode_index
        env = make_env(
            env_id=env_id,
            room_size=room_size,
            max_steps=max_steps,
            dirt_count=dirt_count,
            obstacle_count=obstacle_count,
            layout_mode=layout_mode,
            sensor_mode=sensor_mode,
            lidar_rays=lidar_rays,
            render_mode="rgb_array",
        )
        if env.observation_space.shape != model.observation_space.shape:
            raise ValueError(
                "Visualization env observation shape "
                f"{env.observation_space.shape} does not match model "
                f"{model.observation_space.shape}. Pass the run's layout and sensor flags."
            )
        rollout = run_policy_episode(
            model=model,
            env=env,
            seed=episode_seed,
            include_steps=True,
            capture_frames=True,
        )

        gif_path = artifacts_dir / f"episode_seed_{episode_seed}.gif"
        trajectory_path = artifacts_dir / f"episode_seed_{episode_seed}_trajectory.json"

        _write_gif(rollout["frames"], gif_path, fps=fps, hold_final_frames=hold_final_frames)
        trajectory_payload = {
            "run_id": run_id,
            "episode_seed": episode_seed,
            "summary": rollout["summary"],
            "steps": rollout["steps"],
        }
        trajectory_path.write_text(json.dumps(trajectory_payload, indent=2))

        gif_paths.append(str(gif_path))
        trajectory_paths.append(str(trajectory_path))

    manifest = {
        "run_id": run_id,
        "seed": seed,
        "fps": fps,
        "hold_final_frames": hold_final_frames,
        "room_size": room_size,
        "max_steps": max_steps,
        "dirt_count": dirt_count,
        "obstacle_count": obstacle_count,
        "layout_mode": layout_mode,
        "sensor_mode": sensor_mode,
        "lidar_rays": lidar_rays,
        "env_id": env_id,
        "gif_paths": gif_paths,
        "trajectory_paths": trajectory_paths,
    }
    manifest_path = artifacts_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--fps", type=int, default=6)
    parser.add_argument("--hold-final-frames", type=int, default=18)
    parser.add_argument("--room-size", type=float)
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--dirt-count", type=int)
    parser.add_argument("--obstacle-count", type=int)
    parser.add_argument("--layout-mode", choices=["preset", "random"])
    parser.add_argument("--sensor-mode", choices=["oracle", "lidar_local_dirt"])
    parser.add_argument("--lidar-rays", type=int)
    parser.add_argument("--env-id")
    args = parser.parse_args()

    manifest = generate_run_artifacts(
        run_id=args.run_id,
        seed=args.seed,
        episodes=args.episodes,
        fps=args.fps,
        hold_final_frames=args.hold_final_frames,
        room_size=args.room_size,
        max_steps=args.max_steps,
        dirt_count=args.dirt_count,
        obstacle_count=args.obstacle_count,
        layout_mode=args.layout_mode,
        sensor_mode=args.sensor_mode,
        lidar_rays=args.lidar_rays,
        env_id=args.env_id,
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
