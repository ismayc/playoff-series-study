#!/bin/bash
# Every check in this study. Non-zero exit on any failure. PY overrides the
# interpreter (the family orchestrator sets it to a shared venv).
#
# The harvest (01) needs the network and is not rerun here; the series build
# needs the local, gitignored raw game logs.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-../.venv/bin/python}

echo "=== unit tests: Python (pytest) ==="
$PY -m pytest tests/python -q

echo
echo "=== series build and its checks ==="
$PY python/02_build_series.py | tail -2
