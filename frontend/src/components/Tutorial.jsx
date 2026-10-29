import React,{useEffect,useRef,useState} from 'react';
import {readPreferences,setPreferences} from '../local-data.js';
import Icon from './Icon.jsx';
const STEPS=[
  ['url','Open a website','Enter a permitted public URL, choose the browser viewport, then Open website. The preview is a real screenshot from the existing remote Chromium engine.'],
  ['preview','Select an element','Tap the screenshot to inspect an element without activating its links or forms. Wheel, swipe or use the scroll controls to move the remote page.'],
  ['inspection','Read the evidence','Explore Styles, HTML, Motion and JSON. Capture hover in Motion to attach measured changes; a transition declaration alone is not an observed effect.'],
  ['settings','Choose your prompt settings','Select element, section or visible page; choose the output format, detail and an implementation preset. Free local generation stays available.'],
  ['generate','Generate and review','Generate Prompt from current server-owned evidence. The report separates measurements, inferences, missing evidence and warnings. Review and edit the result.'],
  ['export','Keep your work','Copy the prompt or a section, export TXT/Markdown, or export the missing-information checklist. History saves only explicit versions after you enable device storage.'],
];
export default function Tutorial({replay=0,active=true,preferencesEpoch=0}){
  const [step,setStep]=useState(-1),[dismissed,setDismissed]=useState(()=>readPreferences().tutorialDismissed),[note,setNote]=useState('');
  const lastReplay=useRef(replay),heading=useRef(null);
  useEffect(()=>{setDismissed(readPreferences().tutorialDismissed);},[preferencesEpoch]);
  useEffect(()=>{if(replay!==lastReplay.current){lastReplay.current=replay;setStep(0);}},[replay]);
  useEffect(()=>{
    if(!active||step<0)return;
    const node=globalThis.document?.querySelector(`[data-tour="${STEPS[step][0]}"]`);
    node?.setAttribute('data-tour-active','true');
    const reduced=globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    node?.scrollIntoView?.({behavior:reduced?'instant':'smooth',block:'center'});
    heading.current?.focus();
    return()=>node?.removeAttribute('data-tour-active');
  },[step,active]);
  function finish(){setStep(-1);setDismissed(true);try{setPreferences({tutorialDismissed:true});setNote('');}catch{setNote('Tutorial dismissed for this visit. Browser storage is unavailable.');}}
  if(!active)return null;
  if(step<0)return !dismissed?<aside className="tutorial-invite"><div><Icon name="spark"/><span><strong>A quick orientation?</strong> Six short steps. Explore at your own pace.</span></div><div><button onClick={()=>setStep(0)}>Start tutorial</button><button className="quiet" onClick={finish}>Skip</button></div></aside>:note?<p className="fine-print" role="status">{note}</p>:null;
  return <aside className="tutorial-card" aria-label="Inspector tutorial" onKeyDown={e=>{if(e.key==='Escape')finish();}}><div className="tutorial-progress"><span>GETTING STARTED</span><span>STEP {step+1} OF {STEPS.length}</span></div><h2 ref={heading} tabIndex="-1">{STEPS[step][1]}</h2><p>{STEPS[step][2]}</p><div className="tutorial-controls"><button className="quiet" onClick={finish}>Skip</button><div><button disabled={step===0} onClick={()=>setStep(s=>s-1)}>Back</button><button className="primary" onClick={()=>step===STEPS.length-1?finish():setStep(s=>s+1)}>{step===STEPS.length-1?'Finish':'Next'}</button></div></div><span className="sr-only" role="status">Step {step+1} of {STEPS.length}: {STEPS[step][1]}</span></aside>;
}
