"use strict";

const byId = (id) => document.getElementById(id);
const iconSvgs = {
  shield: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M24 5 39 11v12c0 10-6 17-15 21C15 40 9 33 9 23V11z"/><path d="m17 24 5 5 10-11"/></svg>',
  server: '<svg viewBox="0 0 48 48" aria-hidden="true"><rect x="7" y="7" width="34" height="10" rx="3"/><rect x="7" y="20" width="34" height="10" rx="3"/><rect x="7" y="33" width="34" height="9" rx="3"/><path d="M13 12h1m-1 13h1m-1 12h1M20 12h15m-15 13h15m-15 12h15"/></svg>',
  globe: '<svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="19"/><path d="M5 24h38M24 5c7 6 10 12 10 19S31 37 24 43C17 37 14 30 14 24S17 11 24 5Z"/></svg>',
  folder: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M5 13h15l5 5h18v20H5z"/><path d="M5 18h38"/></svg>',
  cloud: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M13 36h23a8 8 0 0 0 1-16 14 14 0 0 0-27-2 9 9 0 0 0 3 18Z"/><path d="M18 27h12m-6-5v12m-4-4 4 4 4-4"/></svg>',
  share: '<svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="10" cy="24" r="5"/><circle cx="37" cy="10" r="5"/><circle cx="37" cy="38" r="5"/><path d="m15 22 17-9M15 26l17 9"/></svg>',
  printer: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M14 17V7h20v10m-20 20h-5V20a4 4 0 0 1 4-4h22a4 4 0 0 1 4 4v17h-5"/><path d="M14 29h20v12H14zM32 22h1"/></svg>',
  file: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M11 5h18l9 9v29H11zM29 5v10h9"/><path d="M17 24h15m-15 7h15m-15 7h11"/></svg>',
  play: '<svg viewBox="0 0 48 48" aria-hidden="true"><rect x="5" y="8" width="38" height="32" rx="4"/><path d="m20 16 14 8-14 8z"/></svg>',
  check: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M24 5 40 11v12c0 10-6 17-16 21C14 40 8 33 8 23V11z"/><path d="m16 24 6 6 11-12"/></svg>',
  cube: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="m24 5 18 10v19L24 44 6 34V15zM6 15l18 10 18-10M24 25v19"/></svg>',
  gear: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="m20 5 8 0 2 6 5 2 5-3 5 6-4 5 1 6 5 4-3 7-7-1-4 4-1 6h-8l-2-6-5-2-5 3-5-6 4-5-1-6-5-4 3-7 7 1 4-4z"/><circle cx="24" cy="24" r="7"/></svg>'
};

function createServiceTile(service) {
  const tile = document.createElement("div");
  tile.className = "service-tile";
  tile.setAttribute("aria-label", `${service.name}: плейсхолдер макета, роботу не підтверджено`);
  const icon = document.createElement("span");
  icon.className = "service-icon";
  icon.setAttribute("aria-hidden", "true");
  icon.innerHTML = iconSvgs[service.icon] || "<svg viewBox=\"0 0 48 48\" aria-hidden=\"true\"><circle cx=\"24\" cy=\"24\" r=\"15\"/></svg>";
  const name = document.createElement("span");
  name.className = "service-name";
  name.textContent = service.name;
  const detail = document.createElement("span");
  detail.className = "service-detail";
  detail.textContent = service.detail;
  tile.append(icon, name, detail);
  return tile;
}

function createWifiCard(network) {
  const card = document.createElement("article");
  card.className = "wifi-card";
  const heading = document.createElement("div");
  heading.className = "wifi-title-row";
  const icon = document.createElement("span");
  icon.className = "wifi-icon";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = "⌁";
  const title = document.createElement("div");
  const h3 = document.createElement("h3");
  h3.textContent = `Бездротова мережа (${network.band})`;
  const state = document.createElement("p");
  state.className = "online";
  state.innerHTML = '<span class="status-dot" aria-hidden="true"></span>';
  state.append(document.createTextNode(network.status + " (макет)"));
  title.append(h3, state);
  heading.append(icon, title);
  const specs = document.createElement("dl");
  specs.className = "wifi-specs";
  const rows = [["SSID:", network.ssid], ["Канал:", network.channel], ["Швидкість:", network.speed], ["Підключено:", `${network.clients} пристрої (макет)`]];
  for (const [label, value] of rows) {
    const dt = document.createElement("dt"); dt.textContent = label;
    const dd = document.createElement("dd"); dd.textContent = value;
    specs.append(dt, dd);
  }
  card.append(heading, specs);
  return card;
}

