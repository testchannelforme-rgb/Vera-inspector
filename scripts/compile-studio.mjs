// Parse/bundle only. Generated JS and project configuration are never executed here.
import {createRequire} from 'node:module';
const require=createRequire(new URL('../frontend/package.json',import.meta.url));
const {build,transform}=require('esbuild');
let input='';for await(const chunk of process.stdin){input+=chunk;if(input.length>220000)process.exit(2);}
try {
 const project=JSON.parse(input),files=project.files;
 await transform(files['style.css'],{loader:'css',logLevel:'silent'});
 const result=await build({entryPoints:[project.format==='react'?'main.jsx':'script.js'],bundle:true,write:false,format:'iife',platform:'browser',target:'es2020',jsx:'transform',logLevel:'silent',minify:true,define:{'process.env.NODE_ENV':'"production"'},plugins:[{name:'bounded-project',setup(b){
  b.onResolve({filter:/.*/},args=>{
   if(args.namespace==='file')return;
   if(['react','react-dom/client'].includes(args.path))return {path:require.resolve(args.path)};
   const name=args.path.replace(/^\.\//,'');
   if(!(name in files)||name.includes('/')||name.includes('..')||! /\.(jsx?|css)$/.test(name))throw Error('Unsupported import: '+args.path+'; only project files, react and react-dom/client are supported.');
   return {path:name,namespace:'project'};
  });
  b.onLoad({filter:/.*/,namespace:'project'},args=>({contents:args.path.endsWith('.css')?'':files[args.path],loader:args.path.endsWith('.jsx')?'jsx':'js'}));
 }}]});
 process.stdout.write(JSON.stringify({js:result.outputFiles[0].text}));
}catch(e){process.stdout.write(JSON.stringify({error:(e.errors?.map(e=>e.text).join('\n')||e.message).slice(0,1400)}));process.exitCode=1;}
