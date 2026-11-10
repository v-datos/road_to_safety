#!/usr/bin/env bash
# verify.sh: Run test suites across all three Canadian collision research projects.
# Usage:
#   ./scripts/verify.sh          # Runs test suites (clean checkout portable + derived data if present)
#   ./scripts/verify.sh --full   # Explicitly checks prerequisites for full derived artifact tests

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mpl}"

echo "================================================================="
echo " Canadian Collision Research — Test Suite Verification"
echo "================================================================="

CHECK_FULL=0
if [[ "${1:-}" == "--full" ]]; then
    CHECK_FULL=1
fi

# Prerequisite audit
echo ""
echo "[1/4] Checking Data Prerequisites:"
RTS_DATA="${REPO_ROOT}/projects/road_to_safety/data/derived/corridor_pilot/segment_exposure_crashes.parquet"
TRUCKS_DATA="${REPO_ROOT}/projects/trucks/data/derived/ncdb/collisions.parquet"
BIKES_DATA="${REPO_ROOT}/projects/bicycles/data/derived/build.duckdb"

if [[ -f "$RTS_DATA" ]]; then
    echo "  ✓ Road to Safety: full derived data present (${RTS_DATA})"
else
    echo "  ○ Road to Safety: clean checkout mode (derived parquet absent; artifact tests will be skipped)"
fi

if [[ -f "$TRUCKS_DATA" ]]; then
    echo "  ✓ Trucks: full derived data present (${TRUCKS_DATA})"
else
    echo "  ○ Trucks: clean checkout mode (derived parquet absent; full sensitivity tests will be skipped)"
fi

if [[ -f "$BIKES_DATA" ]]; then
    echo "  ✓ Bicycles: full derived database present (${BIKES_DATA})"
else
    echo "  ○ Bicycles: clean checkout mode (build.duckdb absent; full corridor tests will be skipped)"
fi

if [[ "$CHECK_FULL" -eq 1 ]]; then
    if [[ ! -f "$RTS_DATA" || ! -f "$TRUCKS_DATA" || ! -f "$BIKES_DATA" ]]; then
        echo ""
        echo "ERROR: --full requested but one or more derived datasets are missing."
        echo "To build full derived data:"
        echo "  - projects/road_to_safety: python -m road_to_safety.corridor_pilot"
        echo "  - projects/trucks: uv sync && python src/truck_collisions/build.py"
        echo "  - projects/bicycles: uv sync && python src/bicycle_collisions/build.py"
        exit 1
    fi
fi

# Run road_to_safety
echo ""
echo "[2/4] Testing projects/road_to_safety..."
PYTHON_RTS="${REPO_ROOT}/projects/road_to_safety/.venv/bin/python"
if [[ ! -x "$PYTHON_RTS" ]]; then
    PYTHON_RTS="python3"
fi
(
    cd "${REPO_ROOT}/projects/road_to_safety"
    PYTHONPATH=src "$PYTHON_RTS" -m unittest discover -s tests -v
)

# Run trucks
echo ""
echo "[3/4] Testing projects/trucks..."
PYTHON_TRUCKS="${REPO_ROOT}/projects/trucks/.venv/bin/python"
if [[ ! -x "$PYTHON_TRUCKS" ]]; then
    PYTHON_TRUCKS="python3"
fi
(
    cd "${REPO_ROOT}/projects/trucks"
    PYTHONPATH=src "$PYTHON_TRUCKS" -m unittest discover -s tests -v
)

# Run bicycles
echo ""
echo "[4/4] Testing projects/bicycles..."
PYTHON_BIKES="${REPO_ROOT}/projects/bicycles/.venv/bin/python"
if [[ ! -x "$PYTHON_BIKES" ]]; then
    PYTHON_BIKES="python3"
fi
(
    cd "${REPO_ROOT}/projects/bicycles"
    PYTHONPATH=src "$PYTHON_BIKES" -m unittest discover -s tests -v
)

echo ""
echo "================================================================="
echo " ✓ All test suites completed successfully!"
echo "================================================================="
