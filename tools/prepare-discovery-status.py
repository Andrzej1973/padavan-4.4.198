#!/usr/bin/env python3
"""Expose LLTD and ASUS Info Discovery process observations in the services page."""
import argparse
import ast
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
args = parser.parse_args()
root = args.source / 'trunk/user'
backend = root / 'httpd/web_ex.c'
text = backend.read_text(encoding='utf-8')
array_anchor = 'struct ej_handler ej_handlers[] =\n'
system_entry = '\t{ "json_system_status", ej_system_status_hook},\n'
if (text.count(array_anchor) != 1 or text.count(system_entry) != 1 or
        'ej_wr_discovery_process_state' in text):
    raise SystemExit('Discovery process-status HTTP hook anchors changed')

backend_code = r'''
/* Process presence does not verify LLTD or ASUS discovery exchanges. */
static int wr_discovery_process_state(const char *setting, const char *process,
                                      const char *program)
{
 int requested, active;
 if (access("/proc/self/stat", R_OK) || access(program, X_OK)) return 3;
 requested = nvram_get_int(setting) > 0;
 active = pids(process);
 if (active < 0) return 3;
 active = active > 0;
 return active ? (requested ? 1 : 4) : (requested ? 2 : 0);
}
static int ej_wr_discovery_process_state(int eid, webs_t wp, int argc,
                                         char **argv, const char *setting,
                                         const char *process, const char *program)
{
 int state;
 (void)eid; (void)argv;
 if (argc != 0) return websWrite(wp, "3");
 state = wr_discovery_process_state(setting, process, program);
 return websWrite(wp, "%d", state);
}
static int ej_wr_lltd_process_state(int eid, webs_t wp, int argc, char **argv)
{
 return ej_wr_discovery_process_state(eid, wp, argc, argv,
     "lltd_enable", "lld2d", "/bin/lld2d");
}
static int ej_wr_adsc_process_state(int eid, webs_t wp, int argc, char **argv)
{
 return ej_wr_discovery_process_state(eid, wp, argc, argv,
     "adsc_enable", "infosvr", "/usr/sbin/infosvr");
}
'''
entries = (system_entry +
           '\t{ "wr_lltd_process_state", ej_wr_lltd_process_state},\n' +
           '\t{ "wr_adsc_process_state", ej_wr_adsc_process_state},\n')
text = text.replace(array_anchor, backend_code + '\n' + array_anchor, 1)
text = text.replace(system_entry, entries, 1)

ssh_template = ast.parse(Path(__file__).with_name('prepare-ssh-status.py').read_text(encoding='utf-8'))
def literal(name):
    return next(ast.literal_eval(node.value) for node in ssh_template.body
                if isinstance(node, ast.Assign) and
                any(isinstance(target, ast.Name) and target.id == name
                    for target in node.targets))

page = root / 'www/n56u_ribbon_fixed/Advanced_Services_Content.asp'
html = page.read_text(encoding='utf-8')
if 'wr_discovery_process_status' in html:
    raise SystemExit('Discovery process-status page already exists')

def insert_status_row(mark, service):
    global html
    if html.count(mark) != 1:
        raise SystemExit(f'Expected one services row marker for {service}')
    label_pos = html.index(mark)
    row_start = html.rfind('<tr', 0, label_pos)
    row_end = html.find('</tr>', label_pos)
    if row_start < 0 or row_end < 0:
        raise SystemExit(f'Could not locate services row for {service}')
    row_end += len('</tr>')
    prefix = 'WRLLTD' if service == 'lltd' else 'WRADSC'
    camel = 'wrLLTD' if service == 'lltd' else 'wrADSC'
    status = f'''\n<tr id="{camel}_status_row"><th><#{prefix}ObservedTitle#></th><td>
<strong id="{camel}_process_status" role="status"><#{prefix}Unknown#></strong>
<button type="button" class="btn" onclick="{camel}Refresh()"><#{prefix}Refresh#></button>
<small id="{camel}_observed_at"><#{prefix}NoObservation#></small>
<p class="help-block"><#{prefix}ObservedNote#></p></td></tr>'''
    html = html[:row_end] + status + html[row_end:]

insert_status_row('<#Adm_Svc_lltd#>', 'lltd')
insert_status_row('<#Adm_Svc_adsc#>', 'adsc')

