# Конфіг 4.4 WR1200JS — карта перенесення

Джерело для вихідних побажань: configs.build/wr1200js.config з гілки experimental/hadzhioglu-compare. CAKE виключено за вказівкою користувача. Це попередній аудит символів/можливостей; остаточне підтвердження вимагає збірки кандидата й перевірки його menuconfig/Makefiles.

| Група | Поточне побажання | Попередній стан для Padavan 4.4 | Примітка |
|---|---|---|---|
| Плата/ядро | MT7621, WR1200JS | Є upstream board profile у vipshmily/padavan-4.4; target задає VENDOR=Ralink, PRODUCT=MT7621 | Кандидатний commit c25283e містить board kernel config, але upstream target folder має залишитися незмінним |
| CPU | CPU sleep увімкнений | Потребує пошуку символу | Зберегти лише якщо driver/framework 4.4 має еквівалент |
| Wi-Fi | MT7603E 4.1 + MT7612E 3.0 | Kernel config WR1200JS кандидата вмикає MT7603E і MT7612E з EEPROM offsets 0x0/0x8000 | Треба звірити NVMEM калібрування й підтвердити роботу на роутері |
| IPv6 | Увімкнено | Є в K2P-USB kernel config | Перевірити userland, firewall і WebUI |
| USB | Увімкнено; один фізичний USB 2.0 порт | Kernel WR config отримує USB/PHY/EHCI/OHCI/storage options із K2P-USB, але XHCI/USB3 вимкнений; target template вмикає USB | Ще не зібрано; на роутері перевірити USB2, PHY і port swap |
| FS tools, FAT, exFAT, ext2/3/4, FUSE, swap | Увімкнено | Тимчасовий target template вмикає всі відповідні WR-шаблонні перемикачі | Потребує kernel-config/build proof і перевірки розміру образу |
| HID | Увімкнено | У target template буде ввімкнено; kernel modules/config mapping ще не доведений | Перевірити фактичні HID modules у firmware |
| XFRM/IPsec | Увімкнено | Target template буде ввімкнено, але kernel XFRM і StrongSwan конфіг ще треба додати | Не вважати StrongSwan перенесеним до появи всіх залежностей |
| QoS + IMQ + IFB | Увімкнено, без CAKE | Target template вмикає legacy QoS/IMQ/IFB; kernel IFB модуль додається, а patch `linux-4.4-imq.diff` додає upstream IMQ driver/iptables target | Патч ще має пройти dry-run і повну kernel build проти pinned vendor tree. CAKE не переносити |
| IPSet | Увімкнено | Target template вмикає ipset; kernel IP_SET і типи set додаються в профіль | Перевірити, що kernelconfig не відкидає їх та ipset userland збирається |
| NFS client | Увімкнено | Target template буде ввімкнено | Потрібно перевірити kernel NFS symbols і userspace helper/версію |
| SFE | Увімкнено | Є у WR template 4.4 | Kernel/userland interplay з QoS треба перевірити на збірці/runtime |
| Мови RU/UK, vendor logo | Увімкнено | Userland/WebUI patch | Треба перевірити наявність мов і брендингу в 4.4 base |
| DNSMasq regex | Увімкнено | Не перевірено | Перевірити саме зібраний dnsmasq variant |
| NTFS-3G, U2EC | Увімкнено | NTFS-3G і U2EC є однойменними target selectors і копіюються | Перевірити USB/FUSE kernel modules та наявність готових package sources |
| USBIP, ndisc6/rdisc6 | Увімкнено | Немає однойменних target selectors | Перенести package/build hooks |
| tcpdump, socat, hdparm, LPRD | Увімкнено | Є однойменні target selectors і копіюються | Перевірити binary/daemon package linkage та образ |
| RPL2TP, EAP-PEAP, HTTPS/DDNS TLS, Dropbear | Увімкнено | OpenSSL/SSL/config mapping | Перевірити залежності й flash footprint |
| StrongSwan, AmneziaWG | Увімкнено | StrongSwan є target option і буде ввімкнений; AmneziaWG відсутній | XFRM/kernel dependency потрібен для StrongSwan; AmneziaWG окремо портити під 4.4 ABI |
| OpenSSL EC/executable | Увімкнено | Пакети | Перевірити версію OpenSSL, бо в конфізі QUIC позначений як залежний від OpenSSL 3.5, а в кандидаті може бути інша версія |
| Tor + GeoIP/GeoIPv6 | Увімкнено | Пакети/дані | Перевірити бюджет 16 MiB |
| Privoxy, DNSCrypt, Stubby, DoH, Curl/QUIC | Увімкнено | Curl target option буде ввімкнено; решта відсутня | Портити версії пакетів/TLS залежності; QUIC налаштовано на вимогу OpenSSL 3.5, якої база поки не підтверджує |
| WPAD, zram, ADB, LUA, EoIP | Увімкнено | Відсутні target options | Окремий package/kernel mapping і build rules |
| vlmcsd, iperf3, ZeroTier | Увімкнено | Є однойменні target selectors; копіюються у WR template | Перевірити, що build recipes підтримують MIPS/uClibc |
| Zapret, Zapret2, TPROXY | Увімкнено | Немає однойменних selectors, хоча окремі netfilter features можуть існувати | Перенести packages, modules і firewall rules |
| QR encode, redsocks2, Shadowsocks redir/local | Увімкнено | QR/redsocks2 та окремі SS mode selectors відсутні; umbrella `SHADOWSOCKS` є | Перевірити umbrella пакетом потрібні redir/local binary та додати QR/redsocks recipes |
| Image optimization | size optimization | Не перевірено | Переконатися, що флаг зберігається без зміни runtime опцій |

