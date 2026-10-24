#!/usr/bin/env python3
"""Prepare Classic IoT navigation locally; activation backend is still pending.

Deliberately not wired into the firmware workflow until production activation
and authenticated Apply are available. No duplicate settings writer is added.
"""
import argparse
import hashlib
import json
from pathlib import Path


def prepare(source):
    root = source / 'trunk/user/www'
    web = root / 'n56u_ribbon_fixed'
    assets = Path(__file__).parent
    changes = {}
    state = web / 'state.js'
    original = state.read_text(encoding='utf-8')
    if 'classic-iot-navigation.js' in original:
        raise ValueError('Classic IoT navigation already installed')
    if original.count('function show_banner(') != 1:
        raise ValueError('Classic shared banner changed')
    # Load from state.js so all Classic pages with the banner get the same link.
    # The asset handles both pre-load and post-load arrival, without document.write.
    changes[state] = original + '''
// WR Classic IoT navigation: no configuration changes.
(function () {
 var s = document.createElement('script');
 s.src = '/classic-iot-navigation.js'; s.async = false;
 document.getElementsByTagName('head')[0].appendChild(s);
}());
'''
    for suffix in ('router.asp', 'router2g.asp'):
        path = web / 'device-map' / suffix
        text = path.read_text(encoding='utf-8')
        anchor = '<ul class="nav nav-tabs">'
        if text.count(anchor) != 1 or 'Advanced_IoT_Content.asp' in text:
            raise ValueError('Classic map radio tabs changed: ' + suffix)
        end = text.index('</ul>', text.index(anchor))
        changes[path] = text[:end] + '<li><a href="/Advanced_IoT_Content.asp" target="_top">IoT</a></li>\n' + text[end:]
    pages = []
    for stem in ('Wireless', 'WGuest', 'WMode', 'ACL', 'WSecurity', 'WAdvanced'):
        for band in ('2g', ''):
            name = 'Advanced_' + stem + band + '_Content.asp'
            text = (web / name).read_text(encoding='utf-8')
            if text.count('id="tabMenu"') != 1 or '/state.js' not in text:
                raise ValueError('Classic Wi-Fi page structure changed: ' + name)
            pages.append(name)
    labels = {
        'EN.footer': 'IoT activation is not yet integrated in this firmware. Settings and isolation are not available; the main and guest networks are unchanged.',
        'UK.dict': 'Активацію IoT ще не інтегровано в цю прошивку. Налаштування та ізоляція поки недоступні; основні й гостьові мережі не змінено.',
        'RU.dict': 'Активация IoT ещё не интегрирована в эту прошивку. Настройки и изоляция пока недоступны; основные и гостевые сети не изменены.'
    }
    for name, label in labels.items():
        path = root / 'dict' / name
        text = path.read_text(encoding='utf-8')
        if 'WR_IOT_CLASSIC_Pending=' in text:
            raise ValueError('IoT Classic dictionary key already exists')
        changes[path] = text.rstrip('\n') + '\nWR_IOT_CLASSIC_Pending=' + label + '\n'
    for name, filename in [('classic-iot-navigation.js', 'classic-navigation.js'),
                           ('Advanced_IoT_Content.asp', 'classic-pending.asp')]:
        path = web / name
        if path.exists():
            raise ValueError('Refusing to overwrite existing IoT asset: ' + name)
        changes[path] = (assets / filename).read_text(encoding='utf-8')
    # Validate everything before the first write; keep all existing forms intact.
    for path, text in changes.items():
        path.write_bytes(text.encode('utf-8'))
    report = {'classic_only': True, 'production_activation': False,
              'authenticated_apply': False, 'runtime_verified': False,
              'wifi_pages': pages, 'new_theme': False,
              'files': {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest() for p in changes}}
    (source / 'iot-classic-navigation.json').write_bytes((json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    result = prepare(args.source)
    print('Prepared Classic navigation for', len(result['wifi_pages']), 'Wi-Fi pages; production IoT activation remains pending')
