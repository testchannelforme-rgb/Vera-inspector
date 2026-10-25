"""Actual browser evidence tests; skip honestly if the sandbox cannot launch."""
import json
from app.inspector import HIT_TEST_JS, inspect_element
from app.prompts.schemas import PromptRequest
from app.prompts.evidence import collect_evidence
from app.prompts.service import PromptService
from app.prompts.provider import ProviderConfig


async def test_actual_inspection_to_prompt(browser_manager,fixture_site):
    manager=browser_manager
    session,_=await manager.create(fixture_site+'/prompt.html',{'width':1280,'height':800})
    box=await session.page.locator('button').bounding_box()
    handle=await session.page.evaluate_handle(HIT_TEST_JS,{'x':box['x']+10,'y':box['y']+10})
    session.element=handle.as_element();session.reference_id='button-ref'
    inspection=await inspect_element(session)
    req=PromptRequest(sessionId=session.token,frameId=session.frame_id,referenceId=session.reference_id)
    evidence=await collect_evidence(session,req)
    result=await PromptService(ProviderConfig()).generate(evidence,req)
    assert inspection.styles['background-color'] in result.prompt
    assert '160px' in result.prompt and 'Start exploring' in result.prompt
    assert result.mode=='fallback'
    await manager.close(session.token)


async def test_actual_section_page_and_sensitive_inputs(browser_manager,fixture_site):
    manager=browser_manager
    session,_=await manager.create(fixture_site+'/prompt.html',{'width':1280,'height':800})
    session.element=await session.page.query_selector('button');session.reference_id='ref'
    req=PromptRequest(sessionId=session.token,frameId=session.frame_id,referenceId='ref',scope='section')
    section=await collect_evidence(session,req)
    assert section['nodes'][0]['tag']=='section'
    full=await collect_evidence(session,req.model_copy(update={'scope':'page'}))
    data=json.dumps(full)
    assert 'password-value-SECRET' not in data and 'edited-private-SECRET' not in data
    assert 'signed-secret' not in data and 'me@example.com' not in data
    assert any(n['tag']=='input' for n in full['nodes'])
    assert any(n['tag']=='nav' for n in full['nodes'])
    await manager.close(session.token)
