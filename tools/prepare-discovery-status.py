#!/usr/bin/env python3
"""Expose LLTD, ASUS Info Discovery, KMS and watchdog observations in services."""
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
        'ej_wr_discovery_process_state' in text or
        'ej_wr_watchdog_module_state' in text):
    raise SystemExit('Discovery process-status HTTP hook anchors changed')

backend_code = r'''
/* Process presence does not verify LLTD or ASUS discovery exchanges. */
static int wr_process_present(const char *name)
{
 DIR *proc;
 struct dirent *entry;
 int found = 0, read_error = 0;
 const unsigned char *p;
 const char *proc_path = "/proc";
#ifdef WR_DISCOVERY_STATUS_TEST
 const char *test_proc_path = getenv("WR_DISCOVERY_TEST_PROC");
 if (test_proc_path && *test_proc_path) proc_path = test_proc_path;
#endif
 proc = opendir(proc_path);
 if (!proc) return -1;
 for (;;) {
  char path[256], comm[64];
  FILE *file;
  size_t length;
  errno = 0;
  entry = readdir(proc);
  if (!entry) { if (errno) read_error = 1; break; }
  p = (const unsigned char *)entry->d_name;
  if (!*p) continue;
  while (*p && *p >= '0' && *p <= '9') p++;
  if (*p || p == (const unsigned char *)entry->d_name) continue;
  if (snprintf(path, sizeof(path), "%s/%s/comm", proc_path, entry->d_name) >= (int)sizeof(path)) {
   read_error = 1;
   break;
  }
  file = fopen(path, "r");
  if (!file) {
   if (errno != ENOENT && errno != ESRCH) read_error = 1;
   continue;
  }
  if (!fgets(comm, sizeof(comm), file)) {
   if (ferror(file)) read_error = 1;
   fclose(file);
   if (read_error) break;
   continue;
  }
  fclose(file);
  length = strlen(comm);
  while (length && (comm[length - 1] == '\n' || comm[length - 1] == '\r')) comm[--length] = '\0';
  if (!strcmp(comm, name)) found = 1;
 }
 if (closedir(proc)) read_error = 1;
 return read_error ? -1 : found;
}
static int wr_discovery_process_state(const char *setting, const char *process,
                                      const char *program)
{
 int requested, active;
 if (access("/proc", R_OK | X_OK) || access(program, X_OK)) return 3;
 requested = nvram_get_int(setting) > 0;
 active = wr_process_present(process);
 if (active < 0) return 3;
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
static int ej_wr_vlmcsd_process_state(int eid, webs_t wp, int argc, char **argv)
{
 return ej_wr_discovery_process_state(eid, wp, argc, argv,
     "vlmcsd_enable", "vlmcsd", "/usr/bin/vlmcsd");
}
/* Sysfs module presence is not evidence that the CPU timer is being serviced. */
static int wr_watchdog_module_state(void)
{
 struct stat sysfs, module;
 int requested = nvram_get_int("watchdog_cpu") != 0;
 if (stat("/sys/module", &sysfs) || !S_ISDIR(sysfs.st_mode) ||
     access("/sys/module", R_OK | X_OK)) return 3;
 if (!stat("/sys/module/rt_timer_wdg", &module))
  return requested ? 1 : 4;
 if (errno == ENOENT || errno == ENOTDIR)
  return requested ? 2 : 0;
 return 3;
}
static int ej_wr_watchdog_module_state(int eid, webs_t wp, int argc, char **argv)
{
 int state;
 (void)eid; (void)argv;
 if (argc != 0) return websWrite(wp, "3");
 state = wr_watchdog_module_state();
 return websWrite(wp, "%d", state);
}
'''
required_includes = ('#include <dirent.h>\n', '#include <errno.h>\n',
                     '#include <string.h>\n', '#include <sys/stat.h>\n')
include_block = ''.join(include for include in required_includes if include.strip() not in text)
if include_block:
    include_anchor = '#include <stdio.h>\n'
    if text.count(include_anchor) != 1:
        raise SystemExit('Could not locate web_ex.c include block')
    text = text.replace(include_anchor, include_anchor + include_block, 1)
