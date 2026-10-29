"""Validate/minimize optional visual evidence before rendering or provider use."""
import json
from itertools import islice
import math
import re
from .css_safety import sanitize_css,UNSAFE

KEYS=set('background-color background-image background-position background-size background-repeat background-clip background-origin background-attachment background-blend-mode -webkit-background-clip -webkit-text-fill-color -webkit-text-stroke-width -webkit-text-stroke-color text-shadow mix-blend-mode isolation filter backdrop-filter mask-image -webkit-mask-image mask-size mask-position mask-repeat mask-clip mask-origin mask-mode mask-composite clip-path position z-index opacity transform transform-origin overflow overflow-x overflow-y pointer-events box-shadow border-radius top left right bottom width height display color font-family font-size font-weight line-height'.split())
CRITICAL=('background-image','background-color','background-clip','-webkit-text-fill-color','-webkit-text-stroke-width','text-shadow','mask-image','position','z-index','opacity','transform','width','height','color')


def safe_box(box):
    if not isinstance(box,dict):return None
    if not all(isinstance(box.get(k),(int,float)) and not isinstance(box.get(k),bool) and math.isfinite(box[k]) and abs(box[k])<=1e9 for k in ('x','y','width','height')):return None
    if box['width']<0 or box['height']<0:return None
    return {k:box[k] for k in ('x','y','width','height')}


def paint_record(raw,clean,redactions):
    raw=raw if isinstance(raw,dict) else {}
    fields=raw.get('styles',{});fields=fields if isinstance(fields,dict) else {}
    styles={};changed=[];cut=[];omitted=[]
    for k in sorted(set(islice(fields,120))&KEYS,key=lambda k:(k not in CRITICAL,k)):
        value,modified,limited=sanitize_css(k,fields[k],redactions)
        if modified:changed.append(k)
        if limited:cut.append(k)
        if value is None:continue
        if len(json.dumps({**styles,k:value},ensure_ascii=True).encode())>2500:omitted.append(k);continue
        styles[k]=value
    names=lambda name:[clean(k,80) for k in raw.get(name,[])[:60] if isinstance(k,str)] if isinstance(raw.get(name),list) else []
    return {'styles':styles,'sanitizedProperties':sorted(set(changed+names('sanitizedProperties'))),
            'styleTruncatedProperties':sorted(set(cut+names('styleTruncatedProperties'))),
            'omittedProperties':sorted(set(omitted+[k for k in names('omittedProperties') if k in KEYS]))}


def sanitize_visual(raw,clean,redactions,budget=None):
    budget=budget if budget is not None else {'remaining':8}
    raw=raw if isinstance(raw,dict) else {};result={'pseudoElements':[],'omitted':0,'omittedProperties':[k for k in raw.get('omittedProperties',[])[:60] if isinstance(k,str) and k in KEYS] if isinstance(raw.get('omittedProperties'),list) else []}
    pseudos=raw.get('pseudoElements',[]);pseudos=pseudos if isinstance(pseudos,list) else []
    seen=set()
    for p in pseudos[:2]:
        if not isinstance(p,dict) or p.get('pseudo') not in ('::before','::after') or p['pseudo'] in seen:continue
        if budget['remaining']<=0:result['omitted']+=1;continue
        seen.add(p['pseudo']);budget['remaining']-=1
        content=p.get('content','');content=content if isinstance(content,str) else ''
        kind=p.get('contentKind') if p.get('contentKind') in ('empty','text','reference','unresolved') else 'unresolved'
        if len(content)>8192 or UNSAFE.search(content) or re.search(r'(?:attr|counter|counters)\s*\(',content,re.I):
            content='[content reference omitted]';kind='reference'
        result['pseudoElements'].append({'pseudo':p['pseudo'],'contentKind':kind,'content':clean(content,160),
            **paint_record(p,clean,redactions),'geometry':'computed dimensions/offsets only; pseudo bounding rectangle not measured'})
    result['omitted']+=max(0,len(pseudos)-2)
    return result


def sanitize_context(raw,clean,redactions,budget=None):
    raw=raw if isinstance(raw,dict) else {};owners=raw.get('owners',[]);owners=owners if isinstance(owners,list) else []
    result={'owners':[],'coverage':{},'method':'CSS and bounding-box context only; no pixel colors or paint order verified'}
    count=0
    for item in owners[:8]:
        if not isinstance(item,dict) or item.get('relation') not in ('ancestor','nearby-decoration','nearby-text-layer'):continue
        if not re.fullmatch(r'(?:ancestor:[1-6]|nearby:[0-9])',str(item.get('owner',''))):continue
        box=safe_box(item.get('box'));distance=item.get('distance')
        if box is None or not isinstance(distance,int) or isinstance(distance,bool) or not 1<=distance<=6:continue
        paint=paint_record(item,clean,redactions);visual=sanitize_visual(item,clean,redactions,budget)
        omitted=sorted(set(paint['omittedProperties']+visual['omittedProperties']))
        record={'owner':item['owner'],'relation':item['relation'],'distance':distance,'tag':clean(item.get('tag',''),40),
                'box':box,**paint,**visual,'omittedProperties':omitted}
        if item.get('sameDirectText') is True:record['sameDirectText']=True
        if item.get('hiddenFromAT') is True:record['hiddenFromAT']=True
        if len(json.dumps({**result,'owners':result['owners']+[record]},ensure_ascii=True).encode())>5500:count+=1;continue
        result['owners'].append(record)
    coverage=raw.get('coverage',{});coverage=coverage if isinstance(coverage,dict) else {}
    for k in ('contextOmitted','pseudoOmitted'):result['coverage'][k]=coverage.get(k,False) is True
    for k in ('contextChecks','pseudoCount'):
        n=coverage.get(k,0);result['coverage'][k]=min(100,max(0,n)) if isinstance(n,int) and not isinstance(n,bool) else 0
    result['coverage']['ownersOmitted']=count+max(0,len(owners)-8)
    return result
