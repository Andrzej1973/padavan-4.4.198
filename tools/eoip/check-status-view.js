'use strict';
const assert = require('assert');
const view = require('./status-view.js');
function snapshot() {
    return {schema: 1, slots: Array.from({length: 8}, (_, slot) => ({slot, state: 'absent'}))};
}
async function main() {
    let reply = snapshot();
    reply.slots[2] = {slot: 2, state: 'up', ifindex: 42, mtu: 1458, master: 0};
    assert.strictEqual(view.parse(reply)[2].ifindex, 42);
    reply.slots.reverse();
    assert.strictEqual(view.parse(reply)[2].slot, 2);
    for (const bad of [null, {}, {schema: 2, slots: []}, {schema: 1, slots: []}])
        assert.strictEqual(view.parse(bad), null);
    reply = snapshot(); reply.slots[1].slot = 0;
    assert.strictEqual(view.parse(reply), null);
    reply = snapshot(); reply.slots[0].state = 'working';
    assert.strictEqual(view.parse(reply), null);
    reply = snapshot(); reply.slots[0] = {slot: 0, state: 'up', ifindex: '42', mtu: 1458, master: 0};
    assert.strictEqual(view.parse(reply), null);
    const displays = []; let resolve, calls = 0;
    const refresh = view.refresher(() => { calls++; return new Promise(r => { resolve = r; }); }, rows => displays.push(rows));
    const first = refresh();
    await Promise.resolve();
    assert.strictEqual(await refresh(), false);
    assert.strictEqual(calls, 1);
    resolve(snapshot());
    assert.strictEqual(await first, true);
    assert.strictEqual(displays[0], null);
    assert.strictEqual(displays[1].length, 8);
    const fail = view.refresher(() => Promise.reject(new Error('offline')), rows => displays.push(rows));
    assert.strictEqual(await fail(), false);
    assert.strictEqual(displays[displays.length - 1], null);
    console.log('PASS EoIP status model: schema, slot uniqueness, numeric fields, single-flight and failure clearing');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
