#!/usr/bin/env python3
"""Generate a model-specific setup guide from an enabled firmware profile."""
import argparse
import re
from pathlib import Path


def read_config(path):
    values = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        match = re.fullmatch(r"(CONFIG_[A-Za-z0-9_]+)=(.*)", line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def is_enabled(config, key):
    return config.get(key) == "y"


def link(label, url, plain):
    return f"[{label}]({url})" if not plain else f"{label}: {url}"


SERVICE_GUIDES = {
    "CONFIG_FIRMWARE_INCLUDE_ZEROTIER": {
        "title": "ZeroTier",
        "body": [
            "Потрібен, коли слід безпечно з'єднати роутер і власні пристрої через Інтернет без відкриття портів.",
            "Створіть власний обліковий запис і приватну мережу в {central}; Network ID введіть у сторінці ZeroTier роутера, застосуйте зміни та авторизуйте вузол у Central.",
            "Для пошти використовуйте скриньку, яку контролюєте довго; пароль має бути унікальним, згенерованим менеджером паролів. Увімкніть MFA, якщо його пропонує обраний спосіб входу. Не зберігайте пароль, Recovery Code або Network ID у відкритому файлі.",
            "Після перезавантаження перевірте статус вузла та авторизацію. Доступ до WebUI/SSH і до LAN вмикайте окремо лише коли він потрібен.",
            "Вимкнення служби зберігає членство в мережі; перед видаленням або зміною Network ID збережіть поточний стан.",
        ],
        "links": [("ZeroTier Central — створення й керування мережею", "https://central.zerotier.com/"),
                  ("Офіційний Quickstart — мережа, Network ID і авторизація", "https://docs.zerotier.com/quickstart/"),
                  ("Довідка CLI та статусів", "https://docs.zerotier.com/cli/")],
    },
    "CONFIG_FIRMWARE_INCLUDE_STUBBY": {
        "title": "Stubby: DNS-over-TLS (DoT)",
        "body": [
            "DoT шифрує DNS між роутером і DNS-постачальником. У строгому режимі DNS припиняється, якщо TLS-сертифікат не підтверджено.",
            "Спочатку перевірте правильний системний час і звичайний DNS. Потім увімкніть Stubby, оберіть відомого постачальника та для кожного сервера вкажіть правильні IP-адресу і tls_auth_name.",
            "Не залишайте одночасно застарілий користувацький dnsmasq.conf з no-resolv або server=127.0.0.1#порт, якщо Stubby вимкнено: це може позбавити клієнтів DNS.",
            "Після застосування перевірте відкриття доменів на клієнті та після перезавантаження. Якщо DNS зник, вимкніть Stubby, приберіть локальний server=127.0.0.1#... із користувацького dnsmasq.conf і застосуйте налаштування.",
            "Перемикач задає бажаний стан Stubby; окремий підпис показує наявність процесу. «Процес запущений; DNS не перевірено» ще не підтверджує відповідь DNS або TLS. «Увімкнено; процес не знайдено» означає, що запит на ввімкнення не відповідає спостереженому стану. Кнопка «Оновити стан» лише перечитує стан, не запускає службу; автоматичне оновлення відбувається раз на 30 секунд на видимій сторінці. При помилці читання показано «Стан процесу невідомий».",
        ],
        "links": [("Офіційне налаштування Stubby", "https://dnsprivacy.org/dns_privacy_daemon_-_stubby/configuring_stubby/"),
                  ("Опис строгого режиму Stubby", "https://dnsprivacy.org/dns_privacy_daemon_-_stubby/about_stubby/")],
    },
    "CONFIG_FIRMWARE_INCLUDE_DOH": {
        "title": "DNS-over-HTTPS (DoH)",
        "body": [
            "DoH є окремим захищеним способом резолвінгу DNS. Увімкніть або DoH, або Stubby на час первинного тесту, щоб причина несправності була зрозумілою.",
            "Перед увімкненням перевірте час роутера та звичайний DNS. Після застосування перевірте домени на клієнті й повторіть перевірку після перезавантаження.",
            "При збої вимкніть DoH та видаліть зі свого dnsmasq.conf локальний server=127.0.0.1#... лише якщо він належить вимкненій службі.",
            "Перемикач DoH і окремий стан процесу мають різні призначення. Наявність процесу не підтверджує відповідь DNS, TLS або роботу кожного налаштованого постачальника. «Процес запущений попри вимкнення» вказує на розбіжність із бажаним станом; «Стан процесу невідомий» означає, що перевірка не дала надійного результату. Оновлюйте стан вручну кнопкою або дочекайтеся автоматичного перечитування раз на 30 секунд на видимій сторінці. Ці перевірки не змінюють конфігурацію.",
        ],
        "links": [("RFC 8484 — стандарт DNS-over-HTTPS", "https://www.rfc-editor.org/rfc/rfc8484")],
    },
    "CONFIG_FIRMWARE_INCLUDE_WIREGUARD": {
        "title": "WireGuard",
        "body": [
            "Створіть окрему пару ключів для кожного вузла; приватний ключ не передавайте і не публікуйте. Заповніть адресу тунелю, публічний ключ вузла, Endpoint та Allowed IPs згідно зі своєю схемою мережі.",
            "Застосуйте конфігурацію, перевірте handshake та доступ лише до потрібних підмереж. Перед маршрутизацією всього трафіку перевірте, що WebUI й SSH лишаються доступними.",
            "На сторінці VPN стан інтерфейсу показано окремо від handshake. Дані handshake збираються раз на 30 секунд; кнопка «Оновити стан» перечитує останній зразок. Позначка «застарілі» означає невдалу або прострочену перевірку. Лічильник свіжих handshake стосується моменту збору, а вік даних показано окремо. Наявність handshake не підтверджує роботу маршрутів: перевірте доступ до потрібного ресурсу через тунель.",
        ],
        "links": [("Офіційний сайт WireGuard", "https://www.wireguard.com/"),
                  ("Швидкий посібник WireGuard", "https://www.wireguard.com/quickstart/")],
    },
    "CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG": {
        "title": "AmneziaWG",
        "body": [
            "AmneziaWG має власні параметри маскування поверх WireGuard. Імпортуйте конфігурацію тільки з довіреного джерела, не публікуйте приватний ключ чи QR-код.",
            "Для оцінки зв’язку використовуйте окремі показники стану інтерфейсу й handshake на сторінці VPN. Дані оновлюються раз на 30 секунд; ручне оновлення читає останній зразок. Недоступні чи застарілі дані не означають підтверджений розрив тунелю. Після handshake перевірте фактичний доступ до потрібної LAN-адреси.",
            "Спершу налаштуйте тунель так, щоб він маршрутизував лише потрібну LAN-підмережу. Переконайтеся, що аварійний локальний доступ до роутера зберігається до вмикання маршруту за замовчуванням.",
        ],
        "links": [("Офіційна документація Amnezia", "https://docs.amnezia.org/documentation/"),
                  ("Документація AmneziaWG", "https://docs.amnezia.org/documentation/amnezia-wg/")],
    },
    "CONFIG_FIRMWARE_INCLUDE_SSWAN": {
        "title": "IPsec / StrongSwan",
        "body": [
            "IPsec використовуйте для сумісності з корпоративними або site-to-site мережами. До вмикання узгодьте з адміністратором адресу шлюзу, локальні й віддалені підмережі, метод автентифікації та маршрути.",
            "Не замінюйте робочий WAN-маршрут маршрутом тунелю без локального резервного доступу. Після застосування перевірте встановлення SA, доступ до потрібної підмережі й DNS.",
        ],
        "links": [("Офіційна документація strongSwan", "https://docs.strongswan.org/"),
                  ("Посібник strongSwan щодо site-to-site VPN", "https://docs.strongswan.org/docs/latest/howtos/siteToSite.html")],
    },
    "CONFIG_FIRMWARE_INCLUDE_ZRAM": {
        "title": "ZRAM",
        "body": [
            "ZRAM створює стиснений swap у RAM. Після ввімкнення перевірте, що окремий статус показує «Працює: swap активний». Обраний розмір, наявність модуля чи самого пристрою ще не підтверджують активний swap; ZRAM не додає фізичної пам'яті.",
            "Для WR1200JS залиште початковий розмір консервативним. Якщо роутер стає нестабільним, вимкніть ZRAM, перезавантажте та збережіть системний журнал для аналізу.",
            "Кнопка «Оновити стан» перечитує фактичну активність swap, не змінює розмір і не перезапускає службу. Стан також оновлюється раз на 30 секунд на видимій сторінці. «Не працює: swap не активний» означає, що ввімкнена настройка не підтверджена активним swap; «Ще працює попри вимкнення» означає, що swap залишився активним. При помилці перевірки показано «Стан невідомий».",
            "Для перевірки через SSH виконайте cat /proc/swaps: активний ZRAM має окремий запис /dev/zram0. Після перезавантаження повторіть перевірку. Не вважайте ввімкнений перемикач доказом успішного запуску.",
        ],
        "links": [("Документація ядра Linux про zram", "https://docs.kernel.org/admin-guide/blockdev/zram.html")],
    },
    "CONFIG_FIRMWARE_INCLUDE_QOS": {
        "title": "QoS",
        "body": [
            "QoS потрібен, коли важливі затримка й справедливий розподіл каналу. Виміряйте реальну швидкість без QoS та задайтесь приблизно 85–95% стабільної швидкості каналу.",
            "На 100 Мбіт/с починайте з 85–90 Мбіт/с; на 300 Мбіт/с — з 255–285 Мбіт/с. Для 1 Гбіт/с оцініть навантаження CPU: програмний QoS може зменшити пропускну здатність.",
        ],
        "links": [("Документація Linux Traffic Control", "https://www.kernel.org/doc/html/latest/networking/tc-actions-env-rules.html")],
    },
    "CONFIG_FIRMWARE_INCLUDE_SFE": {
        "title": "Shortcut Forwarding Engine (SFE)",
        "body": [
            "SFE може підвищувати IPv4 NAT-маршрутизацію, але може обійти функції, яким потрібне повне проходження пакетів через QoS, детальний облік або складні правила.",
            "Для 100/300 Мбіт/с вмикайте лише після перевірки всіх потрібних служб. Для 1 Гбіт/с порівняйте швидкість і стабільність з увімкненим та вимкненим SFE; при проблемі поверніть попередній режим.",
        ],
        "links": [],
    },
    "CONFIG_FIRMWARE_INCLUDE_DROPBEAR": {
        "title": "SSH (Dropbear)",
        "body": [
            "Залишайте SSH доступним лише з LAN або через свій VPN. Задайте унікальний пароль адміністратора, а для постійного віддаленого доступу використовуйте ключі authorized_keys.",
            "Не відкривайте SSH у WAN без потреби. Перед зміною VPN/DNS перевірте локальний SSH, щоб не втратити шлях відновлення.",
        ],
        "links": [("Документація Dropbear", "https://matt.ucc.asn.au/dropbear/dropbear.html")],
    },
    "CONFIG_FIRMWARE_INCLUDE_IPERF3": {
        "title": "iPerf3",
        "body": [
            "iPerf3 використовується для вимірювання LAN/Wi-Fi. Увімкніть на короткий час, запускайте тест лише всередині своєї мережі та вимкніть після вимірювання.",
        ],
        "links": [("Документація iPerf3", "https://software.es.net/iperf/")],
    },
    "CONFIG_FIRMWARE_INCLUDE_USBIP": {
        "title": "USB/IP",
        "body": [
            "USB/IP передає USB-пристрій мережею. Використовуйте тільки в довіреній LAN/VPN; не робіть службу доступною з WAN.",
        ],
        "links": [("Документація USB/IP у Linux", "https://docs.kernel.org/usb/usbip_protocol.html")],
    },
    "CONFIG_FIRMWARE_INCLUDE_U2EC": {
        "title": "USB-принтер (U2EC)",
        "body": [
            "Підключіть принтер до USB, увімкніть службу лише в LAN і додайте принтер на комп'ютерах за адресою роутера та портом, показаними в WebUI. Не відкривайте друк у WAN.",
            "Після перезавантаження надрукуйте тестову сторінку. Якщо пристрій не визначається, від'єднайте USB, перезавантажте роутер і підключіть принтер після повного запуску.",
        ],
        "links": [],
    },
    "CONFIG_FIRMWARE_INCLUDE_EOIP": {
        "title": "EoIP",
        "body": [
            "EoIP об'єднує віддалені сегменти Ethernet. Узгодьте IP кінців і Tunnel ID, перевірте маршрути та не створюйте петлю між мостами.",
        ],
        "links": [("Документація MikroTik EoIP", "https://help.mikrotik.com/docs/spaces/ROS/pages/24805521/EoIP")],
    },
    "CONFIG_FIRMWARE_INCLUDE_PRIVOXY": {
        "title": "Privoxy",
        "body": [
            "Privoxy є HTTP-проксі з фільтрацією. Не вмикайте його як прозорий проксі для всієї мережі без тесту: він може впливати на сайти та продуктивність.",
        ],
        "links": [("Документація Privoxy", "https://www.privoxy.org/user-manual/")],
    },
    "CONFIG_FIRMWARE_INCLUDE_SHADOWSOCKS": {
        "title": "Shadowsocks",
        "body": [
            "Потрібні адреса і порт власного або наданого вам сервера, метод шифрування та пароль сервера. Обліковий запис на сайті проєкту для використання протоколу не потрібний.",
            "Введіть параметри сервера в розділі Shadowsocks. Спочатку перевірте з'єднання на одному клієнті, DNS і доступ до WebUI. Лише потім застосовуйте перенаправлення до інших клієнтів. Якщо з'єднання порушилось, вимкніть Shadowsocks і перевірте звичайний DNS та маршрутизацію.",
        ],
        "links": [("Офіційна документація Shadowsocks", "https://shadowsocks.org/")],
    },
    "CONFIG_FIRMWARE_INCLUDE_SSREDIR": {
        "title": "Shadowsocks transparent proxy",
        "body": ["Спершу перевірте тунель для одного клієнта. Лише після успішного DNS, маршрутизації та доступу до WebUI розширюйте правила на інші пристрої."],
        "links": [("Shadowsocks", "https://shadowsocks.org/")],
    },
    "CONFIG_FIRMWARE_INCLUDE_SSLOCAL": {
        "title": "Shadowsocks SOCKS5-клієнт",
        "body": ["SOCKS5-клієнт слухає лише там, де він справді потрібен. Не робіть його доступним із WAN; перевірте DNS та один клієнт перед тим, як вмикати перенаправлення для мережі."],
        "links": [("Shadowsocks", "https://shadowsocks.org/")],
    },
    "CONFIG_FIRMWARE_INCLUDE_VLMCSD": {
        "title": "vlmcsd",
        "body": ["Служба призначена тільки для сумісних лабораторних сценаріїв у власній LAN. Не відкривайте її у WAN і не використовуйте для обходу ліцензування. Якщо така потреба відсутня, залишайте службу вимкненою."],
        "links": [("Вихідний проєкт vlmcsd", "https://github.com/Wind4/vlmcsd")],
    },
    "CONFIG_FIRMWARE_INCLUDE_WPAD": {
        "title": "WPAD / PAC",
        "body": ["WPAD автоматично повідомляє браузерам налаштування проксі. Тримайте його вимкненим, якщо проксі не використовується; неправильний PAC може позбавити клієнтів доступу до Інтернету."],
        "links": [],
    },
    "CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING": {
        "title": "Band Steering",
        "body": ["Увімкніть після того, як 2.4 і 5 ГГц мають однакові SSID, захист і пароль. Перевіряйте переміщення клієнта по будинку; старі або IoT-клієнти можуть потребувати окремої 2.4 ГГц мережі."],
        "links": [],
    },
}

# Every enabled INCLUDE selector must be classified.  A future selector cannot
# silently appear in a final package without either a user guide or an explicit
# statement that it is a library/driver rather than a service.
COMPONENT_FLAGS = {
    "CONFIG_FIRMWARE_INCLUDE_FS_TOOLS", "CONFIG_FIRMWARE_INCLUDE_NTFS_3G",
    "CONFIG_FIRMWARE_INCLUDE_HID", "CONFIG_FIRMWARE_INCLUDE_XFRM",
    "CONFIG_FIRMWARE_INCLUDE_IMQ", "CONFIG_FIRMWARE_INCLUDE_IFB",
    "CONFIG_FIRMWARE_INCLUDE_IPSET", "CONFIG_FIRMWARE_INCLUDE_LANG_RU",
    "CONFIG_FIRMWARE_INCLUDE_LANG_UK", "CONFIG_FIRMWARE_INCLUDE_VENDOR_LOGO",
    "CONFIG_FIRMWARE_INCLUDE_TCPDUMP", "CONFIG_FIRMWARE_INCLUDE_SOCAT",
    "CONFIG_FIRMWARE_INCLUDE_NDISC6_RDISC6", "CONFIG_FIRMWARE_INCLUDE_EAP_PEAP",
    "CONFIG_FIRMWARE_INCLUDE_DDNS_SSL", "CONFIG_FIRMWARE_INCLUDE_HTTPS",
    "CONFIG_FIRMWARE_INCLUDE_DROPBEAR_FAST_CODE", "CONFIG_FIRMWARE_INCLUDE_OPENSSL_EC",
    "CONFIG_FIRMWARE_INCLUDE_OPENSSL_EXE", "CONFIG_FIRMWARE_INCLUDE_CURL",
    "CONFIG_FIRMWARE_INCLUDE_QUIC", "CONFIG_FIRMWARE_INCLUDE_OPENSSL_35",
    "CONFIG_FIRMWARE_INCLUDE_LUA", "CONFIG_FIRMWARE_INCLUDE_TPROXY",
    "CONFIG_FIRMWARE_INCLUDE_QRENCODE",
}


def build_guide(model, config, plain, identity=None):
    out = []
    def heading(text, level=1):
        out.append(("#" * level + " " if not plain else "\n" + ("=" if level == 1 else "-") * len(text) + "\n") + text)
    heading(f"Налаштування {model}")
    if identity:
        out.append(identity)
    out += ["Цей посібник сформовано з увімкнених параметрів профілю прошивки.",
            "Він описує склад збірки, але не підтверджує роботу на конкретному роутері. Перед оновленням збережіть налаштування та забезпечте локальний спосіб відновлення."]
    heading("Початкова мережа і швидкість", 2)
    out += ["100 Мбіт/с: оберіть автоматичне узгодження Ethernet, перевірте кабель Cat5e та не вмикайте QoS без потреби.",
            "300 Мбіт/с: використовуйте гігабітні порти й Cat5e/Cat6; перевірте швидкість дротовим клієнтом перед оцінкою Wi-Fi.",
            "1 Гбіт/с: потрібні гігабітні WAN і LAN порти моделі. Якщо порт 100 Мбіт/с, гігабітний тариф через нього не досягнеться. Прискорення NAT перевіряйте разом із потрібними VPN, QoS і брандмауером.",
            "Wi-Fi: для основної мережі використовуйте WPA2-Personal/AES, окрему мережу 2.4 ГГц для старих або IoT клієнтів і тестуйте Band Steering після зміни SSID/захисту."]
    enabled = []
    for key, guide in SERVICE_GUIDES.items():
        if is_enabled(config, key):
            enabled.append((key, guide))
    heading("Увімкнені служби", 2)
    if not enabled:
        out.append("У цьому профілі немає служб із каталогом інструкцій.")
    for key, guide in enabled:
        heading(guide["title"], 3)
        for paragraph in guide["body"]:
            central = link("ZeroTier Central", "https://central.zerotier.com/", plain)
            out.append(paragraph.format(central=central))
        for label, url in guide["links"]:
            out.append(link(label, url, plain))
        out.append(f"Параметр профілю: {key}=y")
    covered = set(SERVICE_GUIDES)
    leftovers = sorted(key for key, value in config.items()
                       if value == "y" and key in COMPONENT_FLAGS)
    unknown = sorted(key for key, value in config.items()
                     if value == "y" and key.startswith("CONFIG_FIRMWARE_INCLUDE_")
                     and key not in covered and key not in COMPONENT_FLAGS)
    if unknown:
        raise ValueError("Enabled selectors need a guide or component classification: " + ", ".join(unknown))
    heading("Включені компоненти без окремого веб-сервісу", 2)
    if leftovers:
        out += ["Ці компоненти входять до образу як підтримка протоколу, мови, утиліта або залежність. Вони не означають, що служба запущена.",
                *[f"- {key}=y" for key in leftovers]]
    else:
        out.append("Немає.")
    heading("Збереження доступу", 2)
    out += ["Після кожної зміни перевірте WebUI, DNS на клієнті та SSH з LAN. Для DNS/VPN міняйте одну службу за раз.",
            "Не публікуйте конфігураційні архіви, приватні ключі, QR-коди, паролі або коди відновлення."]
    return "\n\n".join(out) + "\n", [key for key, _ in enabled], leftovers


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--markdown", required=True, type=Path)
    parser.add_argument("--text", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--build-number")
    parser.add_argument("--commit")
    args = parser.parse_args()
    identity = None
    if args.build_number or args.commit:
        if not args.build_number or not args.commit:
            parser.error('build-number and commit must be supplied together')
        if not re.fullmatch(r'[1-9][0-9]{0,3}', args.build_number) or not re.fullmatch(r'[0-9a-f]{40}', args.commit):
            parser.error('invalid build identity')
        identity = f"Тестова збірка: {args.build_number}; позначення у версії: {args.build_number}_{args.commit[:8]}; коміт: {args.commit}."
    config = read_config(args.config)
    markdown, enabled, components = build_guide(args.model, config, plain=False, identity=identity)
    text, _, _ = build_guide(args.model, config, plain=True, identity=identity)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.text.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(markdown, encoding="utf-8")
    args.text.write_text(text, encoding="utf-8")
    args.report.write_text(
        "{\n  \"model\": \"%s\",\n  \"guided_services\": [%s],\n  \"classified_components\": [%s]\n}\n" %
        (args.model, ", ".join('"%s"' % key for key in enabled),
         ", ".join('"%s"' % key for key in components)), encoding="utf-8")


if __name__ == "__main__":
    main()
