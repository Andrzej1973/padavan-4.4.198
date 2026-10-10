const assert=require('assert'),api=require('./roaming.js');
function sample(){return {epoch:'session',serverUptimeMs:5000,dropped:0,clientDropped:0,clientEvictions:0,gap:false,cacheState:'current',events:[{sequence:1,uptimeMs:0,kind:'observed',mac:'02:00:00:00:00:01',before:0,after:1,cause:'unknown'}]};}
let h=sample();assert(api.valid(h));assert.equal(api.relation(null,h),'new_session');assert.equal(api.relation(h,sample()),'unchanged');
for(const mutate of [x=>x.events[0].mac='<img>',x=>x.events[0].cause='steering',x=>x.events[0].uptimeMs=6000,x=>x.events.push(x.events[0]),x=>x.events[0].sequence=9007199254740992,x=>x.events=Array(257).fill(x.events[0])]){let x=sample();mutate(x);assert(!api.valid(x));}
let next=sample();next.epoch='restart';assert.equal(api.relation(h,next),'new_session');next=sample();next.serverUptimeMs=4000;assert.equal(api.relation(h,next),'older');
next=sample();next.events.push({sequence:2,uptimeMs:5000,kind:'band_change',mac:'02:00:00:00:00:01',before:1,after:2,cause:'unknown'});assert.equal(api.relation(h,next),'updated');
console.log('PASS bounded roaming history, session reset, old response and evidence validation');
