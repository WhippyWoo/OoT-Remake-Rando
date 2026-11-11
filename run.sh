#!/bin/sh
# OoT Remake Randomizer launcher for macOS/Linux.
cd "$(dirname "$0")" || exit 1
PY=$(command -v python3 || command -v python) || { echo "Python 3 is not installed."; exit 1; }
"$PY" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" || { echo "Python 3.8 or newer is needed."; exit 1; }
"$PY" -c "from lib import zst; import sys; sys.exit(0 if zst.BACKEND else 1)" 2>/dev/null || "$PY" -m pip install --user zstandard || exit 1
exec "$PY" gui.py
