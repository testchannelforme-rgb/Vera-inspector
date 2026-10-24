import asyncio
from unittest.mock import AsyncMock
import pytest
from app.proxy import EgressProxy
from app.security import NetworkPolicy, PolicyError


async def test_proxy_second_lookup_rejects_rebinding(monkeypatch):
    policy=NetworkPolicy({'example.com'})
    policy.validate=AsyncMock(return_value='https://example.com/')
    proxy=EgressProxy(policy)
    async def lookup(*args,**kwargs):return [(2,1,6,'',('127.0.0.1',443))]
    monkeypatch.setattr(asyncio.get_running_loop(),'getaddrinfo',lookup)
    with pytest.raises(PolicyError):await proxy.resolve('https://example.com')


async def test_proxy_resolves_to_numeric_pinned_address(monkeypatch):
    policy=NetworkPolicy({'example.com'});policy.validate=AsyncMock(return_value='https://example.com/')
    proxy=EgressProxy(policy)
    async def lookup(*a,**kw):return [(2,1,6,'',('93.184.216.34',443))]
    monkeypatch.setattr(asyncio.get_running_loop(),'getaddrinfo',lookup)
    assert await proxy.resolve('https://example.com')==('https://example.com/','93.184.216.34',443)


async def send_proxy(proxy,request):
    port=proxy.server.sockets[0].getsockname()[1]
    reader,writer=await asyncio.open_connection('127.0.0.1',port)
    writer.write(request);await writer.drain()
    data=await asyncio.wait_for(reader.read(),2)
    writer.close();await writer.wait_closed()
    return data


async def test_proxy_auth_and_private_destinations():
    proxy=EgressProxy(NetworkPolicy({'example.com'}));await proxy.start()
    try:
        r=await send_proxy(proxy,b'CONNECT example.com:443 HTTP/1.1\r\n\r\n')
        assert r.startswith(b'HTTP/1.1 407')
        request=('CONNECT 127.0.0.1:443 HTTP/1.1\r\nProxy-Authorization: Basic '+proxy.credentials+'\r\n\r\n').encode()
        r=await send_proxy(proxy,request)
        assert r.startswith(b'HTTP/1.1 403')
        request=('POST http://example.com/ HTTP/1.1\r\nProxy-Authorization: Basic '+proxy.credentials+'\r\n\r\n').encode()
        assert (await send_proxy(proxy,request)).startswith(b'HTTP/1.1 403')
    finally:await proxy.stop()
    assert not proxy.tasks and proxy.server is None


async def test_proxy_relays_fixture_http_and_connect(fixture_site):
    proxy=EgressProxy(NetworkPolicy({'example.com'}))
    port=int(fixture_site.rsplit(':',1)[1])
    # Only the unit-test proxy gets this exact local fixture exception.
    async def resolve(url):
        assert url.startswith(fixture_site+'/') or url==fixture_site.replace('http:','https:')+'/'
        return url,'127.0.0.1',port
    proxy.resolve=resolve
    await proxy.start()
    try:
        request=(f'GET {fixture_site}/ HTTP/1.1\r\nHost: ignored\r\nProxy-Authorization: Basic {proxy.credentials}\r\n\r\n').encode()
        response=await send_proxy(proxy,request)
        assert b'200 OK' in response and b'Inspect this card' in response
        reader,writer=await asyncio.open_connection('127.0.0.1',proxy.server.sockets[0].getsockname()[1])
        writer.write((f'CONNECT 127.0.0.1:{port} HTTP/1.1\r\nProxy-Authorization: Basic {proxy.credentials}\r\n\r\n').encode());await writer.drain()
        assert (await reader.readuntil(b'\r\n\r\n')).startswith(b'HTTP/1.1 200')
        writer.write(b'GET / HTTP/1.0\r\n\r\n');await writer.drain()
        assert b'Inspect this card' in await asyncio.wait_for(reader.read(),2)
        writer.close();await writer.wait_closed()
    finally:await proxy.stop()
