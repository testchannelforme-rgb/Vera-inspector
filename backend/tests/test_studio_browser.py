"""Offline browser acceptance. Explicit runner binary; never changes production launch.

STUDIO_TEST_CHROMIUM may point to a host UI test runner. That runner uses no OS
sandbox in this restricted host; production protected-engine acceptance remains
in the inherited browser suite and must pass separately on a capable host.
"""
import asyncio
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import socket
import subprocess
import zipfile
import pytest
from playwright.async_api import async_playwright,expect
import uvicorn
from app.browser_manager import BrowserManager
from app.config import Settings
from app.main import create_app
from app.studio.service import StudioService
from conftest import FixturePolicy,QuietHandler
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import functools
import threading

pytestmark=pytest.mark.browser

@asynccontextmanager
async def source_app(fixture_site,monkeypatch):
    executable=os.getenv('STUDIO_TEST_CHROMIUM')
    if not executable:pytest.skip('Set STUDIO_TEST_CHROMIUM for offline UI runner; protected engine tests are separate.')
    manager=BrowserManager(Settings(),FixturePolicy(fixture_site))
    original_resolve=manager.proxy.resolve
    async def resolve(url):
        if url.startswith(fixture_site+'/'):return url,'127.0.0.1',int(fixture_site.rsplit(':',1)[1])
        return await original_resolve(url)
    manager.proxy.resolve=resolve
    async def start():
        await manager.proxy.start();manager.playwright=await async_playwright().start()
        manager.browser=await manager.playwright.chromium.launch(executable_path=executable,headless=True,
            args=['--no-sandbox','--disable-dev-shm-usage','--proxy-bypass-list=<-loopback>'])
    manager.start=start
    from app.security import normalize_url
    monkeypatch.setattr('app.main.normalize_url',lambda v:v if v.startswith(fixture_site+'/') else normalize_url(v))
    service=StudioService(db=':memory:');service.generation_limit=30
    app=create_app(Settings(),manager,studio_service=service)
    sock=socket.socket();sock.bind(('127.0.0.1',0));sock.listen();port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,log_level='error',access_log=False))
    task=asyncio.create_task(server.serve(sockets=[sock]))
    try:
        for _ in range(500):
            if server.started:break
            await asyncio.sleep(.01)
        assert server.started
        yield f'http://127.0.0.1:{port}',manager,service
    finally:server.should_exit=True;await task

