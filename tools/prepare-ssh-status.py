#!/usr/bin/env python3
"""Show SSH requested state separately from observed daemon presence."""
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
        'ej_wr_ssh_process_state' in text):
    raise SystemExit('SSH process-status HTTP hook anchors changed')
handler = r'''
static int wr_process_present(const char *name);
/* Process presence does not verify a listening socket or login success. */
static int ej_wr_ssh_process_state(int eid, webs_t wp, int argc, char **argv)
{
 int requested, active;
 (void)eid; (void)argv;
 if (argc != 0) return websWrite(wp, "3");
 if (access("/proc/self/stat", R_OK)) return websWrite(wp, "3");
 requested = nvram_get_int("sshd_enable") > 0;
#if defined(APP_DROPBEAR)
 active = wr_process_present("dropbear");
#elif defined(APP_OPENSSH)
 active = wr_process_present("sshd");
#else
 return websWrite(wp, "3");
#endif
 if (active < 0) return websWrite(wp, "3");
 active = active > 0;
 return websWrite(wp, "%d", active ? (requested ? 1 : 4) : (requested ? 2 : 0));
}
'''
text = text.replace(array_anchor, handler + '\n' + array_anchor, 1)
text = text.replace(system_entry, system_entry + '\t{ "wr_ssh_process_state", ej_wr_ssh_process_state},\n', 1)

page = root / 'www/n56u_ribbon_fixed/Advanced_Services_Content.asp'
html = page.read_text(encoding='utf-8')
row_anchor = '''<tr id="row_sshd">'''
row_end = '''</tr>
                                        <tr id="row_ssh_keys"'''
unsupported = '''if(!found_app_sshd()){
\t\tshowhide_div('row_sshd', 0);
\t\ttextarea_sshd_enabled(0);
\t}else
\t\tsshd_auth_change();'''
if (html.count(row_anchor) != 1 or html.count(row_end) != 1 or
        html.count(unsupported) != 1 or 'id="wr_ssh_process_status"' in html):
    raise SystemExit('SSH status page anchors changed')
status_row = '''</tr>
                                        <tr id="wr_ssh_status_row">
                                            <th><#WRSSHObservedTitle#></th>
                                            <td><strong id="wr_ssh_process_status" role="status"><#WRSSHUnknown#></strong>
                                                <button type="button" class="btn" onclick="wrSSHRefresh()"><#WRSSHRefresh#></button>
                                                <small id="wr_ssh_observed_at"><#WRSSHNoObservation#></small>
                                                <p class="help-block"><#WRSSHObservedNote#></p></td>
                                        </tr>
                                        <tr id="row_ssh_keys"'''
html = html.replace(row_end, status_row, 1)
script = r'''
var wrSSHStatusBusy = false;
var wrSSHGeneration = 0, wrSSHSampledAt = 0;
function wrSSHRender(state) {
    var generation = ++wrSSHGeneration;
    wrSSHSampledAt = 0;
    var labels = ["<#WRSSHOff#>", "<#WRSSHPresent#>", "<#WRSSHMissing#>", "<#WRSSHUnknown#>", "<#WRSSHStillPresent#>"];
    var classes = ['text-muted', 'text-info', 'text-error', 'text-warning', 'text-warning'];
    var element = document.getElementById('wr_ssh_process_status');
    if (!element) return;
    var valid = typeof state === 'number' && Math.floor(state) === state && state >= 0 && state < labels.length;
    element.textContent = valid ? labels[state] : labels[3];
    element.className = valid ? classes[state] : classes[3];
    if (valid && state !== 3) {
        wrSSHSampledAt = Date.now();
        window.setTimeout(function() {
            if (generation === wrSSHGeneration) wrSSHRender(null);
        }, 45000);
        var observedAt = document.getElementById('wr_ssh_observed_at');
        if (observedAt) observedAt.textContent = '<#WRSSHLastObservation#> ' + new Date().toLocaleTimeString();
    }
}
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && wrSSHSampledAt && Date.now() - wrSSHSampledAt >= 45000) wrSSHRender(null);
});
function wrSSHRefresh() {
    if (wrSSHStatusBusy || document.hidden || !found_app_sshd()) return;
    wrSSHStatusBusy = true;
    $j.ajax({url:'/update.cgi', data:{output:'wr_ssh_process_state'}, dataType:'json', cache:false, timeout:5000})
        .done(function(state) { wrSSHRender(state); })
        .fail(function() { wrSSHRender(null); })
        .always(function() { wrSSHStatusBusy = false; });
}
'''
anchor = 'function applyRule(){'
if html.count(anchor) != 1:
    raise SystemExit('SSH status script insertion point changed')
