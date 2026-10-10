'use strict';
const assert=require('assert');const homepage=require('./roaming-view.js');
class Element {
 constructor(tag){this.tagName=tag;this.children=[];this.parentNode=null;this.style={};this.attributes={};this.events={};this._text='';this.scrollTop=0;}
 get firstChild(){return this.children[0]||null;}
 set textContent(value){this._text=String(value);this.children=[];}get textContent(){return this._text+this.children.map(n=>n.textContent).join('');}
 appendChild(n){if(n.parentNode)n.parentNode.removeChild(n);this.children.push(n);n.parentNode=this;return n;}
 removeChild(n){this.children=this.children.filter(x=>x!==n);n.parentNode=null;}
 setAttribute(k,v){this.attributes[k]=v;}addEventListener(k,v){this.events[k]=v;}removeEventListener(k){delete this.events[k];}
}
const doc={createElement:tag=>new Element(tag),events:{},hidden:false,addEventListener:function(k,v){this.events[k]=v;},removeEventListener:function(k){delete this.events[k];},defaultView:{pageXOffset:0,pageYOffset:40,scrollTo:function(x,y){assert.strictEqual(y,40);}}};
function all(n){return [n].concat(...n.children.map(all));}
const root=new Element('section'),view=homepage.createView(doc,root);view.filter.value='';
const h={epoch:'session',dropped:4,clientDropped:2,clientEvictions:1,gap:false,events:[{kind:'observed',mac:'02:00:00:00:00:01',uptimeMs:5000,after:1},{kind:'gap',mac:'',uptimeMs:10000}]};
view.render(h);assert.equal(view.list.children.length,2);assert(root.textContent.includes('Observation gap'));assert(root.textContent.includes('Overwritten events: 4'));
view.details.open=true;view.list.scrollTop=25;view.filter.value='FF';view.filter.events.input();assert.equal(view.list.children.length,1);assert.equal(view.details.open,true);assert.equal(view.list.scrollTop,25);
view.render(h);assert.equal(view.filter.value,'FF');view.setState({state:'Stale'});assert(root.textContent.includes('last available history'));
console.log('PASS roaming timeline, MAC filter, gap visibility, expanded state and scroll preservation');

view.setState({state:'Updating'});assert(root.textContent.includes('last available history'));view.setState({state:'Current'});assert(!root.textContent.includes('last available history'));assert.equal(view.list.style.overflowY,'auto');

let options,started=0,stopped=0,visible;
const mounted=homepage.mount(doc,new Element('section'),{}, {create:(refresh,o)=>{options=o;return {start:()=>started++,stop:()=>stopped++,setVisible:v=>visible=v};}});
assert.equal(started,1);assert.equal(visible,true);doc.hidden=true;doc.events.visibilitychange();assert.equal(visible,false);doc.hidden=false;doc.events.visibilitychange();assert.equal(visible,true);mounted.stop();assert.equal(stopped,1);assert(!doc.events.visibilitychange);
class XHR {
 constructor(){XHR.last=this;this.readyState=0;this.status=200;this.responseText='';this.aborted=false;}
 open(method,url){assert.equal(method,'GET');assert(url.startsWith('/wr_roaming.json'));}
 setRequestHeader(name,value){assert.equal(name,'Accept');assert.equal(value,'application/json');}send(){}abort(){this.aborted=true;if(this.onabort)this.onabort();}
 reply(value){this.responseText=value;this.readyState=4;this.onreadystatechange();}
}
global.XMLHttpRequest=XHR;
let calls=0,result;
const abort=options.request((error,data)=>{calls++;result={error,data};});XHR.last.reply(JSON.stringify({epoch:'session'}));assert(!result.error);assert.equal(result.data.epoch,'session');abort();assert.equal(calls,1);
options.request(error=>result=error);XHR.last.reply('<html>login</html>');assert(result instanceof Error);
options.request(error=>result=error);XHR.last.reply('x'.repeat(131073));assert(result instanceof Error);
options.request(error=>result=error);XHR.last.onprogress({loaded:131073});assert(result instanceof Error);assert(XHR.last.aborted);
options.request(error=>result=error);XHR.last.status=401;XHR.last.reply('{}');assert(result instanceof Error);
assert(require('fs').readFileSync(require('path').join(__dirname,'roaming-view.js'),'utf8').split('').every(c=>c.charCodeAt(0)<128));
console.log('PASS history mount/visibility/cleanup, single completion, login/error rejection and bounded abortable JSON transport');
