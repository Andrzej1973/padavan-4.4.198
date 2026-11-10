// Execute the actual renderer with production schema; DOM fixture only, not browser acceptance.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, 'public/wifi.js'), 'utf8');
const original = JSON.parse(fs.readFileSync(path.join(__dirname, 'public/wifi-schema.json'), 'utf8'));
class Node {
  constructor(tag) { this.tagName=tag.toUpperCase(); this.children=[]; this.dataset={}; this.classList={toggle(){}}; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children=nodes; }
  setAttribute() {}
  removeAttribute() {}
}
const flatten = n => [n,...n.children.flatMap(flatten)];
(async () => {
  const routes=['wifi/common','wifi/split','wifi/iot',...['24','5'].flatMap(b=>['general','guest','bridge','mac','radius','advanced'].map(s=>'wifi/split/'+b+'/'+s))];
  for (const route of routes) {
    const nodes=new Map();
    const get=id=>{ if(!nodes.has(id)) nodes.set(id,new Node('main')); return nodes.get(id); };
    let failure;
    vm.runInNewContext(source, {
      fetch:async()=>({ok:true,json:async()=>({...original,demo:false})}),
      document:{getElementById:get,querySelector:get,createElement:t=>new Node(t)},
      location:{hash:'#'+route}, window:{addEventListener(){}},
      console:{error:e=>{failure=e;}},
    });
    await new Promise(resolve=>setImmediate(resolve));
    assert.ifError(failure);
    const content=flatten(get('modern-wifi'));
    assert.equal(get('modern-wifi').hidden,false,route);
    assert(!content.some(n=>['FORM','INPUT','SELECT','TEXTAREA','BUTTON'].includes(n.tagName)),route);
    assert(!content.some(n=>/demo-password|Home-2.4G|Home-5G/.test(n.textContent||'')),route);
    const links=content.filter(n=>n.href?.startsWith('/Advanced_'));
    const expected=route==='wifi/common'?2:route.startsWith('wifi/split/')?1:0;
    assert.equal(links.length,expected,route);
    if (expected===1) {
      const [, ,band, section]=route.split('/');
      assert.equal(links[0].href,'/'+original.pages[band][section].classic,route);
    }
  }
  console.log('PASS: actual production Wi-Fi renderer, 15 routes; no draft forms; exact per-band Classic destinations; IoT reserved. DOM fixture only.');
})().catch(e=>{console.error(e);process.exitCode=1;});
