import test from 'node:test';
import assert from 'node:assert/strict';
import {toViewport,overlayStyle} from '../src/coordinates.js';
const vp={width:1280,height:800};
test('half-size screenshot maps accurately with page offsets',()=>{
  assert.deepEqual(toViewport(340,220,{left:20,top:20,width:640,height:400},vp),{x:640,y:400});
});
test('responsive quarter scale preserves the selected point',()=>{
  assert.deepEqual(toViewport(145,80,{left:20,top:30,width:320,height:200},vp),{x:500,y:200});
});
test('clamps viewport edges; never returns x == width',()=>{
  assert.deepEqual(toViewport(999,999,{left:0,top:0,width:640,height:400},vp),{x:1279.99,y:799.99});
  assert.deepEqual(toViewport(-30,-50,{left:0,top:0,width:640,height:400},vp),{x:0,y:0});
});
test('zero-size image cannot be mapped',()=>assert.throws(()=>toViewport(0,0,{width:0,height:0},vp)));
test('overlay uses viewport-relative percentages and allows clipped bounds',()=>{
  assert.deepEqual(overlayStyle({x:-64,y:80,width:640,height:40},vp),{left:'-5%',top:'10%',width:'50%',height:'5%'});
});
test('DPR does not enter CSS-pixel conversion',()=>{
  for(const dpr of [1,2,3]) assert.deepEqual(toViewport(160,100,{left:0,top:0,width:320,height:200},{...vp,devicePixelRatio:dpr}),{x:640,y:400});
});
