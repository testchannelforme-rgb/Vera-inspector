(root, scope) => {
  // No values, attributes containing URLs, HTML, scripts, selectors or storage.
  if (!root?.isConnected) throw new Error('Selection detached');
  let boundary = 'selected element';
  if (scope === 'section') {
    const section = root.closest('section,article,nav,header,footer,main,[role="region"]');
    root = section || root.parentElement || root;
    boundary = section ? 'nearest semantic section ancestor (heuristic boundary)' : 'immediate parent (heuristic boundary)';
  }
  const sensitive = 'input,textarea,select,option,[contenteditable]:not([contenteditable="false"]),[data-veyra-private]';
  const skipped = 'script,style,noscript,template,iframe,frame';
  const properties = ['display','position','width','height','box-sizing','margin-top','margin-right','margin-bottom','margin-left','padding-top','padding-right','padding-bottom','padding-left','gap','flex-direction','flex-wrap','justify-content','align-items','grid-template-columns','grid-template-rows','overflow','z-index','transform','background-color','color','opacity','font-family','font-size','font-weight','line-height','letter-spacing','text-align','text-transform','border-top','border-right','border-bottom','border-left','border-radius','box-shadow','fill','stroke','stroke-width','filter','text-decoration','object-fit','animation-name','animation-duration','animation-delay','animation-iteration-count','animation-timing-function','transition-property','transition-duration','transition-delay','transition-timing-function'];
  const nodes = [], stack = [{el:root, parent:null, depth:0}], start=performance.now();
  let visited=0, truncated=false, excluded=0;
  while (stack.length && nodes.length < 55 && visited < 1500 && performance.now()-start < 120) {
    const {el,parent,depth} = stack.pop(); visited++;
    if (!(el instanceof Element) || (el.parentElement?.closest(sensitive)) || el.matches(skipped) || depth > 16) { excluded++; continue; }
    const r=el.getBoundingClientRect(), s=getComputedStyle(el);
    const visible=r.width>0 && r.height>0 && r.right>0 && r.bottom>0 && r.left<innerWidth && r.top<innerHeight && s.visibility==='visible' && Number(s.opacity)>0 && s.display!=='none';
    if (!visible && el!==root) continue;
    // Direct visible text only; never innerText on an ancestor of a private input.
    let text='';
    if (visible && !el.matches(sensitive)) for (const child of el.childNodes) if (child.nodeType===Node.TEXT_NODE) {
      const range=document.createRange();range.selectNodeContents(child);
      const rects=[...range.getClientRects()];
      if(rects.some(b=>b.width>0 && b.height>0 && b.bottom>0 && b.top<innerHeight && b.right>0 && b.left<innerWidth)) text+=child.textContent+' ';
      if(text.length>240)break;
    }
    const id=nodes.length;
    const styles=Object.fromEntries(properties.map(p=>[p,s.getPropertyValue(p).slice(0,180)]));
    // URL-bearing CSS is reduced to a presence flag; signed asset URLs stay private.
    if(s.backgroundImage!=='none')styles['background-image']='present; asset URL omitted';
    const role=el.getAttribute('role');
    const node={id,parent,tag:el.localName,depth,visible,text:text.replace(/\s+/g,' ').trim().slice(0,240),role:role?.slice(0,50)||null,
      box:Object.fromEntries(['x','y','width','height'].map(k=>[k,Math.round(r[k]*100)/100])),styles,
      behavior:{linkPresent:el.localName==='a'&&el.hasAttribute('href'),button:el.localName==='button',expanded:el.getAttribute('aria-expanded')===null?null:el.getAttribute('aria-expanded')==='true',nativeDisclosure:el.localName==='details',activeAnimationCount:el.getAnimations({subtree:false}).length},
      image:el.localName==='img'?{present:true,alt:el.getAttribute('alt')?.slice(0,160)||'',naturalWidth:el.naturalWidth,naturalHeight:el.naturalHeight}:null};
    nodes.push(node);
    if(el.matches(sensitive)){excluded++;continue;}
    if(el.children.length>1500)truncated=true;
    const children=Array.from({length:Math.min(el.children.length,1500)},(_,i)=>el.children[i]);
    // Open shadow roots can be sampled. Closed roots and iframe documents stay opaque.
    if(el.shadowRoot)children.push(...el.shadowRoot.children);
    for(let i=children.length-1;i>=0;i--) stack.push({el:children[i],parent:id,depth:depth+1});
  }
  truncated=truncated||stack.length>0;
  return {schemaVersion:'0.3-evidence',scope,boundary,viewport:{width:innerWidth,height:innerHeight},scroll:{x:scrollX,y:scrollY},nodes,truncated,excluded,visited};
}
