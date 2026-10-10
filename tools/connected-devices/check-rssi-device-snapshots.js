'use strict';
/* Offline validation of privately saved authenticated router responses. */
var fs=require('fs'),assert=require('assert'),schema=require('./rssi.js');
if(process.argv.length!==4)throw new Error('Usage: node check-rssi-device-snapshots.js first.json second.json');
function read(path){var text=fs.readFileSync(path,'utf8');assert(Buffer.byteLength(text)<=100000,'Response exceeds monitor bound');var h=JSON.parse(text);assert(schema.valid(h),'Invalid RSSI response');return h;}
var first=read(process.argv[2]),second=read(process.argv[3]);
function latest(h,radio){var events=h.events.filter(function(e){return e.radio===radio;});return events.length?events[events.length-1]:null;}
function less(a,b){return a.length<b.length||(a.length===b.length&&a<b);}
var radios=[];
for(var i=0;i<2;i++){
 var a=latest(first,i),b=latest(second,i),same=!!(a&&b&&a.session===b.session);
 if(same)assert(!less(b.sequence,a.sequence),'Sequence regressed within the same adapter session');
 radios.push({radio:i,available:second.radios[i].available,sameObservedSession:same,events:second.events.filter(function(e){return e.radio===i;}).length,missing:second.radios[i].missing,driverOverwritten:second.radios[i].driverOverwritten});
}
console.log(JSON.stringify({schemaValid:true,cacheState:second.cacheState,radios:radios,runtimeRoamingVerified:false},null,2));