entries = (system_entry +
           '\t{ "wr_lltd_process_state", ej_wr_lltd_process_state},\n' +
           '\t{ "wr_adsc_process_state", ej_wr_adsc_process_state},\n' +
           '\t{ "wr_vlmcsd_process_state", ej_wr_vlmcsd_process_state},\n' +
           '\t{ "wr_watchdog_module_state", ej_wr_watchdog_module_state},\n')
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
if ('wr_discovery_process_status' in html or 'wrWatchdog_process_status' in html or
        'wrVlmcsd_process_status' in html):
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
    prefix, camel = {
        'lltd': ('WRLLTD', 'wrLLTD'),
        'adsc': ('WRADSC', 'wrADSC'),
        'vlmcsd': ('WRVLMCS', 'wrVlmcsd'),
        'watchdog': ('WRWDG', 'wrWatchdog'),
    }[service]
    status = f'''\n<tr id="{camel}_status_row"><th><#{prefix}ObservedTitle#></th><td>
<strong id="{camel}_process_status" role="status"><#{prefix}Unknown#></strong>
<button type="button" class="btn" onclick="{camel}Refresh()"><#{prefix}Refresh#></button>
<small id="{camel}_observed_at"><#{prefix}NoObservation#></small>
<p class="help-block"><#{prefix}ObservedNote#></p></td></tr>'''
    html = html[:row_end] + status + html[row_end:]

insert_status_row('<#Adm_Svc_lltd#>', 'lltd')
insert_status_row('<#Adm_Svc_adsc#>', 'adsc')
insert_status_row('id="div_vlmcsd"', 'vlmcsd')
insert_status_row('<#TweaksWdg#>', 'watchdog')

