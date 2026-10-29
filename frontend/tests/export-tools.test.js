import test from 'node:test';import assert from 'node:assert/strict';
import {promptSections,checklistText,exportPrompt} from '../src/export-tools.js';
test('section copy uses the edited eight-section text rather than stale generated output',()=>{
 const text='# Brief\n## 1. Objective\nEdited objective\n## 2. Structure\nTree\n## 8. Accuracy notes\nUnknown';const parts=promptSections(text);assert.equal(parts.length,3);assert.equal(parts[0].text,'## 1. Objective\nEdited objective');assert.equal(parts[2].text,'## 8. Accuracy notes\nUnknown');assert.deepEqual(promptSections('Free form edited text'),[]);
});
test('exports preserve exact manual text, create downloads and revoke object URLs',async()=>{
 let blob,clicked=false,removed=false,revoked=false;const link={remove:()=>{removed=true;},click:()=>{clicked=true;}};const env={URL:{createObjectURL:b=>{blob=b;return 'blob:test';},revokeObjectURL:u=>{assert.equal(u,'blob:test');revoked=true;}},document:{createElement:()=>link,body:{appendChild:n=>assert.equal(n,link)}},setTimeout:f=>f()};
 exportPrompt('Exact edited text\n<inert>','md',env);assert.equal(await blob.text(),'Exact edited text\n<inert>');assert.equal(blob.type,'text/markdown;charset=utf-8');assert.equal(link.download,'veyra-prompt.md');assert.ok(clicked&&removed&&revoked);assert.throws(()=>exportPrompt('x','html',env),/Unsupported/);
});
test('checklists distinguish missing evidence and cannot invent a report for restored text',()=>{
 assert.match(checklistText(null),/No generation evidence/);const text=checklistText({assetChecklist:['Supply image for node 4'],missing:['Hover capture'],limitations:['No pixel comparison']});assert.match(text,/- \[ \] Supply image for node 4/);assert.match(text,/Manual prompt edits do not alter/);assert.doesNotMatch(text,/accuracy.*%/);
});
