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
#include "wr-doh-instances.h"
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
 active = pids(process);
 if (active < 0) return websWrite(wp, "3");
 active = active > 0; requested = nvram_get_int(key) > 0;
 return websWrite(wp, "%d", active ? (requested ? 1 : 4) : (requested ? 2 : 0));
}
static int ej_wr_doh_instance_state(int eid, webs_t wp, int argc, char **argv)
{
 struct wr_doh_instances observed;unsigned configured=0,i;char key[24];int requested,active,state;
 (void)eid;(void)argv;
 if(argc!=0)return websWrite(wp,"{\"error\":\"invalid_request\"}");
 for(i=0;i<4;i++){
  snprintf(key,sizeof(key),"doh_server%u",i);
  if(*nvram_safe_get(key))configured|=1U<<i;
 }
 requested=nvram_get_int("doh_enable")>0;
 if(access("/proc/self/stat",R_OK)){
  memset(&observed,0,sizeof(observed));observed.configured=configured;observed.unknown=15;state=3;
 }else{
  observed=wr_doh_observe(configured,"/var/run/doh-proxy","/proc");
  active=pids("https_dns_proxy");state=active<0?3:active?(requested?1:4):(requested?2:0);
 }
 return websWrite(wp,"{\"state\":%d,\"requested\":%d,\"configuredMask\":%u,\"ownedMask\":%u,\"unknownMask\":%u,\"duplicateMask\":%u}",
                  state,requested,observed.configured,observed.owned,observed.unknown,observed.duplicate);
}
'''
changes = [(path, s.replace(anchor, code + '\n' + anchor).replace(entry, entry + '\t{ "wr_dns_process_state", ej_wr_dns_process_state},\n\t{ "wr_doh_instance_state", ej_wr_doh_instance_state},\n'))]
changes.append((root/'httpd/wr-doh-instances.h',Path(__file__).with_name('doh-instance-status.h').read_text(encoding='utf-8')))
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
    if service=='doh':
        renderer=Path(__file__).with_name('doh-instance-view.js').read_text(encoding='utf-8')
        refresh=refresh.replace('var wrDNSBusy=false;', 'var wrDNSBusy=false;\n'+renderer)
        refresh=refresh.replace('data:{output:"wr_dns_process_state",arg0:"doh"}', 'data:{output:"wr_doh_instance_state"}')
        refresh=refresh.replace('$j("#wr_dns_process_status").text(typeof state === "number" && labels[state] || labels[3]);','wrDoHRender(state);')
        refresh=refresh.replace('$j("#wr_dns_process_status").text(labels[3]);','wrDoHRender(null);')
        js='\n wrDoHRender(<% wr_doh_instance_state(); %>);\n'
    # Route initial and AJAX observations through the same bounded lifetime.
    if service=='doh':
        refresh=refresh.replace('wrDoHRender(state);','wrDNSRender(state);').replace('wrDoHRender(null);','wrDNSRender(null);')
        js='\n wrDNSRender(<% wr_doh_instance_state(); %>);\n'
        display='wrDoHRender(value);'
    else:
        refresh=refresh.replace('$j("#wr_dns_process_status").text(typeof state === "number" && labels[state] || labels[3]);','wrDNSRender(state);')
        refresh=refresh.replace('$j("#wr_dns_process_status").text(labels[3]);','wrDNSRender(null);')
        js='\n wrDNSRender(<% wr_dns_process_state("stubby"); %>);\n'
        display='var labels=['+','.join('"<#WRDNS'+k+'#>"' for k in keys[:5])+'];\n'
        display+='var valid=typeof value==="number" && Math.floor(value)===value && value>=0 && value<5;\n$j("#wr_dns_process_status").text(valid ? labels[value] : labels[3]);'
    refresh+='\nvar wrDNSGeneration=0,wrDNSSampledAt=0;\nfunction wrDNSRender(value){\n'
    refresh+=' var generation=++wrDNSGeneration;wrDNSSampledAt=0;\n'+display+'\n'
    refresh+=' if(value!==null && value!==undefined){wrDNSSampledAt=Date.now();window.setTimeout(function(){if(generation===wrDNSGeneration)wrDNSRender(null);},45000);}\n}\n'
    refresh+='document.addEventListener("visibilitychange",function(){if(!document.hidden && wrDNSSampledAt && Date.now()-wrDNSSampledAt>=45000)wrDNSRender(null);});\n'
    html = re.sub(r'(function initial\(\)\s*\{)', lambda m:refresh+m[1]+js+'\n window.setInterval(wrDNSRefresh,30000);\n', html, count=1)
    html = html.replace(table, '<div id="wr_dns_process_status" role="status"><#WRDNSUnknown#></div><p class="help-block"><#WRDNSNote#></p><button type="button" class="btn" onclick="wrDNSRefresh()"><#WRDNSRefresh#></button>\n' + table)
    if service=='doh':
        html=html.replace('<div id="wr_dns_process_status"', '<div id="wr_doh_instances" role="status"><#WRDNSUnknown#></div><p class="help-block"><#WRDNSInstanceNote#></p><div id="wr_dns_process_status"',1)
    changes.append((path, html))
labels = {
 'EN.footer':['Disabled; process not found','Process present; DNS not verified','Enabled; process not found','Process state unknown','Process present despite disabled setting','Process state refreshes every 30 seconds while this page is visible. DNS response and TLS validation require separate verification.','Refresh status'],
 'UK.dict':['Вимкнено; процес не знайдено','Процес запущений; DNS не перевірено','Увімкнено; процес не знайдено','Стан процесу невідомий','Процес запущений попри вимкнення','Стан процесу оновлюється раз на 30 секунд, коли сторінка видима. Відповідь DNS та перевірка TLS потребують окремого підтвердження.','Оновити стан'],
 'RU.dict':['Выключено; процесс не найден','Процесс запущен; DNS не проверен','Включено; процесс не найден','Состояние процесса неизвестно','Процесс запущен при выключенной настройке','Состояние процесса обновляется раз в 30 секунд, пока страница видима. Ответ DNS и проверка TLS требуют отдельного подтверждения.','Обновить состояние'],
}
instance_keys=['NoSlots','ConfiguredSlots','OwnedSlots','MissingSlots','UnknownSlots','UnexpectedSlots','DuplicateSlots','InstanceNote']
instance_labels={
 'EN.footer':['none','Configured slots','Slots with verified process ownership','Configured slots without a confirmed process','Unverified slots','Processes in unconfigured slots','Duplicate PID slots','PID-file and executable ownership only; listener, resolver profile and DNS/TLS functionality are not verified. Slot numbers match resolver fields 1–4.'],
 'UK.dict':['немає','Налаштовані слоти','Слоти з підтвердженою належністю процесу','Налаштовані слоти без підтвердженого процесу','Неперевірені слоти','Процеси в неналаштованих слотах','Слоти з повторним PID','Перевіряються лише PID-файл і виконуваний файл процесу; порт, профіль резолвера та робота DNS/TLS не перевірені. Номери слотів відповідають полям резолверів 1–4.'],
 'RU.dict':['нет','Настроенные слоты','Слоты с подтверждённой принадлежностью процесса','Настроенные слоты без подтверждённого процесса','Непроверенные слоты','Процессы в ненастроенных слотах','Слоты с повторным PID','Проверяются только PID-файл и исполняемый файл процесса; порт, профиль резолвера и работа DNS/TLS не проверены. Номера слотов соответствуют полям резолверов 1–4.'],
}
keys+=instance_keys
for name in labels:labels[name]+=instance_labels[name]
for name, values in labels.items():
    path = root / 'www/dict' / name
    content = path.read_text(encoding='utf-8')
    if 'WRDNSUnknown=' in content:
        raise SystemExit('DNS process labels already present')
    changes.append((path, content.rstrip('\n')+'\n'+'\n'.join('WRDNS'+k+'='+v for k,v in zip(keys,values))+'\n'))
for path, content in changes:
    path.write_text(content, encoding='utf-8')
print('Prepared DNS process observation; functional DNS/TLS health remains unverified')
