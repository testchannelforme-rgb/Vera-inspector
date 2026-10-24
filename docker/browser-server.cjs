const fs=require('node:fs');
const crypto=require('node:crypto');
const {chromium}=require('playwright');
(async()=>{
  // Writable ephemeral HOME avoids profile/NSS/cache errors on a read-only rootfs.
  process.env.HOME=fs.mkdtempSync('/tmp/veyra-home-');
  process.env.XDG_CACHE_HOME=process.env.HOME+'/cache';
  const token=fs.readFileSync('/run/secrets/control_token','utf8').trim();
  if(!/^[a-f0-9]{64}$/.test(token))throw Error('Invalid control token');
  const firewall=JSON.parse(fs.readFileSync('/run/veyra/firewall.json','utf8'));
  const server=await chromium.launchServer({
    headless:true,channel:'chromium',chromiumSandbox:true,host:'0.0.0.0',port:3000,wsPath:token,
    proxy:{server:'http://172.30.88.2:8888'},
    args:['--disable-quic','--dns-prefetch-disable','--force-webrtc-ip-handling-policy=disable_non_proxied_udp','--proxy-bypass-list=<-loopback>'],
    timeout:20000
  });
  fs.writeFileSync('/run/veyra/ready.json',JSON.stringify({version:'0.2.0',sandboxEnabled:true,firewall,tokenHash:crypto.createHash('sha256').update(token).digest('hex'),startedAt:new Date().toISOString()}));
  console.log('Sandboxed Chromium control service ready on the internal network.');
  let stopping=false;
  server.on('close',()=>process.exit(stopping?0:1));
  for(const signal of ['SIGTERM','SIGINT'])process.on(signal,async()=>{stopping=true;await server.close();});
})().catch(error=>{console.error('Browser startup failed:',String(error).replace(/wss?:\/\/\S+/g,'[control endpoint]'));process.exit(1);});
