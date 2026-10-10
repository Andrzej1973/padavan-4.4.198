/* Bounded history validation; no inferred steering cause or external AP. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.WRRoaming=factory();})(typeof window!=='undefined'?window:this,function(){
 'use strict';
 function integer(n){return typeof n==='number'&&isFinite(n)&&n>=0&&n<=9007199254740991&&Math.floor(n)===n;}
 function decimal64(s){return typeof s==='string'&&/^(0|[1-9][0-9]{0,19})$/.test(s)&&(s.length<20||s<='18446744073709551615');}
 function actionsValid(a,now){
  if(!a||typeof a.ownerAvailable!=='boolean'||!decimal64(a.dropped)||!decimal64(a.rejected)||!decimal64(a.missing)||!Array.isArray(a.events)||a.events.length>256)return false;
  var sequences={},times={};
  for(var i=0;i<a.events.length;i++){
   var e=a.events[i];
   if(!e||typeof e.session!=='string'||!/^[0-9a-f]{16}$/.test(e.session)||e.session==='0000000000000000'||!integer(e.sequence)||!e.sequence||!integer(e.uptimeMs)||e.uptimeMs>now||typeof e.mac!=='string'||!/^[0-9A-F]{2}(:[0-9A-F]{2}){5}$/.test(e.mac)||e.mac==='00:00:00:00:00:00'||(parseInt(e.mac.slice(0,2),16)&1)||!integer(e.radio)||e.radio>1||!integer(e.bss)||e.bss>15||!integer(e.cookie)||e.cookie>4294967295||['allow','remove_candidate'].indexOf(e.operation)<0||['intent','ioctl_accepted','ioctl_failed','driver_ack'].indexOf(e.stage)<0||typeof e.result!=='number'||Math.floor(e.result)!==e.result||e.result < -2147483648||e.result>2147483647||e.outcome!=='unknown')return false;
   if(sequences[e.session]&&e.sequence<=sequences[e.session]||times[e.session]!==undefined&&e.uptimeMs<times[e.session])return false;
   sequences[e.session]=e.sequence;times[e.session]=e.uptimeMs;
  }
  return true;
 }
 function valid(h){
  if(!h||typeof h.epoch!=='string'||!h.epoch.length||h.epoch.length>64||!integer(h.serverUptimeMs)||!integer(h.dropped)||!integer(h.clientDropped)||!integer(h.clientEvictions)||typeof h.gap!=='boolean'||['current','stale','unavailable'].indexOf(h.cacheState)<0||!Array.isArray(h.events)||h.events.length>256)return false;
  if(h.actions!==undefined&&!actionsValid(h.actions,h.serverUptimeMs))return false;
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
  if(current<old)return 'older';
  if(next.gap!==previous.gap||next.dropped!==previous.dropped||next.clientDropped!==previous.clientDropped||next.clientEvictions!==previous.clientEvictions)return 'updated';
  if(JSON.stringify(previous.actions)!==JSON.stringify(next.actions))return 'updated';
  return current===old?'unchanged':'updated';
 }
 function create(refresh,options){
  var adapted={},key;for(key in options)if(Object.prototype.hasOwnProperty.call(options,key))adapted[key]=options[key];
  adapted.validate=valid;adapted.relation=relation;return refresh.create(adapted);
 }
 return {valid:valid,actionsValid:actionsValid,relation:relation,create:create};
});
