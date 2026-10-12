#!/usr/bin/env python3
"""Expose observed ZRAM swap state without changing requested configuration."""
import argparse
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
if html.count(init) != 1 or html.count(select) != 1:
    raise SystemExit('ZRAM page anchors changed')
labels = ['Off', 'Active', 'Failed', 'Unknown', 'StillActive']
html = html.replace(init, init + '\n\tvar zs = <% wr_zram_state(); %>;\n\tvar zl = [' + ','.join('"<#WRZram' + x + '#>"' for x in labels) + '];\n\t$j("#wr_zram_status").text(zl[zs] || zl[3]);')
html = html.replace(select, '<div id="wr_zram_status" role="status"><#WRZramUnknown#></div>\n                                                ' + select)
translations = {
 'EN.footer': ['Disabled', 'Working: swap active', 'Not working: swap inactive', 'State unknown', 'Still working despite disabled setting'],
 'UK.dict': ['Вимкнено', 'Працює: swap активний', 'Не працює: swap не активний', 'Стан невідомий', 'Ще працює попри вимкнення в налаштуваннях'],
 'RU.dict': ['Выключено', 'Работает: swap активен', 'Не работает: swap не активен', 'Состояние неизвестно', 'Ещё работает при выключенной настройке'],
}
changes = [(web, updated), (page, html)]
for filename, values in translations.items():
    path = root / 'www/dict' / filename
    content = path.read_text(encoding='utf-8')
    if 'WRZramUnknown=' in content:
        raise SystemExit('ZRAM labels already present')
    changes.append((path, content.rstrip('\n') + '\n' + '\n'.join('WRZram' + key + '=' + value for key, value in zip(labels, values)) + '\n'))
for path, content in changes:
    path.write_text(content, encoding='utf-8')
print('Prepared observed ZRAM page state; refreshed on page load, runtime unverified')
