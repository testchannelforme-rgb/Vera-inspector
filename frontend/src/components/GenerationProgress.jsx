import React from 'react';
import {motion,useReducedMotion} from 'motion/react';
export default function GenerationProgress({events=[],working=false}){
 const reduce=useReducedMotion();
 if(!events.length)return null;
 return <ol className="generation-progress" aria-label="Generation stages" aria-live="polite">{events.map((e,i)=><motion.li key={i} initial={reduce?false:{opacity:0,y:4}} animate={{opacity:1,y:0}} transition={{duration:reduce?0:.18}} aria-current={working&&i===events.length-1?'step':undefined}><span>{i+1}</span>{e.stage}</motion.li>)}</ol>;
}
