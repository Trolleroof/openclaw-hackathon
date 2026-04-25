import argparse
import json

from app.rl.env import RoombaEnv


def evaluate_random_baseline(
    episodes: int = 50,
    room_size: float = 10.0,
    max_steps: int = 200,
    dirt_count: int = 3,
):
    env = RoombaEnv(
        room_size=room_size,
        max_steps=max_steps,
        dirt_count=dirt_count,
    )

    successes = 0
    remaining = []
    rewards = []

    for episode_index in range(episodes):
        obs, _ = env.reset(seed=episode_index)
        total_reward = 0.0
        last_info = {"remaining_dirt": dirt_count, "steps": 0}

        for _ in range(env.max_steps):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += float(reward)
            last_info = info

            if terminated or truncated:
                break

        successes += int(last_info["remaining_dirt"] == 0)
        remaining.append(last_info["remaining_dirt"])
        rewards.append(total_reward)

    return {
        "episodes": episodes,
        "random_success_rate": successes / episodes,
        "random_avg_remaining_dirt": sum(remaining) / episodes,
        "random_avg_reward": sum(rewards) / episodes,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--room-size", type=float, default=10.0)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--dirt-count", type=int, default=3)
    args = parser.parse_args()

    metrics = evaluate_random_baseline(
        episodes=args.episodes,
        room_size=args.room_size,
        max_steps=args.max_steps,
        dirt_count=args.dirt_count,
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
