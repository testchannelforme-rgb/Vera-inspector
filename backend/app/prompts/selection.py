"""Prioritize evidence without renumbering nodes or inventing parent relationships."""


def importance(node):
    tag=node.get('tag','');styles=node.get('styles',{});behavior=node.get('behavior',{})
    score=1000 if node.get('selected') else 0
    score+=120 if tag=='h1' else 100 if tag in ('h2','h3','h4','h5','h6') else 0
    score+=90 if tag in ('button','a','input','select','summary') else 0
    score+=85 if tag in ('img','svg','video','canvas') or node.get('image') else 0
    score+=65 if tag=='nav' else 40 if tag in ('main','section','article','header','footer','aside') else 0
    score+=35 if node.get('text') else 0
    score+=20 if styles.get('display') in ('flex','inline-flex','grid','inline-grid') else 0
    score+=12 if styles.get('box-shadow','none') not in ('none','') else 0
    score+=8 if styles.get('background-image','none') not in ('none','') else 0
    score+=10 if behavior.get('expanded') is not None or behavior.get('nativeDisclosure') else 0
    return score


def selection_plan(nodes, maximum, cost=None, budget=None):
    """Return included nodes in source order plus explicit omission diagnostics.

    A whole ancestor chain must fit before accepting a candidate. The selected
    node's chain may exceed the detail count (never the byte budget) so concise
    output still explains what the user selected. Invalid/orphan paths are not
    silently reparented. The first node is the declared snapshot root.
    """
    if not nodes:return [],{'omitted':0,'invalid':0,'contextExpanded':False}
    by_id={};invalid=0
    for n in nodes:
        ident=n.get('id')
        if not isinstance(ident,int) or isinstance(ident,bool) or ident in by_id:
            invalid+=1;continue
        by_id[ident]=n
    root_id=nodes[0].get('id');chosen=set();spent=0;expanded=False
    def path_for(n):
        path=[];seen=set()
        while n is not None:
            ident=n['id']
            if ident in seen:return None
            seen.add(ident);path.append(ident)
            if ident==root_id:return list(reversed(path))
            n=by_id.get(n.get('parent'))
        return None
    valid=[]
    for index,n in enumerate(by_id.values()):
        path=path_for(n)
        if path is None:invalid+=1;continue
        valid.append((n,path,index))
    anchors=[v for v in valid if v[0].get('selected')]
    ranked=sorted(valid,key=lambda v:(v[0]['id']!=root_id,not v[0].get('selected'),-importance(v[0]),v[2]))
    for n,path,_ in ranked:
        missing=[ident for ident in path if ident not in chosen]
        chain_cost=sum(cost(by_id[i]) for i in missing) if cost else len(missing)
        limit=max(maximum,len(path)) if n.get('selected') else maximum
        if len(chosen)+len(missing)>limit or (budget is not None and spent+chain_cost>budget):continue
        chosen.update(missing);spent+=chain_cost
        if len(chosen)>maximum:expanded=True
    result=[n for n in nodes if n.get('id') in chosen and by_id.get(n.get('id')) is n]
    return result,{'omitted':len(nodes)-len(result),'invalid':invalid,'contextExpanded':expanded,
                   'selectedOmitted':bool(anchors) and not all(n['id'] in chosen for n,_,_ in anchors)}
