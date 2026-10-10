/* Bounded history validation; no inferred steering cause or external AP. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.WRRoaming=factory();})(typeof window!=='undefined'?window:this,function(){
 'use strict';
 function integer(n){return typeof n==='number'&&isFinite(n)&&n>=0&&n<=9007199254740991&&Math.floor(n)===n;}
 function valid(h){
  if(!h||typeof h.epoch!=='string'||!h.epoch.length||h.epoch.length>64||!integer(h.serverUptimeMs)||!integer(h.dropped)||!integer(h.clientDropped)||!integer(h.clientEvictions)||typeof h.gap!=='boolean'||['current','stale','unavailable'].indexOf(h.cacheState)<0||!Array.isArray(h.events)||h.events.length>256)return false;
  var sequence=0;
  for(var i=0;i<h.events.length;i++){
   var e=h.events[i];
   if(!e||!integer(e.sequence)||e.sequence<=sequence||!integer(e.uptimeMs)||e.uptimeMs>h.serverUptimeMs||['observed','band_change','ambiguous','gap'].indexOf(e.kind)<0||!integer(e.before)||e.before>3||!integer(e.after)||e.after>3||e.cause!=='unknown'||typeof e.mac!=='string')return false;
   if(e.kind==='gap'){if(e.mac!==''||e.before!==0||e.after!==0)return false;}
   else if(!/^[0-9A-F]{2}(:[0-9A-F]{2}){5}$/.test(e.mac))return false;
   if(e.kind==='band_change'&&!(e.before===1&&e.after===2||e.before===2&&e.after===1))return false;
   if(e.kind==='observed'&&(e.before!==0||[1,2].indexOf(e.after)<0))return false;
   if(e.kind==='ambiguous'&&e.after!==3)return false;
   sequence=e.sequence;
  }
  return true;
 }
 function relation(previous,next){
  if(!valid(next))return 'invalid';
  if(!previous||previous.epoch!==next.epoch)return 'new_session';
  if(next.serverUptimeMs<previous.serverUptimeMs)return 'older';
  var old=previous.events.length?previous.events[previous.events.length-1].sequence:0;
  var current=next.events.length?next.events[next.events.length-1].sequence:0;
  return current<old?'older':current===old?'unchanged':'updated';
 }
 return {valid:valid,relation:relation};
});
