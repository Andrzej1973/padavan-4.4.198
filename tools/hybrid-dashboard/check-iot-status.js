'use strict';
const assert = require('node:assert/strict');
const { parseSnapshot, filterRows } = require('./iot-status.js');
const snapshot = {
  cacheState: 'current', stage: 'none', truncated: false, invalid: 0,
  collectionAgeMs: 100,
  devices: [
    { mac: '00:11:22:33:44:55', hostname: '<script>client</script>', ip: '192.168.1.2',
      networkmapStale: false, presence: 'associated',
      radios: [{ band: '2g', apIndex: 0, rssi: -55 }, { band: '5g', apIndex: 0, rssi: -67 }] },
    { mac: '00:11:22:33:44:66', hostname: 'Sensor', ip: '192.168.2.2',
      networkmapStale: true, presence: 'associated',
      radios: [{ band: '2g', apIndex: 2, rssi: null }] },
    { mac: '00:11:22:33:44:77', presence: 'associated',
      radios: [{ band: '5g', apIndex: 2, rssi: -40 }] }
  ]
};
const rows = parseSnapshot(snapshot);
assert.deepEqual(rows.map(row => row.network), ['main', 'five', 'iot']);
assert.equal(rows[0].name, '<script>client</script>');
assert.equal(rows[2].ip, '—');
assert.equal(rows[2].rssi, '—');
assert.equal(filterRows(rows, 'five', '192.168').length, 1);
assert.equal(filterRows(rows, 'all', 'SENSOR').length, 1);
for (const change of [
  { cacheState: 'stale' }, { stage: 'radio' }, { invalid: 1 },
  { truncated: true }, { collectionAgeMs: 15001 }, { collectionAgeMs: null },
  { devices: null }
]) assert.throws(() => parseSnapshot({ ...snapshot, ...change }));
assert.throws(() => parseSnapshot({ ...snapshot, devices: [snapshot.devices[0], snapshot.devices[0]] }));
assert.deepEqual(parseSnapshot({ ...snapshot, devices: [] }), []);
console.log('PASS monitor band/BSS attribution, stale/incomplete refusal, unknown RSSI/IP, duplicate refusal and filtering. DOM, live endpoint and runtime remain unverified.');
