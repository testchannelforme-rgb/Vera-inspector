import asyncio
import hashlib
import json
from pathlib import Path
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from playwright.async_api import Error as PlaywrightError, TimeoutError as PlaywrightTimeout
from app.config import Settings
from app.security import NetworkPolicy, PolicyError, normalize_url
from app.diagnostics import PageDiagnostics, startup_diagnostic
from app.browser_manager import BrowserManager, Session, SessionError
from app.main import create_app
from app.rendering import settle_page


@pytest.mark.parametrize('raw,expected',[
 ('example.com','https://example.com/'),(' www.roblox.com ','https://www.roblox.com/'),
 ('wikipedia.org','https://wikipedia.org/'),('https://EXAMPLE.COM:443/a?q=1#here','https://example.com/a?q=1'),
 ('http://example.com','http://example.com/'),('example.com:443','https://example.com/'),
 ('example.com/a?b=1','https://example.com/a?b=1'),('https://example.com.','https://example.com/'),
 ('https://bücher.de/lesen','https://xn--bcher-kva.de/lesen'),
 ('https://[2606:4700:4700::1111]','https://[2606:4700:4700::1111]/')])
def test_smart_normalization(raw,expected):
    assert normalize_url(raw)==expected
    assert normalize_url(expected)==expected


@pytest.mark.parametrize('raw',[
 'hello world','hello','https://','//example.com','file:///etc/passwd','javascript:alert(1)','data:text/html,x',
 'ftp://example.com','https:example.com','https://u:p@example.com','example.com\\evil',
 'http://example.com:','http://example.com:0','https://example.com:9999','https://a..com',
 'https://-bad.com','http://[fe80::1%25eth0]', 'http://127.1','http://0177.0.0.1',
 'http://0x7f000001','http://2130706433','http://127.0.0.1','http://[::1]',
 'http://[::ffff:127.0.0.1]','http://[64:ff9b::7f00:1]','http://[2002:7f00:1::]',
 'http://[2001::1]','http://169.254.169.254','http://168.63.129.16','http://100.100.100.200',
 'http://10.0.0.1','http://172.16.0.1','http://192.168.1.1','http://224.0.0.1',
 'http://[ff02::1]','http://[fc00::1]','http://[2001:db8::1]','http://127。0。0。1',
 'https://metadata.google.internal','https://host.localdomain'])
def test_public_mode_rejects_unsafe_syntax_and_destinations(raw):
    with pytest.raises(PolicyError):NetworkPolicy(mode='public').parse(raw)


def test_public_policy_does_not_need_allowlist():
    for host in ['example.com','www.roblox.com','www.wikipedia.org','www.python.org']:
        assert NetworkPolicy(mode='public').parse(host)[1]==host


def test_local_public_launch_is_forbidden():
    settings=Settings(network_mode='isolated-public')
    with pytest.raises(ValueError,match='isolated Compose'):settings.validate_isolation()


def test_isolation_proof_and_token_must_match(tmp_path):
    token='f'*64
    proof={'sandboxEnabled':True,'firewall':{'proxyIp':'172.30.88.2','ipv4':'OUTPUT DROP; established + gateway:8888 only','ipv6':'OUTPUT DROP; established only'},'tokenHash':hashlib.sha256(token.encode()).hexdigest()}
    path=tmp_path/'proof.json';path.write_text(json.dumps(proof))
    settings=Settings(network_mode='isolated-public',browser_endpoint='ws://browser:3000/'+token,
        proxy_server='http://172.30.88.2:8888',proxy_password='test-only',isolation_proof_file=str(path))
    settings.validate_isolation()
    proof['sandboxEnabled']=False;path.write_text(json.dumps(proof))
    with pytest.raises(ValueError,match='proof'):settings.validate_isolation()


@pytest.mark.parametrize('error,category',[
 ('Executable doesn\'t exist at /cache/chrome','browser-binary-missing'),
 ('error while loading shared libraries: libnss3.so','browser-libraries-missing'),
 ('Running as root without --no-sandbox is not supported','browser-sandbox-unavailable'),
 ('connect ECONNREFUSED ws://browser:3000/super-secret','browser-service-unavailable')])
def test_startup_error_categories_and_redaction(error,category):
    d=startup_diagnostic(error)
    assert d['category']==category and d['sandboxEnabled']
    assert 'super-secret' not in d['message']


