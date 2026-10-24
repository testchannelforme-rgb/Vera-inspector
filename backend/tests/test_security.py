import asyncio
import socket
import pytest
from app.security import NetworkPolicy, PolicyError


@pytest.mark.parametrize('url',[
    'file:///etc/passwd','ftp://example.com/a','javascript:alert(1)','data:text/html,Hi',
    'http://localhost','http://a.localhost','http://internal.local',
    'http://127.0.0.1','http://127.1','http://2130706433','http://0x7f000001',
    'http://10.1.2.3','http://172.16.0.1','http://192.168.1.1','http://169.254.169.254',
    'http://[::1]','http://[::ffff:127.0.0.1]','http://[fe80::1%25eth0]',
    'http://100.100.100.200','https://example.com.evil.test','https://example.com.',
    'http://example.com:8000','https://u:p@example.com','https://example.com\\@evil.test',
    'https://example.com/a\nb','https://example.com:bad','https://example.com:0',
])
async def test_reject_unsafe_urls(url):
    with pytest.raises(PolicyError):
        await NetworkPolicy({'example.com','127.0.0.1','::1','169.254.169.254'}).validate(url)


def test_valid_parse_and_remove_fragment():
    assert NetworkPolicy({'example.com'}).parse('https://example.com/a?q=1#x')==('https://example.com/a?q=1','example.com',443)


def test_wildcard_and_empty_allowlist_rejected():
    for hosts in [set(),{'*'}]:
        with pytest.raises(ValueError):NetworkPolicy(hosts)


async def test_validate_all_dns_records(monkeypatch):
    async def lookup(*a,**kw):
        return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.216.34',443)),(socket.AF_INET,socket.SOCK_STREAM,6,'',('10.0.0.1',443))]
    monkeypatch.setattr(asyncio.get_running_loop(),'getaddrinfo',lookup)
    with pytest.raises(PolicyError):await NetworkPolicy({'example.com'}).validate('https://example.com')


async def test_public_dns_accepted(monkeypatch):
    async def lookup(*a,**kw):return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.216.34',443))]
    monkeypatch.setattr(asyncio.get_running_loop(),'getaddrinfo',lookup)
    assert await NetworkPolicy({'example.com'}).validate('https://example.com')=='https://example.com/'


async def test_dns_failure_closed(monkeypatch):
    async def lookup(*a,**kw):raise OSError('private resolver details')
    monkeypatch.setattr(asyncio.get_running_loop(),'getaddrinfo',lookup)
    with pytest.raises(PolicyError,match='DNS lookup failed'):await NetworkPolicy({'example.com'}).validate('https://example.com')
