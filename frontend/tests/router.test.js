import test from 'node:test';import assert from 'node:assert/strict';import {routeFromHash} from '../src/router.js';
test('separate home, inspector, policy and brand routes remain addressable; unknown input is inert',()=>{
 assert.deepEqual(routeFromHash(''),{page:'',section:null});assert.equal(routeFromHash('#/inspector').page,'inspector');for(const p of ['privacy','cookies','terms','about','contact','preferences','brand'])assert.equal(routeFromHash('#/'+p).page,p);assert.deepEqual(routeFromHash('#/?section=features'),{page:'',section:'features'});assert.equal(routeFromHash('#/javascript:alert(1)').page,'not-found');
});