async def test_navigation_error_categories():
    manager=BrowserManager(Settings(render_wait_ms=0))
    manager.policy.validate=AsyncMock(return_value='https://example.com/')
    manager.browser=type('Browser',(),{'is_connected':lambda _:True})()
    page=AsyncMock();page.is_closed=lambda:False
    session=Session('test',AsyncMock(),page)
    for exc,code in [(PlaywrightTimeout('timeout'),'navigation-timeout'),(PlaywrightError('failed'),'website-inaccessible')]:
        page.goto.side_effect=exc
        with pytest.raises(SessionError) as caught:await manager.navigate(session,'https://example.com/')
        assert caught.value.code==code
    page.goto.side_effect=None;page.goto.return_value=type('Response',(),{'status':403})()
    with pytest.raises(SessionError) as caught:await manager.navigate(session,'https://example.com/')
    assert caught.value.code=='website-blocked-or-inaccessible'
    assert caught.value.diagnostics['httpStatus']==403


async def test_empty_page_is_reported_and_valid_page_is_not():
    for count,empty in [(0,True),(3,False)]:
        page=AsyncMock();page.evaluate.return_value={'hasBody':True,'visibleCandidates':count,'textLength':count*20,'readyState':'complete'}
        result=await settle_page(page,0)
        assert result['empty']==empty


async def test_screenshot_failure_has_own_category():
    page=AsyncMock();page.is_closed=lambda:False;page.screenshot.side_effect=PlaywrightError('failed')
    session=Session('test',None,page)
    with pytest.raises(SessionError) as caught:await session.screenshot_data()
    assert caught.value.code=='screenshot-failure'


def test_frontend_normalizes_using_same_endpoint():
    manager=BrowserManager(Settings());manager.start=AsyncMock();manager.stop=AsyncMock()
    with TestClient(create_app(manager=manager)) as client:
        headers={'X-Veyra-Client':'inspector-v0.1'}
        assert client.post('/api/normalize',json={'url':' www.roblox.com '},headers=headers).json()=={'url':'https://www.roblox.com/'}
        assert client.post('/api/normalize',json={'url':'not a website'},headers=headers).status_code==400
        assert client.post('/api/normalize',json={'url':123},headers=headers).status_code==422
        assert client.get('/api/health').json()['networkMode']=='restricted'


async def test_subresource_post_works_but_private_requests_fail():
    manager=BrowserManager(Settings())
    page=AsyncMock();session=Session('test',None,page)
    route=AsyncMock();route.request=type('Request',(),{'resource_type':'fetch','method':'POST','post_data_buffer':b'{"publicQuery":1}','url':'https://example.com/api'})()
    manager.policy.validate=AsyncMock(return_value=route.request.url)
    await manager._route(session,route)
    route.continue_.assert_awaited_once()
    manager.policy.validate=AsyncMock(side_effect=PolicyError('private blocked'))
    await manager._route(session,route)
    route.abort.assert_awaited_once()
    assert session.diagnostics.blocked


async def test_full_chromium_channel_and_sandbox_are_always_requested(monkeypatch):
    import app.browser_manager as module
    fake_browser=type('Browser',(),{'close':AsyncMock()})()
    launch=AsyncMock(return_value=fake_browser)
    driver=type('Driver',(),{'chromium':type('Chromium',(),{'launch':launch})(),'stop':AsyncMock()})()
    launcher=type('Launcher',(),{'start':AsyncMock(return_value=driver)})()
    monkeypatch.setattr(module,'async_playwright',lambda:launcher)
    manager=BrowserManager(Settings())
    await manager.start()
    kwargs=launch.await_args.kwargs
    assert kwargs['channel']=='chromium' and kwargs['chromium_sandbox'] is True
    assert '--no-sandbox' not in kwargs['args']
    await manager.stop()


def test_resource_http_errors_are_recorded_without_queries():
    from types import SimpleNamespace
    callbacks={}
    page=SimpleNamespace(on=lambda event,handler:callbacks.__setitem__(event,handler))
    d=PageDiagnostics();d.attach(page)
    callbacks['response'](SimpleNamespace(status=403,url='https://cdn.example.com/app.js?secret=hidden',request=SimpleNamespace(resource_type='script')))
    record=d.export()['resourceHttpErrors'][0]
    assert record=={'scheme':'https','host':'cdn.example.com','status':403,'resourceType':'script'}
    assert 'hidden' not in json.dumps(d.export())


async def test_unavailable_browser_is_reported_before_public_dns():
    manager=BrowserManager(Settings());manager.policy.validate=AsyncMock()
    with pytest.raises(SessionError) as caught:await manager.create('example.com',{'width':1280,'height':800})
    assert caught.value.code=='browser-engine-failure' and caught.value.status==503
    manager.policy.validate.assert_not_awaited()
