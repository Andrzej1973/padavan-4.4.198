#!/usr/bin/env python3
"""Observe fixed WG interfaces without claiming peer connectivity."""
import argparse
import re
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
a = p.parse_args()
root = a.source / 'trunk/user'
web = root / 'httpd/web_ex.c'
text = web.read_text(encoding='utf-8')
anchor = 'struct ej_handler ej_handlers[] =\n'
entry = '\t{ "json_system_status", ej_system_status_hook},\n'
if text.count(anchor)!=1 or text.count(entry)!=1 or 'ej_wr_vpn_interface_state' in text:
    raise SystemExit('VPN interface handler anchors changed')
code = r'''
#include <errno.h>
/* 0 disabled/absent, 1 interface UP, 2 enabled/absent, 3 unknown,
 * 4 interface UP despite disabled setting, 5 interface present but DOWN. */
static int ej_wr_vpn_interface_state(int eid, webs_t wp, int argc, char **argv)
{
 const char *path, *key; FILE *fp; unsigned long flags; char extra;
 int requested, state=3;
 (void)eid;
 if(argc!=1 || !argv || !argv[0]) return websWrite(wp,"3");
 if(!strcmp(argv[0],"client")){path="/sys/class/net/wg0/flags";key="vpnc_enable";}
 else if(!strcmp(argv[0],"server")){path="/sys/class/net/wg1/flags";key="vpns_enable";}
 else return websWrite(wp,"3");
 if(access("/sys/class/net",R_OK)) return websWrite(wp,"3");
 requested=nvram_get_int(key)>0;
 fp=fopen(path,"r");
 if(!fp){if(errno==ENOENT)state=requested?2:0;}
 else {
  if(fscanf(fp,"%lx %c",&flags,&extra)==1 && !ferror(fp))
   state=(flags&1)?(requested?1:4):5;
  if(fclose(fp))state=3;
 }
 return websWrite(wp,"%d",state);
}
'''
changes=[(web,text.replace(anchor,code+'\n'+anchor).replace(entry,entry+'\t{ "wr_vpn_interface_state", ej_wr_vpn_interface_state},\n'))]
keys=['Off','Up','Missing','Unknown','StillUp','Down','Note','Controller']
for page,role,kind in [('vpncli.asp','client','vpnc'),('vpnsrv.asp','server','vpns')]:
    path=root/'www/n56u_ribbon_fixed'/page
    html=path.read_text(encoding='utf-8')
    table='<table class="table" id="'+('tbl_vpnc_config' if role=='client' else 'tbl_vpn_config')+'"'
    if html.count(table)!=1 or len(re.findall(r'function initial\(\)\s*\{',html))!=1:
        raise SystemExit('VPN page anchors changed: '+page)
    js='\n var vs = <% wr_vpn_interface_state("'+role+'"); %>;\n var vl = ['+','.join('"<#WRVPN'+k+'#>"' for k in keys[:6])+'];\n $j("#wr_vpn_interface_status").text(vl[vs] || vl[3]);\n $j("#wr_vpn_observation").toggle(document.form.'+kind+'_type.value == "3");\n'
    html=re.sub(r'(function initial\(\)\s*\{)',lambda m:m[1]+js,html,count=1)
    html=html.replace(table,'<div id="wr_vpn_observation"><div id="wr_vpn_interface_status" role="status"><#WRVPNUnknown#></div><p class="help-block"><#WRVPNNote#></p></div>\n'+table)
    if role=='client':
        old='$("col_vpnc_wg_state").innerHTML = \'<#Connected#>\';'
        oldclass="$('col_vpnc_wg_state').setAttribute('class', 'label label-success');"
        if html.count(old)!=1 or html.count(oldclass)!=1:
            raise SystemExit('VPN cached-controller label changed')
        html=html.replace(old,'$("col_vpnc_wg_state").innerHTML = \'<#WRVPNController#> <#Connected#>\';').replace(oldclass,oldclass.replace('label-success','label-info'))
    changes.append((path,html))
labels={
 'EN.footer':['Disabled; interface absent','Interface UP; peer link not verified','Enabled; interface absent','Interface state unknown','Interface UP despite disabled setting','Interface present but DOWN','Observed on page load. Interface UP does not prove a handshake or working routes.','Last controller state:'],
 'UK.dict':['Вимкнено; інтерфейс відсутній','Інтерфейс увімкнений; зв’язок із вузлом не перевірено','Увімкнено; інтерфейс відсутній','Стан інтерфейсу невідомий','Інтерфейс увімкнений попри вимкнення','Інтерфейс існує, але вимкнений','Стан на момент відкриття сторінки. Увімкнений інтерфейс не підтверджує handshake або роботу маршрутів.','Останній стан контролера:'],
 'RU.dict':['Выключено; интерфейс отсутствует','Интерфейс включён; связь с узлом не проверена','Включено; интерфейс отсутствует','Состояние интерфейса неизвестно','Интерфейс включён при выключенной настройке','Интерфейс существует, но выключен','Состояние при открытии страницы. Включённый интерфейс не подтверждает handshake или работу маршрутов.','Последнее состояние контроллера:'],
}
for name,values in labels.items():
    path=root/'www/dict'/name
    content=path.read_text(encoding='utf-8')
    if 'WRVPNUnknown=' in content:raise SystemExit('VPN labels already present')
    changes.append((path,content.rstrip('\n')+'\n'+'\n'.join('WRVPN'+k+'='+v for k,v in zip(keys,values))+'\n'))
for path,content in changes:path.write_text(content,encoding='utf-8')
print('Prepared VPN interface observation; peer handshake and routes remain unverified')
