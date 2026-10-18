#!/usr/bin/env python3
"""Expose observed ZRAM swap state without changing requested configuration."""
import argparse
import re
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
a = p.parse_args()
root = a.source / 'trunk/user'
web = root / 'httpd/web_ex.c'
s = web.read_text(encoding='utf-8')
anchor = 'struct ej_handler ej_handlers[] =\n'
entry = '\t{ "json_system_status", ej_system_status_hook},\n'
if s.count(anchor) != 1 or s.count(entry) != 1 or 'ej_wr_zram_state' in s:
    raise SystemExit('ZRAM status handler anchors changed')
code = r'''
/* 0 off, 1 active, 2 requested but inactive, 3 unknown, 4 active despite off. */
static int ej_wr_zram_state(int eid, webs_t wp, int argc, char **argv)
{
 int state = 3;
 (void)eid; (void)argc; (void)argv;
#if defined(SUPPORT_ZRAM)
 FILE *fp = fopen("/proc/swaps", "r");
 char line[512], device[128];
 int active = 0, rows = 0, failed = 0;
 if (fp) {
  while (fgets(line, sizeof(line), fp)) {
   if (++rows > 256 || !strchr(line, '\n')) { failed = 1; break; }
   if (sscanf(line, "%127s", device) != 1) { failed = 1; break; }
   if (rows == 1) {
    if (strcmp(device, "Filename")) failed = 1;
    if (failed) break;
   } else if (!strcmp(device, "/dev/zram0")) active = 1;
  }
  if (ferror(fp)) failed = 1;
  if (fclose(fp)) failed = 1;
  if (!failed && rows) {
   int requested = nvram_get_int("zram_enable") > 0;
   state = active ? (requested ? 1 : 4) : (requested ? 2 : 0);
  }
 }
#endif
 return websWrite(wp, "%d", state);
}
'''
updated = s.replace(anchor, code + '\n' + anchor).replace(entry, entry + '\t{ "wr_zram_state", ej_wr_zram_state},\n')
page = root / 'www/n56u_ribbon_fixed/Advanced_System_Content.asp'
html = page.read_text(encoding='utf-8')
init = '\tif (!found_support_zram()) showhide_div("row_zram", 0);'
select = '<select name="zram_enable" class="input">'
if html.count(init) != 1 or html.count(select) != 1 or len(re.findall(r'function initial\(\)\s*\{',html))!=1:
    raise SystemExit('ZRAM page anchors changed')
labels = ['Off', 'Active', 'Failed', 'Unknown', 'StillActive']
refresh='\nvar wrZramBusy=false;\nvar wrZramGeneration=0,wrZramSampledAt=0;\n'
refresh+='function wrZramRender(state){\n var generation=++wrZramGeneration;wrZramSampledAt=0;\n'
refresh+=' var labels=['+','.join('"<#WRZram'+x+'#>"' for x in labels)+'];\n'
refresh+=' var valid=typeof state === "number" && Math.floor(state)===state && state>=0 && state<5;\n'
refresh+=' $j("#wr_zram_status").text(valid ? labels[state] : labels[3]);\n'
refresh+=' if(valid && state!==3){wrZramSampledAt=Date.now();window.setTimeout(function(){if(generation===wrZramGeneration)wrZramRender(null);},45000);}\n}\n'
refresh+='document.addEventListener("visibilitychange",function(){if(!document.hidden && wrZramSampledAt && Date.now()-wrZramSampledAt>=45000)wrZramRender(null);});\n'
refresh+='function wrZramRefresh(){\n'
refresh+=' if(wrZramBusy || document.hidden || !found_support_zram())return;\n wrZramBusy=true;\n'
refresh+=' var labels=['+','.join('"<#WRZram'+x+'#>"' for x in labels)+'];\n'
refresh+=' $j.ajax({url:"/update.cgi",data:{output:"wr_zram_state"},dataType:"json",cache:false,timeout:5000})\n'
refresh+=' .done(function(state){wrZramRender(state);})\n'
refresh+=' .fail(function(){wrZramRender(null);})\n'
refresh+=' .always(function(){wrZramBusy=false;});\n}\n'
html=re.sub(r'(function initial\(\)\s*\{)',lambda m:refresh+m[1],html,count=1)
html = html.replace(init, init + '\n\twrZramRender(<% wr_zram_state(); %>);\n\tif(found_support_zram()) window.setInterval(wrZramRefresh,30000);')
html = html.replace(select, '<div id="wr_zram_status" role="status"><#WRZramUnknown#></div><button type="button" class="btn" onclick="wrZramRefresh()"><#WRZramRefresh#></button>\n                                                ' + select)
translations = {
 'EN.footer': ['Disabled', 'Working: swap active', 'Not working: swap inactive', 'State unknown', 'Still working despite disabled setting'],
 'UK.dict': ['Вимкнено', 'Працює: swap активний', 'Не працює: swap не активний', 'Стан невідомий', 'Ще працює попри вимкнення в налаштуваннях'],
 'RU.dict': ['Выключено', 'Работает: swap активен', 'Не работает: swap не активен', 'Состояние неизвестно', 'Ещё работает при выключенной настройке'],
}
changes = [(web, updated), (page, html)]
refresh_labels={'EN.footer':'Refresh status','UK.dict':'Оновити стан','RU.dict':'Обновить состояние'}
for filename, values in translations.items():
    path = root / 'www/dict' / filename
    content = path.read_text(encoding='utf-8')
    if 'WRZramUnknown=' in content:
        raise SystemExit('ZRAM labels already present')
    changes.append((path, content.rstrip('\n') + '\n' + '\n'.join('WRZram' + key + '=' + value for key, value in zip(labels, values)) + '\nWRZramRefresh='+refresh_labels[filename]+'\n'))
for path, content in changes:
    path.write_text(content, encoding='utf-8')
print('Prepared observed ZRAM page state with manual/visible-page refresh; runtime unverified')
