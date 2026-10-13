#!/usr/bin/env python3
"""Expose process observation separately from DNS functionality."""
import argparse
import re
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
a = p.parse_args()
root = a.source / 'trunk/user'
path = root / 'httpd/web_ex.c'
s = path.read_text(encoding='utf-8')
anchor = 'struct ej_handler ej_handlers[] =\n'
entry = '\t{ "json_system_status", ej_system_status_hook},\n'
if s.count(anchor) != 1 or s.count(entry) != 1 or 'ej_wr_dns_process_state' in s:
    raise SystemExit('DNS process status anchors changed')
code = r'''
/* Process observation only: never equate a PID with successful DNS/TLS. */
static int ej_wr_dns_process_state(int eid, webs_t wp, int argc, char **argv)
{
 const char *key = NULL; char *process = NULL; int active, requested;
 (void)eid;
 if (argc != 1 || !argv || !argv[0]) return websWrite(wp, "3");
 if (!strcmp(argv[0], "stubby")) { key="stubby_enable"; process="stubby"; }
 else if (!strcmp(argv[0], "doh")) { key="doh_enable"; process="https_dns_proxy"; }
 else return websWrite(wp, "3");
 if (access("/proc/self/stat", R_OK)) return websWrite(wp, "3");
 active = pids(process) > 0; requested = nvram_get_int(key) > 0;
 return websWrite(wp, "%d", active ? (requested ? 1 : 4) : (requested ? 2 : 0));
}
'''
changes = [(path, s.replace(anchor, code + '\n' + anchor).replace(entry, entry + '\t{ "wr_dns_process_state", ej_wr_dns_process_state},\n'))]
keys = ['Off', 'Present', 'Absent', 'Unknown', 'StillPresent', 'Note', 'Refresh']
for page, service in [('Advanced_Services_DoT.asp', 'stubby'), ('Advanced_Services_DoH.asp', 'doh')]:
    path = root / 'www/n56u_ribbon_fixed' / page
    if not path.exists():
        continue
    html = path.read_text(encoding='utf-8')
    table = '<table width="100%" cellpadding="4" cellspacing="0"'
    if html.count(table) != 1 or len(re.findall(r'function initial\(\)\s*\{', html)) != 1:
        raise SystemExit('DNS status page anchors changed: ' + page)
    js = '\n var ds = <% wr_dns_process_state("' + service + '"); %>;\n var dl = [' + ','.join('"<#WRDNS' + k + '#>"' for k in keys[:5]) + '];\n $j("#wr_dns_process_status").text(dl[ds] || dl[3]);\n'
    refresh='\nvar wrDNSBusy=false;\nfunction wrDNSRefresh(){\n'
    refresh+=' if(wrDNSBusy || document.hidden)return;\n wrDNSBusy=true;\n'
    refresh+=' var labels=['+','.join('"<#WRDNS'+k+'#>"' for k in keys[:5])+'];\n'
    refresh+=' $j.ajax({url:"/update.cgi",data:{output:"wr_dns_process_state",arg0:"'+service+'"},dataType:"json",cache:false,timeout:5000})\n'
    refresh+=' .done(function(state){$j("#wr_dns_process_status").text(typeof state === "number" && labels[state] || labels[3]);})\n'
    refresh+=' .fail(function(){$j("#wr_dns_process_status").text(labels[3]);})\n'
    refresh+=' .always(function(){wrDNSBusy=false;});\n}\n'
    html = re.sub(r'(function initial\(\)\s*\{)', lambda m:refresh+m[1]+js+'\n window.setInterval(wrDNSRefresh,30000);\n', html, count=1)
    html = html.replace(table, '<div id="wr_dns_process_status" role="status"><#WRDNSUnknown#></div><p class="help-block"><#WRDNSNote#></p><button type="button" class="btn" onclick="wrDNSRefresh()"><#WRDNSRefresh#></button>\n' + table)
    changes.append((path, html))
labels = {
 'EN.footer':['Disabled; process not found','Process present; DNS not verified','Enabled; process not found','Process state unknown','Process present despite disabled setting','Process state refreshes every 30 seconds while this page is visible. DNS response and TLS validation require separate verification.','Refresh status'],
 'UK.dict':['Вимкнено; процес не знайдено','Процес запущений; DNS не перевірено','Увімкнено; процес не знайдено','Стан процесу невідомий','Процес запущений попри вимкнення','Стан процесу оновлюється раз на 30 секунд, коли сторінка видима. Відповідь DNS та перевірка TLS потребують окремого підтвердження.','Оновити стан'],
 'RU.dict':['Выключено; процесс не найден','Процесс запущен; DNS не проверен','Включено; процесс не найден','Состояние процесса неизвестно','Процесс запущен при выключенной настройке','Состояние процесса обновляется раз в 30 секунд, пока страница видима. Ответ DNS и проверка TLS требуют отдельного подтверждения.','Обновить состояние'],
}
for name, values in labels.items():
    path = root / 'www/dict' / name
    content = path.read_text(encoding='utf-8')
    if 'WRDNSUnknown=' in content:
        raise SystemExit('DNS process labels already present')
    changes.append((path, content.rstrip('\n')+'\n'+'\n'.join('WRDNS'+k+'='+v for k,v in zip(keys,values))+'\n'))
for path, content in changes:
    path.write_text(content, encoding='utf-8')
print('Prepared DNS process observation; functional DNS/TLS health remains unverified')
