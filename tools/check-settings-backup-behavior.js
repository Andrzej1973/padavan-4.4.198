#!/usr/bin/env node
// Execute the inherited backup/restore handlers from a built ROMFS page with
// inert browser/HTTP substitutes. No request reaches a router or CGI endpoint.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const pagePath = process.argv[2];
if (!pagePath) throw new Error('usage: node tools/check-settings-backup-behavior.js <ROMFS-page.asp>');
const sources = pagePath === '--stdin' ? JSON.parse(fs.readFileSync(0, 'utf8')) : {
  page: fs.readFileSync(pagePath, 'utf8'),
  state: fs.readFileSync(path.join(path.dirname(pagePath), 'state.js'), 'utf8'),
};
const {page, state} = sources;

function extractFunction(name, source = page) {
  const match = source.match(new RegExp('function\\s+' + name + '\\s*\\([^)]*\\)\\s*\\{[\\s\\S]*?^\\}', 'm'));
  assert(match, 'ROMFS page missing function ' + name);
  return match[0];
}

const calls = [];
const form = {
  productid: {value: 'WR1200JS'},
  action_mode: {value: ''},
  action1: {blur() { calls.push('blur'); }},
  file_nv: {value: 'backup.CFG', focus() { calls.push('focus-nv'); }},
  file_st: {value: 'backup.TBZ', focus() { calls.push('focus-storage'); }},
  submit() { calls.push('submit'); },
};
let confirmation = false;
let loginSafe = false;
let submittedPath = '';
const sandbox = {
  document: {form},
  location: {href: ''},
  lan_ipaddr: '192.168.1.1',
  login_safe: () => loginSafe,
  show_banner() {}, show_menu() {}, show_footer() {}, support_mtd_rwfs: () => false,
  showhide_div(id, visible) { calls.push(['visibility', id, visible]); },
  confirm: () => confirmation,
  alert(message) { calls.push(['alert', message]); },
  showLoading() { calls.push('loading-nv'); },
  showLoadingOne() { calls.push('loading-storage'); },
  set_frm_action_apply(value) { calls.push(['apply', value]); },
  set_frm_action_upload(value) { submittedPath = value; calls.push(['upload', value]); },
  disableCheckChangedStatus() { calls.push('disable-change-check'); },
};
const run = (name) => vm.runInNewContext('(' + extractFunction(name) + ')', sandbox);
sandbox.set_frm_action_apply = (value) => {
  calls.push(['apply', value]);
  run('set_frm_action_apply')(value);
};
sandbox.set_frm_action_upload = (value) => {
  submittedPath = value;
  calls.push(['upload', value]);
  run('set_frm_action_upload')(value);
};

// The safe-session gate hides all privileged controls until login_safe passes.
run('initial')();
assert.equal(calls.length, 0, 'unsafe session revealed backup/restore rows');
loginSafe = true;
run('initial')();
const visibleRows = calls.filter((call) => Array.isArray(call) && call[0] === 'visibility');
assert.equal(visibleRows.length, 8);
assert(visibleRows.every(([, , visible]) => visible === 1));
const expectedRows = ['row_nv_reset', 'row_nv_backup', 'row_nv_restore1', 'row_nv_restore2',
  'row_st_reset', 'row_st_backup', 'row_st_restore1', 'row_st_restore2'];
assert.deepEqual(visibleRows.map((row) => row[1]).sort(), expectedRows.slice().sort());
for (const id of expectedRows) {
  assert(new RegExp('<tr[^>]*id="' + id + '"[^>]*style="display:none"').test(page),
    id + ' must start hidden');
}
calls.length = 0;

// Cancelling either destructive confirmation must not submit a form.
assert.equal(run('restoreNVRAM')(), false);
assert.equal(run('restoreStorage')(), false);
assert(!calls.includes('submit'));
assert(!calls.some((call) => Array.isArray(call) && call[0] === 'apply'));

// Confirmed actions use the existing firmware routes and exact backup names.
confirmation = true;
run('restoreNVRAM')();
assert(calls.includes('loading-nv'));
assert(calls.some((call) => Array.isArray(call) && call[0] === 'apply' && call[1] === ' RestoreNVRAM '));
assert(calls.includes('submit'));
assert.equal(form.action, 'apply.cgi');
assert.equal(form.enctype, 'application/x-www-form-urlencoded');
assert.equal(form.action_mode.value, ' RestoreNVRAM ');
calls.length = 0;
run('restoreStorage')();
assert(calls.includes('loading-storage'));
assert(calls.some((call) => Array.isArray(call) && call[0] === 'apply' && call[1] === ' RestoreStorage '));
assert(calls.includes('submit'));
calls.length = 0;

run('saveSetting')();
assert.equal(sandbox.location.href, 'Settings_WR1200JS.CFG');
assert(calls.some((call) => Array.isArray(call) && call[0] === 'apply' && call[1] === ''));
assert(!calls.includes('submit'));
calls.length = 0;
run('saveStorage')();
assert.equal(sandbox.location.href, 'Storage_WR1200JS.TBZ');
assert(calls.some((call) => Array.isArray(call) && call[0] === 'apply' && call[1] === ''));
assert(!calls.includes('submit'));
calls.length = 0;