script = r'''
var wrDiscoveryBusy = {lltd:false, adsc:false};
var wrDiscoveryGeneration = {lltd:0, adsc:0};
var wrDiscoverySampledAt = {lltd:0, adsc:0};
var wrDiscoveryLabels = {
    lltd:["<#WRLLTDOff#>","<#WRLLDTPresent#>","<#WRLLDTMissing#>","<#WRLLDTUnknown#>","<#WRLLDTStillPresent#>"],
    adsc:["<#WRADSCOff#>","<#WRADSCPresent#>","<#WRADSCMissing#>","<#WRADSCUnknown#>","<#WRADSCStillPresent#>"]
};
function wrDiscoveryRender(service, state) {
    var generation = ++wrDiscoveryGeneration[service];
    wrDiscoverySampledAt[service] = 0;
    var labels = wrDiscoveryLabels[service];
    var classes = ['text-muted','text-info','text-error','text-warning','text-warning'];
    var element = document.getElementById('wr' + (service === 'lltd' ? 'LLTD' : 'ADSC') + '_process_status');
    if (!element) return;
    var valid = typeof state === 'number' && Math.floor(state) === state && state >= 0 && state < labels.length;
    element.textContent = valid ? labels[state] : labels[3];
    element.className = valid ? classes[state] : classes[3];
    if (valid && state !== 3) {
        wrDiscoverySampledAt[service] = Date.now();
        window.setTimeout(function() {
            if (generation === wrDiscoveryGeneration[service]) wrDiscoveryRender(service, null);
        }, 45000);
        var observed = document.getElementById('wr' + (service === 'lltd' ? 'LLTD' : 'ADSC') + '_observed_at');
        if (observed) observed.textContent = (service === 'lltd' ? '<#WRLLTDLastObservation#>' : '<#WRADSCLastObservation#>') + ' ' + new Date().toLocaleTimeString();
    }
}
document.addEventListener('visibilitychange', function() {
    if (document.hidden) return;
    ['lltd','adsc'].forEach(function(service) {
        if (wrDiscoverySampledAt[service] && Date.now() - wrDiscoverySampledAt[service] >= 45000)
            wrDiscoveryRender(service, null);
    });
});
function wrDiscoveryRefresh(service) {
    if (wrDiscoveryBusy[service] || document.hidden) return;
    wrDiscoveryBusy[service] = true;
    $j.ajax({url:'/update.cgi', data:{output:'wr_' + service + '_process_state'}, dataType:'json', cache:false, timeout:5000})
        .done(function(state) { wrDiscoveryRender(service, state); })
        .fail(function() { wrDiscoveryRender(service, null); })
        .always(function() { wrDiscoveryBusy[service] = false; });
}
function wrLLTDRefresh() { wrDiscoveryRefresh('lltd'); }
function wrADSCRefresh() { wrDiscoveryRefresh('adsc'); }
'''
apply_anchor = 'function applyRule(){'
if html.count(apply_anchor) != 1:
    raise SystemExit('Discovery status script insertion point changed')
html = html.replace(apply_anchor, script + '\n' + apply_anchor, 1)
cron_init = '''\twrCronRender(<% wr_cron_process_state(); %>);
\twindow.setInterval(wrCronRefresh,30000);'''
if html.count(cron_init) != 1:
    raise SystemExit('Expected the Cron observer to precede discovery observers')
html = html.replace(cron_init, cron_init + '''
\twrDiscoveryRender('lltd', <% wr_lltd_process_state(); %>);
\twrDiscoveryRender('adsc', <% wr_adsc_process_state(); %>);
\twindow.setInterval(function(){wrLLTDRefresh();wrADSCRefresh();},30000);''', 1)

