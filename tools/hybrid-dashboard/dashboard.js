"use strict";
let previousCpu = null;
const element = (id) => document.getElementById(id);
const pending = new Set();
async function getStatus(path) {
  if (pending.has(path)) return null;
  pending.add(path);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);
  try {
    const response = await fetch(path, {cache: "no-store", credentials: "same-origin", signal: controller.signal});
    if (!response.ok) throw new Error("HTTP error");
    return await response.text();
  } finally { clearTimeout(timeout); pending.delete(path); }
}
function showUnavailable() {
  ["cpu", "memory", "uptime"].forEach((id) => { element(id).textContent = "Н/Д"; });
  element("status").textContent = "Не вдалося отримати стан роутера";
  previousCpu = null;
}
async function refresh() {
  try {
    const text = await getStatus("/system_status_data.asp");
    if (text === null) return;
    const match = /^\s*var\s+si_new\s*=\s*(\{[\s\S]*\})\s*;\s*$/.exec(text);
    if (!match) throw new Error("Unexpected response");
    const data = JSON.parse(match[1]);
    const cpu = data.cpu, ram = data.ram, uptime = data.uptime;
    if (![cpu?.busy, cpu?.total, ram?.used, ram?.total, uptime?.days, uptime?.hours, uptime?.minutes].every(Number.isFinite) || ram.total <= 0 || ram.used < 0 || ram.used > ram.total) throw new Error("Invalid data");
    const total = previousCpu && cpu.total - previousCpu.total;
    const busy = previousCpu && cpu.busy - previousCpu.busy;
    element("cpu").textContent = total > 0 && busy >= 0 && busy <= total ? `${Math.round(100 * busy / total)}%` : "—";
    previousCpu = {busy: cpu.busy, total: cpu.total};
    element("memory").textContent = `${Math.round(100 * ram.used / ram.total)}%`;
    element("uptime").textContent = `${uptime.days} д ${uptime.hours} год ${uptime.minutes} хв`;
    element("status").textContent = "Системні показники оновлено";
  } catch (_) { showUnavailable(); }
}
refresh();
setInterval(refresh, 10000);

async function refreshWan() {
  try {
    const text = await getStatus("/status_wanlink.asp");
    if (text === null) return;
    const match = /(?:^|\n)\s*function\s+wanlink_status\(\)\s*\{\s*return\s+(\d+);\s*\}/.exec(text);
    if (!match) throw new Error("Unexpected response");
    const code = Number(match[1]);
    element("wan").textContent = code === 0 ? "Підключено" : code <= 9 ? "Немає підключення" : "Н/Д";
  } catch (_) { element("wan").textContent = "Н/Д"; }
}
refreshWan();
setInterval(refreshWan, 10000);

async function refreshLan() {
  try {
    const text = await getStatus("/status_lanlink.asp");
    if (text === null) return;
    const block = /function\s+ether_link_status\(idx\)\s*\{([\s\S]*?)\}/.exec(text);
    if (!block) throw new Error("Unexpected response");
    const ports = [...block[1].matchAll(/if\(idx==(\d+)\)\s*return\s*'([^']*)';/g)]
      .filter((match) => Number(match[1]) > 0);
    if (!ports.length || new Set(ports.map((match) => match[1])).size !== ports.length) throw new Error("Invalid LAN ports");
    if (ports.some((match) => !/^(?:No Link|(?:10|100|1000) Mbps, (?:Half Duplex|Full Duplex, FC (?:TX\/RX|TX Asy|RX Asy|OFF))(?:, EEE)?)$/.test(match[2]))) throw new Error("Unknown port status");
    const active = ports.filter((match) => match[2] !== "No Link").length;
    element("lan").textContent = `${active} з ${ports.length} портів підключено`;
  } catch (_) { element("lan").textContent = "Н/Д"; }
}
refreshLan();
setInterval(refreshLan, 10000);