// Upload validation and destinations are exercised against the ROMFS code.
sandbox.checkFileName = run('checkFileName');
run('uploadSetting')();
assert.equal(submittedPath, 'restore_nv.cgi');
assert.equal(form.action, 'restore_nv.cgi');
assert.equal(form.enctype, 'multipart/form-data');
assert.equal(form.action_mode.value, '');
assert(calls.includes('disable-change-check'));
assert(calls.includes('submit'));
calls.length = 0;
form.file_st.value = 'wrong.txt';
run('uploadStorage')();
assert(!calls.includes('submit'), 'invalid storage backup extension was submitted');
assert(calls.some((call) => Array.isArray(call) && call[0] === 'alert'));
form.file_st.value = 'backup.TBZ';
calls.length = 0;
run('uploadStorage')();
assert.equal(submittedPath, 'restore_st.cgi');
assert(calls.includes('submit'));

for (const [handler, field, other, extension, route] of [
  ['uploadSetting', 'file_nv', 'file_st', 'CFG', 'restore_nv.cgi'],
  ['uploadStorage', 'file_st', 'file_nv', 'TBZ', 'restore_st.cgi'],
]) {
  for (const [filename, accepted] of [
    ['', false], ['x.' + extension, false], ['backup.txt', false],
    ['backup.' + extension + '.exe', false],
    ['backup.' + extension.toLowerCase(), true],
    ['C:\\fakepath\\backup.' + extension, true],
  ]) {
    calls.length = 0;
    submittedPath = '';
    form[field].value = filename;
    form[other].value = 'another selected file';
    run(handler)();
    assert.equal(calls.includes('submit'), accepted, handler + ': ' + filename);
    assert.equal(form[other].value, '', 'other upload field was not cleared');
    if (accepted) {
      assert.equal(form.action, route);
      assert.equal(form.enctype, 'multipart/form-data');
    } else {
      assert.equal(submittedPath, '');
      assert(calls.some((call) => Array.isArray(call) && call[0] === 'alert'));
    }
  }
}

// Flash-save feedback must reset the actual button on success and errors.
// All Ajax calls remain inert and no timer string is evaluated.
let ajax;
const timers = [];
const buttons = new Map();
function button(id) {
  if (!buttons.has(id)) buttons.set(id, {
    classes: new Set(),
    addClass(value) { this.classes.add(value); return this; },
    removeClass(value) { this.classes.delete(value); return this; },
    val() { return this; },
  });
  return buttons.get(id);
}
const jquery = (selector) => {
  assert(/^#[A-Za-z0-9_]+$/.test(selector), 'invalid button selector: ' + selector);
  return button(selector.slice(1));
};
jquery.ajax = (options) => { ajax = options; };
sandbox.$j = jquery;
sandbox.jQuery = {noConflict: () => jquery};
sandbox.setTimeout = (callback, delay) => {
  assert.equal(typeof callback, 'function', 'flash feedback must not use string timers');
  assert.equal(delay, 1500);
  timers.push(callback);
};
sandbox.reset_btn_commit = vm.runInNewContext('(' + extractFunction('reset_btn_commit', state) + ')', sandbox);
const pageCommit = run('send_commit_action');
const headerCommit = vm.runInNewContext('(' + extractFunction('commit', state) + ')', sandbox);
for (const [id, invoke] of [
  ['commit_nvram', () => pageCommit('commit_nvram', button('commit_nvram'))],
  ['commit_storage', () => pageCommit('commit_storage', button('commit_storage'))],
  ['commit_btn', () => headerCommit()],
]) {
  for (const [kind, response, expectedClass] of [
    ['error', {}, 'alert-error'], ['success', {sys_result: 0}, 'alert-success'],
    ['success', {sys_result: 1}, 'alert-error'], ['success', null, 'alert-error'],
    ['success', {}, 'alert-error'],
    ['success', {sys_result: false}, 'alert-error'],
    ['success', {sys_result: ''}, 'alert-error'],
    ['success', {sys_result: '0'}, 'alert-error'],
  ]) {
    ajax = null;
    invoke();
    assert(ajax);
    assert.equal(ajax.type, 'post');
    assert.equal(ajax.url, '/apply.cgi');
    assert.equal(ajax.data.action_mode, ' CommitFlash ');
    assert.equal(ajax.data.nvram_action, id === 'commit_btn' ? 'commit_nvram' : id);
    ajax[kind](response);
    assert(button(id).classes.has(expectedClass));
    assert.equal(timers.length, 1);
    timers.shift()();
    assert.equal(button(id).classes.size, 0, 'feedback was not cleared for ' + id);
  }
}
ajax = null;
pageCommit('', button('commit_nvram'));
assert.equal(ajax, null);
confirmation = false;
headerCommit();
assert.equal(ajax, null, 'cancelled flash commit sent a request');

console.log('PASS settings backup/restore ROMFS JS: exact safe-session rows, cancel paths, form encoding, downloads, upload routes and flash-save success/error feedback');
