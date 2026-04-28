# Nia Memory

Nia stores narrative memory and source locations. It is not the canonical metrics database.

## Before Runs

Search Nia for:

- prior runs for the same `env_id`
- reward-shaping failures
- obstacle layout lessons
- relevant Webots, Gymnasium, or SB3 docs

## After Runs

Write a concise note for meaningful runs and benchmark summaries.

```markdown
type: apollolabs_run_summary
run_id: run_abc123
env_id: ApolloLabs/FullCleaning-v0
status: completed

artifact_locations:
  report: runs/run_abc123/report.json
  config: runs/run_abc123/rl_config.json
  metrics: runs/run_abc123/metrics/eval_metrics.json
  progress: runs/run_abc123/metrics/train_progress.jsonl
  artifacts: runs/run_abc123/artifacts/
  logs: runs/run_abc123/logs/
  wandb: <url if present>

summary:
  The run reached 0.82 success rate with no reward-hacking flags.

worked:
  - Local dirt signal improved final approach.

failed:
  - Dense obstacles still caused stall loops.

next:
  - Test this config across three seeds.
```

Keep raw logs and full metrics in Apollo Labs or W&B. Store locations and interpretation in Nia.
