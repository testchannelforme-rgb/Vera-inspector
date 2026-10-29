#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v docker >/dev/null || { printf 'Docker is required for public mode. Local unrestricted browsing is disabled.\n'; exit 1; }
docker compose version >/dev/null
umask 077
mkdir -p .veyra-runtime
# Random capabilities never enter source control. Existing values survive restarts.
python3 - <<'PY'
from pathlib import Path
import secrets
for name in ['control_token','proxy_password']:
 p=Path('.veyra-runtime')/name
 if not p.exists():p.write_text(secrets.token_hex(32))
 p.chmod(0o444)  # Bind-mounted Compose secrets must be readable by isolated service UIDs.
PY
if [[ -z "${VEYRA_UI_ORIGIN:-}" && -n "${CODESPACE_NAME:-}" && -n "${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-}" ]]; then
 export VEYRA_UI_ORIGIN="https://${CODESPACE_NAME}-8001.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
fi
export VEYRA_BUILD_REVISION="$(git rev-parse HEAD)"
docker compose -f compose.inspection.yml up --build -d --wait
# Failure leaves the app stopped, rather than running public mode on unverified rules.
if ! docker compose -f compose.inspection.yml exec -T --user pwuser browser node /opt/veyra-browser/probe-network.cjs; then
 docker compose -f compose.inspection.yml stop app browser
 printf 'Isolation verification failed. Public browsing has been stopped.\n'
 exit 1
fi
python3 - <<'PYREADY'
import urllib.request,json,time
base='http://127.0.0.1:8001/api'
for _ in range(30):
 try:
  with urllib.request.urlopen(base+'/health',timeout=2) as response:health=json.load(response)
  break
 except Exception:time.sleep(.5)
else:raise SystemExit('Veyra API did not become ready. Check Compose logs.')
if health['status']!='ready':
 request=urllib.request.Request(base+'/browser/retry',method='POST',headers={'X-Veyra-Client':'inspector-v0.1'})
 with urllib.request.urlopen(request,timeout=35) as response:health=json.load(response)
if health['status']!='ready':raise SystemExit('Browser is unavailable. No permissive fallback was enabled.')
if health.get('version')!='0.4.0':raise SystemExit('Wrong application version on port 8001. Check stale containers.')
print('VEYRA AI',health['version'],'commit',health.get('commit'),'browser readiness verified.')
PYREADY
printf 'Veyra is on private forwarded port 8001. Stop with: docker compose -f compose.inspection.yml stop\n'
