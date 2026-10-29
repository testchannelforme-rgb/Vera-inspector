"""Minimize website data before local generation or any provider transmission."""
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from ..browser_manager import SessionError
from .selection import selection_plan
from .css_safety import sanitize_css
from .visual_evidence import sanitize_context,sanitize_visual

BOUNDARY_JS = Path(__file__).with_name('boundary.js').read_text()
COLLECT_JS = Path(__file__).with_name('collect.js').read_text().replace('__VEYRA_BOUNDARY_FUNCTION__', '('+BOUNDARY_JS+')').replace('__VEYRA_VISUAL_FUNCTION__', Path(__file__).with_name('visual.js').read_text())
MAX_EVIDENCE_BYTES = 48000
# Best effort redaction complements collection exclusions; it is not PII classification.
REDACTIONS = [
    (r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[email omitted]'),
    (r'(?i)\b(?:bearer\s+\S+|(?:api[_ -]?key|password|token|secret)\s*[:=]\s*\S+)', '[credential-like text omitted]'),
    (r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b', '[token omitted]'),
    (r'\b(?:sk-|ghp_|github_pat_)[A-Za-z0-9_-]{12,}\b', '[token omitted]'),
    (r'\b[0-9a-fA-F]{32,}\b', '[identifier omitted]'),
    (r'(?i)(?:https?://|www\.)\S+', '[URL omitted]'),
]


def clean_text(value, limit=240):
    text = re.sub(r'[\x00-\x08\x0b-\x1f\x7f]', '', str(value))[:2000]
    for pattern, replacement in REDACTIONS:
        if '@' in pattern and '@' not in text:continue
        text = re.sub(pattern, replacement, text)
    # Newlines in page copy must never become prompt headings/instructions.
    return ' '.join(text.split())[:limit]


def sanitize(raw, url, hover=None):
    evidence = {k: raw[k] for k in ('schemaVersion','scope','boundary','viewport','scroll','truncated','excluded')}
    evidence['boundary'] = clean_text(evidence['boundary'], 500)
    parsed = urlsplit(url)
    evidence['source'] = {'origin': f'{parsed.scheme}://{parsed.hostname}', 'capturedAt': datetime.now(timezone.utc).isoformat()}
    if raw.get('boundaryDecision'):
        # All collector reason labels are static; sanitize anyway before AI transmission.
        decision=raw['boundaryDecision']
        evidence['boundaryDecision']={k:decision[k] for k in ('method','rootTag','distance','score')}
        evidence['boundaryDecision']['reasons']=[clean_text(v,100) for v in decision.get('reasons',[])[:8]]
        evidence['boundaryDecision']['candidates']=[{k:clean_text(v,100) if isinstance(v,str) else v
            for k,v in c.items() if k in ('tag','distance','score','rejected')}
            for c in decision.get('candidates',[])[:11]]
    if raw.get('collection'):
        evidence['collection']={k:v for k,v in raw['collection'].items()
            if k in ('visited','candidates','returned','elapsedMs','method','selectedReturned','rawCharacterLimit')}
    cleaned=[]
    visual_budget={'remaining':8}
    for item in raw.get('nodes', [])[:55]:
        if not isinstance(item,dict) or not all(k in item for k in ('id','parent','tag','depth','visible','box','behavior','image')):continue
        node = {k: item[k] for k in ('id','parent','tag','depth','visible','box','behavior','image')}
        node['tag'] = clean_text(node['tag'], 40)
        node['text'] = clean_text(item.get('text', ''))
        node['role'] = clean_text(item.get('role') or '', 50)
        node['selected']=item.get('selected',False) is True
        if 'siblingIndex' in item:node['siblingIndex']=item['siblingIndex']
        if item.get('parentRelationship') in ('snapshot-root','dom-child','shadow-host'):node['parentRelationship']=item['parentRelationship']
        if 'viewportIntersection' in item:node['viewportIntersection']=item['viewportIntersection']
        if item.get('accessibility'):
            node['accessibility']={'label':clean_text(item['accessibility'].get('label',''),160),
                'hiddenFromAT':item['accessibility'].get('hiddenFromAT',False) is True,'disabled':item['accessibility'].get('disabled',False) is True,'method':'DOM attributes only; accessible name not verified'}
        if node['image']:
            image=node['image'] if isinstance(node['image'],dict) else {}
            number=lambda v:v if isinstance(v,(int,float)) and not isinstance(v,bool) and 0<=v<=1e9 else None
            node['image']={'present':True,'alt':clean_text(image.get('alt',''),160),'naturalWidth':number(image.get('naturalWidth')),'naturalHeight':number(image.get('naturalHeight'))}
            complete=image.get('complete')
            node['image']['assetStatus']='loaded' if complete is True and (node['image']['naturalWidth'] or 0)>0 else 'unavailable' if complete is True else 'pending' if complete is False else 'unknown'
        node['styles']={};changed=[clean_text(k,80) for k in item.get('sanitizedProperties',[])[:100] if isinstance(k,str)] if isinstance(item.get('sanitizedProperties'),list) else [];limited=[clean_text(k,80) for k in item.get('styleTruncatedProperties',[])[:100] if isinstance(k,str)] if isinstance(item.get('styleTruncatedProperties'),list) else []
        fields=item.get('styles',{})
        for k,v in list(fields.items())[:120] if isinstance(fields,dict) else []:
            key=clean_text(k,80);value,modified,cut=sanitize_css(key,v,REDACTIONS)
            if value is not None:node['styles'][key]=value
            if modified:changed.append(key)
            if cut:limited.append(key)
        node['styleTruncatedProperties']=[clean_text(k,80) for k in sorted(set(limited))[:100]]
        node['sanitizedProperties']=[clean_text(k,80) for k in sorted(set(changed))[:100]]
        if item.get('visual'):node['visual']=sanitize_visual(item['visual'],clean_text,REDACTIONS,visual_budget)
        cleaned.append(node)
    # Budget admission is importance-based and accepts whole ancestor chains.
    # Six KB remain reserved for a bounded existing hover observation.
    if raw.get('visualContext'):evidence['visualContext']=sanitize_context(raw['visualContext'],clean_text,REDACTIONS,visual_budget)
    evidence['nodes']=[]
    base_bytes=len(json.dumps(evidence,ensure_ascii=True).encode())
    cost=lambda n:len(json.dumps(n,ensure_ascii=True).encode())+2
    evidence['nodes'],sample=selection_plan(cleaned,55,cost=cost,budget=MAX_EVIDENCE_BYTES-6500-base_bytes)
    evidence['sampling']=sample
    evidence['truncated'] |= sample['omitted']>0
    evidence['hover'] = hover
    if len(json.dumps(evidence,ensure_ascii=True).encode()) > MAX_EVIDENCE_BYTES:
        evidence['hover']=None;evidence['truncated']=True
    return evidence


def hover_summary(inspection):
    """Only bounded measured differences; never HTML, screenshots or arbitrary keyframes."""
    animation=inspection.animations
    if not animation.hover:return None
    changes={}
    for sample in animation.observations:
        for key, pair in sample.get('changesFromBaseline',{}).items():
            if key not in changes and len(changes)<16 and all('url(' not in str(v).lower() for v in pair.values()):
                changes[key]={k:clean_text(v,160) for k,v in pair.items() if k in ('before','observed')}
    return {'referenceId':inspection.element.referenceId,'requestedIntervalMs':animation.hover['requestedIntervalMs'],
            'actualDurationMs':animation.hover['actualDurationMs'],'baselineWasAlreadyHovered':animation.hover['baselineWasAlreadyHovered'],
            'changes':changes,'geometrySamples':[s['geometry'] for s in animation.observations[:3]]}


async def collect_evidence(session, request):
    async with asyncio.timeout(5):
        return await _collect_evidence(session, request)


async def _collect_evidence(session, request):
    session.check_frame(request.frameId)
    root = session.element
    if request.scope != 'page':
        if root is None or not request.referenceId or request.referenceId != session.reference_id:
            raise SessionError('Select an element in the current preview before generating this scope.',409,'prompt-selection-stale')
        raw = await root.evaluate(COLLECT_JS, request.scope)
    else:
        raw = await session.page.evaluate('() => ('+COLLECT_JS+')(document.body,"page")')
    if (raw.get('boundaryDecision') or {}).get('method')=='selection-required':
        raise SessionError('Select a heading, control or child inside the intended component for section scope. Use page scope for the page wrapper.',422,'prompt-section-too-broad')
    hover = getattr(session,'prompt_hover',None) if request.scope=='element' else None
    evidence = sanitize(raw, session.page.url, hover)
    if not evidence['nodes']:
        raise SessionError('No safe visible content was available for this target. Select another element.',422,'prompt-no-evidence')
    if not any(n['visible'] for n in evidence['nodes']):
        raise SessionError('The target is no longer visible. Refresh the preview and select it again.',409,'prompt-target-hidden')
    return evidence
