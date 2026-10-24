import test from 'node:test';
import assert from 'node:assert/strict';
import {api} from '../src/api.js';

test('API remains same-origin and retains structured navigation diagnostics',async()=>{
 const previous=globalThis.fetch;
 globalThis.fetch=async(url,options)=>{
  assert.equal(url,'/api/sessions');assert.equal(options.headers['X-Veyra-Client'],'inspector-v0.1');
  return {ok:false,json:async()=>({detail:'Website timed out',code:'navigation-timeout',diagnostics:{httpStatus:null}})};
 };
 try{await assert.rejects(api('/sessions',{}),error=>error.code==='navigation-timeout'&&error.diagnostics.httpStatus===null);}
 finally{globalThis.fetch=previous;}
});

test('interrupted screenshot response is distinguished from generation failure',async()=>{
 const previous=globalThis.fetch;
 globalThis.fetch=async()=>({ok:true,json:async()=>{throw new SyntaxError('truncated');}});
 try{await assert.rejects(api('/sessions'),error=>error.code==='response-transfer-failure');}
 finally{globalThis.fetch=previous;}
});

test('normalization response is consumed without a second client URL parser',async()=>{
 const previous=globalThis.fetch;
 globalThis.fetch=async(url,options)=>{
  assert.equal(url,'/api/normalize');assert.equal(JSON.parse(options.body).url,' example.com ');
  return {ok:true,json:async()=>({url:'https://example.com/'})};
 };
 try{assert.deepEqual(await api('/normalize',{url:' example.com '}),{url:'https://example.com/'});}
 finally{globalThis.fetch=previous;}
});
