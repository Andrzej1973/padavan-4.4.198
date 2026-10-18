const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync(require('node:path').join(__dirname, 'web/vpn-profiles-page.html'), 'utf8')
 .match(/<script[^>]*>([\s\S]*?)<\/script>/)[1].replace(/<%[\s\S]*?%>/g, '""');
const elements = {}, requests = [];
function element(id) {
 return elements[id] ||= {value: '', textContent: '', disabled: false, style: {}, getAttribute: key => key};
}
const context = {document: {getElementById: element}, confirm: () => true,
 jQuery: Object.assign(() => {}, {ajax: request => requests.push(request)})};
vm.createContext(context);vm.runInContext(source, context);
context.wrVPNToken = '0123456789abcdef0123456789abcdef';
context.wrVPNEdit(2, '9007199254740993');
assert.equal(requests[0].url, '/wr_vpn_export.cgi');
context.wrVPNEditCancel();requests[0].success({config: 'late private config'});
assert.equal(element('wr_vpn_edit_config').value, '');
context.wrVPNEdit(2, '9007199254740993');requests[1].success({config: 'private config'});
assert.equal(element('wr_vpn_edit_config').value, 'private config');
context.wrVPNEditSave();context.wrVPNEditSave();
assert.equal(requests.length, 3);
assert.equal(requests[2].url, '/wr_vpn_edit.cgi');
assert.equal(requests[2].data, context.wrVPNToken + '\n2\n9007199254740993\nprivate config');
context.wrVPNEditCancel();assert.equal(element('wr_vpn_edit_config').value, 'private config');
requests[2].error();
assert.equal(element('wr_vpn_edit_save').disabled, true);
assert.equal(element('wr_vpn_edit_config').value, 'private config');
context.wrVPNEditSave();assert.equal(requests.length, 3);
context.wrVPNEditCancel();assert.equal(element('wr_vpn_edit_config').value, '');
context.wrVPNEdit(2, '2');requests[3].success({config: 'replacement'});
context.wrVPNEditSave();requests[4].success({saved: true, started: false});
assert.equal(element('wr_vpn_edit_config').value, '');
assert.equal(context.wrVPNEditing, null);
assert.equal(requests.length, 5);
console.log('PASS editor: exact revision string, explicit export, late-response rejection, single save, uncertain-write retry gate and private text clearing');
