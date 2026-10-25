"""Minimize website data before local generation or any provider transmission."""
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from ..browser_manager import SessionError
from .selection import selection_plan

BOUNDARY_JS = Path(__file__).with_name('boundary.js').read_text()
COLLECT_JS = Path(__file__).with_name('collect.js').read_text().replace('__VEYRA_BOUNDARY_FUNCTION__', '('+BOUNDARY_JS+')')
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
            if k in ('visited','candidates','returned','elapsedMs','method','selectedReturned')}
    cleaned=[]
    for item in raw.get('nodes', [])[:55]:
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
                'disabled':item['accessibility'].get('disabled',False) is True,'method':'DOM attributes only; accessible name not verified'}
        if node['image']:
            node['image'] = {**node['image'], 'alt':clean_text(node['image'].get('alt',''),160)}
        node['styles']={};changed=[]
        for k,v in list(item.get('styles',{}).items())[:100]:
            if not isinstance(v,str):continue
            key=clean_text(k,80)
            if 'url(' in v.lower():changed.append(key);continue
            # Preserve internal CSS whitespace; apply credential redaction, then bound it.
            value=re.sub(r'[\x00-\x08\x0b-\x1f\x7f]','',v)[:2000]
            for pattern,replacement in REDACTIONS:value=re.sub(pattern,replacement,value)
            value=value[:180]
            node['styles'][key]=value
            if value!=v:changed.append(key)
        node['styleTruncatedProperties']=[clean_text(k,80) for k in item.get('styleTruncatedProperties',[])[:100]]
        node['sanitizedProperties']=changed
        cleaned.append(node)
    # Budget admission is importance-based and accepts whole ancestor chains.
    # Six KB remain reserved for a bounded existing hover observation.
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
