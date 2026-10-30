"""Bounded compiler and opaque-origin HTML renderer; no generated code runs in Python/Node."""
import asyncio
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import secrets
from ..browser_manager import SessionError

ROOT=Path(__file__).resolve().parents[3]
COMPILE_LOCK=asyncio.Semaphore(2)

async def compile_project(project):
    if COMPILE_LOCK.locked():raise SessionError('Preview compiler is busy. Try again shortly.',429,'preview-busy')
    async with COMPILE_LOCK:
        try:
            proc=await asyncio.create_subprocess_exec('node',str(ROOT/'scripts/compile-studio.mjs'),stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,limit=1048576)
        except OSError as exc:raise SessionError('Node/compiler is unavailable. Run setup.sh.',503,'compiler-unavailable') from exc
        try:
            async with asyncio.timeout(8):out,_=await proc.communicate(project.model_dump_json().encode())
        except BaseException:
            if proc.returncode is None:proc.kill()
            await proc.wait();raise
        if len(out)>900000:raise SessionError('Compiled output exceeds the preview budget.',422,'code-invalid')
        try:result=json.loads(out)
        except ValueError:raise SessionError('Compiler failed. Check server dependencies.',503,'compiler-unavailable') from None
        if proc.returncode or 'error' in result:raise SessionError(result.get('error','Invalid code.'),422,'code-invalid')
        return result['js']

class SafeMarkup(HTMLParser):
    """Only inert HTML + safe attributes. The compiled script is added separately."""
    blocked={'script','style','iframe','frame','object','embed','base','meta','link','svg','math','template','noscript'}
    void={'area','br','col','hr','img','input','source','wbr'}
    allowed=set('html head title body div section article header footer main nav aside h1 h2 h3 h4 h5 h6 p span strong em small button a ul ol li label figure figcaption blockquote pre code hr br details summary img input textarea select option form table thead tbody tr td th'.split())
    def __init__(self):super().__init__(convert_charrefs=True);self.parts=[];self.skip=[]
    def handle_starttag(self,tag,attrs):
        if self.skip:
            if tag not in self.void and tag not in {'meta','link','base','embed'}:self.skip.append(tag)
            return
        if tag in self.blocked:
            if tag not in {'meta','link','base','embed'}:self.skip.append(tag)
            return
        if tag not in self.allowed or tag in {'html','head','body'}:return
        safe=[]
        for key,value in attrs:
            value=value or ''
            if key in {'id','class','role','type','disabled','placeholder','tabindex','open','colspan','rowspan','alt','width','height'} or key.startswith(('aria-','data-')):
                safe.append((key,value))
            elif key=='style':
                from .local import declarations
                styles={}
                for part in value.split(';'):
                    k,sep,v=part.partition(':')
                    if sep:styles[k.strip()]=v.strip()
                cleaned=declarations(styles)
                if cleaned:safe.append(('style',cleaned))
            elif key=='href' and value.startswith('#'):safe.append((key,value))
            elif key=='src' and tag=='img' and value.startswith(('data:image/png;base64,','data:image/jpeg;base64,','data:image/webp;base64,')):safe.append((key,value))
        self.parts.append('<'+tag+''.join(' '+k+'="'+html.escape(v,quote=True)+'"' for k,v in safe)+'>')
    def handle_endtag(self,tag):
        if self.skip:
            if tag==self.skip[-1]:self.skip.pop()
            return
        if tag in self.allowed and tag not in self.void|{'html','head','body'}:self.parts.append('</'+tag+'>')
    def handle_data(self,data):
        if not self.skip:self.parts.append(html.escape(data))
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in self.void:self.handle_endtag(tag)

def document(project,js,bridge_token=None):
    nonce=secrets.token_urlsafe(24)
    csp=f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'unsafe-inline'; img-src data:; font-src 'none'; connect-src 'none'; media-src 'none'; frame-src 'none'; worker-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; sandbox allow-scripts; frame-ancestors 'self'"
    parser=SafeMarkup();parser.feed(project.files['index.html'])
    markup=''.join(parser.parts)
    # Prevent closing the trusted script/style boundaries with edited source text.
    js=js.replace('</','<\\/')
    css=project.files['style.css'].replace('<','\\3c ')
    bridge="""addEventListener('error',e=>parent.postMessage({type:'veyra-preview-error',message:String(e.message).slice(0,600)},'*'));addEventListener('unhandledrejection',e=>parent.postMessage({type:'veyra-preview-error',message:String(e.reason).slice(0,600)},'*'));addEventListener('click',e=>{const a=e.target.closest('a');if(a&&!a.getAttribute('href')?.startsWith('#'))e.preventDefault();});setTimeout(()=>parent.postMessage({type:'veyra-preview-metrics',overflow:document.documentElement.scrollWidth>innerWidth,nodes:Array.from(document.querySelectorAll('[data-veyra-node]')).slice(0,55).map(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {id:Number(e.dataset.veyraNode),width:r.width,height:r.height,fontSize:s.fontSize,color:s.color}})},'*'),120);"""
    instrumentation=(Path(__file__).with_name('bridge.js').read_text().replace('__BRIDGE_TOKEN__',json.dumps(bridge_token or 'disabled')))
    bridge+=instrumentation
    return '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>'+css+'</style></head><body><script nonce="'+nonce+'">'+bridge+'</script>'+markup+'<script nonce="'+nonce+'">'+js+'</script></body></html>',csp
