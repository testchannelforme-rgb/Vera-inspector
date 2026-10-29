"""Evidence-driven offline reconstruction. Never labelled as AI output."""
import html
import json
import re
from ..prompts.css_safety import sanitize_css
from .schemas import Project

TAGS=set('div section article header footer main nav aside h1 h2 h3 h4 h5 h6 p span strong em small button a ul ol li label figure figcaption blockquote pre code hr br details summary'.split())
VOID={'hr','br'}

def declarations(styles):
    result=[]
    for key,value in styles.items():
        if not re.fullmatch(r'-?[a-z][a-z-]{0,60}',key) or key in ('animation-name','animation-duration','animation-delay','animation-iteration-count'):continue
        safe,_,_=sanitize_css(key,value,[])
        if safe is None or any(c in safe for c in '{};<>') or 'omitted' in safe:continue
        result.append(f'{key}: {safe}')
    return '; '.join(result)

def reconstruct(evidence, output):
    nodes=evidence['nodes'];by_id={n['id']:n for n in nodes};children={}
    for n in nodes:children.setdefault(n.get('parent'),[]).append(n)
    warnings=['Local measured reconstruction; no AI model was called.',
              'Only collected visible nodes are included. Breakpoints and unobserved application behavior are unknown.',
              'Asset URLs and private input values are excluded. Missing images use labelled placeholders; original fonts may fall back.',
              'Navigation targets, backend actions and unobserved scroll triggers are not recovered.']
    if evidence.get('truncated'):warnings.append('Inspection was truncated; some content is missing.')
    rules=['* { box-sizing: border-box; }','body { margin: 0; }', '.veyra-root { max-width: 100%; overflow-wrap: anywhere; }',
           '.asset-placeholder { display: grid; place-items: center; border: 1px dashed currentColor; min-height: 40px; }']
    def emit(n):
        cls='v'+str(n['id']);tag=n['tag'] if n['tag'] in TAGS else 'div'
        styles=dict(n.get('styles',{}));visual=n.get('visual',{})
        # Keep measured layout but allow the outer box to fit the preview viewport.
        if n is nodes[0]:styles.update({'max-width':'100%','position':'relative','margin-top':'0px','margin-left':'0px'})
        rules.append('.'+cls+' { '+declarations(styles)+'; }')
        for p in visual.get('pseudoElements',[]):
            if p.get('contentKind') in ('empty','text'):
                content=p.get('content','').strip('"\'')
                rules.append('.'+cls+p['pseudo']+' { content: '+json.dumps(content)+'; '+declarations(p.get('styles',{}))+'; }')
        text=html.escape(n.get('text',''))
        attrs=f' class="{cls}" data-veyra-node="{n["id"]}"'
        if n.get('accessibility',{}).get('label'):attrs+=' aria-label="'+html.escape(n['accessibility']['label'],quote=True)+'"'
        if n['tag'] in ('img','svg','canvas','video'):
            attrs=f' class="{cls} asset-placeholder" role="img" aria-label="Asset unavailable"'
            text=html.escape((n.get('image') or {}).get('alt','') or 'Asset unavailable')
        if tag=='button':attrs+=' type="button"'
        if tag=='a':attrs+=' href="#"'
        if tag in VOID:return f'<{tag}{attrs}>'
        return f'<{tag}{attrs}>{text}'+''.join(emit(c) for c in sorted(children.get(n['id'],[]),key=lambda c:c.get('siblingIndex',c['id'])))+f'</{tag}>'
    markup=''.join(emit(n) for n in nodes if n.get('parent') not in by_id)
    hover=evidence.get('hover')
    if hover and not hover.get('baselineWasAlreadyHovered'):
        selected=next((n for n in nodes if n.get('selected')),nodes[0])
        changes={k:v['observed'] for k,v in hover.get('changes',{}).items() if 'observed' in v}
        rules.append('.v'+str(selected['id'])+':is(:hover,:focus-visible) { '+declarations(changes)+'; }')
    if any(n.get('styles',{}).get('animation-name','none')!='none' for n in nodes):warnings.append('Animation names were observed but original keyframe rules were not recovered; those animations are omitted.')
    rules.append('@media (max-width: 640px) { .veyra-root { width: 100%; } .veyra-root img { max-width: 100%; } }')
    css='\n\n'.join(rules)+'\n'
    js="// Original navigation and backend actions are unknown.\ndocument.querySelectorAll('a[href=\"#\"]').forEach(a => a.addEventListener('click', e => e.preventDefault()));\n"
    if output=='vanilla':
        files={'index.html':'<!doctype html>\n<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Veyra recreation</title><link rel="stylesheet" href="style.css"></head><body><div class="veyra-root">'+markup+'</div><script src="script.js"></script></body></html>\n','style.css':css,'script.js':js}
    else:
        # HTML is escaped static content produced by this module, not source-page HTML.
        jsx=markup.replace('class=','className=')
        jsx=re.sub(r'<(hr|br)([^>]*?)>',r'<\1\2 />',jsx)
        # Text braces are JSX delimiters; convert all literal text to expressions via a parser.
        from html.parser import HTMLParser
        class JSX(HTMLParser):
            def __init__(self):super().__init__(convert_charrefs=True);self.parts=[]
            def handle_starttag(self,tag,attrs):
                a=' '.join(('className' if k.lower()=='classname' else k)+'={'+json.dumps(v or '')+'}' for k,v in attrs)
                self.parts.append('<'+tag+(' '+a if a else '')+(' />' if tag in VOID else '>'))
            def handle_endtag(self,tag):
                if tag not in VOID:self.parts.append('</'+tag+'>')
            def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs)
            def handle_data(self,data):self.parts.append('{'+json.dumps(data)+'}')
        parser=JSX();parser.feed(jsx);jsx=''.join(parser.parts)
        files={'App.jsx':'import React from "react";\nimport "./style.css";\n\nexport default function App() {\n  return <div className="veyra-root">'+jsx+'</div>;\n}\n',
               'main.jsx':'import React from "react";\nimport { createRoot } from "react-dom/client";\nimport App from "./App.jsx";\ncreateRoot(document.getElementById("root")).render(<App />);\n',
               'style.css':css,'index.html':'<!doctype html>\n<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Veyra recreation</title></head><body><div id="root"></div><script type="module" src="/main.jsx"></script></body></html>\n',
               'package.json':json.dumps({'name':'veyra-recreation','version':'1.0.0','private':True,'type':'module','scripts':{'dev':'vite --host 127.0.0.1','build':'vite build','preview':'vite preview --host 127.0.0.1'},'dependencies':{'react':'19.1.1','react-dom':'19.1.1'},'devDependencies':{'vite':'8.3.5'}},indent=2)+'\n',
               'vite.config.js':'export default {};\n'}
    files['README.md']='# Veyra recreation\n\n'+('Open index.html in a browser or serve this directory with `python3 -m http.server 8080`.' if output=='vanilla' else 'Use Node 22.12+ or 24 LTS. Run `npm install`, then `npm run dev`. Build with `npm run build`. No API key is required.')+'\n\n'+ '\n'.join('- '+w for w in warnings)+'\n'
    return Project(format=output,files=files),warnings
