#!/usr/bin/env python3
"""Translate the inherited WireGuard client labels without changing its fields."""
import argparse
from pathlib import Path
import re

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--verify-image', action='store_true')
a = p.parse_args()
root = a.source / ('trunk/romfs/www' if a.verify_image else 'trunk/user/www')
page = root / ('Advanced_wireguard.asp' if a.verify_image else 'n56u_ribbon_fixed/Advanced_wireguard.asp')
text = page.read_text(encoding='utf-8')
entries = [
    ('WireGuard 是一个易于配置、快速且安全的开源VPN', 'Description',
     'This is the legacy simplified WireGuard form. Choose WireGuard or AmneziaWG on the <a href="/vpncli.asp">VPN client and profiles page</a>. Changing an existing tunnel may disconnect it.',
     'Це стара спрощена форма WireGuard. Вибір WireGuard або AmneziaWG доступний на сторінці <a href="/vpncli.asp">VPN-клієнт і профілі</a>. Зміна чинного тунелю може розірвати з’єднання.',
     'Это старая упрощённая форма WireGuard. Выбор WireGuard или AmneziaWG доступен на странице <a href="/vpncli.asp">VPN-клиент и профили</a>. Изменение действующего туннеля может разорвать соединение.'),
    ('启用wireguard客户端', 'Enable',
     'Enable WireGuard client', 'Увімкнути клієнт WireGuard', 'Включить клиент WireGuard'),
    ('本机密钥key ', 'LocalKey',
     'Local private key', 'Локальний приватний ключ', 'Локальный приватный ключ'),
    ('本机IP（格式 10.0.0.2/24）', 'LocalIP',
     'Local IP address (e.g. 10.0.0.2/24)', 'Локальна IP-адреса (наприклад, 10.0.0.2/24)', 'Локальный IP-адрес (например, 10.0.0.2/24)'),
    ('对端密钥key ', 'PeerKey',
     'Peer public key', 'Публічний ключ вузла', 'Публичный ключ узла'),
    ('对端ip:端口（格式 223.5.6.6:4900)', 'Endpoint',
     'Peer IP address and port (e.g. 223.5.6.6:4900)', 'IP-адреса та порт вузла (наприклад, 223.5.6.6:4900)', 'IP-адрес и порт узла (например, 223.5.6.6:4900)'),
]
if a.verify_image:
    assert not re.search(r'[\u3400-\u9fff]', text), 'Untranslated WireGuard image text'
    for index, language in enumerate(('EN', 'UK', 'RU'), 2):
        dictionary = (root / (language + '.dict')).read_text(encoding='utf-8').splitlines()
        for entry in entries:
            key = 'WRWG_' + entry[1]
            assert text.count('<#' + key + '#>') == 1, 'Missing page label: ' + key
            values = [line.split('=', 1)[1] for line in dictionary if line.startswith(key + '=')]
            assert values == [entry[index]], 'Missing or changed translation: ' + language + '/' + key
    print('PASS WireGuard image labels and exact EN/UK/RU translations')
    raise SystemExit(0)
for original, suffix, *_ in entries:
    if text.count(original) != 1:
        raise SystemExit('WireGuard label anchor changed: ' + suffix)
    text = text.replace(original, '<#WRWG_' + suffix + '#>')
if re.search(r'[\u3400-\u9fff]', text):
    raise SystemExit('Unexpected untranslated WireGuard text; no files written')
changes = [(page, text)]
for index, name in enumerate(('EN.footer', 'UK.dict', 'RU.dict'), 2):
    path = root / 'dict' / name
    dictionary = path.read_text(encoding='utf-8')
    keys = {line.split('=', 1)[0] for line in dictionary.splitlines() if '=' in line}
    additions = []
    for entry in entries:
        key = 'WRWG_' + entry[1]
        if key in keys:
            raise SystemExit('WireGuard translation key already exists: ' + key)
        additions.append(key + '=' + entry[index])
    changes.append((path, dictionary.rstrip() + '\n' + '\n'.join(additions) + '\n'))
for path, content in changes:
    with path.open('w', encoding='utf-8', newline='\n') as stream:
        stream.write(content)
print('Localized six inherited WireGuard labels in EN/UK/RU; backend and fields unchanged')