@asynccontextmanager
async def static_project(root):
    handler=functools.partial(QuietHandler,directory=str(root))
    server=ThreadingHTTPServer(('127.0.0.1',0),handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield f'http://127.0.0.1:{server.server_port}'
    finally:server.shutdown();server.server_close();thread.join()

@pytest.mark.parametrize('fmt',['vanilla','react'])
async def test_offline_studio_full_flow(fixture_site,monkeypatch,tmp_path,fmt):
    async with source_app(fixture_site,monkeypatch) as (base,manager,service):
        context=await manager.browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
        await context.add_init_script('navigator.clipboard.writeText = async text => { window.__copied = text; };')
        page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        await page.goto(base+'/#/inspector')
        await page.get_by_role('textbox',name='Website URL').fill(fixture_site+'/prompt.html')
        await page.get_by_role('button',name='Open website →').click()
        image=page.get_by_role('button',name='Select an element in the website screenshot')
        await expect(image).to_be_visible()
        session=next(iter(manager.sessions.values()))
        target=await session.page.get_by_role('button',name='Start exploring').bounding_box()
        box=await image.bounding_box();scale=box['width']/1280
        await image.click(position={'x':(target['x']+target['width']/2)*scale,'y':(target['y']+target['height']/2)*scale})
        await expect(page.get_by_role('button',name='Generate Code',exact=True)).to_be_enabled()
        # Existing prompt generation still uses the same selected evidence.
        await page.get_by_role('button',name='Generate Prompt',exact=True).click()
        await expect(page.get_by_role('button',name='Copy Prompt',exact=True)).to_be_enabled()
        studio=page.get_by_role('region',name='Veyra Code Studio')
        await studio.get_by_label('Code output format').select_option(fmt)
        await studio.get_by_role('button',name='Generate Code',exact=True).click()
        await expect(studio.get_by_role('button',name='Download project')).to_be_enabled(timeout=20000)
        frame=studio.frame_locator('iframe')
        await expect(frame.get_by_role('button',name='Start exploring')).to_be_visible(timeout=20000)
        assert await frame.locator('body').evaluate("() => {try {parent.document.body; return false} catch {return true}}")
        assert await frame.locator('body').evaluate("() => {try {localStorage.getItem('x'); return false} catch {return true}}")
        await studio.get_by_role('button',name='style.css',exact=True).click()
        editor=studio.get_by_role('textbox',name='Code editor style.css')
        await expect(editor).to_be_visible()
        await editor.fill('button { background: rgb(180, 20, 30); color: white; width: 160px; height: 48px; }')
        await expect(frame.get_by_role('button',name='Start exploring')).to_have_css('background-color','rgb(180, 20, 30)',timeout=15000)
        await editor.press('Control+z')
        await expect(editor).to_contain_text('rgb(37, 99, 235)')
        await editor.press('Control+Shift+z')
        await expect(editor).to_contain_text('rgb(180, 20, 30)')
        await studio.get_by_role('button',name='Copy file').click()
        assert 'rgb(180, 20, 30)' in await page.evaluate('window.__copied')
        async with page.expect_download() as download:
            await studio.get_by_role('button',name='Download project').click()
        archive=tmp_path/'export.zip';await (await download.value).save_as(archive)
        exported=tmp_path/'exported'
        with zipfile.ZipFile(archive) as z:z.extractall(exported)
        assert 'rgb(180, 20, 30)' in (exported/'style.css').read_text()
        if fmt=='react':
            (exported/'node_modules').symlink_to(Path('frontend/node_modules').resolve(),target_is_directory=True)
            run=await asyncio.to_thread(subprocess.run,['npm','run','build'],cwd=exported,capture_output=True,text=True,timeout=30)
            assert run.returncode==0,run.stderr
        async with static_project(exported/'dist' if fmt=='react' else exported) as url:
            independent=await context.new_page();await independent.goto(url)
            await expect(independent.get_by_role('button',name='Start exploring')).to_have_css('background-color','rgb(180, 20, 30)')
            await independent.close()
        if os.getenv('STUDIO_SHOTS_DIR'):
            shots=Path(os.environ['STUDIO_SHOTS_DIR']);shots.mkdir(parents=True,exist_ok=True)
            await studio.screenshot(path=str(shots/(fmt+'-studio.png')))
        # Bad JS yields a visible compiler error without changing the current files.
        await studio.get_by_role('button',name='script.js' if fmt=='vanilla' else 'App.jsx',exact=True).click()
        await studio.get_by_role('textbox',name='Code editor '+('script.js' if fmt=='vanilla' else 'App.jsx')).fill('function (')
        await expect(studio.get_by_role('alert')).to_be_visible(timeout=15000)
        await studio.get_by_role('button',name='style.css',exact=True).click()
        await expect(studio.get_by_role('textbox',name='Code editor style.css')).to_contain_text('rgb(180, 20, 30)')
        await studio.get_by_role('button',name='Reset generated code').click()
        await studio.get_by_role('button',name='Confirm restore',exact=True).click()
        await studio.get_by_role('button',name='Restore previous').click()
        await studio.get_by_role('button',name='Confirm restore',exact=True).click()
        await expect(studio.get_by_role('textbox',name='Code editor style.css')).to_contain_text('rgb(180, 20, 30)')
        for width in [1024,768,390]:
            await page.set_viewport_size({'width':width,'height':900})
            assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'Overflow at {width}'
            if width<=900:
                await studio.get_by_role('tab',name='Live preview',exact=True).click()
                await expect(studio.locator('.studio-live')).to_be_visible()
                await studio.get_by_role('tab',name='Edit',exact=True).click()
                await expect(studio.locator('.studio-edit')).to_be_visible()
        assert not errors,errors
        await context.close()

async def test_runtime_error_and_resource_isolation(fixture_site,monkeypatch):
    from app.studio.local import reconstruct
    from test_studio import evidence
    async with source_app(fixture_site,monkeypatch) as (base,manager,service):
        context=await manager.browser.new_context();page=await context.new_page();await page.goto(base)
        await page.evaluate("localStorage.setItem('host-secret','PRIVATE')")
        project,_=reconstruct(evidence(),'vanilla')
        project.files['script.js']="""
let blocked=0;
try { parent.document.body.innerHTML='BAD'; } catch { blocked++; }
try { localStorage.getItem('host-secret'); } catch { blocked++; }
fetch('/api/health').then(()=>document.body.textContent='BAD').catch(()=>document.body.textContent=blocked===2?'SAFE':'BAD');
"""
        response=await context.request.post(base+'/api/studio/preview',headers={'X-Veyra-Client':'inspector-v0.1'},data={'project':project.model_dump()})
        assert response.ok
        url=(await response.json())['url']
        await page.evaluate("url=>{const f=document.createElement('iframe');f.title='isolation test';f.sandbox='allow-scripts';f.src=url;document.body.append(f)}",url)
        await expect(page.frame_locator('iframe[title="isolation test"]').locator('body')).to_have_text('SAFE')
        assert await page.evaluate("localStorage.getItem('host-secret')")=='PRIVATE'
        assert (await page.get_by_role('heading',level=1).inner_text()).replace('\n','')=='See the detail.Build the vision.'
        await context.close()
