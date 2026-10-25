export function promptBody(session,frame,inspection,preferences) {
  if(!session || !frame?.frameId) throw new Error('Open a website first.');
  if(preferences.scope!=='page' && !inspection?.element?.referenceId) throw new Error('Select an element first.');
  return {sessionId:session,frameId:frame.frameId,referenceId:preferences.scope==='page'?null:inspection.element.referenceId,...preferences};
}

export async function copyPrompt(text,textarea,clipboard=globalThis.navigator?.clipboard) {
  if(!text)throw new Error('Generate a prompt first.');
  try {
    if(!clipboard?.writeText)throw new Error('Clipboard unavailable');
    await clipboard.writeText(text);return 'Prompt copied.';
  } catch {
    textarea?.focus();textarea?.select();
    return 'Clipboard unavailable. The prompt is selected; use Copy from your browser or keyboard.';
  }
}

export function generationGate() {
  let active=false;
  return async operation=>{
    if(active)return false;
    active=true;
    try {await operation();return true;}finally{active=false;}
  };
}
