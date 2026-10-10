'use strict';
const assert=require('assert');const homepage=require('./homepage.js');
class Element {
 constructor(tag){this.tagName=tag;this.children=[];this.parentNode=null;this.style={};this.attributes={};this.events={};this._text='';this.scrollTop=0;}
 set textContent(value){this._text=String(value);this.children=[];}get textContent(){return this._text+this.children.map(n=>n.textContent).join('');}
 appendChild(n){if(n.parentNode)n.parentNode.removeChild(n);this.children.push(n);n.parentNode=this;return n;}
 removeChild(n){this.children=this.children.filter(x=>x!==n);n.parentNode=null;}
 setAttribute(k,v){this.attributes[k]=v;}addEventListener(k,v){this.events[k]=v;}removeEventListener(k){delete this.events[k];}
}
const doc={createElement:tag=>new Element(tag),events:{},hidden:false,addEventListener:function(k,v){this.events[k]=v;},removeEventListener:function(k){delete this.events[k];},defaultView:{pageXOffset:0,pageYOffset:40,scrollTo:function(x,y){assert.strictEqual(y,40);}}};
function all(n){return [n].concat(...n.children.map(all));}
const root=new Element('section'),view=homepage.createView(doc,root);
const devices=[{mac:'00:11:22:33:44:55',ip:'192.168.1.2',hostname:'android-phone',networkmapStale:false},{mac:'02:11:22:33:44:66',ip:'192.168.1.3',hostname:'<img src=x onerror=alert(1)>',networkmapStale:true}];
view.render({devices,sourceUpdatedAt:1700000000});
let rows=all(root).filter(n=>n.tagName==='tr'&&n.parentNode.tagName==='tbody');assert.strictEqual(rows.length,2);const first=rows[0];
assert.ok(root.textContent.includes('Possible')&&root.textContent.includes('Last known observation'));
assert.ok(root.textContent.includes('<img src=x onerror=alert(1)>'));assert.ok(!all(root).some(n=>n.tagName==='img'));
const group=all(root).find(n=>n.attributes['data-network']==='unknown');group.open=false;
const scroll=all(group).find(n=>n.className==='wr-device-scroll');scroll.scrollTop=25;
view.filter.value='Android';view.filter.events.change();assert.strictEqual(rows[1].style.display,'none');
view.render({devices:[Object.assign({},devices[0],{hostname:'android-updated'}),devices[1]],sourceUpdatedAt:1700000001});
rows=all(root).filter(n=>n.tagName==='tr'&&n.parentNode.tagName==='tbody');assert.strictEqual(rows[0],first);assert.strictEqual(view.filter.value,'Android');assert.strictEqual(group.open,false);assert.strictEqual(scroll.scrollTop,25);
view.setState({state:'Stale'});assert.ok(root.textContent.includes('showing last available'));
view.render({devices:[devices[0]],truncated:true,invalid:2});assert.strictEqual(all(root).filter(n=>n.tagName==='tr'&&n.parentNode.tagName==='tbody').length,1);assert.ok(root.textContent.includes('Snapshot truncated'));
let options,started=0,stopped=0,visible;
const mounted=homepage.mount(doc,new Element('section'),{create:o=>{options=o;return {start:()=>started++,stop:()=>stopped++,setVisible:v=>visible=v,retry:()=>{}};}});
assert.strictEqual(started,1);assert.strictEqual(visible,true);doc.hidden=true;doc.events.visibilitychange();assert.strictEqual(visible,false);mounted.stop();assert.strictEqual(stopped,1);
class XHR {
 constructor(){XHR.last=this;this.readyState=0;this.status=200;this.responseText='';}
 open(method,url){assert.strictEqual(method,'GET');assert.ok(url.startsWith('/wr_devices.json'));}setRequestHeader(){}send(){}abort(){if(this.onabort)this.onabort();}
 reply(value){this.responseText=value;this.readyState=4;this.onreadystatechange();}
}
global.XMLHttpRequest=XHR;
let received;const abort=options.request((error,data)=>received={error,data});XHR.last.reply(JSON.stringify({devices:[],epoch:'e',sequence:1}));assert.ok(!received.error);assert.strictEqual(received.data.sequence,1);abort();assert.ok(!received.error);
options.request(error=>received=error);XHR.last.reply('<html>login</html>');assert.ok(received instanceof Error);
console.log('PASS safe DOM text insertion, stable rows/filter/groups/scroll, stale feedback, visibility wiring and JSON XHR transport');
