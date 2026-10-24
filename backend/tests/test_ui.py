"""Real browser -> served React -> API -> remote browser -> actual DOM -> export."""
import asyncio
import json
from pathlib import Path
import socket
from unittest.mock import AsyncMock
import pytest
import uvicorn
from app.main import create_app
from app.config import Settings

pytestmark=pytest.mark.browser


async def test_tablet_ui_selection_hover_export(browser_manager,fixture_site,monkeypatch):
    from app.security import normalize_url
    monkeypatch.setattr("app.main.normalize_url",lambda value:value if value.startswith(fixture_site+"/") else normalize_url(value))
    manager=browser_manager
    # The fixture already started the real manager; prevent lifespan from launching twice.
    original_start=manager.start
    manager.start=AsyncMock()
    app=create_app(Settings(),manager)
    sock=socket.socket();sock.bind(('127.0.0.1',0));sock.listen()
    port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,log_level='error',access_log=False))
    task=asyncio.create_task(server.serve(sockets=[sock]))
    context=None
    try:
        for _ in range(200):
            if server.started:break
            await asyncio.sleep(.01)
        assert server.started
        context=await manager.browser.new_context(viewport={'width':1024,'height':900},accept_downloads=True)
        page=await context.new_page()
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        await page.goto(f'http://127.0.0.1:{port}')
        await page.get_by_label('Website URL').fill(fixture_site+'/')
        await page.get_by_role('button',name='Open website').click()
        preview=page.get_by_role('button',name='Select an element in the website screenshot')
        await preview.wait_for()
        await page.wait_for_function('document.querySelector(".image-stage")?.getAttribute("aria-busy")==="false"')
        session=next(s for s in manager.sessions.values())
        target=await session.page.locator('#explore').bounding_box()
        displayed=await preview.bounding_box()
        x=(target['x']+target['width']/2)*displayed['width']/1280
        y=(target['y']+target['height']/2)*displayed['height']/800
        await preview.click(position={'x':x,'y':y})
        overlay=page.get_by_test_id('selection-overlay');await overlay.wait_for()
        assert 'button' in await overlay.inner_text()
        rect=await overlay.bounding_box()
        assert abs(rect['width']-160*displayed['width']/1280)<2
        await page.get_by_role('tab',name='Motion',exact=True).click()
        await page.get_by_role('button',name='Capture hover').click()
        await page.get_by_text('Captured states',exact=True).wait_for(timeout=10000)
        async with page.expect_download() as download_info:
            await page.get_by_role('button',name='Export JSON').click()
        download=await download_info.value
        path=await download.path()
        data=json.loads(Path(path).read_text())
        assert data['element']['id']=='explore'
        assert data['animations']['observations']
        assert not errors
        Path('artifacts').mkdir(exist_ok=True)
        await download.save_as('artifacts/ui-export.json')
        await page.screenshot(path='artifacts/veyra-tablet.png',full_page=True)
        await page.set_viewport_size({'width':390,'height':844})
        assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        await page.screenshot(path='artifacts/veyra-mobile.png',full_page=True)
        await page.get_by_role('button',name='Clear',exact=True).click()
        await overlay.wait_for(state='detached')
        await page.get_by_role('button',name='Close',exact=True).click()
        await page.get_by_text('Session closed.',exact=True).wait_for()
        assert not manager.sessions
    finally:
        if context:await context.close()
        server.should_exit=True
        await task
        manager.start=original_start
