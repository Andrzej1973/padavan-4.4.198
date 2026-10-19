#!/usr/bin/env python3
"""Localize inherited dictionary values and complete EN/UK/RU help entries.

The pinned Padavan base ships `dict/EN.footer` with Chinese captions for a group
of menu titles, the generic Enable/Disable pair and the SmartDNS help block.
Those values leak into every language, because a key that is missing from
`UK.dict` or `RU.dict` falls back to the English dictionary. This step rewrites
the English values and appends the matching Ukrainian and Russian entries. It
also fills omitted field labels and contextual help for the LAN/DNS and Wi-Fi
settings, replacing stale translations where necessary.

This changes source only. Device runtime behaviour is not verified here.
"""
import argparse
import re
from pathlib import Path

CJK = re.compile(r'[\u3400-\u9fff]')

# key, English, Ukrainian, Russian
ENTRIES = [
    ('AP_Relay', 'Open wireless relay enhancement script',
     'Відкрити сценарій налаштування бездротового мосту',
     'Открыть сценарий настройки беспроводного моста'),
    ('AP_Relay_1', 'Wireless repeater enhancements: automatically search for and switch to relay signals and channels configured in the script for automatic bridging.',
     'Покращення бездротового мосту: автоматично шукати й перемикати сигнал і канал ретранслятора, задані у сценарії.',
     'Улучшения беспроводного моста: автоматически искать и переключать сигнал и канал ретранслятора, заданные в сценарии.'),
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

# key, English, Ukrainian, Russian. The pinned inherited dictionaries omit
# these item names and descriptions in one or both languages, which makes the
# selected locale fall back to English on hover (and for some visible labels).
HELP_ENTRIES = [
    ('LANHostConfig_x_LDNSServer6_itemname', 'DNSv6 Server 1',
     'DNS-сервер IPv6 1', 'DNS-сервер IPv6 1'),
    ('LANHostConfig_x_LDNSServer61_itemname', 'DNSv6 Server 2',
     'DNS-сервер IPv6 2', 'DNS-сервер IPv6 2'),
    ('LANHostConfig_x_LDNSServer6_itemdesc',
     'This field indicates the IP Address of DNSv6 to provide to clients that request IP Address from DHCP Server. You can leave it blank, then the DNS request will be processed by the router.',
     'Це поле задає IPv6-адресу DNS-сервера, яку DHCP надаватиме клієнтам. Якщо залишити поле порожнім, DNS-запити оброблятиме маршрутизатор.',
     'Это поле задаёт IPv6-адрес DNS-сервера, который DHCP будет передавать клиентам. Если оставить поле пустым, DNS-запросы будет обрабатывать маршрутизатор.'),
    ('LANHostConfig_ForceDNS_itemname', 'Redirect all clients DNS requests?',
     'Переспрямовувати DNS-запити всіх клієнтів?',
     'Перенаправлять DNS-запросы всех клиентов?'),
    ('LANHostConfig_ForceDNS_itemdesc',
     'Force use of router DNS for all network clients.',
     'Примусово використовувати DNS роутера для всіх клієнтів мережі.',
     'Принудительно использовать DNS роутера для всех клиентов сети.'),
    ('LANHostConfig_DHCPFilterAAAA_itemname', 'Disable IPv6 DNS records?',
     'Вимкнути записи IPv6 у DNS?', 'Отключить записи IPv6 в DNS?'),
    ('LANHostConfig_DHCPFilterAAAA_itemdesc',
     'Disabling IPv6 DNS records removes AAAA records from responses. IPv6 addresses will not be returned.',
     'Якщо вимкнути записи IPv6 у DNS, із відповідей буде вилучено записи AAAA, а IPv6-адреси не повертатимуться.',
     'При отключении записей IPv6 из DNS-ответов удаляются записи AAAA, поэтому IPv6-адреса возвращаться не будут.'),
    ('LANHostConfig_DHCPAllservers_itemname', 'Enable DNS queries for all servers?',
     'Надсилати DNS-запити до всіх серверів?',
     'Отправлять DNS-запросы всем серверам?'),
    ('LANHostConfig_DHCPAllservers_itemdesc',
     'By default, when dnsmasq has more than one upstream server available, it will only send requests to one server. Enabling DNS queries to all servers causes dnsmasq to send all queries to all available servers. The response from the server that responded first will be returned to the original sender of the request.',
     'Якщо dnsmasq має кілька upstream-серверів, за замовчуванням він надсилає запит лише одному. Цей параметр змушує надсилати кожен запит усім доступним серверам; клієнт отримає першу відповідь.',
     'Если у dnsmasq доступно несколько upstream-серверов, по умолчанию он отправляет запрос только одному. Этот параметр заставляет отправлять каждый запрос всем доступным серверам; клиент получит первый ответ.'),
    ('LANHostConfig_DHCPStrictorder_itemname', 'Enable DNS strict-order?',
     'Увімкнути суворий порядок DNS-серверів?',
     'Включить строгий порядок DNS-серверов?'),
    ('LANHostConfig_DHCPStrictorder_itemdesc',
     'By default, dnsmasq sends requests to any of the upstream servers it knows and tries to give preference to servers that are known to be running. Enabling DNS strict-order forces dnsmasq to check every request on every server strictly in the order in which they appear.<br/><br/>To use DNS strict-order — you need to disable DNS queries for all servers.',
     'За замовчуванням dnsmasq надсилає запити доступним upstream-серверам і надає перевагу тим, що відповідають. Суворий порядок змушує його перевіряти сервери послідовно, у порядку зі списку.<br/><br/>Щоб увімкнути суворий порядок, вимкніть надсилання DNS-запитів до всіх серверів.',
     'По умолчанию dnsmasq отправляет запросы доступным upstream-серверам и отдаёт предпочтение тем, которые отвечают. Строгий порядок заставляет его проверять серверы последовательно, в порядке списка.<br/><br/>Чтобы включить строгий порядок, отключите отправку DNS-запросов всем серверам.'),
    ('LANHostConfig_DHCPStopDNSRebind_itemname', 'Enable DNS Rebind protection?',
     'Увімкнути захист від DNS rebinding?',
     'Включить защиту от DNS rebinding?'),
    ('LANHostConfig_DHCPStopDNSRebind_itemdesc',
     'Enabling this will protect your LAN against DNS rebind attacks.',
     'Цей параметр захищає локальну мережу від атак DNS rebinding, які намагаються спрямувати клієнта на локальну адресу через DNS.',
     'Этот параметр защищает локальную сеть от атак DNS rebinding, которые пытаются направить клиента на локальный адрес через DNS.'),
    ('LANHostConfig_DHCPProxyDNSSEC_itemname', 'Forward upstream DNSSEC results?',
     'Передавати результати перевірки DNSSEC?', 'Передавать результаты проверки DNSSEC?'),
    ('LANHostConfig_DHCPProxyDNSSEC_itemdesc',
     'Forwards DNSSEC validation results from upstream DNS servers (proxy-dnssec). This option does not enable local signature validation. Use a trusted validating upstream resolver.',
     'Передає результати перевірки DNSSEC від upstream DNS-серверів (proxy-dnssec). Цей параметр не вмикає локальну перевірку підписів. Використовуйте довірений резолвер, який перевіряє DNSSEC.',
     'Передаёт результаты проверки DNSSEC от upstream DNS-серверов (proxy-dnssec). Этот параметр не включает локальную проверку подписей. Используйте доверенный резолвер, который проверяет DNSSEC.'),
    ('LANHostConfig_ManualARP_itemdesc',
     'Used to bind the IP address of a network device to its MAC address. This helps prevent ARP spoofing and other ARP attacks by denying network access to a device with a matching IP address in the binding list but an unrecognized MAC address.',
     'Зв’язує IP-адресу пристрою з його MAC-адресою. Це допомагає протидіяти ARP-spoofing та іншим ARP-атакам: пристрій зі зв’язаною IP-адресою, але невідомою MAC-адресою не отримає доступу до мережі.',
     'Связывает IP-адрес устройства с его MAC-адресом. Это помогает противодействовать ARP-spoofing и другим ARP-атакам: устройство со связанным IP-адресом, но неизвестным MAC-адресом не получит доступ к сети.'),
    ('LAN_STP_itemname', 'Enable Spanning Tree Protocol (STP)?',
     'Увімкнути протокол остовного дерева (STP)?',
     'Включить протокол связующего дерева (STP)?'),
    ('LAN_STP_itemdesc',
     'The main purpose of STP is to eliminate loops in an arbitrary Ethernet network topology that has one or more network bridges connected by redundant connections.',
     'STP усуває петлі в Ethernet-топології, де один або кілька мережевих мостів з’єднані резервними каналами.',
     'STP устраняет петли в топологии Ethernet, где один или несколько сетевых мостов соединены резервными каналами.'),
    ('WIFILDPC_itemname', 'Enable LDPC Codes Support?',
     'Увімкнути підтримку кодування LDPC?',
     'Включить поддержку кодирования LDPC?'),
    ('WIFILDPC_itemdesc',
     'LDPC is an error-correcting coding method. Availability depends on radio, driver and client support.',
     'LDPC — метод кодування для корекції помилок. Доступність залежить від підтримки радіомодуля, драйвера та клієнтського пристрою.',
     'LDPC — метод кодирования для коррекции ошибок. Доступность зависит от поддержки радиомодуля, драйвера и клиентского устройства.'),
    ('WIFILDPC2_itemname', 'Enable LDPC Codes Support?',
     'Увімкнути підтримку кодування LDPC?',
     'Включить поддержку кодирования LDPC?'),
    ('WIFILDPC2_itemdesc',
     'Enable support for LDPC encoding allows the use of a more modern error correction standard used to ensure high coding reliability and improve coding efficiency.',
     'Кодування LDPC використовує сучасніший метод корекції помилок для підвищення надійності та ефективності передавання.',
     'Кодирование LDPC использует более современный метод коррекции ошибок для повышения надёжности и эффективности передачи.'),
    ('WLANConfig11n_band_steering_itemname', 'Enable Band Steering?',
     'Увімкнути Band Steering?', 'Включить Band Steering?'),
    ('WLANConfig11n_band_steering_itemdesc',
     'Enable Band Steering allows you to combine two Wi-Fi networks from one router (in the 2.4 GHz and 5 GHz bands) into one network (with the same name) and automatically connect devices to the frequency that will provide maximum speed and connection stability.',
     'Band Steering об’єднує мережі Wi-Fi 2,4 і 5 ГГц під одним ім’ям і допомагає спрямовувати пристрої до відповідного діапазону. Остаточний вибір діапазону залежить від пристрою-клієнта.',
     'Band Steering объединяет сети Wi-Fi 2,4 и 5 ГГц под одним именем и помогает направлять устройства в подходящий диапазон. Окончательный выбор диапазона зависит от клиентского устройства.'),
    ('WLANConfig11n_mumimo_itemname', 'Enable MU-MIMO?',
     'Увімкнути MU-MIMO?', 'Включить MU-MIMO?'),
    ('WLANConfig11n_mumimo_itemdesc',
     'Enable MU-MIMO allows data to be transmitted to multiple devices simultaneously over different spatial streams. MU-MIMO reduces network latency and improves overall throughput.',
     'MU-MIMO дає змогу одночасно передавати дані кільком пристроям різними просторовими потоками, що може зменшити затримку та підвищити загальну пропускну здатність.',
     'MU-MIMO позволяет одновременно передавать данные нескольким устройствам по разным пространственным потокам, что может уменьшить задержку и повысить общую пропускную способность.'),
    ('WLANConfig11n_80211kv', 'Enable 802.11KV',
     'Увімкнути 802.11KV', 'Включить 802.11KV'),
    ('WLANConfig11n_80211r', 'Enable 802.11R',
     'Увімкнути 802.11R', 'Включить 802.11R'),
    ('WLANConfig11n_amsdu_itemname', 'Enable AMSDU',
     'Увімкнути агрегацію A-MSDU', 'Включить агрегацию A-MSDU'),
    ('WLANConfig11n_amsdu_itemdesc',
     'Enable A-MSDU aggregation can significantly increase the link throughput, especially with a large number of small packets, but at the same time increase the delay time in case of packet loss due to retransmission of an aggregated packet. Enable AMSDU also increases the load on the processor.',
     'Агрегація A-MSDU може підвищити пропускну здатність, особливо для багатьох дрібних пакетів. Водночас повторне передавання агрегованого пакета після втрати може збільшити затримку, а обробка A-MSDU — навантаження на процесор.',
     'Агрегация A-MSDU может повысить пропускную способность, особенно при передаче множества небольших пакетов. При этом повторная передача агрегированного пакета после потери может увеличить задержку, а обработка A-MSDU — нагрузку на процессор.'),
]


def read(path):
    return path.read_text(encoding='utf-8')


def transform_dictionaries(english, ukrainian, russian):
    """Return localized EN/UK/RU source text, rejecting changed anchors."""
    source_values = {
        'AP_Relay': '【Click to open the configuration wireless relay enhancement script】',
        'AP_Relay_1': 'Wireless repeater enhancements:【It can automatically search and switch the relay signals and channels preconfigured in the script for automatic bridging】',
        'LANHostConfig_x_LDNSServer6_itemdesc': 'This field indicates the IP Address of DNSv6 to provide to clients that request IP Address from DHCP Server. You can leave it blank, then the DNS request will be processed by ZVMODELVZ.',
        'LANHostConfig_DHCPProxyDNSSEC_itemname': 'Enable DNSSEC support?',
        'LANHostConfig_DHCPProxyDNSSEC_itemdesc': 'Enabling this will protect DNS by introducing authentication for DNS servers. This prevents DNS hacking and poisoning. If the authoritative DNS server has DNSSEC, enabling DNSSEC ensures your DNS queries are answered by that DNS server, and not an imposter.',
        'WIFILDPC_itemdesc': 'Enable support for LDPC encoding allows the use of a more modern error correction standard used to ensure high coding reliability and improve coding efficiency. This thing is mandatory for 11ac, optional for 11n. Required for PMF (802.11w).',
    }
    for entry in ENTRIES:
        pattern = re.compile(r'(?m)^' + re.escape(entry[0]) + r'=(.*)$')
        found = pattern.findall(english)
        if len(found) != 1:
            raise ValueError('Inherited dictionary anchor mismatch (%d matches): %s' % (len(found), entry[0]))
        expected_source = source_values.get(entry[0])
        if expected_source is not None and found[0] != expected_source:
            raise ValueError('Inherited relay-help anchor changed: ' + entry[0])
        if expected_source is None and not CJK.search(found[0]):
            raise ValueError('Inherited dictionary value is not Chinese any more: ' + entry[0])
        english = pattern.sub(lambda match, item=entry: item[0] + '=' + item[1], english, count=1)

    for entry in HELP_ENTRIES:
        pattern = re.compile(r'(?m)^' + re.escape(entry[0]) + r'=(.*)$')
        found = pattern.findall(english)
        if found != [source_values.get(entry[0], entry[1])]:
            raise ValueError('Inherited help anchor mismatch: ' + entry[0])
        if found != [entry[1]]:
            english = pattern.sub(lambda match, item=entry: item[0] + '=' + item[1],
                                  english, count=1)
    if CJK.search(english):
        raise ValueError('Chinese value remains in the English dictionary; no files written')

    localized = []
    for index, name, dictionary in ((2, 'UK.dict', ukrainian), (3, 'RU.dict', russian)):
        keys = {line.split('=', 1)[0] for line in dictionary.splitlines() if '=' in line}
        additions = []
        for entry in ENTRIES:
            if entry[0] in keys:
                raise ValueError('Inherited translation key already present: ' + name + '/' + entry[0])
            additions.append(entry[0] + '=' + entry[index])
        for entry in HELP_ENTRIES:
            pattern = re.compile(r'(?m)^' + re.escape(entry[0]) + r'=(.*)$')
            found = pattern.findall(dictionary)
            if len(found) > 1:
                raise ValueError('Duplicate localized help key: ' + name + '/' + entry[0])
            if found:
                dictionary = pattern.sub(
                    lambda match, item=entry: item[0] + '=' + item[index],
                    dictionary, count=1)
            else:
                additions.append(entry[0] + '=' + entry[index])
        if additions:
            dictionary = dictionary.rstrip('\n') + '\n' + '\n'.join(additions) + '\n'
        localized.append(dictionary)
    return english, localized[0], localized[1]


def verify_image_dictionaries(dictionaries):
    """Raise ValueError unless EN/UK/RU contain each expected value exactly once."""
    locale_indices = {'EN.dict': 1, 'UK.dict': 2, 'RU.dict': 3}
    if set(dictionaries) != set(locale_indices):
        raise ValueError('Expected exactly EN.dict, UK.dict and RU.dict')
    for name, content in dictionaries.items():
        dictionary = content.splitlines()
        index = locale_indices[name]
        for entry in ENTRIES + HELP_ENTRIES:
            values = [line.split('=', 1)[1] for line in dictionary
                      if line.startswith(entry[0] + '=')]
            if values != [entry[index]]:
                raise ValueError('Missing or changed localized dictionary value: ' + name + '/' + entry[0])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('--verify-image', action='store_true')
    args = parser.parse_args()
    if args.verify_image:
        root = args.source / 'trunk/romfs/www'
        try:
            verify_image_dictionaries({name: read(root / name)
                                       for name in ('EN.dict', 'UK.dict', 'RU.dict')})
        except ValueError as error:
            raise SystemExit(str(error))
        print('PASS inherited dictionary values in EN/UK/RU')
        return

    source = args.source / 'trunk/user/www/dict'
    english_path = source / 'EN.footer'
    ukrainian_path = source / 'UK.dict'
    russian_path = source / 'RU.dict'
    try:
        english, ukrainian, russian = transform_dictionaries(
            read(english_path), read(ukrainian_path), read(russian_path))
    except ValueError as error:
        raise SystemExit(str(error))
    for path, content in ((english_path, english), (ukrainian_path, ukrainian),
                          (russian_path, russian)):
        with path.open('w', encoding='utf-8', newline='\n') as stream:
            stream.write(content)
    print('Localized %d inherited values and %d help entries in EN/UK/RU' %
          (len(ENTRIES), len(HELP_ENTRIES)))


if __name__ == '__main__':
    main()
