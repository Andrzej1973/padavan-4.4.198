#!/usr/bin/env python3
"""Make the inherited Shadowsocks client process badge truthful."""
import argparse
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
args = parser.parse_args()
root = args.source / "trunk/user"
page = root / "www/n56u_ribbon_fixed/Shadowsocks.asp"
html = page.read_text(encoding="utf-8")
backend = root / "httpd/web_ex.c"
c = backend.read_text(encoding="utf-8")
status_anchor = "static int shadowsocks_status_hook(int eid, webs_t wp, int argc, char **argv)\n"
entry_anchor = '\t{ "shadowsocks_status", shadowsocks_status_hook},\n'
entry_add = '\t{ "wr_ss_client_process_state", ej_wr_ss_client_process_state},\n'
array_anchor = "struct ej_handler ej_handlers[] =\n"
if (c.count(status_anchor) != 1 or c.count(array_anchor) != 1 or
        c.count(entry_anchor) != 1 or "ej_wr_ss_client_process_state" in c):
    raise SystemExit("Shadowsocks HTTP handler anchors changed")
handler = r'''/* Exact Shadowsocks process observation; this does not verify traffic. */
static int ej_wr_ss_client_process_state(int eid, webs_t wp, int argc, char **argv)
{
 const char *process, *configured; int requested, active;
 (void)eid;
 if (argc != 1 || !argv || !argv[0]) return websWrite(wp, "3");
 if (!strcmp(argv[0], "redir")) {
  process = "ss-redir"; requested = nvram_get_int("ss_enable");
  if (requested != 0 && requested != 1) return websWrite(wp, "3");
 } else if (!strcmp(argv[0], "local")) {
  process = "ss-local"; configured = nvram_safe_get("socks5_enable");
  requested = configured && *configured && strcmp(configured, "nil") != 0;
 } else return websWrite(wp, "3");
 if (access("/proc/self/stat", R_OK)) return websWrite(wp, "3");
 active = pids((char *)process);
 if (active < 0) return websWrite(wp, "3");
 active = active > 0;
 return websWrite(wp, "%d", active ? (requested ? 1 : 4) : (requested ? 2 : 0));
}
'''
c = c.replace(status_anchor, handler + "\n" + status_anchor, 1)
c = c.replace(entry_anchor, entry_anchor + entry_add, 1)

init_call = "\t\t\tfill_ss_status(shadowsocks_status());"
if html.count(init_call) != 1 or "wrSSProcessRender" in html:
    raise SystemExit("Shadowsocks process-status page anchors changed")
html = html.replace(init_call, "\t\t\tfill_ss_external_status();\n\t\t\twrSSProcessRender('redir', <% wr_ss_client_process_state(\"redir\"); %>);\n\t\t\twrSSProcessRender('local', <% wr_ss_client_process_state(\"local\"); %>);\n\t\t\twindow.setInterval(wrSSProcessRefreshAll, 30000);", 1)

start = "\t\tfunction fill_ss_status(status_code) {"
end = "\t\tfunction fill_dns2tcp_status(status_code) {"
if html.count(start) != 1 or html.count(end) != 1:
    raise SystemExit("Shadowsocks status function anchors changed")
begin = html.index(start)
finish = html.index(end, begin)
old = html[begin:finish]
if "WRSSProcessUnknown" in old:
    raise SystemExit("Shadowsocks process status already prepared")
if '$("ss_status").innerHTML' not in old:
    raise SystemExit("Shadowsocks status function body changed")
