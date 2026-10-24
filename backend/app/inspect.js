(el) => {
  if (!el || !el.isConnected) throw new Error('Selected element is no longer attached.');
  const groups = {
    appearance: ['background-color','background-image','color','opacity','border-top','border-right','border-bottom','border-left','border-radius','box-shadow','filter','backdrop-filter','fill','stroke'],
    typography: ['font-family','font-size','font-weight','font-style','line-height','letter-spacing','text-align','text-transform','text-decoration'],
    layout: ['width','height','min-width','max-width','min-height','max-height','margin-top','margin-right','margin-bottom','margin-left','padding-top','padding-right','padding-bottom','padding-left','display','position','top','right','bottom','left','box-sizing','flex-direction','flex-wrap','flex-grow','flex-shrink','flex-basis','justify-content','align-items','align-self','gap','row-gap','column-gap','grid-template-columns','grid-template-rows','grid-auto-flow','overflow','overflow-x','overflow-y','z-index','transform','transform-origin','object-fit','cursor'],
    animation: ['animation-name','animation-duration','animation-delay','animation-iteration-count','animation-timing-function','animation-direction','animation-fill-mode','animation-play-state','transition-property','transition-duration','transition-delay','transition-timing-function']
  };
  const read = (target,pseudo) => {
    const s=getComputedStyle(target,pseudo);
    return Object.fromEntries(Object.values(groups).flat().map(k=>[k,s.getPropertyValue(k)]));
  };
  const styles=read(el);
  const rect=el.getBoundingClientRect();
  const root=el.getRootNode();
  function selectorFor(node) {
    let parts=[];
    for(let n=node;n && n.nodeType===1;n=n.parentElement) {
      if(n.id && root.querySelectorAll('#'+CSS.escape(n.id)).length===1) {parts.unshift('#'+CSS.escape(n.id));break;}
      let part=n.localName;
      if(n.parentElement) {
        const peers=[...n.parentElement.children].filter(p=>p.localName===n.localName);
        if(peers.length>1) part+=':nth-of-type('+(peers.indexOf(n)+1)+')';
      }
      parts.unshift(part);
      if(root.querySelectorAll(parts.join(' > ')).length===1) break;
    }
    return parts.join(' > ');
  }
  const selector=selectorFor(el);
  // Never render website HTML in the UI. This sanitized clone is text-only evidence.
  const clone=el.cloneNode(true);
  const sensitive='script,style,noscript,template,input,textarea,select';
  for(const n of [clone,...clone.querySelectorAll('*')]) {
    if(n.matches(sensitive)) { n.replaceChildren(); n.removeAttribute('value'); }
    for(const a of [...n.attributes]) if(/^on/i.test(a.name)||['value','srcdoc','nonce'].includes(a.name)) n.removeAttribute(a.name);
  }
  const html=clone.outerHTML;
  const custom={}; const computed=getComputedStyle(el);
  for(const k of computed) if(k.startsWith('--') && Object.keys(custom).length<100) custom[k]=computed.getPropertyValue(k).slice(0,500);
  const pseudo={};
  for(const key of ['::before','::after']) {
    const s=getComputedStyle(el,key);
    if(s.content!=='none' && s.content!=='normal') pseudo[key]={...read(el,key),content:s.content};
  }
  const active=el.getAnimations({subtree:false}).slice(0,30).map(a=> {
    const effect=a.effect; const timing=effect?.getComputedTiming();
    const finite=v=>typeof v==='number'&&!Number.isFinite(v)?String(v):v;
    return {type:a.constructor.name,animationName:a.animationName??null,transitionProperty:a.transitionProperty??null,playState:a.playState,currentTime:finite(a.currentTime),playbackRate:a.playbackRate,timing:timing?Object.fromEntries(Object.entries(timing).map(([k,v])=>[k,finite(v)])):null,keyframes:effect?.getKeyframes().slice(0,30)??[]};
  });
  const explicitName=el.getAttribute('aria-label');
  const labelled=(el.getAttribute('aria-labelledby')||'').split(/\s+/).map(id=>el.ownerDocument.getElementById(id)?.textContent||'').join(' ').trim();
  const implicitRoles={button:'button',a:el.hasAttribute('href')?'link':null,img:'img',nav:'navigation',main:'main',input:'textbox'};
  const safeText=el.matches(sensitive)?'':(el.innerText||el.textContent||'').trim().slice(0,1000);
  return {
    element:{tagName:el.localName,id:el.id||'',classes:[...el.classList],selector,selectorUnique:root.querySelectorAll(selector).length===1,selectorScope:root===document?'document':'open-shadow-root',text:safeText,html:html.slice(0,20000),htmlTruncated:html.length>20000,accessibility:{role:el.getAttribute('role')||implicitRoles[el.localName]||null,name:(explicitName||labelled||el.getAttribute('alt')||safeText).slice(0,300),method:'best-effort DOM attributes; not the complete accessibility tree'}},
    geometry:Object.fromEntries(['x','y','width','height','top','right','bottom','left'].map(k=>[k,rect[k]])),
    styles,
    styleGroups:Object.fromEntries(Object.entries(groups).map(([g,keys])=>[g,Object.fromEntries(keys.map(k=>[k,styles[k]]))])),
    pseudoElements:pseudo,customProperties:custom,
    animations:{detected:active.length>0||styles['animation-name']!=='none',metadata:Object.fromEntries(groups.animation.map(k=>[k,styles[k]])),active,observations:[],hover:null}
  };
}
