#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ "${1:-}" == "--isolated" ]]; then exec bash scripts/start-isolated.sh; fi
if [[ ! -x .venv/bin/python || ! -d frontend/node_modules || ! -f frontend/dist/index.html ]]; then
  bash scripts/setup.sh
fi
# One same-origin app; only this port needs forwarding. No secrets or paid APIs.
export PYTHONPATH="$(pwd)/backend${PYTHONPATH:+:$PYTHONPATH}"
printf '\nOpen port 8000 in your Codespaces Ports tab. Keep its visibility Private.\n'
exec .venv/bin/python -m uvicorn app.main:app --host "${VEYRA_BIND_HOST:-127.0.0.1}" --port 8000 --workers 1 --no-proxy-headers --no-access-log --timeout-keep-alive 5 --limit-concurrency 24
