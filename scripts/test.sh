#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$(pwd)/backend${PYTHONPATH:+:$PYTHONPATH}"
npm --prefix frontend test
npm --prefix frontend run build
.venv/bin/python -m pytest -q -rs "$@"
# pytest explains blocked browser tests, but a green unit suite is not acceptance.
.venv/bin/python scripts/check_browser.py
