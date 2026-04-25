# Minimal RL → Webots Plan

## Stack
- **Frontend:** [Next.js](https://nextjs.org/) — UI, dashboards, run history, config forms (in place today).
- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) — API for ClawLab orchestration, training jobs, metrics/proxy to W&B or your DB, report storage, and AgentMail delivery. RL/Webots worker processes are started or supervised from here (or by a worker the API enqueues).
- **Agent harness:** Hermes is the agent runtime used to execute orchestration tasks. Hermes is not the product name and not the backend service.

## Run everything (local)

From the **repository root** (`openclaw-hackathon/`), **not** inside `app/`. (`uvicorn` imports the `app` package next to `requirements.txt`.) Use two terminals.

**One-time setup**

```bash
cd /path/to/openclaw-hackathon   # repo root; must see requirements.txt and app/ here
python3 -m venv .venv            # macOS/Linux often use python3; Windows: py -3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

If `python3 -m venv .venv` fails with an **ensurepip** error (common with some Python 3.14 installs), install a stable Python and point at it, e.g. Homebrew: `brew install python@3.12` then:

```bash
$(brew --prefix python@3.12)/bin/python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Remove a mistakenly created venv under `app/` before retrying: `rm -rf app/.venv`.

Copy env template if you do not already have one: `cp .env.example .env` and fill in secrets as needed. The Next app talks to the API at `http://127.0.0.1:8000` by default (`NEXT_PUBLIC_HERMES_API_BASE_URL` overrides this if set in `frontend/.env.local`).

**Terminal 1 — FastAPI (ClawLab API)**

```bash
cd /path/to/openclaw-hackathon
source .venv/bin/activate
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000` — interactive docs: `http://127.0.0.1:8000/docs`

**Terminal 2 — Next.js frontend**

```bash
cd frontend
npm run dev
```

- UI: `http://localhost:3000`

**Optional — full local script (train / eval / baseline)** after the venv is active and deps are installed:

```bash
./scripts/run_local.sh
```

## ClawLab orchestrator (what it actually does)

ClawLab is the **orchestration layer** — not the physics engine and not the RL math inside `env.step`. It does **not** replace Webots or PPO; it **produces** worlds/config, **launches** training, **aggregates telemetry**, and **ships a report**. The Hermes agent harness can run these orchestration steps, but the user-facing platform is ClawLab.

| Responsibility | Meaning |
|----------------|---------|
| **Generate the world** | Outputs world assets + config: `.wbt`, layout params, obstacles (start with **parameterized templates**; full procedural `.wbt` is v2). Webots still **loads and runs** the world. |
| **Run the full training** | **Supervises the job**: invokes `train.py` / pipeline with the right flags, seeds, env config — the training **process** runs as today; ClawLab is the job runner + config layer, optionally executed through the Hermes harness. |
| **Monitor** | **One database** as source of truth for runs, step/episode metrics, artifacts, hyperparams. Charts/dashboards **read** from that DB (ClawLab services or workers **write** rows). |
| **Report** | After a run: aggregate best checkpoint, curves, config, summary → Markdown/HTML/PDF (or hand off to email/tools). |

**v1 honesty:** “World generation” can mean templated `.wbt` + JSON knobs — still ClawLab-generated in a defensible hackathon sense.

### AgentMail (reports only)

