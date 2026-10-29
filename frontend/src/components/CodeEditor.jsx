import React,{useEffect,useRef} from 'react';

// One editor at a time; language packages load only when Code Studio opens a file.
export default function CodeEditor({name,value,onChange,disabled=false}){
 const host=useRef(null),view=useRef(null),latest=useRef(value),change=useRef(onChange),[fallback,setFallback]=React.useState(false);
 change.current=onChange;latest.current=value;
 useEffect(()=>{
  if(!host.current)return;
  let cancelled=false;
  Promise.all([import('codemirror'),import('@codemirror/view'),import('@codemirror/state'),import('@codemirror/lang-javascript'),import('@codemirror/lang-html'),import('@codemirror/lang-css')]).then(([cm,{EditorView},{EditorState},{javascript},{html},{css}])=>{
   if(cancelled)return;
   const lang=name.endsWith('.css')?css():name.endsWith('.html')?html():javascript({jsx:name.endsWith('.jsx')});
   const editor=new EditorView({parent:host.current,state:EditorState.create({doc:latest.current,extensions:[cm.basicSetup,lang,EditorState.readOnly.of(disabled),EditorView.editable.of(!disabled),EditorView.contentAttributes.of({'aria-label':'Code editor '+name}),EditorView.updateListener.of(update=>{if(update.docChanged)change.current(update.state.doc.toString());}),EditorView.theme({'&':{height:'100%',fontSize:'13px'},'.cm-scroller':{overflow:'auto',fontFamily:'ui-monospace, monospace'},'.cm-content':{minHeight:'420px'},'&.cm-focused':{outline:'2px solid #ad8bff'}})]})});
   view.current=editor;
  }).catch(()=>{if(!cancelled)setFallback(true);});
  return()=>{cancelled=true;view.current?.destroy();view.current=null;};
 },[name,disabled]);
 useEffect(()=>{const v=view.current;if(v&&v.state.doc.toString()!==value)v.dispatch({changes:{from:0,to:v.state.doc.length,insert:value}});},[value]);
 return <div className="code-editor-host">{fallback?<textarea aria-label={'Code editor '+name} spellCheck="false" value={value} disabled={disabled} onChange={e=>onChange(e.target.value)}/>:<div ref={host} className="codemirror-host"/>}</div>;
}