translations = {
    'EN.footer': {
        'WRLLTDObservedTitle':'Observed LLTD process',
        'WRLLTDOff':'Disabled; LLTD process not found',
        'WRLLDTPresent':'Enabled; LLTD process present (protocol unverified)',
        'WRLLDTMissing':'Enabled; LLTD process not found',
        'WRLLDTUnknown':'LLTD process state unavailable',
        'WRLLDTStillPresent':'Disabled; LLTD process still present',
        'WRLLTDRefresh':'Refresh status',
        'WRLLTDLastObservation':'Last process observation:',
        'WRLLTDNoObservation':'No confirmed process observation yet',
        'WRLLTDObservedNote':'Shows the saved setting and the lld2d process only. LLTD discovery exchanges and client visibility are not verified.',
        'WRADSCObservedTitle':'Observed ASUS Info Discovery process',
        'WRADSCOff':'Disabled; infosvr process not found',
        'WRADSCPresent':'Enabled; infosvr process present (discovery unverified)',
        'WRADSCMissing':'Enabled; infosvr process not found',
        'WRADSCUnknown':'ASUS Info Discovery process state unavailable',
        'WRADSCStillPresent':'Disabled; infosvr process still present',
        'WRADSCRefresh':'Refresh status',
        'WRADSCLastObservation':'Last process observation:',
        'WRADSCNoObservation':'No confirmed process observation yet',
        'WRADSCObservedNote':'Shows the saved setting and the infosvr process only. ASUS discovery replies and device visibility are not verified.',
    },
    'UK.dict': {
        'WRLLTDObservedTitle':'Спостереження процесу LLTD',
        'WRLLTDOff':'Вимкнено; процес LLTD відсутній',
        'WRLLDTPresent':'Увімкнено; процес LLTD працює (протокол не перевірено)',
        'WRLLDTMissing':'Увімкнено; процес LLTD не знайдено',
        'WRLLDTUnknown':'Стан процесу LLTD недоступний',
        'WRLLDTStillPresent':'Вимкнено; процес LLTD досі працює',
        'WRLLTDRefresh':'Оновити стан',
        'WRLLTDLastObservation':'Останнє спостереження процесу:',
        'WRLLTDNoObservation':'Підтвердженого спостереження процесу ще немає',
        'WRLLTDObservedNote':'Показує збережене налаштування та лише наявність процесу lld2d. Обмін LLTD і видимість пристроїв не перевірені.',
        'WRADSCObservedTitle':'Спостереження процесу ASUS Info Discovery',
        'WRADSCOff':'Вимкнено; процес infosvr відсутній',
        'WRADSCPresent':'Увімкнено; процес infosvr працює (виявлення не перевірено)',
        'WRADSCMissing':'Увімкнено; процес infosvr не знайдено',
        'WRADSCUnknown':'Стан процесу ASUS Info Discovery недоступний',
        'WRADSCStillPresent':'Вимкнено; процес infosvr досі працює',
        'WRADSCRefresh':'Оновити стан',
        'WRADSCLastObservation':'Останнє спостереження процесу:',
        'WRADSCNoObservation':'Підтвердженого спостереження процесу ще немає',
        'WRADSCObservedNote':'Показує збережене налаштування та лише наявність процесу infosvr. Відповіді ASUS Discovery і видимість пристроїв не перевірені.',
    },
    'RU.dict': {
        'WRLLTDObservedTitle':'Наблюдение процесса LLTD',
        'WRLLTDOff':'Выключено; процесс LLTD отсутствует',
        'WRLLDTPresent':'Включено; процесс LLTD работает (протокол не проверен)',
        'WRLLDTMissing':'Включено; процесс LLTD не найден',
        'WRLLDTUnknown':'Состояние процесса LLTD недоступно',
        'WRLLDTStillPresent':'Выключено; процесс LLTD всё ещё работает',
        'WRLLTDRefresh':'Обновить состояние',
        'WRLLTDLastObservation':'Последнее наблюдение процесса:',
        'WRLLTDNoObservation':'Подтверждённого наблюдения процесса пока нет',
        'WRLLTDObservedNote':'Показывает сохранённую настройку и только наличие процесса lld2d. Обмен LLTD и видимость устройств не проверены.',
        'WRADSCObservedTitle':'Наблюдение процесса ASUS Info Discovery',
        'WRADSCOff':'Выключено; процесс infosvr отсутствует',
        'WRADSCPresent':'Включено; процесс infosvr работает (обнаружение не проверено)',
        'WRADSCMissing':'Включено; процесс infosvr не найден',
        'WRADSCUnknown':'Состояние процесса ASUS Info Discovery недоступно',
        'WRADSCStillPresent':'Выключено; процесс infosvr всё ещё работает',
        'WRADSCRefresh':'Обновить состояние',
        'WRADSCLastObservation':'Последнее наблюдение процесса:',
        'WRADSCNoObservation':'Подтверждённого наблюдения процесса пока нет',
        'WRADSCObservedNote':'Показывает сохранённую настройку и только наличие процесса infosvr. Ответы ASUS Discovery и видимость устройств не проверены.',
    },
}
for filename, values in translations.items():
    path = root / 'www/dict' / filename
    content = path.read_text(encoding='utf-8')
    if 'WRLLDTObservedTitle=' in content or 'WRADSCObservedTitle=' in content:
        raise SystemExit(f'Discovery status labels already exist in {filename}')
    content = content.rstrip('\n') + '\n' + '\n'.join(
        f'{key}={value}' for key, value in values.items()) + '\n'
    path.write_text(content, encoding='utf-8', newline='\n')

backend.write_text(text, encoding='utf-8', newline='\n')
page.write_text(html, encoding='utf-8', newline='\n')
print('Prepared LLTD and ASUS Info process observations; protocol behavior remains unverified')
