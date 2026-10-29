#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ "${1:-}" == "--isolated" ]]; then exec bash scripts/start-isolated.sh; fi
port="${VEYRA_PORT:-8001}"
# A stale process must be identified, never silently killed or relabelled.
python3 - "$port" <<'PY'
import socket,sys
s=socket.socket()
try:s.bind(('127.0.0.1',int(sys.argv[1])))
except OSError:raise SystemExit('Port '+sys.argv[1]+' is occupied. Check its /api/health and stop the old Veyra process before restarting.')
finally:s.close()
PY
if [[ ! -x .venv/bin/python || ! -d frontend/node_modules ]]; then bash scripts/setup.sh; fi
# Always build checked-out sources. An old dist directory must not mask a new version.
npm --prefix frontend run build
export PYTHONPATH="$(pwd)/backend${PYTHONPATH:+:$PYTHONPATH}"
printf '\nVEYRA AI V0.4.0 · private forwarded port %s · commit %s\n' "$port" "$(git rev-parse --short HEAD)"
exec .venv/bin/python -m uvicorn app.main:app --host "${VEYRA_BIND_HOST:-127.0.0.1}" --port "$port" --workers 1 --no-proxy-headers --no-access-log --timeout-keep-alive 5 --limit-concurrency 24
