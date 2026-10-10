(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.WRRoamingView=factory();})(typeof window!=='undefined'?window:this,function(){
 'use strict';
 function createView(doc,root){
  function node(tag,text,parent){var n=doc.createElement(tag);if(text)n.textContent=text;(parent||root).appendChild(n);return n;}
  node('h3','Wi-Fi observation history');var status=node('p','Unavailable'),notice=node('p',''),label=node('label','Client MAC: '),filter=node('input','',label),details=node('details',''),summary=node('summary','Recent events',details),list=node('ol','',details),last=null;
  filter.type='text';filter.maxLength=17;filter.setAttribute('aria-label','Filter history by client MAC');details.open=false;
  node('p','Observed changes do not prove Band Steering or RSSI Kick caused them. External access points are not observed.');
  function band(n){return n===1?'2.4 GHz':n===2?'5 GHz':n===3?'both bands / ambiguous':'unknown';}
  function render(h){last=h;var scroll=list.scrollTop;while(list.firstChild)list.removeChild(list.firstChild);
   var match=filter.value.trim().toUpperCase(),count=0;
   for(var i=h.events.length-1;i>=0;i--){var e=h.events[i];if(match&&e.kind!=='gap'&&e.mac.indexOf(match)<0)continue;
    var message=e.kind==='gap'?'Observation gap':e.kind==='band_change'?'Observed band change: '+band(e.before)+' to '+band(e.after):e.kind==='ambiguous'?'Simultaneous or ambiguous association':'Association observed: '+band(e.after);
    node('li',Math.floor(e.uptimeMs/1000)+' s uptime | '+(e.mac?e.mac+' | ':'')+message,list);count++;
   }
   summary.textContent='Recent events ('+count+')';list.scrollTop=scroll;
   notice.textContent='History is held in RAM for collector session '+h.epoch+'. Overwritten events: '+h.dropped+'; omitted client observations: '+h.clientDropped+'; reused inactive client slots: '+h.clientEvictions+(h.gap?'. Observation currently incomplete.':'');
  }
  filter.addEventListener('input',function(){if(last)render(last);});
  return {render:render,setState:function(s){status.textContent=s.state+(s.state==='Stale'?' \u2014 showing last available history':'');},filter:filter,details:details,list:list};
 }
 function mount(doc,root,refresh,history){var view=createView(doc,root),poller=history.create(refresh,{request:function(done){
  var xhr=new XMLHttpRequest(),settled=false;function finish(error,value){if(settled)return;settled=true;done(error,value);}
  xhr.open('GET','/wr_roaming.json?_='+Date.now(),true);xhr.setRequestHeader('Accept','application/json');
  xhr.onreadystatechange=function(){if(xhr.readyState!==4)return;if(xhr.status!==200){finish(new Error('History unavailable'));return;}try{if(xhr.responseText.length>131072)throw new Error('History too large');finish(null,JSON.parse(xhr.responseText));}catch(e){finish(e);}};
  xhr.onerror=function(){finish(new Error('Network error'));};xhr.onabort=function(){finish(new Error('Aborted'));};xhr.onprogress=function(e){if(e.loaded>131072){finish(new Error('History too large'));xhr.abort();}};xhr.send(null);return function(){xhr.abort();};
 },onData:view.render,onState:view.setState});
 function visibility(){poller.setVisible(!doc.hidden);}doc.addEventListener('visibilitychange',visibility);visibility();poller.start();
 return {stop:function(){poller.stop();doc.removeEventListener('visibilitychange',visibility);},view:view};
 }
 return {createView:createView,mount:mount};
});
