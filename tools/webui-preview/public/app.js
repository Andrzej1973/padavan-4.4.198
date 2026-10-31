"use strict";

const byId = (id) => document.getElementById(id);
const pageNames = {
  internet: "Інтернет",
  iot: "Мережа IoT",
  lan: "Локальна мережа",
  vpn: "VPN",
  dns: "DNS і проксі",
  services: "Служби",
  monitoring: "Моніторинг",
  firewall: "Брандмауер",
  qos: "QoS",
  system: "Система",
  log: "Журнал"
};
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
  const tile = document.createElement("button");
  tile.type = "button";
  tile.className = "service-tile";
  tile.setAttribute("aria-label", `${service.name}: відкрити локальний ${dashboardData?.demo ? "DEMO" : "READ-ONLY"}-розділ; Classic ${service.href}; runtime не підтверджено`);
  tile.addEventListener("click", () => {
    let route = "services";
    if (["Stubby", "DoH", "Privoxy", "WPAD / PAC"].includes(service.name)) route = "dns";
    if (["WireGuard", "AmneziaWG", "ZeroTier", "Shadowsocks"].includes(service.name)) route = "vpn";
    location.hash = route;
  });
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

function createOverviewCard(title, status, detail, values, unavailable) {
  const card = document.createElement("article");
  card.className = `overview-card${unavailable ? " unavailable" : ""}`;
  const heading = document.createElement("div");
  heading.className = "overview-title-row";
  const icon = document.createElement("span");
  icon.className = "overview-icon";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = "⌁";
  const titleElement = document.createElement("div");
  const h3 = document.createElement("h3");
  h3.textContent = title;
  const state = document.createElement("p");
  state.className = unavailable ? "offline" : "online";
  state.innerHTML = '<span class="status-dot" aria-hidden="true"></span>';
  state.append(document.createTextNode(status));
  titleElement.append(h3, state);
  heading.append(icon, titleElement);
  card.append(heading);
  if (values && values.length) {
    const specs = document.createElement("dl");
    specs.className = "overview-specs";
    for (const [label, value] of values) {
      const dt = document.createElement("dt"); dt.textContent = label;
      const dd = document.createElement("dd"); dd.textContent = value;
      specs.append(dt, dd);
    }
    card.append(specs);
  } else {
    const note = document.createElement("p");
    note.className = "overview-note";
    note.textContent = detail;
    card.append(note);
  }
  return card;
}

function setProgress(barId, labelId, value) {
  if (value === null || value === undefined || value === "") {
    byId(barId).style.width = "0%";
    byId(labelId).textContent = "Н/Д";
    return;
  }
  const safeValue = Math.max(0, Math.min(100, Number(value) || 0));
  byId(barId).style.width = `${safeValue}%`;
  byId(labelId).textContent = `${safeValue}%`;
}

function renderTelemetry(data) {
  byId("traffic-download").textContent = data.traffic.download ?? "Н/Д";
  byId("traffic-upload").textContent = data.traffic.upload ?? "Н/Д";
  const chart = byId("traffic-chart");
  const width = 620;
  const height = 150;
  const samples = (data.traffic.samples || []).map((value) => Math.max(0, Math.min(100, Number(value) || 0)));
  if (samples.length < 2) {
    const empty = document.createElementNS("http://www.w3.org/2000/svg", "text");
    empty.setAttribute("x", String(width / 2));
    empty.setAttribute("y", String(height / 2));
    empty.setAttribute("text-anchor", "middle");
    empty.classList.add("traffic-empty");
    empty.textContent = "Н/Д";
    chart.replaceChildren(empty);
    byId("process-list").replaceChildren();
    if (!data.processes?.length) {
      const item = document.createElement("li");
      item.textContent = "Н/Д";
      byId("process-list").append(item);
    }
    return;
  }
  const step = width / Math.max(1, samples.length - 1);
  const points = samples.map((value, index) => [index * step, height - 18 - (value / 100) * (height - 30)]);
  const line = points.map(([x, y], index) => `${index ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`).join(" ");
  const area = `${line} L${width},${height} L0,${height} Z`;
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.classList.add("traffic-lines");
  for (let row = 1; row < 5; row += 1) {
    const grid = document.createElementNS("http://www.w3.org/2000/svg", "line");
    grid.setAttribute("x1", "0");
    grid.setAttribute("x2", String(width));
    grid.setAttribute("y1", String((height / 5) * row));
    grid.setAttribute("y2", String((height / 5) * row));
    grid.classList.add("traffic-grid");
    svg.append(grid);
  }
  const areaPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
  areaPath.setAttribute("d", area);
  areaPath.classList.add("traffic-area");
  const linePath = document.createElementNS("http://www.w3.org/2000/svg", "path");
  linePath.setAttribute("d", line);
  linePath.classList.add("traffic-line");
  svg.append(areaPath, linePath);
  chart.replaceChildren(svg);

  const processList = byId("process-list");
  processList.replaceChildren(...(data.processes || []).map((process) => {
    const item = document.createElement("li");
    const name = document.createElement("span");
    name.textContent = process.name;
    const value = document.createElement("b");
    value.textContent = process.cpu;
    const bar = document.createElement("i");
    bar.style.setProperty("--process-load", `${Math.max(2, Math.min(100, Number.parseFloat(process.cpu) || 0))}%`);
    item.append(name, value, bar);
    return item;
  }));
}

