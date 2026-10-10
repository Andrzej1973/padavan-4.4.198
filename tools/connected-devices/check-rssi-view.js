'use strict';
const assert=require('assert'),rssi=require('./rssi-view.js');
class Element {
 constructor(tag){this.tagName=tag;this.children=[];this.parentNode=null;this.style={};this.attributes={};this.events={};this.value='';this._text='';this.scrollTop=0;}
 set textContent(value){this._text=String(value);this.children=[];}get textContent(){return this._text+this.children.map(n=>n.textContent).join('');}
 get firstChild(){return this.children[0]||null;}
 appendChild(n){if(n.parentNode)n.parentNode.removeChild(n);this.children.push(n);n.parentNode=this;return n;}
 removeChild(n){this.children=this.children.filter(x=>x!==n);n.parentNode=null;}
 setAttribute(k,v){this.attributes[k]=v;}addEventListener(k,v){this.events[k]=v;}removeEventListener(k){delete this.events[k];}
}
const doc={createElement:tag=>new Element(tag)},root=new Element('section'),view=rssi.createView(doc,root);
const h={evicted:'0',radios:[{radio:0,available:false,attempted:true,missing:'1',restarts:'0'},{radio:1,available:true,attempted:true,missing:'0',restarts:'0'}],events:[{mac:'02:11:22:33:44:55',radio:0,uptimeMs:'999',attempt:1,stage:'frame_submitted'},{mac:'02:22:33:44:55:66',radio:1,uptimeMs:'1000',attempt:2,stage:'entry_cleared'}]};
view.render(h);assert.strictEqual(view.list.children.length,2);assert(view.list.textContent.includes('Station table entry cleared'));
view.details.open=true;view.list.scrollTop=18;view.filter.value='02:11';view.filter.events.input();
assert.strictEqual(view.list.children.length,1);assert(view.list.textContent.includes('Disconnect frame submitted'));
assert(view.details.open&&view.list.scrollTop===18);view.setState({state:'Stale'});assert(root.textContent.includes('last available data'));
view.render(h);assert.strictEqual(view.list.children.length,1);assert(view.details.open);
console.log('PASS RSSI DOM filtering, stage labels, stale notice and retained expansion/scroll');