## Активні опції без однойменного WR1200JS target перемикача

Звірка `configs.build/wr1200js.config` з `trunk/configs/templates/WR1200JS.config` у pinned commit `c25283e915a2a00a763774dd255b14aff997285e`: 67 активних `CONFIG_FIRMWARE_*` ключів у вихідному конфігу; 33 мають такий самий ключ у 4.4 target template, 34 не мають. Відсутній ключ означає, що він не переноситься автоматично.

| Опція/група | Статус у 4.4 fork | Наступна робота |
|---|---|---|
| CPU sleep; explicit MT7603/MT7612 version selectors | Немає template options; kernel drivers є у WR board config | Звірити runtime CPU governor/sleep implementation та точні upstream driver revisions |
| FS_TOOLS; Shortcut FE; RU/UK languages; vendor logo; dnsmasq regex | Немає однойменних перемикачів | Перенести потрібні userland/WebUI patches окремо |
| USBIP, ndisc6/rdisc6, DDNS TLS | Немає однойменних WR template selectors | Перевірити package Makefiles і перенести selector/build hook |
| NTFS-3G, LPRD, U2EC, socat, hdparm, HTTPS, Dropbear fast code | Є однойменні WR template selectors; значення конфігу переносяться | Підтвердити залежності, успішне збирання та flash footprint |
| AmneziaWG | Немає target option | Окремо портити kernel+userspace проти 4.4 ABI |
| Tor, GeoIP databases, OBFS4, Privoxy, DNSCrypt, Stubby, DoH | Немає target options | Адаптувати package sources, init/config, data files та flash budget |
| QUIC | Немає target option; конфіг коментує необхідність OpenSSL 3.5, яка не підтверджена у базі | Визначити TLS/QUIC dependency, потім портити або зафіксувати як несумісне |
| WPAD, zram, ADB, LUA, EoIP, TPROXY, Zapret/2, qrencode, redsocks2 | Немає цільових selectors | Перенести kernel/package/firewall/build scripts по одному |
| iperf3, ZeroTier, Shadowsocks redir/local | Target template має `IPERF3`, `ZEROTIER` і umbrella `SHADOWSOCKS` selectors; автоматичне зіставлення вмикає обидва потрібні сервіси, якщо вони активні у вихідному конфігу | Перевірити, що umbrella Shadowsocks містить потрібні redir і local modes |
| CAKE | Відсутній у target fork і виключений користувачем | Не переносити |

## Ризики, які вирішуємо першими

1. Перевірити config-to-kernel pipeline і реальний build для USB/filesystems/IPSet/IFB/NFS.
2. Перевірити upstream IMQ 4.4 backport на конфлікти, складання ядра, xtables target і роботу з класичним QoS.
3. Перенести XFRM/StrongSwan і решту наявних пакетів.
4. Перенести vendor/product config та відсутні сервіси з матрицею, не підміняючи їх приблизними аналогами.
5. Wi-Fi EEPROM calibration path і USB PHY/swap на реальному WR1200JS.
6. Підтвердження control K2P job та прив'язка перевіреного toolchain digest.
7. Пакетний перенос features і вимірювання образу проти 16 MiB flash budget.

