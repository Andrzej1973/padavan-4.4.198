(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.WRRoamingView=factory();})(typeof window!=='undefined'?window:this,function(){
 'use strict';
 function createView(doc,root){
  function node(tag,text,parent){var n=doc.createElement(tag);if(text)n.textContent=text;(parent||root).appendChild(n);return n;}
  node('h3','Wi-Fi observation history');var status=node('p','Unavailable'),notice=node('p',''),label=node('label','Client MAC: '),filter=node('input','',label),details=node('details',''),summary=node('summary','Recent events',details),list=node('ol','',details),last=null;
  var actionDetails=node('details',''),actionSummary=node('summary','Band Steering commands',actionDetails),actionNotice=node('p','',actionDetails),actionList=node('ol','',actionDetails);actionDetails.open=false;actionList.style.maxHeight='280px';actionList.style.overflowY='auto';
  var exportButton=node('button','Export history JSON');exportButton.type='button';exportButton.disabled=true;
  filter.type='text';filter.maxLength=17;filter.setAttribute('aria-label','Filter history by client MAC');details.open=false;list.style.maxHeight='280px';list.style.overflowY='auto';
  node('p','Observed changes do not prove Band Steering or RSSI Kick caused them. External access points are not observed.');
  function band(n){return n===1?'2.4 GHz':n===2?'5 GHz':n===3?'both bands / ambiguous':'unknown';}
  function render(h){last=h;exportButton.disabled=false;var scroll=list.scrollTop;while(list.firstChild)list.removeChild(list.firstChild);
   var match=filter.value.trim().toUpperCase(),count=0;
   for(var i=h.events.length-1;i>=0;i--){var e=h.events[i];if(match&&e.kind!=='gap'&&e.mac.indexOf(match)<0)continue;
    var message=e.kind==='gap'?'Observation gap':e.kind==='band_change'?'Observed band change: '+band(e.before)+' to '+band(e.after):e.kind==='ambiguous'?'Simultaneous or ambiguous association':'Association observed: '+band(e.after);
    node('li',Math.floor(e.uptimeMs/1000)+' s uptime | '+(e.mac?e.mac+' | ':'')+message,list);count++;
   }
   summary.textContent='Recent events ('+count+')';list.scrollTop=scroll;
   var actionScroll=actionList.scrollTop,actionCount=0,a=h.actions;
   while(actionList.firstChild)actionList.removeChild(actionList.firstChild);
   if(a){
    for(var j=a.events.length-1;j>=0;j--){var command=a.events[j];if(match&&command.mac.indexOf(match)<0)continue;
     var stage=command.stage==='intent'?'Command requested':command.stage==='ioctl_accepted'?'Driver ioctl accepted':command.stage==='ioctl_failed'?'Driver ioctl failed':'Driver acknowledgement';
     var operation=command.operation==='allow'?'allow candidate':'remove candidate';
     node('li',Math.floor(command.uptimeMs/1000)+' s uptime | '+command.mac+' | '+(command.radio===0?'2.4 GHz':'5 GHz')+' | '+operation+' | '+stage+' (result '+command.result+'). Roaming outcome unknown.',actionList);actionCount++;
    }
    actionNotice.textContent=(a.ownerAvailable?'Producer verified at last collection.':'Producer unavailable; retained commands may be old.')+' Overwritten: '+a.dropped+'; rejected: '+a.rejected+'; missing in current producer session: '+a.missing+'. Command acceptance does not prove a client moved.';
   }else actionNotice.textContent='Command monitoring is unavailable in this firmware.';
   actionSummary.textContent='Band Steering commands ('+actionCount+')';actionList.scrollTop=actionScroll;

   notice.textContent='History is held in RAM for collector session '+h.epoch+'. Overwritten events: '+h.dropped+'; omitted client observations: '+h.clientDropped+'; reused inactive client slots: '+h.clientEvictions+(h.gap?'. Observation currently incomplete.':'');
  }
  filter.addEventListener('input',function(){if(last)render(last);});
  exportButton.addEventListener('click',function(){
   if(!last)return;
   var win=doc.defaultView,link=null,url=null;
   if(!win||!win.Blob||!win.URL||!win.URL.createObjectURL){status.textContent='Export unavailable in this browser';return;}
   try{
    url=win.URL.createObjectURL(new win.Blob([JSON.stringify(last,null,2)],{type:'application/json'}));
    link=node('a','');link.href=url;link.download='wr1200js-wifi-history.json';link.style.display='none';link.click();
   }catch(error){status.textContent='History export failed';}
   finally{if(link&&link.parentNode)link.parentNode.removeChild(link);if(url)win.setTimeout(function(){win.URL.revokeObjectURL(url);},1000);}
  });
  var stale=false;
  return {render:render,setState:function(s){if(s.state==='Stale')stale=true;else if(s.state==='Current')stale=false;status.textContent=s.state+(stale?' \u2014 showing last available history':'');},filter:filter,details:details,list:list,actionDetails:actionDetails,actionList:actionList,exportButton:exportButton};
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
