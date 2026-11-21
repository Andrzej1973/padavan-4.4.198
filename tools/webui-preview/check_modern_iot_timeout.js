'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(process.argv[2],'utf8');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 for(const stage of ['headers','body']){
  const nodes={},timers=new Map();let timerId=0,resolveLate,signal,calls=0;
  const timeout=fn=>{timers.set(++timerId,fn);return timerId;};
  const window={setTimeout:timeout};
  vm.runInNewContext(source,{window,document:{createElement(){return {
   set innerHTML(html){for(const m of html.matchAll(/id="([^"]+)"/g))nodes[m[1]]={value:'',disabled:false,checked:false,textContent:''};},
   querySelector(sel){return nodes[sel.slice(1)];}};}},
   AbortController,URLSearchParams,setTimeout:timeout,clearTimeout:id=>timers.delete(id),
   fetch:(url,options)=>{
    calls++;signal=options.signal;
    const late=new Promise(resolve=>{resolveLate=resolve;});
    return stage==='headers'?late:Promise.resolve({ok:true,json:()=>late});
   }});
  window.wrModernIot.render({append(){}});
  nodes['iot-refresh'].onclick();await tick();
  assert.equal(calls,1);assert.equal(timers.size,1);
  [...timers.values()][0]();
  assert(signal.aborted);assert(!nodes['iot-refresh'].disabled);
  assert(nodes['iot-save'].disabled);
  const message=nodes['iot-message'].textContent;
  const reply={token:'a'.repeat(32)};
  resolveLate(stage==='headers'?{ok:true,json:async()=>reply}:reply);
  await tick();await tick();
  assert.equal(calls,1,'late token must not launch view request');
  assert.equal(nodes['iot-message'].textContent,message);
  assert(nodes['iot-save'].disabled);assert.equal(timers.size,0);
 }
 console.log('PASS Modern IoT timeout: headers/body stalls terminate once, abort signal, controls recover, late token ignored, no follow-up request');
})().catch(e=>{console.error(e);process.exitCode=1;});
