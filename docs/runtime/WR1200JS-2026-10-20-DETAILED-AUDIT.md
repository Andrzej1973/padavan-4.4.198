# WR1200JS — докладний read-only аудит, 2026-10-20

## Межі й відтворюваність

Знімки знято через Windows OpenSSH, `ASUS@192.168.20.1`, приблизно
15:14–15:26 UTC. Служби, радіомодулі, маршрути, NVRAM і firewall не змінювали;
перезавантаження, прошивання та очищення журналів не виконували. Діагностичні
DNS/HTTP-запити та SSH-сесії самі створюють трафік і записи журналу.

Перевірено ідентичність, CPU/RAM/swap, flash/mounts, процеси, модулі,
слухачі, інтерфейси/лічильники, маршрути/rules, міст, IPv4/IPv6 firewall,
DNS-конфіг/відповідь, VPN handshake/лічильники, Wi-Fi stat/private ioctl inventory,
активні .dat, kernel config, журнали, thermal paths і наявність CLI providers.
Зібрано **54 числові enable-прапорці та 89 несекретних Wi-Fi select-полів**;
значення й оцінки містить сусідній JSON. Для неперевірених прапорців явно
вказано, що зібрано лише збережене значення. Це не доказ роботи всіх 143 полів.
Неінвентаризовані текстові параметри/нестандартні прапорці залишаються поза цим
переліком; паролі, ключі та SSID у нього не включені.

23 первинні текстові знімки зберігаються **поза Git-репозиторієм**:
`C:/Users/ANDRZEJ/Documents/Codex/2026-09-29/router-audit-private-20261020/`.
Там є процеси, мережеві адреси, журнали й локальні ідентифікатори; не публікувати
їх без очищення. JSON містить імена/розміри/SHA256 для перевірки незмінності.
Інший локальний агент може звірити висновки з цими файлами.

## Прошивка та ресурси

- Syslog прямо ідентифікує встановлену **4.4.198.9-474_4fc90055**. Новіші CI
  #492/#493 не означають, що цей роутер їх уже виконує.
- Linux 4.4.198, kernel build 2026-10-18 14:19 UTC; MT7621, чотири логічні CPU.
  Uptime понад дві доби, load приблизно 0.01/0.03/0.02.
- MemTotal 123652 kB, MemAvailable 51940 kB у першому знімку.
- `/dev/zram0` активний swap: 30912 kB, використано 0, priority 32767.
- Flash 16 MiB; Factory 64 KiB, Storage 256 KiB. SquashFS `/` read-only,
  його 100% у df є властивістю образу, а не переповненням writable tmpfs.
  `/tmp` використано 428 KiB із 24 MiB, `/var` 56 KiB із 4 MiB.
- Kernel taint 4096 (out-of-tree module flag); сам по собі не означає crash.
  У доступних журналах не знайдено panic/Oops/Call Trace/OOM. Це не гарантує
  відсутності історичних збоїв поза збереженим журналом.
- MIPS interrupt ERR зріс 381671 → 381674; значення зафіксоване, його причина
  й зв'язок із мережевими симптомами не встановлені.

## Мережа, VPN, DNS та служби

- `br0`: eth2, ra0, rai0. WAN eth3 має carrier=1; operstate показує unknown.
  Conntrack 243/16384 у знімку. IPv4/IPv6 filter INPUT/FORWARD мають default DROP;
  це не повний тест доступності/ізоляції всіх правил.
- За приблизно чотири хвилини: WAN RX +23053 пакетів, RX drops +243,
  RX errors +0; br0 RX drops +4. Пакети можуть відкидатися з різних причин;
  ці лічильники не встановлюють причину й не дорівнюють виміряній втраті
  користувацького трафіку. Для eth2/ra0/rai0/wg1 у цьому інтервалі приросту
  errors не було; WG TX drops/errors також не зросли.
- `hw_nat_mode=2`, `sfe_enable=2`; HNAT і SFE-модулі завантажені.
  Прискорення конкретного потоку/throughput не вимірювали.
- AWG-модуль і `wg1` присутні; один peer має handshake о 15:14:40 UTC та
  зростаючі RX/TX. Інший peer без handshake. Ключі/endpoint-и не публікуються.
