const assert=require('assert'),api=require('./roaming.js');
function sample(){return {epoch:'session',serverUptimeMs:5000,dropped:0,clientDropped:0,clientEvictions:0,gap:false,cacheState:'current',events:[{sequence:1,uptimeMs:0,kind:'observed',mac:'02:00:00:00:00:01',before:0,after:1,cause:'unknown'}]};}
let h=sample();assert(api.valid(h));assert.equal(api.relation(null,h),'new_session');assert.equal(api.relation(h,sample()),'unchanged');
for(const mutate of [x=>x.events[0].mac='<img>',x=>x.events[0].cause='steering',x=>x.events[0].uptimeMs=6000,x=>x.events.push(x.events[0]),x=>x.events[0].sequence=9007199254740992,x=>x.events=Array(257).fill(x.events[0])]){let x=sample();mutate(x);assert(!api.valid(x));}
let next=sample();next.epoch='restart';assert.equal(api.relation(h,next),'new_session');next=sample();next.serverUptimeMs=4000;assert.equal(api.relation(h,next),'older');
next=sample();next.events.push({sequence:2,uptimeMs:5000,kind:'band_change',mac:'02:00:00:00:00:01',before:1,after:2,cause:'unknown'});assert.equal(api.relation(h,next),'updated');
console.log('PASS bounded roaming history, session reset, old response and evidence validation');

let callback,states=[],data=[],timers=new Map(),id=0;
const poller=api.create(require('./refresh.js'),{request:done=>{callback=done;return ()=>{};},setTimer:(fn,delay)=>{let n=++id;timers.set(n,{fn,delay});return n;},clearTimer:n=>timers.delete(n),onData:x=>data.push(x),onState:x=>states.push(x.state)});
poller.start();callback(null,sample());assert.equal(data.length,1);
poller.retry();let newer=sample();newer.serverUptimeMs=10000;callback(null,newer);assert.equal(data.length,1);
poller.retry();callback(null,sample());assert.equal(states.at(-1),'Stale');assert.equal(data.length,1);
poller.setVisible(false);assert.equal(states.at(-1),'Paused');poller.setVisible(true);newer=sample();newer.epoch='restarted';callback(null,newer);assert.equal(data.length,2);
poller.stop();assert.equal(timers.size,0);
console.log('PASS shared history refresh, unchanged-event metadata, old-response rejection and new session');

let counters=sample();counters.clientDropped=1;assert.equal(api.relation(sample(),counters),'updated');counters=sample();counters.gap=true;assert.equal(api.relation(sample(),counters),'updated');

(function(){
 var r=require('./roaming.js'),assert=require('assert');
 var a={ownerAvailable:true,dropped:'0',rejected:'0',missing:'0',events:[{session:'ffffffffffffffff',sequence:1,uptimeMs:5,mac:'02:00:00:00:00:01',radio:0,bss:0,cookie:1,operation:'allow',stage:'ioctl_accepted',result:0,outcome:'unknown'}]};
 assert(r.actionsValid(a,5));a.events[0].outcome='roamed';assert(!r.actionsValid(a,5));a.events[0].outcome='unknown';
 a.events.push(Object.assign({},a.events[0]));assert(!r.actionsValid(a,5));a.events.pop();
 a.dropped='18446744073709551616';assert(!r.actionsValid(a,5));a.dropped='18446744073709551615';assert(r.actionsValid(a,5));
 a.events[0].session='0000000000000000';assert(!r.actionsValid(a,5));
 console.log('PASS bounded action browser schema, exact 64-bit identities, replay and invented outcome rejection');
})();
