# Minimal RL → Webots Plan

## Stack
- **Frontend:** [Next.js](https://nextjs.org/) — UI, dashboards, run history, config forms (in place today).
- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) — API for Hermes orchestration, training jobs, metrics/proxy to W&B or your DB, webhooks (e.g. AgentMail triggers). RL/Webots worker processes are started or supervised from here (or by a worker the API enqueues).

## Hermes agent (what it actually does)

Hermes is the **orchestrator** — not the physics engine and not the RL math inside `env.step`. It does **not** replace Webots or PPO; it **produces** worlds/config, **launches** training, **aggregates telemetry**, and **ships a report**.

| Responsibility | Meaning |
|----------------|---------|
| **Generate the world** | Outputs world assets + config: `.wbt`, layout params, obstacles (start with **parameterized templates**; full procedural `.wbt` is v2). Webots still **loads and runs** the world. |
| **Run the full training** | **Supervises the job**: invokes `train.py` / pipeline with the right flags, seeds, env config — the training **process** runs as today; Hermes is the job runner + config layer. |
| **Monitor** | **One database** as source of truth for runs, step/episode metrics, artifacts, hyperparams. Charts/dashboards **read** from that DB (Hermes or workers **write** rows). |
| **Report** | After a run: aggregate best checkpoint, curves, config, summary → Markdown/HTML/PDF (or hand off to email/tools). |

**v1 honesty:** “World generation” can mean templated `.wbt` + JSON knobs — still Hermes-generated in a defensible hackathon sense.

### AgentMail (how it attaches)

| Topic | Details |
|-------|---------|
| **[AgentMail](https://docs.agentmail.to/welcome)** | Async **human channel**; Hermes already produces a run summary — email is a transport. |
| **Low-hanging fruit** | **When a training run finishes** (success, early stop, or crash), Hermes sends a **structured** message to an inbox: `run_id`, config snapshot, final / best metrics, checkpoint path, optional link to the metrics DB or dashboard, and error text if the process failed. One API call at the end of the supervised job. |

**AgentMail shape (suggested):** keep the “report” as JSON or Markdown Hermes already builds, then pass the same object into AgentMail (subject: `[RL] run {id} {status}`). No duplicate logic: **DB / W&B = analytics**, **email = human ping + same structured payload**.

### Nia (memory + what Hermes should learn)

Nia is the **knowledge and memory layer** on top of raw metrics. **W&B / the DB** store numbers and run metadata; Nia (via the **[Nia API](https://docs.trynia.ai/welcome)**, index + search, MCP in Cursor) holds **narrative memory**: what we tried, what **worked**, what **failed**, and **why** (postmortems, design notes, cited doc snippets from Webots/RL material we index).

| Topic | Details |
|-------|---------|
| **Role** | **Organizational memory** so Hermes is not “stateless” every time it sets up a sim: retrieve prior lessons before generating worlds, rewards, or configs. |
| **What we index** | This repo, `plan.md`, run postmortems (short markdown or JSON we append per run: outcome + key factors + failure class), and external docs (Webots supervisor, Gymnasium, etc.). |
| **How Hermes uses it** | Before proposing a new environment or sim layout, Hermes calls Nia (search / context) to pull **relevant** past notes and doc passages — e.g. “we already saw collision resets fail with layout X” or “template Y matched our best `mean_return`.” That feed is the **catch-up and improve** input: the next world/config is **grounded** in what did and did not work, not only the latest prompt. |
| **Complement, not replace** | Truth tables for “best run by metric” stay in **W&B/DB**; Nia answers **“what should we remember about that run in words?”** and **“what does the manual say about Z?”** |

**v1 / v2:** v1 = index repo + a **generated note per run** (success/fail + 2–3 bullets) into Nia; v2 = Hermes FastAPI enqueues a **Nia search** step in the orchestration path before `generate world` or `apply config`, so the agent **gets better at setting up sims** over the season by reusing indexed memory and official docs.

---

## Phase 1: Simple 2D RL (No Webots)
- Build Roomba-like env (env.py)
- Train PPO (train.py)
- Evaluate (eval.py)
- Goal: prove RL loop works in minutes

## Phase 2: Introduce Hermes
- Generate env + world/config (from templates or prompts)
- Run full training via CLI (Hermes supervises the run, not inner training loop)
- **One DB** for all telemetry; wire graphs/dashboards to that store
- **AgentMail (default v1):** on run exit, Hermes sends the structured end-of-run report to your inbox
- **Nia:** index run notes + repo/docs; Hermes (or v2: FastAPI) queries Nia before new world/env setup so sim decisions reuse **what worked / what failed**

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
- Hermes reads unified DB → compares experiments
- Adjust reward/config; next run uses new artifacts
- **End-of-run report**: actual outputs, metrics, best policy path

## Phase 6: Worlds API (optional)
- Generate GLB scene
- Import into Webots
- Overlay RL primitives

## Goal
Prompt → Environment → Training → Evaluation → Improvement