function createPageField(field) {
  const row = document.createElement("div");
  row.className = "page-field";
  const label = document.createElement("span");
  label.textContent = field.label;
  const value = document.createElement("b");
  value.textContent = field.value;
  row.append(label, value);
  return row;
}

function createPageService(service) {
  const row = document.createElement("div");
  row.className = "page-service";
  const copy = document.createElement("span");
  const title = document.createElement("b");
  title.textContent = service.name;
  const state = document.createElement("small");
  state.textContent = service.state;
  copy.append(title, state);
  const marker = document.createElement("span");
  marker.className = "service-state";
  marker.textContent = dashboardData?.demo ? "DEMO" : "LIVE";
  row.append(copy, marker);
  return row;
}

let dashboardData = null;

function setActiveNavigation(route) {
  for (const button of document.querySelectorAll(".nav-item[data-route], #wifi-navigation")) {
    const buttonRoute = button.id === "wifi-navigation" ? "wifi" : button.dataset.route;
    const active = route === buttonRoute || (buttonRoute === "wifi" && route.startsWith("wifi"));
    button.classList.toggle("active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  }
}

function renderGenericPage(route) {
  const page = dashboardData?.pages?.[route];
  const mount = byId("modern-page");
  if (!page) return false;
  mount.replaceChildren();
  const panel = document.createElement("section");
  panel.className = "panel modern-page-panel";
  const heading = document.createElement("div");
  heading.className = "panel-heading";
  const title = document.createElement("h1");
  title.textContent = page.title;
  const demo = document.createElement("span");
  demo.className = "demo-chip";
  demo.textContent = dashboardData?.demo ? "DEMO" : "LIVE";
  heading.append(title, demo);
  const description = document.createElement("p");
  description.className = "page-description";
  description.textContent = page.description;
  panel.append(heading, description);

  if (page.fields) {
    const grid = document.createElement("div");
    grid.className = "page-field-grid";
    grid.append(...page.fields.map(createPageField));
    panel.append(grid);
  }
  if (page.services) {
    const grid = document.createElement("div");
    grid.className = "page-service-grid";
    grid.append(...page.services.map(createPageService));
    panel.append(grid);
  }
  if (page.log) {
    const log = document.createElement("pre");
    log.className = "demo-log";
    log.textContent = page.log.join("\n");
    panel.append(log);
  }

  const footer = document.createElement("div");
  footer.className = "page-footer";
  const source = document.createElement("span");
  source.textContent = `Classic: ${page.classic}`;
  const classic = document.createElement("button");
  classic.type = "button";
  classic.className = "secondary-button";
  classic.textContent = "Пояснення Classic";
  classic.addEventListener("click", () => openUnavailable(page.title, page.classic));
  footer.append(source, classic);
  panel.append(footer);
  mount.append(panel);
  return true;
}

function renderRoute() {
  if (!dashboardData) return;
  const route = location.hash.replace(/^#\/?/, "");
  const home = byId("modern-home");
  const wifi = byId("modern-wifi");
  const page = byId("modern-page");
  if (!route || route === "home") {
    page.hidden = true;
    home.hidden = false;
    setActiveNavigation("home");
    return;
  }
  if (route.startsWith("wifi")) {
    page.hidden = true;
    setActiveNavigation(route);
    return;
  }
  if (!renderGenericPage(route)) return;
  home.hidden = true;
  wifi.hidden = true;
  page.hidden = false;
  setActiveNavigation(route);
  page.focus({ preventScroll: true });
  window.scrollTo({ top: 0, behavior: "auto" });
}

async function loadDemo() {
  const response = await fetch("/api/dashboard.json", { method: "GET", credentials: "omit", cache: "no-store" });
  if (!response.ok) throw new Error(`HTTP ${response.status} loading local demo data`);
  const data = await response.json();
  if (typeof data.demo !== "boolean") throw new Error("Refusing to display unmarked Modern data");
  document.body.dataset.mode = data.demo ? "demo" : "live";
  byId("preview-banner-text").textContent = data.demo
    ? "ЛОКАЛЬНЕ DEMO · дані та служби на цій сторінці не є станом роутера"
    : "PADAVAN MODERN · LIVE READ-ONLY · дані зчитано з поточного роутера";
  document.querySelectorAll(".demo-chip").forEach((chip) => {
    chip.textContent = data.demo ? "DEMO" : "LIVE";
  });
  byId("sidebar-note").textContent = data.demo
    ? "Локальний макет усіх погоджених розділів. Дані позначені DEMO; налаштування не передаються роутеру."
    : "Padavan Modern read-only: відображення стану не змінює конфігурацію роутера.";
  document.querySelectorAll(".header-action").forEach((button) => {
    button.title = data.demo ? "Недоступно в локальному DEMO" : "Керування доступне у Padavan Classic";
  });
  byId("firmware").textContent = `${data.firmware}${data.demo ? " · DEMO" : ""}`;
  byId("footer-device").textContent = `${data.device} (Powered by Padavan)`;
  byId("services-grid").replaceChildren(...data.serviceTiles.map(createServiceTile));
  const overview = [
    createOverviewCard("Інтернет", data.internet.status, "", [
      ["Тип:", data.internet.connection], ["IP:", data.internet.ip], ["Час роботи:", data.internet.uptime]
    ], false),
    ...data.wifi.map((network) => createOverviewCard(`Wi-Fi ${network.band}`, network.status + (data.demo ? " (макет)" : ""), "", [
      ["SSID:", network.ssid], ["Канал:", network.channel], ["Клієнти:", `${network.clients}${data.demo ? " (макет)" : ""}`]
    ], false)),
    createOverviewCard("Мережа IoT", data.iot.status, data.iot.detail, [], true)
  ];
  byId("overview-cards").replaceChildren(...overview);
  byId("interfaces-detail").textContent = `${data.interfaces.status} · ${data.interfaces.detail}`;
  byId("uptime-value").textContent = data.uptime;
  byId("device-total").textContent = data.devices.total;
  const breakdown = [["Провідні:", data.devices.wired], ["Wi-Fi 2,4 ГГц:", data.devices.wifi24], ["Wi-Fi 5 ГГц:", data.devices.wifi5]];
  for (const [label, value] of breakdown) {
    const dt = document.createElement("dt"); dt.textContent = label;
    const dd = document.createElement("dd"); dd.textContent = value;
    byId("device-breakdown").append(dt, dd);
  }
  setProgress("cpu-bar", "cpu-label", data.cpuPercent);
  setProgress("memory-bar", "memory-label", data.memoryPercent);
  setProgress("zram-bar", "zram-percent", data.zram.percent);
  byId("temperature-cpu").textContent = data.temperatures.cpu ?? "Н/Д";
  byId("temperature-radio").textContent = data.temperatures.radio5 ?? "Н/Д";
  byId("zram-used").textContent = data.zram.used;
  byId("zram-compression").textContent = data.zram.compression;
  byId("zram-status").textContent = data.zram.status;
  byId("usb-status").textContent = data.usb.status;
  byId("usb-filesystem").textContent = data.usb.filesystem;
  byId("usb-space").textContent = data.usb.freeTotal;
  renderTelemetry(data);
  const pageByLabel = new Map(data.classicPages.map((page) => [page.label, page.file]));
  for (const button of document.querySelectorAll(".nav-item.unavailable")) {
    button.dataset.file = pageByLabel.get(button.dataset.page) || "";
  }
  dashboardData = data;
  renderRoute();
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

document.querySelectorAll(".nav-item[data-route]").forEach((button) => {
  button.addEventListener("click", () => {
    location.hash = button.dataset.route === "home" ? "" : button.dataset.route;
  });
});
window.addEventListener("hashchange", renderRoute);
byId("theme-button").addEventListener("click", () => openUnavailable("Padavan Classic", "працює у прошивці; ASP/CGI не запускаються локально"));
byId("close-dialog").addEventListener("click", () => dialog.close());
byId("dialog-ok").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); });
updateClock();
setInterval(updateClock, 30_000);
byId("modern-page").tabIndex = -1;
loadDemo().catch((error) => {
  console.error(error);
  const note = document.createElement("p");
  note.className = "section-note load-error";
  note.setAttribute("role", "alert");
  note.textContent = "Не вдалося завантажити локальні DEMO-дані.";
  document.querySelector(".services-panel").append(note);
});