- Stubby enabled=1, процес і loopback :5453 присутні. Конфіг вимагає TLS
  authentication та TLS-only transport, два upstream TCP/853 ESTABLISHED.
  dnsmasq має no-resolv і звичайний upstream 127.0.0.1#5453; є окремі прямі
  DNS-винятки для часу. example.com через 127.0.0.1 успішно резолвиться.
  IPv6/client/browser DNS bypass і повний no-leak тест не виконано.
- DoH, Privoxy, USB/IP, U2EC, ZeroTier збережені вимкненими; це не acceptance
  їхнього start/stop. Пакети деяких із них присутні незалежно від процесу.
- Dropbear працює з -s, key-auth успішний; authorized_keys у перевірених
  home-шляхах мають 0600. Прямий LAN HTTP без credentials повертає 401.
  Loopback HTTP повертає 200; не переносити цей результат на зовнішній доступ.
- vlmcsd працює та слухає :1688; активація не перевірялася. Watchdog процес
  присутній; це не перевірка hardware watchdog recovery.
- DHCP enabled=1, dnsmasq працює, 16 lease-записів (не 16 доведених online-клієнтів).
- DDNS enabled=1, журнал зберігає помилки inadyn code 48 від 18 жовтня;
  успішне актуальне оновлення не підтверджене.
- lprd_enable=1 та wins_enable=1, але lpd/nmbd не знайдені ні shell type,
  ні в перевіреному /usr/sbin. Це збережені прапорці без доведеного provider;
  потрібне зіставлення з capability/UI, а не мовчазне ввімкнення пакетів.
- `tc` відсутній у live #474. QoS-політику тут підтвердити не можна.
  Пакування tc виправлене й підтверджене image-аудитом #492, але не встановлене.
- USB mass-storage не виявлено; storage/USBIP/U2EC transfer-тести не виконано.

## Wi-Fi, KVR та Beamforming

- Основні ra0/rai0 активні; guest-enable обох діапазонів =0. Окремого IoT
  bridge/DHCP у знімку немає; wr_iot_enable відсутній. BssidNum=2 — не третій BSS.
- 2.4 GHz channel 13, HT_BW=0; 5 GHz channel 40, HT_BW=1/VHT_BW=1.
  У 5-GHz .dat другий профіль OPEN/NONE, але guest flag=0 і vif не доведений
  активним; не трактувати цей рядок як доказ відкритої доступної мережі.
- 5-GHz driver stat: температура 37 (driver readout), average RSSI -53,
  last TX VHT MCS9/2SS/80 MHz. CRC/PER та retry — накопичені vendor counters;
  формати/відсотки не є контрольним тестом якості. Для 2.4 GHz CRC PER=39.6%,
  для 5 GHz=26.0% у цьому знімку; потрібне спостереження під відомим навантаженням.
- CPU thermal/hwmon paths відсутні; CONFIG_THERMAL/HWMON вимкнені.
  Не показувати температуру радіочипа як температуру CPU.
- wl_txbf=1, але wl_txbf_en=0, CONFIG_MT76X2_AP_TXBF_SUPPORT вимкнений,
  ITxBfEn/ETxBfEnCond=0. Beamforming не підтверджений, saved toggle вводить в оману.
  Board capability fix уже підготовлений окремо локально, ще не підтверджений live.
- **rt_HT_80211KV=1, rt_HT_80211R=1, wl_HT_80211KV=1, wl_HT_80211R=1.**
  У live kernel MT7603E DOT11K_RRM, WNM і DOT11R_FT вимкнені. Для mt76x2
  CONFIG_RT_DOT11K_RRM/RT_DOT11R_FT увімкнені; Makefile підключає RRM/FT objects.
  WNM/802.11v compiled path для 5 GHz ще не доведений.
- Обидва .dat містять RRMEnable=0/WNMEnable=0, а потім двічі 1;1.
  Pinned RC ralink.c генерує саме ці дублікати. RTMPGetKeyParameter в обох
  драйверах використовує перший rtstrstr-збіг: попередній нуль перекриває
  пізніші записи для споживачів цього parser-а. FT flags теж дублюються.
- `prepare-wifi-kvr-config.py` усуває ці дублікати й shadowing default-и.
  Локальний C emitter-тест пройшов 16 комбінацій band/flags/DBDC під -Werror.
  Це code-level виправлення; новий image/runtime результат ще потрібен.
