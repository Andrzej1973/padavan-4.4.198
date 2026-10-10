/* Preserve 128-bit session identity and 64-bit counters as strings. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.WRRssi=factory();})(typeof window!=='undefined'?window:this,function(){
 'use strict';
 function u64(s){return typeof s==='string'&&/^(0|[1-9][0-9]{0,19})$/.test(s)&&(s.length<20||s<='18446744073709551615');}
 function greater(a,b){return a.length>b.length||(a.length===b.length&&a>b);}
 function uint(n,max){return typeof n==='number'&&isFinite(n)&&n>=0&&n<=max&&Math.floor(n)===n;}
 function valid(h){
  if(!h||['current','stale','unavailable'].indexOf(h.cacheState)<0||!u64(h.evicted)||!Array.isArray(h.radios)||h.radios.length!==2||!Array.isArray(h.events)||h.events.length>256)return false;
  var i,r,e,key,last=Object.create(null);
  for(i=0;i<2;i++){
   r=h.radios[i];
   if(!r||r.radio!==i||typeof r.available!=='boolean'||typeof r.attempted!=='boolean'||!uint(r.error,2147483647)||
      !u64(r.failures)||!u64(r.recoveries)||!u64(r.lastSuccessMs)||!u64(r.missing)||!u64(r.restarts)||
      (r.available&&(!r.attempted||r.error!==0)))return false;
  }
  var expected=h.radios[0].available&&h.radios[1].available?'current':h.events.length?'stale':'unavailable';
  if(h.cacheState!==expected)return false;
  for(i=0;i<h.events.length;i++){
   e=h.events[i];
   if(!e||typeof e.session!=='string'||!/^[0-9a-f]{32}$/.test(e.session)||/^0{32}$/.test(e.session)||
      !u64(e.sequence)||e.sequence==='0'||!u64(e.uptimeMs)||!uint(e.attempt,4294967295)||!e.attempt||
      typeof e.mac!=='string'||!/^[0-9A-F]{2}(:[0-9A-F]{2}){5}$/.test(e.mac)||e.mac==='00:00:00:00:00:00'||
      (parseInt(e.mac.slice(0,2),16)&1)||!uint(e.radio,1)||!uint(e.bss,15)||
      ['decision','allocation_failed','frame_submitted','entry_cleared'].indexOf(e.stage)<0||e.outcome!=='unknown')return false;
   key=e.radio+':'+e.session;
   if(last[key]&&!greater(e.sequence,last[key]))return false;
   last[key]=e.sequence;
  }
  return true;
 }
 function relation(a,b){if(!valid(b))return 'invalid';return JSON.stringify(a)===JSON.stringify(b)?'unchanged':'updated';}
 function create(refresh,options){var adapted={},key;for(key in options)if(Object.prototype.hasOwnProperty.call(options,key))adapted[key]=options[key];adapted.validate=valid;adapted.relation=relation;return refresh.create(adapted);}
 return {valid:valid,relation:relation,create:create};
});
