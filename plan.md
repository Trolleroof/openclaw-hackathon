# Minimal RL → Webots Plan

## Phase 1: Simple 2D RL (No Webots)
- Build Roomba-like env (env.py)
- Train PPO (train.py)
- Evaluate (eval.py)
- Goal: prove RL loop works in minutes

## Phase 2: Introduce Hermes
- Generate env + config automatically
- Run training via CLI
- Log metrics (success rate, reward)

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
- Hermes monitors runs
- Adjust reward/config
- Compare experiments

## Phase 6: Worlds API (optional)
- Generate GLB scene
- Import into Webots
- Overlay RL primitives

## Goal
Prompt → Environment → Training → Evaluation → Improvement
