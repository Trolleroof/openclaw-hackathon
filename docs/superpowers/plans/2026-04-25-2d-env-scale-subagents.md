# 2D Environment Scale-Out Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current fixed-route 2D PPO demo into a configurable 2D RL environment suite with randomized layouts, synthetic LiDAR, local dirt sensing, held-out evaluation, and diagnostics that expose reward hacking.

**Architecture:** Keep the existing `RoombaEnv` working while extracting layout and sensor logic into standalone modules that can be built in parallel. Integrate through explicit config objects after those modules are tested, then run seed sweeps and visualization against train and held-out layouts.

**Tech Stack:** Python 3.11, Gymnasium, Stable-Baselines3 PPO, NumPy, Pillow, `unittest`.

---

## File Ownership

- Agent A owns layout generation only: create `app/rl/layouts.py`, `tests/test_layouts.py`.
- Agent B owns sensor simulation only: create `app/rl/sensors.py`, `tests/test_sensors.py`.
- Agent C owns metrics and evaluation diagnostics: modify `app/rl/eval.py`, `app/rl/telemetry.py`, create/update `tests/test_eval_diagnostics.py`.
- Agent D owns training/config plumbing: create `app/rl/config.py`, modify `app/rl/train.py`, `app/schemas/run.py`, `scripts/run_local.sh`, create/update tests.
- Integration agent owns `app/rl/env.py` after A/B/D land.
- Do not modify `frontend/` in this plan.

## Parallel Wave 1

### Task 1: Layout Generator Agent

**Files:**
- Create: `app/rl/layouts.py`
- Create: `tests/test_layouts.py`

- [ ] **Step 1: Write failing tests for deterministic preset and randomized held-out layouts**

```python
import unittest
import numpy as np

from app.rl.layouts import LayoutConfig, generate_layout


class LayoutTests(unittest.TestCase):
    def test_preset_layout_matches_existing_default(self):
        layout = generate_layout(LayoutConfig(mode="preset", room_size=10.0, dirt_count=3), seed=0)
        np.testing.assert_allclose(layout.robot, np.array([1.0, 1.0], dtype=np.float32))
        self.assertEqual(layout.heading, 0.0)
        np.testing.assert_allclose(
            layout.dirt,
            np.array([[8.0, 8.0], [2.0, 7.0], [7.0, 2.0]], dtype=np.float32),
        )
        self.assertEqual(layout.obstacles, [])

    def test_random_layout_reproducible_by_seed(self):
        config = LayoutConfig(mode="random", room_size=10.0, dirt_count=5, obstacle_count=2)
        a = generate_layout(config, seed=123)
        b = generate_layout(config, seed=123)
        np.testing.assert_allclose(a.robot, b.robot)
        np.testing.assert_allclose(a.dirt, b.dirt)
        self.assertEqual(a.obstacles, b.obstacles)

    def test_random_layout_changes_across_seeds(self):
        config = LayoutConfig(mode="random", room_size=10.0, dirt_count=5, obstacle_count=2)
        a = generate_layout(config, seed=123)
        b = generate_layout(config, seed=124)
        self.assertFalse(np.allclose(a.dirt, b.dirt))

    def test_generated_positions_have_clearance(self):
        config = LayoutConfig(mode="random", room_size=10.0, dirt_count=20, obstacle_count=4, min_clearance=0.6)
        layout = generate_layout(config, seed=9)
        self.assertTrue(np.all(layout.dirt >= 0.5))
        self.assertTrue(np.all(layout.dirt <= 9.5))
        for dirt in layout.dirt:
            self.assertGreaterEqual(np.linalg.norm(dirt - layout.robot), config.min_clearance)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and confirm import failure**

Run:

```bash
.venv/bin/python -m unittest tests.test_layouts
```

Expected: fail with `ModuleNotFoundError: No module named 'app.rl.layouts'`.

- [ ] **Step 3: Implement `layouts.py`**

```python
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CircleObstacle:
    x: float
    y: float
    radius: float


