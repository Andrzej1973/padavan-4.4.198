/* Shared refresh lifecycle. Transport must return an abort function.
 * Snapshot observation timestamps belong to the collector, never this poller. */
(function(root,factory){
 if(typeof module==='object'&&module.exports)module.exports=factory();
 else root.WRDeviceRefresh=factory();
})(typeof window!=='undefined'?window:this,function(){
 'use strict';
 function valid(snapshot){
  return snapshot&&typeof snapshot.epoch==='string'&&snapshot.epoch.length>0&&snapshot.epoch.length<=64&&
   typeof snapshot.sequence==='number'&&isFinite(snapshot.sequence)&&snapshot.sequence>=0&&Math.floor(snapshot.sequence)===snapshot.sequence&&
   Array.isArray(snapshot.devices)&&snapshot.devices.length<=128;
 }
 function create(options){
  var schedule=options.setTimer||setTimeout,cancel=options.clearTimer||clearTimeout;
  var validate=options.validate||valid;
  function relation(previous,next){if(options.relation)return options.relation(previous,next);if(!previous||previous.epoch!==next.epoch)return "new_session";return next.sequence<previous.sequence?"older":next.sequence===previous.sequence?"unchanged":"updated";}
  var running=false,visible=true,timer=null,flight=null,generation=0,failures=0,last=null;
  function state(name){if(options.onState){try{options.onState({state:name,hasData:last!==null,failures:failures});}catch(ignore){/* UI callbacks must not stop retries. */}}}
  function clear(){if(timer!==null){cancel(timer);timer=null;}}
  function later(delay){clear();if(running&&visible)timer=schedule(function(){timer=null;poll();},delay);}
  function abandon(){
   generation++;
   if(flight){var old=flight;flight=null;cancel(old.timeout);if(old.abort){try{old.abort();}catch(ignore){}}}
  }
  function poll(){
   if(!running||!visible||flight)return;
   clear();var id=++generation,entry={abort:null,timeout:null};flight=entry;state('Updating');
   function finish(error,snapshot){
    if(!flight||flight!==entry||id!==generation)return;
    flight=null;cancel(entry.timeout);
    if(!error&&!validate(snapshot))error=new Error('Invalid device snapshot');
    var change=!error?relation(last,snapshot):"invalid";
    if(!error&&(change==="older"||change==="invalid"))error=new Error("Older or invalid snapshot");
    if(error){failures=Math.min(failures+1,4);state(last?'Stale':'Unavailable');later(Math.min(30000,5000*Math.pow(2,failures-1)));return;}
    failures=0;
    if(change!=="unchanged"){
     try{if(options.onData)options.onData(snapshot);}catch(error){failures=1;state(last?'Stale':'Unavailable');later(5000);return;}
     last=snapshot;
    }
    /* Keep newest freshness metadata even if event rows did not change. */
    last=snapshot;
    state(snapshot.cacheState==='stale'?'Stale':snapshot.cacheState==='unavailable'?'Unavailable':'Current');later(5000);
   }
   entry.timeout=schedule(function(){
    if(flight!==entry)return;
    /* Invalidate before abort: transports may synchronously invoke their callback. */
    flight=null;generation++;if(entry.abort){try{entry.abort();}catch(ignore){}}
    failures=Math.min(failures+1,4);state(last?'Stale':'Unavailable');later(Math.min(30000,5000*Math.pow(2,failures-1)));
   },5000);
   try{
    entry.abort=options.request(finish);
    if(typeof entry.abort!=='function')throw new Error('Abortable transport required');
   }catch(error){finish(error);}
  }
  return {
   start:function(){if(running)return;running=true;poll();},
   stop:function(){running=false;clear();abandon();state('Stopped');},
   setVisible:function(value){
    value=!!value;if(value===visible)return;visible=value;
    if(!visible){clear();abandon();state('Paused');}else if(running)poll();
   },
   retry:function(){if(running&&visible&&!flight)poll();}
  };
 }
 return {create:create,validSnapshot:valid};
});
