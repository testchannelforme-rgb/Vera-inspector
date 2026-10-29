import React,{useEffect,useRef,useState} from 'react';
import {api} from '../api.js';
import {editProject,exportProject,saveDownload,fidelityDiagnostics} from '../studio-utils.js';
const CodeEditor=React.lazy(()=>import('./CodeEditor.jsx'));

export default function CodeStudio({session,frame,inspection,busy=false,onBusy=()=>{}}){
 const [config,setConfig]=useState(null),[format,setFormat]=useState('vanilla'),[scope,setScope]=useState('element'),[mode,setMode]=useState('local'),[consent,setConsent]=useState(false);
 const [project,setProject]=useState(null),[result,setResult]=useState(null),[file,setFile]=useState('index.html'),[original,setOriginal]=useState(null),[history,setHistory]=useState([]);
 const [working,setWorking]=useState(false),[error,setError]=useState(''),[status,setStatus]=useState(''),[instruction,setInstruction]=useState(''),[refineConsent,setRefineConsent]=useState(false);
 const [metrics,setMetrics]=useState(null);
 const [preview,setPreview]=useState(''),[previewError,setPreviewError]=useState(''),[rendering,setRendering]=useState(false),[auto,setAuto]=useState(true),[viewport,setViewport]=useState('100%'),[tab,setTab]=useState('edit'),[expanded,setExpanded]=useState(false),[split,setSplit]=useState(50);
 const iframe=useRef(null),epoch=useRef(0),renderEpoch=useRef(0),current=useRef(null),running=useRef(false);
 const identity=`${session}:${frame?.frameId}:${inspection?.element?.referenceId}`;current.current=project;
 useEffect(()=>{api('/studio/config',undefined,'GET').then(setConfig).catch(e=>setError(e.message));},[]);
 useEffect(()=>{epoch.current++;setConsent(false);if(current.current)setStatus('Selection changed. Your code is kept. Regenerate to attach the new selection.');},[identity]);
 useEffect(()=>{const receive=e=>{if(e.source!==iframe.current?.contentWindow||e.origin!=='null')return;if(e.data?.type==='veyra-preview-error')setPreviewError(String(e.data.message).slice(0,600));if(e.data?.type==='veyra-preview-metrics'&&Array.isArray(e.data.nodes)&&e.data.nodes.length<=55)setMetrics(e.data);};window.addEventListener('message',receive);return()=>window.removeEventListener('message',receive);},[]);
 useEffect(()=>{if(!project||!auto)return;const timer=setTimeout(()=>render(project),900);return()=>{clearTimeout(timer);renderEpoch.current++;};},[project,auto]);
 useEffect(()=>()=>{epoch.current++;renderEpoch.current++;},[]);
 function remember(){if(project)setHistory(h=>[...h.slice(-9),{project,result,original}]);}
 async function generate(){
  if(running.current)return;running.current=true;const token=epoch.current;
  setWorking(true);onBusy(true);setError('');setStatus(mode==='auto'?'Generating with the configured AI model…':'Reconstructing measured structure and styles…');
  try{
   const response=await api('/studio/generate',{sessionId:session,frameId:frame.frameId,referenceId:inspection?.element?.referenceId||null,scope,format,target:format==='react'?'react':'html-css-js',mode,consent});
   if(token!==epoch.current){setStatus('Selection changed during generation. Current code was preserved; generate again.');return;}
   remember();setProject(response.project);setOriginal(response.project);setResult(response);setFile(format==='react'?'App.jsx':'index.html');setStatus(response.summary+' · '+(response.mode==='ai'?'AI: '+response.model:'Local measured reconstruction'));setPreview('');
  }catch(e){setError(e.message);setStatus('Generation failed. Existing code is preserved.');}finally{running.current=false;setWorking(false);onBusy(false);}
 }
 async function render(p=project){
  if(!p)return;const token=++renderEpoch.current;setRendering(true);setPreviewError('');setMetrics(null);
  try{const data=await api('/studio/preview',{project:p});if(token===renderEpoch.current)setPreview(data.url);}
  catch(e){if(token===renderEpoch.current)setPreviewError(e.message);}
  finally{if(token===renderEpoch.current)setRendering(false);}
 }
 async function refine(){
  if(running.current)return;running.current=true;setWorking(true);onBusy(true);setError('');const before=project;
  try{
   const response=await api('/studio/refine',{generationId:result.generationId,project:before,instruction,consent:refineConsent});
   remember();setProject(response.project);setResult({...result,...response});setStatus('Modified: '+response.modifiedFiles.join(', ')+' · '+response.summary);setRefineConsent(false);
  }catch(e){setError(e.message);}finally{running.current=false;setWorking(false);onBusy(false);}
 }
 function edit(text){try{setProject(editProject(project,file,text));}catch(e){setError(e.message);}}
 function restore(){const last=history.at(-1);if(!last)return;setProject(last.project);setResult(last.result);setOriginal(last.original);if(!last.project.files[file])setFile(Object.keys(last.project.files)[0]);setHistory(h=>h.slice(0,-1));setStatus('Previous project restored.');}
 async function copy(){try{await navigator.clipboard.writeText(project.files[file]);setStatus(file+' copied.');}catch{setError('Clipboard unavailable. Select code in the editor and copy, or download the project.');}}
 return <section className={'code-studio'+(expanded?' studio-expanded':'')} aria-label="Veyra Code Studio">
  <div className="studio-heading"><div><span className="eyebrow">INSPECT → GENERATE → EDIT → PREVIEW → EXPORT</span><h2>Code Studio <small>V0.4.0</small></h2></div><button onClick={()=>setExpanded(v=>!v)} aria-pressed={expanded}>{expanded?'Compact workspace':'Expand workspace'}</button></div>
  <div className="studio-toolbar">
   <label>Output<select aria-label="Code output format" value={format} disabled={working} onChange={e=>setFormat(e.target.value)}><option value="vanilla">HTML / CSS / JavaScript</option><option value="react">React project</option></select></label>
   <label>Scope<select aria-label="Code selection scope" value={scope} disabled={working} onChange={e=>setScope(e.target.value)}><option value="element">Selected element</option><option value="section">Selected section</option><option value="page">Visible page</option></select></label>
   <label>Generator<select aria-label="Code generator" value={mode} disabled={working} onChange={e=>{setMode(e.target.value);setConsent(false);}}><option value="local">Local · measured reconstruction</option><option value="auto" disabled={!config?.codeAIAvailable}>AI · configured model</option></select></label>
   <button className="primary" onClick={generate} disabled={busy||working||!session||!frame||(scope!=='page'&&!inspection)||(mode==='auto'&&!consent)}>{working?'Generating…':'Generate Code'}</button>
   <button onClick={()=>render()} disabled={!project||working||rendering}>Preview</button><button onClick={copy} disabled={!project||working}>Copy file</button>
   <button onClick={()=>{try{saveDownload(exportProject(project),'veyra-'+project.format+'.zip');setStatus('Current project exported.');}catch(e){setError(e.message);}}} disabled={!project||working}>Download project</button>
   <button disabled={!project||working||!original} onClick={()=>{remember();setProject(original);setStatus('Original generated files restored. Previous edits are in Restore previous.');}}>Reset generated code</button>
   <button disabled={!history.length||working} onClick={restore}>Restore previous</button>
  </div>
  {mode==='auto'&&<label className="studio-consent"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/>Send the selected, redacted website evidence to the configured external AI provider for this generation.</label>}
  <p className="fine-print">{config?`${config.plan} operator plan · ${config.generationLimit} generations/day · ${config.refinementLimit} refinements/day`:'Checking configuration…'} · Local editor renders are unmetered. Code stays in this open session; download before closing the tab.</p>
  {error&&<div role="alert" className="error">{error}</div>}<div role="status" aria-live="polite" className="notice">{status}</div>
  {!project?<div className="studio-empty"><h3>Turn your selection into working code.</h3><p>Open a website, select a component, choose an output, then generate. Local mode works without an API key.</p></div>:<>
   <div role="tablist" aria-label="Code workspace view" className="studio-mobile-tabs"><button role="tab" aria-selected={tab==='edit'} onClick={()=>setTab('edit')}>Edit</button><button role="tab" aria-selected={tab==='preview'} onClick={()=>setTab('preview')}>Live preview</button></div>
   <label className="studio-resize">Panel width<input type="range" min="30" max="70" aria-label="Editor panel width" value={split} onChange={e=>setSplit(Number(e.target.value))}/></label>
   <div className={'studio-grid show-'+tab} style={{'--editor-width':split+'%'}}>
    <div className="studio-edit"><nav aria-label="Generated files" className="studio-files">{Object.keys(project.files).map(name=><button key={name} aria-pressed={file===name} disabled={working} onClick={()=>setFile(name)}>{name}</button>)}</nav><div className="studio-code"><div className="panel-title">{file}<span>{project.format==='react'?'React project':'Vanilla web'}</span></div><React.Suspense fallback={<p>Loading editor…</p>}><CodeEditor name={file} value={project.files[file]||''} onChange={edit} disabled={working}/></React.Suspense></div></div>
    <section className="studio-live" aria-label="Generated website preview"><div className="preview-toolbar"><select aria-label="Preview viewport" value={viewport} onChange={e=>setViewport(e.target.value)}><option value="100%">Desktop · fit</option><option value="768px">Tablet · 768</option><option value="390px">Mobile · 390</option></select><button onClick={()=>render()} disabled={rendering}>Refresh preview</button><label><input type="checkbox" checked={auto} onChange={e=>setAuto(e.target.checked)}/>Auto preview</label></div>
     <p role="status" className="fine-print">{rendering?'Compiling preview…':preview?'Sandbox active · network resources blocked':'Press Preview to render.'}</p>
     {previewError&&<div role="alert" className="error">{previewError}</div>}
     <div className="studio-preview-scroll">{preview&&<iframe ref={iframe} title="Generated code preview" src={preview} sandbox="allow-scripts" referrerPolicy="no-referrer" allow="camera 'none'; microphone 'none'; geolocation 'none'; clipboard-read 'none'; clipboard-write 'none'" style={{width:viewport}}/>}</div>
    </section>
   </div>
   <div className="studio-refine"><label>Refine current code<input aria-label="Refinement instruction" maxLength={1200} value={instruction} disabled={working} onChange={e=>setInstruction(e.target.value)} placeholder="Make this section responsive"/></label><label className="studio-consent"><input type="checkbox" checked={refineConsent} onChange={e=>setRefineConsent(e.target.checked)}/>Send current code and its selected evidence to the configured refinement provider.</label><button disabled={working||!config?.refineAIAvailable||instruction.trim().length<5||!refineConsent} onClick={refine}>Refine code with AI</button>{!config?.refineAIAvailable&&<p className="fine-print">AI refinement is unavailable until a provider is configured. Manual editing works.</p>}</div>
   <details className="studio-diagnostics"><summary>Generation evidence and limitations</summary><p>Modified files: {result?.modifiedFiles?.join(', ')}</p>{result?.warnings?.map((w,i)=><p key={i}>{w}</p>)}{metrics&&<p>Preview checks: {JSON.stringify(fidelityDiagnostics(result?.diagnostics?.expected,metrics))}. Size tolerance: 2px or 5%. This compares DOM measurements at the current viewport; it is not a pixel similarity score.</p>}<pre>{JSON.stringify(result?.diagnostics||{},null,2)}</pre></details>
  </>}
 </section>;
}