new = '''\t\tfunction wrSSProcessRender(kind, state) {
\t\t\tvar id = kind === 'redir' ? 'wr_ss_redir_state' : 'wr_ss_local_state';
\t\t\tvar timeId = kind === 'redir' ? 'wr_ss_redir_time' : 'wr_ss_local_time';
\t\t\tvar labels = ["<#WRSSOff#>", "<#WRSSPresent#>", "<#WRSSMissing#>", "<#WRSSUnknown#>", "<#WRSSStillPresent#>"];
\t\t\tvar valid = typeof state === 'number' && Math.floor(state) === state && state >= 0 && state < labels.length;
\t\t\tvar active = valid && state === 1;
\t\t\tvar node = document.getElementById(id);
\t\t\tif (!node) return;
\t\t\tnode.textContent = valid ? labels[state] : labels[3];
\t\t\tnode.className = 'label label-' + (active ? 'success' : 'warning');
\t\t\twrSSProcessSampledAt[kind] = valid ? Date.now() : 0;
\t\t\tif (valid) {
\t\t\t\tvar observed = document.getElementById(timeId);
\t\t\t\tif (observed) observed.textContent = '<#WRSSObservedAt#> ' + new Date().toLocaleTimeString();
\t\t\t\tvar generation = ++wrSSProcessGeneration[kind];
\t\t\t\twindow.setTimeout(function() {
\t\t\t\t\tif (generation === wrSSProcessGeneration[kind]) wrSSProcessRender(kind, null);
\t\t\t\t}, 45000);
\t\t\t}
\t\t}
\t\tvar wrSSProcessBusy = {redir:false, local:false};
\t\tvar wrSSProcessGeneration = {redir:0, local:0};
\t\tvar wrSSProcessSampledAt = {redir:0, local:0};
\t\tfunction wrSSProcessRefresh(kind) {
\t\t\tif (wrSSProcessBusy[kind] || document.hidden) return;
\t\t\twrSSProcessBusy[kind] = true;
\t\t\t$j.ajax({url:'/update.cgi', data:{output:'wr_ss_client_process_state',arg0:kind}, dataType:'json', cache:false, timeout:5000})
\t\t\t\t.done(function(state) { wrSSProcessRender(kind, state); })
\t\t\t\t.fail(function() { wrSSProcessRender(kind, null); })
\t\t\t\t.always(function() { wrSSProcessBusy[kind] = false; });
\t\t}
\t\tfunction wrSSProcessRefreshAll() {
\t\t\twrSSProcessRefresh('redir'); wrSSProcessRefresh('local');
\t\t}
\t\tdocument.addEventListener('visibilitychange', function() {
\t\t\tif (document.hidden) return;
\t\t\tvar now = Date.now();
\t\t\t['redir','local'].forEach(function(kind) {
\t\t\t\tif (wrSSProcessSampledAt[kind] && now - wrSSProcessSampledAt[kind] >= 45000) wrSSProcessRender(kind, null);
\t\t\t});
\t\t});
\t\tfunction fill_ss_external_status() {
\t\t\t$("domestic_ip").innerHTML = '<iframe src="http://ip.3322.net" height="30" scrolling="no" frameborder="0" marginheight="0" marginwidth="0"></iframe>';
\t\t\t$("foreign_ip").innerHTML = '<iframe src="https://ifconfig.me/ip" height="30" scrolling="no" frameborder="0" marginheight="0" marginwidth="0"></iframe>';
\t\t\t$("gg_status").innerHTML = '<span><img alt="无法访问" src="https://www.google.com/favicon.ico?' + new Date().getTime() + '" /></span>';
\t\t}
'''
html = html[:begin] + new + html[finish:]
row = re.compile(r'(?m)^(?P<indent>\t+)\t*<th width="50%"><#Client#> <#running_status#>：</th>\r?\n(?P=indent)\t*<td id="ss_status"></td>\r?\n(?P=indent)\t*</tr>')
matches = list(row.finditer(html))
if len(matches) != 1:
    raise SystemExit("Shadowsocks status table row anchor changed")
