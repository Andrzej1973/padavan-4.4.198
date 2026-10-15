# Хто зараз виконавець

Оновлено: 2026-10-15. Правила ролі — `docs/AGENT-HANDOFF-RULES-SOL-DEEPSEEK.md`, розділ 12.

## Поточний виконавець — передача роботи

- **Новий виконавець:** DeepSeek, за прямою вказівкою користувача «Передає роботу іншому агенту» (2026-10-15).
- **Sol:** завершив запис передачі й припинив редагування коду; далі перевіряльник.
- Пряме повідомлення DeepSeek не доставлено: його чат не знайдено серед доступних чатів застосунку. Цей документ потрібно передати йому для прийняття роботи.
- Одна спільна робоча копія, один виконавець. Не запускати конкурентні зміни.

## Актуальний стан передачі (має пріоритет над історією нижче)

- Код перед передачею: `cc140d3`, гілка `main`; робоча копія
  `C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\router-guide-work`.
- Активний блок: EoIP. Читати `docs/EOIP-SERVICE.md` і `tools/eoip/`.
- Реалізовано й перевірено CI: валідація конфігурації, read-only netlink-запит, owned create/remove CLI,
  приватні runtime-записи, оркестрація lifecycle, configure-адаптер (`configure.h`), контролер
  (`controller.h`: мапінг слота на `wr-eoip<slot>` і alias `wr-eoip:<slot>:v1`, реальні ops з
  інжектованим транспортом) та службовий вхід `worker.c` (start/stop/status; профіль з `ENABLED=0`
  зупиняє слот тим самим перевіреним шляхом очищення, а не лишає напівстворений інтерфейс).
- Пакування: `integrate-eoip.py` збирає `/usr/bin/eoip-service` поряд із `eoip-ctl`; локальний прогон
  скрипта на макеті дав повний include-closure пакета.
- Успішні CI: 38772832369 (configure), 38775647354 (контролер), 38776214864 (фікстура воркера),
  38776427458 (фікстура + димовий запуск реального бінарника: `slot absent 0`), 38778372364 (фікс include-ів).
- **Відкрита перевірка, першим ділом:** повна збірка 288 ВПАЛА на `worker.o` — у sysroot-і uClibc
  `linux/if_tunnel.h` вимагає `IFNAMSIZ` і `struct iphdr`. Виправлено в `cc140d3` (`net/if.h` і
  `linux/ip.h` перед `linux/if_tunnel.h`; у `configure.h` замінено `linux/if.h` на `net/if.h`).
  Повна збірка 289 на `cc140d3` на момент передачі ще виконувалась: перевірити її результат і не
  заявляти про компіляцію воркера для MIPS до підтвердження.
- Наступний крок: persistence (nvram-схема слотів + defaults/variables + `/etc/storage`) і політика
  завантаження default-off через rc-диспетчер, далі EN/UK/RU WebUI та інструкція.
- Не чіпати сторонній diff `tools/prepare-wifi-hwnat-mode.py` (лише CRLF) і не додавати untracked
  фікстури/cache у Git.
- ZeroTier заморожено; прошивання й reboot роутера потребують окремого дозволу; приймання на пристрої
  не завершене.


## Історія попередніх етапів

Нижче залишені попередні записи; вони не визначають поточного виконавця чи наступний крок.
## Робоча копія та ціль

- Робоча копія: `C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\router-guide-work`, гілка `main`.
- Репозиторій: `Andrzej1973/padavan-4.4.198`.
- Мета: порт YOUHUA WR1200JS на Linux 4.4.198 зі збереженням чинних налаштувань
  і потрібних функцій, без CAKE; головні критерії — стабільність і збереження
  доступу до роутера. Порядок: WR1200JS → Mi Mini → локальні бази й офлайн-проєкт.

## Активне завдання виконавця

