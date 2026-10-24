#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -x .venv/bin/python ]] || { printf 'Project Python is missing. Run bash scripts/setup.sh.\n'; exit 1; }
export PYTHONPATH="$(pwd)/backend"
.venv/bin/python - <<'PY'
import sys,os,json,importlib.metadata
from pathlib import Path
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 executable=p.chromium.executable_path
 print(json.dumps({'python':sys.executable,'pythonVersion':sys.version.split()[0],
  'playwrightVersion':importlib.metadata.version('playwright'),'browserChannel':'chromium',
  'chromiumExecutable':executable,'binaryExists':Path(executable).exists(),
  'browserCache':os.getenv('PLAYWRIGHT_BROWSERS_PATH','user default'),
  'uid':os.getuid() if hasattr(os,'getuid') else None},indent=2))
PY
if [[ "${1:-}" != "--environment-only" ]]; then
 .venv/bin/python scripts/check_browser.py
fi
