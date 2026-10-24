#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ is required"'
node -e 'let [a,b]=process.versions.node.split(".").map(Number); if(!((a===20&&b>=19)||(a===22&&b>=12)||a>22)) throw Error("Use Node 22.12+ or 24 LTS")'
if [[ ! -x .venv/bin/python ]]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install -r backend/requirements-dev.txt
if [[ "${1:-}" == "--system-deps" ]]; then
  if [[ "$(id -u)" == "0" ]]; then
    .venv/bin/python -m playwright install-deps chromium
  else
    sudo "$(pwd)/.venv/bin/python" -m playwright install-deps chromium
  fi
fi
.venv/bin/python -m playwright install --no-shell chromium
npm --prefix frontend ci --no-audit --no-fund
npm --prefix frontend run build
printf '\nSetup finished. Start with: bash start.sh\n'
