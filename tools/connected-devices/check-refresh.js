'use strict';
const assert=require('assert');const refresh=require('./refresh.js');
let now=0,nextId=0,timers=new Map(),requests=[],rows=[],states=[];
function tick(delta){const end=now+delta;while(true){let pair=null;for(const [id,t] of timers)if(t.at<=end&&(!pair||t.at<pair[1].at))pair=[id,t];if(!pair)break;now=pair[1].at;timers.delete(pair[0]);pair[1].fn();}now=end;}
const poller=refresh.create({setTimer:(fn,delay)=>{const id=++nextId;timers.set(id,{fn,at:now+delay});return id;},clearTimer:id=>timers.delete(id),request:done=>{const req={done,aborted:false};requests.push(req);return ()=>{req.aborted=true;done(new Error('aborted'));};},onData:s=>rows.push(s),onState:s=>states.push(s)});
const snapshot=(sequence,epoch='boot-A')=>({epoch,sequence,devices:[],observedAt:123});
poller.start();poller.start();poller.retry();assert.strictEqual(requests.length,1);
requests[0].done(null,snapshot(2));assert.strictEqual(rows.length,1);assert.strictEqual(rows[0].observedAt,123);
tick(4999);assert.strictEqual(requests.length,1);tick(1);assert.strictEqual(requests.length,2);
requests[1].done(null,snapshot(2));assert.strictEqual(rows.length,1); // Cached data does not renew observation or redraw rows.
tick(5000);requests[2].done(new Error('offline'));assert.strictEqual(states.at(-1).state,'Stale');assert.strictEqual(rows.length,1);
tick(5000);requests[3].done(new Error('offline'));tick(9999);assert.strictEqual(requests.length,4);tick(1);assert.strictEqual(requests.length,5);
requests[4].done(null,snapshot(3));assert.strictEqual(rows.length,2);assert.strictEqual(states.at(-1).failures,0);
tick(5000);const old=requests[5];poller.setVisible(false);assert.ok(old.aborted);tick(60000);assert.strictEqual(requests.length,6);
poller.setVisible(true);assert.strictEqual(requests.length,7);old.done(null,snapshot(99));assert.strictEqual(rows.length,2);
requests[6].done(null,snapshot(1));assert.strictEqual(states.at(-1).state,'Stale');assert.strictEqual(rows.length,2);
tick(5000);requests[7].done(null,snapshot(0,'boot-B'));assert.strictEqual(rows.length,3); // New collector epoch may reset sequence.
tick(5000);const timed=requests[8];tick(5000);assert.ok(timed.aborted);assert.strictEqual(states.at(-1).state,'Stale');timed.done(null,snapshot(100,'boot-B'));assert.strictEqual(rows.length,3);
poller.stop();tick(60000);assert.strictEqual(requests.length,9);assert.strictEqual(timers.size,0);
let staleCallback,staleStates=[];
const serverStale=refresh.create({request:done=>{staleCallback=done;return ()=>{};},setTimer:()=>1,clearTimer:()=>{},onState:s=>staleStates.push(s)});
serverStale.start();const staleSnapshot=snapshot(1);staleSnapshot.cacheState='stale';staleCallback(null,staleSnapshot);assert.strictEqual(staleStates.at(-1).state,'Stale');serverStale.stop();
assert.ok(!refresh.validSnapshot(snapshot(-1)));assert.ok(!refresh.validSnapshot({epoch:'a',sequence:1,devices:Array(129)}));
assert.ok(!refresh.validSnapshot({epoch:'a',sequence:NaN,devices:[]}));
let callback,renderStates=[],renderTimers=new Map(),renderId=0;
const renderFault=refresh.create({request:done=>{callback=done;return ()=>{throw new Error('transport abort error');};},setTimer:(fn,delay)=>{const id=++renderId;renderTimers.set(id,{fn,delay});return id;},clearTimer:id=>renderTimers.delete(id),onData:()=>{throw new Error('render failure');},onState:s=>renderStates.push(s)});
renderFault.start();callback(null,snapshot(1));assert.strictEqual(renderStates.at(-1).state,'Unavailable');assert.strictEqual(renderTimers.size,1);
renderFault.retry();renderFault.setVisible(false);assert.strictEqual(renderStates.at(-1).state,'Paused');renderFault.stop();assert.strictEqual(renderTimers.size,0);
console.log('PASS single-flight refresh, cache sequence, error recovery/backoff, hidden pause/resume, timeout abort, stale preservation and collector epoch reset');
