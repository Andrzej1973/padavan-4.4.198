const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
for (const [name, prefix, key] of [['ssh', 'wrSSH', 'WRSSH'], ['iperf3', 'wrIperf3', 'WRIperf3'], ['privoxy', 'wrPrivoxy', 'WRPrivoxy']]) {
 const text = fs.readFileSync(path.join(__dirname, 'prepare-' + name + '-status.py'), 'utf8');
 const script = text.match(/(?:script|js) = r'''([\s\S]*?)'''/)[1];
 const elements = {}, timers = [], listeners = {};
 let now = 1000;
 class Clock extends Date {static now() {return now;}}
 const context = {Date: Clock, document: {hidden: false,
  getElementById: id => elements[id] ||= {},
  addEventListener: (type, callback) => {listeners[type] = callback;}},
  window: {setTimeout: (callback, delay) => {assert.equal(delay, 45000);timers.push(callback);}}};
 vm.createContext(context);vm.runInContext(script, context);
 const render = context[prefix + 'Render'];
 const status = () => elements['wr_' + name + '_process_status'].textContent;
 render(1);assert.equal(status(), '<#' + key + 'Present#>');
 const old = timers[0];render(0);old();assert.equal(status(), '<#' + key + 'Off#>');
 timers[1]();assert.equal(status(), '<#' + key + 'Unknown#>');
 render(1);now += 45001;listeners.visibilitychange();
 assert.equal(status(), '<#' + key + 'Unknown#>');
 for (const invalid of [1.5, -1, 5, '1', null, NaN]) {
  render(invalid);assert.equal(status(), '<#' + key + 'Unknown#>');
 }
 console.log('PASS ' + name + ' process observation expiry, stale timer rejection, visible-page age check and invalid state refusal');
}
