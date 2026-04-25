import argparse
import json
from pathlib import Path

from PIL import Image
from stable_baselines3 import PPO

from app.config import RUNS_DIR
from app.rl.env import RoombaEnv
from app.rl.telemetry import run_policy_episode


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
    seed: int = 0,
    episodes: int = 1,
    fps: int = 6,
    hold_final_frames: int = 18,
    room_size: float = 10.0,
    max_steps: int = 200,
    dirt_count: int = 3,
) -> dict:
    run_dir = RUNS_DIR / run_id
    model_path = run_dir / "model" / "roomba_policy.zip"
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    model = PPO.load(str(model_path))
    gif_paths = []
    trajectory_paths = []

    for episode_index in range(episodes):
        episode_seed = seed + episode_index
        env = RoombaEnv(
            room_size=room_size,
            max_steps=max_steps,
            dirt_count=dirt_count,
            render_mode="rgb_array",
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
        "fps": fps,
        "hold_final_frames": hold_final_frames,
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
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--fps", type=int, default=6)
    parser.add_argument("--hold-final-frames", type=int, default=18)
    parser.add_argument("--room-size", type=float, default=10.0)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--dirt-count", type=int, default=3)
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
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
