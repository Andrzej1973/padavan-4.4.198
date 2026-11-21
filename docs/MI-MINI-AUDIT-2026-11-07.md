# Xiaomi Mi WiFi Mini (R1CM): аудит і план Padavan 4.4.198

Дата: 2026-11-07. Виконавець: Sol. Статус пріоритету: Mi Mini відкладений
до WR1200JS acceptance, включно з чотирма фінальними варіантами (вимога
власника від 2026-11-17). Цей документ зберігає майбутній план; не продовжувати
Mi Mini аудит чи реалізацію під час поточного WR1200JS етапу.
Статус: аудит завершено; реалізація Mi Mini у цьому завданні не виконувалася.
Код, конфігурації, драйвери й Git-історія не змінені; комітів/push/PR немає.
Не запускалися збірки Mi Mini, підключення до пристрою, flash, reboot або Factory-записи.

## 1. Джерела та межі доказів

Робочий checkout: /home/andrzej/padavan-build/router-guide-work.
Гілка codex/wr1200js-service-webui; HEAD 9a883efff9944f9f4f507729f4aa3d611865b06d.
Наявні локальні WR1200JS-зміни збережено. docs/reference/ не чіпали.

Позначення джерел:
- R: файли цього checkout на зазначеному HEAD, включно з локальними поточними документами.
- B: базове vendor-дерево c25283e915a2a00a763774dd255b14aff997285e, прочитане через git show з /home/andrzej/padavan-build/firmware-source-backup/padavan-4.4.git. Шляхи trunk/... нижче — шляхи всередині цього Git-об’єкта, а не твердження про встановлені пакети.
- N: свіжий nilabsent/padavan-ng master c29b12da69b1593a6e8cf65cd43767fc99bb6386, перевірений через GitHub API сьогодні.
- D: локальний donor RikudouPatrickstar/padavan-fusion 6f59c3d6f827fe9349aa8eb4e3401021d281bfd5, reference_only=true.
- P: кандидат радіопорту Mi Mini, зафіксований на nilabsent d2c5846299949c57a4e867284069900b561dd2a4.

Source-факт означає лише наявність відповідного коду. Він не доводить effective .config, повну image-збірку чи роботу на пристрої. Історичні CI-повідомлення наведено як архівні докази; старі артефакти заново не перевірялися.
Перед реалізацією повторно звірити N та потрібні залежності з тим самим джерелом. Не замінювати vendor-дерево чистим upstream.

## 2. Висновок про готовність плати

Повного підтриманого Mi Mini образу 4.4.198 у проєкті немає.
R boards.json: id=mi-mini, build_enabled=false, recipe=null, status=board-port-pending; radio-object-probe-only. Не вмикати профіль у загальну матрицю лише через наявність package config.
R configs.build/mi-mini.config: XIAOMI/MT7620/MI-MINI, legacy WIFI2_DRIVER=2.7 і WIFI5_DRIVER=3.0 прямо позначені як непідтверджені для 4.4.

Апаратні дані підтверджені конфігураціями/board source, але не оглядом нашого фізичного екземпляра:

| Властивість | Джерело / символ | Статус |
| --- | --- | --- |
| MT7620, RAM 128 MiB | N kernel-3.4.x.config:60 CONFIG_RALINK_RAM_SIZE=128; R CONFIG_PRODUCT=MT7620 | Source-факт; фактичну ревізію перевірити |
| Flash 16 MiB | N kernel-3.4.x.config:836 CONFIG_RT2880_FLASH_16M=y | Не весь обсяг доступний firmware |
| USB: один порт, legacy USB2 EHCI/OHCI | N board.mk:8 BOARD_NUM_USB_PORTS=1; D USB_EHCI_HCD/OHCI_HCD | 4.4 PHY/VBUS/device runtime ще не доведені |
| Три Ethernet PHY, без Gigabit | N board.h:28–30 BOARD_NUM_ETH_EPHY=3, BOARD_HAS_EPHY_L1000/W1000=0 | Не підставляти mapping MT7530 від WR1200JS; WAN/LAN перевірити |
| Два діапазони, 2T2R | N board.h:22–26 BOARD_HAS_5G_11AC=1, обидва TX/RX=2 | 2.4 integrated MT7620/RT2860; 5G MT7612E за наявним board audit |
| Reset/VBUS/LED | N board.h:11 reset30; power24, USB LED26, USB power65/on1 | Не вважати фізичну LED-семантику перевіреною |

