"""Deterministic CSS/geometry interpretations, never pixel-verified appearance."""

def intersects(a,b):
    if not isinstance(a,dict) or not isinstance(b,dict):return 0
    try:
        area=min(a['width']*a['height'],b['width']*b['height'])
        overlap=max(0,min(a['x']+a['width'],b['x']+b['width'])-max(a['x'],b['x']))*max(0,min(a['y']+a['height'],b['y']+b['height'])-max(a['y'],b['y']))
        return overlap/area if area>0 else 0
    except (KeyError,TypeError):return 0


def paint_features(styles):
    if not isinstance(styles,dict):return []
    result=[]
    image=styles.get('background-image','none')
    if image not in ('none',''):
        result.append('background layers; asset references may be omitted')
    if styles.get('background-clip')=='text' or styles.get('-webkit-background-clip')=='text':result.append('background clipped to text')
    if styles.get('-webkit-text-fill-color') in ('transparent','rgba(0, 0, 0, 0)'):result.append('transparent text fill (computed color alone does not establish visible glyph color)')
    for k in ('text-shadow','box-shadow','filter','backdrop-filter','mask-image','-webkit-mask-image','clip-path','transform'):
        if styles.get(k,'none') not in ('none',''):result.append(k)
    if styles.get('-webkit-text-stroke-width','0px') not in ('0px','0',''):result.append('text stroke')
    if styles.get('mix-blend-mode','normal')!='normal':result.append('blend mode')
    if styles.get('opacity','1')!='1':result.append('opacity')
    if styles.get('isolation','auto')=='isolate':result.append('isolation')
    return result


def coalesce(pairs):
    groups=[]
    for pair in pairs:
        related=[g for g in groups if g['text']==pair['text'] and set(g['nodes'])&set(pair['nodes'])]
        group=dict(pair);group['nodes']=list(pair['nodes'])
        for existing in related:
            group['nodes']=list(dict.fromkeys(existing['nodes']+group['nodes']));groups.remove(existing)
        groups.append(group)
    return groups


def relationships(nodes):
    result=[]
    for index,a in enumerate(nodes[:55]):
        text=' '.join(a.get('text','').split())
        if len(text)<4:continue
        for b in nodes[index+1:55]:
            if ' '.join(b.get('text','').split())!=text or intersects(a.get('box'),b.get('box'))<.8:continue
            sa,sb=a.get('styles',{}),b.get('styles',{})
            related=a.get('parent')==b.get('parent') or a.get('parent')==b.get('id') or b.get('parent')==a.get('id')
            indicators=any(s.get('position') in ('absolute','fixed') or s.get('transform','none') not in ('none','') or s.get('opacity','1')!='1' or s.get('background-clip')=='text' or s.get('-webkit-text-fill-color') in ('transparent','rgba(0, 0, 0, 0)') for s in (sa,sb))
            if related and indicators:
                result.append({'nodes':[a['id'],b['id']],'text':text,'basis':'same direct copy, overlapping bounding rectangles, related DOM and layering CSS',
                    'uncertainty':'may be a visual composition, state variants or accessibility alternatives; preserve both nodes/styles; no pixel occlusion or state activation verified'})
                if len(result)>=8:return coalesce(result)
    return coalesce(result)


def summary_lines(evidence,nodes,quote):
    lines=['### Visual Composition Summary',
        'Observed CSS belongs to its named owner. Context is outside the requested content scope. Interpretations below are hypotheses; no pixel color, complete paint order or occlusion was measured.']
    for n in nodes:
        features=paint_features(n.get('styles',{}))
        if features:lines.append(f'- Node {n["id"]}: CSS indicators: '+', '.join(features)+'. Exact values follow in shared/node-specific style maps.')
        if n.get('visual',{}).get('pseudoElements'):lines.append(f'- Node {n["id"]} owns generated pseudo-element CSS; recreate that decoration on its owner, not as unrelated content.')
    lines.append('For text-clipped backgrounds/transparent text fill, preserve the clip/fill relationship on that owner; do not render its computed color as an additional opaque text layer.')
    context=evidence.get('visualContext',{})
    for owner in context.get('owners',[]):
        ref=owner['owner'];relation=owner['relation']
        lines.append(f'- Context {ref} ({relation}, <{owner["tag"]}>): observed paint/layout CSS at this external owner. Do not assign its background to the selected child or rebuild unrelated surrounding content.')
        if owner.get('sameDirectText'):lines.append(f'  Inference: {ref} may be an overlapping text layer/alternative of the target; retain attribution and verify visually. Matching copy alone is not a deduplication rule.')
    for relation in relationships(nodes):lines.append('- Inferred text-layer relationship '+quote({k:v for k,v in relation.items() if k!='text'})+'. Do not turn it blindly into independent flow headings or collapse the DOM.')
    if not nodes:lines.append('No visual node evidence available.')
    return lines


def detail_lines(evidence,nodes,quote):
    lines=['### Attributed visual context and pseudo-elements',
        'These records contain sanitized computed values, not measured pseudo rectangles or a browser paint tree. Placeholder/reference tokens are not executable CSS. Background layer order is CSS order; a gradient or asset belongs to its recorded owner.']
    for n in nodes:
        for pseudo in n.get('visual',{}).get('pseudoElements',[]):lines.append(f'- Owner Node {n["id"]}{pseudo["pseudo"]}: '+quote(pseudo))
    context=evidence.get('visualContext',{})
    for owner in context.get('owners',[]):lines.append('- Context owner '+owner['owner']+': '+quote(owner))
    if context:lines.append('Visual context coverage: '+quote(context.get('coverage',{}))+'. No more distant/omitted background is established.')
    return lines
