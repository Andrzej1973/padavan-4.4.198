#!/usr/bin/env python3
"""Connect one requested steering switch to the existing Wi-Fi apply event.

This is the settings control only. Fresh runtime status reporting is a separate
requirement; an enabled selection must not be presented as proven running.
"""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
root = p.parse_args().source / 'trunk/user'
paths = [root/'httpd/Makefile', root/'httpd/variables.c', root/'httpd/web_ex.c',
         root/'www/n56u_ribbon_fixed/Advanced_WAdvanced2g_Content.asp']
make, variables, caps, page = [f.read_text(encoding='utf-8') for f in paths]
make_anchor = 'CFLAGS += -Wall -I. -I$(SHDIR) -I$(SHDIR)/include\n'
var_anchor = '{"rt_band_steering", "", NULL, EVM_RESTART_WIFI2},'
cap_anchor = '\twebsWrite(wp,\n\t\t"function found_utl_hdparm()'
start = '<tr id="row_band_steering" style="display:none">'
if (make.count(make_anchor) != 1 or variables.count(var_anchor) != 1 or
    caps.count(cap_anchor) != 1 or page.count(start) != 1 or
    any('APP_WR_BAND_STEERING' in text for text in (make, variables, caps))):
    raise ValueError('Web control source anchors changed; no files written')
begin = page.index(start)
end = page.index('</tr>', begin)+len('</tr>')
row = page[begin:end]
if row.count('rt_band_steering') != 3:
    raise ValueError('Expected pinned 2G steering control; no files written')
row = row.replace('rt_band_steering', 'wr_bs_enable')
old_label = '<a class="help_tooltip" href="javascript:void(0);" onmouseover="openTooltip(this, 3, 20);"><#WLANConfig11n_band_steering_itemname#></a>'
if row.count(old_label) != 1:
    raise ValueError('Steering label changed; no files written')
row = row.replace(old_label, '<#WR_BS_Title#>')
row = row.replace('</select>', '</select>\n'
    '                                              <p class="help-block"><#WR_BS_Help#></p>')
page = page[:begin]+row+page[end:]
make = make.replace(make_anchor, make_anchor+
    'ifeq ($(CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING),y)\n'
    'CFLAGS += -DAPP_WR_BAND_STEERING\nendif\n')
variables = variables.replace(var_anchor, var_anchor+
    '\n#ifdef APP_WR_BAND_STEERING\n'
    '\t\t\t{"wr_bs_enable", "", NULL, EVM_RESTART_WIFI2},\n#endif')
caps = caps.replace(cap_anchor,
    '#ifdef APP_WR_BAND_STEERING\n'
    '\t/* One coordinated control on the 2G settings page; hide legacy 5G. */\n'
    '\thas_2g_band_steering = 1;\n\thas_5g_band_steering = 0;\n#endif\n'+cap_anchor)
translations = {
    'EN.footer': ('Band Steering (2.4 GHz + 5 GHz)',
                  'Requested setting. Use the same SSID and security on both bands. Disabled by default; client roaming behavior varies.'),
    'UK.dict': ('Band Steering (2,4 ГГц + 5 ГГц)',
                'Бажане налаштування. Використовуйте однакові SSID і захист в обох діапазонах. Типово вимкнено; поведінка клієнтів під час роумінгу може відрізнятися.'),
    'RU.dict': ('Band Steering (2,4 ГГц + 5 ГГц)',
                'Желаемая настройка. Используйте одинаковые SSID и защиту в обоих диапазонах. По умолчанию отключено; поведение клиентов при роуминге может различаться.'),
}
dictionary_changes = []
for name, (title, help_text) in translations.items():
    path = root/'www/dict'/name
    text = path.read_text(encoding='utf-8')
    if 'WR_BS_Title=' in text or 'WR_BS_Help=' in text:
        raise ValueError('Steering dictionary keys already present; no files written')
    dictionary_changes.append((path, text.rstrip('\n')+'\nWR_BS_Title='+title+'\nWR_BS_Help='+help_text+'\n'))
for path, text in list(zip(paths, (make, variables, caps, page)))+dictionary_changes:
    path.write_text(text, encoding='utf-8')
print('Prepared one requested dual-band switch; fresh runtime status remains separate')
