#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ is required"'
node -e 'let [a,b]=process.versions.node.split(".").map(Number); if(!((a===20&&b>=19)||(a===22&&b>=12)||a>22)) throw Error("Use Node 22.12+ or 24 LTS")'
if [[ "${1:-}" == "--system-deps" ]]; then
 printf 'V0.2 bakes Linux browser libraries into the development image. Rebuild Container instead of changing APT repositories.\n'
fi
if [[ ! -x .venv/bin/python ]]; then
 if [[ -e .venv || -L .venv ]]; then
   mkdir -p .v02-backups
   mv .venv ".v02-backups/venv-$(date +%s)"
 fi
 python3 -m venv .venv
fi
.venv/bin/python -m pip install -r backend/requirements-dev.txt
# The maintained image already has this matching full Chromium build. Local
# installs use the same binary; launch always specifies channel='chromium'.
if ! .venv/bin/python - <<'PY'
from pathlib import Path
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 if not Path(p.chromium.executable_path).exists():raise SystemExit(1)
PY
then
 .venv/bin/python -m playwright install --no-shell chromium
fi
npm --prefix frontend ci --no-audit --no-fund
npm --prefix frontend run build
printf '\nSetup finished. Public mode: bash start.sh --isolated\nRestricted local mode: bash start.sh\n'
