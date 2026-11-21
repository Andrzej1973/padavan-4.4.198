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
      fetch:async url=>({ok:true,json:async()=>url==='/wr_modern.json'?{wifiConfiguration:{schemaVersion:1,source:'stored-nvram',runtimeVerified:false,shared:'0',guests:{'24':{enable:'1',ssid:'Stored Guest <24>',closed:'0',auth_mode:'psk',wpa_mode:'2',crypto:'aes',lan_isolate:'1',ap_isolate:'0',macrule:'0',mcs_mode:'0',date_x:'0111110',time_x:'08002200',time2_x:'10002300',wpa_psk:'DO-NOT-COPY'}},bands:Object.fromEntries(['24','5'].map(b=>[b,{ssid:'Stored-'+b,auth_mode:'psk',wep_x:'0',wpa_mode:'2',crypto:'aes',radio_x:'1',closed:'0',channel:b==='24'?'6':'44',HT_BW:'1',gmode:'2',HT_EXTCHA:'1',country_code:'UA',radio_date_x:'0111110',radio_time_x:'08002200',radio_time2_x:'10002300'}]))}}:({...original,demo:false})}),
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
    if(['wifi/split/24/general','wifi/split/5/general'].includes(route)) {
      assert(controls.length>=8 && controls.every(n=>n.disabled===true),route);
      assert(content.some(n=>n.textContent==='Радіопараметри'));
      if(route==='wifi/split/5/general'){
        assert(controls.some(n=>n.value==='a/n'));
        assert(controls.some(n=>n.value==='UA'));
        assert(controls.some(n=>n.value==='08:00 – 22:00'));
        assert(content.some(n=>n.textContent==='Розклад роботи'));
        assert(!controls.some(n=>n.value==='b/g/n'));
      }
      assert(!content.some(n=>(n.textContent||'').includes('Мережа без пароля')));
    } else if(route==='wifi/split/24/guest') {
      assert(controls.length>=15 && controls.every(n=>n.disabled===true),route);
      assert(controls.some(n=>n.value==='Stored Guest <24>'));
      assert(controls.some(n=>n.value==='08:00 – 22:00'));
      assert(controls.some(n=>n.value==='10:00 – 23:00'));
      assert(!controls.some(n=>n.type==='password' || n.value==='DO-NOT-COPY'));
      assert(content.some(n=>n.textContent==='Ізоляція та доступ'));
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
  for(const activeBand of ['24','5']) for(const variant of ['open','shared','20mhz','missing','unknown','legacy']) {
    const nodes=new Map();
    const get=id=>{if(!nodes.has(id))nodes.set(id,new Node('main'));return nodes.get(id);};
    const band={ssid:'Stored',auth_mode:variant==='open'?'open':'psk',wep_x:'0',wpa_mode:'2',crypto:'aes',radio_x:variant==='unknown'?'?':'0',closed:variant==='unknown'?'':'0',channel:'0',HT_BW:variant==='20mhz'?'0':'1',gmode:variant==='legacy'?'0':'2',HT_EXTCHA:'1'};
    const data=variant==='missing'?{}:{wifiConfiguration:{schemaVersion:1,source:'stored-nvram',runtimeVerified:false,shared:variant==='shared'?'1':'0',bands:{24:band,5:band}}};
    let failure;
    vm.runInNewContext(source,{
      fetch:async url=>({ok:true,json:async()=>url==='/wr_modern.json'?data:({...original,demo:false})}),
      document:{getElementById:get,querySelector:get,createElement:t=>new Node(t)},
      location:{hash:'#wifi/split/'+activeBand+'/general'},window:{addEventListener(){}},
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
  console.log('PASS accepted page02/04 conditional states: open warning, shared-lock notice, 20MHz dependency, missing-config fallback; no Apply');
})().catch(e=>{console.error(e);process.exitCode=1;});

(async()=>{
  for(const variant of ['missing','malformed','open','radio-off','unknown']) {
    const nodes=new Map();
    const get=id=>{if(!nodes.has(id))nodes.set(id,new Node('main'));return nodes.get(id);};
    const band={ssid:'Main',auth_mode:'psk',wep_x:'0',wpa_mode:'2',crypto:'aes',radio_x:variant==='radio-off'?'0':'1',closed:'0',channel:'6',HT_BW:'1',gmode:'2',HT_EXTCHA:'1'};
    const guest={enable:variant==='unknown'?'?':'0',ssid:'Independent Guest',closed:'0',auth_mode:variant==='open'?'open':'psk',wpa_mode:'2',crypto:'aes',lan_isolate:'1',ap_isolate:'0',macrule:'0',mcs_mode:'0',date_x:variant==='unknown'?'bad':'1000001',time_x:variant==='unknown'?'24002500':'22000800',time2_x:'10002300',wpa_psk:'SECRET-NEVER-RENDER'};
    if(variant==='malformed') delete guest.crypto;
    const data={wifiConfiguration:{schemaVersion:1,source:'stored-nvram',runtimeVerified:false,shared:'1',bands:{24:band,5:band},guests:variant==='missing'?{}:{24:guest}}};
    let failure;
    vm.runInNewContext(source,{
      fetch:async url=>({ok:true,json:async()=>url==='/wr_modern.json'?data:({...original,demo:false})}),
      document:{getElementById:get,querySelector:get,createElement:t=>new Node(t)},
      location:{hash:'#wifi/split/24/guest'},window:{addEventListener(){}},
      console:{error:e=>{failure=e;}},TextEncoder,
    });
    await new Promise(resolve=>setImmediate(resolve));assert.ifError(failure);
    const content=flatten(get('modern-wifi'));
    const unavailable=['missing','malformed'].includes(variant);
    assert.equal(content.some(n=>n.tagName==='INPUT'),!unavailable);
    assert.equal(content.some(n=>(n.textContent||'').startsWith('Не вдалося прочитати налаштування Guest')),unavailable);
    assert.equal(content.some(n=>(n.textContent||'').startsWith('Гостьова мережа без пароля')),variant==='open');
    assert.equal(content.some(n=>(n.textContent||'').startsWith('Радіомодуль 2,4 ГГц вимкнено')),variant==='radio-off');
    assert(!content.some(n=>n.value==='Main'||n.value==='SECRET-NEVER-RENDER'));
    assert(!content.some(n=>n.tagName==='BUTTON'||n.tagName==='FORM'));
    if(variant==='unknown') assert(content.some(n=>n.textContent==='Невідомо'));
    if(!unavailable && variant!=='unknown') assert(content.some(n=>n.value==='22:00 – 08:00'));
  }
  console.log('PASS Guest03 conditional states: missing/malformed configuration, open warning, radio off, unknown schedule, independent shared-mode values; no writes');
})().catch(e=>{console.error(e);process.exitCode=1;});
