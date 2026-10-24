from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    allowed_hosts: frozenset[str] = frozenset({'example.com', 'www.example.com'})
    ui_origin: str | None = None
    max_sessions: int = 2
    session_ttl: int = 600
    idle_ttl: int = 180
    navigation_timeout_ms: int = 15000
    max_requests: int = 250

    @classmethod
    def from_env(cls):
        origin = os.getenv('VEYRA_UI_ORIGIN')
        name = os.getenv('CODESPACE_NAME')
        domain = os.getenv('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN')
        if not origin and name and domain:
            origin = f'https://{name}-8000.{domain}'
        return cls(allowed_hosts=frozenset(os.getenv('VEYRA_ALLOWED_HOSTS', 'example.com,www.example.com').split(',')), ui_origin=origin)
