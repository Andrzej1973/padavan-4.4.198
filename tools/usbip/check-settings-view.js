const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
function element(){return {children:[],checked:false,disabled:false,textContent:'',value:'0',
 appendChild(node){this.children.push(node);},removeChild(node){this.children.splice(this.children.indexOf(node),1);},
 get firstChild(){return this.children[0]||null;}};}
const nodes={},requests=[];let confirm=false;
for(const key of ['rows','save','add','ack','result'])nodes['wr_usbip_settings_'+key]=element();
nodes.wr_usbip_device_select=element();
const ctx={document:{getElementById:id=>nodes[id],createElement:element},window:{confirm:()=>confirm},
 Date:{now:()=>100000},wrUSBIPActionRows:[],wrUSBIPActionTime:100000,wrUSBIPActionToken:'a'.repeat(32),
 wrUSBIPSettingsLabels:Object.fromEntries(['remove','discard','loading','unknown','loaded','invalid','draft','confirm','saved','unsynced'].map(x=>[x,x]))};
ctx.$j={ajax(options){const r={options,done(fn){this.success=fn;return this;},fail(fn){this.failure=fn;return this;},always(fn){this.complete=fn;return this;}};requests.push(r);return r;}};
vm.createContext(ctx);vm.runInContext(fs.readFileSync(__dirname+'/settings-view.js','utf8'),ctx);
const empty=Array(16).fill(null),row={busid:'1-1',vendor:'1234',product:'abcd',serial_hex:'756e6974'};
const hex=ctx.wrUSBIPSettingsEncode(empty);assert(hex);assert.equal(JSON.stringify(ctx.wrUSBIPSettingsDecode(hex)),JSON.stringify(empty));
assert.equal(ctx.wrUSBIPSettingsDecode(hex.slice(0,-2)),null);
const duplicate=empty.slice();duplicate[0]=row;duplicate[1]={...row,busid:'1-2'};assert.equal(ctx.wrUSBIPSettingsEncode(duplicate),null);
ctx.wrUSBIPSettingsLoad();assert.equal(requests.length,1);assert(nodes.wr_usbip_settings_save.disabled);
requests[0].success({state:2,table_hex:hex});requests[0].complete();assert(ctx.wrUSBIPSettingsLoaded);
ctx.wrUSBIPActionRows=[row];ctx.wrUSBIPSettingsAdd();assert(ctx.wrUSBIPSettingsDirty);assert.equal(nodes.wr_usbip_settings_rows.children.length,1);
ctx.wrUSBIPSettingsAdd();assert.equal(nodes.wr_usbip_settings_result.textContent,'invalid');
ctx.wrUSBIPSettingsSave();assert.equal(requests.length,1);
nodes.wr_usbip_settings_ack.checked=true;ctx.wrUSBIPSettingsSave();assert.equal(requests.length,2);
assert.equal(requests[1].options.type,'POST');assert.equal(requests[1].options.data.ack,'1');
assert.equal(ctx.wrUSBIPSettingsDecode(requests[1].options.data.table_hex)[0].serial_hex,row.serial_hex);
ctx.wrUSBIPSettingsSave();assert.equal(requests.length,2);
requests[1].success({saved:true,synchronized:true,applied:false,flash_committed:false});requests[1].complete();
assert.equal(nodes.wr_usbip_settings_result.textContent,'saved');assert(!ctx.wrUSBIPSettingsDirty);
nodes.wr_usbip_settings_ack.checked=true;ctx.wrUSBIPSettingsSave();requests[2].failure();requests[2].complete();
assert(!ctx.wrUSBIPSettingsLoaded&&nodes.wr_usbip_settings_save.disabled);
ctx.wrUSBIPSettingsDirty=true;ctx.wrUSBIPSettingsLoad();assert.equal(requests.length,3);
confirm=true;ctx.wrUSBIPSettingsLoad();assert.equal(requests.length,4);
requests[3].success({state:0});requests[3].complete();assert(!ctx.wrUSBIPSettingsLoaded);
console.log('PASS USBIP settings view: codec, identity duplicates, confirmed save, one request, uncertain result and draft preservation');
