from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import RUNS_DIR
from app.rl.benchmark import read_progress_snapshots, write_benchmark_summary
from app.rl.eval import evaluate_policy
from app.rl.train import train_policy


CORE_ENVS = [
    "ClawLab/ObstacleAvoidance-v0",
    "ClawLab/PointNavigation-v0",
    "ClawLab/DirtSeeking-v0",
    "ClawLab/FullCleaning-v0",
]


def run_curriculum(
    env_ids: list[str],
    steps: int,
    seeds: list[int],
    eval_episodes: int,
    device: str,
    prefix: str,
    progress_eval_interval: int,
    progress_eval_episodes: int,
) -> dict:
    run_metrics = []
    for env_id in env_ids:
        env_slug = env_id.split("/", 1)[1].replace("-", "_").lower()
        for seed in seeds:
            run_id = f"{prefix}_{env_slug}_seed{seed}"
            train_policy(
                run_id=run_id,
                env_id=env_id,
                total_timesteps=steps,
                seed=seed,
                device=device,
                verbose=0,
                progress_eval_interval=progress_eval_interval,
                progress_eval_episodes=progress_eval_episodes,
            )
            metrics = evaluate_policy(run_id=run_id, episodes=eval_episodes)
            progress = read_progress_snapshots(
                RUNS_DIR / run_id / "metrics" / "train_progress.jsonl"
            )
            run_metrics.append(
                {
                    "run_id": run_id,
                    "env_id": env_id,
                    "metrics": metrics,
                    "progress": progress,
                }
            )

    summary_path = RUNS_DIR / f"{prefix}_summary.json"
    return write_benchmark_summary(run_metrics, summary_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["smoke", "core"], default="core")
    parser.add_argument("--steps", type=int, default=50_000)
    parser.add_argument("--seeds", default="1")
    parser.add_argument("--eval-episodes", type=int, default=20)
    parser.add_argument("--device", default="cpu", choices=["auto", "cpu", "cuda", "mps"])
    parser.add_argument("--prefix", default="clawlab")
    parser.add_argument("--progress-eval-interval", type=int)
    parser.add_argument("--progress-eval-episodes", type=int, default=2)
    args = parser.parse_args()

    if args.profile == "smoke":
        steps = 1_024
        seeds = [1]
        eval_episodes = 1
        prefix = f"{args.prefix}_smoke"
        progress_eval_interval = args.progress_eval_interval or 512
        progress_eval_episodes = 1
    else:
        steps = args.steps
        seeds = [int(seed) for seed in args.seeds.split(",") if seed.strip()]
        eval_episodes = args.eval_episodes
        prefix = args.prefix
        progress_eval_interval = args.progress_eval_interval or max(steps // 5, 1_000)
        progress_eval_episodes = args.progress_eval_episodes

    summary = run_curriculum(
        env_ids=CORE_ENVS,
        steps=steps,
        seeds=seeds,
        eval_episodes=eval_episodes,
        device=args.device,
        prefix=prefix,
        progress_eval_interval=progress_eval_interval,
        progress_eval_episodes=progress_eval_episodes,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
