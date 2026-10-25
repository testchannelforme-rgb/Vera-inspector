"""Minimize website data before local generation or any provider transmission."""
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from ..browser_manager import SessionError

COLLECT_JS = Path(__file__).with_name('collect.js').read_text()
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
    parsed = urlsplit(url)
    evidence['source'] = {'origin': f'{parsed.scheme}://{parsed.hostname}', 'capturedAt': datetime.now(timezone.utc).isoformat()}
    evidence['nodes'] = []
    for item in raw.get('nodes', [])[:55]:
        node = {k: item[k] for k in ('id','parent','tag','depth','visible','box','behavior','image')}
        node['tag'] = clean_text(node['tag'], 40)
        node['text'] = clean_text(item.get('text', ''))
        node['role'] = clean_text(item.get('role') or '', 50)
        if node['image']:
            node['image'] = {**node['image'], 'alt':clean_text(node['image'].get('alt',''),160)}
        node['styles'] = {k:clean_text(v,180) for k,v in item['styles'].items() if 'url(' not in v.lower()}
        evidence['nodes'].append(node)
        if len(json.dumps(evidence,ensure_ascii=True).encode()) > MAX_EVIDENCE_BYTES-6000:
            evidence['nodes'].pop();evidence['truncated']=True;break
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
    hover = getattr(session,'prompt_hover',None) if request.scope=='element' else None
    evidence = sanitize(raw, session.page.url, hover)
    if not evidence['nodes']:
        raise SessionError('No safe visible content was available for this target. Select another element.',422,'prompt-no-evidence')
    if not any(n['visible'] for n in evidence['nodes']):
        raise SessionError('The target is no longer visible. Refresh the preview and select it again.',409,'prompt-target-hidden')
    return evidence
