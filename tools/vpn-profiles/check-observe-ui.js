const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, 'web/vpn-profiles-page.html'), 'utf8')
 .match(/<script[^>]*>([\s\S]*?)<\/script>/)[1].replace(/<%[\s\S]*?%>/g, '""');
function scenario(response, expected) {
 const label = {textContent: ''}, button = {disabled: false}, requests = [], timers = [];
 const text = {getAttribute: key => key};
 const context = {document: {getElementById: id => id === 'wr_vpn_link_2' ? label : text},
  Date: class {toLocaleTimeString() {return '12:34:56';}},
  setTimeout: (callback, ms) => {assert.equal(ms, 30000);timers.push(callback);},
  jQuery: Object.assign(function() {}, {ajax: r => requests.push(r)})};
 vm.createContext(context); vm.runInContext(source, context);
 context.wrVPNObserve(2, button); context.wrVPNObserve(2, button);
 assert.equal(requests.length, 1);
 assert.equal(requests[0].url, '/update.cgi');
 assert.equal(requests[0].data.output, 'wr_vpn_profile_observation');
 assert.equal(requests[0].data.arg0, 2); assert.equal(requests[0].cache, false);
 if (response === 'error') requests[0].error(); else requests[0].success(response);
 const sampled = ['up', 'down', 'absent'].includes(expected);
 assert.equal(label.textContent, 'data-' + expected + (sampled ? ' (12:34:56)' : ''));
 assert.equal(button.disabled, false);
 assert.equal(requests.length, 1, 'observation must not mutate or poll');
 assert.equal(timers.length, sampled ? 1 : 0);
 if (sampled) {
  context.wrVPNObserve(2, button); // New query invalidates the old expiry.
  requests[1].success(link);
  timers[0](); assert.equal(label.textContent, 'data-up (12:34:56)');
  timers[1](); assert.equal(label.textContent, 'data-unknown');
  assert.equal(requests.length, 2, 'expiry must not query the network');
 }
}
const link = {id: 2, ownership: 'unverified', interface_state: 'observed', kind: 'wireguard', up: true};
scenario(link, 'up');
scenario({...link, kind: 'amneziawg', up: false}, 'down');
scenario({...link, interface_state: 'absent', up: null}, 'absent');
scenario({...link, id: 1}, 'unknown');
scenario({...link, up: 'true'}, 'unknown');
scenario({...link, kind: 'other'}, 'unknown');
scenario({...link, interface_state: 'unknown'}, 'unknown');
scenario(null, 'unknown'); scenario('error', 'unknown');
console.log('PASS profile observation UI: exact ID, absent/up/down/unknown, no connectivity claim or network mutation');
