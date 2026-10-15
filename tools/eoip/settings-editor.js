(function (root, factory) {
 'use strict';
 if (typeof module === 'object' && module.exports) module.exports = factory();
 else root.WREoIPEditor = factory();
}(typeof window !== 'undefined' ? window : this, function () {
 'use strict';
 var fields = ['enable','autostart','local','remote','id','mtu','keepalive','retries','bridge'];
 function valid(reply) {
  if (!reply || reply.schema !== 1 || ['0','1'].indexOf(reply.master)<0 ||
      !Array.isArray(reply.slots) || reply.slots.length!==8) return false;
  return reply.slots.every(function(row,index) {
   return row && row.slot===index && fields.every(function(key) {
    return typeof row[key]==='string' && row[key].length<48 &&
      (['enable','autostart'].indexOf(key)<0 || ['0','1'].indexOf(row[key])>=0);
   });
  });
 }
 function mount(target, labels, transport) {
  var doc=target.ownerDocument, token='', loaded=false, busy=false, inputs=[], rows=[];
  target.textContent='';
  target.className='wr-eoip-editor';
  function element(tag,text,parent) {
   var node=doc.createElement(tag);
   if(text!==undefined) node.textContent=text;
   if(parent) parent.appendChild(node);
   return node;
  }
  function input(parent,key,title) {
   var label=element('label',title,parent), control;
   if (key==='enable' || key==='autostart') {
    control=element('select',undefined,label);
    ['0','1'].forEach(function(value) {
     var option=element('option',value==='1'?labels.on:labels.off,control); option.value=value;
    });
   } else { control=element('input',undefined,label); control.type='text'; control.maxLength=47; }
   inputs.push(control); return control;
  }
  var master=input(target,'enable',labels.masterEnable);
  for(var slot=0;slot<8;slot++) {
   var details=element('details',undefined,target), row={};
   details.open=slot===0;
   element('summary',labels.slot+' '+slot,details);
   var group=element('fieldset',undefined,details);
   fields.forEach(function(key) { row[key]=input(group,key,labels[key]); });
   rows.push(row);
  }
  var acknowledgement=element('label',labels.confirm,target), ack=element('input',undefined,acknowledgement);
  ack.type='checkbox';
  var message=element('p',labels.unavailable,target); message.setAttribute('role','status');
  function button(text,action) { var node=element('button',text,target); node.type='button'; node.className='btn'; node.onclick=action; return node; }
  var save=button(labels.save,function(){submit(false);});
  var disable=button(labels.disable,function(){submit(true);});
  var reload=button(labels.reload,load);
  function controls() {
   inputs.forEach(function(node){node.disabled=busy || !loaded;});
   save.disabled=busy || !loaded || !token;
   disable.disabled=busy || !token;
   ack.disabled=busy || !token;
   reload.disabled=busy;
  }
  function submit(off) {
   if(busy || !token || (!off && !loaded)) return;
   if(!ack.checked) { message.textContent=labels.confirm; return; }
   var payload={token:token,ack:'1',eoip_enable:off?'0':master.value};
   if(!off) rows.forEach(function(row,index) {
    fields.forEach(function(key){payload['eoip_slot'+index+'_'+key]=row[key].value;});
   });
   busy=true; controls(); message.textContent=labels.saving;
   Promise.resolve().then(function(){return transport.save(payload);}).then(function(reply) {
    if(reply && reply.saved_in_ram===true && reply.apply_requested===true && reply.applied===null) {
     if(off) master.value='0';
     ack.checked=false; message.textContent=labels.saved;
    } else message.textContent=labels.rejected;
   },function(){message.textContent=labels.uncertain;}).then(function(){busy=false;controls();});
  }
  function load() {
   if(busy) return;
   busy=true; loaded=false; token=''; ack.checked=false; controls(); message.textContent=labels.loading;
   Promise.resolve().then(function(){return transport.read('wr_eoip_token');}).then(function(value) {
    if(typeof value!=='string' || !/^[0-9a-f]{32}$/.test(value)) throw new Error('token unavailable');
    token=value;
    return transport.read('wr_eoip_settings');
   }).then(function(reply) {
    if(!valid(reply)) throw new Error('settings unavailable');
    master.value=reply.master;
    rows.forEach(function(row,index){fields.forEach(function(key){row[key].value=reply.slots[index][key];});});
    loaded=true; message.textContent=labels.loaded;
   }).catch(function(){message.textContent=labels.unavailable;}).then(function(){busy=false;controls();});
  }
  load();
  return {reload:load};
 }
 return {valid:valid,mount:mount};
}));
