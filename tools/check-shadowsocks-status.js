#!/usr/bin/env node
"use strict";

const fs = require("fs");
const vm = require("vm");

const file = process.argv[2];
if (!file) throw new Error("usage: node check-shadowsocks-status.js prepared-Shadowsocks.asp");
const page = fs.readFileSync(file, "utf8");
const start = page.indexOf("function wrSSProcessRender(kind, state)");
const end = page.indexOf("var wrSSProcessBusy", start);
if (start < 0 || end < 0) throw new Error("status renderer not found in prepared page");
const source = page.slice(start, end).replace(/<#(WRSS(?:Off|Present|Missing|Unknown|StillPresent|ObservedAt))#>/g,
  (_, key) => key);
const elements = {
  wr_ss_redir_state: {textContent: "", className: ""},
  wr_ss_local_state: {textContent: "", className: ""},
  wr_ss_redir_time: {textContent: ""},
  wr_ss_local_time: {textContent: ""},
};
const timers = [];
const context = {
  document: {getElementById: (id) => elements[id] || null},
  window: {setTimeout: (fn, ms) => { timers.push({fn, ms}); }},
  wrSSProcessGeneration: {redir: 0, local: 0},
  wrSSProcessSampledAt: {redir: 0, local: 0},
  Date,
  Math,
};
vm.createContext(context);
vm.runInContext(source, context, {timeout: 1000});

const cases = [
  [0, "WRSSOff", "label-warning"],
  [1, "WRSSPresent", "label-success"],
  [2, "WRSSMissing", "label-warning"],
  [3, "WRSSUnknown", "label-warning"],
  [4, "WRSSStillPresent", "label-warning"],
  [-1, "WRSSUnknown", "label-warning"],
  [1.5, "WRSSUnknown", "label-warning"],
  [null, "WRSSUnknown", "label-warning"],
  ["1", "WRSSUnknown", "label-warning"],
];
for (const [state, label, color] of cases) {
  context.wrSSProcessRender("redir", state);
  if (elements.wr_ss_redir_state.textContent !== label ||
      !elements.wr_ss_redir_state.className.endsWith(color)) {
    throw new Error(`wrong rendering for state ${String(state)}: ${JSON.stringify(elements.wr_ss_redir_state)}`);
  }
}
if (!timers.length || timers.some((timer) => timer.ms !== 45000)) {
  throw new Error("valid states must expire after 45 seconds");
}
console.log("PASS Shadowsocks status UI states, fail-closed colors and expiry");
