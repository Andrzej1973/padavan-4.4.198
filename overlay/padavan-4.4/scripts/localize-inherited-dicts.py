#!/usr/bin/env python3
"""Replace Chinese values inherited in the English dictionary and complete the
Ukrainian and Russian dictionaries for the same keys.

The pinned Padavan base ships `dict/EN.footer` with Chinese captions for a group
of menu titles, the generic Enable/Disable pair and the SmartDNS help block.
Those values leak into every language, because a key that is missing from
`UK.dict` or `RU.dict` falls back to the English dictionary. This step rewrites
the English values and appends the matching Ukrainian and Russian entries.

This changes source only. Device runtime behaviour is not verified here.
"""
import argparse
import re
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('--verify-image', action='store_true')
args = parser.parse_args()

CJK = re.compile(r'[\u3400-\u9fff]')

# key, English, Ukrainian, Russian
ENTRIES = [
    ('menu5_25', 'Intranet tunneling', 'Тунелювання інтранету', 'Туннелирование интранета'),
    ('menu5_27', 'File manager', 'Файловий менеджер', 'Файловый менеджер'),
    ('menu5_27_1', 'File manager', 'Файловий менеджер', 'Файловый менеджер'),
    ('menu5_30', 'Tunneling services', 'Служби тунелювання', 'Службы туннелирования'),
    ('menu5_31', 'Music unlocking', 'Розблокування музики', 'Разблокировка музыки'),
    ('menu5_31_1', 'Music unlocking', 'Розблокування музики', 'Разблокировка музыки'),
    ('menu5_36', 'Aliyun Drive', 'Aliyun Drive', 'Aliyun Drive'),
    ('menu5_37', 'QoS traffic control', 'Керування трафіком QoS', 'Управление трафиком QoS'),
    ('Disable', 'Disable', 'Вимкнути', 'Отключить'),
    ('Enable', 'Enable', 'Увімкнути', 'Включить'),
    ('SmartDNS_6',
     'SmartDNS is a local high-performance DNS server that avoids domain poisoning, returns the fastest IP address and can filter ads.',
     'SmartDNS — локальний високопродуктивний DNS-сервер, який запобігає підміні доменів, повертає найшвидшу IP-адресу та може фільтрувати рекламу.',
     'SmartDNS — локальный высокопроизводительный DNS-сервер, который предотвращает подмену доменов, возвращает самый быстрый IP-адрес и может фильтровать рекламу.'),
    ('SmartDNS3_1', 'Redirect TCP port 53 to SmartDNS',
     'Перенаправляти TCP-порт 53 на SmartDNS', 'Перенаправлять TCP-порт 53 на SmartDNS'),
    ('SmartDNS4_1', 'Redirect IPv6 UDP/TCP port 53 to SmartDNS',
     'Перенаправляти IPv6 UDP/TCP порт 53 на SmartDNS', 'Перенаправлять IPv6 UDP/TCP порт 53 на SmartDNS'),
    ('SmartDNS6', 'Number of cached domain results',
     'Кількість кешованих результатів доменів', 'Количество кэшированных результатов доменов'),
    ('SmartDNS7', 'Persist the cache', 'Зберігати кеш на диску', 'Сохранять кэш на диске'),
    ('SmartDNS8', 'TCP connection idle timeout',
     'Час простою TCP-з’єднання', 'Время простоя TCP-соединения'),
    ('SmartDNS9', 'Domain TTL result', 'Результат TTL домену', 'Результат TTL домена'),
    ('SmartDNS12', 'Maximum TTL returned to clients',
     'Максимальний TTL, що повертається клієнтам', 'Максимальный TTL, возвращаемый клиентам'),
    ('SmartDNS13', 'Maximum number of IP addresses returned to a client',
     'Максимальна кількість IP-адрес, що повертаються клієнту',
     'Максимальное количество IP-адресов, возвращаемых клиенту'),
    ('SmartDNS19', 'ipset timeout', 'Тайм-аут ipset', 'Тайм-аут ipset'),
    ('SmartDNS20', 'Speed test mode', 'Режим перевірки швидкості', 'Режим проверки скорости'),
    ('SmartDNS21', 'Dual-stack IP selection',
     'Вибір IP у подвійному стеку', 'Выбор IP в двойном стеке'),
    ('SmartDNS22', 'Dual-stack selection threshold',
     'Поріг вибору в подвійному стеку', 'Порог выбора в двойном стеке'),
    ('SmartDNS23', 'Prefer IPv6 in dual-stack selection',
     'Надавати перевагу IPv6 у подвійному стеку', 'Предпочитать IPv6 в двойном стеке'),
    ('SmartDNS24_1', 'Force SOA for AAAA queries',
     'Примусово повертати SOA для AAAA', 'Принудительно возвращать SOA для AAAA'),
    ('SmartDNS25_1', 'Force SOA for the specified qtype',
     'Примусово повертати SOA для вказаного qtype', 'Принудительно возвращать SOA для указанного qtype'),
    ('SmartDNS27', 'Expired cache service',
     'Служба застарілого кешу', 'Служба устаревшего кэша'),
    ('SmartDNS27_1',
     'When enabled, an expired record with TTL 0 is returned for incoming queries while the record is refreshed in parallel, so clients do not wait.',
     'Коли ввімкнено, на запит повертається застарілий запис із TTL 0, а сам запис оновлюється паралельно, тому клієнт не чекає.',
     'Когда включено, на запрос возвращается устаревшая запись с TTL 0, а сама запись обновляется параллельно, поэтому клиент не ждёт.'),
    ('SmartDNS28', 'Maximum timeout for the expired cache service',
     'Максимальний тайм-аут служби застарілого кешу', 'Максимальный тайм-аут службы устаревшего кэша'),
    ('SmartDNS28_1', 'Seconds; 0 disables the timeout, a value above 0 sets the timeout in seconds.',
     'Секунди; 0 вимикає тайм-аут, значення більше 0 задає тайм-аут у секундах.',
     'Секунды; 0 отключает тайм-аут, значение больше 0 задаёт тайм-аут в секундах.'),
    ('SmartDNS29', 'TTL of the returned expired cache record',
     'TTL поверненого застарілого запису', 'TTL возвращаемой устаревшей записи'),
    ('SmartDNS30', 'Dual-stack prefetch interval',
     'Період попереднього вибору в подвійному стеку', 'Период предварительного выбора в двойном стеке'),
    ('SmartDNS31', 'Enable', 'Увімкнути', 'Включить'),
]


