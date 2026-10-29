import React,{useEffect,useRef,useState} from 'react';
import {api} from '../api.js';
import {copyPrompt,generationGate,promptBody} from '../prompt-utils.js';

export default function PromptPanel({session,frame,inspection,busy,aiAvailable,onBusy}) {
  const [scope,setScope]=useState('element'),[target,setTarget]=useState('react'),[detail,setDetail]=useState('detailed'),[style,setStyle]=useState('faithful'),[mode,setMode]=useState('local');
  const [text,setText]=useState(''),[result,setResult]=useState(null),[status,setStatus]=useState(''),[error,setError]=useState(''),[generating,setGenerating]=useState(false);
  const textarea=useRef(null),gate=useRef(generationGate()),epoch=useRef(0);
  const identity=`${session||''}:${frame?.frameId||''}:${inspection?.element?.referenceId||''}`;
  useEffect(()=>{epoch.current++;setText('');setResult(null);setStatus('');setError('');},[identity]);
  const enabled=!!session && !!frame && (scope==='page'||!!inspection);
  async function generate() {
    if(busy||!enabled)return;
    await gate.current(async()=>{
      const version=epoch.current;
      setGenerating(true);onBusy(true);setError('');setStatus('Collecting current visible evidence…');
      try {
        const body=promptBody(session,frame,inspection,{scope,target,detail,style,mode});
        const data=await api('/prompts/generate',body);
        if(version!==epoch.current)return;
        setText(data.prompt);setResult(data);setStatus('Prompt ready. Review and edit before using it in a coding tool.');
      } catch(e){if(version===epoch.current){setError(e.message);setStatus('Generation failed. Any existing draft is preserved.');}}
      finally{setGenerating(false);onBusy(false);}
    });
  }
  return <section className="prompt-panel" aria-label="AI recreation prompt">
    <div className="panel-title">Generate AI Prompt <span className="badge">V0.3.2 · PROMPTS ONLY</span></div>
    <div className="prompt-content">
      <p className="fine-print">Target: {scope==='page'?'Visible page at the current scroll position':inspection?`Selected <${inspection.element.tagName}>${scope==='section'?' and scored local component boundary':''}`:'Select an element in the preview'}. Existing selection and JSON export stay available above.</p>
      <div className="prompt-controls">
        <label>Generation scope<select value={scope} disabled={busy||generating} onChange={e=>setScope(e.target.value)}><option value="element">Selected element</option><option value="section">Selected section</option><option value="page">Full page · visible sample</option></select></label>
        <label>Implementation format<select value={target} disabled={busy||generating} onChange={e=>setTarget(e.target.value)}><option value="html-css">HTML + CSS</option><option value="html-css-js">HTML + CSS + JavaScript</option><option value="react">React</option></select></label>
        <label>Prompt detail<select value={detail} disabled={busy||generating} onChange={e=>setDetail(e.target.value)}><option value="concise">Concise</option><option value="detailed">Detailed</option><option value="highly-detailed">Highly detailed</option></select></label>
        <label>Recreation style<select value={style} disabled={busy||generating} onChange={e=>setStyle(e.target.value)}><option value="faithful">Faithful recreation</option><option value="responsive">Responsive recreation</option><option value="accessible">Accessible recreation</option></select></label>
        <label>Generation mode<select value={mode} disabled={busy||generating} onChange={e=>setMode(e.target.value)}><option value="local">Local · no API key or cost</option><option value="auto">Optional AI + local fallback</option></select></label>
      </div>
      <p className="fine-print">{mode==='local'?'Local generation stays on the Veyra backend.':aiAvailable?'AI mode sends reduced website evidence to the configured provider. Review only public content; provider quotas or charges may apply.':'AI is not configured. The local generator will produce the prompt.'} Private input values, cookies, HTML and signed asset URLs are excluded. Visible page text may still contain personal information.</p>
      <div className="prompt-actions"><button className="primary" disabled={!enabled||busy||generating} onClick={generate}>{generating?'Generating…':'Generate Prompt'}</button><button disabled={!result||busy||generating} onClick={generate}>Regenerate</button><button disabled={!text||generating} onClick={async()=>setStatus(await copyPrompt(text,textarea.current))}>Copy Prompt</button></div>
      <div className="notice" role="status" aria-live="polite">{status}</div>
      {error&&<div className="error" role="alert">{error}</div>}
      {result&&<><p className="fine-print">{result.mode==='ai'?`AI assisted · ${result.provider} / ${result.model}`:'Local fallback · deterministic measured evidence'} · {result.evidenceSummary.nodeCount} sampled nodes · {result.evidenceSummary.boundary}</p><details><summary>Accuracy notes</summary><ul className="fine-print">{result.warnings.map((w,i)=><li key={i}>{w}</li>)}</ul></details></>}
      <label className="prompt-output-label">Editable recreation prompt<textarea ref={textarea} aria-label="Generated prompt" spellCheck="false" value={text} onChange={e=>{setText(e.target.value);setStatus('Draft edited. Copy includes your edits; regenerate replaces this draft.');}} disabled={generating} placeholder="Generate a prompt from inspected content. No source code is generated here." rows={18}/></label>
      <p className="fine-print">Regenerate replaces edits. Page, scroll and selection changes clear the draft. Three generations per session per minute; one generation at a time.</p>
    </div>
  </section>;
}
