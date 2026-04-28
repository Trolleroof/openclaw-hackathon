# Run Specs

Prefer small configs first. Scale only after plumbing and smoke metrics look sane.

## Smoke Run

```json
{
  "env_id": "ApolloLabs/ObstacleAvoidance-v0",
  "total_timesteps": 30000,
  "eval_episodes": 20,
  "seed": 1,
  "device": "cpu"
}
```

## Standard Single Run

```json
{
  "env_id": "ApolloLabs/FullCleaning-v0",
  "total_timesteps": 200000,
  "eval_episodes": 50,
  "seed": 42,
  "layout_mode": "random",
  "sensor_mode": "lidar_local_dirt",
  "lidar_rays": 16,
  "obstacle_count": 4,
  "device": "cpu"
}
```

## Curriculum Order

1. `ApolloLabs/ObstacleAvoidance-v0`
2. `ApolloLabs/PointNavigation-v0`
3. `ApolloLabs/DirtSeeking-v0`
4. `ApolloLabs/FullCleaning-v0`

Scale to easy/dense/random variants after the core env succeeds across seeds.

## Guardrails

- Do not begin with million-step runs.
- Use 2-3 seeds before declaring a config robust.
- Stop escalation if smoke runs fail or reward-hacking flags appear.
- Prefer CPU locally unless CUDA is explicitly available.
