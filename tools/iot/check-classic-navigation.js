/* In-memory DOM checks: no dependencies, temporary directories or router calls. */
'use strict';
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync(__dirname + '/classic-navigation.js', 'utf8');
const pairs = ['Wireless', 'WGuest', 'WMode', 'ACL', 'WSecurity', 'WAdvanced']
    .map(stem => ['Advanced_' + stem + '2g_Content.asp', 'Advanced_' + stem + '_Content.asp']);
function check(path, expected, readyState = 'complete') {
    const ids = Object.create(null);
    function element(tag) {
        return {tag, children: [], attributes: {}, className: '',
            appendChild(n) { n.parentNode = this; this.children.push(n); return n; },
            insertBefore(n, before) { n.parentNode = this; this.children.splice(this.children.indexOf(before), 0, n); },
            setAttribute(k, v) { this.attributes[k] = v; },
            set id(v) { this._id = v; ids[v] = this; }, get id() { return this._id; }};
    }
    const host = element('div'), tab = element('div'), banner = element('div');
    tab.id = 'tabMenu'; host.appendChild(tab);
    const button = element('input'); button.id = 'wifi5_b'; button.className = 'btn btn-mini btn-info';
    banner.appendChild(button);
    const guest = element('div'), guestButton = element('input');
    guestButton.id = 'wifi5_b_g'; guestButton.className = 'btn btn-mini';
    guest.appendChild(guestButton);
    const sidebar = element('div'); sidebar.id = 'subMenu';
    const scheduled = [], listeners = {};
    const document = {readyState, createElement: element,
        createTextNode: text => ({text}), getElementById: id => ids[id] || null};
    const context = {document, window: {location: {pathname: '/' + path},
        setTimeout: fn => scheduled.push(fn),
        addEventListener: (name, fn) => { listeners[name] = fn; }}};
    vm.runInNewContext(source, context);
    if (readyState !== 'complete') {
        assert(!ids['wr-classic-radio-tabs']);
        assert(listeners.load);
        listeners.load();
    }
    assert(!ids['wr-classic-radio-tabs']);
    while (scheduled.length) scheduled.shift()();
    const list = ids['wr-classic-radio-tabs'];
    if (expected) {
        assert(list); assert.strictEqual(list.className, 'nav nav-tabs');
        assert.strictEqual(list.children.length, 3);
        const links = list.children.map(li => li.children[0]);
        assert.deepStrictEqual(links.map(a => a.attributes.href), expected);
        assert.strictEqual(list.children.filter(li => li.className === 'active').length, 1);
        assert.strictEqual(links.filter(a => a.attributes['aria-current'] === 'page')[0].attributes.href, '/' + path);
    } else assert(!list);
    assert.strictEqual(ids.wifi_iot_b.attributes.href, '/Advanced_IoT_Content.asp');
    assert.strictEqual(ids.wifi_iot_b_g.attributes.href, '/Advanced_IoT_Content.asp');
    assert.strictEqual(ids.wifi_iot_b_g.className, 'btn btn-mini' + (path === 'Advanced_IoT_Content.asp' ? ' btn-info' : ''));
    assert.strictEqual(ids['wr-classic-iot-menu'].attributes.href, '/Advanced_IoT_Content.asp');
    assert.strictEqual(button.className, 'btn btn-mini btn-info');
    assert.strictEqual(guestButton.className, 'btn btn-mini');
    const before = host.children.length;
    vm.runInNewContext(source, context);
    while (scheduled.length) scheduled.shift()();
    assert.strictEqual(host.children.length, before);
    assert.strictEqual(banner.children.filter(n => n.id === 'wifi_iot_b').length, 1);
    assert.strictEqual(guest.children.filter(n => n.id === 'wifi_iot_b_g').length, 1);
}
for (const pair of pairs) for (const path of pair)
    check(path, ['/' + pair[0], '/' + pair[1], '/Advanced_IoT_Content.asp']);
check('Advanced_IoT_Content.asp', ['/' + pairs[0][0], '/' + pairs[0][1], '/Advanced_IoT_Content.asp']);
check('index.asp', null);
check('Advanced_Wireless2g_Content.asp', ['/' + pairs[0][0], '/' + pairs[0][1], '/Advanced_IoT_Content.asp'], 'loading');
assert(!/fetch\s*\(|XMLHttpRequest|localStorage|submit\s*\(/.test(source));
console.log('PASS 14 Classic routes plus deferred load: destinations, active tabs, preserved buttons, sidebar and idempotence; no configuration writer');
