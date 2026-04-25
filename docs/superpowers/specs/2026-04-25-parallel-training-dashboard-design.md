# Parallel Training Dashboard Design

## Goal

Turn the frontend into a live monitor for many concurrent PPO training runs. The dashboard should answer four questions quickly:

- What trainings are running?
- Which runs are winning?
- Which runs failed?
- Where are the artifacts?

W&B handles deep charts, sweep comparison, and long-term experiment analytics. This app only needs a compact operational view over active and recent runs.

## Non-Goals

- Do not build a W&B replacement.
- Do not stream Webots video in the first version.
- Do not add Hermes chat controls to the dashboard yet.
- Do not require WebSockets/SSE for the first version.
- Do not block the UI while training runs execute.

## Recommended Approach

Use a polling dashboard backed by run folders and background training processes.

The frontend polls `GET /api/runs` every 1-2 seconds and renders one compact card per run. The backend starts each training run in a background subprocess or worker, returns immediately, and stores status/metrics/artifact paths under `runs/{run_id}`.

This is faster and safer than implementing a custom realtime event bus. It is good enough for local parallel training visibility, and W&B can handle the richer charting layer.

## Dashboard Layout

The first screen is a dense run board:

```text
Header:
  Active trainings
  Queued
  Completed
  Failed
  Best success rate / best reward

Controls:
  New run
  Refresh
  Backend filter: all / python / webots
  Status filter: all / running / failed / completed

Grid:
  [Run Card] [Run Card] [Run Card] [Run Card]
  [Run Card] [Run Card] [Run Card] [Run Card]
```

Each card includes:

- `run_id`
- status: `queued`, `running`, `completed`, `failed`, `cancelled`
- backend: `python` or `webots`
- seed
- world/config name when present
- elapsed time
- progress: `timesteps_done / total_timesteps`
- latest reward or mean reward
- success rate
- average remaining dirt
- W&B URL when present
- artifact links: model, metrics, logs

Cards should be scannable without opening a detail page.

## Detail View

Clicking a card opens a detail view or side panel with:

- full config snapshot
- latest metrics
- final metrics when complete
- recent log tail
- artifact paths
- W&B run URL
- error traceback if failed

No custom charting is required in v1. If charts are needed, link to W&B.

## Backend API

Keep the API small:

```text
POST /api/runs
GET  /api/runs
GET  /api/runs/{run_id}
GET  /api/runs/{run_id}/logs
GET  /api/runs/{run_id}/metrics
```

`POST /api/runs` should return immediately after creating and starting a job:

```json
{
  "run_id": "run_ab12cd34ef",
  "status": "queued",
  "config": {
    "backend": "python",
    "total_timesteps": 200000,
    "seed": 42
  }
}
```

`GET /api/runs` returns the latest metadata for all runs. The frontend can poll this endpoint for live status.

## Run Storage

Each run owns a directory:

```text
runs/{run_id}/
  metadata.json
  config.json
  metrics/
    metrics.jsonl
    combined_metrics.json
    eval_metrics.json
  model/
    roomba_policy.zip
  logs/
    stdout.log
    stderr.log
    error.txt
```

`metadata.json` is the source of truth for dashboard cards:

```json
{
  "run_id": "run_ab12cd34ef",
  "status": "running",
  "backend": "python",
  "seed": 42,
  "progress": {
    "timesteps_done": 32768,
    "total_timesteps": 200000
  },
  "latest_metrics": {
    "mean_reward": 12.4,
    "success_rate": 0.48,
    "avg_remaining_dirt": 1.2
  },
  "artifacts": {
    "model_path": null,
    "metrics_path": "runs/run_ab12cd34ef/metrics/metrics.jsonl",
    "wandb_url": "https://wandb.ai/..."
  },
  "error": null
}
```

Training jobs should update `metadata.json` periodically and append time-series metrics to `metrics.jsonl`.

## Parallel Execution

For the fastest implementation, use subprocesses:

- `POST /api/runs` writes config and metadata.
- Backend starts `python -m app.rl.train_worker --run-id ...`.
- Worker writes progress and metrics into the run directory.
- API reads files and returns summaries.

This avoids in-process event-loop issues and keeps each training isolated. It also maps naturally to Webots later because each Webots run can own its own process.

Limit concurrency with a simple max-workers setting. Runs above the limit stay `queued`.

## W&B Integration

W&B is optional but preferred for charts.

Each worker can initialize a W&B run with:

- `run_id`
- backend
- seed
- world/config name
- PPO hyperparameters
- reward and success metrics

The dashboard only stores and displays the W&B URL. It does not duplicate W&B charts.

## Error Handling

Failed runs must preserve enough information to debug quickly:

- status becomes `failed`
- `error` stores a short message
- `logs/error.txt` stores traceback
- `logs/stdout.log` and `logs/stderr.log` remain accessible
- card shows failed state and links to logs

If a worker process disappears without final metadata, the API should mark it `failed` or `stale` after a timeout.

## Testing

Test in three layers:

- Unit test run metadata read/write helpers.
- API test that `POST /api/runs` returns immediately and creates a run directory.
- Frontend test/manual check that mocked `GET /api/runs` data renders multiple concurrent cards.

For an ASAP version, manual verification is acceptable if it proves:

- two or more runs can be launched
- the dashboard shows them at the same time
- statuses update without page reload
- failed runs are visible
- artifact paths are discoverable