Важливі розбіжності донорів: D задає BOARD_GPIO_LED_LAN=29, N — undef; D Store=0x80000, N Store=0x40000. Тому копіювання всієї board-конфігурації неприпустиме. Потрібні реальні /proc/mtd, bootlog, GPIO і калібрування конкретного R1CM.
Свіжі board-файли: https://github.com/nilabsent/padavan-ng/tree/c29b12da69b1593a6e8cf65cd43767fc99bb6386/trunk/configs/boards/XIAOMI/MI-MINI

## 3. Ядро, Ethernet, радіо та образ

R docs/mi-mini-port-status.md документує аудит pinned B: є SOC_MT7620, mt7620a.dtsi та eval DTS, але немає завершеного Mi Mini DTS. Сам eval має іншу RAM-конфігурацію і не є готовим board description.
Там само: vendor raeth OF match не встановлює готову MT7620 Ethernet-інтеграцію; залишкові CONFIG_RALINK_MT7620 гілки switch-коду не тотожні effective SOC_MT7620. Це потрібно повторно підтвердити під час target-порту.
5G MT7612E у vendor-дереві наявний; integrated 2.4G потребував окремого порту. Не підміняти його MT7602E/MT7603E через схожість назв.

Вже існують R overlay/padavan-4.4/candidates/mi-mini/:
- configure-mi-mini-radio-probe.sh, install-mi-mini-radio-candidate.py, integrate-mi-mini-factory.py;
- mi-mini-port-bundle/radio-source.diff та new-files/Kconfig, rt2860v2-ap.Kconfig;
- new-files/os/linux/mi_mini_platform.c:10–11 вимагає built-in CONFIG_SOC_MT7620;
- new-files/os/linux/mi_mini_factory.c — окремий checked Factory adapter.
Не починати цей порт заново і не маскувати нерозв’язані символи success-stub-ами.

R docs/evidence/MI-MINI-RADIO-PROBE-CI-2026-10-26.md: історичні runs 38130857982 / 7c4a4dff та 37136824063 / d201fda успішні в обмеженому probe. Пізніший історичний log підтверджує isolated MIPS vmlinux link, не Mi Mini firmware. На 2026-10-26 артефакти відсутні; це не свіжо перевірений повний образ. FULL-LINK-AUDIT.md містить попередні невдалі етапи — їх не трактувати як останній загальний CI-статус.

Factory: перевіряти межі розділу, повний backup erase block, довжини read/write, завершення erase, серіалізацію і byte-wise readback. In-place NOR update не є power-loss-atomic. Автозапис чужого EEPROM/Factory/bootloader заборонений; supplied patch не є дозволом на включення.

Ліміту firmware у байтах поки не встановлено: немає прийнятої Mi Mini 4.4 partition map/image recipe. Не прирівнювати 16 MiB chip до допустимого TRX. Gate повинен обчислювати межу firmware-розділу без bootloader, Factory, конфігурації та інших резервів і перевіряти формат саме встановленого bootloader. Вільне місце й RAM визначати вимірами готового образу, не сумою приблизних коментарів config.

## 4. Звичайний Router: що повторно використати

B trunk/user/rc/net_wan.c — WAN/link/protocol lifecycle, net_lan.c — LAN/bridge; net_lan.c:731 викликає start_dns_dhcpd(is_ap_mode). B firewall_ex.c формує правила, а shared/defaults.c містить NVRAM defaults.
B www/n56u_ribbon_fixed/Advanced_OperationMode_Content.asp:156–158 має sw_mode=1/4/3; ці значення не треба самовільно перейменовувати або ототожнювати з новим dual-band repeater.
Наявність цих механізмів не доводить працездатність Ethernet/WAN на новій платі.
Router acceptance: фізичний WAN/LAN mapping; DHCP/DNS; IPv4 NAT; окремо IPv6 route/firewall; обидва радіо; керування HTTPS/LAN; збереження старих налаштувань і USB-друк. Зміна режиму не повинна скидати конфігурацію або ламати повернення до Router.

## 5. Репітер: наявне і відсутнє

