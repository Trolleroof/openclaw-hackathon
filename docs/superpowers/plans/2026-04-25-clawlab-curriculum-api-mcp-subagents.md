# ClawLab Curriculum, API, and MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a scalable ClawLab RL curriculum with named Gymnasium environments, API access, run orchestration, metrics, and an MCP inspection/control layer.

**Architecture:** Split the current monolithic `RoombaEnv` into shared utilities plus explicit curriculum envs. Each env owns one learning objective, while shared train/eval/telemetry code works from env IDs such as `ClawLab/ObstacleAvoidance-v0`. The API and MCP layers call stable Python service functions rather than duplicating RL logic.

**Tech Stack:** Python, Gymnasium, Stable-Baselines3 PPO, FastAPI, Pydantic, local `runs/` artifacts, MCP server tools/resources.

---

## Current State

- Existing core env: `app/rl/env.py::RoombaEnv`
- Existing shared utilities: `app/rl/layouts.py`, `app/rl/sensors.py`, `app/rl/diagnostics.py`, `app/rl/telemetry.py`
- Existing training/eval: `app/rl/train.py`, `app/rl/eval.py`, `app/rl/baseline.py`, `app/rl/visualize.py`
- Existing API: `app/main.py`, `app/services/runner.py`, `app/schemas/run.py`
- Do not modify frontend for this phase.

## Target Envs

Core curriculum envs:

- `ClawLab/ObstacleAvoidance-v0`
- `ClawLab/PointNavigation-v0`
- `ClawLab/DirtSeeking-v0`
- `ClawLab/FullCleaning-v0`

Scaled variants after core envs compile:

- `ClawLab/ObstacleAvoidanceEasy-v0`
- `ClawLab/ObstacleAvoidanceDense-v0`
- `ClawLab/PointNavigationOpen-v0`
- `ClawLab/PointNavigationObstacles-v0`
- `ClawLab/DirtSeekingLocal-v0`
- `ClawLab/DirtSeekingSparse-v0`
- `ClawLab/FullCleaningEasy-v0`
- `ClawLab/FullCleaningRandom-v0`
- `ClawLab/FullCleaningDenseObstacles-v0`

## Subagent Ownership

Each implementation agent must treat the rest of the codebase as shared. Do not revert or overwrite other agents' files. If a shared helper is needed, request coordinator integration rather than editing shared files directly unless assigned.

| Agent | Owns | Write Scope |
|---|---|---|
| Env Agent 1 | Obstacle avoidance | `app/rl/envs/obstacle_avoidance.py`, `tests/test_obstacle_avoidance_env.py` |
| Env Agent 2 | Point navigation | `app/rl/envs/point_navigation.py`, `tests/test_point_navigation_env.py` |
| Env Agent 3 | Dirt seeking | `app/rl/envs/dirt_seeking.py`, `tests/test_dirt_seeking_env.py` |
| Env Agent 4 | Full cleaning | `app/rl/envs/full_cleaning.py`, `tests/test_full_cleaning_env.py` |
| Integration Agent | Registry and shared config | `app/rl/envs/__init__.py`, `app/rl/envs/registry.py`, `app/rl/envs/base.py`, `app/rl/config.py`, `tests/test_env_registry.py` |
| Training Agent | PPO env-ID support | `app/rl/train.py`, `app/rl/eval.py`, `app/rl/baseline.py`, `app/rl/visualize.py`, `tests/test_training_env_ids.py` |
| API Agent | FastAPI run control | `app/schemas/run.py`, `app/services/runner.py`, `app/main.py`, `tests/test_run_api.py` |
| MCP Agent | MCP control/inspection | `app/mcp/clawlab_server.py`, `app/mcp/__init__.py`, `tests/test_clawlab_mcp.py` |
| Benchmark Agent | Smoke runs and summaries | `scripts/run_clawlab_curriculum.py`, `app/rl/benchmark.py`, `tests/test_benchmark_summary.py` |

