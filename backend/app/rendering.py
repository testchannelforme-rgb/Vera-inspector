import asyncio
import time

# Geometric/content evidence, not a guarantee that a site's app is ready.
READINESS_JS='''() => {
 const body=document.body;
 if(!body)return {hasBody:false,visibleCandidates:0,textLength:0,readyState:document.readyState};
 let count=0;
 for(const el of body.querySelectorAll('*')) {
  if(count>=8)break;
  if(['SCRIPT','STYLE','NOSCRIPT','TEMPLATE','META','LINK'].includes(el.tagName))continue;
  const r=el.getBoundingClientRect(),s=getComputedStyle(el);
  if(r.width>1&&r.height>1&&s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity)>0)count++;
 }
 const publicText=(body.innerText||'').slice(0,5000).toLowerCase();
 const accessChecks=['verify you are human','access denied','checking your browser','complete the captcha','unusual traffic'].filter(s=>publicText.includes(s));
 return {hasBody:true,title:document.title.slice(0,200),accessChecks,visibleCandidates:count,textLength:(body.innerText||'').trim().length,readyState:document.readyState,
  imagesReady:[...document.images].filter(i=>i.complete&&i.naturalWidth>0).length,canvasCount:document.querySelectorAll('canvas,svg').length};
}'''


async def settle_page(page,budget_ms,diagnostics=None):
    deadline=time.monotonic()+budget_ms/1000
    evidence={}
    # A bounded readiness window gives SPAs time to hydrate. Never wait forever
    # for networkidle; analytics, streaming and polling may never become idle.
    while True:
        evidence=await page.evaluate(READINESS_JS)
        elapsed=budget_ms-round(max(0,deadline-time.monotonic())*1000)
        content = evidence.get('textLength',0)>40 or evidence.get('imagesReady',0)>0 or evidence.get('canvasCount',0)>0
        quiet = diagnostics is None or (not diagnostics.inflight and time.monotonic()-diagnostics.last_activity>=.6)
        if content and evidence.get('readyState')=='complete' and elapsed>=2000 and quiet:
            break
        if time.monotonic()>=deadline:break
        await asyncio.sleep(min(.2,max(0,deadline-time.monotonic())))
    # Fonts can change element geometry. Waiting is bounded and does not alter CSS.
    try:await page.evaluate('()=>Promise.race([document.fonts.ready,new Promise(r=>setTimeout(r,350))]).then(()=>true)')
    except Exception:pass
    return {**evidence,'observationWindowMs':budget_ms,'observedElapsedMs':min(budget_ms,max(0,elapsed)),
            'empty':not evidence.get('visibleCandidates') and not evidence.get('textLength')}