ZeroTier, сторінка `Advanced_zerotier.asp`. Етап 1 — локалізація EN/UK/RU і
обмежене оновлення статусу замість ручного перезавантаження — підтверджено
збіркою 271 (крок «Verify ZeroTier page localization and bounded status
refresh» пройшов на скомпільованому образі).
Деталі: `docs/evidence/ZEROTIER-PAGE-LOCALIZATION-2026-10-14.md`.
Етап 2 — групування Moon, статичних маршрутів і застарілого NAT під одним
згорнутим блоком із збереженням доступності кнопки «Застосувати» — реалізовано
в коді й перевірено локально; компіляція підтверджена збіркою 272, на пристрої ще ні.
Деталі: `docs/evidence/ZEROTIER-ADVANCED-CONTROLS-2026-10-14.md`.

## Поточний інкремент (поза ZeroTier)

Поточне продовження Sol: USB/IP — кандидат `tools/usbip/service.sh` та
ізольований тест. Правила LAN-only вже перевірені окремим CI. Контролер
не пакується, не запускається на роутері й не підключений до boot/WebUI.
Наступний крок: перевірити його CI, потім завершити інтеграцію з firewall
rebuild, persistence й автентифікованими діями. ZeroTier залишається без змін.
Оновлення: ізольований CI контролера пройшов (38639330507). Підготовлено
атомарні правила порту 3240 у чотирьох генераторах firewall; локальне
застосування до базового джерела успішне. Наступний крок — перевірити native CI
та повну збірку цієї інтеграції, далі persistence/boot і керування через WebUI.
Маркери власності, stop timeout і відмова restart мають перевірятися до
пакування. Жодних команд на живому роутері цього етапу не виконувалося.

Продовження 2026-10-15: повна збірка №274 та CI станів служб успішні на
`8d634d7`. Додано пакування ручного контролера `wr-usbip` і його політики з
перевіркою точної відповідності файлів у ROMFS. Цей новий інкремент ще потребує
повної збірки; автозапуск, persistence й WebUI залишаються незавершеними.
Наступний крок: перевірити пакування, потім додати вимкнене за замовчуванням
постійне налаштування та інтеграцію життєвого циклу. ZeroTier не змінювався.

Додано генератор default-off `usbip_enable` та умовні RC boot/shutdown hooks.
Застосування до базових `cflags.mk`, `defaults.c`, `services.c` пройшло локально.
Компіляція нового інкремента і збереження на пристрої ще не підтверджені;
наступний крок — звірити CI, далі автентифіковане керування й правдивий
поточний стан у WebUI. Живий роутер не змінювався.

Наступний інкремент USB/IP: перемикач запитаного стану EN/UK/RU через чинний
General Apply, окрема подія bit 55 та RC restart/stop. Локальна трансформація
базових C/ASP із тестовими словниками успішна; compile/Apply на пристрої ще не
перевірені. CI служб `397ac99` успішний, повна збірка ще активна на перевірці.
Далі перевірити повну компіляцію UI, потім інвентаризацію USB та керування
експортом. Жодних змін на живому роутері або в ZeroTier.

Виправлення CI: run 38740589879 впав до компіляції через зайнятий ZRAM bit 55.
Усі 64 біти вже розподілено після Stubby. USB/IP переведено на чинну USB/spooler
транзакцію; `reconcile` не перезапускає вже запущений власний демон. Зміна
USB/IP також оновлює printer spoolers. Додано source fixture у короткий CI та
перевірки reconcile/timeout у lifecycle fixture. Локальний source fixture
успішний; Linux CI та повна компіляція цього виправлення ще очікуються.

CI 38741251046 успішний, включно з reconcile/timeout та Apply fixture.
Попередня повна збірка 38739882902 впала при копіюванні політики: бракувало
вкладеної ROMFS-папки. Makefile тепер створює її явно. Інструкцію USB/IP у
генераторі комплектної інструкції розширено; локальна генерація TXT/Markdown
успішна. Далі перевірити повну збірку виправленого пакування.

Підготовлено наступний інкремент: обмежений read-only список USB sysfs у
USB/IP WebUI з EN/UK/RU, початковим і ручним оновленням. Прив’язка до
usbip-host не видається за передачу даних. Локальна трансформація успішна;
native sanitizer fixture додано до CI, результати ще не отримано. Run
38741650267 на останній перевірці компілює без помилок кроків. Далі звірити
обидва CI й пакування, потім додати контрольований bind/unbind та перевірки.

