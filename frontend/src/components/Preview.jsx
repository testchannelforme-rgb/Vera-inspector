import React,{useEffect,useRef,useState} from 'react';
import {overlayStyle,toViewport} from '../coordinates.js';

export default function Preview({frame,inspection,busy,onSelect,onScroll,onImageError}) {
  const image=useRef(null),gesture=useRef(null),actions=useRef({});
  const [decodedFrame,setDecodedFrame]=useState(null);
  const frameId=frame?.frameId;
  const imageError=useRef(onImageError);imageError.current=onImageError;
  const waitingForImage=!!frame && decodedFrame!==frameId;
  const disabled=busy||waitingForImage;
  actions.current={onScroll,busy:disabled,frame};
  useEffect(()=>{
    let cancelled=false;
    if(image.current&&frameId) image.current.decode().then(()=>{if(!cancelled)setDecodedFrame(frameId);}).catch(()=>{if(!cancelled){setDecodedFrame(frameId);imageError.current?.('Screenshot reached the frontend but could not be decoded. Refresh the image.');}});
    return()=>{cancelled=true;};
  },[frameId]);
  useEffect(()=>{
    const node=image.current;
    if(!node) return;
    let timer,deltaX=0,deltaY=0,lastPoint;
    const wheel=e=>{
      e.preventDefault();
      const state=actions.current;
      if(state.busy) return;
      lastPoint=toViewport(e.clientX,e.clientY,node.getBoundingClientRect(),state.frame.viewport);
      const unit=e.deltaMode===1?16:e.deltaMode===2?state.frame.viewport.height:1;
      deltaX+=e.deltaX*unit;deltaY+=e.deltaY*unit;
      clearTimeout(timer);
      timer=setTimeout(()=>{
        if(!actions.current.busy) actions.current.onScroll(lastPoint,Math.max(-1000,Math.min(1000,deltaY)),Math.max(-1000,Math.min(1000,deltaX)));
        deltaX=deltaY=0;
      },120);
    };
    node.addEventListener('wheel',wheel,{passive:false});
    return()=>{node.removeEventListener('wheel',wheel);clearTimeout(timer);};
  },[!!frame]);
  if(!frame) return <div className="preview-empty"><span className="empty-icon">⌖</span><h2>Inspect what’s on the web.</h2><p>Open an approved public URL to see its real Chromium rendering.</p><div className="empty-steps"><span>01 &nbsp; Open a site</span><span>02 &nbsp; Select an element</span><span>03 &nbsp; Explore its styles</span></div></div>;
  const point=e=>toViewport(e.clientX,e.clientY,image.current.getBoundingClientRect(),frame.viewport);
  return <div className="preview-wrap">
    <div className="browser-strip"><span className="browser-dot"/><span className="preview-url">{frame.url}</span><span>{frame.viewport.width} × {frame.viewport.height}</span></div>
    <div className={`image-stage ${disabled?'is-busy':''}`} aria-busy={disabled}>
      <img ref={image} className="site-image" src={frame.image} alt="Website screenshot. Tap an element to inspect; swipe to scroll." draggable="false" role="button" tabIndex={disabled?-1:0} aria-label="Select an element in the website screenshot" onPointerDown={e=>{
        if(disabled)return;
        gesture.current={x:e.clientX,y:e.clientY,p:point(e)};
        e.currentTarget.setPointerCapture(e.pointerId);
      }} onPointerCancel={()=>{gesture.current=null;}} onPointerUp={e=>{
        if(!gesture.current||disabled)return;
        const start=gesture.current;gesture.current=null;
        const dx=start.x-e.clientX,dy=start.y-e.clientY;
        if(Math.abs(dx)+Math.abs(dy)>14){const rect=image.current.getBoundingClientRect();onScroll(start.p,Math.max(-1000,Math.min(1000,dy*frame.viewport.height/rect.height)),Math.max(-1000,Math.min(1000,dx*frame.viewport.width/rect.width)));}
        else onSelect(point(e));
      }} onKeyDown={e=>{
        if(disabled)return;
        if(e.key==='Enter'||e.key===' '){e.preventDefault();onSelect({x:frame.viewport.width/2,y:frame.viewport.height/2});}
        if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();onScroll({x:frame.viewport.width/2,y:frame.viewport.height/2},e.key==='ArrowDown'?300:-300,0);}
      }}/>
      {inspection&&<div data-testid="selection-overlay" className="selection-overlay" style={overlayStyle(inspection.geometry,frame.viewport)}><span>{inspection.element.tagName} · {Math.round(inspection.geometry.width)} × {Math.round(inspection.geometry.height)}</span></div>}
      {disabled&&<div className="preview-busy"><span className="spinner"/> Updating preview</div>}
    </div>
    <div className="preview-foot"><span>Tap to inspect · Swipe or wheel to scroll</span><span>CSS pixels · DPR 1</span></div>
  </div>;
}
