'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class Element {
  constructor() { this.children = []; this.listeners = {}; this.value = ''; }
  addEventListener(name, handler) { this.listeners[name] = handler; }
  appendChild(child) { this.children.push(child); }
  replaceChildren() { this.children = []; }
}
const ids = ['clients', 'network', 'search', 'empty', 'count-main', 'count-iot',
  'count-five', 'refresh', 'monitor-status', 'updated', 'automatic'];
const elements = Object.fromEntries(ids.map(id => [id, new Element()]));
elements.network.value = 'all';
elements.automatic.checked = true;
const events = {};
const requests = [];
const intervals = new Map();
let intervalId = 0;
const context = {
  document: { getElementById: id => elements[id], createElement: () => new Element(), hidden: false },
  window: { addEventListener: (name, handler) => { events[name] = handler; } },
  AbortController, Date,
  setTimeout, clearTimeout,
  setInterval: handler => { intervals.set(++intervalId, handler); return intervalId; },
  clearInterval: id => intervals.delete(id),
  fetch: (url, options) => new Promise(resolve => requests.push({ url, options, resolve }))
};
vm.runInNewContext(fs.readFileSync(__dirname + '/iot-status.js', 'utf8'), context);
const snapshot = {
  cacheState: 'current', stage: 'none', truncated: false, invalid: 0, collectionAgeMs: 1,
  devices: [{ mac: '00:11:22:33:44:55', hostname: '<b>sensor</b>', ip: '192.168.2.2',
    networkmapStale: false, presence: 'associated', radios: [{ band: '2g', apIndex: 2, rssi: -60 }] }]
};
const flush = () => new Promise(resolve => setImmediate(resolve));
async function answer(index, data) {
  requests[index].resolve({ ok: true, text: async () => JSON.stringify(data) });
  await flush();
}
(async () => {
  assert.equal(requests.length, 1);
  elements.refresh.listeners.click();
  assert.equal(requests.length, 1);
  await answer(0, snapshot);
  assert.equal(elements.clients.children.length, 1);
  assert.equal(elements.clients.children[0].children[0].textContent, '<b>sensor</b>');
  assert.equal(elements['count-iot'].textContent, '1');
  elements.network.value = 'five'; elements.network.listeners.change();
  assert.equal(elements.clients.children.length, 0);
  assert.equal(elements.empty.hidden, false);
  elements.network.value = 'all'; elements.network.listeners.change();
  elements.search.value = 'absent'; elements.search.listeners.input();
  assert.equal(elements.clients.children.length, 0);
  elements.search.value = ''; elements.search.listeners.input();
  elements.refresh.listeners.click();
  await answer(1, { ...snapshot, cacheState: 'stale' });
  assert.equal(elements.clients.children.length, 0);
  assert.equal(elements['count-iot'].textContent, '—');
  assert.equal(elements.empty.hidden, true);
  assert.equal(elements.refresh.disabled, false);
  elements.refresh.listeners.click(); await answer(2, snapshot);
  assert.equal(elements.clients.children.length, 1);
  events.pagehide(); assert.equal(intervals.size, 0);
  events.pageshow({ persisted: true });
  assert.equal(intervals.size, 1);
  assert.equal(requests.length, 4);
  await answer(3, snapshot);
  events.pagehide();
  console.log('PASS actual monitor DOM logic with injected DOM/fetch: duplicate request guard, filters/search, stale clearing, retry and back-cache resume.');
})().catch(error => { console.error(error); process.exitCode = 1; });
