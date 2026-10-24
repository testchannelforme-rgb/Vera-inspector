export async function api(path,body,method='POST') {
  const controller=new AbortController();
  const timeout=setTimeout(()=>controller.abort(),30000);
  try {
    const response=await fetch('/api'+path,{method,signal:controller.signal,headers:{'Content-Type':'application/json','X-Veyra-Client':'inspector-v0.1'},...(body===undefined?{}:{body:JSON.stringify(body)})});
    const data=await response.json();
    if(!response.ok) throw new Error(typeof data.detail==='string'?data.detail:'Invalid request. Check the URL, viewport, or selected element.');
    return data;
  } catch(error) {
    if(error.name==='AbortError') throw new Error('The browser did not respond in time. Open the site again.');
    throw error;
  } finally {clearTimeout(timeout);}
}
