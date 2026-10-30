(() => {
  let edit=false,selected=null,scrollQueued=false;const token=__BRIDGE_TOKEN__;
  let sent=0;const send=(type,data={})=>{if(++sent<=300)parent.postMessage({type,token,...data},'*');};
  const text=value=>{try{return String(value).replace(/(?:bearer\s+\S+|(?:api[_ -]?key|password|token|secret)\s*[:=]\s*\S+)/gi,'[redacted]').replace(/https?:\/\/\S+/g,'[URL omitted]').slice(0,600);}catch{return '[unprintable]'}};
  addEventListener('error',e=>send('veyra-preview-console',{level:'error',message:e.target!==window?'Resource failed: '+(e.target.tagName||'asset'):text(e.message)}),true);
  addEventListener('unhandledrejection',e=>send('veyra-preview-console',{level:'error',message:text(e.reason)}));
  for(const level of ['warn','error']){const old=console[level].bind(console);console[level]=(...args)=>{send('veyra-preview-console',{level,message:args.slice(0,4).map(text).join(' ')});old(...args)}}
  addEventListener('message',e=>{
    if(e.source!==parent||e.data?.token!==token)return;
    if(e.data.type==='veyra-edit-mode'){edit=e.data.enabled===true;if(!edit&&selected){selected.style.outline=selected.dataset.veyraPreviousOutline||'';delete selected.dataset.veyraPreviousOutline;selected=null;}}
    if(e.data.type==='veyra-scroll'&&Number.isFinite(e.data.deltaY))scrollBy(0,Math.max(-1000,Math.min(1000,e.data.deltaY)));
  });
  addEventListener('click',e=>{
    if(!edit)return;
    e.preventDefault();e.stopImmediatePropagation();
    const n=e.target.closest('[data-veyra-node]');
    if(selected){selected.style.outline=selected.dataset.veyraPreviousOutline||'';delete selected.dataset.veyraPreviousOutline;}
    if(!n){send('veyra-preview-selected',{id:null});return;}
    selected=n;n.dataset.veyraPreviousOutline=n.style.outline;n.style.outline='2px solid #4B7FCF';
    const id=Number(n.dataset.veyraNode);send('veyra-preview-selected',{id:Number.isSafeInteger(id)?id:null});
  },true);
  addEventListener('scroll',()=>{if(scrollQueued)return;scrollQueued=true;requestAnimationFrame(()=>{scrollQueued=false;send('veyra-preview-scroll',{y:scrollY})})},{passive:true});
})();