@dataclass(frozen=True)
class LayoutConfig:
    mode: str = "preset"
    room_size: float = 10.0
    dirt_count: int = 3
    obstacle_count: int = 0
    min_clearance: float = 0.6
    randomize_start: bool = True


@dataclass(frozen=True)
class Layout:
    robot: np.ndarray
    heading: float
    dirt: np.ndarray
    obstacles: list[CircleObstacle]


PRESET_DIRT = np.array(
    [[8.0, 8.0], [2.0, 7.0], [7.0, 2.0], [5.0, 5.0], [8.0, 3.0], [3.0, 8.0]],
    dtype=np.float32,
)


def generate_layout(config: LayoutConfig, seed: int | None = None) -> Layout:
    if config.mode == "preset":
        dirt = PRESET_DIRT[: config.dirt_count].copy()
        dirt = np.clip(dirt, 0.5, config.room_size - 0.5).astype(np.float32)
        return Layout(
            robot=np.array([1.0, 1.0], dtype=np.float32),
            heading=0.0,
            dirt=dirt,
            obstacles=[],
        )
    if config.mode != "random":
        raise ValueError(f"Unsupported layout mode: {config.mode}")

    rng = np.random.default_rng(seed)
    robot = _sample_point(rng, config.room_size)
    heading = float(rng.uniform(-np.pi, np.pi)) if config.randomize_start else 0.0
    obstacles = [
        CircleObstacle(*_sample_point(rng, config.room_size), radius=float(rng.uniform(0.25, 0.75)))
        for _ in range(config.obstacle_count)
    ]
    dirt = []
    attempts = 0
    while len(dirt) < config.dirt_count:
        attempts += 1
        if attempts > config.dirt_count * 500:
            raise RuntimeError("Could not generate layout with requested clearance")
        point = _sample_point(rng, config.room_size)
        if np.linalg.norm(point - robot) < config.min_clearance:
            continue
        if any(np.linalg.norm(point - np.array([obs.x, obs.y])) < obs.radius + config.min_clearance for obs in obstacles):
            continue
        dirt.append(point)

    return Layout(
        robot=robot.astype(np.float32),
        heading=heading,
        dirt=np.array(dirt, dtype=np.float32),
        obstacles=obstacles,
    )


def _sample_point(rng: np.random.Generator, room_size: float) -> np.ndarray:
    return rng.uniform(0.5, room_size - 0.5, size=2).astype(np.float32)
```

- [ ] **Step 4: Run tests and commit**

Run:

```bash
.venv/bin/python -m unittest tests.test_layouts
```

Expected: all tests pass.

Commit:

```bash
git add app/rl/layouts.py tests/test_layouts.py
git commit -m "Add randomized 2D layout generator"
```

### Task 2: Sensor Simulation Agent

**Files:**
- Create: `app/rl/sensors.py`
- Create: `tests/test_sensors.py`

- [ ] **Step 1: Write failing tests for LiDAR and local dirt sensors**

```python
import unittest
import numpy as np

from app.rl.layouts import CircleObstacle
from app.rl.sensors import cast_lidar_rays, local_dirt_signal


