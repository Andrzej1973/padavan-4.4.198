#!/usr/bin/env python3
"""Translate both inherited RSSI controls and their existing tooltip keys."""
import argparse
from pathlib import Path
import re

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
p.add_argument('--verify-image', action='store_true')
a = p.parse_args()
entries = [
    ('WLANConfig11b_KickStaRssiLow_itemname',
     'Disconnect clients below RSSI (dBm):',
     'Відключати клієнтів із сигналом нижче (дБм):',
     'Отключать клиентов с сигналом ниже (дБм):'),
    ('WLANConfig11b_KickStaRssiLow_itemdesc',
     '0 disables this threshold. A negative value (-100 to -1 dBm) lets the driver disconnect an already connected client when its signal falls below the threshold. For example, -80 dBm is weaker than -75 dBm. Measurement and delay depend on the driver. This does not guarantee reconnection to another band or access point; weak-signal and IoT clients may lose access.',
     '0 — поріг вимкнений. Від’ємне значення від -100 до -1 дБм дозволяє драйверу відключати вже підключеного клієнта, коли сигнал слабший за поріг. Наприклад, -80 дБм слабше за -75 дБм. Вимірювання та затримка залежать від драйвера. Перехід на інший діапазон або точку доступу не гарантований; віддалені пристрої та IoT можуть втратити зв’язок.',
     '0 — порог выключен. Отрицательное значение от -100 до -1 дБм позволяет драйверу отключать уже подключённого клиента при сигнале слабее порога. Например, -80 дБм слабее -75 дБм. Измерение и задержка зависят от драйвера. Переход на другой диапазон или точку доступа не гарантирован; удалённые устройства и IoT могут потерять связь.'),
    ('WLANConfig11b_AssocReqRssiThres_itemname',
     'Reject new connections below RSSI (dBm):',
     'Не підключати клієнтів із сигналом нижче (дБм):',
     'Не подключать клиентов с сигналом ниже (дБм):'),
    ('WLANConfig11b_AssocReqRssiThres_itemdesc',
     '0 disables this threshold. A negative value (-100 to -1 dBm) rejects new association requests with a signal below the threshold; it does not disconnect existing clients. More negative means weaker signal. An aggressive threshold can prevent distant clients from connecting. Leave both RSSI thresholds at 0 unless their effect has been checked with your clients.',
     '0 — поріг вимкнений. Від’ємне значення від -100 до -1 дБм відхиляє нові запити на підключення зі слабшим сигналом; уже підключених клієнтів цей поріг не відключає. Що більш від’ємне число, то слабший сигнал. Надто суворий поріг може завадити віддаленим пристроям підключитися. Залишайте обидва пороги 0, доки їхню дію не перевірено з вашими клієнтами.',
     '0 — порог выключен. Отрицательное значение от -100 до -1 дБм отклоняет новые запросы подключения с более слабым сигналом; уже подключённых клиентов этот порог не отключает. Чем отрицательнее число, тем слабее сигнал. Слишком строгий порог может помешать удалённым устройствам подключиться. Оставляйте оба порога 0 до проверки их действия с вашими клиентами.'),
]
root = a.source / ('trunk/romfs/www' if a.verify_image else 'trunk/user/www/dict')
changes = []
for column, name in enumerate(('EN.dict' if a.verify_image else 'EN.footer', 'UK.dict', 'RU.dict'), 1):
    path = root / name
    text = path.read_text(encoding='utf-8')
    for entry in entries:
        pattern = re.compile(r'^' + re.escape(entry[0]) + r'=[^\r\n]*', re.M)
        found = pattern.findall(text)
        if a.verify_image:
            if found != [entry[0] + '=' + entry[column]]:
                raise SystemExit('RSSI translation missing/changed: ' + name + '/' + entry[0])
        else:
            if len(found) > 1 or (column == 1 and not found):
                raise SystemExit('RSSI dictionary anchor mismatch: ' + name + '/' + entry[0])
            replacement = entry[0] + '=' + entry[column]
            text = pattern.sub(lambda _: replacement, text) if found else text.rstrip() + '\n' + replacement + '\n'
    changes.append((path, text))
if not a.verify_image:
    for path, text in changes:
        path.write_text(text, encoding='utf-8', newline='\n')
print('PASS RSSI control labels and tooltips in EN/UK/RU' + (' image' if a.verify_image else ' source'))