---

## Task 1: Shared Env Base and Registry

**Agent:** Integration Agent

**Files:**
- Create: `app/rl/envs/base.py`
- Create: `app/rl/envs/registry.py`
- Create: `app/rl/envs/__init__.py`
- Test: `tests/test_env_registry.py`

- [ ] **Step 1: Add failing registry tests**

Create `tests/test_env_registry.py`:

```python
import unittest

import gymnasium as gym


class EnvRegistryTests(unittest.TestCase):
    def test_clawlab_envs_can_be_made_by_id(self):
        env_ids = [
            "ClawLab/ObstacleAvoidance-v0",
            "ClawLab/PointNavigation-v0",
            "ClawLab/DirtSeeking-v0",
            "ClawLab/FullCleaning-v0",
        ]
        for env_id in env_ids:
            env = gym.make(env_id)
            obs, _ = env.reset(seed=123)
            self.assertTrue(env.observation_space.contains(obs))
            env.close()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verify test fails before implementation**

Run:

```bash
.venv/bin/python -m unittest tests.test_env_registry
```

Expected: failure because `ClawLab/...` envs are not registered.

- [ ] **Step 3: Implement registry API**

Create `app/rl/envs/registry.py` with `register_clawlab_envs()` that calls `gymnasium.register` for the four core IDs. Each entry point should point at its env class.

Create `app/rl/envs/__init__.py` that imports and calls registration idempotently.

- [ ] **Step 4: Add base helpers**

Create `app/rl/envs/base.py` with shared `BaseClawLabEnv` utilities for:

- action space: `Discrete(3)`
- heading normalization
- collision check helpers
- shared render helpers, if practical
- common info keys: `steps`, `hit_wall`, `hit_obstacle`, `reward_components`

- [ ] **Step 5: Run registry tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_env_registry
```

Expected: all registered env IDs instantiate and return valid observations.

- [ ] **Step 6: Commit**

```bash
git add app/rl/envs tests/test_env_registry.py
git commit -m "Add ClawLab env registry"
```

---

## Task 2: Obstacle Avoidance Env

**Agent:** Env Agent 1

**Files:**
- Create: `app/rl/envs/obstacle_avoidance.py`
- Test: `tests/test_obstacle_avoidance_env.py`

**Spec:**
- No dirt objective.
- Random start and obstacles.
- Reward collision-free forward movement and clearance.
- Penalize wall/obstacle hits.
- Terminate on surviving `max_steps` or optional reaching a safe waypoint.

- [ ] **Step 1: Add failing tests**

Create tests that verify:

- observation is valid
- forward collision is blocked
- obstacle collision adds negative `obstacle_penalty`
- a random policy episode produces telemetry keys

- [ ] **Step 2: Implement env**

Implement `ObstacleAvoidanceEnv(gym.Env)` using `generate_layout`, `cast_lidar_rays`, and the shared collision helpers.

Minimum observation:

```text
sin_heading, cos_heading, lidar rays, wall clearances
```

Minimum reward components:

```text
step_penalty, forward_reward, clearance_reward, wall_penalty, obstacle_penalty, survival_bonus
```

- [ ] **Step 3: Run tests**

```bash
.venv/bin/python -m unittest tests.test_obstacle_avoidance_env
```

- [ ] **Step 4: Commit**

```bash
git add app/rl/envs/obstacle_avoidance.py tests/test_obstacle_avoidance_env.py
git commit -m "Add ClawLab obstacle avoidance env"
```

---

## Task 3: Point Navigation Env

**Agent:** Env Agent 2

**Files:**
- Create: `app/rl/envs/point_navigation.py`
- Test: `tests/test_point_navigation_env.py`

**Spec:**
- Random target point.
- Obstacles optional by config.
- Reward distance-to-target progress and efficient pathing.
- Penalize collisions and excessive turning.
- Terminate when robot reaches target radius.

- [ ] **Step 1: Add failing tests**

