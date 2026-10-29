"""Bounded CSS sanitization. URLs are never resolved or sent to a provider."""
import re

MAX_CSS_INPUT=8192
VISUAL_LIMIT=1024
ASSET='present; asset URL omitted'
LAYER_ASSET='[asset reference omitted]'
UNSAFE=re.compile(r'\\|/\*|url\s*\(|image-set\s*\(|(?:https?|data|blob|file|javascript|ftp):|//|www\.',re.I)
GRADIENT=re.compile(r'^(?:repeating-)?(?:linear|radial|conic)-gradient\(',re.I)
VISUAL_KEYS=set('background-image background-position background-size background-repeat background-clip background-origin background-attachment background-blend-mode -webkit-background-clip -webkit-text-fill-color -webkit-text-stroke-width -webkit-text-stroke-color text-shadow mix-blend-mode isolation filter backdrop-filter mask-image -webkit-mask-image mask-size mask-position mask-repeat mask-clip mask-origin mask-mode mask-composite clip-path transform transform-origin box-shadow'.split())


def background_layers(value):
    """Keep layer indices and safe gradients; asset tokens are placeholders, not CSS."""
    if not isinstance(value,str) or len(value)>MAX_CSS_INPUT:return '[CSS omitted: size limit]',True,True
    if value=='none':return value,False,False
    if value in (ASSET,LAYER_ASSET):return value,True,False
    parts=[];start=0;depth=0;quote=None
    for i,c in enumerate(value):
        if c=='\\':return '[CSS omitted: unsupported layers]',True,True
        if quote:
            if c==quote:quote=None
            continue
        if c in ('"',"'"):quote=c
        elif c=='(':
            depth+=1
            if depth>16:return '[CSS omitted: unsupported layers]',True,True
        elif c==')':
            depth-=1
            if depth<0:return '[CSS omitted: unsupported layers]',True,True
        elif c==',' and depth==0:
            parts.append(value[start:i].strip());start=i+1
            if len(parts)>=8:return '[CSS omitted: unsupported layers]',True,True
    if quote or depth:return '[CSS omitted: unsupported layers]',True,True
    parts.append(value[start:].strip())
    safe=[v if v=='none' or (GRADIENT.match(v) and not UNSAFE.search(v) and not any(q in v for q in ('"',"'"))) else LAYER_ASSET for v in parts]
    result=ASSET if safe==[LAYER_ASSET] else ', '.join(safe)
    return result[:VISUAL_LIMIT],result!=value,len(result)>VISUAL_LIMIT


def sanitize_css(key,value,redactions):
    if not isinstance(value,str):return None,True,False
    if len(value)>MAX_CSS_INPUT:return '[CSS omitted: size limit]',True,True
    original=value
    # Normalize control bytes before URL detection, never after the safety check.
    value=re.sub(r'[\x00-\x08\x0b-\x1f\x7f]','',value)
    if key in ('background-image','mask-image','-webkit-mask-image'):
        value,changed,limited=background_layers(value)
    elif UNSAFE.search(value):return None,True,False
    else:changed=limited=False
    cap=VISUAL_LIMIT if key in VISUAL_KEYS else 180
    limited=limited or len(value)>cap
    value=value[:cap]
    value=re.sub(r'[\x00-\x08\x0b-\x1f\x7f]','',value)
    for pattern,replacement in redactions:
        if '@' in pattern and '@' not in value:continue
        value=re.sub(pattern,replacement,value)
    return value[:cap],changed or value!=original,limited or len(value)>cap
