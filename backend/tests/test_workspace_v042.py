from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.main import create_app
from app.browser_manager import BrowserManager,Session
from app.config import Settings
from app.studio.schemas import GenerateRequest
from app.studio.service import StudioService
from app.studio.local import reconstruct
from test_studio import evidence

@pytest.fixture
def client(monkeypatch):
 manager=BrowserManager(Settings());manager.start=AsyncMock();manager.stop=AsyncMock()
 page=AsyncMock();manager.sessions['s']=Session('s',AsyncMock(),page,frame_id='f')
 async def collect(session,body):return evidence()
 monkeypatch.setattr('app.main.collect_evidence',collect)
 monkeypatch.setattr('app.studio.comparison.capture_reference',AsyncMock(return_value=None))
 # create_app resolves this function on construction, so patch before creating it.
 service=StudioService(db=':memory:')
 with TestClient(create_app(manager=manager,studio_service=service)) as c:yield c,manager,service

H={'X-Veyra-Client':'inspector-v0.1'}
def test_progress_records_only_actual_pipeline_stages_and_is_bounded(client):
 c,manager,s=client;ident='a'*32
 r=c.post('/api/studio/generate',headers=H,json={'sessionId':'s','frameId':'f','requestId':ident})
 assert r.status_code==200,r.text
 assert [e['stage'] for e in c.get('/api/studio/progress/'+ident).json()['events']]==['Inspecting','Analyzing','Generating','Validating','Complete']
 assert c.get('/api/studio/progress/'+'b'*32).json()=={'events':[]}
 for i in range(40):s.stage(str(i),'Inspecting')
 assert len(s.progress)<=32
 with pytest.raises(ValidationError):GenerateRequest(sessionId='s',frameId='f',requestId='bad')

def test_resize_validates_limits_and_preserves_live_session(client):
 c,m,s=client
 r=c.post('/api/sessions/s/viewport',headers=H,json={'frameId':'f','viewport':{'width':2000,'height':800}})
 assert r.status_code==422
 m.sessions['s'].page.set_viewport_size.assert_not_called()
 assert c.post('/api/sessions/s/viewport',json={'frameId':'f','viewport':{'width':768,'height':900}}).status_code==403

async def test_bridge_token_is_unique_and_preview_stays_opaque():
 s=StudioService(db=':memory:');p,_=reconstruct(evidence(),'vanilla')
 a=await s.preview(p);b=await s.preview(p)
 assert a['bridgeToken']!=b['bridgeToken']
 doc=s.previews[a['url'].rsplit('/',1)[1]][1]
 assert a['bridgeToken'] in doc and b['bridgeToken'] not in doc
 assert 'e.source!==parent' in doc and 'veyra-preview-selected' in doc
 assert 'sandbox allow-scripts' in s.previews[a['url'].rsplit('/',1)[1]][2]
