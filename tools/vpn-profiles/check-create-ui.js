const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, 'web/vpn-profiles-page.html'), 'utf8');
const source = html.match(/<script[^>]*>([\s\S]*?)<\/script>/)[1]
 .replace(/<%[\s\S]*?%>/g, '"0123456789abcdef0123456789abcdef"');
function fixture(overrides = {}) {
 const elements = {
  wr_vpn_create_id: {value: '2'},
  wr_vpn_create_protocol: {value: 'wireguard'},
  wr_vpn_create_config: {value: '[Interface]\nPrivateKey = fixture\n'},
  wr_vpn_create_button: {disabled: false},
  wr_vpn_create_status: {textContent: '', getAttribute: key => key},
  wr_vpn_protect: {value: ''},
  wr_vpn_protect_help: {getAttribute: key => key},
 };
 for (const [id, value] of Object.entries(overrides)) elements[id].value = value;
 const requests = [], alerts = [];
 const context = {document: {getElementById: id => elements[id]},
  alert: text => alerts.push(text), confirm: () => true,
  jQuery: Object.assign(function(selector) {
   if (selector === '#wr_vpn_protect') return {val: () => elements.wr_vpn_protect.value};
  }, {ajax: request => requests.push(request)})};
 vm.createContext(context); vm.runInContext(source, context);
 return {context, elements, requests, alerts};
}
for (const protocol of ['wireguard', 'amneziawg']) {
 const f = fixture({wr_vpn_create_protocol: protocol});
 const config = f.elements.wr_vpn_create_config.value;
 f.context.wrVPNCreate(); f.context.wrVPNCreate();
 assert.equal(f.requests.length, 1, 'duplicate click must not submit twice');
 const r = f.requests[0];
 assert.equal(r.url, '/wr_vpn_create.cgi'); assert.equal(r.type, 'POST');
 assert.equal(r.processData, false); assert.equal(r.dataType, 'json');
 assert.equal(r.data, `0123456789abcdef0123456789abcdef\n2\n${protocol}\n${config}`);
 assert.equal(f.elements.wr_vpn_create_button.disabled, true);
 r.success({saved: true, started: false});
 assert.equal(f.elements.wr_vpn_create_config.value, '');
 assert.equal(f.elements.wr_vpn_create_status.textContent, 'data-saved');
 assert.equal(f.elements.wr_vpn_create_button.disabled, false);
 assert.equal(f.requests.length, 1, 'save must not activate or export');
}
for (const overrides of [{wr_vpn_create_id: '01'}, {wr_vpn_create_id: '1000'},
 {wr_vpn_create_id: '1\n2'}, {wr_vpn_create_protocol: 'other'}, {wr_vpn_create_config: ''}]) {
 const f = fixture(overrides); f.context.wrVPNCreate();
 assert.equal(f.requests.length, 0);
 assert.equal(f.elements.wr_vpn_create_status.textContent, 'data-failed');
}
for (const response of [null, {saved: true}, {saved: true, started: true}, {error: 'create_unconfirmed'}, 'error']) {
 const f = fixture(); const before = f.elements.wr_vpn_create_config.value;
 f.context.wrVPNCreate();
 if (response === 'error') f.requests[0].error(); else f.requests[0].success(response);
 assert.equal(f.elements.wr_vpn_create_button.disabled, false);
 assert.equal(f.elements.wr_vpn_create_status.textContent, 'data-failed');
 assert.equal(f.elements.wr_vpn_create_config.value, before, 'unconfirmed save must not discard user input');
 assert.equal(f.requests.length, 1, 'no automatic retry on uncertain write');
}
{
 const f = fixture(); f.context.wrVPNToken = ''; f.context.wrVPNCreate();
 assert.equal(f.requests.length, 0);
}
console.log('PASS create UI: WG/AWG POST payload, no activation, duplicate/invalid refusal, confirmed-save clearing, uncertain-write handling');
for (const value of ['', '192.168.1.0/24, 10.8.0.0/24', 'bad', Array(9).fill('10.0.0.0/24').join(',')]) {
 const f = fixture({wr_vpn_protect: value}); f.context.wrVPNAct('up', 2);
 assert.equal(f.requests.length, 0); assert.equal(f.alerts.length, 1);
}
{
 const protect = '192.168.1.0/24,10.8.0.0/24';
 const f = fixture({wr_vpn_protect: protect}); f.context.wrVPNAct('up', 2);
 assert.equal(f.requests.length, 1); assert.equal(f.requests[0].data.protect, protect);
 assert.equal(f.requests[0].data.operation, 'up');
}
for (const operation of ['down', 'delete']) {
 const f = fixture(); f.context.wrVPNAct(operation, 2);
 assert.equal(f.requests.length, 1); assert.equal(f.requests[0].data.operation, operation);
}
console.log('PASS explicit protected-subnet input: empty/invalid start refusal, exact forwarding, stop/delete remain available');