function setProgress(barId, labelId, value) {
  const safeValue = Math.max(0, Math.min(100, Number(value) || 0));
  byId(barId).style.width = `${safeValue}%`;
  byId(labelId).textContent = `${safeValue}%`;
}

async function loadDemo() {
  const response = await fetch("/api/dashboard.json", { method: "GET", credentials: "omit", cache: "no-store" });
  if (!response.ok) throw new Error(`HTTP ${response.status} loading local demo data`);
  const data = await response.json();
  if (data.demo !== true) throw new Error("Refusing to display unmarked preview data");
  byId("firmware").textContent = `${data.firmware} · DEMO`;
  byId("footer-device").textContent = `${data.device} (Powered by Padavan)`;
  byId("services-grid").replaceChildren(...data.serviceTiles.map(createServiceTile));
  byId("wifi-cards").replaceChildren(...data.wifi.map(createWifiCard));
  byId("device-total").textContent = data.devices.total;
  const breakdown = [["Провідні:", data.devices.wired], ["Wi-Fi 2.4 ГГц:", data.devices.wifi24], ["Wi-Fi 5 ГГц:", data.devices.wifi5]];
  for (const [label, value] of breakdown) {
    const dt = document.createElement("dt"); dt.textContent = label;
    const dd = document.createElement("dd"); dd.textContent = value;
    byId("device-breakdown").append(dt, dd);
  }
  setProgress("cpu-bar", "cpu-label", data.cpuPercent);
  setProgress("memory-bar", "memory-label", data.memoryPercent);
  setProgress("zram-bar", "zram-percent", data.zram.percent);
  byId("zram-used").textContent = data.zram.used;
  byId("zram-compression").textContent = data.zram.compression;
  byId("usb-filesystem").textContent = data.usb.filesystem;
  byId("usb-space").textContent = data.usb.freeTotal;
  const pageByLabel = new Map(data.classicPages.map((page) => [page.label, page.file]));
  for (const button of document.querySelectorAll(".nav-item.unavailable")) {
    button.dataset.file = pageByLabel.get(button.dataset.page) || "";
  }
}

function updateClock() {
  byId("clock").textContent = `${new Date().toLocaleDateString("uk-UA")} ${new Date().toLocaleTimeString("uk-UA", { hour: "2-digit", minute: "2-digit" })} · локальний час`;
}

const dialog = byId("info-dialog");
function openUnavailable(page, file) {
  byId("dialog-title").textContent = `${page} — недоступно у preview`;
  byId("dialog-copy").textContent = "Це наявний розділ Padavan Classic. Для його роботи потрібні роутерний ASP/CGI-обробник; локальний перегляд не підключається до роутера й не імітує цю сторінку.";
  byId("dialog-file").textContent = file || "шлях не підтверджено";
  dialog.showModal();
}

document.querySelectorAll(".nav-item.unavailable").forEach((button) => {
  button.addEventListener("click", () => openUnavailable(button.dataset.page, button.dataset.file));
});
byId("theme-button").addEventListener("click", () => openUnavailable("Padavan Classic", "працює у прошивці; ASP/CGI не запускаються локально"));
byId("close-dialog").addEventListener("click", () => dialog.close());
byId("dialog-ok").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); });
updateClock();
setInterval(updateClock, 30_000);
loadDemo().catch((error) => {
  console.error(error);
  const note = document.createElement("p");
  note.className = "section-note load-error";
  note.setAttribute("role", "alert");
  note.textContent = "Не вдалося завантажити локальні DEMO-дані.";
  document.querySelector(".services-panel").append(note);
});
