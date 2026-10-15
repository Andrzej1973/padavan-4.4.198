const fs=require('fs'),vm=require('vm'),assert=require('assert');
const nodes={},requests=[],timers=[];
let now=100000,refreshes=0;
for(const id of ['wr_usbip_device_select','wr_usbip_ack','wr_usbip_bind','wr_usbip_unbind','wr_usbip_action_result'])
 nodes[id]={value:'0',checked:false,disabled:true,options:[],textContent:'',appendChild(option){this.options.push(option);}};
const ctx={Date:{now:()=>now},document:{hidden:false,getElementById:id=>nodes[id],createElement:()=>({})},
 window:{setTimeout:fn=>timers.push(fn)},wrUSBIPActionToken:'a'.repeat(32),
 wrUSBIPActionLabels:{unknown:'UNKNOWN',pending:'PENDING',done:'DONE',failed:'FAILED'},
 wrUSBIPInventoryRefresh:()=>refreshes++,wrUSBIPRefresh:()=>refreshes++};
ctx.$j=selector=>({text:value=>{nodes[selector.slice(1)].textContent=value;}});
ctx.$j.ajax=options=>{
 const request={options,done(fn){this.success=fn;return this;},fail(fn){this.failure=fn;return this;},always(fn){this.complete=fn;return this;}};
 requests.push(request);return request;
};
function complete(request,value,failed=false){(failed?request.failure:request.success)(value);if(request.complete)request.complete();}
vm.createContext(ctx);vm.runInContext(fs.readFileSync(__dirname+'/action-view.js','utf8'),ctx);
const row={busid:'1-1',vendor:'1234',product:'abcd',exported:0};
ctx.wrUSBIPActionDevices([row]);assert(nodes.wr_usbip_bind.disabled);
ctx.wrUSBIPActionDaemon=1;nodes.wr_usbip_ack.checked=true;ctx.wrUSBIPActionUpdate();
assert(!nodes.wr_usbip_bind.disabled&&nodes.wr_usbip_unbind.disabled);
ctx.wrUSBIPActionSubmit('invalid');assert.equal(requests.length,0);
ctx.wrUSBIPActionSubmit('bind');assert.equal(requests.length,1);
assert.equal(requests[0].options.type,'POST');assert.equal(requests[0].options.data.busid,'1-1');
assert(!nodes.wr_usbip_ack.checked&&nodes.wr_usbip_bind.disabled);
ctx.wrUSBIPActionSubmit('bind');assert.equal(requests.length,1);
const id='b'.repeat(32);complete(requests[0],{accepted:true,id});assert.equal(requests.length,2);
complete(requests[1],{id:'c'.repeat(32),state:2,code:0});assert.equal(nodes.wr_usbip_action_result.textContent,'UNKNOWN');
ctx.wrUSBIPActionPoll();complete(requests[2],{id,state:1,code:-1});
assert(ctx.wrUSBIPActionBusy&&nodes.wr_usbip_bind.disabled);
ctx.wrUSBIPActionPoll();complete(requests[3],{id,state:2,code:0});
assert.equal(nodes.wr_usbip_action_result.textContent,'DONE');assert.equal(refreshes,2);
nodes.wr_usbip_ack.checked=true;now+=31000;ctx.wrUSBIPActionSubmit('bind');assert.equal(requests.length,4);
ctx.wrUSBIPActionDevices(null);assert(nodes.wr_usbip_bind.disabled&&nodes.wr_usbip_unbind.disabled);
ctx.wrUSBIPActionDevices([{...row,exported:1}]);nodes.wr_usbip_ack.checked=true;ctx.wrUSBIPActionUpdate();
assert(!nodes.wr_usbip_unbind.disabled);
ctx.wrUSBIPActionSubmit('unbind');complete(requests[4],null,true);
assert.equal(nodes.wr_usbip_action_result.textContent,'UNKNOWN');assert.equal(requests.length,5);
ctx.wrUSBIPActionToken='';nodes.wr_usbip_ack.checked=true;ctx.wrUSBIPActionUpdate();assert(nodes.wr_usbip_unbind.disabled);
console.log('PASS USB/IP action view: fresh selection, daemon state, confirmation, POST, single flight, matching job, stale data, timeout');