Tests must verify:

- target is randomized by seed
- moving toward target improves reward versus turning away in a controlled setup
- reaching target terminates successfully
- collision flags are surfaced

- [ ] **Step 2: Implement env**

Implement `PointNavigationEnv(gym.Env)`.

Observation:

```text
sin_heading, cos_heading, target_vector_robot_frame, target_distance, lidar rays, remaining_step_fraction
```

Reward components:

```text
step_penalty, progress, alignment, turn_penalty, wall_penalty, obstacle_penalty, success
```

- [ ] **Step 3: Run tests**

```bash
.venv/bin/python -m unittest tests.test_point_navigation_env
```

- [ ] **Step 4: Commit**

```bash
git add app/rl/envs/point_navigation.py tests/test_point_navigation_env.py
git commit -m "Add ClawLab point navigation env"
```

---

## Task 4: Dirt Seeking Env

**Agent:** Env Agent 3

**Files:**
- Create: `app/rl/envs/dirt_seeking.py`
- Test: `tests/test_dirt_seeking_env.py`

**Spec:**
- One or more dirt particles.
- Objective is to find and approach dirt, not necessarily clean all dirt.
- Uses local dirt sensor and obstacle-aware dirt proximity vector.
- Rewards first detection, reducing distance to visible dirt, and reaching clean radius.

- [ ] **Step 1: Add failing tests**

Tests must verify:

- dirt positions change with random seeds
- obstacle blocks dirt proximity signal
- reaching dirt terminates or emits `found_dirt=True`
- reward is higher when moving toward visible dirt

- [ ] **Step 2: Implement env**

Implement `DirtSeekingEnv(gym.Env)`.

Observation:

```text
sin_heading, cos_heading, local_dirt_signal, dirt_proximity_vector, lidar rays, remaining_step_fraction
```

Reward components:

```text
step_penalty, dirt_visible, dirt_progress, found_dirt, wall_penalty, obstacle_penalty
```

- [ ] **Step 3: Run tests**

```bash
.venv/bin/python -m unittest tests.test_dirt_seeking_env
```

- [ ] **Step 4: Commit**

```bash
git add app/rl/envs/dirt_seeking.py tests/test_dirt_seeking_env.py
git commit -m "Add ClawLab dirt seeking env"
```

---

## Task 5: Full Cleaning Env

**Agent:** Env Agent 4

**Files:**
- Create: `app/rl/envs/full_cleaning.py`
- Test: `tests/test_full_cleaning_env.py`

**Spec:**
- Full task: randomized dirt, randomized start, optional obstacles.
- Combines cleaning, navigation, and obstacle avoidance.
- Should wrap or share logic with current `RoombaEnv` behavior where possible.
- Must expose the same reward-hacking telemetry keys used by diagnostics.

- [ ] **Step 1: Add failing tests**

Tests must verify:

- cleaning dirt removes it
- all dirt cleaned terminates with success bonus
- collision abuse appears in telemetry when forced
- LiDAR/local dirt observation includes obstacle-aware dirt vector

- [ ] **Step 2: Implement env**

Implement `FullCleaningEnv(gym.Env)`.

Observation should match the final `random + lidar_local_dirt` behavior unless configured otherwise.

Reward components:

```text
step_penalty, progress, alignment, clean, terminal, turn_penalty, wall_penalty, obstacle_penalty
```

- [ ] **Step 3: Run tests**

```bash
.venv/bin/python -m unittest tests.test_full_cleaning_env
```

- [ ] **Step 4: Commit**

```bash
git add app/rl/envs/full_cleaning.py tests/test_full_cleaning_env.py
git commit -m "Add ClawLab full cleaning env"
```

---

## Task 6: Train/Eval Support for Env IDs

**Agent:** Training Agent

**Files:**
- Modify: `app/rl/config.py`
- Modify: `app/rl/train.py`
- Modify: `app/rl/eval.py`
- Modify: `app/rl/baseline.py`
- Modify: `app/rl/visualize.py`
- Test: `tests/test_training_env_ids.py`