html = html.replace(anchor, script + '\n' + anchor, 1)
init_status = '''if(!found_app_sshd()){
\t\tshowhide_div('row_sshd', 0);
\t\ttextarea_sshd_enabled(0);
\t\tshowhide_div('wr_ssh_status_row', 0);
\t}else{
\t\twrSSHRender(<% wr_ssh_process_state(); %>);
\t\twindow.setInterval(wrSSHRefresh, 30000);
\t\tsshd_auth_change();
\t}'''
html = html.replace(unsupported, init_status, 1)
if html.count("window.setInterval(wrSSHRefresh, 30000);\n\t\tsshd_auth_change();") != 1:
    raise SystemExit('SSH authorization controls are not initialized with the status observer')
if "\n\t\t}else\n\t\tsshd_auth_change();" in html:
    raise SystemExit('Unexpected dangling SSH authorization branch')

translations = {
    'EN.footer': {
        'WRSSHObservedTitle': 'Observed daemon state',
        'WRSSHOff': 'Disabled; daemon not found',
        'WRSSHPresent': 'Enabled; daemon present (connection not verified)',
        'WRSSHMissing': 'Enabled; daemon not found',
        'WRSSHUnknown': 'Daemon state unknown',
        'WRSSHStillPresent': 'Disabled; daemon still present',
        'WRSSHRefresh': 'Refresh status',
        'WRSSHLastObservation': 'Last daemon observation:',
        'WRSSHNoObservation': 'No confirmed daemon observation yet',
        'WRSSHObservedNote': 'Shows the saved SSH mode and whether the selected SSH daemon process is present. Listening socket, firewall reachability and authentication are not verified. Refreshes every 30 seconds while this page is visible.',
    },
    'UK.dict': {
        'WRSSHObservedTitle': 'Спостережений стан служби',
        'WRSSHOff': 'Вимкнено; процесу служби не знайдено',
        'WRSSHPresent': 'Увімкнено; процес служби є (з’єднання не перевірено)',
        'WRSSHMissing': 'Увімкнено; процесу служби не знайдено',
        'WRSSHUnknown': 'Стан служби невідомий',
        'WRSSHStillPresent': 'Вимкнено; процес служби досі працює',
        'WRSSHRefresh': 'Оновити стан',
        'WRSSHLastObservation': 'Останнє спостереження служби:',
        'WRSSHNoObservation': 'Підтвердженого спостереження служби ще немає',
        'WRSSHObservedNote': 'Показує режим SSH у налаштуваннях і наявність процесу служби. Сокет прослуховування, доступність через брандмауер і автентифікацію не перевірено. Оновлення кожні 30 секунд, поки сторінка відкрита.',
    },
    'RU.dict': {
        'WRSSHObservedTitle': 'Наблюдаемое состояние службы',
        'WRSSHOff': 'Выключено; процесс службы не найден',
        'WRSSHPresent': 'Включено; процесс службы есть (соединение не проверено)',
        'WRSSHMissing': 'Включено; процесс службы не найден',
        'WRSSHUnknown': 'Состояние службы неизвестно',
        'WRSSHStillPresent': 'Выключено; процесс службы всё ещё работает',
        'WRSSHRefresh': 'Обновить состояние',
        'WRSSHLastObservation': 'Последнее наблюдение службы:',
        'WRSSHNoObservation': 'Подтверждённого наблюдения службы пока нет',
        'WRSSHObservedNote': 'Показывает сохранённый режим SSH и наличие процесса службы. Сокет прослушивания, доступность через брандмауэр и аутентификация не проверены. Обновление каждые 30 секунд, пока страница открыта.',
    },
}
for filename, values in translations.items():
    path = root / 'www/dict' / filename
    content = path.read_text(encoding='utf-8')
    if 'WRSSHUnknown=' in content:
        raise SystemExit(f'SSH status labels already exist in {filename}')
    content = content.rstrip('\n') + '\n' + '\n'.join(f'{key}={value}' for key, value in values.items()) + '\n'
    path.write_text(content, encoding='utf-8', newline='\n')

backend.write_text(text, encoding='utf-8', newline='\n')
page.write_text(html, encoding='utf-8', newline='\n')
print('Prepared SSH requested/observed daemon status; connection and authentication remain unverified')
