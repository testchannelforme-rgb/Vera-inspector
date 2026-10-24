import React,{useEffect,useRef,useState} from 'react';
import {api} from './api.js';
import Preview from './components/Preview.jsx';
import Inspector from './components/Inspector.jsx';

export default function App() {
  const [url,setUrl]=useState('https://example.com');
  const [viewport,setViewport]=useState('1280x800');
  const [session,setSession]=useState(null),[frame,setFrame]=useState(null),[inspection,setInspection]=useState(null);
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState(''),[health,setHealth]=useState(null);
  const running=useRef(false),sessionRef=useRef(null);
  useEffect(()=>{api('/health',undefined,'GET').then(setHealth).catch(()=>setError('Backend is unavailable. Start it with bash start.sh.'));},[]);
  useEffect(()=>{
    sessionRef.current=session;
    const close=()=>{
      if(sessionRef.current) fetch('/api/sessions/'+sessionRef.current,{method:'DELETE',headers:{'X-Veyra-Client':'inspector-v0.1'},keepalive:true}).catch(()=>{});
    };
    window.addEventListener('pagehide',close);return()=>window.removeEventListener('pagehide',close);
  },[session]);
  async function run(operation) {
    if(running.current)return;
    running.current=true;setBusy(true);setError('');setNotice('');
    try {await operation();}catch(e){setError(e.message);}finally{running.current=false;setBusy(false);}
  }
  function update(data) {setFrame(data.frame);setInspection(data.inspection);}
  function open(e) {
    e?.preventDefault();
    run(async()=>{
      if(session) await api('/sessions/'+session,undefined,'DELETE');
      setSession(null);setFrame(null);setInspection(null);
      const [width,height]=viewport.split('x').map(Number);
      const data=await api('/sessions',{url,viewport:{width,height}});
      setSession(data.sessionId);update(data);setNotice('Website opened. Tap any element to inspect it.');
    });
  }
  const action=(name,body)=>run(async()=>update(await api(`/sessions/${session}/${name}`,body)));
  const scroll=(p,dy,dx=0)=>action('scroll',{...p,deltaY:dy,deltaX:dx,frameId:frame.frameId});
  const serialized=()=>JSON.stringify(inspection,null,2);
  function download() {
    const blob=new Blob([serialized()],{type:'application/json'}),href=URL.createObjectURL(blob),a=document.createElement('a');
    a.href=href;a.download='veyra-inspection.json';a.click();setTimeout(()=>URL.revokeObjectURL(href),1000);setNotice('Inspection JSON exported.');
  }
  return <div className="app-shell">
    <header className="app-header"><div className="brand"><span className="brand-mark">V</span><div>VEYRA <span className="brand-sub">INSPECTOR</span></div><span className="version">v0.1</span></div><div className="header-status"><span className={`status-dot ${health?.status==='ready'?'ready':''}`}/>{health?.status==='ready'?'Chromium ready':health?'Browser unavailable':'Connecting…'}</div></header>
    <main>
      <div className="workspace-heading"><div><span className="eyebrow">WEBSITE INSPECTION ENGINE</span><h1>Look closer.</h1><p>Real elements. Real computed styles.</p></div><span className="mode-badge">CONTROLLED PUBLIC SITES</span></div>
      <form className="toolbar" onSubmit={open}>
        <label className="url-field"><span aria-hidden="true">↗</span><input aria-label="Website URL" type="url" required value={url} onChange={e=>setUrl(e.target.value)} spellCheck="false" placeholder="https://example.com" disabled={busy}/></label>
        <select aria-label="Browser viewport" value={viewport} onChange={e=>setViewport(e.target.value)} disabled={busy}><option value="1280x800">Desktop · 1280</option><option value="1024x768">Tablet · 1024</option><option value="390x844">Mobile · 390</option></select>
        <button className="primary open-button" type="submit" disabled={busy}>{busy?<><span className="spinner"/> Working</>:'Open website →'}</button>
        <button type="button" disabled={!session||busy} onClick={()=>action('reload')} title="Reload website">Reload</button>
      </form>
      <div className="connection-note">Allowed hosts: {health?.allowedHosts?.join(', ')||'checking…'} · Private browsing contexts expire after 10 minutes.</div>
      {health?.detail&&<div className="error" role="alert">{health.detail}</div>}
      {error&&<div className="error" role="alert">{error}</div>}
      <div className="notice" role="status" aria-live="polite">{notice|| (busy?'Waiting for the remote browser…':'Select without clicking links or submitting forms on the inspected site.')}</div>
      <div className="workspace">
        <section className="preview-panel" aria-label="Website preview"><div className="panel-title">Website preview <div className="preview-actions"><button disabled={!session||busy} onClick={()=>action('refresh')}>Refresh image</button><button disabled={!session||busy} onClick={()=>scroll({x:frame.viewport.width/2,y:frame.viewport.height/2},-500)}>↑ Scroll</button><button disabled={!session||busy} onClick={()=>scroll({x:frame.viewport.width/2,y:frame.viewport.height/2},500)}>↓ Scroll</button><button disabled={!session||busy} onClick={()=>run(async()=>{await api('/sessions/'+session,undefined,'DELETE');setSession(null);setFrame(null);setInspection(null);setNotice('Session closed.');})}>Close</button></div></div>
          <Preview frame={frame} inspection={inspection} busy={busy} onSelect={point=>action('select',{...point,frameId:frame.frameId})} onScroll={scroll}/>
          {!!frame?.warnings?.length&&<div className="warnings" role="status">Some requests were blocked: {frame.warnings.join(' ')}</div>}
        </section>
        <Inspector inspection={inspection} busy={busy} onHover={()=>action('hover',{frameId:frame.frameId,durationMs:1000,intervalMs:100})} onClear={()=>action('clear')} onExport={download} onCopy={()=>run(async()=>{if(!navigator.clipboard)throw new Error('Clipboard is unavailable. Use Export JSON.');await navigator.clipboard.writeText(serialized());setNotice('JSON copied to clipboard.');})}/>
      </div>
      <footer>VEYRA AI <span>Milestone 01 · Inspection only · No AI services required</span></footer>
    </main>
  </div>;
}
