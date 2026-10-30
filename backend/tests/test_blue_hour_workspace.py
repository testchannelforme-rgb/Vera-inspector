import os
import asyncio
from pathlib import Path
import pytest
from playwright.async_api import expect
from test_studio_browser import source_app

async def wait_native(page,predicate):
 for _ in range(100):
  if await page.evaluate('() => ('+predicate+')'):return
  await asyncio.sleep(.05)
 raise AssertionError('Native fullscreen state did not settle: '+predicate)

@pytest.mark.parametrize('fmt',['vanilla','react'])
async def test_blue_hour_tools_end_to_end(fixture_site,monkeypatch,tmp_path,fmt):
 if not os.getenv('STUDIO_TEST_CHROMIUM'):pytest.skip('Set STUDIO_TEST_CHROMIUM for offline browser acceptance')
 async with source_app(fixture_site,monkeypatch) as (base,manager,service):
  context=await manager.browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True,reduced_motion='reduce')
  await context.add_init_script('Element.prototype.requestFullscreen=undefined;') # Exercise mobile-compatible fallback explicitly.
  page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(base+'/#/inspector')
  await expect(page.locator('.brand img').first).to_have_attribute('src','/brand/veyra-official.webp')
  assert await page.locator('.brand img').first.evaluate('e=>e.complete&&e.naturalWidth>0')
  assert await page.evaluate('getComputedStyle(document.documentElement).backgroundColor')=='rgb(8, 21, 41)'
  await page.get_by_role('textbox',name='Website URL').fill(fixture_site+'/prompt.html')
  await page.get_by_role('button',name='Open website →').click()
  original=page.get_by_role('region',name='Website preview',exact=True)
  await original.get_by_role('button',name='Fullscreen inspector',exact=True).click()
  await expect(original).to_have_class('preview-panel workspace-fullscreen')
  await expect(original.get_by_role('button',name='Select an element in the website screenshot')).to_be_visible()
  await expect(original.get_by_role('button',name='Select an element in the website screenshot')).to_have_attribute('tabindex','0')
  session=next(iter(manager.sessions.values()));box=await session.page.get_by_role('button',name='Start exploring').bounding_box()
  image=original.get_by_role('button',name='Select an element in the website screenshot')
  rect=await image.bounding_box();scale=rect['width']/1280
  await image.hover(position={'x':(box['x']+box['width']/2)*scale,'y':(box['y']+box['height']/2)*scale})
  await expect(original.locator('.hover-overlay')).to_be_visible()
  await image.click(position={'x':(box['x']+box['width']/2)*scale,'y':(box['y']+box['height']/2)*scale})
  await expect(original.get_by_test_id('selection-overlay')).to_be_visible()
  await page.keyboard.press('Escape');await expect(original).not_to_have_class('preview-panel workspace-fullscreen')
  studio=page.get_by_role('region',name='Veyra Code Studio')
  await studio.get_by_label('Code output format').select_option(fmt)
  await studio.get_by_role('button',name='Generate Code',exact=True).click()
  await expect(studio.get_by_role('button',name='Download project',exact=True).first).to_be_enabled(timeout=25000)
  await expect(studio.get_by_role('list',name='Generation stages')).to_contain_text('Complete')
  frame=studio.frame_locator('iframe')
  await expect(frame.get_by_role('button',name='Start exploring')).to_be_visible(timeout=20000)
  await expect(frame.get_by_role('button',name='Start exploring')).to_have_css('background-color','rgb(37, 99, 235)')
  await studio.get_by_role('button',name='Fullscreen editor',exact=True).click()
  await expect(studio.locator('.studio-edit')).to_have_class('studio-edit workspace-fullscreen')
  await studio.get_by_role('button',name='style.css',exact=True).click()
  editor=studio.get_by_role('textbox',name='Code editor style.css');await editor.fill('button { background: rgb(20, 140, 80); width: 160px; height: 48px; }')
  await studio.get_by_role('button',name='Exit editor fullscreen',exact=True).last.click()
  await expect(frame.get_by_role('button',name='Start exploring')).to_have_css('background-color','rgb(20, 140, 80)',timeout=15000)
  await studio.get_by_role('button',name='Fullscreen preview',exact=True).click()
  await expect(studio.locator('.studio-live')).to_have_class('studio-live workspace-fullscreen')
  await page.keyboard.press('Escape')
  await studio.get_by_label('Click to edit',exact=True).check()
  await frame.get_by_role('button',name='Start exploring').click()
  mapped='App.jsx' if fmt=='react' else 'index.html'
  await expect(studio.get_by_role('textbox',name='Code editor '+mapped)).to_be_visible()
  selected=await studio.locator('.cm-content').evaluate('e=>getSelection().toString()')
  assert 'data-veyra-node' in selected,selected
  await studio.get_by_label('Click to edit',exact=True).uncheck()
  await studio.get_by_role('button',name='Compare mode',exact=True).click()
  await expect(studio.get_by_role('region',name='Original website comparison')).to_be_visible()
  await studio.get_by_label('Preview viewport').select_option('390px')
  await studio.get_by_role('button',name='Match original viewport').click()
  await expect(studio.get_by_role('region',name='Original website comparison')).to_contain_text('390 × 844')
  assert await studio.locator('iframe').evaluate('e=>e.clientWidth')==390
  await studio.get_by_role('button',name='Fullscreen comparison').click()
  await expect(studio.locator('.studio-grid')).to_have_class('studio-grid show-edit compare-active workspace-fullscreen')
  await page.keyboard.press('Escape')
  await studio.get_by_role('button',name='Compare mode',exact=True).click()
  await studio.get_by_role('button',name='Version history',exact=True).click()
  await studio.get_by_role('button',name='Save checkpoint',exact=True).click()
  await studio.get_by_role('button',name='Save draft',exact=True).first.click()
  await expect(studio.locator('.save-status')).to_contain_text('Saved locally')
  await page.reload();studio=page.get_by_role('region',name='Veyra Code Studio')
  await studio.get_by_role('button',name='style.css',exact=True).click()
  await expect(studio.get_by_role('textbox',name='Code editor style.css')).to_contain_text('rgb(20, 140, 80)')
  await studio.get_by_role('button',name='Version history',exact=True).click()
  await studio.get_by_role('button',name='Restore checkpoint 1',exact=True).click()
  await expect(studio.get_by_role('button',name='Confirm restore')).to_be_visible()
  await studio.get_by_role('button',name='Cancel restore').click()
  code_file='script.js' if fmt=='vanilla' else 'App.jsx'
  await studio.get_by_role('button',name=code_file,exact=True).click()
  await studio.get_by_role('textbox',name='Code editor '+code_file).fill('function (')
  await studio.get_by_role('button',name='Error console (0)',exact=True).click()
  await expect(studio.get_by_role('region',name='Preview error console')).to_contain_text('error',timeout=15000)
  console_code="console.warn('Console fixture token=PRIVATEVALUE');" if fmt=='vanilla' else "import React from 'react';console.warn('Console fixture token=PRIVATEVALUE');export default function App(){return <button data-veyra-node={0}>Done</button>}"
  await studio.get_by_role('textbox',name='Code editor '+code_file).fill(console_code)
  console=studio.get_by_role('region',name='Preview error console')
  await expect(console).to_contain_text('Console fixture [redacted]',timeout=15000)
  await expect(console).not_to_contain_text('PRIVATEVALUE')
  await studio.frame_locator('iframe').locator('body').evaluate("()=>parent.postMessage({type:'veyra-preview-console',level:'error',message:'forged-message',token:'incorrect'},'*')")
  await expect(console).not_to_contain_text('forged-message')
  await page.keyboard.press('Alt+Shift+f');await expect(page.locator('body')).to_have_class('veyra-focus')
  await page.keyboard.press('Escape');await expect(page.locator('body')).not_to_have_class('veyra-focus')
  for width in [1024,768,390]:
   await page.set_viewport_size({'width':width,'height':900})
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
  if os.getenv('STUDIO_SHOTS_DIR'):
   directory=Path(os.environ['STUDIO_SHOTS_DIR']);directory.mkdir(parents=True,exist_ok=True)
   await page.set_viewport_size({'width':1440,'height':1100});await studio.screenshot(path=str(directory/('blue-hour-'+fmt+'.png')))
  assert not errors,errors
  await context.close()