class SensorTests(unittest.TestCase):
    def test_lidar_detects_nearest_wall_ahead(self):
        readings = cast_lidar_rays(
            robot=np.array([1.0, 1.0], dtype=np.float32),
            heading=0.0,
            room_size=10.0,
            obstacles=[],
            ray_count=4,
            max_range=5.0,
        )
        self.assertEqual(readings.shape, (4,))
        self.assertAlmostEqual(readings[0], 1.0)

    def test_lidar_detects_circle_obstacle_before_wall(self):
        readings = cast_lidar_rays(
            robot=np.array([1.0, 1.0], dtype=np.float32),
            heading=0.0,
            room_size=10.0,
            obstacles=[CircleObstacle(x=3.0, y=1.0, radius=0.5)],
            ray_count=8,
            max_range=5.0,
        )
        self.assertLess(readings[0], 0.4)

    def test_local_dirt_signal_only_detects_nearby_dirt(self):
        dirt = np.array([[1.2, 1.1], [8.0, 8.0]], dtype=np.float32)
        self.assertEqual(local_dirt_signal(np.array([1.0, 1.0], dtype=np.float32), dirt, radius=0.4), 1.0)
        self.assertEqual(local_dirt_signal(np.array([5.0, 5.0], dtype=np.float32), dirt, radius=0.4), 0.0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
.venv/bin/python -m unittest tests.test_sensors
```

Expected: fail with `ModuleNotFoundError: No module named 'app.rl.sensors'`.

- [ ] **Step 3: Implement `sensors.py`**

```python
from __future__ import annotations

import numpy as np

from app.rl.layouts import CircleObstacle


def cast_lidar_rays(
    robot: np.ndarray,
    heading: float,
    room_size: float,
    obstacles: list[CircleObstacle],
    ray_count: int = 16,
    max_range: float = 5.0,
    step_size: float = 0.05,
) -> np.ndarray:
    readings = []
    for ray_index in range(ray_count):
        angle = heading + (2 * np.pi * ray_index / ray_count)
        direction = np.array([np.cos(angle), np.sin(angle)], dtype=np.float32)
        distance = _ray_distance(robot, direction, room_size, obstacles, max_range, step_size)
        readings.append(distance / max_range)
    return np.array(readings, dtype=np.float32)


def local_dirt_signal(robot: np.ndarray, dirt: np.ndarray, radius: float) -> float:
    if len(dirt) == 0:
        return 0.0
    return float(np.any(np.linalg.norm(dirt - robot, axis=1) <= radius))


def _ray_distance(
    robot: np.ndarray,
    direction: np.ndarray,
    room_size: float,
    obstacles: list[CircleObstacle],
    max_range: float,
    step_size: float,
) -> float:
    distance = 0.0
    while distance < max_range:
        point = robot + direction * distance
        if point[0] <= 0.0 or point[0] >= room_size or point[1] <= 0.0 or point[1] >= room_size:
            return distance
        for obstacle in obstacles:
            center = np.array([obstacle.x, obstacle.y], dtype=np.float32)
            if np.linalg.norm(point - center) <= obstacle.radius:
                return distance
        distance += step_size
    return max_range
```

- [ ] **Step 4: Run tests and commit**

Run:

```bash
.venv/bin/python -m unittest tests.test_sensors
```

Expected: all tests pass.

Commit:

```bash
git add app/rl/sensors.py tests/test_sensors.py
git commit -m "Add 2D sensor simulation"
```

### Task 3: Evaluation Diagnostics Agent

**Files:**
- Modify: `app/rl/telemetry.py`
- Modify: `app/rl/eval.py`
- Create: `tests/test_eval_diagnostics.py`

- [ ] **Step 1: Write failing tests for held-out evaluation flags**

```python
import unittest

from app.rl.eval import summarize_generalization


class EvalDiagnosticsTests(unittest.TestCase):
    def test_generalization_summary_flags_train_eval_gap(self):
        summary = summarize_generalization(
            train_metrics={"success_rate": 1.0, "avg_cleaned_dirt": 3.0},
            heldout_metrics={"success_rate": 0.2, "avg_cleaned_dirt": 1.0},
        )
        self.assertEqual(summary["success_rate_gap"], 0.8)
        self.assertTrue(summary["possible_memorization"])

    def test_generalization_summary_allows_small_gap(self):
        summary = summarize_generalization(
            train_metrics={"success_rate": 0.9, "avg_cleaned_dirt": 2.8},
            heldout_metrics={"success_rate": 0.85, "avg_cleaned_dirt": 2.7},
        )
        self.assertFalse(summary["possible_memorization"])
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
.venv/bin/python -m unittest tests.test_eval_diagnostics
```

Expected: fail with `ImportError: cannot import name 'summarize_generalization'`.

- [ ] **Step 3: Implement summary helper in `app/rl/eval.py`**

```python
def summarize_generalization(train_metrics: dict, heldout_metrics: dict) -> dict:
    success_rate_gap = float(train_metrics["success_rate"] - heldout_metrics["success_rate"])
    cleaned_dirt_gap = float(train_metrics["avg_cleaned_dirt"] - heldout_metrics["avg_cleaned_dirt"])
    return {
        "train_success_rate": train_metrics["success_rate"],
        "heldout_success_rate": heldout_metrics["success_rate"],
        "success_rate_gap": success_rate_gap,
        "cleaned_dirt_gap": cleaned_dirt_gap,
        "possible_memorization": success_rate_gap >= 0.25 or cleaned_dirt_gap >= 1.0,
    }
```

- [ ] **Step 4: Run tests and commit**

Run:

```bash
.venv/bin/python -m unittest tests.test_eval_diagnostics tests.test_phase1_rl
```

Expected: all tests pass.

Commit:

```bash
git add app/rl/eval.py tests/test_eval_diagnostics.py
git commit -m "Add generalization diagnostics"
```

### Task 4: Training Config Agent

**Files:**
- Create: `app/rl/config.py`
- Modify: `app/rl/train.py`
- Modify: `app/schemas/run.py`
- Modify: `scripts/run_local.sh`
- Create: `tests/test_run_config.py`

- [ ] **Step 1: Write failing tests for run config defaults**

```python
import unittest

from app.rl.config import RunConfig
from app.schemas.run import CreateRunRequest


class RunConfigTests(unittest.TestCase):
    def test_run_config_defaults_to_randomized_generalization_mode(self):
        config = RunConfig()
        self.assertEqual(config.total_timesteps, 200_000)
        self.assertEqual(config.layout_mode, "random")
        self.assertEqual(config.sensor_mode, "lidar_local_dirt")
        self.assertEqual(config.eval_seed_offset, 10_000)

    def test_api_request_exposes_layout_and_sensor_mode(self):
        request = CreateRunRequest()
        self.assertEqual(request.layout_mode, "random")
        self.assertEqual(request.sensor_mode, "lidar_local_dirt")
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
.venv/bin/python -m unittest tests.test_run_config
```

Expected: fail with `ModuleNotFoundError: No module named 'app.rl.config'`.

- [ ] **Step 3: Implement config object**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class RunConfig:
    total_timesteps: int = 200_000
    eval_episodes: int = 50
    seed: int = 42
    eval_seed_offset: int = 10_000
    room_size: float = 10.0
    max_steps: int = 200
    dirt_count: int = 6
    obstacle_count: int = 4
    layout_mode: str = "random"
    sensor_mode: str = "lidar_local_dirt"
    lidar_rays: int = 16
    device: str = "auto"
```

- [ ] **Step 4: Update schema fields**

In `app/schemas/run.py`, import `RunConfig` and add:

```python
DEFAULT_RUN_CONFIG = RunConfig()

class CreateRunRequest(BaseModel):
    total_timesteps: int = Field(default=DEFAULT_RUN_CONFIG.total_timesteps, ge=1_000, le=2_000_000)
    eval_episodes: int = Field(default=DEFAULT_RUN_CONFIG.eval_episodes, ge=1, le=1_000)
    seed: int = Field(default=DEFAULT_RUN_CONFIG.seed)
    eval_seed_offset: int = Field(default=DEFAULT_RUN_CONFIG.eval_seed_offset, ge=1)
    room_size: float = Field(default=DEFAULT_RUN_CONFIG.room_size, gt=1.0)
    max_steps: int = Field(default=DEFAULT_RUN_CONFIG.max_steps, ge=20, le=5_000)
    dirt_count: int = Field(default=DEFAULT_RUN_CONFIG.dirt_count, ge=1, le=100)
    obstacle_count: int = Field(default=DEFAULT_RUN_CONFIG.obstacle_count, ge=0, le=100)
    layout_mode: str = Field(default=DEFAULT_RUN_CONFIG.layout_mode, pattern="^(preset|random)$")
    sensor_mode: str = Field(default=DEFAULT_RUN_CONFIG.sensor_mode, pattern="^(oracle|lidar_local_dirt)$")
    lidar_rays: int = Field(default=DEFAULT_RUN_CONFIG.lidar_rays, ge=0, le=128)
    device: str = Field(default=DEFAULT_RUN_CONFIG.device, pattern="^(auto|cpu|cuda|mps)$")
```

- [ ] **Step 5: Run tests and commit**

Run:

```bash
.venv/bin/python -m unittest tests.test_run_config tests.test_phase1_rl
```

Expected: all tests pass after updating any old default assertions.

Commit:

```bash
git add app/rl/config.py app/schemas/run.py app/rl/train.py scripts/run_local.sh tests/test_run_config.py tests/test_phase1_rl.py
git commit -m "Add configurable 2D run defaults"
```

## Integration Wave

### Task 5: Integrate Layouts and Sensors into `RoombaEnv`

**Files:**
- Modify: `app/rl/env.py`
- Modify: `app/rl/train.py`
- Modify: `app/rl/eval.py`
- Modify: `app/rl/baseline.py`
- Modify: `app/services/runner.py`
- Modify: `tests/test_phase1_rl.py`

- [ ] **Step 1: Add env behavior tests**

Add to `tests/test_phase1_rl.py`:

```python
def test_random_layout_env_changes_dirt_by_seed(self):
    a = RoombaEnv(layout_mode="random", seed=1)
    b = RoombaEnv(layout_mode="random", seed=2)
    a.reset(seed=1)
    b.reset(seed=2)
    self.assertFalse(np.allclose(a.dirt, b.dirt))


def test_lidar_local_dirt_mode_removes_oracle_dirt_vectors(self):
    env = RoombaEnv(layout_mode="random", sensor_mode="lidar_local_dirt", lidar_rays=16, seed=1)
    obs, _ = env.reset(seed=1)
    self.assertEqual(obs.shape, (24,))
    self.assertTrue(np.all(obs >= -1.0))
    self.assertTrue(np.all(obs <= 1.0))
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
.venv/bin/python -m unittest tests.test_phase1_rl
```

Expected: fail because `RoombaEnv` has no `layout_mode`, `sensor_mode`, or `lidar_rays` arguments.

- [ ] **Step 3: Update `RoombaEnv.__init__` signature**

In `app/rl/env.py`, add:

```python
layout_mode: str = "preset",
sensor_mode: str = "oracle",
obstacle_count: int = 0,
lidar_rays: int = 0,
eval_seed_offset: int = 10_000,
```

Store these as instance fields and use `LayoutConfig` in `reset()`.

- [ ] **Step 4: Update observations**

Keep existing oracle observation for `sensor_mode="oracle"`. Add `sensor_mode="lidar_local_dirt"` observation:

```python
[
    robot_x_norm,
    robot_y_norm,
    sin_heading,
    cos_heading,
    remaining_dirt_fraction,
    local_dirt_signal,
    *lidar_readings,
    left_wall_norm,
    right_wall_norm,
    bottom_wall_norm,
    top_wall_norm,
]
```

For `lidar_rays=16`, shape is `24`.

- [ ] **Step 5: Update train/eval/baseline/service args**

Thread `layout_mode`, `sensor_mode`, `obstacle_count`, and `lidar_rays` through:

```python
train_policy(...)
evaluate_policy(...)
evaluate_random_baseline(...)
create_run(...)
```

- [ ] **Step 6: Run tests and commit**

Run:

```bash
.venv/bin/python -m unittest tests.test_phase1_rl tests.test_layouts tests.test_sensors tests.test_run_config tests.test_eval_diagnostics
```

Expected: all tests pass.

Commit:

```bash
git add app/rl/env.py app/rl/train.py app/rl/eval.py app/rl/baseline.py app/services/runner.py tests/test_phase1_rl.py
git commit -m "Integrate randomized sensor-based 2D environment"
```

### Task 6: Seed Sweep and Artifact Verification

**Files:**
- Modify: `RL_README.md`
- Modify: `plan.md`
- No frontend files.

- [ ] **Step 1: Run seed sweep**

Run:

```bash
.venv/bin/python -m app.rl.train --run-id lidar_random_seed42 --seed 42 --device cpu --verbose 0
.venv/bin/python -m app.rl.eval --run-id lidar_random_seed42 --episodes 50
.venv/bin/python -m app.rl.visualize --run-id lidar_random_seed42 --seed 10000 --episodes 2 --fps 6 --hold-final-frames 30
```

Expected: model, metrics, GIFs, and trajectory JSON are written.

- [ ] **Step 2: Run held-out seed check**

Run:

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path
metrics = json.loads(Path("runs/lidar_random_seed42/metrics/eval_metrics.json").read_text())
print(json.dumps({
    "success_rate": metrics["success_rate"],
    "avg_cleaned_dirt": metrics["avg_cleaned_dirt"],
    "avg_wall_hits": metrics["avg_wall_hits"],
    "avg_final_clean_step": metrics["avg_final_clean_step"],
}, indent=2))
PY
```

Expected: values print without missing-key errors.

- [ ] **Step 3: Update docs with honest status**

In `plan.md`, update Phase 1 status to say the fast 2D backend now supports both `oracle` and `lidar_local_dirt` modes. In `RL_README.md`, add commands for `layout_mode=random` and visualization.

- [ ] **Step 4: Commit**

```bash
git add RL_README.md plan.md
git commit -m "Document randomized 2D environment workflow"
```

## Subagent Dispatch Prompts

Use these as initial prompts. Tell every worker: “You are not alone in the codebase. Do not revert or overwrite changes outside your owned files. Adapt to concurrent changes.”

### Agent A Prompt

Implement Task 1 from `docs/superpowers/plans/2026-04-25-2d-env-scale-subagents.md`. Own only `app/rl/layouts.py` and `tests/test_layouts.py`. Use TDD. Commit your changes. Return changed files, tests run, and any concerns.

### Agent B Prompt

Implement Task 2 from `docs/superpowers/plans/2026-04-25-2d-env-scale-subagents.md`. Own only `app/rl/sensors.py` and `tests/test_sensors.py`. Use TDD. Commit your changes. Return changed files, tests run, and any concerns.

### Agent C Prompt

Implement Task 3 from `docs/superpowers/plans/2026-04-25-2d-env-scale-subagents.md`. Own only `app/rl/eval.py`, `app/rl/telemetry.py`, and `tests/test_eval_diagnostics.py`. Use TDD. Commit your changes. Return changed files, tests run, and any concerns.

### Agent D Prompt

Implement Task 4 from `docs/superpowers/plans/2026-04-25-2d-env-scale-subagents.md`. Own only `app/rl/config.py`, `app/rl/train.py`, `app/schemas/run.py`, `scripts/run_local.sh`, `tests/test_run_config.py`, and necessary assertions in `tests/test_phase1_rl.py`. Use TDD. Commit your changes. Return changed files, tests run, and any concerns.

## Review Gates

- After Wave 1, run:

```bash
.venv/bin/python -m unittest tests.test_layouts tests.test_sensors tests.test_eval_diagnostics tests.test_run_config tests.test_phase1_rl
```

- Do not start Task 5 until all Wave 1 tests pass.
- After Task 5, run the full backend test command above and a short run:

```bash
.venv/bin/python -m app.rl.train --run-id integration_smoke --total-timesteps 5000 --seed 1 --device cpu --verbose 0
.venv/bin/python -m app.rl.eval --run-id integration_smoke --episodes 3
```

- Before final push, verify:

```bash
git status --short
.venv/bin/python -m unittest tests.test_layouts tests.test_sensors tests.test_eval_diagnostics tests.test_run_config tests.test_phase1_rl
```

