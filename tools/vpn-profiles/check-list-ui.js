const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync(require('node:path').join(__dirname, 'web/vpn-profiles-page.html'), 'utf8')
 .match(/<script[^>]*>([\s\S]*?)<\/script>/)[1].replace(/<%[\s\S]*?%>/g, '""');
const markup = (page, total) => `<tr data-page="${page}" data-total="${total}"></tr>`;
let html = markup(0, 25);
const props = {}, texts = {}, requests = [], alerts = [];
const context = {document: {getElementById: () => ({getAttribute: key => key})},
 alert: text => alerts.push(text),
 jQuery: Object.assign(function(selector) {
  if (typeof selector === 'function') return;
  return {html: value => {if (value === undefined) return html;html = value;},
   attr: key => {const m = html.match(new RegExp(key + '="([^"]+)"'));return m && m[1];},
   prop: (name, value) => {props[selector + ':' + name] = value;},
   text: value => {texts[selector] = value;}};
 }, {ajax: request => requests.push(request)})};
vm.createContext(context); vm.runInContext(source, context);
assert.equal(context.wrVPNListControls(), true);
assert.equal(props['#wr_vpn_previous:disabled'], true);
assert.equal(props['#wr_vpn_next:disabled'], false);
context.wrVPNListLoad(1);context.wrVPNListLoad(2);
assert.equal(requests.length, 1);
assert.equal(requests[0].data.output, 'wr_vpn_profile_rows');
assert.equal(requests[0].data.arg0, 1);assert.equal(requests[0].dataType, 'html');
requests[0].success(markup(1, 25));
assert.equal(context.wrVPNListPage, 1);assert.equal(texts['#wr_vpn_page_number'], '2');
assert.equal(props['#wr_vpn_previous:disabled'], false);
context.wrVPNListLoad(2);requests[1].success(markup(2, 25));
assert.equal(props['#wr_vpn_next:disabled'], true);
context.wrVPNListLoad(1);requests[2].success('unavailable');
assert.equal(html, markup(2, 25));assert.equal(context.wrVPNListPage, 2);
assert.equal(alerts.length, 1);
context.wrVPNListLoad(1);requests[3].error();
assert.equal(html, markup(2, 25));assert.equal(context.wrVPNListBusy, false);
for (const page of [-1, 100, 1.5]) context.wrVPNListLoad(page);
assert.equal(requests.length, 4);
context.wrVPNListLoad(context.wrVPNListPage);
assert.equal(requests[4].data.arg0, 2);
requests[4].success(markup(2, 25));
assert.equal(props['#wr_vpn_refresh:disabled'], false);
console.log('PASS paged profile UI: navigation, single flight, bounds, failed-response preservation and no automatic polling');
