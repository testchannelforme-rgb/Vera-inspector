import {zipSync,strToU8} from 'fflate';
export const PROJECT_LIMIT=180000;
export function projectSize(project){return Object.values(project?.files||{}).reduce((n,s)=>n+new TextEncoder().encode(s).length,0);}
export function editProject(project,name,text){
 const next={...project,files:{...project.files,[name]:text}};
 if(projectSize(next)>PROJECT_LIMIT)throw Error('Project exceeds 180 KB. Your previous code was kept.');
 return next;
}
export function exportProject(project){
 return zipSync(Object.fromEntries(Object.entries(project.files).map(([name,text])=>[name,strToU8(text)])),{level:6});
}
export function saveDownload(bytes,name,type='application/zip'){
 const href=URL.createObjectURL(new Blob([bytes],{type}));
 const a=document.createElement('a');a.href=href;a.download=name;a.click();
 setTimeout(()=>URL.revokeObjectURL(href),1000);
}
export function changedFiles(before,after){return Object.keys(after.files).filter(k=>before?.files[k]!==after.files[k]);}

export function fidelityDiagnostics(expected,observed){
 const actual=new Map((observed?.nodes||[]).slice(0,55).map(n=>[n.id,n]));
 const report={measuredNodes:actual.size,missing:0,sizeDifferences:0,typographyDifferences:0,colorDifferences:0,overflow:observed?.overflow===true};
 for(const e of (expected||[]).slice(0,55)){
  const n=actual.get(e.id);if(!n){report.missing++;continue;}
  if(['width','height'].some(k=>Number.isFinite(e[k])&&Number.isFinite(n[k])&&Math.abs(e[k]-n[k])>Math.max(2,e[k]*.05)))report.sizeDifferences++;
  if(e.fontSize&&n.fontSize!==e.fontSize)report.typographyDifferences++;
  if(e.color&&n.color!==e.color)report.colorDifferences++;
 }
 return report;
}
