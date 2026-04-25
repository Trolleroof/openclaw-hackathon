import argparse
import json

from stable_baselines3 import PPO

from app.config import RUNS_DIR
from app.rl.env import RoombaEnv


def evaluate_policy(
    run_id: str,
    episodes: int = 50,
    room_size: float = 10.0,
    max_steps: int = 200,
    dirt_count: int = 3,
):
    run_dir = RUNS_DIR / run_id
    model_path = run_dir / "model" / "roomba_policy.zip"
    metrics_dir = run_dir / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)

    env = RoombaEnv(
        room_size=room_size,
        max_steps=max_steps,
        dirt_count=dirt_count,
    )

    model = PPO.load(str(model_path))

    successes = 0
    rewards = []
    steps_list = []
    remaining_dirt_list = []
    wall_hits = 0

    for episode_index in range(episodes):
        obs, _ = env.reset(seed=episode_index)
        total_reward = 0.0
        last_info = {"remaining_dirt": dirt_count, "steps": 0}

        for _ in range(env.max_steps):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += float(reward)

            if info.get("hit_wall"):
                wall_hits += 1

            last_info = info

            if terminated or truncated:
                break

        success = last_info["remaining_dirt"] == 0
        successes += int(success)
        rewards.append(total_reward)
        steps_list.append(last_info["steps"])
        remaining_dirt_list.append(last_info["remaining_dirt"])

    metrics = {
        "episodes": episodes,
        "success_rate": successes / episodes,
        "avg_reward": sum(rewards) / episodes,
        "avg_steps": sum(steps_list) / episodes,
        "avg_remaining_dirt": sum(remaining_dirt_list) / episodes,
        "wall_hits": wall_hits,
    }

    metrics_path = metrics_dir / "eval_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2))

    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--room-size", type=float, default=10.0)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--dirt-count", type=int, default=3)
    args = parser.parse_args()

    metrics = evaluate_policy(
        run_id=args.run_id,
        episodes=args.episodes,
        room_size=args.room_size,
        max_steps=args.max_steps,
        dirt_count=args.dirt_count,
    )

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
