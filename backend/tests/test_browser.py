import base64
import json
from pathlib import Path
import pytest
from app.animation import capture_hover
from app.inspector import HIT_TEST_JS, inspect_element
from app.schemas import Inspection

pytestmark=pytest.mark.browser


async def select_id(session, selector):
    box=await session.page.locator(selector).bounding_box()
    handle=await session.page.evaluate_handle(HIT_TEST_JS,{'x':box['x']+box['width']/2,'y':box['y']+box['height']/2})
    session.element=handle.as_element();session.reference_id='test-reference'
    return await inspect_element(session)


async def test_navigation_screenshot_selection_css_serialization(browser_manager,fixture_site):
    s,frame=await browser_manager.create(fixture_site+'/',{'width':1280,'height':800})
    assert browser_manager.browser.is_connected()
    assert s.page.url==fixture_site+'/'
    assert base64.b64decode(frame['image'].split(',')[1]).startswith(b'\xff\xd8')
    data=await select_id(s,'#explore')
    assert data.element.tagName=='button' and data.element.id=='explore'
    assert data.styles['background-color']=='rgb(37, 99, 235)'
    assert data.styles['font-size']=='16px'
    assert data.geometry.width==160 and data.geometry.height==48
    assert data.element.selectorUnique and data.element.accessibility.name=='Explore fixture'
    assert data.pseudoElements['::before']['content']!='none'
    assert data.customProperties['--accent']=='#2563eb'
    assert Inspection.model_validate_json(data.model_dump_json()).element.id=='explore'
    Path('artifacts').mkdir(exist_ok=True)
    Path('artifacts/local-inspection.json').write_text(data.model_dump_json(indent=2))
    await browser_manager.close(s.token)
    assert s.context not in browser_manager.browser.contexts
    assert not browser_manager.sessions


async def test_hover_observes_actual_changes(browser_manager,fixture_site):
    s,_=await browser_manager.create(fixture_site+'/',{'width':1280,'height':800})
    await select_id(s,'#explore')
    data=await capture_hover(s,600,100)
    assert data.animations.detected
    assert len(data.animations.observations)==7
    assert any('background-color' in item['changesFromBaseline'] for item in data.animations.observations)
    assert data.animations.observations[-1]['styles']['background-color']=='rgb(200, 40, 80)'
    assert all(data.animations.hover['screenshots'].values())
    Path('artifacts/hover-inspection.json').write_text(data.model_dump_json(indent=2))


async def test_nested_scroll_shadow_svg(browser_manager,fixture_site):
    s,_=await browser_manager.create(fixture_site+'/',{'width':1280,'height':800})
    data=await select_id(s,'#shadow-button')
    assert data.element.selectorScope=='open-shadow-root'
    data=await select_id(s,'svg rect');assert data.element.tagName=='rect'
    box=await s.page.locator('#nested').bounding_box()
    await s.page.mouse.move(box['x']+20,box['y']+20)
    await s.page.mouse.wheel(0,250);await s.page.wait_for_timeout(250)
    assert await s.page.locator('#nested').evaluate('(e)=>e.scrollTop')>0
    await s.page.mouse.move(900,600);await s.page.mouse.wheel(0,500);await s.page.wait_for_timeout(250)
    assert await s.page.evaluate('scrollY')>0


async def test_subresources_and_redirects_are_checked(browser_manager,fixture_site):
    s,_=await browser_manager.create(fixture_site+'/blocked-fetch',{'width':1280,'height':800})
    await s.page.wait_for_timeout(250)
    assert s.blocked
    with pytest.raises(Exception):await browser_manager.create(fixture_site+'/redirect-private',{'width':1280,'height':800})
    assert len(browser_manager.sessions)==1


async def test_session_limit_and_no_handle_reuse(browser_manager,fixture_site):
    s,_=await browser_manager.create(fixture_site+'/',{'width':1280,'height':800})
    await select_id(s,'#explore')
    await browser_manager.navigate(s,fixture_site+'/')
    assert s.element is None
    await browser_manager.create(fixture_site+'/',{'width':1280,'height':800})
    with pytest.raises(Exception,match='busy'):await browser_manager.create(fixture_site+'/',{'width':1280,'height':800})


@pytest.mark.public
async def test_real_public_site(browser_manager,request):
    if not request.config.getoption('--public'):pytest.skip('Use --public to enable real-world navigation.')
    s,frame=await browser_manager.create('https://example.com',{'width':1280,'height':800})
    data=await select_id(s,'h1')
    assert data.element.text=='Example Domain'
    assert data.styles['font-size']
    Path('artifacts/public-inspection.json').write_text(data.model_dump_json(indent=2))
    Path('artifacts/public-website.jpg').write_bytes(base64.b64decode(frame['image'].split(',')[1]))
