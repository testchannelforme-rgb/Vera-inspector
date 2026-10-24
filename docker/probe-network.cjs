const net=require('node:net');
function connect(host,port,allowed){return new Promise((resolve,reject)=>{
 const socket=net.connect({host,port});
 socket.setTimeout(1200);
 socket.once('connect',()=>{socket.destroy();allowed?resolve():reject(Error(`Unexpected direct connection to ${host}:${port}`));});
 const blocked=()=>{socket.destroy();allowed?reject(Error('Required gateway is unreachable')):resolve();};
 socket.once('timeout',blocked);socket.once('error',blocked);
});}
(async()=>{
 // The gateway deliberately listens on 9999 as a live canary. Firewall permits
 // only 8888. A mere ECONNREFUSED at an unused port would not prove this rule.
 await connect('172.30.88.2',8888,true);
 await connect('172.30.88.2',9999,false);
 await connect('127.0.0.1',3000,false);
 await connect('169.254.169.254',80,false);
 await connect('1.1.1.1',443,false);
 await connect('2606:4700:4700::1111',443,false);
 console.log('PASS: gateway reachable; live canary, control loopback, metadata, direct public IPv4/IPv6 blocked.');
})().catch(error=>{console.error(error.message);process.exit(1);});
