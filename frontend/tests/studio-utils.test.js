import test from 'node:test';
import assert from 'node:assert/strict';
import {unzipSync,strFromU8} from 'fflate';
import {editProject,exportProject,changedFiles,saveDownload} from '../src/studio-utils.js';

test('project edits preserve other files and do not mutate originals; ZIP contains exact current code',()=>{
 const original={format:'vanilla',files:{'index.html':'<h1>Hi</h1>','style.css':'h1{color:red}','script.js':'console.log(1)'}};
 const edited=editProject(original,'style.css','h1{color:blue}');
 assert.equal(original.files['style.css'],'h1{color:red}');assert.equal(edited.files['script.js'],original.files['script.js']);
 assert.deepEqual(changedFiles(original,edited),['style.css']);
 const files=unzipSync(exportProject(edited));assert.equal(strFromU8(files['style.css']),'h1{color:blue}');assert.equal(Object.keys(files).length,3);
 assert.throws(()=>editProject(original,'style.css','x'.repeat(180001)),/180 KB/);
});
test('download uses filename and cleans object URLs',()=>{
 const URL0=globalThis.URL,doc0=globalThis.document,timer0=globalThis.setTimeout;let revoked='',clicked=false,anchor={click(){clicked=true;}};
 globalThis.URL={createObjectURL:()=> 'blob:test',revokeObjectURL:s=>{revoked=s;}};globalThis.document={createElement:()=>anchor};globalThis.setTimeout=fn=>fn();
 try{saveDownload(new Uint8Array([1]),'project.zip');assert.equal(anchor.download,'project.zip');assert.equal(clicked,true);assert.equal(revoked,'blob:test');}finally{globalThis.URL=URL0;globalThis.document=doc0;globalThis.setTimeout=timer0;}
});

test('fidelity checks report missing nodes, sizes, type, colors and overflow without an accuracy score',async()=>{
 const {fidelityDiagnostics}=await import('../src/studio-utils.js');
 const report=fidelityDiagnostics([{id:1,width:100,height:50,fontSize:'16px',color:'red'},{id:2}],{nodes:[{id:1,width:140,height:50,fontSize:'20px',color:'blue'}],overflow:true});
 assert.deepEqual(report,{measuredNodes:1,missing:1,sizeDifferences:1,typographyDifferences:1,colorDifferences:1,overflow:true});
});
