#!/usr/bin/env python3
"""Expose the forced wireless offload policy without changing saved mode values."""
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--verify-image', action='store_true')
a = p.parse_args()
labels = {
    'WRHNAT_Off': ('Disabled', 'Вимкнено', 'Выключено'),
    'WRHNAT_LegacyLAN': ('LAN offload (legacy setting; Wi-Fi offload disabled)',
                         'Прискорення LAN (старе налаштування; прискорення Wi-Fi вимкнено)',
                         'Ускорение LAN (старое значение; ускорение Wi-Fi выключено)'),
    'WRHNAT_LAN': ('LAN offload (Wi-Fi offload disabled)',
                  'Прискорення LAN (прискорення Wi-Fi вимкнено)',
                  'Ускорение LAN (ускорение Wi-Fi выключено)'),
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
    print('PASS forced-off WAN labels and EN/UK/RU dictionaries')
    raise SystemExit(0)
report = json.loads((a.source / 'wifi-hwnat-source.json').read_text())
if report.get('wireless_offload_disabled') is not True:
    raise SystemExit('WAN labels require an enforced wireless offload policy')
originals = ('Disable (Slow)', 'Offload TCP/UDP for LAN/WLAN', 'Offload TCP/UDP for LAN')
for original, key in zip(originals, labels):
    if text.count(original) != 1:
        raise SystemExit('WAN offload label anchor changed: ' + original)
    text = text.replace(original, '<#' + key + '#>')
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
print('WAN labels show wired offload policy; values 0/1/2 and NVRAM unchanged')
