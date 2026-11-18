'use strict';
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const ids = {};
['message','refresh','ram','auto','save','enabled','ssid','gateway','mask','first','last','action','password'].forEach(name => {
    ids['iot-' + name] = {value: name === 'action' ? 'keep' : '', checked: false, disabled: false, textContent: ''};
});
const calls = [], timers = [];
const window = {document: {getElementById: id => ids[id]}, jQuery: {ajax: call => calls.push(call)}, setTimeout: fn => timers.push(fn)};
let now = 1000;
vm.runInNewContext(fs.readFileSync(__dirname + '/classic-config.js', 'utf8'), {window, Error, Date: {now: () => now}});
window.wrIotConfig.init();
assert(ids['iot-save'].disabled && !ids['iot-refresh'].disabled);
ids['iot-save'].onclick(); assert.strictEqual(calls.length, 0);
function load(configured = true) {
    ids['iot-refresh'].onclick();
    const token = calls.shift(); assert.strictEqual(token.url, '/wr_iot_token.cgi');
    token.success({token: 'a'.repeat(32)});
    const view = calls.shift(); assert.strictEqual(view.type, 'POST'); assert.strictEqual(view.url, '/wr_iot_view.cgi');
    view.success({revision: 'b'.repeat(32), configured, enabled: false, key_present: configured,
        ssid: configured ? '<IoT>' : '', gateway: configured ? '192.168.50.1' : '', mask: configured ? '255.255.255.0' : '', first: configured ? '192.168.50.20' : '', last: configured ? '192.168.50.200' : ''});
}
load(); assert.strictEqual(ids['iot-ssid'].value, '<IoT>');
assert(ids['iot-password'].disabled && !ids['iot-save'].disabled);
ids['iot-password'].value = 'unwanted';
ids['iot-save'].onclick();
const save = calls.shift(); assert.strictEqual(save.url, '/wr_iot_edit_save.cgi');
assert.strictEqual(save.data.wr_iot_request_psk, ''); assert.strictEqual(save.data.revision, 'b'.repeat(32));
ids['iot-save'].onclick(); assert.strictEqual(calls.length, 0);
save.success({accepted: true, id: 'c'.repeat(32)});
const poll = calls.shift(); assert.strictEqual(poll.url, '/wr_iot_result.cgi');
poll.success({id: 'c'.repeat(32), state: 'queued'}); assert.strictEqual(timers.length, 1);
timers.shift()(); calls.shift().success({id: 'c'.repeat(32), state: 'saved_in_flash'});
assert(ids['iot-save'].disabled && !ids['iot-refresh'].disabled && ids['iot-message'].textContent.includes('flash'));
assert.strictEqual(ids['iot-password'].value, '');
load(false); assert.strictEqual(ids['iot-action'].value, 'replace'); assert(!ids['iot-password'].disabled);
ids['iot-password'].value = 'new-password';ids['iot-ram'].onclick();
const ram = calls.shift(); assert.strictEqual(ram.url, '/wr_iot_edit_ram.cgi');assert.strictEqual(ram.data.wr_iot_request_psk, 'new-password');
ram.error();assert.strictEqual(calls.length, 0);assert(ids['iot-ram'].disabled);assert.strictEqual(ram.data.wr_iot_request_psk, '');
load();ids['iot-auto'].onclick();const auto = calls.shift();assert.strictEqual(auto.url, '/wr_iot_edit_auto.cgi');
auto.success({accepted: true, id: 'd'.repeat(32)});
calls.shift().success({id: 'd'.repeat(32), state: 'recovery_required'});
assert.strictEqual(calls.length, 0);assert.strictEqual(timers.length, 0);assert(ids['iot-message'].textContent.includes('не повторюється'));
load();ids['iot-refresh'].onclick();calls.shift().success({token: 'bad'});
assert(ids['iot-save'].disabled && !ids['iot-refresh'].disabled);
load();now += 110000;ids['iot-save'].onclick();assert.strictEqual(calls.length, 0);assert(ids['iot-save'].disabled);
load();now--;ids['iot-ram'].onclick();assert.strictEqual(calls.length, 0);assert(ids['iot-ram'].disabled);
console.log('PASS Classic config DOM: explicit reads, text/value rendering, KEEP/REPLACE, three endpoint modes, queue/result distinction, one-shot submit, no retry after uncertainty, secret field clearing; simulated network only');