Підтвердження: service run 38742194847 на `51777f0` успішний; журнал містить
виконання lifecycle, Apply та native ASan/UBSan inventory fixture. Це тестові
sysfs-файли, не фізичний USB. Повні runs 38741650267 і 38742194875 ще активні,
їх не перезапускали. Перед bind/unbind потрібні окремі перевірки параметрів,
власності процесу та запобігання від’єднанню зайнятих дисків/мережевих пристроїв;
не подавати read-only EJ endpoint як механізм зміни прив’язки драйвера.

Додано кандидат read-only preflight `tools/usbip/device-policy.sh`: перевіряє
ID, USB hubs, змонтовані block partitions, swap і мережеві/TTY дочірні пристрої.
Не пакується й не виконує bind/unbind. Linux fixture додано у короткий CI,
результат ще очікується. Це не усуває hotplug/open/mount races; мутаційний
контролер і UI залишаються відкритими. Обидві повні збірки ще компілювалися
без повідомлених помилок кроків на повторній перевірці.

Preflight CI 38743018133 на `dab0502` успішний. Підготовлено ручні контролерні
bind/unbind із чотирма argv, перевіркою ID виробника/пристрою, lifecycle lock,
власного демона для bind та idle usbip_status=1 для unbind. Пакування обох
helper-скриптів і порівняння ROMFS додано; Linux fixture нового action ще має
пройти. WebUI mutation та persistence export лишаються незавершеними;
перевірки не усувають kernel hotplug/open/connect races. Роутер не змінювався.

Підтверджено повну збірку №279 (`f86005b`): успішна, фінальний пакет завантажено
у `../build279-final`, SHA256 TRX/інструкції/конфігу записано в
`docs/evidence/WR1200JS-BUILD279.md`. №279 передує inventory та bind/unbind;
не видавати її за перевірку пізніших змін. CI 38743571036 на `f2ad65c`
успішний і справді виконав action/preflight fixtures. Наступний крок —
перевірити новіший образ і додати фонові WebUI-дії: синхронний kernel bind
у головному HTTP-процесі може затримати доступ, тому його не додано.

Збірка №280 (`51777f0`) також успішна; пакет завантажено в
`../build280-final`, SHA256 та межі доказів —
`docs/evidence/WR1200JS-BUILD280.md`. Вона підтверджує компіляцію/пакування
inventory, але передує ручним bind/unbind. Фоновий executor ще не реалізовано:
потрібні окремий процес, закриття успадкованих HTTP fd, один активний job,
ідентифікатор результату й явний unknown за застарілих/непідтверджених даних.
WebUI мутації потребують safe session, POST і непередбачуваний CSRF token;
не підміняти ці вимоги синхронним eval або прапорцем підтвердження у формі.

Почато фоновий executor: кандидат `tools/usbip/job-worker.h` з одним lock,
випадковим ID, атомарним result, закриттям HTTP fd та окремим controller child.
Native fixture додано у sanitizer CI; локально перевірено diff, виконання C
очікується на Linux CI. Не пакується/не викликається з HTTPD. Далі перевірити
CI, реалізувати читання/вік результату й async reap перед WebUI реєстрацією.

CI 38745059831 на `5ff4723` успішний: журнал підтвердив native sanitizer
background-job fixture (nonblocking start, one job, ID/result, failure, FD
closure, private directory). Повна збірка №281, run 38743571489 на `f2ad65c`,
також успішна; її фінальний пакет у цьому інкременті ще не завантажено.

Додано строгий reader результату worker: ID, canonical JSON, state/code,
приватний regular file без symlink, monotonic час/вік; помилки очищають output
до unknown. Додано waitpid лише tracked PID з WNOHANG. Sanitizer fixture
розширено; CI цього інкремента ще очікується. Далі підключити safe POST/CSRF,
reader та неблокувальне прибирання до HTTPD, потім UI; нічого не вмикалося
на фізичному роутері.

