export async function api(path,body,method='POST',timeoutMs=45000) {
  const controller=new AbortController();
  const timeout=setTimeout(()=>controller.abort(),timeoutMs);
  try {
    const response=await fetch('/api'+path,{method,signal:controller.signal,headers:{'Content-Type':'application/json','X-Veyra-Client':'inspector-v0.1'},...(body===undefined?{}:{body:JSON.stringify(body)})});
    const data=await response.json();
    if(!response.ok){const error=new Error(typeof data.detail==='string'?data.detail:'Invalid request. Check the URL, viewport, or selected element.');error.code=data.code;error.diagnostics=data.diagnostics;throw error;}
    return data;
  } catch(error) {
    if(error.name==='SyntaxError'){const failure=new Error('The browser response could not be decoded. The screenshot/inspection transfer may have been interrupted. Refresh or reopen the site.');failure.code='response-transfer-failure';throw failure;}
    if(error.name==='AbortError') throw new Error('The browser did not respond in time. Open the site again.');
    throw error;
  } finally {clearTimeout(timeout);}
}
