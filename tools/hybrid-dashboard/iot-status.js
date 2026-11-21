'use strict';
(function () {
  const networks = {
    main: 'Основна 2,4 ГГц',
    iot: 'IoT 2,4 ГГц',
    five: 'Основна 5 ГГц'
  };

  function parseSnapshot(snapshot) {
    if (!snapshot || snapshot.cacheState !== 'current' || snapshot.stage !== 'none' ||
        snapshot.truncated !== false || snapshot.invalid !== 0 ||
        !Number.isFinite(snapshot.collectionAgeMs) || snapshot.collectionAgeMs < 0 ||
        snapshot.collectionAgeMs > 15000 || !Array.isArray(snapshot.devices) ||
        snapshot.devices.length > 256) {
      throw new Error('Недоступний, застарілий або неповний знімок клієнтів.');
    }
    const rows = [];
    const identities = new Set();
    for (const device of snapshot.devices) {
      if (device.presence !== 'associated') continue;
      if (typeof device.mac !== 'string' || !/^(?:[0-9a-f]{2}:){5}[0-9a-f]{2}$/i.test(device.mac) ||
          !Array.isArray(device.radios) || device.radios.length > 2) {
        throw new Error('Некоректні дані клієнта.');
      }
      for (const radio of device.radios) {
        let network;
        if (radio.band === '2g' && radio.apIndex === 0) network = 'main';
        else if (radio.band === '2g' && radio.apIndex === 2) network = 'iot';
        else if (radio.band === '5g' && radio.apIndex === 0) network = 'five';
        else continue;
        const identity = device.mac.toLowerCase() + '/' + network;
        if (identities.has(identity)) throw new Error('Повторні дані клієнта.');
        identities.add(identity);
        const rssi = Number.isInteger(radio.rssi) && radio.rssi > -127 && radio.rssi < 0
          ? String(radio.rssi) : '—';
        rows.push({
          name: typeof device.hostname === 'string' ? device.hostname.slice(0, 128) : '—',
          ip: device.networkmapStale === false && typeof device.ip === 'string'
            ? device.ip.slice(0, 45) : '—',
          mac: device.mac, network, rssi
        });
      }
    }
    return rows;
  }

  function filterRows(rows, network, search) {
    const query = search.trim().toLocaleLowerCase('uk');
    return rows.filter(row => (network === 'all' || row.network === network) &&
      [row.name, row.ip, row.mac].some(value => value.toLocaleLowerCase('uk').includes(query)));
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { parseSnapshot, filterRows };
    return;
  }
  const element = id => document.getElementById(id);
  let rows = [];
  let available = false;
  let request = null;
  let stopped = false;

  function render() {
    const body = element('clients');
    body.replaceChildren();
    const visible = filterRows(rows, element('network').value, element('search').value);
    for (const row of visible) {
      const tr = document.createElement('tr');
      for (const text of [row.name, networks[row.network], row.ip, row.mac, row.rssi, 'Немає даних']) {
        const td = document.createElement('td');
        td.textContent = text;
        tr.appendChild(td);
      }
      body.appendChild(tr);
    }
    element('empty').hidden = !available || visible.length !== 0;
    for (const network of Object.keys(networks)) {
      const count = rows.filter(row => row.network === network).length;
      element('count-' + network).textContent = available && count > 0 ? String(count) : '—';
    }
  }

  async function refresh() {
    if (request || stopped) return;
    const controller = new AbortController();
    request = controller;
    element('refresh').disabled = true;
    element('monitor-status').textContent = 'Оновлення даних…';
    const timeout = setTimeout(() => controller.abort(), 8000);
    try {
      const response = await fetch('/wr_devices.json', {
        cache: 'no-store', credentials: 'same-origin', signal: controller.signal
      });
      if (!response.ok) throw new Error('Не вдалося отримати дані клієнтів.');
      const text = await response.text();
      if (text.length > 262144) throw new Error('Завелика відповідь сервера.');
      const next = parseSnapshot(JSON.parse(text));
      if (stopped) return;
      rows = next;
      available = true;
      element('updated').textContent = 'Останнє оновлення ' + new Date().toLocaleTimeString('uk');
      element('monitor-status').textContent = 'Поточний знімок спостережених Wi-Fi клієнтів.';
    } catch (error) {
      if (stopped) return;
      rows = [];
      available = false;
      element('monitor-status').textContent = 'Не вдалося оновити дані. Натисніть «Оновити» для повтору.';
    } finally {
      clearTimeout(timeout);
      request = null;
      if (!stopped) {
        element('refresh').disabled = false;
        render();
      }
    }
  }

  element('refresh').addEventListener('click', refresh);
  element('network').addEventListener('change', render);
  element('search').addEventListener('input', render);
  function poll() {
    if (element('automatic').checked && !document.hidden) refresh();
  }
  let timer = setInterval(poll, 10000);
  window.addEventListener('pageshow', event => {
    if (!event.persisted) return;
    stopped = false;
    timer = setInterval(poll, 10000);
    refresh();
  });
  window.addEventListener('pagehide', () => {
    stopped = true;
    clearInterval(timer);
    if (request) request.abort();
  });
  refresh();
}());