Підтверджені Padavan-аналоги:
- B rc/net_wifi.c:605–665 start_wifi_apcli_wl/rt: modes3/4, окремі 5G/2G APCLI, додавання в LAN bridge за !sta_wisp або AP mode.
- B rc/net_wifi.c:164 get_apcli_sta_auto; 669 reconnect_apcli: iwpriv ApCliAutoConnect / ApCliEnable.
- B rc/ralink.c:1599–1638: генерація ApCliSsid, ApCliAuthMode, ApCliEncrypType, ApCliWPAPSK.
- B rc/net_wan.c:1970 get_wan_wisp_active перевіряє поточний WISP interface і get_apcli_connected; detect_link.c:253/280 використовує цей стан.
- B www/.../Advanced_WMode2g_Content.asp:343–366 — mode_x, LAN bridge / WAN(WISP), sta_auto; відповідна Advanced_WMode_Content.asp для 5G.
- N legacy kernel config має RT2860V2_AP_APCLI=y та MT76X2_AP_APCLI=y. Це evidence legacy включення, не target4.4 сумісність.

Наявний scan backend також знайдено: B httpd/ralink.c:1655 ej_wl_scan_5g і :1773 ej_wl_scan_2g використовують SiteSurvey=1; web_ex.c:4517/4521 реєструє wl_scan_5g/wl_scan_2g. Розширювати цей шлях з перевіркою автентифікації, таймаутів і driver-підтримки, а не створювати дубльований сканер.

Критично: B net_wifi.c:178–194 get_apcli_wisp_ifname спочатку повертає 2G, потім 5G за enabled/mode/SSID, без порівняння RSSI, loss або gateway. sta_auto означає driver autoconnect, не готовий dual-band health selector. Свіжого доказу вже реалізованого оркестратора в нашому проєкті не встановлено.

Рекомендована початкова топологія: маршрутизований WISP/NAT, один active uplink, стабільна окрема LAN-підмережа і власний DHCP. Це рекомендація, не чинна реалізація. Bridge залишити окремим режимом лише після доказів APCLI/4-address/MAC translation/DHCP/IPv6. Не підключати обидва uplink одночасно в один bridge: можливі петля та конфлікт DHCP.
Один радіомодуль як uplink, другий як AP — обґрунтований кандидат за двома окремими radio paths; на 4.4 потрібні target/runtime докази. AP+STA на одному радіо зазвичай потребує спільного каналу: не обіцяти незалежні AP/STA-канали. Scan може переривати передачу; seamless roaming/NAT-session continuity не обіцяється.

План оркестратора: ручний/автоматичний режим; окремі профілі SSID/BSSID/security/priority для діапазонів; bounded scan; стан DISABLED/SCANNING/CONNECTING/VERIFYING/ACTIVE/DEGRADED/COOLDOWN; контроль link, gateway, loss/RTT, RSSI trend; internet-check лише опційно й окремо від LAN-доступності. Початкові параметри для тестів: опитування 5–10с, кілька послідовних невдач перед failover, dwell60–120с, cooldown/backoff; числові значення — пропозиція, не виміряна оптимальна політика. Немає потреби переносити драйвери на hostapd тільки заради цього.
При зміні uplink повторити DHCP/route/DNS/firewall, зберегти management LAN, не записувати NVRAM кожного poll. Історію обмежити RAM ring-buffer; flash — лише налаштування і рідкі контрольні події. Відновлення після reboot/AP loss перевіряти без factory reset.

## 6. USB-друк: використовувати наявний механізм

Не писати новий print server. B user/Makefile:208–216 додає p910nd при CONFIG_USB_SUPPORT; LPRng і u2ec — окремі selectors. Отже, вимкнені LPRD/U2EC в R configs.build/mi-mini.config не означають автоматичної відсутності RAW-друку. Потрібно підтвердити effective CONFIG_USB_SUPPORT, CONFIG_USB_PRINTER/usblp і фінальний ROMFS.
B p910nd/Makefile:23–24 встановлює /usr/sbin/p910nd. rc/services_usb.c:131–139 керує RAW за rawd_enable:0 off,1 on,2 bidirectional; daemon index0 відповідає TCP9100 (p910nd.c BASEPORT=9100).
B rc/services_usb.c:150–201 шукає /dev/usb/lp0..9, викликає spoolers; усі виклики використовують index0 — багатопринтерний USB-hub/окремі порти не приймати без додаткової перевірки.
B hotplug_usb.c:92–110 повідомляє on_hotplug/on_unplug; rc.c:995–1009 відкладено обробляє події; services_stor.c:1453–1463 запускає/зупиняє spoolers. Це lifecycle source, не перевірка boot recovery на R1CM.
B libdisk/usb_info.c:249–266 вже читає idVendor/idProduct/manufacturer/product. httpd/aidisk.c:105–128 виводить manufacturer/model; device-map/printer.asp споживає ці масиви. Новий usbutils/usb.ids daemon для читання цих полів не потрібен.
B www/.../Advanced_Printer_others.asp:132–169 має RAW select і LPR/U2EC toggles; httpd/variables.c:292 rawd_enable -> EVM_RESTART_SPOOLER; rc.c:995 виконує restart_usb_printer_spoolers. Повторно використати цей UI/backend, не дублювати endpoint.
Драйвери/rendering залишаються на ПК. p910nd передає байти, не перетворює довільний формат у мову принтера. Host-based/GDI, vendor-only, firmware-upload і IPP-only пристрої можуть не підтримувати usblp/RAW. Точну модель/статус сторінки не обіцяти лише за USB descriptor.
IPP-over-USB — окрема можлива потреба конкретного пристрою; готового ipp-usb package у перевірених B user/libs шляхах не знайдено. Не додавати автоматично CUPS, printer drivers чи ipp-usb.

