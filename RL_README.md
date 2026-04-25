# Roomba RL FastAPI — Phase 1 MVP

This is the simplest possible FastAPI scaffold for the Phase 1 RL demo.

It trains a tiny Roomba-style 2D cleaning robot environment using Gymnasium + Stable-Baselines3 PPO.

## What this proves

```text
API request
→ generate/configure RL environment
→ train PPO policy
→ evaluate policy
→ save metrics/model
→ return run results
```

This is the foundation before Webots integration.

## Project structure

```text
roomba_rl_fastapi/
  app/
    main.py
    config.py
    schemas/
      run.py
    services/
      runner.py
    rl/
      env.py
      train.py
      eval.py
      baseline.py
  runs/
  scripts/
    run_local.sh
  requirements.txt
  .env.example
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

On Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run the API

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Train from API

POST:

```text
/api/runs
```

Example body:

```json
{
  "total_timesteps": 30000,
  "eval_episodes": 50,
  "seed": 42
}
```

The endpoint runs training synchronously for simplicity.

For 30k timesteps, this should usually complete in a few minutes.

## Get run status

```text
GET /api/runs/{run_id}
```

## List runs

```text
GET /api/runs
```

## Direct CLI training

```bash
python -m app.rl.train --run-id local_test --total-timesteps 30000
python -m app.rl.eval --run-id local_test --episodes 50
python -m app.rl.baseline --episodes 50
```

## Phase 1 success criteria

You are done when:

- `/health` works
- `POST /api/runs` creates a run
- model saves to `runs/{run_id}/model/roomba_policy.zip`
- metrics save to `runs/{run_id}/metrics/eval_metrics.json`
- PPO beats random baseline

## Next steps

1. Add W&B logging.
2. Add config.yaml support.
3. Add async/background jobs.
4. Add ClawLab report generation and API storage.
5. Replace Python env backend with Webots env backend later.
6. Run orchestration tasks through the Hermes agent harness where useful.
7. Send stored run reports through AgentMail.
