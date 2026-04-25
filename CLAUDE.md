# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **openclaw-hackathon**: a reinforcement learning + physics simulation orchestration system. The architecture consists of:

- **Frontend**: Next.js dashboard for run history, configuration, and metrics visualization
- **Backend**: FastAPI orchestration layer (Hermes) for world generation, training supervision, and telemetry aggregation
- **RL Core**: PPO training pipeline with Gymnasium environment interface
- **Physics**: Webots simulator integration for realistic robot/environment dynamics
- **Knowledge Layer**: Nia for indexed memory of runs and documentation
- **Communication**: AgentMail for end-of-run reports and notifications

See **`plan.md`** for the full architecture roadmap (Phases 1–6) and detailed responsibility matrix.

## Frontend (Next.js)

### Setup & Development

```bash
cd frontend
npm install
npm run dev        # Start dev server on http://localhost:3000
npm run build      # Build for production
npm start          # Start production server
npm run lint       # Run ESLint
```

### Structure

- `app/layout.tsx`: Root layout with metadata and global fonts (Geist Sans/Mono)
- `app/page.tsx`: Home page component
- `app/globals.css`: Global styles (Tailwind CSS v4)
- `public/`: Static assets
- `tsconfig.json`: TypeScript configuration with `@/*` path alias pointing to root

### Tech Stack

- **Next.js 16.2.4** with App Router (latest features)
- **React 19.2.4** (latest)
- **TypeScript 5** (strict mode enabled)
- **Tailwind CSS 4** (@tailwindcss/postcss)
- **ESLint 9** with next/eslint-config

### Key Patterns

- Use `@/` alias for imports (e.g., `@/components/Button`)
- Component-driven: build reusable UI components in `app/components/` (not yet structured; create as needed)
- Server components by default; mark interactive components with `'use client'` at the top
- Metadata and SEO: configure in `layout.tsx` or per-route with `metadata` exports

### Important Notes

- This is Next.js 16 with potential breaking changes from earlier versions — check `frontend/AGENTS.md` for deprecation notices
- The frontend is **dashboard-only** in v1: display run history, configs, and metrics from the backend API
- No authentication is implemented yet; coordinate with backend when auth is needed

## Backend (FastAPI)

Not yet implemented. When adding the backend:

- Hermes orchestrator should live in a `backend/` directory (or sibling to `frontend/`)
- It should expose a REST API for:
  - Creating/querying training runs
  - Fetching telemetry and metrics
  - Submitting world/config generation requests
- The backend will be called from the frontend (likely via `/api/` Next.js routes or direct HTTP)

## RL & Webots Integration

When implementing (phases 1–4 of plan.md):

- **Phase 1** (simple 2D RL): `env.py`, `train.py`, `eval.py` in a top-level `rl/` directory
- **Phase 3** (Webots): `.wbt` world files in `rl/worlds/`; controller bridge in `rl/controllers/`
- Keep training loop separate from orchestration (Hermes supervises, not embeds)

## Development Workflow

1. **Plan**: Check `plan.md` for the feature or phase; understand Hermes responsibilities vs. other layers
2. **Frontend**: Add UI components/pages in `frontend/app/`; start the dev server to test
3. **Backend**: When needed, add FastAPI routes and database models
4. **Testing**: Frontend linting runs via `npm run lint`; add unit tests in `**/*.test.ts(x)` (runner TBD)
5. **Coordination**: Frontend calls backend APIs; Hermes orchestrates the RL training and telemetry

## Glossary

- **Hermes**: FastAPI orchestrator that generates environments, supervises training, aggregates metrics
- **Nia**: Knowledge/memory layer (indexing runs, docs, lessons learned)
- **AgentMail**: Service for sending structured run reports via email
- **W&B**: Weights & Biases integration for metrics and checkpoints (planned)
- **Webots**: Physics engine + simulator for realistic robot/environment dynamics

## Next Steps

Refer to `plan.md` Phase 2 and 3 for immediate priorities:
- Phase 2: Hermes FastAPI setup, unified telemetry DB, AgentMail integration
- Phase 3: Webots world + robot integration
