"""A bounded evidence inventory. Counts are coverage, never an accuracy score."""
import math
from .presets import selected_evidence
from .composition import relationships


def quality_report(evidence, request, warnings):
    chosen, sampling = selected_evidence(evidence, request)
    nodes = evidence.get('nodes', [])
    valid_box = lambda n: all(isinstance(n.get('box', {}).get(k), (int, float)) and not isinstance(n['box'][k], bool) and math.isfinite(n['box'][k]) for k in ('x', 'y', 'width', 'height'))
    styles = sum(len(n.get('styles', {})) for n in chosen)
    modified = sum(len(set(n.get('sanitizedProperties', [])) | set(n.get('styleTruncatedProperties', []))) for n in chosen)
    pseudo = sum(len(n.get('visual', {}).get('pseudoElements', [])) for n in chosen)
    images = [n for n in chosen if n.get('image')]
    observed = [f'{sum(valid_box(n) for n in chosen)} described nodes have captured bounding rectangles.',
                f'{styles} sanitized computed CSS entries across described nodes; {modified} property flags indicate sanitization or length limits.',
                f'{pseudo} owner-attributed pseudo-element records; their bounding rectangles were not measured.']
    viewport = evidence.get('viewport', {})
    if isinstance(viewport.get('width'), (int, float)) and isinstance(viewport.get('height'), (int, float)):
        observed.insert(0, f'One captured viewport: {viewport["width"]} × {viewport["height"]} CSS px.')
    inferred = ['Component extraction and reusable tokens are implementation recommendations, not recovered source code.']
    if request.scope == 'section':
        inferred.append('Section boundaries are heuristics; verify the chosen local region against the screenshot.')
    if relationships(chosen):
        inferred.append('Potential overlapping text compositions are hypotheses; keep distinct DOM nodes and styles until verified.')
    missing = ['Exact responsive breakpoints and alternate viewport layouts.',
               'Original authored stylesheet, font files and font licensing.',
               'Complete paint order, pixel occlusion and canvas/iframe/closed-shadow internals.',
               'Navigation destinations, activated controls and hidden interaction states.']
    if evidence.get('hover'):
        observed.append('An actual prior hover capture is attached; see its baseline, timestamps and measured changes in section 5.')
        if evidence['hover'].get('baselineWasAlreadyHovered'):
            missing.append('A resting hover baseline; the attached baseline was already hovered.')
    else:
        missing.append('Hover endpoints and timing: use Capture hover, then regenerate.')
    tasks = []
    for n in images:
        tasks.append(f'Node {n["id"]}: supply an authorized image asset; verify captured alt text and object-fit. The original URL was omitted.')
    for n in chosen:
        if n.get('tag') in ('svg', 'canvas', 'video'):
            tasks.append(f'Node {n["id"]}: supply the original {n["tag"]} content or use a clearly labelled placeholder.')
        if any('[asset' in str(v).lower() or '[url' in str(v).lower() for v in n.get('styles', {}).values()):
            tasks.append(f'Node {n["id"]}: resolve omitted CSS image/mask asset references without guessing URLs.')
    if not tasks:
        tasks.append('No specific asset task was identified in the described sample; this does not establish asset completeness.')
    tasks.extend(['Verify font availability and licensing; document any substituted font.',
                  'Inspect additional viewports before claiming responsive fidelity.',
                  'Verify keyboard/focus, contrast and reduced-motion behavior in the implementation.'])
    context = evidence.get('visualContext', {}).get('coverage', {})
    truncated = bool(evidence.get('truncated') or sampling['omitted'] or context.get('contextOmitted') or context.get('ownersOmitted'))
    if not chosen:
        missing.insert(0, 'Usable connected node evidence. Select a target and capture again before recreating it.')
    return {'schemaVersion': '1', 'preset': request.preset,
            'coverage': {'collectedNodes': len(nodes), 'describedNodes': len(chosen),
                         'rendererOmittedNodes': sampling['omitted'], 'invalidPaths': sampling['invalid'],
                         'computedStyleEntries': styles, 'flaggedProperties': modified,
                         'pseudoRecords': pseudo, 'imageRecords': len(images),
                         'truncated': truncated, 'selectedOmitted': bool(sampling.get('selectedOmitted') or evidence.get('sampling', {}).get('selectedOmitted'))},
            'observed': observed, 'inferred': inferred, 'missing': missing,
            'assetChecklist': list(dict.fromkeys(tasks))[:32],
            'warnings': list(dict.fromkeys(warnings))[:40],
            'limitations': ['Evidence inventory only; no pixel similarity, quality percentage or accessibility certification was measured.',
                            'Counts refer to described nodes. Collection and byte budgets can omit further evidence.']}
