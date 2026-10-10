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
