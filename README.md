# ClawLab — RL Run Orchestrator

ClawLab is a small RL training platform built around a 2D Roomba-style cleaning
environment. It trains a PPO policy, evaluates it against a random baseline,
generates rollout GIFs, stores a structured **run report**, and ships that
report to humans through **AgentMail** while logging a narrative lesson into
**Nia / Hermes**.

The stack:

- **FastAPI backend** (`app/`) — orchestrates training, evaluation,
  visualization, reporting, and notifications.
- **Next.js frontend** (`frontend/`) — dashboard for run history, metrics,
  GIFs, AgentMail inbox, and Nia memory.
- **Hermes** — agent harness that runs the orchestration. Code lives in
  `app/services/hermes.py`.
- **AgentMail** — async email channel for end-of-run reports
  (`app/services/agentmail.py`).
- **Nia** — narrative memory layer queried *before* a run and written *after*
  a run.
- **MCP server** (`app/mcp/clawlab_server.py`) — exposes ClawLab tools and
  resources to Claude / Cursor over MCP.

---

## How a run actually works

This is the whole flow when you `POST /api/runs`:

```
client → POST /api/runs
       → app/main.py:create_training_run
       → app/services/runner.py:create_run
             1. allocate run_id, write metadata.json
             2. Hermes asks Nia for prior lessons   (hermes.query_nia)
             3. train PPO policy                    (app/rl/train.py)
             4. evaluate policy + random baseline   (app/rl/eval.py, baseline.py)
             5. write combined_metrics.json
             6. generate rollout GIF + trajectory   (app/rl/visualize.py)
             7. build RunReport (markdown + JSON)   (app/services/reports.py)
             8. Hermes posts lesson to Slack +
                sends report through AgentMail      (app/services/hermes.py)
             9. write report.json next to the run
```

All artifacts for a run end up under `runs/<run_id>/`:

```
runs/run_abc123/
  metadata.json              # run config + status + paths
  rl_config.json             # the PPO/env config snapshot
  report.json                # canonical RunReport (used by API + AgentMail)
  model/roomba_policy.zip    # trained PPO checkpoint
  metrics/eval_metrics.json  # PPO eval metrics
  metrics/combined_metrics.json  # PPO vs random baseline
  metrics/train_progress.jsonl   # per-step training log
  artifacts/<...>.gif        # rollout video
  artifacts/manifest.json    # artifact index
  logs/                      # stdout/stderr + MCP tool output
```

The frontend (`frontend/app/runs/[id]/page.tsx`) reads the same `RunReport`
that AgentMail sends, so the email and the dashboard never disagree.

---

## How we use AgentMail

**Goal:** when a training run finishes (success, early stop, or crash),
ClawLab sends the *exact same* structured `RunReport` to a human inbox. The
backend is the source of truth; AgentMail is just the delivery channel.

**Where it lives:** `app/services/agentmail.py`.

**What it does:**

1. `send_report(report, recipient)` — called by Hermes at end-of-run.
   - Takes a `RunReport` (the same Pydantic model the API serves).
   - Renders a rich HTML email via `_html_report(report)` using the
     ClawLab/Hermes visual language (dark card, status pill, metric grid).
   - Falls back to the markdown version (`report.markdown`) for the plain
     text body.
   - POSTs to `https://api.agentmail.to/v0/inboxes/{INBOX_ID}/messages/send`
     with labels `["hermes", "run-report", <status>]`.
   - Returns an `AgentMailResult` with `delivery_status`, `message_id`,
     `thread_id`. Hermes writes those back into `report.json` so the
     frontend can show "Email delivered ✓" with the AgentMail thread id.

2. `list_inbox_messages(limit)` and `get_inbox_message(message_id)` —
   used by the `/api/v1/agentmail/messages` routes so the dashboard
   (`frontend/app/agentmail/page.tsx`) can render the inbox without the
   user leaving the app.

3. `build_mock_run_report()` + `POST /api/v1/agentmail/mock-run` — a
   one-click demo that fabricates a `RunReport`, sends it via AgentMail,
   and returns the delivery status. Useful for hackathon demos and for
   verifying the AgentMail integration without running PPO.

**Configuration** (read from `.env` via `app/config.py`):

| Env var                    | Purpose                                          |
| -------------------------- | ------------------------------------------------ |
| `AGENTMAIL_API_KEY`        | Bearer token for the AgentMail API.              |
| `AGENTMAIL_INBOX_ID`       | The inbox that sends the email.                  |
| `AGENTMAIL_API_BASE_URL`   | Defaults to `https://api.agentmail.to/v0`.       |
| `REPORT_RECIPIENT_EMAIL`   | Comma-separated list of human recipients.        |
| `HERMES_PUBLIC_BASE_URL`   | Used to build the dashboard link in the report.  |

If any of the required vars are missing, `send_report` returns
`delivery_status="skipped"` instead of crashing the run.

**Subject convention:** `[RL] run {run_id} {status}` — easy to filter on.

---

## How we use Nia

**Goal:** ClawLab should not be stateless every time it sets up a sim. Before
a run, we ask Nia for relevant prior lessons; after a run, we drop a concise
lesson note back into Nia. Numbers stay in metrics/W&B; *interpretations*
stay in Nia.

**Where it lives:**

- `app/services/hermes.py` — the actual integration in code.
- `skills/clawlab-curriculum-experimentation/references/nia-memory.md` —
  the lesson-note template Hermes writes into Nia.
- `npx nia-docs https://docs.innate.bot/` — CLI used to read Innate / Nia
  docs while developing.

