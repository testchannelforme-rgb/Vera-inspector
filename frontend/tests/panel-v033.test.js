import test from 'node:test';import assert from 'node:assert/strict';import React from 'react';import TestRenderer,{act} from 'react-test-renderer';import {loadComponent} from './load-component.js';
const {default:Panel}=await import(await loadComponent(new URL('../src/components/PromptPanel.jsx',import.meta.url)));
globalThis.IS_REACT_ACT_ENVIRONMENT=true;
const base={session:'s',frame:{frameId:'f'},inspection:{element:{referenceId:'r',tagName:'button'}},busy:false,aiAvailable:false,onBusy:()=>{}};
const button=(root,label)=>root.findAllByType('button').find(n=>n.children.join('')===label);
const store=()=>{const map=new Map();return {getItem:k=>map.get(k)??null,setItem:(k,v)=>map.set(k,String(v)),removeItem:k=>map.delete(k)};};
const response={prompt:'## 1. Objective\nMeasured initial draft',mode:'fallback',warnings:[],evidenceSummary:{nodeCount:1,boundary:'selected element'}};
test('manual drafts survive selection changes, regeneration has undo, history restores without claiming live evidence',async()=>{
 const oldFetch=globalThis.fetch,oldStorage=globalThis.localStorage;globalThis.localStorage=store();globalThis.fetch=async()=>({ok:true,json:async()=>response});let renderer;
 try{
  await act(async()=>{renderer=TestRenderer.create(React.createElement(Panel,base));});
  await act(async()=>{renderer.root.findByProps({'aria-label':'Generated prompt'}).props.onChange({target:{value:'My hand-edited draft'}});});
  await act(async()=>{renderer.update(React.createElement(Panel,{...base,frame:{frameId:'new'}}));});
  assert.equal(renderer.root.findByProps({'aria-label':'Generated prompt'}).props.value,'My hand-edited draft');
  await act(async()=>{await button(renderer.root,'Generate Prompt').props.onClick();});
  assert.equal(renderer.root.findByProps({'aria-label':'Generated prompt'}).props.value,response.prompt);
  await act(async()=>{button(renderer.root,'Undo replacement').props.onClick();});
  assert.equal(renderer.root.findByProps({'aria-label':'Generated prompt'}).props.value,'My hand-edited draft');
  await act(async()=>{button(renderer.root,'Enable local history & save version').props.onClick();});
  assert.equal(JSON.parse(globalThis.localStorage.getItem('veyra.prompt-history.v1'))[0].text,'My hand-edited draft');
  const restore=renderer.root.findAllByType('button').find(n=>n.props['aria-label']==='Restore Untitled prompt');
  await act(async()=>{restore.props.onClick();});
  assert.equal(renderer.root.findByProps({'aria-label':'Generated prompt'}).props.value,'My hand-edited draft');
  assert.match(JSON.stringify(renderer.toJSON()),/not live/);
 }finally{if(renderer)await act(async()=>renderer.unmount());globalThis.fetch=oldFetch;if(oldStorage===undefined)delete globalThis.localStorage;else globalThis.localStorage=oldStorage;}
});
test('optional AI requires a deliberate per-generation acknowledgement; local mode never requires it',async()=>{
 const oldFetch=globalThis.fetch;let requests=0,renderer;globalThis.fetch=async()=>{requests++;return {ok:true,json:async()=>response};};
 try{
  await act(async()=>{renderer=TestRenderer.create(React.createElement(Panel,{...base,aiAvailable:true}));});
  await act(async()=>{renderer.root.findAllByType('select').find(n=>n.props.value==='local').props.onChange({target:{value:'auto'}});});
  await act(async()=>{await button(renderer.root,'Generate Prompt').props.onClick();});assert.equal(requests,0);
  await act(async()=>{renderer.root.findAllByType('input').find(n=>n.props.type==='checkbox').props.onChange({target:{checked:true}});});
  await act(async()=>{await button(renderer.root,'Generate Prompt').props.onClick();});assert.equal(requests,1);
  assert.equal(renderer.root.findAllByType('input').find(n=>n.props.type==='checkbox').props.checked,false);
 }finally{if(renderer)await act(async()=>renderer.unmount());globalThis.fetch=oldFetch;}
});
