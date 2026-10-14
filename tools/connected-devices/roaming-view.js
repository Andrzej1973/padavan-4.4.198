(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.WRRoamingView=factory();})(typeof window!=='undefined'?window:this,function(){
 'use strict';
 function createView(doc,root){
  function translated(key,fallback){var value=root.getAttribute&&root.getAttribute('data-wr-'+key);return value&&value.indexOf('<#')<0?value:fallback;}
  function format(key,fallback,values){return translated(key,fallback).replace(/\{([A-Za-z]+)\}/g,function(token,name){return Object.prototype.hasOwnProperty.call(values,name)?String(values[name]):token;});}
  function node(tag,text,parent){var n=doc.createElement(tag);if(text)n.textContent=text;(parent||root).appendChild(n);return n;}
  node('h3',translated('history-title','Wi-Fi observation history'));var status=node('p',translated('state-unavailable','Unavailable')),notice=node('p',''),label=node('label',translated('history-client','Client MAC: ')),filter=node('input','',label),details=node('details',''),summary=node('summary',translated('history-recent','Recent events'),details),list=node('ol','',details),last=null;
  var actionDetails=node('details',''),actionSummary=node('summary',translated('history-commands','Band Steering commands'),actionDetails),actionNotice=node('p','',actionDetails),actionList=node('ol','',actionDetails);actionDetails.open=false;actionList.style.maxHeight='280px';actionList.style.overflowY='auto';
  var exportButton=node('button',translated('history-export','Export history JSON'));exportButton.type='button';exportButton.disabled=true;
  filter.type='text';filter.maxLength=17;filter.setAttribute('aria-label',translated('history-filter','Filter history by client MAC'));details.open=false;list.style.maxHeight='280px';list.style.overflowY='auto';
  node('p',translated('history-help','Observed changes do not prove Band Steering or RSSI Kick caused them. External access points are not observed.'));
  function band(n){return n===1?'2.4 GHz':n===2?'5 GHz':n===3?translated('history-band-both','both bands / ambiguous'):translated('history-band-unknown','unknown');}
  function render(h){last=h;exportButton.disabled=false;var scroll=list.scrollTop;while(list.firstChild)list.removeChild(list.firstChild);
   var match=filter.value.trim().toUpperCase(),count=0;
   for(var i=h.events.length-1;i>=0;i--){var e=h.events[i];if(match&&e.kind!=='gap'&&e.mac.indexOf(match)<0)continue;
    var message=e.kind==='gap'?translated('history-gap','Observation gap'):e.kind==='band_change'?format('history-band-change','Observed band change: {before} to {after}',{before:band(e.before),after:band(e.after)}):e.kind==='ambiguous'?translated('history-ambiguous','Simultaneous or ambiguous association'):format('history-associated','Association observed: {band}',{band:band(e.after)});
    node('li',Math.floor(e.uptimeMs/1000)+' '+translated('history-uptime','s uptime')+' | '+(e.mac?e.mac+' | ':'')+message,list);count++;
   }
   summary.textContent=translated('history-recent','Recent events')+' ('+count+')';list.scrollTop=scroll;
   var actionScroll=actionList.scrollTop,actionCount=0,a=h.actions;
   while(actionList.firstChild)actionList.removeChild(actionList.firstChild);
   if(a){
    for(var j=a.events.length-1;j>=0;j--){var command=a.events[j];if(match&&command.mac.indexOf(match)<0)continue;
     var stage=command.stage==='intent'?translated('history-intent','Command requested'):command.stage==='ioctl_accepted'?translated('history-accepted','Driver ioctl accepted'):command.stage==='ioctl_failed'?translated('history-failed','Driver ioctl failed'):translated('history-verified','Driver candidate-table state verified');
     var operation=command.operation==='allow'?translated('history-allow','allow candidate'):translated('history-remove','remove candidate');
     node('li',Math.floor(command.uptimeMs/1000)+' '+translated('history-uptime','s uptime')+' | '+command.mac+' | '+(command.radio===0?'2.4 GHz':'5 GHz')+' | '+operation+' | '+stage+' '+format('history-command-result','(result {result}). Roaming outcome unknown.',{result:command.result}),actionList);actionCount++;
    }
    actionNotice.textContent=(a.ownerAvailable?translated('history-producer-current','Producer verified at last collection.'):translated('history-producer-unavailable','Producer unavailable; retained commands may be old.'))+' '+format('history-command-counters','Overwritten: {dropped}; rejected: {rejected}; missing in current producer session: {missing}.',a)+(a.monitoringGap?' '+translated('history-monitoring-gap','Monitoring currently incomplete.'):'')+(a.interruptions!==undefined?' '+format('history-interruptions','Collection interruptions: {count}.',{count:a.interruptions}):'')+' '+translated('history-command-limit','Command acceptance does not prove a client moved.');
   }else actionNotice.textContent=translated('history-command-unavailable','Command monitoring is unavailable in this firmware.');
   actionSummary.textContent=translated('history-commands','Band Steering commands')+' ('+actionCount+')';actionList.scrollTop=actionScroll;

   notice.textContent=format('history-counters','History is held in RAM for collector session {epoch}. Overwritten events: {dropped}; omitted client observations: {clientDropped}; reused inactive client slots: {clientEvictions}',h)+(h.gap?'. '+translated('history-incomplete','Observation currently incomplete.'):'');
  }
  filter.addEventListener('input',function(){if(last)render(last);});
  exportButton.addEventListener('click',function(){
   if(!last)return;
   var win=doc.defaultView,link=null,url=null;
   if(!win||!win.Blob||!win.URL||!win.URL.createObjectURL){status.textContent=translated('history-export-unavailable','Export unavailable in this browser');return;}
   try{
    url=win.URL.createObjectURL(new win.Blob([JSON.stringify(last,null,2)],{type:'application/json'}));
    link=node('a','');link.href=url;link.download='wr1200js-wifi-history.json';link.style.display='none';link.click();
   }catch(error){status.textContent=translated('history-export-failed','History export failed');}
   finally{if(link&&link.parentNode)link.parentNode.removeChild(link);if(url)win.setTimeout(function(){win.URL.revokeObjectURL(url);},1000);}
  });
  var stale=false;
  return {render:render,setState:function(s){if(s.state==='Stale')stale=true;else if(s.state==='Current')stale=false;status.textContent=translated('state-'+s.state.toLowerCase(),s.state)+(stale?' \u2014 '+translated('last-observations','showing last available history'):'');},filter:filter,details:details,list:list,actionDetails:actionDetails,actionList:actionList,exportButton:exportButton};
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
