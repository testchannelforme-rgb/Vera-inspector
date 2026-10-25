(selected) => {
  // Scored local containers, never an automatic main/body/html expansion.
  // Reasons are fixed labels, not website-provided IDs, classes or copy.
  const candidates=[], start=performance.now();
  const parentOf=el=>el.parentElement || el.getRootNode()?.host || null;
  const area=r=>Math.max(0,r.width)*Math.max(0,r.height);
  let previous=selected.getBoundingClientRect(), best=null, fallback=null;
  for(let el=selected,distance=0;el && distance<=10;el=parentOf(el),distance++) {
    if(performance.now()-start>20)break;
    const tag=el.localName;
    if(['body','html'].includes(tag))break;
    if(tag==='main'||el.getAttribute('role')==='main') {
      candidates.push({tag,distance,rejected:'page-level landmark'});break;
    }
    const r=el.getBoundingClientRect(),s=getComputedStyle(el),role=el.getAttribute('role');
    const record={tag,distance};candidates.push(record);
    if(!r.width||!r.height||s.display==='none'||s.visibility!=='visible') {record.rejected='no visible box';continue;}
    const structural=['section','article','nav','aside','header','footer','div','ul','ol','form','figure','fieldset'].includes(tag) || ['region','navigation','group','list','article'].includes(role);
    if(!structural){record.rejected='leaf or inline content';previous=r;continue;}
    if(!fallback)fallback={element:el,distance};
    const children=[];
    for(let i=0;i<Math.min(el.children.length,64);i++) {
      const child=el.children[i],b=child.getBoundingClientRect();
      if(b.width>0&&b.height>0)children.push({el:child,box:b});
    }
    const regions=children.filter(c=>['section','main','nav','footer'].includes(c.el.localName)).length;
    const broad=r.height>innerHeight*1.35 && area(r)>area(previous)*2;
    if(broad||regions>=2) {record.rejected=broad?'disproportionately tall ancestor':'multiple unrelated landmark groups';previous=r;continue;}
    const semantic=tag==='nav'||role==='navigation'?38:tag==='article'?32:tag==='section'?30:
      role==='region'?28:['header','footer','aside','fieldset','figure'].includes(tag)?22:0;
    const border=['top','right','bottom','left'].some(side=>parseFloat(s.getPropertyValue('border-'+side+'-width'))>0);
    const rounded=parseFloat(s.borderRadius)>0;
    const shadow=s.boxShadow && s.boxShadow!=='none';
    const bg=s.backgroundColor, parent=parentOf(el),parentBg=parent?getComputedStyle(parent).backgroundColor:null;
    const painted=!!bg&&!['transparent','rgba(0, 0, 0, 0)'].includes(bg)&&bg!==parentBg;
    const visual=border||shadow||(rounded&&painted);
    const layout=['flex','inline-flex','grid','inline-grid'].includes(s.display);
    const padding=['top','right','bottom','left'].some(side=>parseFloat(s.getPropertyValue('padding-'+side))>0);
    const controls=children.filter(c=>['a','button'].includes(c.el.localName)).length;
    const reasons=[];
    if(semantic)reasons.push('local semantic container');
    if(visual)reasons.push('painted component boundary');
    if(layout)reasons.push('flex/grid grouping');
    if(children.length>=2)reasons.push('multiple visible child relationships');
    if(padding)reasons.push('measured internal spacing');
    let score=semantic+(visual?24:0)+(layout?12:0)+(padding?5:0)+(children.length>=2?8:0)+(controls>=2?10:0)+20/(distance+1)-distance*5;
    if(children.length===1&&area(children[0].box)>=area(r)*.9&&!semantic&&!visual) {score-=18;reasons.push('transparent wrapper penalty');}
    if(area(r)>area(previous)*8&&!semantic&&!visual) {score-=12;reasons.push('large expansion penalty');}
    record.score=Math.round(score*100)/100;record.reasons=reasons;
    if(reasons.length&&(!best||score>best.score))best={element:el,score,distance,reasons};
    previous=r;
  }
  // A fallback must itself be local; never resurrect a rejected broad candidate.
  if(fallback && candidates.some(c=>c.distance===fallback.distance&&c.rejected))fallback=null;
  const chosen=best&&best.score>=12?best:fallback;
  const element=chosen?.element||selected;
  return {element,decision:{method:best&&best.score>=12?'scored-local-container':'local-fallback',
    rootTag:element.localName,distance:chosen?.distance||0,score:best&&best.score>=12?Math.round(best.score*100)/100:null,
    reasons:best&&best.score>=12?best.reasons:['no confident local container; retained nearest safe parent or selection'],candidates}};
}
