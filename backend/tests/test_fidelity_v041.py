import json
import os
from pathlib import Path
import subprocess
import types
from unittest.mock import AsyncMock
import pytest
from app.studio.local import reconstruct
from app.studio.service import StudioService
from app.studio.schemas import GenerateRequest
from app.studio.specification import specification
from app.studio.comparison import capture_reference,Comparator
from app.studio.assets import embed_assets
from app.prompts.evidence import collect_evidence
from app.prompts.schemas import PromptRequest
from app.inspector import inspect_element
from test_studio import evidence,provider
from test_studio_browser import source_app

async def test_repair_accepts_only_valid_lower_loss_and_uses_original_on_failure():
    s=StudioService(db=':memory:');s.repairer=provider()
    p,_=reconstruct(evidence(),'vanilla');s.repairer.generate.return_value=({'files':{'style.css':p.files['style.css']+'\nbutton{color:red}'},'summary':'Repair'}, {})
    s.comparator=AsyncMock();s.comparator.render.side_effect=[{'available':True,'loss':50,'missingNodes':0},{'available':True,'loss':10,'missingNodes':0,'runtimeErrors':[]}]
    r=await s.generate(evidence(),GenerateRequest(sessionId='s',frameId='f',autoRepair=True,consent=True),reference={})
    # Empty references are unavailable, so ensure an explicit captured reference is supplied.
    s.comparator.render.side_effect=[{'available':True,'loss':50,'missingNodes':0},{'available':True,'loss':10,'missingNodes':0,'runtimeErrors':[]}]
    r=await s.generate(evidence(),GenerateRequest(sessionId='s',frameId='f',autoRepair=True,consent=True),reference={'captured':True})
    assert r['repair']['accepted'] and r['repair']['attempts']==1
    s.comparator.render.side_effect=[{'available':True,'loss':10,'missingNodes':0},{'available':True,'loss':80,'missingNodes':0,'runtimeErrors':[]}]
    r=await s.generate(evidence(),GenerateRequest(sessionId='s',frameId='f',autoRepair=True,consent=True),reference={'captured':True})
    assert not r['repair']['accepted'] and not r['project']['files']['style.css'].endswith('button{color:red}')

def test_specification_and_brand_separation():
    e=evidence();spec=specification(e,'react')
    assert spec['schema']=='veyra-reconstruction/2' and spec['nodes']==e['nodes']
    p,_=reconstruct(e,'react');assert 'rgb(20, 80, 30)' in p.files['style.css']
    assert '#A8B89A' not in p.files['style.css']
    css=Path('frontend/src/theme.css').read_text();assert '#2E3138' in css and '#A8B89A' in css

@pytest.mark.parametrize('fmt',['vanilla','react'])
async def test_measured_baseline_comparison(fixture_site,monkeypatch,fmt):
    if not os.getenv('STUDIO_TEST_CHROMIUM'):pytest.skip('Offline browser runner not configured')
    legacy=types.ModuleType('app.studio.legacy');legacy.__package__='app.studio'
    exec(subprocess.check_output(['git','show','1c885d0:backend/app/studio/local.py']).decode(),legacy.__dict__)
    reports=[]
    async with source_app(fixture_site,monkeypatch) as (_,manager,_):
        session,_=await manager.create(fixture_site+'/fidelity.html',{'width':900,'height':1600})
        comparator=Comparator(manager)
        for ident in ['nav','hero','grid','responsive','motion']:
            session.element=await session.page.query_selector('#'+ident);session.reference_id='selected'
            e=await collect_evidence(session,PromptRequest(sessionId=session.token,frameId=session.frame_id,referenceId='selected'))
            await embed_assets(session,e)
            ref=await capture_reference(session,e)
            old,_=legacy.reconstruct(e,fmt);new,_=reconstruct(e,fmt)
            a=await comparator.render(old,ref);b=await comparator.render(new,ref)
            assert a['available'] and b['available'],(a,b)
            assert not b['runtimeErrors'],b
            reports.append({'fixture':ident,'format':fmt,'baseline':a,'updated':b})
        # Same inputs: improvements must be real measurements, not an invented percentage.
        assert sum(r['updated']['loss'] for r in reports)<sum(r['baseline']['loss'] for r in reports),reports
    directory=Path(os.getenv('VEYRA_FIDELITY_REPORT_DIR','artifacts/generated/v041'));directory.mkdir(parents=True,exist_ok=True)
    (directory/(fmt+'.json')).write_text(json.dumps(reports,indent=2))

async def test_real_render_repair_and_brand(fixture_site,monkeypatch):
    if not os.getenv('STUDIO_TEST_CHROMIUM'):pytest.skip('Offline browser runner not configured')
    async with source_app(fixture_site,monkeypatch) as (base,manager,_):
        session,_=await manager.create(fixture_site+'/fidelity.html',{'width':900,'height':1600})
        session.element=await session.page.query_selector('#nav');session.reference_id='selected'
        e=await collect_evidence(session,PromptRequest(sessionId=session.token,frameId=session.frame_id,referenceId='selected'))
        ref=await capture_reference(session,e);original,_=reconstruct(e,'vanilla')
        model=provider();model.generate.return_value=({'files':{'style.css':original.files['style.css']+'\nheader{background:white !important}'},'summary':'Injected imperfect model fixture'}, {})
        service=StudioService(db=':memory:',provider=model);service.comparator=Comparator(manager)
        service.repairer=provider();service.repairer.generate.return_value=({'files':{'style.css':original.files['style.css']},'summary':'Injected measured repair fixture'}, {})
        result=await service.generate(e,GenerateRequest(sessionId=session.token,frameId=session.frame_id,mode='auto',consent=True,autoRepair=True),ref)
        assert result['repair']['accepted'] and result['repair']['after']['loss']<result['repair']['before']['loss']
        context=await manager.browser.new_context();page=await context.new_page();await page.goto(base)
        primary=page.locator('.primary').first
        assert await primary.evaluate('e=>getComputedStyle(e).backgroundColor')=='rgb(168, 184, 154)'
        assert await page.evaluate('getComputedStyle(document.documentElement).backgroundColor')=='rgb(46, 49, 56)'
        if os.getenv('STUDIO_SHOTS_DIR'):
            await page.screenshot(path=os.environ['STUDIO_SHOTS_DIR']+'/v041-brand.png',full_page=True)
        await context.close()

async def test_asset_mapping_rejects_page_fabricated_markup():
    e=evidence();e['nodes'][1].update(tag='img',box={'x':0,'y':0,'width':10,'height':10})
    session=AsyncMock();session.page.evaluate.return_value={'1':'data:image/png;base64,abc" onerror="evil()'}
    await embed_assets(session,e);assert 'embeddedAsset' not in e['nodes'][1]

def test_inline_style_survives_safe_preview_without_asset_urls():
    from app.studio.preview import SafeMarkup
    p=SafeMarkup();p.feed('<div style="color:rgb(1, 2, 3);padding:12px;background-image:url(https://evil.test/x)">Hi</div>')
    html=''.join(p.parts);assert 'padding: 12px' in html and 'evil.test' not in html

def test_code_model_token_budget_is_separate(monkeypatch):
    from app.studio.provider import task_config
    monkeypatch.setenv('VEYRA_CODE_AI_MAX_OUTPUT_TOKENS','8192')
    assert task_config('code').max_tokens==8192
    monkeypatch.setenv('VEYRA_CODE_AI_MAX_OUTPUT_TOKENS','999999')
    assert not task_config('code').available