**Before a run** — `hermes.query_nia(template, run_config)` is called from
`runner.create_run` *before* training starts. It posts a Slack message in the
Hermes channel asking the agent to search Nia for prior lessons on the same
`env_id` and config knobs (`room_size`, `dirt_count`, `total_timesteps`,
etc.), then polls the thread for replies. Hermes' reply is stored on the run
as `metadata.nia_context`, so the frontend can show "What Nia remembered
before this run" alongside the metrics.

**After a run** — `hermes.post_lesson(report)` runs once the report is built.
It:

1. Calls `agentmail.send_report` to email the run report.
2. Derives a 3-bullet lesson via `_derive_lesson(report)`:
   - **What worked** — converged success rate / mean reward.
   - **What failed** — low success rate, errors, reward-hacking flags.
   - **Next recommendation** — "increase timesteps 50%", "simplify env",
     "scale to more seeds", etc.
3. Posts a structured Slack block-kit message in the Hermes channel so the
   agent can index the lesson into Nia using the template in
   `skills/.../nia-memory.md`.
4. Writes `hermes_delivery_status` and `agentmail_message_id` back into
   `report.json`.

**Memory dashboard** — `GET /api/v1/memory/lessons` returns every report
with a Hermes delivery status. The frontend (`frontend/app/memory/page.tsx`)
uses it to show the running list of lessons Hermes has shipped to Nia.

**Why it matters:** the next time the user (or the MCP-driven agent) asks
for a new run, the curriculum skill
(`skills/clawlab-curriculum-experimentation/SKILL.md`) tells the agent to
search Nia *first*, so config decisions are grounded in what we've already
learned instead of starting cold.

---

## ClawLab MCP server (for agents)

`app/mcp/clawlab_server.py` exposes the same orchestration as MCP tools and
resources, so an agent in Cursor/Claude can drive runs without going through
HTTP.

Tools: `list_envs`, `describe_env`, `start_training_run`, `get_run_status`,
`start_eval_run`, `generate_run_gif`, `summarize_reward_hacking`,
`compare_runs`.

Resources (URIs): `clawlab://envs`,
`clawlab://runs/{run_id}/{metadata|config|metrics|progress|artifacts|trajectory|report|logs}`.

Run it standalone with `python -m app.mcp.clawlab_server` (requires the
optional `mcp` package).

---

## Setup

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then fill in AGENTMAIL_* and SLACK_* keys
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API docs.

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

### Smoke run

```bash
# Direct CLI (no API)
python -m app.rl.train --run-id local_test --total-timesteps 30000 --device cpu
python -m app.rl.eval  --run-id local_test --episodes 50
python -m app.rl.baseline --episodes 50

# Or end-to-end via the API (will trigger Nia query + AgentMail email)
curl -X POST http://127.0.0.1:8000/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"total_timesteps": 30000, "eval_episodes": 20, "seed": 42}'

# AgentMail sanity check (no PPO required)
curl -X POST http://127.0.0.1:8000/api/v1/agentmail/mock-run
```

### Tests

```bash
.venv/bin/python -m unittest tests.test_phase1_rl
.venv/bin/python -m unittest tests.test_run_reports
```

---

## Key API routes

| Method | Path                                       | Purpose                              |
| ------ | ------------------------------------------ | ------------------------------------ |
| GET    | `/health`                                  | Liveness probe.                      |
| POST   | `/api/runs`                                | Start a synchronous training run.    |
| GET    | `/api/runs`                                | List all runs.                       |
| GET    | `/api/runs/{run_id}`                       | Get run metadata + GIF availability. |
| GET    | `/api/runs/{run_id}/gif`                   | Stream the rollout GIF.              |
| GET    | `/api/v1/runs/{run_id}/report`             | Canonical `RunReport`.               |
| GET    | `/api/v1/reports`                          | All `RunReport`s newest-first.       |
| GET    | `/api/v1/agentmail/messages`               | Inbox listing for the dashboard.     |
| GET    | `/api/v1/agentmail/messages/{message_id}`  | Single message detail (HTML + text). |
| POST   | `/api/v1/agentmail/mock-run`               | Send a fake `RunReport` via AgentMail. |
| GET    | `/api/v1/memory/lessons`                   | Reports already shipped to Nia.      |

---

## Repository layout

```
app/
  main.py                  # FastAPI routes
  config.py                # env vars (AgentMail, Hermes, Slack)
  schemas/                 # Pydantic models (RunReport, AgentMail*, etc.)
  services/
    runner.py              # run lifecycle, calls train/eval/visualize
    reports.py             # build/read/write RunReport
    agentmail.py           # AgentMail HTTP client + HTML report renderer
    hermes.py              # query_nia (pre-run) + post_lesson (post-run)
  rl/                      # env, train, eval, baseline, visualize
  mcp/clawlab_server.py    # MCP tools + resources for agents
frontend/
  app/
    page.tsx               # run history
    runs/[id]/page.tsx     # run detail (metrics + GIF + report)
    agentmail/page.tsx     # AgentMail inbox viewer
    memory/page.tsx        # Nia lesson feed
skills/clawlab-curriculum-experimentation/
  SKILL.md                 # how an agent should drive ClawLab
  references/nia-memory.md # Nia lesson-note template
  references/reporting.md  # AgentMail/Slack/Nia channel split
runs/                      # generated per-run artifacts (gitignored)
plan.md                    # phased roadmap (1–6)
AGENTS.md                  # contributor guide
CLAUDE.md                  # assistant-oriented notes
```

---

## Glossary

- **ClawLab** — the FastAPI orchestrator that supervises runs, stores
  reports, and exposes them to clients.
- **Hermes** — the agent harness running ClawLab work. Sends the AgentMail
  email and writes Nia lessons.
- **AgentMail** — async human notification channel. Same payload as the API.
- **Nia** — narrative memory queried before runs and written after.
- **RunReport** — canonical Pydantic object served by the API, rendered by
  the frontend, and emailed by AgentMail.
