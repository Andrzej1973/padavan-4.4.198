#!/usr/bin/env python3
"""Install EoIP observations, settings editor and localized navigation."""
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
editor_keys = ['Settings','MasterEnable','Enable','Autostart','Local','Remote','ID','Keepalive','Retries','Bridge','Confirm','Save','Disable','Reload','Unavailable','Loading','Loaded','Saving','Saved','Rejected','Uncertain']
editor_labels = {
 'EN.footer': ['Stored EoIP settings','Enable EoIP service','Enable slot','Start slot at boot','Local IPv4 (0.0.0.0 = automatic)','Remote IPv4','Tunnel ID (0–65535)','Keepalive interval (seconds, 0 = off)','Keepalive retries','Bridge (empty = no bridge)','I confirm applying these EoIP changes; existing EoIP tunnels may disconnect.','Save to RAM and request Apply','Disable all EoIP','Reload stored values','Settings unavailable. Reload or use Disable when the confirmation and token are available.','Reading stored settings…','Stored values loaded. These do not describe actual tunnel health.','Saving request…','Saved in RAM; Apply requested. Check observed interfaces and remote traffic. Use the standard Padavan settings save separately for flash persistence.','Save or Apply was not confirmed. Reload stored values and check parameters and observed state.','Response unavailable; the request may have been processed. Check stored and observed state before repeating.'],
 'UK.dict': ['Збережені налаштування EoIP','Увімкнути службу EoIP','Увімкнути слот','Запускати слот при завантаженні','Локальна IPv4 (0.0.0.0 = автоматично)','Віддалена IPv4','ID тунелю (0–65535)','Інтервал keepalive (с, 0 = вимкнено)','Повтори keepalive','Міст (порожньо = без мосту)','Підтверджую застосування змін EoIP; чинні EoIP-тунелі можуть роз’єднатися.','Зберегти в RAM і запитати застосування','Вимкнути весь EoIP','Перечитати збережені значення','Налаштування недоступні. Перечитайте їх або скористайтеся вимкненням, якщо є токен і підтвердження.','Читання збережених налаштувань…','Збережені значення завантажені. Вони не підтверджують роботу тунелю.','Збереження запиту…','Збережено в RAM; застосування запитано. Перевірте інтерфейси та передавання даних. Для запису у флеш окремо використовуйте штатне збереження Padavan.','Запис або застосування не підтверджені. Перечитайте значення та перевірте параметри й фактичний стан.','Відповідь недоступна; запит міг виконатися. Перевірте збережений і фактичний стан перед повтором.'],
 'RU.dict': ['Сохранённые настройки EoIP','Включить службу EoIP','Включить слот','Запускать слот при загрузке','Локальный IPv4 (0.0.0.0 = автоматически)','Удалённый IPv4','ID туннеля (0–65535)','Интервал keepalive (с, 0 = выключено)','Повторы keepalive','Мост (пусто = без моста)','Подтверждаю применение изменений EoIP; действующие EoIP-туннели могут отключиться.','Сохранить в RAM и запросить применение','Выключить весь EoIP','Перечитать сохранённые значения','Настройки недоступны. Перечитайте их или используйте выключение, если доступны токен и подтверждение.','Чтение сохранённых настроек…','Сохранённые значения загружены. Они не подтверждают работу туннеля.','Сохранение запроса…','Сохранено в RAM; применение запрошено. Проверьте интерфейсы и передачу данных. Для записи во флеш отдельно используйте штатное сохранение Padavan.','Запись или применение не подтверждены. Перечитайте значения и проверьте параметры и фактическое состояние.','Ответ недоступен; запрос мог выполниться. Проверьте сохранённое и фактическое состояние перед повтором.'],
}
notes = {
 'EN.footer':'Refresh observations manually. Initial collection may take up to 20 seconds. Settings below are separate from observations; Apply can reconnect existing EoIP tunnels.',
 'UK.dict':'Оновлення спостережень ручне. Перший збір може тривати до 20 секунд. Налаштування нижче відокремлені від фактичного стану; застосування може перепідключити чинні EoIP-тунелі.',
 'RU.dict':'Обновление наблюдений ручное. Первый сбор может занять до 20 секунд. Настройки ниже отделены от фактического состояния; применение может переподключить действующие EoIP-туннели.',
}
for name in labels:
    labels[name][11] = notes[name]
    if len(editor_keys) != len(editor_labels[name]): raise SystemExit('EoIP editor label count mismatch')
    labels[name] += editor_labels[name]
keys += editor_keys
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
pending.append((asset.with_name('wr-eoip-editor.js'), (here / 'settings-editor.js').read_text()))
for path, content in pending:
    path.write_text(content)
print('Prepared EoIP status/settings page, manual refresh and EN/UK/RU labels')
