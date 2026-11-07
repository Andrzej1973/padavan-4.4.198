const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const demo = require('./public/wifi.js');
const planner = require('../shared-wifi/ui.js').plan;
const schema = JSON.parse(fs.readFileSync(path.join(__dirname,'public/wifi-schema.json'),'utf8'));
const state = demo.makeState();
const before = JSON.stringify(state);
for (const hash of ['#wifi/common','#wifi/split','#wifi/iot',...['24','5'].flatMap(b=>Object.keys(demo.sections).map(s=>'#wifi/split/'+b+'/'+s))]) assert.notEqual(demo.route(hash).view,'home');
assert.equal(JSON.stringify(state),before);
state.bands[24].stream_tx='1'; state.bands[5].channel='44';
state.bands[5].closed='1'; state.iot.ssid='Independent-IoT';
state.common.ssid='Спільна мережа'; demo.synchronize(state,planner);
assert.equal(state.bands[24].ssid,'Спільна мережа');
assert.equal(state.bands[5].ssid,'Спільна мережа');
assert.equal(state.bands[24].stream_tx,'1'); assert.equal(state.bands[5].channel,'44');
assert.equal(state.bands[5].closed,'1'); assert.equal(state.iot.ssid,'Independent-IoT');
state.shared=false;
assert.equal(state.bands[5].ssid,'Спільна мережа');
const invalid=demo.makeState(); invalid.common.wpa_psk='short';
assert.throws(()=>demo.synchronize(invalid,planner));
assert.equal(invalid.bands[5].ssid,'Home-5G');
for(const band of ['24','5']) {
  assert.equal(Object.keys(schema.pages[band]).length,6);
  for(const page of Object.values(schema.pages[band])) {
    assert.match(page.sha256,/^[a-f0-9]{64}$/);
    assert(!page.fields.some(f=>f.key.endsWith('_txbf')));
    assert(!JSON.stringify(page).includes('<%'));
    for (const f of page.fields) {
      assert(!f.options.some(o=>o[1].toLowerCase().includes('ax')));
      if (/_stream_(tx|rx)$/.test(f.key)) assert(f.options.every(o=>['1','2'].includes(o[0])));
    }
  }
}
assert.equal(demo.route('#wifi/split/5/unknown').section,'general');
console.log('PASS: 15 Wi-Fi routes; six sections per band; navigation is pure; shared planner validates and copies only six fields; independent/professional/IoT values retained; unsupported TXBF absent.');
