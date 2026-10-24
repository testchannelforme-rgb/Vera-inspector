from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.browser_manager import BrowserManager, Session, SessionError
from app.config import Settings
from app.main import create_app
from app.schemas import OpenRequest, PointRequest


@pytest.fixture
def client():
    manager=BrowserManager(Settings())
    # Only HTTP error handling is tested here. Real browser tests live separately.
    manager.start=AsyncMock()
    manager.stop=AsyncMock()
    with TestClient(create_app(manager=manager)) as client:
        yield client


def test_backend_health(client):
    response=client.get('/api/health')
    assert response.status_code==200
    assert response.json()['status']=='browser-unavailable'


def test_api_unsafe_url(client):
    r=client.post('/api/sessions',json={'url':'http://127.0.0.1'},headers={'X-Veyra-Client':'inspector-v0.1'})
    assert r.status_code==400
    assert '/etc' not in r.text


def test_missing_session(client):
    r=client.post('/api/sessions/missing/select',json={'frameId':'x','x':1,'y':1},headers={'X-Veyra-Client':'inspector-v0.1'})
    assert r.status_code==404


def test_request_csrf_and_origin(client):
    assert client.post('/api/sessions',json={'url':'https://example.com'}).status_code==403
    assert client.post('/api/sessions',json={'url':'https://example.com'},headers={'X-Veyra-Client':'inspector-v0.1','Origin':'https://evil.test'}).status_code==403


def test_request_size(client):
    assert client.post('/api/sessions',content='x'*9000,headers={'X-Veyra-Client':'inspector-v0.1'}).status_code==413


def test_request_validation(client):
    r=client.post('/api/sessions',json={'url':'https://example.com','viewport':{'width':9999,'height':800}},headers={'X-Veyra-Client':'inspector-v0.1'})
    assert r.status_code==422
    with pytest.raises(ValidationError):PointRequest(frameId='x',x=float('nan'),y=2)
    with pytest.raises(ValidationError):OpenRequest(url='https://example.com',fake=1)


def test_stale_frame_and_outside_point():
    page=type('Page',(),{'viewport_size':{'width':1280,'height':800}})()
    session=Session('token',None,page,frame_id='current')
    session.check_frame('current');session.check_point(1279,799)
    with pytest.raises(SessionError):session.check_frame('old')
    with pytest.raises(SessionError):session.check_point(1280,800)


async def test_expiry_cleanup():
    manager=BrowserManager(Settings(session_ttl=1,idle_ttl=1))
    context=AsyncMock();session=Session('token',context,None,born=0,touched=0)
    manager.sessions['token']=session
    await manager.reap()
    assert manager.sessions=={}
    context.close.assert_awaited_once()


async def test_operation_lock_and_expired_session():
    manager=BrowserManager(Settings());s=Session('token',AsyncMock(),None)
    manager.sessions['token']=s
    await s.lock.acquire()
    with pytest.raises(SessionError,match='already running'):
        async with manager.operation('token'):pass
    s.lock.release();s.born=0
    with pytest.raises(SessionError,match='expired'):
        async with manager.operation('token'):pass
    await manager.close('token')


def test_request_length_formats(client):
    assert client.post('/api/sessions',content=b'{}',headers={'X-Veyra-Client':'inspector-v0.1','Content-Length':'bad'}).status_code==400
    assert client.post('/api/sessions',content=b'{}',headers={'X-Veyra-Client':'inspector-v0.1','Content-Length':'-1'}).status_code==400


def test_streamed_oversized_body(client):
    def chunks():
        yield b'x'*5000
        yield b'y'*5000
    assert client.post('/api/sessions',content=chunks(),headers={'X-Veyra-Client':'inspector-v0.1'}).status_code==413


def test_served_frontend_build(client):
    import re
    response=client.get('/')
    assert response.status_code==200 and '<title>Veyra Inspector</title>' in response.text
    for asset in re.findall(r'(?:src|href)="(/assets/[^"]+)"',response.text):
        assert client.get(asset).status_code==200
    assert response.headers['x-frame-options']=='DENY'


def test_codespaces_forwarded_origin():
    manager=BrowserManager(Settings());manager.start=AsyncMock();manager.stop=AsyncMock()
    settings=Settings(ui_origin='https://my-space-8000.app.github.dev')
    with TestClient(create_app(settings,manager)) as client:
        headers={'Origin':settings.ui_origin,'X-Veyra-Client':'inspector-v0.1'}
        assert client.post('/api/sessions/missing/clear',headers=headers).status_code==404
        headers['Origin']='https://attacker.app.github.dev'
        assert client.post('/api/sessions/missing/clear',headers=headers).status_code==403


def test_automatic_codespaces_origin(monkeypatch):
    monkeypatch.delenv('VEYRA_UI_ORIGIN',raising=False)
    monkeypatch.setenv('CODESPACE_NAME','my-space')
    monkeypatch.setenv('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN','app.github.dev')
    assert Settings.from_env().ui_origin=='https://my-space-8000.app.github.dev'
