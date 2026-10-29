import React,{useEffect,useRef,useState} from 'react';
import {api} from '../api.js';
import {copyPrompt,generationGate,promptBody} from '../prompt-utils.js';
import {PRESETS,readPreferences,readHistory,setPreferences,saveVersion,deleteVersion,duplicateVersion} from '../local-data.js';
import {promptSections,exportPrompt,checklistText} from '../export-tools.js';
import EvidenceReport from './EvidenceReport.jsx';
import Icon from './Icon.jsx';

export default function PromptPanel({session,frame,inspection,busy,aiAvailable,onBusy,preferencesEpoch=0}) {
  const [scope,setScope]=useState('element'),[target,setTarget]=useState('react'),[detail,setDetail]=useState('detailed'),[style,setStyle]=useState('faithful'),[mode,setMode]=useState('local'),[preset,setPreset]=useState('faithful');
  const [text,setText]=useState(''),[result,setResult]=useState(null),[status,setStatus]=useState(''),[error,setError]=useState(''),[generating,setGenerating]=useState(false);
  const [tab,setTab]=useState('Prompt'),[history,setHistory]=useState([]),[historyEnabled,setHistoryEnabled]=useState(()=>readPreferences().historyEnabled),[title,setTitle]=useState('Untitled prompt'),[deleteId,setDeleteId]=useState(null),[sectionId,setSectionId]=useState('1'),[aiAcknowledged,setAiAcknowledged]=useState(false),[undo,setUndo]=useState(''),[manualCopy,setManualCopy]=useState(''),[detached,setDetached]=useState(false);
  const textarea=useRef(null),manualTextarea=useRef(null),gate=useRef(generationGate()),epoch=useRef(0),dirty=useRef(false),currentText=useRef(''),lastSavedText=useRef('');
  currentText.current=text;
  const identity=`${session||''}:${frame?.frameId||''}:${inspection?.element?.referenceId||''}`;
  useEffect(()=>{
    epoch.current++;setResult(null);setError('');setAiAcknowledged(false);
    if(dirty.current&&currentText.current){setDetached(true);setStatus('Selection changed. Your edited or restored draft is preserved; it is no longer attached to live evidence.');}
    else {setText('');setStatus('');setDetached(false);}
  },[identity]);
  useEffect(()=>{
    const refresh=()=>{const prefs=readPreferences();setHistoryEnabled(prefs.historyEnabled);if(!prefs.historyEnabled)lastSavedText.current='';try{setHistory(readHistory());}catch(e){setError(e.message);}};
    refresh();globalThis.addEventListener?.('storage',refresh);return()=>globalThis.removeEventListener?.('storage',refresh);
  },[preferencesEpoch]);
  useEffect(()=>{if(manualCopy){manualTextarea.current?.focus();manualTextarea.current?.select();}},[manualCopy]);
  useEffect(()=>{const warn=e=>{if(dirty.current&&currentText.current&&currentText.current!==lastSavedText.current){e.preventDefault();e.returnValue='';}};globalThis.addEventListener?.('beforeunload',warn);return()=>globalThis.removeEventListener?.('beforeunload',warn);},[]);
  const enabled=!!session && !!frame && (scope==='page'||!!inspection);
  const locked=busy||generating;
  const preferences={scope,target,detail,style,preset};
  const sections=promptSections(text),selectedSection=sections.find(s=>s.id===sectionId);
  const report=result?.evidenceSummary?.qualityReport;
  async function copy(value){setManualCopy('');const message=await copyPrompt(value,textarea.current);setStatus(message);if(message.startsWith('Clipboard unavailable'))setManualCopy(value);}
  function operation(action){try{action();setError('');}catch(e){setError(e.message);}}
  function save(enable=false){operation(()=>{if(enable)setPreferences({historyEnabled:true});setHistoryEnabled(readPreferences().historyEnabled);setHistory(saveVersion(text,title,preferences));lastSavedText.current=text;setStatus('Version saved on this device. It was not uploaded.');});}
  function restore(entry){if(text&&text!==entry.text)setUndo(text);setText(entry.text);lastSavedText.current=entry.text;setTitle(entry.title);setScope(entry.preferences.scope);setTarget(entry.preferences.target);setDetail(entry.preferences.detail);setStyle(entry.preferences.style);setPreset(entry.preferences.preset);setResult(null);setDetached(true);dirty.current=true;setTab('Prompt');setStatus('Saved version restored as an editable draft. Its old inspection is not live; generate again for a new evidence report.');}
  function download(value,format,basename){operation(()=>{exportPrompt(value,format,globalThis,basename);setStatus(`Exported ${format.toUpperCase()} using the current text.`);});}
  async function generate() {
    if(locked||!enabled)return;
    if(mode==='auto'&&aiAvailable&&!aiAcknowledged){setError('Acknowledge external AI processing for this generation, or choose Local mode.');return;}
    await gate.current(async()=>{
      const version=epoch.current,previous=text;
      setGenerating(true);onBusy(true);setError('');setStatus('Collecting current visible evidence…');
      try {
        const data=await api('/prompts/generate',promptBody(session,frame,inspection,{...preferences,mode}));
        if(version!==epoch.current)return;
        if(previous&&previous!==data.prompt)setUndo(previous);
        setText(data.prompt);setResult(data);dirty.current=false;setDetached(false);setTab('Prompt');setStatus('Prompt ready. Review the evidence report and edit before using it in a coding tool.');
      } catch(e){if(version===epoch.current){setError(e.message);setStatus('Generation failed. Any existing draft is preserved.');}}
      finally{setGenerating(false);onBusy(false);setAiAcknowledged(false);}
    });
  }
  return <section className="prompt-panel" aria-label="AI recreation prompt" id="prompt-studio">
    <div className="panel-title"><span className="title-with-icon"><Icon name="spark"/> Prompt studio</span><span className="badge">LOCAL GENERATION AVAILABLE</span></div>
    <div className="prompt-studio-grid"><aside className="prompt-settings" data-tour="settings"><span className="eyebrow">YOUR IMPLEMENTATION BRIEF</span><h2>A little more intentional.</h2><p className="fine-print">{scope==='page'?'Visible page at the current scroll position':inspection?`Selected <${inspection.element.tagName}>${scope==='section'?' and its scored local boundary':''}`:'Select an element or choose visible-page scope.'}</p>
      <div className="prompt-controls">
        <label>Generation scope<select value={scope} disabled={locked} onChange={e=>setScope(e.target.value)}><option value="element">Selected element</option><option value="section">Selected section</option><option value="page">Full page · visible sample</option></select></label>
        <label>Implementation format<select value={target} disabled={locked} onChange={e=>setTarget(e.target.value)}><option value="html-css">HTML + CSS</option><option value="html-css-js">HTML + CSS + JavaScript</option><option value="react">React</option></select></label>
        <label>Prompt detail<select value={detail} disabled={locked} onChange={e=>setDetail(e.target.value)}><option value="concise">Concise</option><option value="detailed">Detailed</option><option value="highly-detailed">Highly detailed</option></select></label>
        <label>Recreation style<select value={style} disabled={locked} onChange={e=>setStyle(e.target.value)}><option value="faithful">Faithful recreation</option><option value="responsive">Responsive recreation</option><option value="accessible">Accessible recreation</option></select></label>
        <label className="preset-field">Advanced prompt preset<select value={preset} disabled={locked} onChange={e=>setPreset(e.target.value)}>{PRESETS.map(p=><option key={p.id} value={p.id}>{p.label}</option>)}</select></label>
      </div><p className="preset-description">{PRESETS.find(p=>p.id===preset).description}</p>
      <label className="mode-field">Generation mode<select value={mode} disabled={locked} onChange={e=>{setMode(e.target.value);setAiAcknowledged(false);}}><option value="local">Local · no API key or cost</option><option value="auto">Optional AI + local fallback</option></select></label>
      <p className="fine-print">{mode==='local'?'Local generation runs on the VEYRA backend without a model-provider call.':aiAvailable?'AI mode sends reduced website evidence to the configured provider. Provider quotas or charges may apply.':'AI is not configured. The local generator will produce the prompt.'} Visible text may still contain personal information. <a href="#/privacy">Draft privacy details</a></p>
      {mode==='auto'&&aiAvailable&&<label className="check-label"><input type="checkbox" checked={aiAcknowledged} disabled={locked} onChange={e=>setAiAcknowledged(e.target.checked)}/>I understand this generation sends reduced public website evidence to the configured external AI provider.</label>}
      <div className="prompt-actions" data-tour="generate"><button className="primary" disabled={!enabled||locked} onClick={generate}>{generating?'Generating…':'Generate Prompt'}</button><button disabled={!text||!enabled||locked} onClick={generate}>Regenerate</button></div><p className="fine-print">Three generations per session per minute. Regenerate uses the current selection; Undo keeps the previous draft in memory.</p>
    </aside>
    <div className="prompt-workbench"><div className="studio-tabs" role="tablist" aria-label="Prompt studio views" onKeyDown={e=>{const labels=['Prompt','Evidence','History'];let index=labels.indexOf(tab);if(['ArrowRight','ArrowLeft','Home','End'].includes(e.key)){e.preventDefault();index=e.key==='Home'?0:e.key==='End'?2:(index+(e.key==='ArrowRight'?1:2))%3;setTab(labels[index]);e.currentTarget.querySelectorAll('[role="tab"]')[index]?.focus();}}}>{['Prompt','Evidence','History'].map(name=><button key={name} role="tab" id={`studio-${name.toLowerCase()}`} aria-selected={tab===name} tabIndex={tab===name?0:-1} aria-controls={`studio-panel-${name.toLowerCase()}`} onClick={()=>setTab(name)}>{name}{name==='History'&&history.length>0?<span className="tab-count" aria-hidden="true">{history.length}</span>:null}</button>)}</div>
      <div className="notice studio-status" role="status" aria-live="polite">{status||'Measured detail. Clear guidance. Your editable starting point.'}</div>{error&&<div className="error" role="alert">{error}</div>}
      <div role="tabpanel" id="studio-panel-prompt" aria-labelledby="studio-prompt" hidden={tab!=='Prompt'}>
        {detached&&<p className="warnings">This is a detached draft. Current browser evidence is not attached to its text.</p>}
        {result&&<p className="generation-meta">{result.mode==='ai'?`AI assisted · ${result.provider} / ${result.model}`:'Local · deterministic evidence'} · {result.evidenceSummary.nodeCount} collected nodes · {result.evidenceSummary.boundary}</p>}
        <label className="prompt-output-label">Editable recreation prompt<textarea ref={textarea} aria-label="Generated prompt" spellCheck="false" maxLength={60000} value={text} onChange={e=>{setText(e.target.value);dirty.current=true;setStatus('Draft edited. Copy, export and saved versions include your exact edits.');}} disabled={generating} placeholder="Open a website. Select a detail. Generate a clearer starting point." rows={18}/></label>
        <div className="export-toolkit" data-tour="export" aria-label="Prompt export toolkit"><div className="export-actions"><button disabled={!text||generating} onClick={()=>setTab('History')}>Save version…</button><button disabled={!text||generating} onClick={()=>copy(text)}>Copy Prompt</button><button disabled={!text||generating} onClick={()=>download(text,'txt')}>Export TXT</button><button disabled={!text||generating} onClick={()=>download(text,'md')}>Export Markdown</button>{undo&&<button disabled={generating} onClick={()=>{const previous=text;setText(undo);setUndo(previous);dirty.current=true;setResult(null);setDetached(true);setStatus('Previous draft restored. It is detached from live evidence.');}}>Undo replacement</button>}</div>
          <div className="section-export"><label>Prompt section<select aria-label="Prompt section" value={sectionId} onChange={e=>setSectionId(e.target.value)}>{Array.from({length:8},(_,i)=><option key={i} value={String(i+1)}>{i+1}. {sections.find(s=>s.id===String(i+1))?.title||'Not present in current text'}</option>)}</select></label><button disabled={!selectedSection||generating} onClick={()=>copy(selectedSection.text)}>Copy section</button><button disabled={!report||generating} onClick={()=>download(checklistText(report),'md','veyra-asset-checklist')}>Export asset checklist</button></div><p className="fine-print">Exports use the text currently in the editor. The checklist describes the last generation’s evidence, independent of manual edits.</p></div>
      </div>
      <div role="tabpanel" id="studio-panel-evidence" aria-labelledby="studio-evidence" hidden={tab!=='Evidence'}><EvidenceReport result={result} edited={dirty.current}/></div>
      <div role="tabpanel" id="studio-panel-history" aria-labelledby="studio-history" hidden={tab!=='History'} className="history-panel"><div className="history-heading"><Icon name="history"/><h3>Versions on this device</h3></div><p className="fine-print">Saved text can contain private information. History is never uploaded by this feature. No automatic saving. 20 versions / 512 KiB maximum.</p>
        <label className="history-title">Version title<input aria-label="Version title" value={title} maxLength={80} onChange={e=>setTitle(e.target.value)}/></label>
        {historyEnabled?<button className="primary" disabled={!text||generating} onClick={()=>save()}>Save Version</button>:<div className="history-opt-in"><p>Local history is off. Enable it and explicitly save this draft on this browser origin?</p><button disabled={!text||generating} onClick={()=>save(true)}>Enable local history & save version</button></div>}
        <a className="history-settings" href="#/preferences">Manage device storage</a>
        {!history.length?<div className="history-empty"><Icon name="layers" size={28}/><p>No versions saved. Your open editor is never saved automatically.</p></div>:<ol className="version-list">{history.map(entry=><li key={entry.id}><div><strong>{entry.title}</strong><time dateTime={entry.savedAt}>{new Date(entry.savedAt).toLocaleString()}</time><span>{entry.text.length.toLocaleString()} characters · {PRESETS.find(p=>p.id===entry.preferences.preset)?.label}</span></div><div className="version-actions"><button disabled={generating} onClick={()=>restore(entry)} aria-label={`Restore ${entry.title}`}>Restore</button><button disabled={generating} onClick={()=>operation(()=>{setHistory(duplicateVersion(entry.id));setStatus('Version duplicated locally.');})} aria-label={`Duplicate ${entry.title}`}>Duplicate</button><button disabled={generating} onClick={()=>setDeleteId(entry.id)} aria-label={`Delete ${entry.title}`}>Delete</button></div>{deleteId===entry.id&&<div className="inline-confirm" role="alert"><p>Permanently delete this saved version? The open editor is kept.</p><button className="danger" onClick={()=>operation(()=>{setHistory(deleteVersion(entry.id));setDeleteId(null);setStatus('Saved version deleted.');})}>Confirm delete version</button><button onClick={()=>setDeleteId(null)}>Cancel</button></div>}</li>)}</ol>}
      </div>
      {manualCopy&&<label className="prompt-output-label">Manual copy text<textarea ref={manualTextarea} readOnly value={manualCopy} aria-label="Manual copy text" rows={5}/><button onClick={()=>setManualCopy('')}>Close manual copy</button></label>}
    </div></div>
  </section>;
}
