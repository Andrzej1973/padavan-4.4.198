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
      fetch:async url=>({ok:true,json:async()=>url==='/wr_modern.json'?{wifiConfiguration:{schemaVersion:1,source:'stored-nvram',runtimeVerified:false,shared:'0',bands:Object.fromEntries(['24','5'].map(b=>[b,{ssid:'Stored-'+b,auth_mode:'psk',wep_x:'0',wpa_mode:'2',crypto:'aes',radio_x:'1',closed:'0',channel:b==='24'?'6':'44',HT_BW:'1',gmode:'2',HT_EXTCHA:'1'}]))}}:({...original,demo:false})}),
      document:{getElementById:get,querySelector:get,createElement:t=>new Node(t)},
      location:{hash:'#'+route}, window:{addEventListener(){}},
      console:{error:e=>{failure=e;}}, TextEncoder,
    });
    await new Promise(resolve=>setImmediate(resolve));
    assert.ifError(failure);
    const content=flatten(get('modern-wifi'));
    assert.equal(get('modern-wifi').hidden,false,route);
    assert(!content.some(n=>['FORM','BUTTON'].includes(n.tagName)),route);
    const controls=content.filter(n=>['INPUT','SELECT','TEXTAREA'].includes(n.tagName));
    if(route==='wifi/split/24/general') {
      assert(controls.length>=8 && controls.every(n=>n.disabled===true),route);
      assert(content.some(n=>n.textContent==='Радіопараметри'));
      assert(!content.some(n=>(n.textContent||'').includes('Мережа без пароля')));
    } else assert.equal(controls.length,0,route);
    assert(!content.some(n=>/demo-password|Home-2.4G|Home-5G/.test(n.textContent||'')),route);
    if(route==='wifi/common') {
      assert(content.some(n=>n.textContent==='Stored-24'));
      assert(content.some(n=>n.textContent==='Stored-5'));
      assert(content.some(n=>n.textContent==='WPA2 Personal'));
      assert(content.some(n=>n.textContent==='Увімкнено (збережено)'));
      assert(!content.some(n=>(n.textContent||'').includes('(код)')));
    }
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

// Accepted page02 state gallery describes alternatives, not simultaneous warnings.
(async()=>{
  for(const variant of ['open','shared','20mhz','missing','unknown','legacy']) {
    const nodes=new Map();
    const get=id=>{if(!nodes.has(id))nodes.set(id,new Node('main'));return nodes.get(id);};
    const band={ssid:'Stored',auth_mode:variant==='open'?'open':'psk',wep_x:'0',wpa_mode:'2',crypto:'aes',radio_x:variant==='unknown'?'?':'0',closed:variant==='unknown'?'':'0',channel:'0',HT_BW:variant==='20mhz'?'0':'1',gmode:variant==='legacy'?'0':'2',HT_EXTCHA:'1'};
    const data=variant==='missing'?{}:{wifiConfiguration:{schemaVersion:1,source:'stored-nvram',runtimeVerified:false,shared:variant==='shared'?'1':'0',bands:{24:band,5:band}}};
    let failure;
    vm.runInNewContext(source,{
      fetch:async url=>({ok:true,json:async()=>url==='/wr_modern.json'?data:({...original,demo:false})}),
      document:{getElementById:get,querySelector:get,createElement:t=>new Node(t)},
      location:{hash:'#wifi/split/24/general'},window:{addEventListener(){}},
      console:{error:e=>{failure=e;}},TextEncoder,
    });
    await new Promise(resolve=>setImmediate(resolve));assert.ifError(failure);
    const content=flatten(get('modern-wifi'));
    assert.equal(content.some(n=>(n.textContent||'').startsWith('Мережа без пароля')),variant==='open');
    assert.equal(content.some(n=>n.textContent==='Назва та захист спільні для 2,4 і 5 ГГц'),variant==='shared');
    if(variant==='missing') {
      assert(!content.some(n=>n.tagName==='INPUT'));
      assert(content.some(n=>(n.textContent||'').startsWith('Не вдалося прочитати конфігурацію')));
    }
    if(variant==='20mhz') assert(!content.some(n=>n.textContent==='Додатковий канал'));
    if(variant==='legacy') assert(!content.some(n=>n.textContent==='Ширина каналу' || n.textContent==='Додатковий канал'));
    if(variant==='unknown') assert(!content.some(n=>n.tagName==='INPUT' && n.type==='checkbox'));
    assert(!content.some(n=>n.tagName==='BUTTON'||n.tagName==='FORM'));
  }
  console.log('PASS accepted page02 conditional states: open warning, shared-lock notice, 20MHz dependency, missing-config fallback; no Apply');
})().catch(e=>{console.error(e);process.exitCode=1;});