script = r'''
var wrDiscoveryBusy = {lltd:false, adsc:false, vlmcsd:false, watchdog:false};
var wrDiscoveryGeneration = {lltd:0, adsc:0, vlmcsd:0, watchdog:0};
var wrDiscoverySampledAt = {lltd:0, adsc:0, vlmcsd:0, watchdog:0};
var wrDiscoveryLabels = {
    lltd:["<#WRLLTDOff#>","<#WRLLDTPresent#>","<#WRLLDTMissing#>","<#WRLLDTUnknown#>","<#WRLLDTStillPresent#>"],
    adsc:["<#WRADSCOff#>","<#WRADSCPresent#>","<#WRADSCMissing#>","<#WRADSCUnknown#>","<#WRADSCStillPresent#>"],
    vlmcsd:["<#WRVLMCSOff#>","<#WRVLMCSRunning#>","<#WRVLMCSMissing#>","<#WRVLMCSUnknown#>","<#WRVLMCSStillRunning#>"],
    watchdog:["<#WRWDGOff#>","<#WRWDGPresent#>","<#WRWDGMissing#>","<#WRWDGUnknown#>","<#WRWDGStillPresent#>"]
};
function wrDiscoveryRender(service, state) {
    var generation = ++wrDiscoveryGeneration[service];
    wrDiscoverySampledAt[service] = 0;
    var labels = wrDiscoveryLabels[service];
    var classes = ['text-muted','text-success','text-error','text-warning','text-warning'];
    var suffix = service === 'lltd' ? 'LLTD' : service === 'adsc' ? 'ADSC' :
        service === 'vlmcsd' ? 'Vlmcsd' : 'Watchdog';
    var element = document.getElementById('wr' + suffix + '_process_status');
    if (!element) return;
    var valid = typeof state === 'number' && Math.floor(state) === state && state >= 0 && state < labels.length;
    element.textContent = valid ? labels[state] : labels[3];
    element.className = valid ? classes[state] : classes[3];
    if (valid && state !== 3) {
        wrDiscoverySampledAt[service] = Date.now();
        window.setTimeout(function() {
            if (generation === wrDiscoveryGeneration[service]) wrDiscoveryRender(service, null);
        }, 45000);
    }
    var observed = document.getElementById('wr' + suffix + '_observed_at');
    var lastObservation = service === 'lltd' ? '<#WRLLTDLastObservation#>' :
        service === 'adsc' ? '<#WRADSCLastObservation#>' :
        service === 'vlmcsd' ? '<#WRVLMCSLastObservation#>' : '<#WRWDGLastObservation#>';
    var noObservation = service === 'lltd' ? '<#WRLLTDNoObservation#>' :
        service === 'adsc' ? '<#WRADSCNoObservation#>' :
        service === 'vlmcsd' ? '<#WRVLMCSNoObservation#>' : '<#WRWDGNoObservation#>';
    if (observed) observed.textContent = valid && state !== 3 ?
        lastObservation + ' ' + new Date().toLocaleTimeString() : noObservation;
}
document.addEventListener('visibilitychange', function() {
    if (document.hidden) return;
    ['lltd','adsc','vlmcsd','watchdog'].forEach(function(service) {
        if (wrDiscoverySampledAt[service] && Date.now() - wrDiscoverySampledAt[service] >= 45000)
            wrDiscoveryRender(service, null);
    });
});
function wrDiscoveryRefresh(service) {
    if (wrDiscoveryBusy[service] || document.hidden) return;
    wrDiscoveryBusy[service] = true;
    var outputs = {lltd:'wr_lltd_process_state', adsc:'wr_adsc_process_state',
        vlmcsd:'wr_vlmcsd_process_state', watchdog:'wr_watchdog_module_state'};
    $j.ajax({url:'/update.cgi', data:{output:outputs[service]}, dataType:'json', cache:false, timeout:5000})
        .done(function(state) { wrDiscoveryRender(service, state); })
        .fail(function() { wrDiscoveryRender(service, null); })
        .always(function() { wrDiscoveryBusy[service] = false; });
}
function wrLLTDRefresh() { wrDiscoveryRefresh('lltd'); }
function wrADSCRefresh() { wrDiscoveryRefresh('adsc'); }
function wrVlmcsdRefresh() { wrDiscoveryRefresh('vlmcsd'); }
function wrWatchdogRefresh() { wrDiscoveryRefresh('watchdog'); }
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
\twrDiscoveryRender('vlmcsd', <% wr_vlmcsd_process_state(); %>);
\twrDiscoveryRender('watchdog', <% wr_watchdog_module_state(); %>);
\twindow.setInterval(function(){wrLLTDRefresh();wrADSCRefresh();wrVlmcsdRefresh();wrWatchdogRefresh();},30000);''', 1)

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
        'WRVLMCSObservedTitle':'Observed KMS activation process',
        'WRVLMCSOff':'Disabled; vlmcsd process not found',
        'WRVLMCSRunning':'Enabled; vlmcsd process present',
        'WRVLMCSMissing':'Enabled; vlmcsd process not found',
        'WRVLMCSUnknown':'KMS activation process state unavailable',
        'WRVLMCSStillRunning':'Disabled; vlmcsd process still present',
        'WRVLMCSRefresh':'Refresh status',
        'WRVLMCSLastObservation':'Last process observation:',
        'WRVLMCSNoObservation':'No confirmed process observation yet',
        'WRVLMCSObservedNote':'Shows the saved setting and the vlmcsd process only. It does not verify KMS client requests or activation results.',
        'WRWDGObservedTitle':'Observed CPU watchdog module',
        'WRWDGOff':'Disabled; rt_timer_wdg module not loaded',
        'WRWDGPresent':'Enabled; rt_timer_wdg loaded (timer operation unverified)',
        'WRWDGMissing':'Enabled; rt_timer_wdg not loaded',
        'WRWDGUnknown':'Watchdog module state unavailable',
        'WRWDGStillPresent':'Disabled; rt_timer_wdg still loaded',
        'WRWDGRefresh':'Refresh status',
        'WRWDGLastObservation':'Last module observation:',
        'WRWDGNoObservation':'No confirmed module observation yet',
        'WRWDGObservedNote':'Shows the saved watchdog_cpu setting and whether rt_timer_wdg is registered in sysfs. This does not verify that the hardware timer is active or serviced.',
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
        'WRVLMCSObservedTitle':'Спостереження процесу активації KMS',
        'WRVLMCSOff':'Вимкнено; процес vlmcsd відсутній',
        'WRVLMCSRunning':'Увімкнено; процес vlmcsd працює',
        'WRVLMCSMissing':'Увімкнено; процес vlmcsd не знайдено',
        'WRVLMCSUnknown':'Стан процесу KMS недоступний',
        'WRVLMCSStillRunning':'Вимкнено; процес vlmcsd досі працює',
        'WRVLMCSRefresh':'Оновити стан',
        'WRVLMCSLastObservation':'Останнє спостереження процесу:',
        'WRVLMCSNoObservation':'Підтвердженого спостереження процесу ще немає',
        'WRVLMCSObservedNote':'Показує збережене налаштування та лише наявність процесу vlmcsd. Запити клієнтів KMS та результат активації не перевіряються.',
        'WRWDGObservedTitle':'Стан модуля CPU Watchdog',
        'WRWDGOff':'Вимкнено; модуль rt_timer_wdg не завантажений',
        'WRWDGPresent':'Увімкнено; rt_timer_wdg завантажений (таймер не перевірено)',
        'WRWDGMissing':'Увімкнено; rt_timer_wdg не завантажений',
        'WRWDGUnknown':'Стан модуля Watchdog недоступний',
        'WRWDGStillPresent':'Вимкнено; rt_timer_wdg досі завантажений',
        'WRWDGRefresh':'Оновити стан',
        'WRWDGLastObservation':'Останнє спостереження модуля:',
        'WRWDGNoObservation':'Підтвердженого спостереження модуля ще немає',
        'WRWDGObservedNote':'Показує збережений параметр watchdog_cpu та лише наявність rt_timer_wdg у sysfs. Активність чи обслуговування апаратного таймера не перевіряються.',
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
        'WRVLMCSObservedTitle':'Наблюдение процесса активации KMS',
        'WRVLMCSOff':'Выключено; процесс vlmcsd отсутствует',
        'WRVLMCSRunning':'Включено; процесс vlmcsd работает',
        'WRVLMCSMissing':'Включено; процесс vlmcsd не найден',
        'WRVLMCSUnknown':'Состояние процесса KMS недоступно',
        'WRVLMCSStillRunning':'Выключено; процесс vlmcsd всё ещё работает',
        'WRVLMCSRefresh':'Обновить состояние',
        'WRVLMCSLastObservation':'Последнее наблюдение процесса:',
        'WRVLMCSNoObservation':'Подтверждённого наблюдения процесса пока нет',
        'WRVLMCSObservedNote':'Показывает сохранённую настройку и только наличие процесса vlmcsd. Запросы клиентов KMS и результат активации не проверяются.',
        'WRWDGObservedTitle':'Состояние модуля CPU Watchdog',
        'WRWDGOff':'Выключено; модуль rt_timer_wdg не загружен',
        'WRWDGPresent':'Включено; rt_timer_wdg загружен (работа таймера не проверена)',
        'WRWDGMissing':'Включено; rt_timer_wdg не загружен',
        'WRWDGUnknown':'Состояние модуля Watchdog недоступно',
        'WRWDGStillPresent':'Выключено; rt_timer_wdg всё ещё загружен',
        'WRWDGRefresh':'Обновить состояние',
        'WRWDGLastObservation':'Последнее наблюдение модуля:',
        'WRWDGNoObservation':'Подтверждённого наблюдения модуля пока нет',
        'WRWDGObservedNote':'Показывает сохранённый параметр watchdog_cpu и только наличие rt_timer_wdg в sysfs. Работа или обслуживание аппаратного таймера не проверяются.',
    },
}
for filename, values in translations.items():
    path = root / 'www/dict' / filename
    content = path.read_text(encoding='utf-8')
    if ('WRLLDTObservedTitle=' in content or 'WRADSCObservedTitle=' in content or
            'WRVLMCSObservedTitle=' in content):
        raise SystemExit(f'Discovery status labels already exist in {filename}')
    content = content.rstrip('\n') + '\n' + '\n'.join(
        f'{key}={value}' for key, value in values.items()) + '\n'
    path.write_text(content, encoding='utf-8', newline='\n')

backend.write_text(text, encoding='utf-8', newline='\n')
page.write_text(html, encoding='utf-8', newline='\n')
print('Prepared LLTD/ASUS/KMS process and watchdog module observations; protocols and timer operation remain unverified')
