"""Real protected-Chromium pipeline checks; never substitute synthetic pixels."""
import json
import pytest
from app.prompts.evidence import collect_evidence
from app.prompts.schemas import PromptRequest
from app.prompts.service import PromptService
from app.prompts.provider import ProviderConfig


@pytest.mark.parametrize('scope',['element','section','page'])
async def test_browser_visual_evidence_to_prompt(browser_manager,fixture_site,scope):
    manager=browser_manager
    session,_=await manager.create(fixture_site+'/visual.html',{'width':1280,'height':800})
    session.element=await session.page.query_selector('#target');session.reference_id='visual-ref'
    request=PromptRequest(sessionId=session.token,frameId=session.frame_id,referenceId='visual-ref',scope=scope)
    evidence=await collect_evidence(session,request)
    result=await PromptService(ProviderConfig()).generate(evidence,request)
    assert result.mode=='fallback' and 'Visual Composition Summary' in result.prompt
    assert 'linear-gradient(' in result.prompt
    assert 'token=fixture-only' not in result.prompt
    assert 'not measured' in result.prompt
    if scope=='element':
        assert evidence['nodes'][0]['styles']['-webkit-text-fill-color'] in ('rgba(0, 0, 0, 0)','transparent')
        assert evidence.get('visualContext',{}).get('owners')
    await manager.close(session.token)


async def test_browser_mobile_visual_fixture(browser_manager,fixture_site):
    session,_=await browser_manager.create(fixture_site+'/visual.html',{'width':390,'height':844})
    session.element=await session.page.query_selector('#target');session.reference_id='mobile-visual'
    request=PromptRequest(sessionId=session.token,frameId=session.frame_id,referenceId=session.reference_id)
    evidence=await collect_evidence(session,request)
    assert evidence['viewport']['width']==390 and evidence['nodes'][0]['styles']['font-size']=='30px'
    # This observes one mobile state; it does not discover the authored breakpoint.
    prompt=(await PromptService(ProviderConfig()).generate(evidence,request)).prompt
    assert 'No exact CSS breakpoints' in prompt
    await browser_manager.close(session.token)
