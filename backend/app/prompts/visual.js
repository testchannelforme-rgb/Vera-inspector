({parentOf,isPrivate,hasTime}) => {
  // No fetching, DOM mutation, hit testing, credentials or pixel sampling.
  // This helper only reads bounded paint metadata in the current browser.
  const asset='present; asset URL omitted', omitted='[asset reference omitted]';
  const unsafe=/\\|\/\*|url\s*\(|image-set\s*\(|(?:https?|data|blob|file|javascript|ftp):|\/\/|www\./i;
  const limit=1024, maxInput=8192;
  function layers(value) {
    if(typeof value!=='string'||value.length>maxInput)return {value:'[CSS omitted: size limit]',changed:true,limited:true};
    if(value==='none')return {value,changed:false,limited:false};
    let parts=[],depth=0,start=0,quote=null,bad=false;
    for(let i=0;i<value.length;i++) {
      const c=value[i];if(c==='\\'){bad=true;break;}
      if(quote){if(c===quote)quote=null;continue;}if(c==='"'||c==="'"){quote=c;continue;}
      if(c==='('){if(++depth>16){bad=true;break;}}else if(c===')'){if(--depth<0){bad=true;break;}}
      else if(c===','&&depth===0){parts.push(value.slice(start,i).trim());start=i+1;if(parts.length>=8){bad=true;break;}}
    }
    if(quote||depth||bad)return {value:'[CSS omitted: unsupported layers]',changed:true,limited:true};
    parts.push(value.slice(start).trim());
    const safe=parts.map(v=>/^(?:repeating-)?(?:linear|radial|conic)-gradient\(/i.test(v)&&!unsafe.test(v)&&!/["']/.test(v)?v:v==='none'?v:omitted);
    const result=safe.length===1&&safe[0]===omitted?asset:safe.join(', ');
    return {value:result.slice(0,limit),changed:result!==value,limited:result.length>limit};
  }
  const defaults={
    'background-color':['transparent','rgba(0, 0, 0, 0)'],'background-image':['none'],'background-position':['0% 0%'],'background-size':['auto','auto auto'],
    'background-repeat':['repeat'],'background-clip':['border-box'],'background-origin':['padding-box'],'background-attachment':['scroll'],
    '-webkit-background-clip':['border-box'],'-webkit-text-fill-color':[],'-webkit-text-stroke-width':['0px'],'-webkit-text-stroke-color':[],
    'text-shadow':['none'],'mix-blend-mode':['normal'],'background-blend-mode':['normal'],'isolation':['auto'],
    'filter':['none'],'backdrop-filter':['none'],'mask-image':['none'],'-webkit-mask-image':['none'],
    'mask-size':['auto','auto auto'],'mask-position':['0% 0%'],'mask-repeat':['repeat'],'mask-clip':['border-box'],'mask-origin':['border-box'],'mask-mode':['match-source'],'mask-composite':['add'],
    'clip-path':['none'],'position':['static'],'z-index':['auto'],'opacity':['1'],'transform':['none'],'transform-origin':[],
    'overflow':['visible'],'overflow-x':['visible'],'overflow-y':['visible'],'pointer-events':['auto'],
    'box-shadow':['none'],'border-radius':['0px'],'top':['auto'],'left':['auto'],'right':['auto'],'bottom':['auto']
  };
  let pseudoCount=0,contextChecks=0,contextOmitted=false,pseudoOmitted=false;
  const paint=s=>{const bg=s.getPropertyValue('background-color');return (bg&&!defaults['background-color'].includes(bg))||!['','none'].includes(s.getPropertyValue('background-image'))||!['','none'].includes(s.getPropertyValue('box-shadow'))||!['','none'].includes(s.getPropertyValue('filter'));};
  function styles(s,pseudo=false) {
    const result={},sanitized=[],truncated=[],omitted=[];
    for(const [key,initial] of Object.entries(defaults)) {
      const raw=s.getPropertyValue(key);if(!raw||initial.includes(raw))continue;
      if((key==='-webkit-text-fill-color'||key==='-webkit-text-stroke-color')&&raw===s.getPropertyValue('color'))continue;
      if(key==='transform-origin'&&s.getPropertyValue('transform')==='none')continue;
      if(/(?:background-image|mask-image)$/.test(key)) {
        const safe=layers(raw);result[key]=safe.value;if(safe.changed)sanitized.push(key);if(safe.limited)truncated.push(key);
      }else if(raw.length>maxInput){result[key]='[CSS omitted: size limit]';truncated.push(key);}
      else if(unsafe.test(raw)){result[key]='[CSS reference omitted]';sanitized.push(key);}
      else {result[key]=raw.slice(0,limit);if(raw.length>limit)truncated.push(key);}
    }
    if(pseudo)for(const key of ['display','position','width','height','opacity','color','font-family','font-size','font-weight','line-height']) {
      const value=s.getPropertyValue(key);if(value&&value.length>maxInput){result[key]='[CSS omitted: size limit]';truncated.push(key);}
      else if(value&&!unsafe.test(value)){result[key]=value.slice(0,180);if(value.length>180)truncated.push(key);}
    }
    const priority=['position','z-index','opacity','-webkit-text-fill-color','background-clip','-webkit-background-clip','-webkit-text-stroke-width','width','height','color','background-image','mask-image','-webkit-mask-image','transform'];
    const rank=key=>priority.includes(key)?priority.indexOf(key):priority.length;
    let used=0;for(const key of Object.keys(result).sort((a,b)=>rank(a)-rank(b))){const cost=JSON.stringify([key,result[key]]).length;if(used+cost>3500){delete result[key];omitted.push(key);}else used+=cost;}
    return {styles:result,omittedProperties:omitted,sanitizedProperties:sanitized,styleTruncatedProperties:truncated};
  }
  function read(el,s=getComputedStyle(el),withPseudo=true) {
    const record=styles(s);record.pseudoElements=[];
    if(!withPseudo||isPrivate(el))return record;
    for(const pseudo of ['::before','::after']) {
      if(!hasTime()||pseudoCount>=8){pseudoOmitted=true;break;}
      const ps=getComputedStyle(el,pseudo),content=ps.getPropertyValue('content');
      if(!content||['none','normal'].includes(content)||ps.getPropertyValue('display')==='none')continue;
      pseudoCount++;
      let kind='text',value=content;
      if(content==='""'||content==="''")kind='empty';
      else if(content.length>maxInput){kind='unresolved';value='[content omitted: size limit]';pseudoOmitted=true;}
      else if(unsafe.test(content)){kind='reference';value='[content reference omitted]';}
      else if(/(?:attr|counter|counters)\s*\(/i.test(content)){kind='unresolved';value='[attribute/counter content not resolved]';}
      const p=styles(ps,true);record.pseudoElements.push({pseudo,contentKind:kind,content:value.slice(0,160),...p,
        geometry:'computed dimensions/offsets only; pseudo bounding rectangle not measured'});
    }
    return record;
  }
  const directCopy=el=>{let text='';for(let i=0;i<Math.min(el.childNodes.length,32);i++)if(el.childNodes[i].nodeType===3)text+=el.childNodes[i].textContent.slice(0,240);return text.replace(/\s+/g,' ').trim().slice(0,240);};
  function context(root) {
    const records=[],bounds=root.getBoundingClientRect(),rootCopy=directCopy(root);let parent=parentOf(root),scanned=0;
    for(let distance=1;parent&&distance<=6;distance++,parent=parentOf(parent)) {
      if(!hasTime()){contextOmitted=true;break;}contextChecks++;
      if(isPrivate(parent)){contextOmitted=true;break;}
      const s=getComputedStyle(parent),r=parent.getBoundingClientRect();
      const p=read(parent,s); // Paint is attributed to this context owner, never copied to the child.
      if(Object.keys(p.styles).length||p.pseudoElements.length)records.push({owner:'ancestor:'+distance,relation:'ancestor',distance,tag:parent.localName,
        box:Object.fromEntries(['x','y','width','height'].map(k=>[k,Math.round(r[k]*100)/100])),...p});
      if(distance>2||['main','body','html'].includes(parent.localName))continue;
      for(let i=0;i<parent.children.length&&scanned<24;i++) {
        const sibling=parent.children[i];scanned++;if(sibling===root||sibling.contains?.(root)||isPrivate(sibling))continue;
        if(!hasTime()){contextOmitted=true;break;}contextChecks++;
        const ss=getComputedStyle(sibling),b=sibling.getBoundingClientRect();
        const sameDirectText=!!rootCopy&&directCopy(sibling)===rootCopy;
        if(!['absolute','fixed'].includes(ss.position)||(!paint(ss)&&!sameDirectText)||ss.visibility!=='visible'||Number(ss.opacity)===0)continue;
        const overlap=Math.max(0,Math.min(bounds.right,b.right)-Math.max(bounds.left,b.left))*Math.max(0,Math.min(bounds.bottom,b.bottom)-Math.max(bounds.top,b.top));
        if(!bounds.width||!bounds.height||overlap/(bounds.width*bounds.height)<.5)continue;
        if(records.filter(v=>v.relation.startsWith('nearby-')).length>=2){contextOmitted=true;continue;}
        records.push({owner:'nearby:'+records.length,relation:sameDirectText?'nearby-text-layer':'nearby-decoration',sameDirectText,hiddenFromAT:sibling.getAttribute('aria-hidden')==='true',distance,tag:sibling.localName,
          box:Object.fromEntries(['x','y','width','height'].map(k=>[k,Math.round(b[k]*100)/100])),...read(sibling,ss)});
        if(sameDirectText)records[records.length-1].styles.color=ss.getPropertyValue('color');
      }
    }
    if(parent)contextOmitted=true;
    let used=0;const owners=[];for(const record of records){const size=JSON.stringify(record).length;if(used+size>10000){contextOmitted=true;continue;}owners.push(record);used+=size;}
    return {owners,coverage:{ancestorLimit:6,siblingCheckLimit:24,contextChecks,pseudoLimit:8,pseudoCount,contextOmitted,pseudoOmitted},
      method:'CSS and bounding-box context only; no pixel colors or paint order verified'};
  }
  return {read,context,paint,layers};
}