Reader/reap CI 38745527381 успішний. Підготовлено HTTP integration: окремий
auth route `wr_usbip_action.cgi`, actual POST accessor у httpd.c, safe session,
random CSRF token, ack, body limit 512, async launch і matching result reader
з віком 120 секунд. Локальна трансформація базових C успішна; native fixture
із mock scheduler додано, Linux CI й повна компіляція ще очікуються. Кнопки
та відображення результату в USB UI залишаються наступним кроком. Нічого не
запускалося на живому роутері; ZeroTier не змінено.

HTTP CI 38746035978 успішний; повна збірка 38746036196 на останній перевірці
ще активна. Додано USB/IP action UI EN/UK/RU: вибір із актуального inventory,
ack, bind/unbind, один запит, matching job result, обмежене опитування та ручне
перечитування. Локальний Node fixture й трансформація сторінки успішні.
Далі звірити CI/full image, перевірити готову сторінку; фізичний тест і
export persistence залишаються відкритими. Інструкцію оновлено.

Підтверджено №283 (`31a6496`): full run 38746682565 і service run 38746682477
успішні. Пакет завантажено в `../build283-final`, TRX/guide/config hashes та
перевірений локальний ZIP — `docs/evidence/WR1200JS-BUILD283.md`.
USB/IP код/пакування підтверджені в цьому обсязі; фізичні дії, браузер,
реальна передача й export persistence ще не підтверджені/не завершені.
Далі продовжувати незавершений service scope (USB export persistence/EoIP)
зі звіркою чинних вимог; не називати порт завершеним і не прошивати без дозволу.

Наступний service increment — EoIP. Звірено наявний IPv4 module/eoip-ctl і
повний потрібний обсяг. Додано pure C validator requested-профілю (IPv4, ID,
MTU, keepalive, bridge syntax) та sanitizer fixture. Не пакується і не змінює
тунелі. Межі й наступні кроки: `docs/EOIP-SERVICE.md`. Linux CI ще очікується;
далі owned lifecycle, конфлікти таблиці, persistence, UI та фактичні статуси.

EoIP config CI 38751553924 успішний. Додано RTM_NEWLINK decoder для
ifindex/flags/MTU/master/kind/alias із визначенням власності за kind+міткою,
перевірками довжин/sequence/name та unaligned-safe читанням. Native fixture
додано; CI ще очікується. Netlink transport і lifecycle ще не підключені;
далі kernel-origin transport/identity та власні start/stop. Живі інтерфейси
не змінювалися.

Observer CI 38752028099 успішний. Додано read-only RTM_GETLINK transport:
kernel sender, sequence, length/truncation, 1-секундні send/receive timeouts;
ENOENT/ENODEV відрізняються від unknown. Fixture включає справжні read-only
запити lo/відсутнього інтерфейсу на Linux CI runner, без мережевих змін.
CI ще очікується; MIPS/роутер і lifecycle не перевірено. Далі — owned start/stop.

Query CI 38752406828 успішний. Наявний eoip-ctl розширено owner-параметром:
мітка IFLA_IFALIAS входить у той самий exclusive RTM_NEWLINK, що name/kind.
Дозволено лише add IPv4 wr-eoip0..7 із відповідною міткою; set не може
привласнити сторонній інтерфейс. Fixture перевіряє реальний CLI request із
mock netlink, без створення інтерфейсів. Додано trigger full build для EoIP
candidate source. CI/повна компіляція ще очікуються; далі owned stop/rollback.

Owned-create CI 38752941074 успішний. Додано `owned-remove SLOT IFINDEX`:
query kind/alias/index → delete by index → absence postcheck; foreign/unknown
не видаляються, повторна відсутність є успіхом. Старий remove name збережено.
Query headers пакуються з eoip-ctl; додано wrapped fixture і full image marker.
Нові CI ще очікуються. Далі вищий lifecycle із lock/recorded identity,
rollback, persistence та UI; query/delete race ще не усунуто. Роутер не змінено.