indent = matches[0].group("indent")
rows = (indent + '\t<th width="50%"><#WRSSRedirTitle#></th>\n' + indent +
        '\t<td><span id="wr_ss_redir_state" class="label label-warning" role="status"><#WRSSUnknown#></span> ' +
        '<button type="button" class="btn" onclick="wrSSProcessRefresh(\'redir\')"><#WRSSRefresh#></button> ' +
        '<small id="wr_ss_redir_time"><#WRSSNoObservation#></small></td>\n' + indent + '</tr>\n' +
        indent + '<tr><th width="50%"><#WRSSLocalTitle#></th>\n' + indent +
        '\t<td><span id="wr_ss_local_state" class="label label-warning" role="status"><#WRSSUnknown#></span> ' +
        '<button type="button" class="btn" onclick="wrSSProcessRefresh(\'local\')"><#WRSSRefresh#></button> ' +
        '<small id="wr_ss_local_time"><#WRSSNoObservation#></small></td>\n' + indent + '</tr>\n' +
        indent + '<tr><td colspan="2"><small><#WRSSProcessNote#></small></td></tr>')
html = row.sub(lambda _: rows, html, count=1)

translations = {
    "EN.footer": {
        "WRSSRedirTitle": "Transparent Shadowsocks client (ss-redir)",
        "WRSSLocalTitle": "Local SOCKS5 client (ss-local)",
        "WRSSOff": "Disabled; process not found",
        "WRSSPresent": "Enabled; process present",
        "WRSSMissing": "Enabled; process not found",
        "WRSSUnknown": "State unknown",
        "WRSSStillPresent": "Disabled; process still present",
        "WRSSRefresh": "Refresh",
        "WRSSObservedAt": "Observed:",
        "WRSSNoObservation": "No observation",
        "WRSSProcessNote": "The page compares the saved setting with the exact ss-redir or ss-local process. A running process does not verify server reachability, DNS or client traffic. Refresh manually or every 30 seconds while visible; observations expire after 45 seconds.",
    },
    "UK.dict": {
        "WRSSRedirTitle": "Прозорий клієнт Shadowsocks (ss-redir)",
        "WRSSLocalTitle": "Локальний клієнт SOCKS5 (ss-local)",
        "WRSSOff": "Вимкнено; процесу не знайдено",
        "WRSSPresent": "Увімкнено; процес працює",
        "WRSSMissing": "Увімкнено; процесу не знайдено",
        "WRSSUnknown": "Стан невідомий",
        "WRSSStillPresent": "Вимкнено; процес досі працює",
        "WRSSRefresh": "Оновити",
        "WRSSObservedAt": "Спостережено:",
        "WRSSNoObservation": "Немає спостереження",
        "WRSSProcessNote": "Сторінка порівнює збережене налаштування з точним процесом ss-redir або ss-local. Наявність процесу не підтверджує доступність сервера, DNS чи трафік клієнта. Ручне оновлення або кожні 30 секунд, поки сторінка відкрита; спостереження застаріває через 45 секунд.",
    },
    "RU.dict": {
        "WRSSRedirTitle": "Прозрачный клиент Shadowsocks (ss-redir)",
        "WRSSLocalTitle": "Локальный клиент SOCKS5 (ss-local)",
        "WRSSOff": "Выключено; процесс не найден",
        "WRSSPresent": "Включено; процесс запущен",
        "WRSSMissing": "Включено; процесс не найден",
        "WRSSUnknown": "Состояние неизвестно",
        "WRSSStillPresent": "Выключено; процесс всё ещё работает",
        "WRSSRefresh": "Обновить",
        "WRSSObservedAt": "Наблюдение:",
        "WRSSNoObservation": "Нет наблюдения",
        "WRSSProcessNote": "Страница сравнивает сохранённую настройку с точным процессом ss-redir или ss-local. Наличие процесса не подтверждает доступность сервера, DNS или трафик клиента. Ручное обновление либо раз в 30 секунд, пока страница видна; наблюдение устаревает через 45 секунд.",
    },
}
for filename, values in translations.items():
    path = root / "www/dict" / filename
    text = path.read_text(encoding="utf-8")
    if "WRSSProcessPresent=" in text:
        raise SystemExit(f"Shadowsocks process labels already exist in {filename}")
    text = text.rstrip("\n") + "\n" + "\n".join(
        f"{key}={value}" for key, value in values.items()) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")

page.write_text(html, encoding="utf-8", newline="\n")
backend.write_text(c, encoding="utf-8", newline="\n")
print("Prepared truthful Shadowsocks process badge; proxy functionality remains unverified")
