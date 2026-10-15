'use strict';
const assert=require('assert'), editor=require('./settings-editor.js');
const keys=['enable','autostart','local','remote','id','mtu','keepalive','retries','bridge'];
function snapshot(){return {schema:1,master:'1',slots:Array.from({length:8},(_,slot)=>{
 const row={slot};keys.forEach(key=>row[key]=['enable','autostart'].includes(key)?'0':'');return row;
})};}
class Node {
 constructor(tag,doc){this.tag=tag;this.ownerDocument=doc;this.children=[];this.attrs={};this.value='';}
 set textContent(value){this.text=String(value);this.children=[];}
 get textContent(){return this.text||'';}
 set innerHTML(value){throw new Error('HTML insertion is forbidden');}
 appendChild(child){this.children.push(child);}
 setAttribute(key,value){this.attrs[key]=value;}
}
const doc={createElement(tag){return new Node(tag,doc);}};
function all(node){return [node,...node.children.flatMap(all)];}
const labels={};
['slot','on','off','masterEnable','confirm','save','disable','reload','unavailable','loading','loaded','saving','saved','rejected','uncertain',...keys]
 .forEach(key=>labels[key]=key);
const tick=()=>new Promise(resolve=>setImmediate(resolve));
async function main(){
 assert(editor.valid(snapshot()));
 const bad=snapshot();bad.slots[1].slot=0;assert(!editor.valid(bad));
 bad.slots[1].slot=1;bad.slots[1].enable='bad';assert(!editor.valid(bad));
 const target=new Node('div',doc), payloads=[];
 let fail=false;
 editor.mount(target,labels,{
  read(output){return Promise.resolve(output==='wr_eoip_token'?'a'.repeat(32):snapshot());},
  save(payload){payloads.push(payload);return fail?Promise.reject(new Error('timeout')):
   Promise.resolve({saved_in_ram:true,apply_requested:true,applied:null});}
 });
 await tick();
 const buttons=all(target).filter(node=>node.tag==='button');
 const save=buttons.find(node=>node.text==='save'), disable=buttons.find(node=>node.text==='disable');
 const ack=all(target).find(node=>node.type==='checkbox');
 const message=all(target).find(node=>node.attrs.role==='status');
 assert(!save.disabled && !disable.disabled && message.text==='loaded');
 save.onclick();await tick();assert.strictEqual(payloads.length,0);
 ack.checked=true;save.onclick();save.onclick();await tick();
 assert.strictEqual(payloads.length,1);assert.strictEqual(payloads[0].eoip_enable,'1');
 assert.strictEqual(payloads[0].eoip_slot7_enable,'0');assert.strictEqual(message.text,'saved');
 assert.strictEqual(ack.checked,false);
 fail=true;ack.checked=true;save.onclick();await tick();
 assert.strictEqual(message.text,'uncertain');assert.strictEqual(payloads.length,2);
 const unavailable=new Node('div',doc);
 editor.mount(unavailable,labels,{
  read(output){return output==='wr_eoip_token'?Promise.resolve('b'.repeat(32)):Promise.reject(new Error('bad config'));},
  save(payload){payloads.push(payload);return Promise.resolve({saved_in_ram:true,apply_requested:true,applied:null});}
 });
 await tick();
 const nodes=all(unavailable), fallback=nodes.find(node=>node.tag==='button'&&node.text==='disable');
 assert(!fallback.disabled && nodes.find(node=>node.tag==='button'&&node.text==='save').disabled);
 nodes.find(node=>node.type==='checkbox').checked=true;fallback.onclick();await tick();
 assert.strictEqual(payloads[2].eoip_enable,'0');
 assert.deepStrictEqual(Object.keys(payloads[2]).sort(),['ack','eoip_enable','token']);
 console.log('PASS EoIP editor: bounded schema, load, confirmation, single-flight, uncertain response and independent disable');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
