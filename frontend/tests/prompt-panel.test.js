// Render the actual React component without Chromium. No real provider/network calls.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import React from 'react';
import TestRenderer,{act} from 'react-test-renderer';
import {transformWithOxc} from 'vite';

import {loadComponent} from './load-component.js';
const {default:PromptPanel}=await import(await loadComponent(new URL('../src/components/PromptPanel.jsx',import.meta.url)));
globalThis.IS_REACT_ACT_ENVIRONMENT=true;

const response={prompt:'Measured 160px button',mode:'fallback',warnings:['Visible only'],evidenceSummary:{nodeCount:1,boundary:'selected element'}};
const base={session:'session',frame:{frameId:'frame'},inspection:{element:{referenceId:'ref',tagName:'button'}},busy:false,aiAvailable:false,onBusy:()=>{}};
const buttons=root=>root.findAllByType('button');
const button=(root,label)=>buttons(root).find(n=>n.children.join('')===label);

test('actual panel generates, edits, copies edited text, regenerates and clears stale output',async()=>{
  const originalFetch=globalThis.fetch,originalNavigator=Object.getOwnPropertyDescriptor(globalThis,'navigator');
  let calls=0,copied='',payload;
  globalThis.fetch=async(url,options)=>{calls++;payload=JSON.parse(options.body);return {ok:true,json:async()=>({...response,prompt:response.prompt+' '+calls})};};
  Object.defineProperty(globalThis,'navigator',{configurable:true,value:{clipboard:{writeText:async value=>{copied=value;}}}});
  let renderer;
  try {
    await act(async()=>{renderer=TestRenderer.create(React.createElement(PromptPanel,base));});
    await act(async()=>{await button(renderer.root,'Generate Prompt').props.onClick();});
    assert.equal(payload.referenceId,'ref');assert.equal(payload.detail,'detailed');
    assert.equal(renderer.root.findByType('textarea').props.value,'Measured 160px button 1');
    await act(async()=>{renderer.root.findByType('textarea').props.onChange({target:{value:'My edited draft'}});});
    await act(async()=>{await button(renderer.root,'Copy Prompt').props.onClick();});
    assert.equal(copied,'My edited draft');
    await act(async()=>{await button(renderer.root,'Regenerate').props.onClick();});
    assert.equal(calls,2);assert.equal(renderer.root.findByType('textarea').props.value,'Measured 160px button 2');
    await act(async()=>{renderer.update(React.createElement(PromptPanel,{...base,frame:{frameId:'new-frame'}}));});
    assert.equal(renderer.root.findByType('textarea').props.value,'');
  }finally{
    if(renderer)await act(async()=>renderer.unmount());
    globalThis.fetch=originalFetch;
    if(originalNavigator)Object.defineProperty(globalThis,'navigator',originalNavigator);else delete globalThis.navigator;
  }
});

test('actual panel supports visible page without selection and preserves draft on provider/API failure',async()=>{
  const originalFetch=globalThis.fetch;let fail=false;let renderer;
  globalThis.fetch=async()=>fail?{ok:false,json:async()=>({detail:'Session expired'})}:{ok:true,json:async()=>response};
  try {
    await act(async()=>{renderer=TestRenderer.create(React.createElement(PromptPanel,{...base,inspection:null}));});
    assert.equal(button(renderer.root,'Generate Prompt').props.disabled,true);
    await act(async()=>{renderer.root.findAllByType('select')[0].props.onChange({target:{value:'page'}});});
    assert.equal(button(renderer.root,'Generate Prompt').props.disabled,false);
    await act(async()=>{await button(renderer.root,'Generate Prompt').props.onClick();});
    fail=true;
    await act(async()=>{await button(renderer.root,'Regenerate').props.onClick();});
    assert.equal(renderer.root.findByType('textarea').props.value,response.prompt);
    assert.match(renderer.root.findByProps({role:'alert'}).children.join(''),/Session expired/);
  }finally{if(renderer)await act(async()=>renderer.unmount());globalThis.fetch=originalFetch;}
});
