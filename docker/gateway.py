"""No website content API; only the validated outbound proxy and test canary."""
import asyncio
import os
from pathlib import Path
from app.proxy import EgressProxy
from app.security import NetworkPolicy


async def main():
    proxy=EgressProxy(NetworkPolicy(mode='public'))
    proxy.username='veyra'
    proxy.password=Path('/run/secrets/proxy_password').read_text().strip()
    import base64
    proxy.credentials=base64.b64encode(f'veyra:{proxy.password}'.encode()).decode()
    # Container network only; no host port is published.
    proxy.server=await asyncio.start_server(proxy._accept,'0.0.0.0',8888,limit=16384)
    async def canary(reader,writer):
        writer.write(b'network-canary');await writer.drain();writer.close();await writer.wait_closed()
    canary_server=await asyncio.start_server(canary,'0.0.0.0',9999)
    try:await asyncio.Event().wait()
    finally:canary_server.close();await canary_server.wait_closed();await proxy.stop()


asyncio.run(main())
