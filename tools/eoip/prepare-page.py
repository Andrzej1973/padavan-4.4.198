#!/usr/bin/env python3
"""Install the read-only EoIP status page and localized navigation."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--config', type=Path, required=True)
a = p.parse_args()
if 'CONFIG_FIRMWARE_INCLUDE_EOIP=y' not in a.config.read_text().splitlines():
    raise SystemExit(0)
here = Path(__file__).resolve().parent
www = a.source / 'trunk/user/www'
pages = www / 'n56u_ribbon_fixed'
service = pages / 'Advanced_Services_Content.asp'
text = service.read_text()
anchor = '<div id="tabMenu" class="submenuBlock"></div>'
if text.count(anchor) != 1 or 'Advanced_Services_EoIP.asp' in text:
    raise SystemExit('EoIP service navigation anchor changed')
text = text.replace(anchor, anchor + '\n<p><a class="btn" href="/Advanced_Services_EoIP.asp"><#WREOIPTitle#></a></p>')
keys = ['Title', 'Slot', 'State', 'Index', 'Master', 'Unknown', 'Absent', 'Foreign', 'Up', 'Down', 'Note', 'ReadOnly', 'Refresh', 'Back']
labels = {
 'EN.footer': ['EoIP interface status', 'Slot', 'Observed interface state', 'Interface index', 'Bridge index', 'Data unavailable or stale', 'Interface absent', 'Name held by another interface', 'Administratively enabled', 'Administratively disabled', 'Interface state does not prove peer reachability, keepalive success or frame transfer. Refresh reads observations; it does not start or stop tunnels.', 'This page currently provides observations only. Profile editing is not yet connected. Refresh is manual after initial loading; first collection may take up to 20 seconds.', 'Refresh observations', 'Back to services'],
 'UK.dict': ['Стан інтерфейсів EoIP', 'Слот', 'Спостережений стан інтерфейсу', 'Індекс інтерфейсу', 'Індекс мосту', 'Дані недоступні або застарілі', 'Інтерфейс відсутній', 'Ім’я зайняте стороннім інтерфейсом', 'Адміністративно увімкнений', 'Адміністративно вимкнений', 'Стан інтерфейсу не підтверджує доступність вузла, успіх keepalive чи передавання кадрів. Оновлення лише читає стан і не запускає та не зупиняє тунелі.', 'Сторінка наразі лише показує спостереження. Редагування профілів ще не підключене. Після початкового завантаження оновлення ручне; перший збір може тривати до 20 секунд.', 'Оновити спостереження', 'Назад до служб'],
 'RU.dict': ['Состояние интерфейсов EoIP', 'Слот', 'Наблюдаемое состояние интерфейса', 'Индекс интерфейса', 'Индекс моста', 'Данные недоступны или устарели', 'Интерфейс отсутствует', 'Имя занято сторонним интерфейсом', 'Административно включён', 'Административно выключен', 'Состояние интерфейса не подтверждает доступность узла, успех keepalive или передачу кадров. Обновление только читает состояние и не запускает и не останавливает туннели.', 'Страница пока только показывает наблюдения. Редактирование профилей ещё не подключено. После начальной загрузки обновление ручное; первый сбор может занять до 20 секунд.', 'Обновить наблюдения', 'Назад к службам'],
}
pending = [(service, text), (pages / 'Advanced_Services_EoIP.asp', (here / 'status-page.asp').read_text())]
for name, values in labels.items():
    path = www / 'dict' / name
    content = path.read_text()
    if 'WREOIPTitle=' in content:
        raise SystemExit('EoIP labels already present')
    pending.append((path, content.rstrip('\n') + '\n' + '\n'.join('WREOIP' + key + '=' + value for key, value in zip(keys, values)) + '\n'))
# This directory is part of the base web asset tree and its existing ROMFS rule.
asset = pages / 'bootstrap/js/wr-eoip-status.js'
if not asset.parent.is_dir():
    raise SystemExit('EoIP bootstrap asset directory missing')
pending.append((asset, (here / 'status-view.js').read_text()))
for path, content in pending:
    path.write_text(content)
print('Prepared EoIP read-only page, manual refresh and EN/UK/RU labels')
