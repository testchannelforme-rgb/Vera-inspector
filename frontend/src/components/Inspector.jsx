import React,{useState} from 'react';

function Values({data}) {
  return <dl className="values">{Object.entries(data||{}).map(([key,value])=><React.Fragment key={key}><dt>{key}</dt><dd>{String(value??'—')}</dd></React.Fragment>)}</dl>;
}
export default function Inspector({inspection,busy,onHover,onClear,onCopy,onExport}) {
  const [tab,setTab]=useState('Styles');
  if(!inspection) return <aside className="inspector" aria-label="Element inspector"><div className="panel-title">Inspector <span className="badge">LIVE DOM</span></div><div className="inspector-empty"><div className="selection-icon">⌖</div><h3>No element selected</h3><p>Select something in the preview to see its actual styles, geometry and animation data.</p></div></aside>;
  const {element,geometry,animations}=inspection;
  return <aside className="inspector" aria-label="Element inspector">
    <div className="panel-title">Inspector <button className="text-button" disabled={busy} onClick={onClear}>Clear</button></div>
    <div className="element-summary"><div className="element-tag">&lt;{element.tagName}&gt; <span className="badge">SELECTED</span></div><code className="selector">{element.selector}</code><p>{element.text||'No text content'}</p><div className="dimension-row"><span>{Math.round(geometry.width*100)/100} <small>W</small></span><span>{Math.round(geometry.height*100)/100} <small>H</small></span><span>{Math.round(geometry.x)}, {Math.round(geometry.y)} <small>X,Y</small></span></div></div>
    <div className="tabs" role="tablist" aria-label="Inspector sections" onKeyDown={e=>{const labels=['Styles','HTML','Motion','JSON'];let index=labels.indexOf(tab);if(['ArrowRight','ArrowLeft','Home','End'].includes(e.key)){e.preventDefault();index=e.key==='Home'?0:e.key==='End'?3:(index+(e.key==='ArrowRight'?1:3))%4;setTab(labels[index]);e.currentTarget.querySelectorAll('[role="tab"]')[index]?.focus();}}}>{['Styles','HTML','Motion','JSON'].map(t=><button key={t} role="tab" id={`inspection-${t.toLowerCase()}`} aria-controls="inspection-tab-panel" tabIndex={t===tab?0:-1} aria-selected={t===tab} onClick={()=>setTab(t)}>{t}</button>)}</div>
    <div className="inspector-content" role="tabpanel" id="inspection-tab-panel" aria-labelledby={`inspection-${tab.toLowerCase()}`} aria-label={tab}>
      {tab==='Styles'&&<>
        {Object.entries(inspection.styleGroups).map(([group,values])=><details key={group} open={group==='appearance'||group==='typography'}><summary>{group}</summary><Values data={values}/></details>)}
        <details><summary>Element & geometry</summary><Values data={{id:element.id,classes:element.classes.join(' '),...geometry,role:element.accessibility.role,name:element.accessibility.name,selectorUnique:element.selectorUnique,selectorScope:element.selectorScope}}/></details>
        <details><summary>Pseudo-elements & CSS variables</summary><pre>{JSON.stringify({pseudoElements:inspection.pseudoElements,customProperties:inspection.customProperties},null,2)}</pre></details>
        <p className="fine-print">Values come from getComputedStyle(). Original stylesheet declarations may differ.</p>
      </>}
      {tab==='HTML'&&<><h3>HTML evidence</h3><p className="fine-print">Sanitized snippet · {element.htmlTruncated?'truncated at 20,000 characters':'text only'}</p><pre className="html-code">{element.html}</pre></>}
      {tab==='Motion'&&<><h3>Hover observation</h3><p className="fine-print">Sample computed styles for 1 second at requested 100 ms intervals. The remote mouse moves; no click is sent.</p><button className="primary full-width" onClick={onHover} disabled={busy}>Capture hover</button>
        <Values data={{detected:animations.detected,activeAnimations:animations.active.length,samples:animations.observations.length}}/>
        {animations.hover&&<><h3>Captured states</h3><div className="capture-grid">{Object.entries(animations.hover.screenshots).map(([key,src])=><figure key={key}><img src={src} alt={`Remote website ${key} hover capture`}/><figcaption>{key}</figcaption></figure>)}</div><Values data={{requestedIntervalMs:animations.hover.requestedIntervalMs,actualDurationMs:animations.hover.actualDurationMs,baselineWasAlreadyHovered:animations.hover.baselineWasAlreadyHovered}}/><h3>Changed properties</h3>{animations.observations.some(s=>Object.keys(s.changesFromBaseline).length)?animations.observations.map((s,i)=><details key={i}><summary>{s.elapsedMs} ms · {Object.keys(s.changesFromBaseline).length} changes</summary><pre>{JSON.stringify({changes:s.changesFromBaseline,geometry:s.geometry},null,2)}</pre></details>):<p className="fine-print">No computed-style changes observed in this window. Check geometry and animation metadata in the exported JSON.</p>}</>}
        <details><summary>Static animation metadata</summary><Values data={animations.metadata}/><pre>{JSON.stringify(animations.active,null,2)}</pre></details>
      </>}
      {tab==='JSON'&&<><p className="fine-print">Schema 0.1 · screenshot payloads are abbreviated in this view. Export includes the full data.</p><pre>{JSON.stringify(inspection,(key,value)=>key==='image'||(typeof value==='string'&&value.startsWith('data:image/'))?'[image data included in export]':value,2)}</pre></>}
      <details className="limitations"><summary>Inspection limitations</summary><ul>{inspection.limitations.map(l=><li key={l}>{l}</li>)}</ul></details>
    </div>
    <div className="export-bar"><button onClick={onCopy} disabled={busy}>Copy JSON</button><button className="primary" onClick={onExport} disabled={busy}>Export JSON ↓</button></div>
  </aside>;
}
