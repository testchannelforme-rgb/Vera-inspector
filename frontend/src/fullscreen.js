import {useEffect,useRef,useState} from 'react';
const EVENT='veyra:fullscreen';
export function useFullscreen(id){
 const ref=useRef(null),[active,setActive]=useState(false),[native,setNative]=useState(false);
 const previousFocus=useRef(null),activeRef=useRef(false);activeRef.current=active;
 async function exit(){setActive(false);previousFocus.current?.focus?.();setNative(false);if(document.fullscreenElement===ref.current)await document.exitFullscreen?.().catch(()=>{});}
 async function toggle(){
  if(activeRef.current){await exit();return;}
  window.dispatchEvent(new CustomEvent(EVENT,{detail:id}));
  if(document.fullscreenElement)await document.exitFullscreen?.().catch(()=>{});
  previousFocus.current=document.activeElement;setActive(true);if(ref.current){ref.current.tabIndex=-1;ref.current.focus({preventScroll:true});}
  try{if(ref.current?.requestFullscreen){await ref.current.requestFullscreen();setNative(true);}}catch{setNative(false);}
 }
 useEffect(()=>{
  const other=e=>{if(e.detail!==id){setActive(false);setNative(false);}};
  const escape=e=>{if(e.key==='Tab'&&activeRef.current&&ref.current){const controls=[...ref.current.querySelectorAll('button:not(:disabled),input:not(:disabled),select:not(:disabled),[contenteditable=true]')].filter(n=>n.getClientRects().length);const first=controls[0],last=controls.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();}}if(e.key==='Escape'&&activeRef.current){setActive(false);setNative(false);}};
  const change=()=>{if(document.fullscreenElement===ref.current){setActive(true);setNative(true);}else if(native){setActive(false);setNative(false);}};
  window.addEventListener(EVENT,other);window.addEventListener('keydown',escape);document.addEventListener('fullscreenchange',change);
  return()=>{window.removeEventListener(EVENT,other);window.removeEventListener('keydown',escape);document.removeEventListener('fullscreenchange',change);};
 },[id,native]);
 return {ref,active,native,toggle,exit,className:active?' workspace-fullscreen':''};
}