- [ ] **Step 1: Add failing tests**

Test that `train_policy(..., env_id="ClawLab/ObstacleAvoidance-v0")` creates a model and writes `rl_config.json` with `env_id`.

Test that `evaluate_policy(..., env_id=...)` loads saved `env_id` if the caller omits it.

- [ ] **Step 2: Implement env factory**

Add a shared helper:

```python
def make_env_from_config(env_id: str | None, config: dict):
    if env_id:
        import app.rl.envs
        return gymnasium.make(env_id, **config)
    return RoombaEnv(**config)
```

Keep backward compatibility for old `RoombaEnv` runs.

- [ ] **Step 3: Thread env_id through CLIs**

Add `--env-id` to train/eval/baseline/visualize.

- [ ] **Step 4: Run tests**

```bash
.venv/bin/python -m unittest tests.test_training_env_ids tests.test_phase1_rl
```

- [ ] **Step 5: Commit**

```bash
git add app/rl/config.py app/rl/train.py app/rl/eval.py app/rl/baseline.py app/rl/visualize.py tests/test_training_env_ids.py
git commit -m "Support ClawLab env IDs in RL runners"
```

---

## Task 7: API Support for ClawLab Envs

**Agent:** API Agent

**Files:**
- Modify: `app/schemas/run.py`
- Modify: `app/services/runner.py`
- Modify: `app/main.py`
- Test: `tests/test_run_api.py`

- [ ] **Step 1: Add failing API/schema tests**

Tests must verify:

- `CreateRunRequest(env_id="ClawLab/PointNavigation-v0")` validates.
- invalid env IDs are rejected.
- `/api/envs` returns registered ClawLab envs.
- `/api/runs` metadata includes `env_id`.

- [ ] **Step 2: Extend schemas**

Add:

```python
env_id: str = Field(default="ClawLab/FullCleaning-v0")
```

Use a validator against the registry list.

- [ ] **Step 3: Add API endpoint**

Add:

```text
GET /api/envs
GET /api/envs/{env_id}
```

Return name, task type, default config, observation summary, reward components, and metrics fields.

- [ ] **Step 4: Thread env_id into runner**

Pass `env_id` into `train_policy`, `evaluate_policy`, and `evaluate_random_baseline`.

- [ ] **Step 5: Run tests**

```bash
.venv/bin/python -m unittest tests.test_run_api tests.test_run_config
```

- [ ] **Step 6: Commit**

```bash
git add app/schemas/run.py app/services/runner.py app/main.py tests/test_run_api.py
git commit -m "Expose ClawLab envs through API"
```

---

## Task 8: MCP Server

**Agent:** MCP Agent

**Files:**
- Create: `app/mcp/__init__.py`
- Create: `app/mcp/clawlab_server.py`
- Test: `tests/test_clawlab_mcp.py`

**MCP Timing:** Build this after Tasks 1-7 so the env IDs and run APIs are stable.

**Tools:**

- `list_envs`
- `describe_env`
- `start_training_run`
- `start_eval_run`
- `compare_runs`
- `generate_run_gif`
- `summarize_reward_hacking`

**Resources:**

- `clawlab://envs`
- `clawlab://runs/{run_id}/config`
- `clawlab://runs/{run_id}/metrics`
- `clawlab://runs/{run_id}/progress`
- `clawlab://runs/{run_id}/artifacts`
- `clawlab://runs/{run_id}/trajectory`

- [ ] **Step 1: Add failing MCP tests**

Tests should call server functions directly, not launch a subprocess initially:

- `list_envs()` returns ClawLab IDs.
- `describe_env("ClawLab/FullCleaning-v0")` returns reward components.
- `summarize_reward_hacking(run_id)` reads `eval_metrics.json`.

- [ ] **Step 2: Implement MCP server functions**

