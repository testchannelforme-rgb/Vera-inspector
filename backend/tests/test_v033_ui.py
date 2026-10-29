"""Real Chromium UI acceptance against an ephemeral app and local test fixture.

No mocked rendering, provider call, production network exception or deployment.
Screenshots are captured only after the assertions preceding them pass.
"""
import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
import socket
from unittest.mock import AsyncMock
import pytest
from playwright.async_api import expect
import uvicorn
from app.config import Settings
from app.main import create_app

pytestmark=pytest.mark.browser
SHOTS=Path('artifacts/generated/v033')

@asynccontextmanager
async def candidate_app(manager,monkeypatch):
    from app.security import normalize_url
    origin=manager.policy.origin
    monkeypatch.setattr('app.main.normalize_url',lambda value:value if value.startswith(origin+'/') else normalize_url(value))
    original=manager.start;manager.start=AsyncMock()
    sock=socket.socket();sock.bind(('127.0.0.1',0));sock.listen();port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(create_app(Settings(),manager),log_level='error',access_log=False))
    task=asyncio.create_task(server.serve(sockets=[sock]))
    try:
        for _ in range(400):
            if server.started:break
            await asyncio.sleep(.01)
        assert server.started
        yield f'http://127.0.0.1:{port}'
    finally:
        server.should_exit=True;await task;manager.start=original

async def no_overflow(page):
    assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Horizontal overflow'

async def test_candidate_navigation_tutorial_legal_and_responsive_screenshots(browser_manager,monkeypatch):
    SHOTS.mkdir(parents=True,exist_ok=True)
    async with candidate_app(browser_manager,monkeypatch) as base:
        context=await browser_manager.browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce',accept_downloads=True)
        try:
            page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            for name,width,height in [('desktop',1440,1000),('tablet',1024,900),('mobile',390,844)]:
                await page.set_viewport_size({'width':width,'height':height});await page.goto(base+'/#/')
                await expect(page.get_by_role('heading',level=1)).to_have_text('See the detail.Build the vision.')
                await no_overflow(page)
                assert await page.evaluate('Object.keys(localStorage).length')==0
                assert await context.cookies()==[]
                assert await page.evaluate('matchMedia("(prefers-reduced-motion: reduce)").matches')
                assert await page.locator('.primary').first.evaluate('e=>getComputedStyle(e).transitionDuration')=='0s'
                await page.screenshot(path=str(SHOTS/f'{name}-landing.png'),full_page=True)
                if width==390:
                    await page.get_by_role('button',name='Open navigation').click()
                    await expect(page.get_by_role('button',name='Close navigation')).to_have_attribute('aria-expanded','true')
                    await page.locator('#main-navigation').get_by_role('link',name='About',exact=True).click()
                    await expect(page.get_by_role('heading',level=1)).to_have_text('Make the details useful.')
                    await no_overflow(page)
            for path,title in [('privacy','Privacy Policy'),('cookies','Cookie Policy'),('terms','Terms of Service'),('about','Make the details useful.'),('contact','Help shape the next iteration.'),('preferences','Data preferences'),('brand','Three ways to see VEYRA.')]:
                await page.goto(base+'/#/'+path);await expect(page.get_by_role('heading',level=1)).to_have_text(title);await no_overflow(page)
                if path in ('privacy','cookies','terms'):await expect(page.get_by_text('DRAFT · OWNER REVIEW REQUIRED',exact=True)).to_be_visible()
                if path=='brand':assert await page.locator('.logo-options img').count()==3
            await page.set_viewport_size({'width':1440,'height':1000});await page.goto(base+'/#/brand')
            await page.screenshot(path=str(SHOTS/'logo-concepts.png'),full_page=True)
            await page.goto(base+'/#/inspector')
            await page.get_by_role('button',name='Start tutorial',exact=True).click()
            await expect(page.get_by_role('heading',name='Open a website',exact=True)).to_be_visible()
            await page.get_by_role('button',name='Next',exact=True).click();await expect(page.get_by_role('heading',name='Select an element',exact=True)).to_be_visible()
            await page.get_by_role('button',name='Back',exact=True).click();await expect(page.get_by_role('heading',name='Open a website',exact=True)).to_be_visible()
            await page.get_by_role('button',name='Skip',exact=True).click()
            assert await page.evaluate('JSON.parse(localStorage.getItem("veyra.preferences.v1")).tutorialDismissed')
            await page.reload();await expect(page.get_by_role('button',name='Start tutorial',exact=True)).to_have_count(0)
            await page.get_by_role('button',name='Replay tutorial',exact=True).click()
            for _ in range(5):await page.get_by_role('button',name='Next',exact=True).click()
            await page.get_by_role('button',name='Finish',exact=True).click()
            await expect(page.get_by_role('complementary',name='Inspector tutorial')).to_have_count(0)
            await page.get_by_role('tab',name='Prompt',exact=True).focus();await page.keyboard.press('ArrowRight');await expect(page.get_by_role('tab',name='Evidence',exact=True)).to_be_focused()
            assert not errors,errors
        finally:await context.close()

