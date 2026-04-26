# Metrics and Ranking

Use `compare_runs` for ranking, then inspect metrics resources for details.

## Ranking Priority

1. Higher `success_rate`
2. Lower `reward_hacking.flag_count`
3. Lower `avg_remaining_dirt`
4. Lower `avg_wall_hits`
5. Lower `avg_obstacle_hits`
6. Higher `avg_reward`

## Key Metrics

- `success_rate`: primary task completion signal.
- `avg_reward`: useful trend, not sufficient alone.
- `avg_steps`: efficiency signal.
- `avg_cleaned_dirt`: cleaning progress.
- `avg_remaining_dirt`: failure residue for cleaning envs.
- `avg_wall_hits`, `avg_obstacle_hits`: collision behavior.
- `reward_hacking.flag_count`: escalation blocker.

## Reward-Hacking Checks

Do not recommend a run as best if it has unexplained reward-hacking flags. Summarize the issue and propose a smaller diagnostic run.