def read(path):
    return path.read_text(encoding='utf-8')


if args.verify_image:
    root = args.source / 'trunk/romfs/www'
    for index, name in enumerate(('EN.dict', 'UK.dict', 'RU.dict'), 1):
        dictionary = read(root / name).splitlines()
        for entry in ENTRIES:
            values = [line.split('=', 1)[1] for line in dictionary if line.startswith(entry[0] + '=')]
            if values != [entry[index]]:
                raise SystemExit('Missing or changed inherited dictionary value: ' + name + '/' + entry[0])
    print('PASS inherited dictionary values in EN/UK/RU')
    raise SystemExit(0)

english_path = args.source / 'trunk/user/www/dict/EN.footer'
ukrainian_path = args.source / 'trunk/user/www/dict/UK.dict'
russian_path = args.source / 'trunk/user/www/dict/RU.dict'

english = read(english_path)
for entry in ENTRIES:
    pattern = re.compile(r'(?m)^' + re.escape(entry[0]) + r'=(.*)$')
    found = pattern.findall(english)
    if len(found) != 1:
        raise SystemExit('Inherited dictionary anchor mismatch (%d matches): %s' % (len(found), entry[0]))
    if not CJK.search(found[0]):
        raise SystemExit('Inherited dictionary value is not Chinese any more: ' + entry[0])
    english = pattern.sub(lambda match, item=entry: item[0] + '=' + item[1], english, count=1)

if CJK.search(english):
    raise SystemExit('Chinese value remains in the English dictionary; no files written')

changes = [(english_path, english)]
for index, path in ((2, ukrainian_path), (3, russian_path)):
    dictionary = read(path)
    keys = {line.split('=', 1)[0] for line in dictionary.splitlines() if '=' in line}
    additions = []
    for entry in ENTRIES:
        if entry[0] in keys:
            raise SystemExit('Inherited translation key already present: ' + path.name + '/' + entry[0])
        additions.append(entry[0] + '=' + entry[index])
    changes.append((path, dictionary.rstrip('\n') + '\n' + '\n'.join(additions) + '\n'))

for path, content in changes:
    with path.open('w', encoding='utf-8', newline='\n') as stream:
        stream.write(content)
print('Replaced %d inherited Chinese dictionary values and completed EN/UK/RU' % len(ENTRIES))