// Only deliberate user actions write these app-specific keys. No network access.
export const PREFERENCES_KEY='veyra.preferences.v1';
export const HISTORY_KEY='veyra.prompt-history.v1';
export const HISTORY_LIMIT=20;
export const HISTORY_BYTES=512*1024;
export const PROMPT_LIMIT=60000;
export const PRESETS=[
  {id:'faithful',label:'Faithful Recreation',description:'Keep the captured viewport and measured styles as the starting point.'},
  {id:'responsive-first',label:'Responsive First',description:'Add labelled fluid-layout recommendations and a responsive verification plan.'},
  {id:'accessible-implementation',label:'Accessible Implementation',description:'Prioritize semantics, keyboard operation, focus and documented visual tradeoffs.'},
  {id:'clean-production-code',label:'Clean Production Code',description:'Propose coherent components, scoped tokens and small, testable implementation steps.'},
  {id:'maximum-visual-detail',label:'Maximum Visual Detail',description:'Use up to 28 sampled nodes, retaining attributed paint, pseudo-elements and CSS detail.'},
];
const allowedPreset=new Set(PRESETS.map(p=>p.id));
const bytes=text=>new TextEncoder().encode(text).length;
export function browserStorage(){try{return globalThis.localStorage??null;}catch{return null;}}
function read(storage,key){if(!storage)return null;try{return storage.getItem(key);}catch{throw new Error('Browser storage is blocked. Export your prompt to keep a copy.');}}
export function readPreferences(storage=browserStorage()){
  try {const raw=read(storage,PREFERENCES_KEY);if(!raw||raw.length>1000)return {historyEnabled:false,tutorialDismissed:false};const p=JSON.parse(raw);return {historyEnabled:p?.historyEnabled===true,tutorialDismissed:p?.tutorialDismissed===true};}
  catch{return {historyEnabled:false,tutorialDismissed:false};}
}
export function setPreferences(patch,storage=browserStorage()){
  if(!storage)throw new Error('Browser storage is unavailable. Export your prompt instead.');
  const next={...readPreferences(storage),...patch};
  const safe={historyEnabled:next.historyEnabled===true,tutorialDismissed:next.tutorialDismissed===true};
  // Remove prompt data first so disabling never falsely reports a completed deletion.
  try {if(!safe.historyEnabled)storage.removeItem(HISTORY_KEY);storage.setItem(PREFERENCES_KEY,JSON.stringify(safe));}
  catch{throw new Error('Could not update device preferences. Your browser may be blocking storage.');}
  return safe;
}
export function readHistory(storage=browserStorage()){
  if(!readPreferences(storage).historyEnabled)return [];
  const raw=read(storage,HISTORY_KEY);if(!raw)return [];
  if(bytes(raw)>HISTORY_BYTES)throw new Error('Saved history exceeds the storage limit. Clear local history in Data preferences.');
  let parsed;try{parsed=JSON.parse(raw);}catch{throw new Error('Saved history could not be read. Export any open draft, then clear local history.');}
  if(!Array.isArray(parsed)||parsed.length>HISTORY_LIMIT)throw new Error('Saved history has an unsupported format. Clear it in Data preferences.');
  return parsed.map(entry=>{
    if(!entry||typeof entry.id!=='string'||entry.id.length>100||typeof entry.text!=='string'||entry.text.length>PROMPT_LIMIT||typeof entry.title!=='string'||entry.title.length>80||typeof entry.savedAt!=='string'||!Number.isFinite(Date.parse(entry.savedAt)))throw new Error('A saved version is invalid. Clear local history in Data preferences.');
    // Stored strings remain inert React text. Reports are deliberately not persisted.
    const p=entry.preferences||{};
    return {id:entry.id,text:entry.text,title:entry.title,savedAt:entry.savedAt,preferences:{preset:allowedPreset.has(p.preset)?p.preset:'faithful',scope:['element','section','page'].includes(p.scope)?p.scope:'element',target:['react','html-css','html-css-js'].includes(p.target)?p.target:'react',detail:['concise','detailed','highly-detailed'].includes(p.detail)?p.detail:'detailed',style:['faithful','responsive','accessible'].includes(p.style)?p.style:'faithful'}};
  });
}
export function updateHistory(operation,storage=browserStorage()){
  if(!storage||!readPreferences(storage).historyEnabled)throw new Error('Enable local prompt history before saving on this device.');
  const current=readHistory(storage),next=operation(current);
  if(!Array.isArray(next)||next.length>HISTORY_LIMIT)throw new Error(`History is full (${HISTORY_LIMIT} versions). Delete a version or export it before saving another.`);
  const raw=JSON.stringify(next);
  if(bytes(raw)>HISTORY_BYTES)throw new Error('Local history has reached 512 KiB. Export and delete older versions before saving.');
  try {storage.setItem(HISTORY_KEY,raw);}catch{throw new Error('The browser could not save this version. Your open draft is preserved; export it instead.');}
  return readHistory(storage);
}
export function saveVersion(text,title,preferences,storage=browserStorage()){
  if(typeof text!=='string'||!text.trim()||text.length>PROMPT_LIMIT)throw new Error('Save a nonempty prompt of at most 60,000 characters.');
  const id=globalThis.crypto?.randomUUID?.()??`v-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const entry={id,title:String(title||'Untitled prompt').trim().slice(0,80)||'Untitled prompt',text,savedAt:new Date().toISOString(),preferences};
  return updateHistory(list=>[entry,...list],storage);
}
export function deleteVersion(id,storage=browserStorage()){return updateHistory(list=>list.filter(e=>e.id!==id),storage);}
export function duplicateVersion(id,storage=browserStorage()){
  const source=readHistory(storage).find(e=>e.id===id);if(!source)throw new Error('This version no longer exists.');
  return saveVersion(source.text,`${source.title} · copy`.slice(0,80),source.preferences,storage);
}
export function clearLocalData(storage=browserStorage()){
  if(!storage)throw new Error('Browser storage is unavailable.');
  try {storage.removeItem(HISTORY_KEY);storage.removeItem(PREFERENCES_KEY);storage.removeItem('veyra.code-studio.v2');}catch{throw new Error('Could not clear app data. Use your browser site-data settings.');}
}