Owned-remove CI 38753499644 успішний. Додано кандидат runtime-state: private
directory, nonblocking flock, CLOEXEC, versioned per-slot ifindex, atomic write,
відмова mismatch/corrupt/symlink. Це volatile recovery state, не persistent
профілі. Не пакується. Sanitizer fixture додано, CI ще очікується. Далі
об’єднати create/configure/remove під одним lock із rollback і kernel postcheck.

Runtime-state CI 38753942819 успішний. Додано lifecycle orchestration під одним
lock: absence → create → query identity → record → configure → postcheck;
rollback/stop очищають record лише після підтвердженої відсутності. Існуючі
або foreign links не замінюються. Fixture mock-мережі + справжніх record files
додано, CI ще очікується. Реальні adapter/configure і firmware wiring не
завершені; missing ACK/orphan recovery та повний parameter postcheck відкриті.

Lifecycle CI 38754523227 успішний. Додано endpoint/ID/keepalive observation
і повний п’ятиатрибутний postcheck профілю; missing/mismatch веде до rollback.
Приватні ABI IDs звіряються з eoip_proto.h у fixture, foreign link data не
інтерпретуються як EoIP. Нові CI ще очікуються. Реальний configure adapter,
firmware lifecycle wiring, persistence/UI та фізичне приймання лишаються відкритими.

Локалізація успадкованих значень словників: 33 китайські значення в
`trunk/user/www/dict/EN.footer` замінено англійськими, а `UK.dict` і `RU.dict`
доповнено відповідними перекладами. Новий крок
`overlay/padavan-4.4/scripts/localize-inherited-dicts.py` вписано в застосування
порту та в перевірки образу.
Деталі: `docs/evidence/INHERITED-DICTIONARY-LOCALIZATION-2026-10-14.md`.

## Доступ до пристрою

- Станом на 2026-10-14 доступ працює: тунель користувача відкриває `192.168.20.1`
  (SSH `dropbear 2024.85`, HTTP `httpd`, realm `WR1200JS`).
- Важливо: у пісочниці `ssh` на `PATH` підмінено заглушкою, тому потрібен повний
  шлях `C:\WINDOWS\System32\OpenSSH\ssh.exe`. Підвищення прав не потрібне.
- Пристрій працює на ядрі 4.4.198 (збірка 2026-10-11) — це старіша збірка, ніж HEAD.
- Деталі: `docs/evidence/DEVICE-RUNTIME-ACCESS-2026-10-14.md`.
- 2026-10-14 виконано read-only аудит прошитої збірки за критеріями приймання
  (крок 6): підтверджено завантаження 4.4.198, WAN/LAN, обидва діапазони Wi-Fi,
  AmneziaWG із живим handshake, служби та збережену конфігурацію. Прошита збірка
  старіша за HEAD.
  Деталі: `docs/evidence/DEVICE-READONLY-AUDIT-2026-10-14.md`.

## Журнал передачі ролі

| Дата | Подія | Деталі |
| --- | --- | --- |
| 2026-10-13 | Роль у DeepSeek (за передачею попереднього етапу) | Робота над DNS-відновленням і службами. |
| 2026-10-14 | Роль передано агенту Sol | Користувач: «Будь виконавцем». Створено цей файл і розділ 12 правил. |
| 2026-10-15 | Передачу роботи відкрито для DeepSeek | Користувач: «Передає роботу іншому агенту». Код `cc140d3`; відкрита повна збірка 289. |
| 2026-10-14 | Перевірено доступ до пристрою | Тунель користувача; read-only SSH працює з пісочниці. Автоперевірка підтверджень усе ще зламана. |
| 2026-10-14 | Escalation виправлено, аудит пристрою | Перезапуск Codex після правки `models.json`; read-only аудит прошитої збірки за критеріями кроку 6. |
| 2026-10-14 | Локалізація успадкованих словників | 33 китайські значення в `EN.footer`; `UK.dict` і `RU.dict` доповнено; крок і перевірка додані у workflow. |

## Як змінювати цей запис

Оновлення робить лише агент, який отримав роль, і лише після явної вказівки
користувача. Зупинка мети ставить роль на паузу; відновлення мети тим самим
агентом повертає роль без нового погодження.
