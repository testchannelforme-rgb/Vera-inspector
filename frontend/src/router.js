const routes=new Set(['','inspector','privacy','cookies','terms','about','contact','preferences','brand']);
export function routeFromHash(hash){const [path,query='']=String(hash||'#/').replace(/^#\/?/,'').split('?');return {page:routes.has(path)?path:'not-found',section:new URLSearchParams(query).get('section')};}
