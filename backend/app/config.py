from dataclasses import dataclass
import os
from pathlib import Path
import json
import hashlib
import hmac
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Settings:
    allowed_hosts: frozenset[str] = frozenset({'example.com','www.example.com'})
    network_mode: str = 'restricted'
    browser_endpoint: str | None = None
    proxy_server: str | None = None
    proxy_password: str | None = None
    isolation_proof_file: str | None = None
    ui_origin: str | None = None
    max_sessions: int = 2
    session_ttl: int = 600
    idle_ttl: int = 180
    navigation_timeout_ms: int = 20000
    render_wait_ms: int = 5000
    max_requests: int = 600

    @classmethod
    def from_env(cls):
        origin=os.getenv('VEYRA_UI_ORIGIN')
        name=os.getenv('CODESPACE_NAME');domain=os.getenv('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN')
        if not origin and name and domain:origin=f'https://{name}-8000.{domain}'
        mode=os.getenv('VEYRA_NETWORK_MODE','restricted')
        if mode not in ('restricted','isolated-public'):
            raise ValueError('VEYRA_NETWORK_MODE must be restricted or isolated-public.')
        token_path=os.getenv('VEYRA_CONTROL_TOKEN_FILE')
        proxy_path=os.getenv('VEYRA_PROXY_PASSWORD_FILE')
        try:token=Path(token_path).read_text().strip() if token_path else None
        except OSError:token=None
        try:password=Path(proxy_path).read_text().strip() if proxy_path else None
        except OSError:password=None
        endpoint=f'ws://browser:3000/{token}' if token else None
        return cls(allowed_hosts=frozenset(os.getenv('VEYRA_ALLOWED_HOSTS','example.com,www.example.com').split(',')),
                   network_mode=mode,browser_endpoint=endpoint,isolation_proof_file=os.getenv('VEYRA_ISOLATION_PROOF_FILE'),proxy_server=os.getenv('VEYRA_PROXY_SERVER'),proxy_password=password,ui_origin=origin)

    def validate_isolation(self):
        if self.network_mode not in ('restricted','isolated-public'):raise ValueError('Unsupported network mode.')
        if self.network_mode=='isolated-public' and not (self.browser_endpoint and self.proxy_server and self.proxy_password):
            raise ValueError('Public mode requires the isolated Compose browser and egress gateway. Start with bash start.sh --isolated; local unrestricted browsing is disabled.')

        if self.network_mode=='isolated-public':
            try:
                proof=json.loads(Path(self.isolation_proof_file or '').read_text())
                token=self.browser_endpoint.rsplit('/',1)[1]
                valid=(proof['sandboxEnabled'] is True and proof['firewall']['proxyIp']=='172.30.88.2'
                       and proof['firewall']['ipv4']=='OUTPUT DROP; established + gateway:8888 only'
                       and proof['firewall']['ipv6']=='OUTPUT DROP; established only'
                       and hmac.compare_digest(proof['tokenHash'],hashlib.sha256(token.encode()).hexdigest())
                       and self.proxy_server=='http://172.30.88.2:8888'
                       and urlsplit(self.browser_endpoint).hostname=='browser')
                if not valid:raise ValueError()
            except (OSError,ValueError,KeyError,TypeError):
                raise ValueError('Isolated browser firewall/sandbox readiness proof is missing or mismatched. Restart the supplied Compose stack.') from None