## 7. Ethernet-принтери

Мінімум: список адрес IP/DNS, опис, явно заданий протокол і порт; bounded TCP reachability. RAW9100, LPR515, IPP631 — типові протоколи для перевірки сумісності, не автоматичний доказ підтримки конкретним принтером.
Розділяти: прямий друк ПК->принтер і router proxy. Для першого роутер забезпечує LAN/routing/firewall, а не spooler. Новий proxy без необхідності не робити. TCP connect доводить лише відкритий порт, не успішний друк або точну модель. IPP Get-Printer-Attributes — лише за фактичної підтримки й bounded parser.
B дерево містить mDNS-код старого firefly/mt-daapd, але це не доказ встановленого загального DNS-SD/IPP discovery. Готовий Avahi/ipp-usb daemon у перевірених package paths не встановлений. R має інші discovery-напрацювання; наявність файлів також не означає готовий printer discovery. Перший реліз: ручне додавання; DNS-SD — окремий невеликий етап після розмірних вимірів, без підключення всього Firefly.
У bridge ПК і принтер можуть бути в одній broadcast-domain за успішного APCLI bridging. У WISP downstream ПК може ініціювати доступ до upstream printer за наявності маршруту; reverse discovery/mDNS через NAT не працює автоматично. При overlap підмереж потрібне виявлення конфлікту й явна міграція, а не приховане перепризначення management IP. Guest/IoT доступ дозволяти лише явно; DHCP-сервери не дублювати в одному bridge.

## 8. UI та безпечне застосування

Розширювати наявні Advanced_OperationMode, Advanced_WMode/2g, Advanced_Printer_others і device-map/printer, httpd/variables та rc events. Єдиний логічний flow Router/Repeater має відображати реальні sw_mode/APCLI значення; не вводити другий несумісний конфіг.
Показувати active band/SSID/BSSID, доступний RSSI, link/gateway/health окремо, причину останнього switch, manual/auto/priority, bounded history. Статус «порт доступний» не називати «принтер готовий»; descriptor model може бути Unknown.
Зберегти погоджений neon-style через існуючі компоненти/токени. Modern preview сам по собі не production/backend; runtime-unverified/DEMO маркування зберегти. Не робити другий Apply/HTTP endpoint для друку.
Apply: спочатку валідована candidate config і конфлікти IP/DHCP; потім rollback snapshot налаштувань малого обсягу; послідовне застосування; перевірка management і повернення за таймаутом. Показати стару/нову адресу та спосіб повернення. Саме відкриття браузером нової сторінки не є повним health proof. Не зберігати паролі у звітах/логах.

## 9. Ресурси та безпека