- Band Steering enabled=1, daemon і control socket присутні, ctl status=active.
  Це не підтверджує фактичного переходу клієнта, 802.11k/v чи fast transition r.
  Для KVR потрібні per-band capability gates та over-air/client acceptance.

## Що й чому заповнює журнал

Syslog стартував 18 жовтня 17:33; файл мав 365693 байти перед аудитом і
367679 після частини перевірок. syslogd запускається з -s512 -b0 -S -D
-O /tmp/syslog.log. Це RAM-файл, не безмежний flash-log. printk=7/4/1/7;
зміна console_loglevel сама по собі не прибирає записи, які читає klogd.

У збереженому файлі:

- **981 HNAT mtk_pong_hqos_handler:drop**, усі reason=0x16:
  802 на rai0, 179 на ra0; перше 18 жовтня 17:33:43, останнє 20 жовтня 18:10:45.
- **343 Dropbear записи**: підключення, key-auth, disconnect; поточний аудит
  створив додаткові легітимні SSH-сесії. Один історичний nonexistent-user attempt.
- 185 EAPOL unknown client-index, 162 PhyCap association, 90 ADDBA policy,
  22 MIC mismatch, 18 точних BndStrg NULL-interface повідомлень. BndStrg повідомлення
  закінчуються біля Wi-Fi reconfiguration 19 жовтня 21:30, не безперервно зараз.
- 24 illegal-channel записи й 5 RTMPDrvClose radio-off fail у збереженій історії.
  Час/контекст відрізняються від поточного робочого каналу; причину ще не доведено.

Два знімки kernel ring містили ті самі 1985 рядків: під час цього інтервалу
нових kernel-повідомлень не було. syslog приростав через наш SSH, тому це
накопичена діагностика за дві доби, а не доведений безперервний flood зараз.

Перевірений pinned **raeth/mtk_hnat** hnat_nf_hook.c:1783–1825 друкує warning
через printk_ratelimited та повертає NF_DROP після невдалого fast-path helper.
nf_hnat_mtk.h:94 задає HIT_BIND_FORCE_TO_CPU=0x16. Це не повідомлення про
успішний offload; його не можна просто приховати як нешкідливий текст.
Початково перевірено також іншу mediatek/mtk_hnat копію; для висновку обрано
raeth-шлях, який відповідає шляху live hw_nat.ko. Точне зіставлення бінарника
із перетвореним джерелом #474 й конкретного skb/flow ще потрібне.

## Наступні виправлення та неперевірені вимоги

1. Включити KVR duplicate-record fix у CI; далі перевірити per-band build,
   parser/handler, management frames і поведінку клієнта. Не називати все KVR
   робочим за saved flags. Вирішити unsupported 2.4-GHz UI/backend відповідно
   до board capability policy; не прибирати спільний код інших плат.
2. Розібрати HNAT external-device mapping і failure return для reason 0x16,
   зберігаючи recovery/management. Не вимикати offload live і не маскувати drops.
3. Зіставити EAPOL/MIC/ADDBA/illegal-channel/radio-off записи з драйверним кодом
   і часовими вікнами, перш ніж змінювати debug рівні або звинувачувати пароль.
4. Усунути хибну видимість TXBF та saved-enabled опцій без provider; перевірити
   final ROMFS і UI gates. Збережені налаштування не стирати автоматично.
5. Підтвердити DDNS update, DNS leakage/IPv6 bypass, QoS/SFE traffic, IoT isolation,
   усі service lifecycle/recovery/persistence та client roaming окремими тестами.
6. Перевірити браузерний Apply та actual running config після майбутнього
   погодженого оновлення. Цей аудит не дозволяє flash/reboot/restart служб.

Невдалі/обмежені команди: logread та iwconfig відсутні (використано
/tmp/syslog.log і vendor stat); wg show all interfaces має неправильний синтаксис
для цього CLI (виправлено на wg show interfaces); get_mac_table не повернув
клієнтських рядків, тому нуль клієнтів не стверджується; thermal paths відсутні.
Частина section exit codes відображає останню команду, не успіх кожної команди;
висновки перевірені за фактичним вмістом і stderr, а не за загальним exit=0.