| Topic | Details |
|-------|---------|
| **[AgentMail](https://docs.agentmail.to/welcome)** | Async **human report channel**. ClawLab produces a canonical run report, stores it behind the API, and sends the same report to an inbox through AgentMail. |
| **Low-hanging fruit** | **When a training run finishes** (success, early stop, or crash), ClawLab sends a **structured** message to an inbox: `run_id`, config snapshot, final / best metrics, checkpoint path, optional link to the metrics DB or dashboard, and error text if the process failed. One API call at the end of the supervised job. |

**AgentMail shape (suggested):** keep the “report” as JSON or Markdown ClawLab already builds, store that object via the backend API, then pass the same object into AgentMail (subject: `[RL] run {id} {status}`). No duplicate logic: **DB / W&B = analytics**, **frontend = report viewer**, **AgentMail = inbox copy of the same structured payload**.

### Nia (memory + what ClawLab should learn)

Nia is the **knowledge and memory layer** on top of raw metrics. **W&B / the DB** store numbers and run metadata; Nia (via the **[Nia API](https://docs.trynia.ai/welcome)**, index + search, MCP in Cursor) holds **narrative memory**: what we tried, what **worked**, what **failed**, and **why** (postmortems, design notes, cited doc snippets from Webots/RL material we index).

| Topic | Details |
|-------|---------|
| **Role** | **Organizational memory** so ClawLab is not “stateless” every time it sets up a sim: retrieve prior lessons before generating worlds, rewards, or configs. |
| **What we index** | This repo, `plan.md`, run postmortems (short markdown or JSON we append per run: outcome + key factors + failure class), and external docs (Webots supervisor, Gymnasium, etc.). |
| **How ClawLab uses it** | Before proposing a new environment or sim layout, ClawLab calls Nia (search / context) to pull **relevant** past notes and doc passages — e.g. “we already saw collision resets fail with layout X” or “template Y matched our best `mean_return`.” That feed is the **catch-up and improve** input: the next world/config is **grounded** in what did and did not work, not only the latest prompt. |
| **Complement, not replace** | Truth tables for “best run by metric” stay in **W&B/DB**; Nia answers **“what should we remember about that run in words?”** and **“what does the manual say about Z?”** |

**v1 / v2:** v1 = index repo + a **generated note per run** (success/fail + 2–3 bullets) into Nia; v2 = ClawLab FastAPI enqueues a **Nia search** step in the orchestration path before `generate world` or `apply config`, so the system **gets better at setting up sims** over the season by reusing indexed memory and official docs.

---

## Phase 1: Simple 2D RL (No Webots) — Complete
- Build Roomba-like env (env.py)
- Train PPO (train.py)
- Evaluate (eval.py)
- Goal: prove RL loop works in minutes

Status: complete. The default API run trains PPO, writes model and metrics artifacts, evaluates against a random baseline, and reports `ppo_beats_random=true`. The optimized Phase 1 env now uses normalized navigation observations, wall/dirt features, progress and alignment rewards. The 2D default training budget is 200k PPO steps for better convergence, with 30k-step CPU runs already reaching `success_rate=1.0` across tested seeds.

## Phase 2: Introduce ClawLab Orchestration
- Generate env + world/config (from templates or prompts)
- Run full training via CLI (ClawLab supervises the run, not inner training loop; Hermes may execute the orchestration task)
- **One DB** for all telemetry; wire graphs/dashboards to that store
- **AgentMail (default v1):** on run exit, ClawLab stores the structured end-of-run report through the API and sends the same report to your inbox
- **Nia:** index run notes + repo/docs; ClawLab queries Nia before new world/env setup so sim decisions reuse **what worked / what failed**

## Phase 3: Webots Integration
- Create .wbt world (room + obstacles)
- Use prebuilt robot (differential drive)
- Add controller bridge (rl_controller.py)
- Add supervisor (reset + metrics)

## Phase 4: RL + Webots
- Build Gym wrapper (webots_env.py)
- Train PPO using Webots backend
- Evaluate performance

## Phase 5: Iteration Loop
- ClawLab reads unified DB → compares experiments
- Adjust reward/config; next run uses new artifacts
- **End-of-run report**: actual outputs, metrics, best policy path; visible in the frontend and delivered through AgentMail

## Phase 6: Worlds API (optional)
- Generate GLB scene
- Import into Webots
- Overlay RL primitives

## Goal
Prompt → Environment → Training → Evaluation → Improvement