Use typed functions that call existing Python services. Do not expose arbitrary shell commands.

- [ ] **Step 3: Add MCP process entrypoint**

Add a module entrypoint:

```bash
.venv/bin/python -m app.mcp.clawlab_server
```

- [ ] **Step 4: Run tests**

```bash
.venv/bin/python -m unittest tests.test_clawlab_mcp
```

- [ ] **Step 5: Commit**

```bash
git add app/mcp tests/test_clawlab_mcp.py
git commit -m "Add ClawLab MCP server"
```

---

## Task 9: Benchmark Runner and Smoke Runs

**Agent:** Benchmark Agent

**Files:**
- Create: `app/rl/benchmark.py`
- Create: `scripts/run_clawlab_curriculum.py`
- Test: `tests/test_benchmark_summary.py`

- [ ] **Step 1: Add failing benchmark summary tests**

Test that given fake metrics for four envs, the summary reports:

- success rate
- average cleaned dirt, where relevant
- collision rates
- reward-hacking flag counts
- best run ID

- [ ] **Step 2: Implement benchmark runner**

The script should accept:

```bash
.venv/bin/python scripts/run_clawlab_curriculum.py --steps 50000 --seeds 1,2,3 --eval-episodes 20
```

It should run core envs first, then optionally scaled variants.

- [ ] **Step 3: Add selected smoke profile**

Add a fast profile:

```bash
.venv/bin/python scripts/run_clawlab_curriculum.py --profile smoke
```

Expected: each env trains for minimal steps and writes metrics, primarily to validate plumbing.

- [ ] **Step 4: Run tests**

```bash
.venv/bin/python -m unittest tests.test_benchmark_summary
```

- [ ] **Step 5: Commit**

```bash
git add app/rl/benchmark.py scripts/run_clawlab_curriculum.py tests/test_benchmark_summary.py
git commit -m "Add ClawLab curriculum benchmark runner"
```

---

## Task 10: Final Integration Review

**Agent:** Coordinator

- [ ] **Step 1: Run full test suite**

```bash
.venv/bin/python -m unittest discover tests
```

Expected: all tests pass.

- [ ] **Step 2: Run API smoke**

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then verify:

```bash
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8000/api/envs
```

- [ ] **Step 3: Run curriculum smoke**

```bash
.venv/bin/python scripts/run_clawlab_curriculum.py --profile smoke
```

- [ ] **Step 4: Generate one GIF for `ClawLab/FullCleaning-v0`**

```bash
.venv/bin/python -m app.rl.visualize --run-id <best_full_cleaning_run_id> --episodes 1
```

- [ ] **Step 5: Review reward-hacking flags**

All selected smoke benchmark runs should have `reward_hacking.flag_count` present. If any are nonzero, document them as known reward issues rather than hiding them.

- [ ] **Step 6: Commit final integration docs**

```bash
git add docs/superpowers/plans/2026-04-25-clawlab-curriculum-api-mcp-subagents.md
git commit -m "Plan ClawLab curriculum API and MCP subagents"
```

---

## Execution Strategy

1. Dispatch Env Agents 1-4 in parallel.
2. Dispatch Integration Agent after env agents return or when stubs are ready.
3. Dispatch Training and API agents in parallel after registry lands.
4. Dispatch MCP Agent after API/schema names stabilize.
5. Dispatch Benchmark Agent after train/eval supports env IDs.
6. Coordinator runs full tests, smoke runs, final review, and commit/push.

## Acceptance Criteria

- Four core `ClawLab/...` env IDs can be created with `gym.make`.
- Each env has focused unit tests and valid observations.
- Train/eval/baseline/visualize accept `env_id`.
- FastAPI exposes env listing and run creation by env ID.
- MCP exposes whitelisted tools and read-only resources for envs/runs.
- Benchmark runner can train/eval the curriculum suite.
- Metrics include reward components and reward-hacking flags.
- Frontend remains untouched.