async def test_native_fullscreen_when_supported(fixture_site,monkeypatch):
 if not os.getenv('STUDIO_TEST_CHROMIUM'):pytest.skip('Offline browser runner not configured')
 async with source_app(fixture_site,monkeypatch) as (base,manager,service):
  context=await manager.browser.new_context(viewport={'width':1440,'height':1000});page=await context.new_page();await page.goto(base+'/#/inspector')
  if not await page.evaluate('document.fullscreenEnabled&&!!Element.prototype.requestFullscreen'):
   await context.close();pytest.skip('Native Fullscreen API unavailable; fallback covered separately')
  await page.get_by_role('button',name='Fullscreen inspector',exact=True).click()
  await wait_native(page,'document.fullscreenElement?.getAttribute("aria-label")==="Website preview"')
  await page.get_by_role('button',name='Exit inspector fullscreen',exact=True).click()
  await wait_native(page,'document.fullscreenElement===null')
  from app.studio.local import reconstruct
  from test_studio import evidence
  project,_=reconstruct(evidence(),'vanilla')
  await page.evaluate('(project)=>localStorage.setItem("veyra.code-studio.v2",JSON.stringify({schema:2,project,original:project,file:"index.html",savedAt:new Date().toISOString(),history:[]}))',project.model_dump())
  await page.reload()
  studio=page.get_by_role('region',name='Veyra Code Studio')
  await expect(studio.get_by_role('button',name='Fullscreen editor',exact=True)).to_be_enabled()
  await studio.get_by_role('button',name='Fullscreen editor',exact=True).click()
  await wait_native(page,'document.fullscreenElement?.classList.contains("studio-edit")')
  await studio.locator('.editor-fullscreen-tools').get_by_role('button',name='Exit editor fullscreen',exact=True).click()
  await wait_native(page,'document.fullscreenElement===null')
  await studio.get_by_role('button',name='Fullscreen preview',exact=True).click()
  await wait_native(page,'document.fullscreenElement?.classList.contains("studio-live")')
  await studio.locator('.studio-live').get_by_role('button',name='Exit preview fullscreen',exact=True).click()
  await wait_native(page,'document.fullscreenElement===null')
  await context.close()

