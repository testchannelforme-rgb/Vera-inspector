"""Canonical public destinations. A validating proxy is not an OS egress boundary."""
import asyncio
import ipaddress
import re
import socket
from urllib.parse import urlsplit, urlunsplit, quote


class PolicyError(ValueError):
    pass


DENIED_V6 = tuple(ipaddress.ip_network(n) for n in ('2002::/16','2001::/32','64:ff9b::/96','64:ff9b:1::/48'))
DENIED_V4 = tuple(ipaddress.ip_network(n) for n in ('192.0.0.0/24','192.88.99.0/24','168.63.129.16/32'))
LABEL = re.compile(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z')


def check_public_ip(address: str):
    ip = ipaddress.ip_address(address)
    effective = ip.ipv4_mapped if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped else ip
    denied = DENIED_V4 if effective.version == 4 else DENIED_V6
    if (not effective.is_global or effective.is_reserved or effective.is_multicast
            or effective.is_unspecified or any(effective in block for block in denied)):
        raise PolicyError('Private, loopback, reserved, link-local and metadata destinations are blocked.')


def normalize_url(raw: str) -> str:
    """One authoritative normalizer, also exposed to the frontend via /api/normalize.

    Reject WHATWG alternate IPv4 notation rather than letting Python/Chromium
    disagree about hexadecimal, octal, shortened or integer address forms.
    """
    url = raw.strip()
    if not url or len(url)>2048 or any(c.isspace() or ord(c)<33 or ord(c)==127 for c in url) or '\\' in url:
        raise PolicyError('Enter a website address without spaces, control characters or backslashes.')
    if url.startswith('//'):
        raise PolicyError('Use a hostname or a complete HTTP(S) URL.')
    if '://' not in url:
        # A bare host with a numeric port is allowed, arbitrary scheme:text is not.
        bare_port = re.match(r'^[^/:?#]+:\d+(?:[/?#]|$)',url)
        if ':' in url.split('/')[0].split('?')[0].split('#')[0] and not bare_port and not url.startswith('['):
            raise PolicyError('Only HTTP and HTTPS website addresses are supported.')
        url = 'https://'+url
    try:
        p = urlsplit(url)
        if p.scheme.lower() not in ('http','https') or not p.hostname or p.username is not None or p.password is not None:
            raise ValueError()
        if p.hostname.endswith('..'):raise ValueError()
        host = p.hostname.encode('idna').decode('ascii').lower().rstrip('.')
        if not host or '%' in host:raise ValueError()
        port = p.port if p.port is not None else (443 if p.scheme.lower()=='https' else 80)
        if port not in (80,443):raise ValueError()
    except (ValueError,UnicodeError):
        raise PolicyError('Use a valid HTTP(S) website address on port 80 or 443, without credentials.') from None
    if host=='localhost' or host.endswith(('.localhost','.local','.localdomain','.internal','.lan','.home.arpa')):
        raise PolicyError('Local and internal destinations are blocked.')
    try:
        ip=ipaddress.ip_address(host)
    except ValueError:
        labels=host.split('.')
        if len(labels)<2 or len(host)>253 or not all(LABEL.fullmatch(label) for label in labels):
            raise PolicyError('Enter a valid public hostname, such as example.com.')
        if labels[-1].isdigit() or re.fullmatch(r'0x[0-9a-f]+',labels[-1]):
            raise PolicyError('Alternate numeric IP representations are not supported. Use a canonical public address.')
    else:
        check_public_ip(str(ip))
        host=ip.compressed
    # urlsplit may accept a trailing ':' as an empty port; reject this ambiguity.
    if p.netloc.endswith(':'):raise PolicyError('A URL port must be numeric.')
    authority=f'[{host}]' if ':' in host else host
    default_port=443 if p.scheme.lower()=='https' else 80
    if port!=default_port:authority+=f':{port}'
    path=quote(p.path or '/',safe="/%:@!$&'()*+,;=-._~")
    query=quote(p.query,safe="%/?@:!$&'()*+,;=-._~")
    return urlunsplit((p.scheme.lower(),authority,path,query,''))


class NetworkPolicy:
    def __init__(self, hosts=None, *, mode='restricted'):
        if mode not in ('restricted','public'):raise ValueError('Unknown network policy mode.')
        self.mode=mode
        self.hosts=frozenset(h.strip().lower().encode('idna').decode('ascii').rstrip('.') for h in (hosts or []) if h.strip())
        if '*' in self.hosts or (mode=='restricted' and not self.hosts):
            raise ValueError('Restricted mode requires explicit non-wildcard hosts.')

    def parse(self,url):
        normalized=normalize_url(url)
        p=urlsplit(normalized)
        if self.mode=='restricted' and p.hostname not in self.hosts:
            raise PolicyError('Host is not in the restricted development allowlist. Use the isolated public mode for other public sites.')
        return normalized,p.hostname,p.port or (443 if p.scheme=='https' else 80)

    check_ip=staticmethod(check_public_ip)

    async def validate(self,url):
        normalized,host,port=self.parse(url)
        try:
            records=await asyncio.wait_for(asyncio.get_running_loop().getaddrinfo(host,port,type=socket.SOCK_STREAM),3)
        except (TimeoutError,OSError):
            raise PolicyError('Public DNS lookup failed or timed out.') from None
        if not records:raise PolicyError('DNS returned no addresses.')
        for record in records:self.check_ip(record[4][0])
        return normalized
