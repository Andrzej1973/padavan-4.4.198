/* EoIP observations only. Labels must describe administrative interface state,
 * never peer reachability. No timers or automatic polling are installed here. */
(function (root, factory) {
    'use strict';
    if (typeof module === 'object' && module.exports) module.exports = factory();
    else root.WREoIPStatus = factory();
}(typeof window !== 'undefined' ? window : this, function () {
    'use strict';
    function integer(value, minimum, maximum) {
        return typeof value === 'number' && isFinite(value) &&
            Math.floor(value) === value && value >= minimum && value <= maximum;
    }
    function parse(reply) {
        var rows = [], seen = {}, i, row, owned;
        if (!reply || reply.schema !== 1 || !Array.isArray(reply.slots) || reply.slots.length !== 8) return null;
        if (Object.prototype.hasOwnProperty.call(reply, 'sample_age') && !integer(reply.sample_age, 0, 60)) return null;
        for (i = 0; i < reply.slots.length; i++) {
            row = reply.slots[i];
            if (!row || !integer(row.slot, 0, 7) || seen[row.slot] ||
                ['absent', 'unknown', 'foreign', 'up', 'down'].indexOf(row.state) < 0) return null;
            seen[row.slot] = true;
            owned = row.state === 'up' || row.state === 'down';
            if (owned && (!integer(row.ifindex, 1, 2147483647) ||
                !integer(row.mtu, 68, 65535) || !integer(row.master, 0, 2147483647))) return null;
            rows.push(owned ? {slot: row.slot, state: row.state, ifindex: row.ifindex,
                mtu: row.mtu, master: row.master} : {slot: row.slot, state: row.state});
        }
        rows.sort(function (a, b) { return a.slot - b.slot; });
        return rows;
    }
    function render(target, rows, labels) {
        var doc = target.ownerDocument, table, head, body, i;
        target.textContent = '';
        if (!rows) { target.textContent = labels.unknown; return; }
        table = doc.createElement('table');
        table.className = 'table table-striped';
        function appendRow(parent, values, tag) {
            var tr = doc.createElement('tr');
            values.forEach(function (value) {
                var cell = doc.createElement(tag);
                cell.textContent = String(value);
                tr.appendChild(cell);
            });
            parent.appendChild(tr);
        }
        head = doc.createElement('thead');
        appendRow(head, [labels.slot, labels.state, labels.index, 'MTU', labels.master], 'th');
        table.appendChild(head);
        body = doc.createElement('tbody');
        for (i = 0; i < rows.length; i++) {
            var row = rows[i], owned = row.state === 'up' || row.state === 'down';
            appendRow(body, [row.slot, labels[row.state], owned ? row.ifindex : '-',
                owned ? row.mtu : '-', owned ? row.master : '-'], 'td');
        }
        table.appendChild(body);
        target.appendChild(table);
    }
    function refresher(load, display) {
        var busy = false;
        return function () {
            if (busy) return Promise.resolve(false);
            busy = true;
            return Promise.resolve().then(function () {
                display(null); /* Never leave old 'up' visible during a failed refresh. */
                return load();
            }).then(function (reply) {
                var rows = parse(reply);
                display(rows);
                return rows !== null;
            }, function () {
                display(null);
                return false;
            }).then(function (ok) { busy = false; return ok; }, function (error) {
                busy = false;
                throw error;
            });
        };
    }
    return {parse: parse, render: render, refresher: refresher};
}));