async def test_candidate_real_inspection_prompt_reports_exports_and_history(browser_manager,fixture_site,monkeypatch):
    SHOTS.mkdir(parents=True,exist_ok=True)
    async with candidate_app(browser_manager,monkeypatch) as base:
        context=await browser_manager.browser.new_context(viewport={'width':1440,'height':1100},accept_downloads=True,reduced_motion='reduce')
        try:
            page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            await page.goto(base+'/#/inspector');await page.get_by_role('button',name='Skip',exact=True).click()
            await page.get_by_label('Website URL').fill(fixture_site+'/');await page.get_by_role('button',name='Open website').click()
            preview=page.get_by_role('button',name='Select an element in the website screenshot')
            await preview.wait_for();await page.locator('.image-stage[aria-busy="false"]').wait_for()
            session=next(iter(browser_manager.sessions.values()))
            box=await session.page.locator('#explore').bounding_box();display=await preview.bounding_box()
            await preview.click(position={'x':(box['x']+box['width']/2)*display['width']/1280,'y':(box['y']+box['height']/2)*display['height']/800})
            await page.get_by_test_id('selection-overlay').wait_for();await expect(page.locator('.element-tag')).to_contain_text('button')
            overlay=await page.get_by_test_id('selection-overlay').bounding_box();assert abs(overlay['width']-160*display['width']/1280)<2
            await page.get_by_role('tab',name='Motion',exact=True).click();await page.get_by_role('button',name='Capture hover',exact=True).click()
            await page.get_by_text('Captured states',exact=True).wait_for()
            await page.get_by_label('Advanced prompt preset').select_option('responsive-first')
            await page.get_by_role('button',name='Generate Prompt',exact=True).click()
            output=page.get_by_label('Generated prompt',exact=True);await expect(output).to_have_value(__import__('re').compile('.*## 8. Accuracy notes',__import__('re').S),timeout=30000)
            value=await output.input_value();assert 'intrinsic grid/flex' in value and 'Actual selected-element hover observation' in value
            await page.get_by_role('tab',name='Evidence',exact=True).click();await expect(page.get_by_role('heading',name='Prompt Quality & Evidence Report')).to_be_visible()
            assert await page.locator('.coverage-stats').inner_text();assert 'accuracy score' in await page.locator('.evidence-report').inner_text()
            await page.locator('.evidence-report').screenshot(path=str(SHOTS/'evidence-report.png'))
            await page.get_by_role('tab',name='Prompt',exact=True).click()
            # Screenshots retain a real selected element and generated prompt, not mock evidence.
            for name,width,height in [('desktop',1440,1100),('tablet',1024,900),('mobile',390,844)]:
                await page.set_viewport_size({'width':width,'height':height});await no_overflow(page)
                displayed=await preview.bounding_box();actual=await page.get_by_test_id('selection-overlay').bounding_box()
                assert abs(actual['width']-160*displayed['width']/1280)<2
                await page.screenshot(path=str(SHOTS/f'{name}-workspace.png'),full_page=True)
            await page.set_viewport_size({'width':1440,'height':1100})
            await page.locator('.prompt-panel').screenshot(path=str(SHOTS/'prompt-studio.png'))
            async with page.expect_download() as download_info:await page.get_by_role('button',name='Export asset checklist',exact=True).click()
            checklist=await download_info.value;assert 'Missing evidence' in Path(await checklist.path()).read_text()
            await output.fill('My edited prompt\n## 1. Objective\nKeep my exact edits.');
            for label in ('Export TXT','Export Markdown'):
                async with page.expect_download() as download_info:await page.get_by_role('button',name=label,exact=True).click()
                download=await download_info.value;assert Path(await download.path()).read_text()=='My edited prompt\n## 1. Objective\nKeep my exact edits.'
            await page.get_by_role('tab',name='History',exact=True).click();await page.get_by_label('Version title').fill('UI edited')
            await page.get_by_role('button',name='Enable local history & save version',exact=True).click()
            await expect(page.get_by_role('button',name='Restore UI edited',exact=True)).to_be_visible()
            assert 'Keep my exact edits.' in await page.evaluate('localStorage.getItem("veyra.prompt-history.v1")')
            await page.reload();await page.get_by_role('tab',name='History',exact=True).click();await page.get_by_role('button',name='Restore UI edited',exact=True).click()
            await expect(page.get_by_label('Generated prompt',exact=True)).to_have_value('My edited prompt\n## 1. Objective\nKeep my exact edits.')
            await page.get_by_role('tab',name='Evidence',exact=True).click();await expect(page.get_by_role('heading',name='No evidence report attached',exact=True)).to_be_visible()
            await page.get_by_role('tab',name='History',exact=True).click();await page.get_by_role('button',name='Duplicate UI edited',exact=True).click()
            await page.get_by_role('button',name='Delete UI edited · copy',exact=True).click();await page.get_by_role('button',name='Confirm delete version',exact=True).click()
            assert await page.get_by_role('button',name='Restore UI edited',exact=True).count()==1
            await page.get_by_role('link',name='Data preferences',exact=True).click();await page.get_by_role('checkbox').uncheck()
            await page.get_by_role('button',name='Delete saved versions & disable',exact=True).click()
            assert await page.evaluate('localStorage.getItem("veyra.prompt-history.v1")') is None
            assert not await page.evaluate('JSON.parse(localStorage.getItem("veyra.preferences.v1")).historyEnabled')
            assert not errors,errors
        finally:await context.close()
