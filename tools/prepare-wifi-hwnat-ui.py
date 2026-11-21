#!/usr/bin/env python3
"""Localize the manually selectable wired/Wi-Fi hardware offload modes."""
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--verify-image', action='store_true')
a = p.parse_args()
labels = {
    'WRHNAT_Off': ('Disabled', 'Вимкнено', 'Выключено'),
    'WRHNAT_LegacyLAN': ('Compatible mode (LAN/Wi-Fi)',
                         'Сумісний режим (LAN/Wi-Fi)',
                         'Совместимый режим (LAN/Wi-Fi)'),
    'WRHNAT_LAN': ('LAN only', 'Лише LAN', 'Только LAN'),
    'WRHNAT_WiFiOff': ('Select Compatible mode to try Wi-Fi hardware offload. If Wi-Fi becomes unstable or router load increases, switch back to LAN only.',
                       'Виберіть «Сумісний режим», щоб випробувати апаратне прискорення Wi-Fi. Якщо Wi-Fi стане нестабільним або зросте навантаження на роутер, поверніть «Лише LAN».',
                       'Выберите «Совместимый режим», чтобы проверить аппаратное ускорение Wi-Fi. Если Wi-Fi станет нестабильным или возрастёт нагрузка на роутер, верните «Только LAN».'),
}
root = a.source / ('trunk/romfs/www' if a.verify_image else 'trunk/user/www')
page = root / ('Advanced_WAN_Content.asp' if a.verify_image else 'n56u_ribbon_fixed/Advanced_WAN_Content.asp')
text = page.read_text(encoding='utf-8')
if a.verify_image:
    for index, language in enumerate(('EN', 'UK', 'RU')):
        lines = (root / (language + '.dict')).read_text(encoding='utf-8').splitlines()
        for key, translations in labels.items():
            assert text.count('<#' + key + '#>') == 1, key
            assert [line for line in lines if line.startswith(key + '=')] == [key + '=' + translations[index]], language + '/' + key
    assert 'Offload TCP/UDP for LAN/WLAN' not in text
    assert text.count('<#WRHNAT_WiFiOff#>') == 1
    print('PASS concise WAN offload labels, single Wi-Fi note, and EN/UK/RU dictionaries')
    raise SystemExit(0)
report = json.loads((a.source / 'wifi-hwnat-source.json').read_text())
if report.get('wireless_offload_user_selectable') is not True or report.get('factory_lan_only') is not True:
    raise SystemExit('WAN labels require manual Wi-Fi selection and the LAN-only factory default')
originals = ('Disable (Slow)', 'Offload TCP/UDP for LAN/WLAN', 'Offload TCP/UDP for LAN')
for original, key in zip(originals, labels):
    if text.count(original) != 1:
        raise SystemExit('WAN offload label anchor changed: ' + original)
    text = text.replace(original, '<#' + key + '#>')
row_start = text.find('<tr id="row_hwnat">')
row_end = text.find('</tr>', row_start)
if row_start < 0 or row_end < 0:
    raise SystemExit('WAN hardware offload row anchor changed')
row = text[row_start:row_end]
if row.count('</select>') != 1 or 'WRHNAT_WiFiOff' in row:
    raise SystemExit('WAN hardware offload selector anchor changed')
row = row.replace('</select>', '</select>\n                                                <p class="help-block"><#WRHNAT_WiFiOff#></p>', 1)
text = text[:row_start] + row + text[row_end:]
changes = [(page, text)]
for index, name in enumerate(('EN.footer', 'UK.dict', 'RU.dict')):
    path = root / 'dict' / name
    dictionary = path.read_text(encoding='utf-8')
    keys = {line.split('=', 1)[0] for line in dictionary.splitlines()}
    if keys.intersection(labels):
        raise SystemExit('WAN translation keys already exist')
    changes.append((path, dictionary.rstrip() + '\n' + '\n'.join(key + '=' + values[index] for key, values in labels.items()) + '\n'))
for path, content in changes:
    with path.open('w', encoding='utf-8', newline='\n') as stream:
        stream.write(content)
print('WAN labels distinguish the legacy value from LAN-only offload; Wi-Fi note appears once. Values 0/1/2 and NVRAM are unchanged.')