Конкретний приріст Flash/RAM поки не виміряно: немає готового Mi Mini4.4 образу/boot. Коментарі profile ~0.12MB LPRD/~0.05MB U2EC — не бенчмарк і не гарантований compressed delta. RAW p910nd може вже входити в USB baseline, тому його delta може бути нульовою; це треба виміряти.
Мінімум нових компонентів: один легкий uplink-manager на існуючих RC/iwpriv/NVRAM helpers та UI; network-printer inventory/probe без proxy. Не додавати CUPS, driver packs, media server чи постійний discovery daemon без вимірів. Наявні ext4/exfat/NTFS/FUSE/HTTPS/OpenSSL3.5/AWG у профілі — кандидати перегляду залежностей, не дозвіл видаляти потрібні функції.
Виміри: stripped binaries, squashfs/TRX delta, free firmware bytes, RSS/PSS, CPU під scan/print, OOM/stress, log/flash-write rate, тривалість переключення. Важкі kernel/modules/firmware builds лише GitHub.
Безпека друку потребує окремої реалізації gate: services_usb.c запускає p910nd без -i, хоча p910nd.c:725–726 підтримує bindaddr. Firewall_ex.c:814/1252/1391 має INPUT DROP або ACCEPT залежно від fw_enable_x, є й ACCEPT-гілки інших режимів. Не доведено LAN-only інваріант у всіх режимах. Потрібні явний LAN bind/IPv4+IPv6 policy, firewall-reapply, заборона WAN і небажаних VPN/guest/IoT, перевірка з зовнішніх зон. Це не твердження, що на поточному роутері принтер уже відкритий у WAN.
Network probe: лише дозволені LAN/upstream printer destinations; заборонити WAN-scanning і доступ probe до local management/link-local metadata; не виконувати shell з рядком користувача. UI має використовувати чинну автентифікацію/CSRF-процедуру, bounded input/timeouts і екранування SSID/USB-рядків.

## 10. Обов’язковий IoT і список можливих змін

AGENTS.md і docs/IOT-WIFI-IMPLEMENTATION-CONTRACT.md вимагають основну, гостьову та IoT мережі для кожної прийнятої плати. Mi Mini не може стати supported лише з Router/Repeater. Для 2.4 integrated driver потрібні MBSS capacity, ownership/lifecycle, isolation, target/image і device докази; APCLI/AP/guest/IoT співіснування окремо. Не копіювати MT7603 специфічний MMIO/ACK-код WR1200JS в RT2860.

