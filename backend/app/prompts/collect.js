(selected, scope) => {
  if(!selected?.isConnected)throw new Error('Selection detached');
  const started=performance.now();
  const chooseSection=__VEYRA_BOUNDARY_FUNCTION__;
  const choice=scope==='section'?chooseSection(selected):null;
  const root=choice?.element||selected;
  const boundary=choice?`<${root.localName}> · ${choice.decision.method} · ${choice.decision.reasons.join('; ')}`:scope==='page'?'visible document body':'selected element';
  if(scope==='section'&&(['main','body','html'].includes(root.localName)||root.getAttribute('role')==='main'))return {
    schemaVersion:'0.3-evidence',scope,boundary:'select a local component',boundaryDecision:{...choice.decision,method:'selection-required'},
    viewport:{width:innerWidth,height:innerHeight},scroll:{x:scrollX,y:scrollY},nodes:[],truncated:false,excluded:0};
  const sensitive='input,textarea,select,option,[contenteditable]:not([contenteditable="false"]),[data-veyra-private]';
  const skipped='script,style,noscript,template,iframe,frame';
  const properties=['top','left','right','bottom','vertical-align','list-style-type','outline','display','position','width','height','min-width','max-width','min-height','max-height','box-sizing','margin-top','margin-right','margin-bottom','margin-left','padding-top','padding-right','padding-bottom','padding-left','gap','row-gap','column-gap','flex-direction','flex-wrap','flex-grow','flex-shrink','flex-basis','justify-content','align-items','align-self','grid-template-columns','grid-template-rows','overflow','overflow-x','overflow-y','z-index','transform','background-color','color','opacity','font-family','font-size','font-weight','font-style','line-height','letter-spacing','text-align','text-transform','border-top','border-right','border-bottom','border-left','border-radius','box-shadow','fill','stroke','stroke-width','filter','text-decoration','object-fit','object-position','animation-name','animation-duration','animation-delay','animation-iteration-count','animation-timing-function','transition-property','transition-duration','transition-delay','transition-timing-function'];
  const parentOf=el=>el.parentElement||el.getRootNode()?.host||null;
  const privateAncestor=el=>{let p=parentOf(el),count=0;for(;p&&count<64;p=parentOf(p),count++)if(p.matches(sensitive))return true;return !!p;};
  const visualEngine=(__VEYRA_VISUAL_FUNCTION__)({parentOf,isPrivate:el=>el.matches(sensitive)||privateAncestor(el),hasTime:()=>performance.now()-started<120});
  const selectedPath=new Set();
  for(let el=selected,n=0;el&&n<=16;el=parentOf(el),n++){selectedPath.add(el);if(el===root)break;}
  const queue=[{el:root,parent:null,depth:0,siblingIndex:0,parentRelationship:'snapshot-root'}], pinned=[],candidates=[],seen=new Set();
  let visited=0,excluded=0,truncated=false,queued=1;
  // Breadth-first discovery reaches later sibling headings/CTAs before deep early wrappers.
  // Only small candidate descriptors are retained; full CSS is read for the chosen sample.
  while((queue.length||pinned.length)&&visited<1500&&performance.now()-started<95) {
    const {el,parent,depth,siblingIndex,parentRelationship}=(pinned.length?pinned:queue).shift();visited++;
    if(seen.has(el))continue;seen.add(el);
    if(!(el instanceof Element)||privateAncestor(el)||el.matches(skipped)){excluded++;continue;}
    if(depth>16){truncated=true;continue;}
    const r=el.getBoundingClientRect(),s=getComputedStyle(el);
    const visible=r.width>0&&r.height>0&&r.right>0&&r.bottom>0&&r.left<innerWidth&&r.top<innerHeight&&s.visibility==='visible'&&Number(s.opacity)>0&&s.display!=='none';
    // Zero-box display:contents wrappers still preserve ancestry for their visible children.
    if(!visible&&el!==root&&s.display!=='contents')continue;
    let text='';
    if(visible&&!el.matches(sensitive))for(let i=0;i<Math.min(el.childNodes.length,200);i++) {
      const child=el.childNodes[i];if(child.nodeType!==Node.TEXT_NODE)continue;
      const range=document.createRange();range.selectNodeContents(child);
      const boxes=range.getClientRects();let textVisible=false;
      for(let j=0;j<Math.min(boxes.length,100);j++){const b=boxes[j];if(b.width>0&&b.height>0&&b.bottom>0&&b.top<innerHeight&&b.right>0&&b.left<innerWidth){textVisible=true;break;}}
      if(textVisible)text+=child.textContent+' ';if(text.length>240)break;
    }
    const id=candidates.length,tag=el.localName;
    const descriptor={id,parent,depth,siblingIndex,parentRelationship,el,style:s,tag,visible,selected:el===selected,text:text.replace(/\s+/g,' ').trim().slice(0,240),
      box:Object.fromEntries(['x','y','width','height'].map(k=>[k,Math.round(r[k]*100)/100]))};
    descriptor.priority=(el===root?1000:0)+(el===selected?1000:0)+(selectedPath.has(el)?150:0)+
      (/^h[1-6]$/.test(tag)?100:['nav','main','section','article','header','footer'].includes(tag)?45:0)+
      (['button','a','input','select','summary'].includes(tag)?85:0)+(['img','svg','video','canvas'].includes(tag)?80:0)+
      (descriptor.text?35:0)+(['grid','flex'].includes(s.display)?20:0)+(s.boxShadow!=='none'?8:0)+(visualEngine.paint(s)?45:0)+(['absolute','fixed'].includes(s.position)?20:0);
    candidates.push(descriptor);
    if(el.matches(sensitive)){excluded++;continue;}
    const children=[];
    for(let i=0;i<Math.min(el.children.length,1500);i++)children.push({el:el.children[i],siblingIndex:i,parentRelationship:'dom-child'});
    if(el.shadowRoot)for(let i=0;i<Math.min(el.shadowRoot.children.length,1500-children.length);i++)children.push({el:el.shadowRoot.children[i],siblingIndex:i,parentRelationship:'shadow-host'});
    if(el.children.length>children.length)truncated=true;
    // Visit the selected ancestry first but retain true DOM sibling indices.
    for(const {el:child,siblingIndex,parentRelationship} of children) {
      if(queued>=1500){truncated=true;break;}
      (selectedPath.has(child)?pinned:queue).push({el:child,parent:id,depth:depth+1,siblingIndex,parentRelationship});queued++;
    }
  }
  if(queue.length||pinned.length)truncated=true;
  const byId=new Map(candidates.map(c=>[c.id,c])),keep=new Set();
  const path=c=>{const result=[];for(let n=c;n&&!keep.has(n.id);n=byId.get(n.parent))result.unshift(n.id);return result;};
  for(const c of [...candidates].sort((a,b)=>b.priority-a.priority||a.id-b.id)) {
    const chain=path(c);if(keep.size+chain.length<=55)for(const id of chain)keep.add(id);
  }
  if(keep.size<candidates.length)truncated=true;
  const nodes=[];let visualContext=null,rawChars=0;const admitted=new Set();
  // Materialize important ancestor chains first too; a time cutoff must not
  // revert to dropping late CTAs in discovery order. Sort output only afterward.
  for(const ident of keep) {
    const item=byId.get(ident);
    if(item.parent!==null&&!admitted.has(item.parent)){truncated=true;continue;}
    if(nodes.length&&performance.now()-started>=120){truncated=true;break;}
    const {el,style:s,priority,...node}=item;
    delete node.el;delete node.style;
    const values=properties.map(p=>[p,s.getPropertyValue(p)]);
    node.styleTruncatedProperties=values.filter(([,v])=>v.length>180).map(([p])=>p);
    node.styles=Object.fromEntries(values.map(([p,v])=>[p,v.slice(0,180)]));
    const visual=visualEngine.read(el,s);
    Object.assign(node.styles,visual.styles);
    node.styleTruncatedProperties=node.styleTruncatedProperties.filter(k=>!Object.hasOwn(visual.styles,k)).concat(visual.styleTruncatedProperties);
    node.sanitizedProperties=visual.sanitizedProperties;
    if(visual.pseudoElements.length||visual.omittedProperties.length)node.visual={pseudoElements:visual.pseudoElements,omittedProperties:visual.omittedProperties};
    node.role=el.getAttribute('role')?.slice(0,50)||null;
    node.accessibility={label:el.matches(sensitive)?'':(el.getAttribute('aria-label')||'').slice(0,160),hiddenFromAT:el.getAttribute('aria-hidden')==='true',disabled:el.hasAttribute('disabled')||el.getAttribute('aria-disabled')==='true',method:'DOM attributes only; accessible name not verified'};
    node.behavior={linkPresent:el.localName==='a'&&el.hasAttribute('href'),button:el.localName==='button',expanded:el.getAttribute('aria-expanded')===null?null:el.getAttribute('aria-expanded')==='true',nativeDisclosure:el.localName==='details',activeAnimationCount:el.getAnimations({subtree:false}).length};
    node.image=el.localName==='img'?{present:true,alt:el.getAttribute('alt')?.slice(0,160)||'',naturalWidth:el.naturalWidth,naturalHeight:el.naturalHeight,complete:el.complete}:null;
    const b=node.box;node.viewportIntersection={x:Math.max(0,b.x),y:Math.max(0,b.y),width:Math.max(0,Math.min(innerWidth,b.x+b.width)-Math.max(0,b.x)),height:Math.max(0,Math.min(innerHeight,b.y+b.height)-Math.max(0,b.y))};
    const nodeChars=JSON.stringify(node).length;
    if(rawChars+nodeChars>110000){truncated=true;continue;}
    rawChars+=nodeChars;admitted.add(node.id);nodes.push(node);
    if(!visualContext)visualContext=visualEngine.context(root);
  }
  if(!visualContext)visualContext=visualEngine.context(root);
  if(visualContext.coverage.contextOmitted||visualContext.coverage.pseudoOmitted)truncated=true;
  nodes.sort((a,b)=>a.id-b.id);
  return {schemaVersion:'0.3-evidence',scope,boundary,visualContext,boundaryDecision:choice?.decision||null,viewport:{width:innerWidth,height:innerHeight},scroll:{x:scrollX,y:scrollY},nodes,truncated,excluded,
    collection:{visited,candidates:candidates.length,returned:nodes.length,selectedReturned:nodes.some(n=>n.selected),elapsedMs:Math.round((performance.now()-started)*100)/100,rawCharacterLimit:128000,method:'bounded breadth-first discovery; priority with ancestor closure'}};
}
