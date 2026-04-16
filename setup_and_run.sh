#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# setup_and_run.sh
# Sets up the Python environment and runs the network monitor + validator.
# Usage:  bash setup_and_run.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail   # exit on error, undefined var, or pipe failure

echo "════════════════════════════════════════"
echo " Network Performance Monitor"
echo "════════════════════════════════════════"

# ── 1. Check Python version ───────────────────────────────────────────────────
echo "[1/4] Checking Python version..."
python3 --version
PYTHON_VER=$(python3 -c "import sys; print(sys.version_info.minor)")
if [ "$PYTHON_VER" -lt 10 ]; then
  echo "ERROR: Python 3.10 or higher is required."
  exit 1
fi
echo "      OK"

# ── 2. Install dependencies ───────────────────────────────────────────────────
echo "[2/4] Installing dependencies..."
pip install --quiet -r requirements.txt
echo "      OK"

# ── 3. Run unit tests first ───────────────────────────────────────────────────
echo "[3/4] Running unit tests..."
pytest tests/ -v --tb=short
echo "      Tests complete"

# ── 4. Run the monitor ────────────────────────────────────────────────────────
echo "[4/4] Running network measurements and validation..."
python3 main.py
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
  echo "All done — network is healthy."
else
  echo "Done — validation failures detected. Check output above."
fi

exit $EXIT_CODE
