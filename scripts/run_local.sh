#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PROJECT_ROOT}/.venv/bin/python"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-${PROJECT_ROOT}/.cache}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-${PROJECT_ROOT}/.cache/matplotlib}"

mkdir -p "${MPLCONFIGDIR}"
mkdir -p "${XDG_CACHE_HOME}/fontconfig"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="${PYTHON:-python}"
fi

DEVICE="${DEVICE:-auto}"
TOTAL_TIMESTEPS="${TOTAL_TIMESTEPS:-200000}"
VERBOSE="${VERBOSE:-0}"
LAYOUT_MODE="${LAYOUT_MODE:-random}"
SENSOR_MODE="${SENSOR_MODE:-lidar_local_dirt}"
DIRT_COUNT="${DIRT_COUNT:-6}"
OBSTACLE_COUNT="${OBSTACLE_COUNT:-4}"
LIDAR_RAYS="${LIDAR_RAYS:-16}"

"${PYTHON_BIN}" -m app.rl.train \
  --run-id local_test \
  --total-timesteps "${TOTAL_TIMESTEPS}" \
  --device "${DEVICE}" \
  --verbose "${VERBOSE}" \
  --layout-mode "${LAYOUT_MODE}" \
  --sensor-mode "${SENSOR_MODE}" \
  --dirt-count "${DIRT_COUNT}" \
  --obstacle-count "${OBSTACLE_COUNT}" \
  --lidar-rays "${LIDAR_RAYS}"
"${PYTHON_BIN}" -m app.rl.eval --run-id local_test --episodes 50
"${PYTHON_BIN}" -m app.rl.baseline --episodes 50
