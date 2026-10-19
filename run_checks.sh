#!/bin/bash
# Every check in this study. Non-zero exit on any failure. PY overrides the
# interpreter (the family orchestrator sets it to a shared venv).
#
# The harvests (01 and 10) need the network and are not rerun here; the series build
# needs the local, gitignored raw game logs.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-../.venv/bin/python}

echo "=== unit tests: Python (pytest) ==="
$PY -m pytest tests/python -q

echo
echo "=== unit tests: R (testthat) ==="
Rscript tests/R/run_tests.R | tail -1

echo
echo "=== series build and its checks ==="
$PY python/02_build_series.py | tail -2

echo
echo "=== question 1: Python, then R ==="
$PY python/03_game1.py
Rscript R/03_game1.R

echo
echo "=== question 4: Python, then R ==="
$PY python/06_profiles.py
Rscript R/06_profiles.R

echo
echo "=== question 3: Python, then R ==="
$PY python/08_stakes_rest.py
Rscript R/08_stakes_rest.R

echo
echo "=== follow-ups 5 to 7: Python, then R ==="
$PY python/11_followups.py
Rscript R/11_followups.R

echo
echo "=== follow-up 8 (officials): Python, then R ==="
$PY python/12_officials.py
Rscript R/12_officials.R

echo
echo "=== reconciliation: R vs Python ==="
$PY python/04_reconcile.py | tail -1

echo
echo "=== findings: README numbers regenerate from outputs ==="
$PY python/05_findings.py --check

echo
echo "=== review page builds ==="
$PY python/07_review.py
