'use strict';
var assert=require('assert'),schema=require('./rssi.js');
var h={evicted:'0',radios:[],events:[]};
for(var i=0;i<2;i++)h.radios.push({radio:i,available:false,attempted:false,error:0,failures:'0',recoveries:'0',lastSuccessMs:'0',missing:'0',restarts:'0'});
assert(schema.valid(h));
var e={session:'ffffffffffffffffffffffffffffffff',sequence:'18446744073709551615',uptimeMs:'18446744073709551615',attempt:4294967295,mac:'02:11:22:33:44:55',radio:0,bss:15,stage:'frame_submitted',outcome:'unknown'};
h.events=[e];assert(schema.valid(h));
function reject(change){var copy=JSON.parse(JSON.stringify(h));change(copy);assert(!schema.valid(copy));}
reject(function(x){x.events[0].sequence='18446744073709551616';});
reject(function(x){x.events[0].sequence=1;});
reject(function(x){x.events[0].session='00000000000000000000000000000000';});
reject(function(x){x.events[0].stage='roamed';});
reject(function(x){x.events.push(x.events[0]);});
reject(function(x){x.radios[0].available=true;});
h.events.push(Object.assign({},e,{radio:1}));assert(schema.valid(h));
h.events.push(Object.assign({},e,{session:'00000000000000000000000000000001',sequence:'1'}));assert(schema.valid(h));
console.log('PASS RSSI browser schema: exact maximum counters, separate radios/sessions, invalid and duplicate rejection');
