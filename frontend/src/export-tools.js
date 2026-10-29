export function promptSections(text){
  const sections=[];const regex=/^## ([1-8])\. ([^\n]+)$/gm;const matches=[...text.matchAll(regex)];
  for(let i=0;i<matches.length;i++)sections.push({id:matches[i][1],title:matches[i][2],text:text.slice(matches[i].index,matches[i+1]?.index??text.length).trim()});
  return sections;
}
export function checklistText(report){
  if(!report)return '# Asset and missing-information checklist\n\nNo generation evidence report is attached. Generate a new prompt from a live selection; restored text does not establish measured evidence.\n';
  return ['# Asset and missing-information checklist','', 'Based on the last generation evidence snapshot. Manual prompt edits do not alter these findings.','',...report.assetChecklist.map(x=>'- [ ] '+x),'','## Missing evidence',...report.missing.map(x=>'- [ ] '+x),'','## Limitations',...report.limitations.map(x=>'- '+x)].join('\n');
}
export function exportPrompt(text,format='txt',environment=globalThis,basename='veyra-prompt'){
  if(!text)throw new Error('There is no text to export.');
  if(!['txt','md'].includes(format))throw new Error('Unsupported export format.');
  if(!/^[a-z0-9-]{1,60}$/.test(basename))throw new Error('Invalid export filename.');
  const type=format==='md'?'text/markdown;charset=utf-8':'text/plain;charset=utf-8';
  const url=environment.URL.createObjectURL(new Blob([text],{type}));
  const link=environment.document.createElement('a');link.href=url;link.download=`${basename}.${format}`;
  try {environment.document.body.appendChild(link);link.click();}finally{link.remove();environment.setTimeout(()=>environment.URL.revokeObjectURL(url),1000);}
}
