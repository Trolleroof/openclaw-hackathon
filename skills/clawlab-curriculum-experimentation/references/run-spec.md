# Run Specs

Prefer small configs first. Scale only after plumbing and smoke metrics look sane.

## Smoke Run

```json
{
  "env_id": "ClawLab/ObstacleAvoidance-v0",
  "total_timesteps": 30000,
  "eval_episodes": 20,
  "seed": 1,
  "device": "cpu"
}
```

## Standard Single Run

```json
{
  "env_id": "ClawLab/FullCleaning-v0",
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

1. `ClawLab/ObstacleAvoidance-v0`
2. `ClawLab/PointNavigation-v0`
3. `ClawLab/DirtSeeking-v0`
4. `ClawLab/FullCleaning-v0`

Scale to easy/dense/random variants after the core env succeeds across seeds.

## Guardrails

- Do not begin with million-step runs.
- Use 2-3 seeds before declaring a config robust.
- Stop escalation if smoke runs fail or reward-hacking flags appear.
- Prefer CPU locally unless CUDA is explicitly available.
