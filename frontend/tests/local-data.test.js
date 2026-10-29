import test from 'node:test';
import assert from 'node:assert/strict';
import {HISTORY_KEY,PREFERENCES_KEY,HISTORY_LIMIT,readHistory,readPreferences,setPreferences,saveVersion,duplicateVersion,deleteVersion,clearLocalData} from '../src/local-data.js';
const store=()=>{const map=new Map();return {getItem:k=>map.get(k)??null,setItem:(k,v)=>map.set(k,String(v)),removeItem:k=>map.delete(k),map};};
const prefs={preset:'responsive-first',scope:'section',detail:'detailed',target:'react',style:'faithful'};
test('history requires explicit opt-in, saves exact manual edits, restores and duplicates immutable snapshots',()=>{
 const s=store();assert.deepEqual(readHistory(s),[]);assert.equal(s.map.size,0);assert.throws(()=>saveVersion('edited','Title',prefs,s),/Enable/);
 setPreferences({historyEnabled:true},s);let entries=saveVersion('My manually edited prompt <script>inert</script>','First',prefs,s);assert.equal(entries[0].text,'My manually edited prompt <script>inert</script>');assert.equal(entries[0].preferences.preset,'responsive-first');
 const id=entries[0].id;entries=duplicateVersion(id,s);assert.equal(entries.length,2);assert.notEqual(entries[0].id,id);assert.equal(entries[1].text,entries[0].text);assert.match(entries[0].title,/copy/);assert.equal(deleteVersion(id,s).length,1);
 assert.equal(readHistory(s)[0].text,entries[0].text);
});
test('limits never evict saved work silently or overwrite the open draft',()=>{
 const s=store();setPreferences({historyEnabled:true},s);for(let i=0;i<HISTORY_LIMIT;i++)saveVersion('draft '+i,'Version '+i,prefs,s);const previous=s.getItem(HISTORY_KEY);
 assert.throws(()=>saveVersion('another','Full',prefs,s),/full/);assert.equal(s.getItem(HISTORY_KEY),previous);
 const big=store();setPreferences({historyEnabled:true},big);for(let i=0;i<4;i++)saveVersion('α'.repeat(60000),'Large',prefs,big);const before=big.getItem(HISTORY_KEY);assert.throws(()=>saveVersion('α'.repeat(60000),'Too much',prefs,big),/512 KiB/);assert.equal(big.getItem(HISTORY_KEY),before);
});
test('blocked, corrupt, oversized and tampered storage fails visibly and inertly',()=>{
 const s=store();setPreferences({historyEnabled:true},s);s.setItem(HISTORY_KEY,'not json');assert.throws(()=>readHistory(s),/could not be read/);s.setItem(HISTORY_KEY,JSON.stringify([{id:'1',text:'safe',title:'Title',savedAt:'invalid'}]));assert.throws(()=>readHistory(s),/invalid/);
 s.setItem(HISTORY_KEY,'x'.repeat(530000));assert.throws(()=>readHistory(s),/storage limit/);
 assert.throws(()=>saveVersion('draft','Title',prefs,null),/Enable/);
 const blocked={getItem:()=>null,setItem:()=>{throw Error('quota');},removeItem:()=>{}};assert.throws(()=>setPreferences({historyEnabled:true},blocked),/Could not update/);
});
test('disabling and clearing remove only VEYRA data; no hidden auto-save or upload',()=>{
 const s=store();s.setItem('another-app','keep');setPreferences({historyEnabled:true},s);saveVersion('draft','Saved',prefs,s);setPreferences({historyEnabled:false},s);assert.equal(s.getItem(HISTORY_KEY),null);assert.deepEqual(readHistory(s),[]);assert.equal(s.getItem('another-app'),'keep');
 clearLocalData(s);assert.equal(s.getItem(PREFERENCES_KEY),null);assert.equal(s.getItem('another-app'),'keep');assert.equal(readPreferences(s).tutorialDismissed,false);
});
