#!/usr/bin/env python3
"""Show Privoxy requested state separately from observed process presence."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
args = parser.parse_args()
root = args.source / "trunk/user"
backend = root / "httpd/web_ex.c"
text = backend.read_text(encoding="utf-8")
array_anchor = "struct ej_handler ej_handlers[] =\n"
system_entry = '\t{ "json_system_status", ej_system_status_hook},\n'
if (text.count(array_anchor) != 1 or text.count(system_entry) != 1 or
        "ej_wr_privoxy_process_state" in text):
    raise SystemExit("Privoxy process-status HTTP hook anchors changed")
handler = r'''
static int wr_process_present(const char *name);
/* Process observation only; it does not prove a listener or proxy traffic. */
static int ej_wr_privoxy_process_state(int eid, webs_t wp, int argc, char **argv)
{
 int requested, active;
 (void)eid; (void)argv;
 if (argc != 0) return websWrite(wp, "3");
 if (access("/proc/self/stat", R_OK)) return websWrite(wp, "3");
#if defined(APP_PRIVOXY)
 requested = nvram_get_int("privoxy_enable") > 0;
 active = wr_process_present("privoxy");
 if (active < 0) return websWrite(wp, "3");
 active = active > 0;
 return websWrite(wp, "%d", active ? (requested ? 1 : 4) : (requested ? 2 : 0));
#else
 requested = 0; active = 0;
 (void)requested; (void)active;
 return websWrite(wp, "3");
#endif
}
'''
text = text.replace(array_anchor, handler + "\n" + array_anchor, 1)
text = text.replace(system_entry, system_entry + '\t{ "wr_privoxy_process_state", ej_wr_privoxy_process_state},\n', 1)

page = root / "www/n56u_ribbon_fixed/Advanced_Services_Privoxy.asp"
html = page.read_text(encoding="utf-8")
switch_row = '<tr id="row_privoxy">'
status_row = '''<tr id="wr_privoxy_status_row">
                                            <th><#WRPrivoxyObservedTitle#></th>
                                            <td><strong id="wr_privoxy_process_status" role="status"><#WRPrivoxyUnknown#></strong>
                                                <button type="button" class="btn" onclick="wrPrivoxyRefresh()"><#WRPrivoxyRefresh#></button>
                                                <small id="wr_privoxy_observed_at"><#WRPrivoxyNoObservation#></small>
                                                <p class="help-block"><#WRPrivoxyObservedNote#></p></td>
                                        </tr>

'''
initial = "    change_privoxy_enabled();\n}"
after_switch = '</tr>\n                                        <tr id="row_privoxy_conf"'
if (html.count(switch_row) != 1 or html.count(after_switch) != 1 or
        html.count(initial) != 1 or 'id="wr_privoxy_process_status"' in html):
    raise SystemExit("Privoxy status page anchors changed")
js = r'''
var wrPrivoxyStatusBusy = false;
var wrPrivoxyGeneration = 0, wrPrivoxySampledAt = 0;
function wrPrivoxyRender(state) {
    var generation = ++wrPrivoxyGeneration;
    wrPrivoxySampledAt = 0;
    var labels = ["<#WRPrivoxyOff#>", "<#WRPrivoxyPresent#>", "<#WRPrivoxyMissing#>", "<#WRPrivoxyUnknown#>", "<#WRPrivoxyStillPresent#>"];
    var classes = ['text-muted', 'text-info', 'text-error', 'text-warning', 'text-warning'];
    var element = document.getElementById('wr_privoxy_process_status');
    if (!element) return;
    var valid = typeof state === 'number' && Math.floor(state) === state && state >= 0 && state < labels.length;
    element.textContent = valid ? labels[state] : labels[3];
    element.className = valid ? classes[state] : classes[3];
    if (valid && state !== 3) {
        wrPrivoxySampledAt = Date.now();
        window.setTimeout(function() {
            if (generation === wrPrivoxyGeneration) wrPrivoxyRender(null);
        }, 45000);
        var observedAt = document.getElementById('wr_privoxy_observed_at');
        if (observedAt) observedAt.textContent = '<#WRPrivoxyLastObservation#> ' + new Date().toLocaleTimeString();
    }
}
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && wrPrivoxySampledAt && Date.now() - wrPrivoxySampledAt >= 45000) wrPrivoxyRender(null);
});
function wrPrivoxyRefresh() {
    if (wrPrivoxyStatusBusy || document.hidden || !found_app_privoxy()) return;
    wrPrivoxyStatusBusy = true;
    $j.ajax({url:'/update.cgi', data:{output:'wr_privoxy_process_state'}, dataType:'json', cache:false, timeout:5000})
        .done(function(state) { wrPrivoxyRender(state); })
        .fail(function() { wrPrivoxyRender(null); })
        .always(function() { wrPrivoxyStatusBusy = false; });
}
'''
html = html.replace(initial, "    change_privoxy_enabled();\n    if (found_app_privoxy()) {\n        wrPrivoxyRender(<% wr_privoxy_process_state(); %>);\n        window.setInterval(wrPrivoxyRefresh, 30000);\n    }\n}", 1)
script_anchor = "function change_privoxy_enabled() {"
if html.count(script_anchor) != 1:
    raise SystemExit("Privoxy status script insertion point changed")
html = html.replace(script_anchor, js + "\n" + script_anchor, 1)
html = html.replace(after_switch, '</tr>\n' + status_row + '                                        <tr id="row_privoxy_conf"', 1)

translations = {
    "EN.footer": {
        "WRPrivoxyObservedTitle": "Observed process state",
        "WRPrivoxyOff": "Disabled; process not found",
        "WRPrivoxyPresent": "Enabled; process present (proxy traffic not verified)",
        "WRPrivoxyMissing": "Enabled; process not found",
        "WRPrivoxyUnknown": "Process state unknown",
        "WRPrivoxyStillPresent": "Disabled; process still present",
        "WRPrivoxyRefresh": "Refresh status",
        "WRPrivoxyLastObservation": "Last process observation:",
        "WRPrivoxyNoObservation": "No confirmed process observation yet",
        "WRPrivoxyObservedNote": "Shows the saved enable setting and whether a Privoxy process is present. It does not verify the listening socket, client proxy settings or traffic. Refreshes every 30 seconds while this page is visible.",
    },
    "UK.dict": {
        "WRPrivoxyObservedTitle": "Спостережений стан процесу",
        "WRPrivoxyOff": "Вимкнено; процесу не знайдено",
        "WRPrivoxyPresent": "Увімкнено; процес є (трафік проксі не перевірено)",
        "WRPrivoxyMissing": "Увімкнено; процесу не знайдено",
        "WRPrivoxyUnknown": "Стан процесу невідомий",
        "WRPrivoxyStillPresent": "Вимкнено; процес досі працює",
        "WRPrivoxyRefresh": "Оновити стан",
        "WRPrivoxyLastObservation": "Останнє спостереження процесу:",
        "WRPrivoxyNoObservation": "Підтвердженого спостереження процесу ще немає",
        "WRPrivoxyObservedNote": "Показує збережене налаштування та наявність процесу Privoxy. Сокет прослуховування, налаштування клієнтів і проксі-трафік цим не перевіряються. Оновлення кожні 30 секунд, поки сторінка відкрита.",
    },
    "RU.dict": {
        "WRPrivoxyObservedTitle": "Наблюдаемое состояние процесса",
        "WRPrivoxyOff": "Выключено; процесс не найден",
        "WRPrivoxyPresent": "Включено; процесс есть (прокси-трафик не проверен)",
        "WRPrivoxyMissing": "Включено; процесс не найден",
        "WRPrivoxyUnknown": "Состояние процесса неизвестно",
        "WRPrivoxyStillPresent": "Выключено; процесс всё ещё работает",
        "WRPrivoxyRefresh": "Обновить состояние",
        "WRPrivoxyLastObservation": "Последнее наблюдение процесса:",
        "WRPrivoxyNoObservation": "Подтверждённого наблюдения процесса пока нет",
        "WRPrivoxyObservedNote": "Показывает сохранённую настройку и наличие процесса Privoxy. Сокет прослушивания, настройки клиентов и прокси-трафик этим не проверяются. Обновление каждые 30 секунд, пока страница открыта.",
    },
}
for filename, values in translations.items():
    path = root / "www/dict" / filename
    content = path.read_text(encoding="utf-8")
    if "WRPrivoxyUnknown=" in content:
        raise SystemExit(f"Privoxy status labels already exist in {filename}")
    content = content.rstrip("\n") + "\n" + "\n".join(f"{key}={value}" for key, value in values.items()) + "\n"
    path.write_text(content, encoding="utf-8", newline="\n")

backend.write_text(text, encoding="utf-8", newline="\n")
page.write_text(html, encoding="utf-8", newline="\n")
print("Prepared Privoxy requested/observed process status; listener and traffic remain unverified")
