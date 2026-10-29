// Compile JSX with the installed Vite transform and resolve local modules recursively.
import {readFile} from 'node:fs/promises';
import {transformWithOxc} from 'vite';
const cache=new Map();
export async function loadComponent(file){
  if(cache.has(file.href))return cache.get(file.href);
  let {code}=await transformWithOxc(await readFile(file,'utf8'),file.pathname,{jsx:{runtime:'classic'}});
  const specs=[...code.matchAll(/from "([^"]+)"/g)].map(m=>m[1]);
  for(const spec of new Set(specs)){
    let replacement;
    if(spec==='react')replacement=new URL('../node_modules/react/index.js',import.meta.url).href;
    else if(spec.startsWith('.')){
      const target=new URL(spec,file);
      if(spec.endsWith('.jsx'))replacement=await compileURL(target);
      else replacement=target.href;
    }else continue;
    code=code.replaceAll(`from "${spec}"`,`from "${replacement}"`);
  }
  const url='data:text/javascript;base64,'+Buffer.from(code).toString('base64');cache.set(file.href,url);return url;
}
async function compileURL(file){return loadComponent(file);}
