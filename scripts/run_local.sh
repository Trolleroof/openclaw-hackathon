#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PROJECT_ROOT}/.venv/bin/python"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="${PYTHON:-python}"
fi

"${PYTHON_BIN}" -m app.rl.train --run-id local_test --total-timesteps 30000
"${PYTHON_BIN}" -m app.rl.eval --run-id local_test --episodes 50
"${PYTHON_BIN}" -m app.rl.baseline --episodes 50
