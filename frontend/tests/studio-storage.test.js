import test from 'node:test';
import assert from 'node:assert/strict';
import {readStudio,saveStudio,sourceLocation,STUDIO_KEY} from '../src/studio-storage.js';
const project={format:'vanilla',files:{'index.html':'<button data-veyra-node="17">Hi</button>','style.css':'button{color:red}','script.js':''}};
const storage=()=>{const map=new Map();return {getItem:k=>map.get(k)||null,setItem:(k,v)=>map.set(k,v)}};
test('autosave round trip keeps edited files, original and five checkpoints without saving provider context',()=>{
 const s=storage();const old=structuredClone(project),edited=structuredClone(project);edited.files['style.css']='button{color:blue}';
 saveStudio({project:edited,original:old,file:'style.css',history:Array.from({length:8},(_,i)=>({project:old,original:old,title:'Version '+i,result:{generationId:'private'}}))},s);
 const d=readStudio(s);assert.equal(d.project.files['style.css'],'button{color:blue}');assert.equal(d.history.length,5);assert.equal(d.original.files['style.css'],'button{color:red}');assert.ok(!s.getItem(STUDIO_KEY).includes('generationId'));
});
test('corrupt, oversized, unsupported and blocked drafts fail without overwriting their storage',()=>{
 const s=storage();s.setItem(STUDIO_KEY,'broken');assert.throws(()=>readStudio(s));assert.equal(s.getItem(STUDIO_KEY),'broken');
 assert.throws(()=>saveStudio({project:{...project,files:{...project.files,'../secret':'x'}},original:project,history:[]},s));
 assert.throws(()=>saveStudio({project,original:project,history:[]},{setItem(){throw Error('quota')}}),/quota/);
});
test('source mapping uses unique stable IDs for HTML and JSX; missing and ambiguous IDs remain unmapped',()=>{
 assert.deepEqual(sourceLocation(project,17),{file:'index.html',from:0,to:29,id:17});
 const react={format:'react',files:{'App.jsx':'export default ()=> <button data-veyra-node={"17"}>Hi</button>;'}};
 assert.equal(sourceLocation(react,17).file,'App.jsx');assert.equal(sourceLocation(project,99),null);
 assert.equal(sourceLocation({...project,files:{...project.files,'index.html':project.files['index.html'].repeat(2)}},17),null);
 assert.equal(sourceLocation(project,'17'),null);
});
