# Repository Guidelines

## Project Structure & Module Organization

This repository is a compact FastAPI service for training and evaluating a Roomba-style RL environment.

- `app/main.py` defines the API routes: `/health`, `/api/runs`, and `/api/runs/{run_id}`.
- `app/config.py` centralizes project paths and creates `runs/`.
- `app/schemas/` contains Pydantic request/response models.
- `app/services/` contains orchestration logic for training runs.
- `app/rl/` contains the Gymnasium environment, PPO training, evaluation, and baseline scripts.
- `scripts/run_local.sh` runs a local train/evaluate/baseline sequence.
- `runs/` is generated output for models and metrics; do not treat it as source.

## Build, Test, and Development Commands

Create and activate a virtual environment before running project commands:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the API locally:

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API docs. Run direct RL workflows with:

```bash
python -m app.rl.train --run-id local_test --total-timesteps 30000
python -m app.rl.eval --run-id local_test --episodes 50
python -m app.rl.baseline --episodes 50
./scripts/run_local.sh
```

## Coding Style & Naming Conventions

Use Python 3 style with 4-space indentation, type hints where they clarify API boundaries, and small functions with explicit names. Keep modules grouped by responsibility: API code in `app/main.py`, schemas in `app/schemas/`, run orchestration in `app/services/`, and RL logic in `app/rl/`. Use snake_case for files, functions, variables, and CLI arguments; use PascalCase for Pydantic models.

## Testing Guidelines

No dedicated test suite is currently committed. For changes, at minimum run `/health` through the API and execute the smallest relevant RL command with reduced timesteps or episodes when possible. If adding tests, prefer `pytest`, place tests under `tests/`, and name files `test_*.py`. Avoid committing generated model files or metrics from validation runs.

## Commit & Pull Request Guidelines

Recent history uses short, imperative-style messages such as `Readme/plan` and `Committing plan doc`; keep commits concise and focused. Pull requests should include a short summary, commands run, any API or schema changes, and notes on generated artifacts. Include screenshots only when API docs or user-visible output changes.

## Security & Configuration Tips

Do not commit local virtual environments, secrets, or large run outputs. Keep configurable paths and environment-dependent values out of training logic; prefer `app/config.py` or environment variables loaded via `python-dotenv` when configuration expands.
