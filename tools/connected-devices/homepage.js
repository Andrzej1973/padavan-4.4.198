(function(root,factory){
 if(typeof module==='object'&&module.exports)module.exports=factory(require('./classify.js'));
 else root.WRDeviceHomepage=factory(root.WRDeviceClassification);
})(typeof window!=='undefined'?window:this,function(classification){
 'use strict';
 var categories=['All','Android','Windows','Apple','Smart TV','Unknown'];
 var labels={primary:'Primary network',guest:'Guest network',iot:'IoT network',unknown:'Network not identified'};
 var icons={'Android':'рџџў','Windows':'рџџЎ','Apple':'рџЌЋ','Smart TV':'рџ“є','Unknown':'вќ”'};
 function text(value){return typeof value==='string'?value.slice(0,128):'';}
 function createView(doc,root){
  var groups={},rows=Object.create(null),current=[],warning='',source=null;
  function node(tag,label,parent){var n=doc.createElement(tag);if(label!==undefined)n.textContent=label;if(parent)parent.appendChild(n);return n;}
  function set(n,value){value=String(value);if(n.textContent!==value)n.textContent=value;}
  node('h3','Connected devices',root);
  node('p','Passive observations; current connection and network role may be unknown.',root);
  var controls=node('div',undefined,root),filterLabel=node('label','Category ',controls),filter=node('select',undefined,filterLabel);
  filter.setAttribute('aria-label','Device category');categories.forEach(function(c){var opt=node('option',c,filter);opt.value=c;});filter.value='All';
  var retry=node('button','Retry',controls);retry.type='button';retry.className='btn';
  var status=node('p','Updating',root);status.setAttribute('role','status');status.setAttribute('aria-live','polite');
  var freshness=node('p','Source update time unavailable',root),notice=node('p','',root),empty=node('p','No observations available',root);
  Object.keys(labels).forEach(function(key){
   var details=node('details',undefined,root);details.open=key==='primary'||key==='unknown';details.setAttribute('data-network',key);
   var summary=node('summary',labels[key],details),scroll=node('div',undefined,details);scroll.className='wr-device-scroll';
   var table=node('table',undefined,scroll);table.className='table table-striped';
   var header=node('tr',undefined,node('thead',undefined,table));
   ['Device / address','Connection evidence','Category','Confidence'].forEach(function(label){node('th',label,header);});
   groups[key]={details:details,summary:summary,body:node('tbody',undefined,table),scroll:scroll,total:0,shown:0};details.style.display='none';
  });
  function applyFilter(){
   Object.keys(groups).forEach(function(key){groups[key].shown=0;});
   Object.keys(rows).forEach(function(key){var row=rows[key],show=filter.value==='All'||row.category===filter.value;row.node.style.display=show?'':'none';if(show)groups[row.group].shown++;});
   var count=0,total=0;Object.keys(groups).forEach(function(key){var g=groups[key];set(g.summary,labels[key]+' ('+g.shown+' / '+g.total+')');g.details.style.display=g.total?'':'none';count+=g.shown;total+=g.total;});
   empty.style.display=count?'none':'';set(empty,total?'No devices match this category':'No observations available');
  }
  filter.addEventListener('change',applyFilter);
  function render(snapshot){
   var seen=Object.create(null),positions={},viewport=doc.defaultView;
   var x=viewport?viewport.pageXOffset:0,y=viewport?viewport.pageYOffset:0;
   Object.keys(groups).forEach(function(key){positions[key]=groups[key].scroll.scrollTop;});current=snapshot.devices||[];
   Object.keys(groups).forEach(function(key){groups[key].total=0;});
   current.slice(0,128).forEach(function(record){
    if(!record||typeof record!=='object')return;
    var mac=text(record.mac).toUpperCase(),ip=text(record.ip);if(!mac)return;
    var key=mac+'|'+ip;if(seen[key])return;seen[key]=true;
    var group=Object.prototype.hasOwnProperty.call(labels,record.networkRole)?record.networkRole:'unknown';
    var result=classification.classify(record),row=rows[key];
    if(!row){var tr=node('tr'),cells=[];for(var i=0;i<4;i++)cells.push(node('td',undefined,tr));row=rows[key]={node:tr,cells:cells};}
    if(row.node.parentNode!==groups[group].body)groups[group].body.appendChild(row.node);
    row.group=group;row.category=result.category;groups[group].total++;
    set(row.cells[0],(text(record.hostname)||'Unnamed device')+' В· '+ip+' В· '+mac);
    var connection=record.presence==='associated'?'Wi-Fi association':(record.networkmapStale===true?'Last known observation':record.networkmapStale===false?'Seen by networkmap':'Connection unknown');
    if(record.band==='2g')connection+=' В· 2.4 GHz';else if(record.band==='5g')connection+=' В· 5 GHz';
    if(typeof record.rssi==='number'&&isFinite(record.rssi)&&record.rssi>=-127&&record.rssi<=0)connection+=' В· '+record.rssi+' dBm';
    set(row.cells[1],connection);set(row.cells[2],icons[result.category]+' '+result.category);set(row.cells[3],result.confidence);
    row.cells[3].title=result.evidence.join('; ')||'No reliable classification evidence';
   });
   Object.keys(rows).forEach(function(key){if(!seen[key]){var n=rows[key].node;if(n.parentNode)n.parentNode.removeChild(n);delete rows[key];}});
   warning=(snapshot.truncated?'Snapshot truncated to bounded source limits. ':'')+(snapshot.invalid?'Invalid source records: '+snapshot.invalid+'.':'');
   set(notice,warning);
   source=typeof snapshot.sourceUpdatedAt==='number'&&snapshot.sourceUpdatedAt>0?snapshot.sourceUpdatedAt:null;
   set(freshness,source?'Source updated: '+new Date(source*1000).toLocaleString():'Source update time unavailable');
   applyFilter();
   Object.keys(groups).forEach(function(key){groups[key].scroll.scrollTop=positions[key];});
   if(viewport&&typeof viewport.scrollTo==='function')viewport.scrollTo(x,y);
  }
  return {render:render,setState:function(value){set(status,value.state+(value.state==='Stale'?' вЂ” showing last available observations':''));},retry:retry,filter:filter};
 }
 function mount(doc,root,refresh){
  var view=createView(doc,root),poller=refresh.create({request:function(done){
   var xhr=new XMLHttpRequest(),settled=false;
   function finish(error,value){if(settled)return;settled=true;done(error,value);}
   xhr.open('GET','/wr_devices.json?_='+Date.now(),true);xhr.setRequestHeader('Accept','application/json');
   xhr.onreadystatechange=function(){if(xhr.readyState!==4)return;if(xhr.status!==200){finish(new Error('Device data unavailable'));return;}
    try{if(xhr.responseText.length>131072)throw new Error('Device response too large');finish(null,JSON.parse(xhr.responseText));}catch(error){finish(error);}
   };
   xhr.onerror=function(){finish(new Error('Network error'));};xhr.onabort=function(){finish(new Error('Request aborted'));};
   xhr.onprogress=function(event){if(event.loaded>131072){finish(new Error('Device response too large'));xhr.abort();}};
   xhr.send(null);return function(){xhr.abort();};
  },onData:view.render,onState:view.setState});
  view.retry.addEventListener('click',poller.retry);
  function visibility(){poller.setVisible(!doc.hidden);}
  doc.addEventListener('visibilitychange',visibility);visibility();poller.start();
  return {stop:function(){poller.stop();doc.removeEventListener('visibilitychange',visibility);},view:view};
 }
 return {createView:createView,mount:mount};
});
