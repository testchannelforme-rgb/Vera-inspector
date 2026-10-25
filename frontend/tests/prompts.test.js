import test from 'node:test';
import assert from 'node:assert/strict';
import {promptBody,copyPrompt,generationGate} from '../src/prompt-utils.js';

test('generation uses server references and preferences only',()=>{
  const result=promptBody('s',{frameId:'f',image:'secret image'},{element:{referenceId:'r'},html:'untrusted'},{scope:'element',target:'react',detail:'detailed'});
  assert.deepEqual(result,{sessionId:'s',frameId:'f',referenceId:'r',scope:'element',target:'react',detail:'detailed'});
  assert.equal(promptBody('s',{frameId:'f'},null,{scope:'page'}).referenceId,null);
  assert.throws(()=>promptBody('s',{frameId:'f'},null,{scope:'element'}),/Select/);
});
test('copy uses the edited draft exactly',async()=>{
  let copied;
  assert.equal(await copyPrompt('my edited draft',null,{writeText:async text=>{copied=text;}}),'Prompt copied.');
  assert.equal(copied,'my edited draft');
});
test('clipboard rejection selects editable text and gives manual instructions',async()=>{
  let focused=false,selected=false;
  const status=await copyPrompt('draft',{focus(){focused=true;},select(){selected=true;}},{writeText:async()=>{throw Error();}});
  assert.ok(focused&&selected);assert.match(status,/use Copy/);
});
test('duplicate generation rejected; regenerate allowed after completion or error',async()=>{
  const gate=generationGate();let resolve;let calls=0;
  const first=gate(async()=>{calls++;await new Promise(r=>{resolve=r;});});
  assert.equal(await gate(async()=>{calls++;}),false);resolve();await first;
  await assert.rejects(gate(async()=>{throw Error('failed');}));
  assert.equal(await gate(async()=>{calls++;}),true);assert.equal(calls,2);
});
