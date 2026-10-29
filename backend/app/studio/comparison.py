"""Offline preview rendering in an existing protected browser; no network fetches."""
import asyncio
from io import BytesIO
import math
from PIL import Image,ImageChops,ImageStat
from .preview import compile_project,document

VIRTUAL='https://veyra-preview.invalid/render'
MEASURE="""() => ({nodes:Array.from(document.querySelectorAll('[data-veyra-node]')).slice(0,55).map(e=>{const b=e.getBoundingClientRect(),s=getComputedStyle(e);return {id:Number(e.dataset.veyraNode),x:b.x,y:b.y,width:b.width,height:b.height,color:s.color,background:s.backgroundColor,font:s.fontSize}}),overflow:document.documentElement.scrollWidth>innerWidth})"""

def compare(reference, actual, expected, measured):
    a=Image.open(BytesIO(reference)).convert('RGB');b=Image.open(BytesIO(actual)).convert('RGB')
    if a.size!=b.size:return {'available':False,'reason':'Screenshot dimensions differ; no pixel score computed.'}
    # Downsampling bounds CPU; absolute mean channel error, not an accuracy percentage.
    size=(min(a.width,512),min(a.height,512));delta=ImageChops.difference(a.resize(size),b.resize(size))
    pixel=sum(ImageStat.Stat(delta).mean)/3
    found={n['id']:n for n in measured['nodes']};root=expected[0].get('box',{});errors=[];missing=0;styles=0
    for n in expected:
        m=found.get(n['id'])
        if not m:missing+=1;continue
        box=n.get('box',{})
        for k in ('x','y','width','height'):
            if k in box:
                want=box[k]-(root.get(k,0) if k in ('x','y') else 0)
                errors.append(abs(want-m[k]))
        css=n.get('styles',{})
        styles+=sum(css.get(k) is not None and css[k]!=m[field] for k,field in [('color','color'),('background-color','background'),('font-size','font')])
    geometry=sum(errors)/max(1,len(errors))
    return {'available':True,'pixelMAE':round(pixel,3),'geometryMAEpx':round(geometry,3),'missingNodes':missing,'styleMismatches':styles,'overflow':measured['overflow'],
        'loss':round(pixel+min(geometry,255)+missing*20+styles*3+int(measured['overflow'])*20,3),
        'limitations':['Same captured viewport only; font rasterization and animation timing can differ.','Not an accuracy percentage; missing node IDs reduce comparison reliability.']}

class Comparator:
    def __init__(self,manager):self.manager=manager;self.lock=asyncio.Lock()
    async def render(self,project,reference):
        if not self.manager.browser or not self.manager.browser.is_connected():return {'available':False,'reason':'Protected comparison browser unavailable.'}
        if self.lock.locked():return {'available':False,'reason':'Comparison busy.'}
        async with self.lock:
            context=None
            try:
                async with asyncio.timeout(12):
                    js=await compile_project(project);doc,csp=document(project,js)
                    context=await self.manager.browser.new_context(viewport=reference['viewport'],service_workers='block',accept_downloads=False)
                    async def route(r):
                        if r.request.url==VIRTUAL and r.request.is_navigation_request():
                            await r.fulfill(body=doc,content_type='text/html',headers={'Content-Security-Policy':csp})
                        else:await r.abort()
                    await context.route('**/*',route)
                    await context.route_web_socket('**/*',lambda ws:ws.close())
                    page=await context.new_page();runtime=[]
                    page.on('pageerror',lambda e:runtime.append(str(e)[:200]))
                    context.on('page',lambda p:p.close() if p!=page else None)
                    await page.goto(VIRTUAL,wait_until='load');await page.wait_for_timeout(180)
                    measured=await page.evaluate(MEASURE)
                    image=await page.screenshot(type='png',clip=reference['clip'],timeout=3000)
                    result=compare(reference['png'],image,reference['nodes'],measured)
                    result['runtimeErrors']=runtime[:4]
                    if runtime:result['loss']+=1000
                    return result
            except Exception as exc:return {'available':False,'reason':'Comparison failed: '+type(exc).__name__}
            finally:
                if context:await context.close()

async def capture_reference(session,evidence):
    root=evidence['nodes'][0].get('box',{});vp=evidence.get('viewport',{})
    x=max(0,root.get('x',0));y=max(0,root.get('y',0))
    width=min(root.get('width',0),vp.get('width',0)-x);height=min(root.get('height',0),vp.get('height',0)-y)
    if width<1 or height<1 or width*height>1500000:return None
    # Cropped regions only; screenshots never enter an AI request or an export.
    png=await session.page.screenshot(type='png',clip={'x':x,'y':y,'width':width,'height':height},timeout=3000)
    if len(png)>800000:return None
    return {'png':png,'viewport':{'width':vp['width'],'height':vp['height']},'clip':{'x':0,'y':0,'width':width,'height':height},'nodes':evidence['nodes']}
