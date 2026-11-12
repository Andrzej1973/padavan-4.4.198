"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const elements = Object.fromEntries(["cpu", "memory", "uptime", "status", "wan", "lan"].map((id) => [id, {textContent: ""}]));
const timers = [];
const responses = [];
let lastSignal;
const context = {AbortController, setTimeout: (fn) => setTimeout(fn, 10), clearTimeout, document: {getElementById: (id) => elements[id]}, setInterval: (fn) => timers.push(fn),
  fetch: async (path, options) => { lastSignal = options.signal; return responses.shift(); }};
const reply = (text, ok = true) => ({ok, text: async () => text});
const state = (busy, total) => `var si_new=${JSON.stringify({cpu: {busy, total}, ram: {used: 25, total: 100}, uptime: {days: 2, hours: 3, minutes: 4}})};`;
responses.push(reply(state(10, 100)), reply("function wanlink_status() { return 0;}"), reply("function ether_link_status(idx){\n if(idx==0) return 'No Link';\n if(idx==1) return '1000 Mbps, Full Duplex, FC TX/RX';\n if(idx==2) return 'No Link';\n return 'No Link';\n}"));
vm.runInNewContext(fs.readFileSync(__dirname + "/dashboard.js", "utf8"), context);
async function flush() { await new Promise((resolve) => setImmediate(resolve)); }
(async () => {
  await flush();
  assert.equal(elements.cpu.textContent, "—");
  assert.equal(elements.memory.textContent, "25%");
  assert.equal(elements.uptime.textContent, "2 д 3 год 4 хв");
  assert.equal(elements.wan.textContent, "Підключено");
  assert.equal(elements.lan.textContent, "1 з 2 портів підключено");
  responses.push(reply(state(60, 200)));
  await timers[0]();
  assert.equal(elements.cpu.textContent, "50%");
  responses.push(reply("var si_new={bad};"));
  await timers[0]();
  assert.equal(elements.memory.textContent, "Н/Д");
  responses.push(reply("function wanlink_status() { return 99;}"));
  await timers[1]();
  assert.equal(elements.wan.textContent, "Н/Д");
  responses.push(reply("", false));
  await timers[1]();
  assert.equal(elements.wan.textContent, "Н/Д");
  let resolveFetch;
  responses.push(new Promise((resolve) => { resolveFetch = resolve; }));
  const first = timers[1]();
  await timers[1]();
  assert.equal(elements.wan.textContent, "Н/Д");
  resolveFetch(reply("function wanlink_status() { return 0;}"));
  await first;
  assert.equal(elements.wan.textContent, "Підключено");
  responses.push(reply("function ether_link_status(idx){ if(idx==1) return 'I/O Error'; }"));
  await timers[2]();
  assert.equal(elements.lan.textContent, "Н/Д");
  responses.push(reply("function ether_link_status(idx){ if(idx==1) return 'No Link'; if(idx==1) return 'No Link'; }"));
  await timers[2]();
  assert.equal(elements.lan.textContent, "Н/Д");
  responses.push(reply("invalid"));
  await timers[2]();
  assert.equal(elements.lan.textContent, "Н/Д");
  let aborted = false;
  responses.push(new Promise((resolve, reject) => {
    const interval = setInterval(() => {
      const signal = lastSignal;
      if (signal && signal.aborted) { clearInterval(interval); aborted = true; reject(new Error("aborted")); }
    }, 1);
  }));
  const timed = timers[1]();
  await timed;
  assert.equal(aborted, true);
  assert.equal(elements.wan.textContent, "Н/Д");
  responses.push({ok: true, text: () => new Promise((resolve, reject) => {
    const interval = setInterval(() => {
      if (lastSignal.aborted) { clearInterval(interval); reject(new Error("body aborted")); }
    }, 1);
  })});
  await timers[1]();
  assert.equal(elements.wan.textContent, "Н/Д");
  responses.push(reply("function wanlink_status() { return 0;}"));
  await timers[1]();
  assert.equal(elements.wan.textContent, "Підключено");
  console.log("PASS hybrid status parsing, CPU deltas, invalid and unavailable responses");
})().catch((error) => { console.error(error); process.exitCode = 1; });
