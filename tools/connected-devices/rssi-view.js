(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.WRRssiView=factory();})(typeof window!=='undefined'?window:this,function(){
 'use strict';
 function createView(doc,root){
  function node(tag,text,parent){var n=doc.createElement(tag);n.textContent=text;(parent||root).appendChild(n);return n;}
  var status=node('p','Unavailable'),notice=node('p',''),details=node('details',''),summary=node('summary','RSSI Kick driver events',details),list=node('ol','',details);
  var filter=node('input',''),last=null;filter.maxLength=17;filter.setAttribute('aria-label','Filter RSSI events by MAC');
  list.style.maxHeight='280px';list.style.overflowY='auto';details.open=false;
  node('p','Driver observations do not prove delivery of a disconnect frame or successful roaming.');
  function render(h){last=h;var scroll=list.scrollTop,count=0,match=filter.value.trim().toUpperCase();
   while(list.firstChild)list.removeChild(list.firstChild);
   var labels={decision:'Low RSSI decision',allocation_failed:'Disconnect frame allocation failed',frame_submitted:'Disconnect frame submitted',entry_cleared:'Station table entry cleared'};
   for(var i=h.events.length-1;i>=0;i--){var e=h.events[i];if(match&&e.mac.indexOf(match)<0)continue;
    node('li',e.uptimeMs+' ms uptime | '+e.mac+' | '+(e.radio===0?'2.4 GHz':'5 GHz')+' | '+labels[e.stage]+' | attempt '+e.attempt,list);count++;
   }
   summary.textContent='RSSI Kick driver events ('+count+')';list.scrollTop=scroll;
   notice.textContent=h.radios.map(function(r){return (r.radio===0?'2.4 GHz':'5 GHz')+': '+(r.available?'available':r.attempted?'unavailable':'not collected')+'; missing '+r.missing+'; restarts '+r.restarts+'; driver overwritten '+r.driverOverwritten;}).join(' | ')+' | Evicted from RAM: '+h.evicted;
  }
  filter.addEventListener('input',function(){if(last)render(last);});
  return {render:render,setState:function(s){status.textContent=s.state+(s.state==='Stale'?' — showing last available data':'');},filter:filter,details:details,list:list};
 }
 function mount(doc,root,refresh,schema){
  var view=createView(doc,root),poller=schema.create(refresh,{request:function(done){
   var xhr=new XMLHttpRequest(),settled=false;
   function finish(error,value){if(settled)return;settled=true;done(error,value);}
   xhr.open('GET','/wr_rssi.json?_='+Date.now(),true);xhr.setRequestHeader('Accept','application/json');
   xhr.onreadystatechange=function(){if(xhr.readyState!==4)return;if(xhr.status!==200){finish(new Error('RSSI unavailable'));return;}try{if(xhr.responseText.length>100000)throw new Error('RSSI response too large');finish(null,JSON.parse(xhr.responseText));}catch(e){finish(e);}};
   xhr.onerror=function(){finish(new Error('Network error'));};xhr.onabort=function(){finish(new Error('Aborted'));};
   xhr.onprogress=function(e){if(e.loaded>100000){finish(new Error('RSSI response too large'));xhr.abort();}};
   xhr.send(null);return function(){xhr.abort();};
  },onData:view.render,onState:view.setState});
  function visibility(){poller.setVisible(!doc.hidden);}doc.addEventListener('visibilitychange',visibility);visibility();poller.start();
  return {stop:function(){poller.stop();doc.removeEventListener('visibilitychange',visibility);},view:view};
 }
 return {createView:createView,mount:mount};
});
