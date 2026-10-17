#!/usr/bin/env python3
"""Show iPerf3 requested state separately from observed process presence."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
args = parser.parse_args()
root = args.source / 'trunk/user'
backend = root / 'httpd/web_ex.c'
text = backend.read_text(encoding='utf-8')
array_anchor = 'struct ej_handler ej_handlers[] =\n'
system_entry = '\t{ "json_system_status", ej_system_status_hook},\n'
if (text.count(array_anchor) != 1 or text.count(system_entry) != 1 or
        'ej_wr_iperf3_process_state' in text):
    raise SystemExit('iPerf3 process-status HTTP hook anchors changed')
handler = r'''
/* Process observation only; it does not prove a usable test connection. */
static int ej_wr_iperf3_process_state(int eid, webs_t wp, int argc, char **argv)
{
 int requested, active;
 (void)eid; (void)argv;
 if (argc != 0) return websWrite(wp, "3");
 if (access("/proc/self/stat", R_OK)) return websWrite(wp, "3");
#if defined(APP_IPERF3)
 requested = nvram_get_int("iperf3_enable") > 0;
 active = pids("iperf3");
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
text = text.replace(array_anchor, handler + '\n' + array_anchor, 1)
text = text.replace(system_entry, system_entry + '\t{ "wr_iperf3_process_state", ej_wr_iperf3_process_state},\n', 1)

page = root / 'www/n56u_ribbon_fixed/Advanced_Services_Content.asp'
html = page.read_text(encoding='utf-8')
row_end = '''<input type="radio" name="iperf3_enable" id="iperf3_enable_0" class="input" value="0" <% nvram_match_x("", "iperf3_enable", "0", "checked"); %>/><#checkbox_No#>
                                                </div>
                                            </td>
                                        </tr>'''
unsupported = """if(!found_app_iperf3()){
\t\tshowhide_div('row_iperf3', 0);
\t}"""
if (html.count(row_end) != 1 or html.count(unsupported) != 1 or
        'id="wr_iperf3_process_status"' in html):
    raise SystemExit('iPerf3 status page anchors changed')
status_row = '''<tr id="wr_iperf3_status_row">
                                            <th><#WRIperf3ObservedTitle#></th>
                                            <td><strong id="wr_iperf3_process_status" role="status"><#WRIperf3Unknown#></strong>
                                                <button type="button" class="btn" onclick="wrIperf3Refresh()"><#WRIperf3Refresh#></button>
                                                <small id="wr_iperf3_observed_at"><#WRIperf3NoObservation#></small>
                                                <p class="help-block"><#WRIperf3ObservedNote#></p></td>
                                        </tr>'''
html = html.replace(row_end, row_end + '\n' + status_row, 1)
script = r'''
var wrIperf3StatusBusy = false;
function wrIperf3Render(state) {
    var labels = ["<#WRIperf3Off#>", "<#WRIperf3Present#>", "<#WRIperf3Missing#>", "<#WRIperf3Unknown#>", "<#WRIperf3StillPresent#>"];
    var classes = ['text-muted', 'text-info', 'text-error', 'text-warning', 'text-warning'];
    var element = document.getElementById('wr_iperf3_process_status');
    if (!element) return;
    var valid = typeof state === 'number' && state >= 0 && state < labels.length;
    element.textContent = valid ? labels[state] : labels[3];
    element.className = valid ? classes[state] : classes[3];
    if (valid && state !== 3) {
        var observedAt = document.getElementById('wr_iperf3_observed_at');
        if (observedAt) observedAt.textContent = '<#WRIperf3LastObservation#> ' + new Date().toLocaleTimeString();
    }
}
function wrIperf3Refresh() {
    if (wrIperf3StatusBusy || document.hidden || !found_app_iperf3()) return;
    wrIperf3StatusBusy = true;
    $j.ajax({url:'/update.cgi', data:{output:'wr_iperf3_process_state'}, dataType:'json', cache:false, timeout:5000})
        .done(function(state) { wrIperf3Render(state); })
        .fail(function() { wrIperf3Render(null); })
        .always(function() { wrIperf3StatusBusy = false; });
}
'''
anchor = 'function applyRule(){'
if html.count(anchor) != 1:
    raise SystemExit('iPerf3 status script insertion point changed')
html = html.replace(anchor, script + '\n' + anchor, 1)
init_anchor = """if(!found_app_iperf3()){
\t\tshowhide_div('row_iperf3', 0);
\t}"""
init_status = """if(!found_app_iperf3()){
\t\tshowhide_div('row_iperf3', 0);
\t\tshowhide_div('wr_iperf3_status_row', 0);
\t}else{
\t\twrIperf3Render(<% wr_iperf3_process_state(); %>);
\t\twindow.setInterval(wrIperf3Refresh, 30000);
\t}"""
html = html.replace(init_anchor, init_status, 1)

translations = {
    'EN.footer': {
        'WRIperf3ObservedTitle': 'Observed process state',
        'WRIperf3Off': 'Disabled; process not found',
        'WRIperf3Present': 'Enabled; process present (client test not verified)',
        'WRIperf3Missing': 'Enabled; process not found',
        'WRIperf3Unknown': 'Process state unknown',
        'WRIperf3StillPresent': 'Disabled; process still present',
        'WRIperf3Refresh': 'Refresh status',
        'WRIperf3LastObservation': 'Last process observation:',
        'WRIperf3NoObservation': 'No confirmed process observation yet',
        'WRIperf3ObservedNote': 'Shows the saved enable setting and whether the iPerf3 server process is present. It does not verify a client connection or test result. Refreshes every 30 seconds while this page is visible.',
    },
    'UK.dict': {
        'WRIperf3ObservedTitle': 'Спостережений стан процесу',
        'WRIperf3Off': 'Вимкнено; процесу не знайдено',
        'WRIperf3Present': 'Увімкнено; процес є (клієнтське тестування не перевірено)',
        'WRIperf3Missing': 'Увімкнено; процесу не знайдено',
        'WRIperf3Unknown': 'Стан процесу невідомий',
        'WRIperf3StillPresent': 'Вимкнено; процес досі працює',
        'WRIperf3Refresh': 'Оновити стан',
        'WRIperf3LastObservation': 'Останнє спостереження процесу:',
        'WRIperf3NoObservation': 'Підтвердженого спостереження процесу ще немає',
        'WRIperf3ObservedNote': 'Показує збережене налаштування та наявність серверного процесу iPerf3. Підключення клієнта й результат тесту цим не перевіряються. Оновлення кожні 30 секунд, поки сторінка відкрита.',
    },
    'RU.dict': {
        'WRIperf3ObservedTitle': 'Наблюдаемое состояние процесса',
        'WRIperf3Off': 'Выключено; процесс не найден',
        'WRIperf3Present': 'Включено; процесс есть (тест клиента не проверен)',
        'WRIperf3Missing': 'Включено; процесс не найден',
        'WRIperf3Unknown': 'Состояние процесса неизвестно',
        'WRIperf3StillPresent': 'Выключено; процесс всё ещё работает',
        'WRIperf3Refresh': 'Обновить состояние',
        'WRIperf3LastObservation': 'Последнее наблюдение процесса:',
        'WRIperf3NoObservation': 'Подтверждённого наблюдения процесса пока нет',
        'WRIperf3ObservedNote': 'Показывает сохранённую настройку и наличие серверного процесса iPerf3. Подключение клиента и результат теста этим не проверяются. Обновление каждые 30 секунд, пока страница открыта.',
    },
}
for filename, values in translations.items():
    path = root / 'www/dict' / filename
    content = path.read_text(encoding='utf-8')
    if 'WRIperf3Unknown=' in content:
        raise SystemExit(f'iPerf3 status labels already exist in {filename}')
    content = content.rstrip('\n') + '\n' + '\n'.join(f'{key}={value}' for key, value in values.items()) + '\n'
    path.write_text(content, encoding='utf-8', newline='\n')

backend.write_text(text, encoding='utf-8', newline='\n')
page.write_text(html, encoding='utf-8', newline='\n')
print('Prepared iPerf3 requested/observed process status; client connection and test result remain unverified')