Потенційні файли наступного етапу (це план, не дозвіл змінювати зараз):
- R configs.build/mi-mini.config, boards.json, tools/board-catalog.py; майбутній board-specific 4.4 overlay/DTS/config/partition recipe після аудиту джерел;
- R .github/workflows/mi-mini-radio-probe.yml та окремі image gates, з перевіркою покриття failure monitor;
- R overlay/.../candidates/mi-mini/* наявний platform/Factory/radio bundle; per-board capability manifest у чинному форматі;
- B trunk/user/rc/net_wifi.c, net_wan.c, net_lan.c, detect_link.c, ralink.c, rc.c, firewall_ex.c;
- B trunk/user/rc/services_usb.c, hotplug_usb.c, services_stor.c; user/libdisk/usb_info.c/.h за потреби;
- B trunk/user/httpd/variables.c, aidisk.c та чинний handler/auth stack;
- B trunk/user/shared/defaults.c; наявні названі ASP-сторінки, словники й neon компоненти;
- майбутні мінімальні uplink/printer metadata helpers — лише після узгодження дизайну, без створення чернеток цим аудитом.
Реальні зміни B оформляти через наявні overlay/prepare механізми; базове дерево й vendor-патчі не замінювати. Інші board profiles не чіпати.

## 11. Поетапний план і приймання

0. WR1200JS — головна робота. Mi Mini робити тільки у вільні вікна; падіння WR CI має пріоритет. Не запускати важку Mi Mini збірку заради аудиту.
1. Звірити R1CM revision/bootloader/MTD/Factory та свіжі N-source; створити capability inventory. Реальні device перевірки лише за окремим дозволом. Без цього image layout не приймати.
2. Відтворити існуючий isolated kernel/radio candidate на GitHub; перевірити toolchain, unresolved symbols, Factory bounds і effective конфіги. Після standard — потрібні optional, без дублів і зі збереженням lane queue.
3. Завершити board platform: Ethernet/switch mapping, SPI/partition, USB PHY/VBUS, PCIe/MT7612E, integrated2.4, GPIO/buttons; встановити fail-closed unsupported controls.
4. Отримати мінімальний повний Router image з обов’язковим IoT; підтвердити image size, rootfs, модулі/firmware/calibration provenance. Чинний Router — регресійний baseline.
5. Підключити ручний WISP uplink на кожному радіо окремо; довести друк і management, не вмикати одночасний bridge двох uplink.
6. Додати health selection/hysteresis/backoff і rollback Apply; потім optional bridge і DNS-SD лише за доказами/розмірами.
7. Повторно використати RAW USB UI; network-printer manual inventory, LAN-only policy, достовірні status labels. IPP-over-USB/proxy — тільки за конкретною потребою.
8. Інтеграційні, навантажувальні і release gates; flash/reboot лише з прямим дозволом і планом відновлення.

Приймальні тести:
- Router: WAN/LAN порти, NAT/DHCP/DNS/IPv6, main+guest+IoT, обидва радіо, management, відсутність CAKE у прийнятому образі.
- Repeater: ручні 2G/5G uplink; AP на іншому radio; same-radio channel constraints; weak RSSI при доброму link і сильний RSSI при великій loss; router/AP reboot; invalid credentials; DHCP/DNS loss; backoff/hysteresis; відсутність нескінченного flap.
- Failover: прогнозований розрив сесій; packet loss/downtime записані, без обіцянки seamless; LAN management залишається доступним; recovery після зміни режиму й невдалого Apply.
- USB print: plug/unplug, cold boot з принтером/без, service toggle, RAW bidirectional compatibility, великий job/клієнтський cancel/reconnect, фактично надрукована сторінка; unsupported printer позначається чесно.
- Ethernet print: IP/DNS, RAW/LPR/IPP лише підтриманих моделей, sleep/offline, IP change; прямий друк у Router і WISP/bridge; IPv6; access policy guest/IoT/WAN.
- Security: WAN socket scan4/6 не бачить друк/керування; reapply firewall і mode change не відкривають порти; malformed SSID/USB/IPP fields; тільки автентифікований Apply.
- Ресурси: RAM/CPU під print+scan+WAN, OOM, reconnect-history bounds, flash writes; порівняти baseline і feature images.
- Preflash: точний SHA/source inputs, Mi Mini board ID, підпис/формат/size, SHA256, ROMFS, effective kernel config, EEPROM read offsets, backup/recovery provenance; жодного запису чужого bootloader/Factory.
Кожний тест мати конкретний артефакт і фактичний результат; чекліст не є доказом проходження.

## 12. Рішення й невідомі

Рекомендовано: WISP/NAT за замовчуванням, ручний вибір+пріоритети як перший етап, RAW USB повторно використати, Ethernet друк напряму; без CUPS, proxy та Avahi у baseline. Це рекомендований дизайн.
Потрібно знати перед hardware/release: точна ревізія R1CM/bootloader/partition map; потрібна management-підмережа й чи обов’язковий bridge; моделі USB/Ethernet принтерів та клієнтські ОС; enterprise/WPA3 uplink потреби; допустимий час failover; кому дозволено друк (LAN/VPN/IoT).
Не стверджується підтримка WPA3/enterprise чи всіх принтерів лише за цим кодом.
Історичний дозвіл на фонове впровадження скасований вимогою власника від 2026-11-17. До WR1200JS acceptance, включно з чотирма фінальними варіантами, Mi Mini роботу не вести — ні паралельно, ні під час очікування збірок. Цей аудит є лише збереженим планом і не надає дозволу на реалізацію. Після WR1200JS acceptance перед виконанням перевірити актуальні правила та наявність окремого доручення.

## 13. WR1200JS під час аудиту

Основний пріоритет перевірено першим: optional848/run42377606982 SUCCESS, exact2278e41529772025f87f81ebd537a16e78b5b010. Артефакт13576577878 опрацьовано в пам’яті: baseline/WSC/reload ELF32 LE MIPS relocatable, довжини й SHA256 збігаються; feature baseline-report hashes звірено.
- baseline5788828B: fb871074b9a3f8c15167d18c59e1813171c91ef1ed98391d6c15394953fe23d5
- WSC6398316B: 0bbdb3022b5674497d1703a0a2853efa1c6018d5837880347c3b6caccca74c78
- reload5790896B: 47c289cb976b613a92cd079cd3cd3e151eabbd29a9d56d307395632dbd632aa0
Це target-перевірка того коміту; не runtime, не завершення ACK/ID і не покриття пізніших змін.
Після підготовки цього документа повернути основний фокус на WR1200JS. Жодні двійкові артефакти не збережені на Windows-диску.

## Рішення власника після аудиту — LPRD, 2026-11-07

За прямим дорученням власника configs.build/mi-mini.config тепер включає CONFIG_FIRMWARE_INCLUDE_LPRD=y. Це оновлює попередній опис вимкненого LPRD, який зберігається як стан на момент аудиту. U2EC вимкнений, RAW/p910nd — основний шлях; існуючий UI повторно використовується. Включення пакета не доводить зібраного образу чи роботи служби. Потрібні ROMFS/usblp, LAN/дозволений VPN firewall, boot/hotplug і друк на конкретному принтері. LPRD-рішення збережене як історичний стан конфігурації; воно не дозволяє продовжувати Mi Mini роботу до WR1200JS acceptance з усіма чотирма варіантами.
