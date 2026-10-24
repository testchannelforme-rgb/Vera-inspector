"""Fail-closed, exact-host public network policy. Not an egress firewall."""
import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit


class PolicyError(ValueError):
    pass


class NetworkPolicy:
    def __init__(self, hosts: set[str]):
        self.hosts = frozenset(h.strip().lower().encode('idna').decode('ascii') for h in hosts if h.strip())
        if not self.hosts or '*' in self.hosts:
            raise ValueError('An explicit, non-wildcard host allowlist is required.')

    def parse(self, url: str) -> tuple[str, str, int]:
        if len(url) > 2048 or any(ord(c) < 33 for c in url) or '\\' in url:
            raise PolicyError('URL contains unsupported characters or is too long.')
        try:
            p = urlsplit(url)
            if p.scheme not in ('http', 'https') or not p.hostname or p.username is not None or p.password is not None:
                raise ValueError()
            host = p.hostname.encode('idna').decode('ascii').lower()
            port = p.port if p.port is not None else (443 if p.scheme == 'https' else 80)
            # No unusual ports, ambiguous numeric forms, trailing dot or IPv6 zone IDs.
            if port not in (80, 443) or host.endswith('.') or '%' in host:
                raise ValueError()
        except (ValueError, UnicodeError):
            raise PolicyError('Use a valid public HTTP(S) URL on port 80 or 443.') from None
        if host == 'localhost' or host.endswith(('.localhost', '.local', '.internal')):
            raise PolicyError('Local and internal destinations are blocked.')
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass  # A DNS name, rather than an IP literal.
        else:
            self.check_ip(host)
        if host not in self.hosts:
            raise PolicyError('Host is not in the controlled allowlist. Review README before adding a host.')
        return urlunsplit((p.scheme, p.netloc, p.path or '/', p.query, '')), host, port

    @staticmethod
    def check_ip(address: str):
        ip = ipaddress.ip_address(address)
        # Mapped IPv4 must be checked as IPv4 as well.
        effective = ip.ipv4_mapped if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped else ip
        if not effective.is_global or effective.is_multicast or effective.is_unspecified:
            raise PolicyError('Private, reserved, loopback and metadata destinations are blocked.')

    async def validate(self, url: str) -> str:
        normalized, host, port = self.parse(url)
        try:
            records = await asyncio.wait_for(
                asyncio.get_running_loop().getaddrinfo(host, port, type=socket.SOCK_STREAM), 3)
        except (TimeoutError, OSError):
            raise PolicyError('Public DNS lookup failed or timed out.') from None
        if not records:
            raise PolicyError('DNS returned no addresses.')
        for record in records:
            self.check_ip(record[4][0])  # Reject mixed public/private DNS responses too.
        return normalized
