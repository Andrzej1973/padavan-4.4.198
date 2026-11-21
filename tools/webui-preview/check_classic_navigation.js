// Execute actual generic-page renderer; minimal DOM fixture, not browser acceptance.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const app=fs.readFileSync(path.join(__dirname,'public/app.js'),'utf8');
const renderer=app.slice(app.indexOf('function renderGenericPage('),app.indexOf('function renderRoute('));
class Node {
  constructor(tag){this.tagName=tag.toUpperCase();this.children=[];}
  append(...nodes){this.children.push(...nodes);}
  replaceChildren(){this.children=[];}
  addEventListener(){}
}
const flatten=n=>[n,...n.children.flatMap(flatten)];
for(const demo of [true,false]) {
  for(const route of ['vpn','iot']) {
    const mount=new Node('main');
    const page={title:'test',description:'test',classic:'vpncli.asp / Advanced_zerotier.asp / https://bad.example / ../apply.cgi / javascript:bad'};
    const context=vm.createContext({dashboardData:{demo,pages:{[route]:page}},byId:()=>mount,document:{createElement:t=>new Node(t)},openUnavailable(){}});
    vm.runInContext(renderer,context);
    assert.equal(vm.runInContext(`renderGenericPage('${route}')`,context),true);
    const nodes=flatten(mount);
    const links=nodes.filter(n=>n.tagName==='A');
    assert.deepEqual(links.map(n=>n.href),demo||route==='iot'?[]:['/vpncli.asp','/Advanced_zerotier.asp']);
    assert.equal(nodes.filter(n=>n.tagName==='BUTTON').length,demo&&route!=='iot'?1:0);
  }
}
console.log('PASS actual generic renderer: production Classic links, multiple destinations, invalid URLs rejected, DEMO explanations, IoT unavailable; DOM fixture only');
