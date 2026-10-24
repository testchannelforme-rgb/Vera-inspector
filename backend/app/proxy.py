"""Small local egress gate: validate every destination, then connect to a vetted IP.

TLS stays end-to-end. This closes the resolver/connection rebinding gap on HTTP
proxy traffic, but is still not a host firewall. Keep the exact public allowlist.
"""
import asyncio
import base64
from contextlib import suppress
import ipaddress
import secrets
import socket
from urllib.parse import urlsplit
from .security import PolicyError


class EgressProxy:
    def __init__(self, policy, max_connections=48):
        self.policy = policy
        self.server = None
        self.username = 'veyra'
        self.password = secrets.token_urlsafe(32)
        self.tasks = set()
        self.max_connections = max_connections
        self.credentials = base64.b64encode(f'{self.username}:{self.password}'.encode()).decode()

    async def start(self):
        self.server = await asyncio.start_server(self._accept, '127.0.0.1', 0, limit=16384)

    @property
    def config(self):
        return {'server': f'http://127.0.0.1:{self.server.sockets[0].getsockname()[1]}',
                'username': self.username, 'password': self.password}

    async def resolve(self, url):
        # Policy checks ALL DNS answers. The second lookup is also validated;
        # the returned numeric address is used directly for the connection.
        normalized = await self.policy.validate(url)
        p = urlsplit(normalized)
        port = p.port if p.port is not None else (443 if p.scheme == 'https' else 80)
        records = await asyncio.wait_for(asyncio.get_running_loop().getaddrinfo(p.hostname, port, type=socket.SOCK_STREAM), 3)
        if not records:
            raise PolicyError('No destination addresses.')
        for record in records:
            self.policy.check_ip(record[4][0])
        return normalized, str(ipaddress.ip_address(sorted(records,key=lambda r:r[0]!=socket.AF_INET)[0][4][0])), port

    async def _accept(self, reader, writer):
        task = asyncio.current_task()
        if len(self.tasks) >= self.max_connections:
            writer.close();await writer.wait_closed();return
        self.tasks.add(task)
        upstream = None
        try:
            async with asyncio.timeout(90):
                header = await reader.readuntil(b'\r\n\r\n')
                if len(header)>16384:
                    raise ValueError('Header too large')
                lines = header.decode('latin1').split('\r\n')
                method, target, version = lines[0].split(' ')
                headers = dict(line.split(':',1) for line in lines[1:] if ':' in line)
                headers = {k.lower():v.strip() for k,v in headers.items()}
                if not secrets.compare_digest(headers.get('proxy-authorization',''), 'Basic '+self.credentials):
                    writer.write(b'HTTP/1.1 407 Proxy Authentication Required\r\nProxy-Authenticate: Basic realm="Veyra"\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
                    await writer.drain();return
                if method=='CONNECT':
                    if '/' in target or '@' in target or any(c.isspace() for c in target):
                        raise PolicyError('Invalid tunnel authority')
                    url='https://'+target+'/'
                elif method in ('GET','HEAD'):
                    url=target
                    if urlsplit(url).scheme != 'http':raise PolicyError('Expected absolute HTTP request')
                else:
                    raise PolicyError('Unsupported proxy method')
                normalized, address, port = await self.resolve(url)
                upstream_reader, upstream = await asyncio.wait_for(asyncio.open_connection(address,port),5)
                if method=='CONNECT':
                    writer.write(b'HTTP/1.1 200 Connection Established\r\n\r\n');await writer.drain()
                else:
                    p=urlsplit(normalized)
                    path=p.path or '/'
                    if p.query:path+='?'+p.query
                    forwarded=[f'{method} {path} HTTP/1.1',f'Host: {p.netloc}', 'Connection: close']
                    # Discard hop-by-hop and body-related headers. No request body is forwarded.
                    excluded={'host','connection','proxy-authorization','proxy-connection','content-length','transfer-encoding','upgrade','te','trailer','keep-alive'}
                    forwarded += [f'{k}: {v}' for k,v in headers.items() if k not in excluded]
                    upstream.write(('\r\n'.join(forwarded)+'\r\n\r\n').encode('latin1'));await upstream.drain()
                remaining=[24*1024*1024]
                async def relay(source,destination):
                    while remaining[0]>0:
                        chunk=await asyncio.wait_for(source.read(min(65536,remaining[0])),10)
                        if not chunk:return
                        remaining[0]-=len(chunk)
                        destination.write(chunk);await destination.drain()
                pumps={asyncio.create_task(relay(upstream_reader,writer)),asyncio.create_task(relay(reader,upstream))}
                try:
                    await asyncio.wait(pumps,return_when=asyncio.FIRST_COMPLETED)
                finally:
                    for pump in pumps:pump.cancel()
                    await asyncio.gather(*pumps,return_exceptions=True)
        except (PolicyError,ValueError,OSError,TimeoutError,asyncio.IncompleteReadError,asyncio.LimitOverrunError):
            with suppress(Exception):
                writer.write(b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n');await writer.drain()
        finally:
            if upstream:
                upstream.close()
                with suppress(Exception):await upstream.wait_closed()
            writer.close()
            with suppress(Exception):await writer.wait_closed()
            self.tasks.discard(task)

    async def stop(self):
        if self.server:
            self.server.close();await self.server.wait_closed()
            self.server=None
        for task in list(self.tasks):task.cancel()
        await asyncio.gather(*list(self.tasks),return_exceptions=True)