async def test_cross_tab_autosave_conflict_keeps_current_work(fixture_site,monkeypatch):
 if not os.getenv('STUDIO_TEST_CHROMIUM'):pytest.skip('Offline browser runner not configured')
 import json
 from app.studio.local import reconstruct
 from test_studio import evidence
 async with source_app(fixture_site,monkeypatch) as (base,manager,service):
  context=await manager.browser.new_context(viewport={'width':1440,'height':1000})
  p,_=reconstruct(evidence(),'vanilla');data={'schema':2,'project':p.model_dump(),'original':p.model_dump(),'file':'style.css','savedAt':'2026-10-30T01:00:00Z','history':[]}
  page=await context.new_page();await page.goto(base)
  await page.evaluate('(data)=>localStorage.setItem("veyra.code-studio.v2",JSON.stringify(data))',data)
  await page.goto(base+'/#/inspector');studio=page.get_by_role('region',name='Veyra Code Studio')
  await expect(studio.get_by_role('textbox',name='Code editor style.css')).to_be_visible()
  await expect(studio.locator('.save-status')).to_contain_text('Saved locally')
  other=await context.new_page();await other.goto(base)
  await other.evaluate('''()=>{const d=JSON.parse(localStorage.getItem('veyra.code-studio.v2'));d.savedAt='2026-10-30T02:00:00Z';d.project.files['style.css']='NEWER DRAFT';localStorage.setItem('veyra.code-studio.v2',JSON.stringify(d));}''')
  await expect(studio.locator('.save-status')).to_contain_text('Another tab changed')
  await studio.get_by_role('textbox',name='Code editor style.css').fill('MY UNSAVED CODE')
  assert await page.evaluate("JSON.parse(localStorage.getItem('veyra.code-studio.v2')).project.files['style.css']")=='NEWER DRAFT'
  await expect(studio.get_by_role('textbox',name='Code editor style.css')).to_contain_text('MY UNSAVED CODE')
  await context.close()

async def test_runtime_and_asset_failures_reach_console(fixture_site,monkeypatch):
 if not os.getenv('STUDIO_TEST_CHROMIUM'):pytest.skip('Offline browser runner not configured')
 import re
 from app.studio.local import reconstruct
 from test_studio import evidence
 async with source_app(fixture_site,monkeypatch) as (base,manager,service):
  context=await manager.browser.new_context();page=await context.new_page();await page.goto(base)
  project,_=reconstruct(evidence(),'vanilla')
  project.files['script.js']="setTimeout(()=>{throw Error('runtime-fixture')},80)"
  project.files['index.html']=project.files['index.html'].replace('<body>','<body><img src="data:image/png;base64,not-a-valid-image">')
  await page.evaluate('(project)=>localStorage.setItem("veyra.code-studio.v2",JSON.stringify({schema:2,project,original:project,file:"script.js",savedAt:new Date().toISOString(),history:[]}))',project.model_dump())
  await page.goto(base+'/#/inspector');studio=page.get_by_role('region',name='Veyra Code Studio')
  await expect(studio.locator('iframe')).to_be_visible(timeout=15000)
  await studio.get_by_role('button',name=re.compile(r'^Error console')).click()
  console=studio.get_by_role('region',name='Preview error console')
  await expect(console).to_contain_text('runtime-fixture',timeout=15000)
  await expect(console).to_contain_text('Resource failed: IMG',timeout=15000)
  await context.close()
