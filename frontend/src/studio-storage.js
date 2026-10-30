import {projectSize,PROJECT_LIMIT} from './studio-utils.js';
export const STUDIO_KEY='veyra.code-studio.v2';
const MAX_BYTES=2*1024*1024;
function valid(p){return p&&['vanilla','react'].includes(p.format)&&p.files&&Object.entries(p.files).every(([k,v])=>['index.html','style.css','script.js','App.jsx','main.jsx','package.json','vite.config.js','README.md'].includes(k)&&typeof v==='string')&&projectSize(p)<=PROJECT_LIMIT;}
export function readStudio(storage=globalThis.localStorage){
 const raw=storage?.getItem(STUDIO_KEY);if(!raw)return null;
 if(raw.length>MAX_BYTES)throw Error('Saved Code Studio draft exceeds its limit. Download current work before clearing it.');
 const d=JSON.parse(raw);
 if(d.schema!==2||!valid(d.project)||!valid(d.original)||!Array.isArray(d.history)||d.history.length>5||d.history.some(v=>!valid(v.project)||!valid(v.original)))throw Error('Saved Code Studio draft is invalid. It has not been replaced.');
 return d;
}
export function saveStudio(state,storage=globalThis.localStorage){
 if(!valid(state.project)||!valid(state.original))throw Error('Draft is too large or invalid. Download to preserve it.');
 const data={schema:2,project:state.project,original:state.original,file:state.file,savedAt:new Date().toISOString(),history:state.history.slice(-5).map(v=>({project:v.project,original:v.original||v.project,title:String(v.title||'Checkpoint').slice(0,80),savedAt:v.savedAt||new Date().toISOString()}))};
 const raw=JSON.stringify(data);if(new TextEncoder().encode(raw).length>MAX_BYTES)throw Error('Code Studio reached its 2 MiB storage limit. Export or delete older checkpoints.');
 storage.setItem(STUDIO_KEY,raw);return data.savedAt;
}
export function sourceLocation(project,id){
 if(!Number.isSafeInteger(id)||id<0)return null;
 const name=project.format==='react'?'App.jsx':'index.html',text=project.files[name]||'';
 const pattern=new RegExp('data-veyra-node\\s*=\\s*(?:["\\\']'+id+'["\\\']|\\{\\s*["\\\']?'+id+'["\\\']?\\s*\\})','g');
 const matches=[...text.matchAll(pattern)];if(matches.length!==1)return null;
 const marker=matches[0],from=text.lastIndexOf('<',marker.index);let end=text.indexOf('>',marker.index);
 if(from<0||end<0)return null;
 return {file:name,from,to:end+1,id};
}
