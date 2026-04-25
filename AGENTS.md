# Repository Guidelines

## Project Structure & Module Organization

This repository combines a **FastAPI** orchestration API for training and evaluating a Roomba-style RL environment with a **Next.js** frontend in `frontend/`. Root-level `plan.md` records product and implementation planning; `CLAUDE.md` holds assistant-oriented notes.

**Backend**

- `app/main.py` defines the API routes: `/health`, `/api/runs`, and `/api/runs/{run_id}`.
- `app/config.py` centralizes project paths and creates `runs/`.
- `app/schemas/` contains Pydantic request/response models.
- `app/services/` contains orchestration logic for training runs.
- `app/rl/` contains the Gymnasium environment, PPO training, evaluation, and baseline scripts.
- `scripts/run_local.sh` runs a local train/evaluate/baseline sequence.
- `runs/` is generated output for models and metrics; do not treat it as source.

**Frontend**

Inside `frontend/`, application routes live in `app/`. Reusable UI components are in `app/components/`, shared frontend data and helpers are in `app/lib/`, and static assets are in `public/`. Route examples include `app/page.tsx`, `app/runs/[id]/page.tsx`, `app/agentmail/page.tsx`, and `app/memory/page.tsx`.

## Build, Test, and Development Commands

**Python API**

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

**Frontend** — run from `frontend/`:

```bash
npm install
npm run dev
npm run build
npm run start
npm run lint
```

`npm install` installs dependencies from `package-lock.json`. `npm run dev` starts the local Next.js development server. `npm run build` validates the production build. `npm run start` serves the built app. `npm run lint` runs ESLint with Next.js Core Web Vitals and TypeScript rules.

## Coding Style & Naming Conventions

**Python:** Use Python 3 style with 4-space indentation, type hints where they clarify API boundaries, and small functions with explicit names. Keep modules grouped by responsibility: API code in `app/main.py`, schemas in `app/schemas/`, run orchestration in `app/services/`, and RL logic in `app/rl/`. Use snake_case for files, functions, variables, and CLI arguments; use PascalCase for Pydantic models.

**TypeScript / React:** Components should be named in PascalCase (for example `RunCard.tsx`); utility modules should use concise lower-case names (for example `app/lib/runs.ts`). Prefer named exports for shared components and helpers. Use two-space indentation, double quotes, semicolons, and Tailwind utility classes in JSX. Keep styling aligned with `frontend/app/globals.css`, especially the existing CSS variables, typography classes, and dark telemetry-dashboard visual language.

## Testing Guidelines

**Backend:** Run `pytest` for the test suite under `tests/` (for example `tests/test_phase1_rl.py`). For ad-hoc checks, hit `/health` through the API and execute the smallest relevant RL command with reduced timesteps or episodes when possible. Avoid committing generated model files or metrics from validation runs.

**Frontend:** Run `npm run lint` and `npm run build` from `frontend/`. If you add tests, add the test script to `frontend/package.json`, keep tests near the code they cover or under a clearly named test directory, and use names such as `ComponentName.test.tsx` or `helper.test.ts`.

## Commit & Pull Request Guidelines

Recent history uses short, imperative-style messages; keep commits concise and focused. Pull requests should include a short summary, commands run, verification steps, and notes on API, schema, or UI changes. Include screenshots or screen recordings when user-visible output changes. Link related issues or planning notes when relevant. Call out new dependencies, environment variables, or migration steps.

## Security & Configuration Tips

Do not commit local virtual environments, secrets, or large run outputs. Keep configurable paths and environment-dependent values out of training logic; prefer `app/config.py` or environment variables loaded via `python-dotenv` when configuration expands.

## Agent-Specific Instructions

The nested `frontend/AGENTS.md` warns that this project uses a newer Next.js version with breaking changes. Before making framework-sensitive changes, check the relevant local Next.js documentation under `frontend/node_modules/next/dist/docs/` after dependencies are installed.
