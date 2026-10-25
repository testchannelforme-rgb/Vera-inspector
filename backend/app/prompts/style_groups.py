"""Lossless factoring of included nodes' sanitized computed CSS.

Shared means equal measured strings, not proven inheritance or a CSS class.
Merge referenced groups then node-specific values to reconstruct every property.
"""
from collections import defaultdict

LAYOUT=set('display position width height min-width max-width min-height max-height box-sizing margin-top margin-right margin-bottom margin-left padding-top padding-right padding-bottom padding-left gap row-gap column-gap flex-direction flex-wrap flex-grow flex-shrink flex-basis justify-content align-items align-self grid-template-columns grid-template-rows overflow overflow-x overflow-y z-index transform object-fit object-position'.split())
TYPOGRAPHY=set('font-family font-size font-weight font-style line-height letter-spacing text-align text-transform text-decoration'.split())


def category(key):
    if key in LAYOUT:return 'layout'
    if key in TYPOGRAPHY:return 'typography'
    if key.startswith(('animation-','transition-')):return 'motion'
    return 'appearance'


def factor_styles(nodes):
    pairs=defaultdict(list)
    for n in nodes:
        for key,value in n.get('styles',{}).items():pairs[(key,value)].append(n['id'])
    sets=defaultdict(dict);specific={n['id']:{} for n in nodes}
    for (key,value),members in sorted(pairs.items()):
        if len(members)>=2:sets[(category(key),tuple(members))][key]=value
        else:specific[members[0]][key]=value
    groups={};refs={n['id']:[] for n in nodes}
    for index,((kind,members),styles) in enumerate(sorted(sets.items()),1):
        name='S'+str(index);groups[name]={'category':kind,'nodes':list(members),'styles':styles}
        for ident in members:refs[ident].append(name)
    return {'groups':groups,'nodes':{n['id']:{'refs':refs[n['id']],'specific':specific[n['id']]} for n in nodes}}


def reconstruct(factored, ident):
    node=factored['nodes'][ident];result={}
    for ref in node['refs']:result.update(factored['groups'][ref]['styles'])
    result.update(node['specific']);return result
