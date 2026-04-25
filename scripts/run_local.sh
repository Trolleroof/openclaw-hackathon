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

"${PYTHON_BIN}" -m app.rl.train --run-id local_test --total-timesteps 30000 --device "${DEVICE}"
"${PYTHON_BIN}" -m app.rl.eval --run-id local_test --episodes 50
"${PYTHON_BIN}" -m app.rl.baseline --episodes 50
