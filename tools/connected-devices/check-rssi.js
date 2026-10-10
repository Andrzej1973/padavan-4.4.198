'use strict';
var assert=require('assert'),schema=require('./rssi.js');
var h={cacheState:'current',evicted:'0',radios:[],events:[]};
for(var i=0;i<2;i++)h.radios.push({radio:i,available:true,attempted:true,error:0,failures:'0',recoveries:'0',lastSuccessMs:'0',missing:'0',restarts:'0'});
assert(schema.valid(h));
var e={session:'ffffffffffffffffffffffffffffffff',sequence:'18446744073709551615',uptimeMs:'18446744073709551615',attempt:4294967295,mac:'02:11:22:33:44:55',radio:0,bss:15,stage:'frame_submitted',outcome:'unknown'};
h.events=[e];assert(schema.valid(h));
function reject(change){var copy=JSON.parse(JSON.stringify(h));change(copy);assert(!schema.valid(copy));}
reject(function(x){x.events[0].sequence='18446744073709551616';});
reject(function(x){x.events[0].sequence=1;});
reject(function(x){x.events[0].session='00000000000000000000000000000000';});
reject(function(x){x.events[0].stage='roamed';});
reject(function(x){x.cacheState='stale';});
reject(function(x){x.events.push(x.events[0]);});
reject(function(x){x.radios[0].attempted=false;});
h.events.push(Object.assign({},e,{radio:1}));assert(schema.valid(h));
h.events.push(Object.assign({},e,{session:'00000000000000000000000000000001',sequence:'1'}));assert(schema.valid(h));
console.log('PASS RSSI browser schema: exact maximum counters, separate radios/sessions, invalid and duplicate rejection');

(function(){
 var callback,states=[],data=[],timers=new Map(),id=0,aborts=0;
 var poller=schema.create(require('./refresh.js'),{request:function(done){callback=done;return function(){aborts++;};},setTimer:function(fn,delay){var n=++id;timers.set(n,{fn:fn,delay:delay});return n;},clearTimer:function(n){timers.delete(n);},onData:function(x){data.push(x);},onState:function(x){states.push(x.state);}});
 poller.start();callback(null,h);assert.strictEqual(data.length,1);
 poller.retry();callback(new Error('503'));assert.strictEqual(states.at(-1),'Stale');assert.strictEqual(data.length,1);
 poller.retry();var bad=JSON.parse(JSON.stringify(h));bad.events[0].stage='roamed';callback(null,bad);assert.strictEqual(states.at(-1),'Stale');assert.strictEqual(data.length,1);
 poller.retry();callback(null,h);assert.strictEqual(states.at(-1),'Current');assert.strictEqual(data.length,1);
 poller.retry();poller.setVisible(false);assert.strictEqual(states.at(-1),'Paused');assert.strictEqual(aborts,1);
 poller.setVisible(true);var newer=JSON.parse(JSON.stringify(h));newer.evicted='1';callback(null,newer);assert.strictEqual(data.length,2);
 poller.retry();var stale=JSON.parse(JSON.stringify(newer));stale.cacheState='stale';stale.radios[0].available=false;stale.radios[0].error=5;callback(null,stale);assert.strictEqual(states.at(-1),'Stale');
 poller.stop();assert.strictEqual(timers.size,0);
 console.log('PASS RSSI shared refresh retains data on network/schema failure, recovers, pauses and cancels timers');
})();
