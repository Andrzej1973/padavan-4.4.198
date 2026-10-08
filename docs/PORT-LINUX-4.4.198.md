# План переходу WR1200JS на Linux 4.4.198

Дата аудиту: 2026-09-30

## Ціль

Підготувати Padavan для YOUHUA WR1200JS на Linux 4.4.198. Зберегти налаштування `configs.build/wr1200js.config` та підтвердити сумісність кожної потрібної функції з новою основою. CAKE не входить до цілі перенесення.

## Поточний стан

- Робоча гілка цього репозиторію: `experimental/hadzhioglu-compare`.
- У локальному checkout є два коміти попереду `origin`, незакомічені зміни `configs.build/wr1200js.config` і `pre-build.sh`, а також локальні файли інтеграції CAKE. Цей аудит їх не змінює.
- Файл `variables` зараз вказує на `nilabsent/padavan-ng`, гілку `master` і `HEAD`; поточний білд тому не є збіркою Linux 4.4.198.
- Кандидатна база для контрольної перевірки: [hanwckf/padavan-4.4](https://github.com/hanwckf/padavan-4.4), commit `ff77acc51a4ad5d88660f0ac25a34a1f6f9060c6`.
- Для цільової плати знайдено ближчий кандидат: [vipshmily/padavan-4.4](https://github.com/vipshmily/padavan-4.4), commit `c25283e915a2a00a763774dd255b14aff997285e` від 2024-07-30. У ньому вже є WR1200JS board files, DTB та kernel config для Linux 4.4.198. Він стає основою подальшого порту після окремої контрольної збірки й аудиту джерела/toolchain.
- WR1200JS kernel config кандидата вмикає обидва потрібні радіодрайвери MT7603E і MT7612E та EEPROM offsets 0x0/0x8000. Це підтверджує наявність опцій у вихідному дереві, але ще не доводить калібрування і роботу Wi-Fi на роутері.
- Кандидатний profile має USB вимкненим, хоча плата має один USB-порт. Workflow зливає USB/PHY/host/storage kernel options з K2P-USB в тимчасовий WR kernel config; target template окремо вмикає USB і файлові системи.
- Кандидатний загальний DTS успадковує розмітку K2P. Локальний WR1200JS layout зберігає відомі адреси Padavan 3.4: Firmware 0x50000+0xF70000, Storage 0xFC0000+0x40000, SPI 10 MHz. Перед образом треба звірити цю таблицю з image packer і bootloader.
- Workflow кандидата використовує власний toolchain release на GitHub; збірка викликає `make WR1200JS TOOLCHAIN=mipsel-linux-uclibc`, потім Padavan `build_firmware.sh`. Архів uClibc має ім'я `mipsel-linux-uclibc.tar.xz`; checksum збережено як build evidence, але це саме по собі не автентифікує upstream archive.
- Збірочна ціль кандидата використовує WR1200JS kernel config і board files; workflow накладає власний WR1200JS DTS та layout include. DTB обирається через `CONFIG_RALINK_BUILTIN_DTB_NAME="wr1200js"`, тому зміна DTS Makefile не потрібна. Потрібно ще перевірити завершений kernel config/image output на Linux runner.
- Поточний workflow проєкту очікує Padavan-ng структуру та toolchain 3.4, тому порт 4.4 лишається окремим workflow й не змінює робочу збірку.
- Додано окремий ручний workflow `.github/workflows/build-padavan-4.4-control.yml`: він збирає K2P на базі `hanwckf/padavan-4.4` як незалежну перевірку старішого 4.4 середовища. Він не перевіряє pinned базу `vipshmily` і не є прошивкою WR1200JS. Перевірку цільового CI запуску ще треба завершити.
- У джерелах WR1200JS кандидата є профіль MediaTek AP драйверів для MT7603E та MT7612E. Треба ще перевірити image build hooks, EEPROM/калібрувальні файли й роботу на платі.
- Поточне визначення WR1200JS містить власні GPIO кнопок/LED, один USB-порт і параметр перестановки USB-порту. Ці значення треба виразити у профілі плати й DTS 4.4, а не копіювати з K2P.
- Розмітка флеш-пам'яті потребує особливої уваги. У WR1200JS Firmware починається з `0x50000` і має розмір `0xF70000`, Storage починається з `0xFC0000` і має `0x40000`. У DTS K2P з 4.4 для 16 MiB Firmware має `0xF30000`, а Storage починається з `0xF80000` і має `0x80000`. Розмітку K2P не можна використовувати як є.
- У upstream CI плати MT7621 згруповані за кількістю USB-портів: без USB, один USB і два USB. WR1200JS має йти адаптованим шляхом для одного USB, не через шаблон K2P.

## Етапи

1. **Зафіксувати контрольний стан і карту конфігурації.** Зберегти перелік увімкнених функцій, відповідні символи конфігурації, пакети, драйвери та перевірки. Відокремити зміни, які вже належать локальному робочому дереву.
2. **Перевірити й зафіксувати основу 4.4.198.** Визначити точний commit, toolchain, збірочні сценарії, ліцензійні/вендорські компоненти та спосіб відтворюваної збірки. Не перемикати основну успішну збірку на непідтверджену базу.
3. **Підготувати board port WR1200JS.** Є початкові board files, DTS, kernel config і layout в `overlay/padavan-4.4`; звірити їх з образом, Ethernet/switch, MAC/калібруванням Wi-Fi, USB та GPIO/LED до цільової збірки.
4. **Зібрати контрольний образ 4.4.198 для WR1200JS.** Спершу досягти відтворюваного CI-білду. Перевірити тип і розмір образу, не прошиваючи його на роутер до завершення аудиту сумісності та плану відновлення.
5. **Перенести конфіг по групах.** Для кожного активного параметра визначити відповідний символ/пакет у 4.4-базі. Зафіксувати статус: перенесено, замінено, відсутнє або потребує адаптації. Зберегти стан вебінтерфейсу й користувацькі налаштування, наскільки дозволяє нова база.
7. **Перевірити на реальному WR1200JS.** Після окремого підтвердження готовності образу перевірити завантаження, LAN/WAN, Wi-Fi 2.4/5 ГГц, USB, сервіси, збереження налаштувань, швидкість і відновлення. CI-збірка сама по собі не доводить працездатність на пристрої.

## Критерії завершення

- Збірка використовує точно визначений Linux 4.4.198 commit і toolchain.
- Є окрема підтримка WR1200JS у цільовій базі; конфігурація плати та формат образу перевірені.
- Для кожної активної функції початкового конфіга є перевірений результат сумісності; жодна не зникає мовчки.
- Усі доступні перевірки збірки проходять, а робота на роутері підтверджена окремо.
- Кожен етап і обмеження описані в цій нотатці та звіті користувачу.

## Журнал виконання

- [x] Початковий аудит локальної гілки й конфігурації.
- [x] Перевірка, що кандидатна база орієнтована на Linux 4.4.198/MT7621.
- [x] Перевірка наявності плати WR1200JS у кандидатному переліку: профіль знайдено в іншому 4.4 fork.
- [x] Зіставити дані плати WR1200JS і DTS/розмітку флеш-пам'яті/радіодрайвери кандидата 4.4.
- [x] Зафіксувати SHA кандидата; закріплення його у конфігурації збірки ще попереду.
- [x] Знайти upstream toolchain release для 4.4; його цілісність і відтворюваність ще треба закріпити.
- [x] Додати ізольований ручний build path для контрольної бази 4.4.198; CI запуск ще очікує.
- [x] Знайти окремий fork з профілем WR1200JS, MT7603E/MT7612E та toolchain.
- [x] Додати початковий WR1200JS board/DTS/layout overlay і ізольований ручний workflow.
- [ ] Довести board port WR1200JS, flash layout, image hooks і Wi-Fi calibration path збіркою та аналізом образу.
- [ ] Перенести конфіг і потрібні функції партіями.
- [ ] Зібрати CI-образ і виконати апаратну перевірку.

## Прогрес порту WR1200JS на Linux 4.4.198

### Виконано в цьому кроці

- Підтверджено, що локальний репозиторій є build-wrapper, а не повним деревом Padavan: він містить `variables`, `configs.build/wr1200js.config`, pre/post-build hooks і overlay.
- Зіставлено профіль WR1200JS з device tree OpenWrt. Підтверджені factory EEPROM адреси: 2.4 GHz — `0x0000`, 5 GHz — `0x8000`; MAC для LAN — `0xe000`, WAN — `0xe006`; заводський розділ — `0x40000..0x4ffff`.
- Виявлено окремий Padavan 4.4 fork з повним вихідним профілем WR1200JS, що містить DTB і kernel config під Linux/mips 4.4.198.
- Локально створено попередній WR1200JS overlay на базі цього профілю. Він є заготовкою для збірки; його ще треба звірити з build hooks.
- Локальний ручний workflow `.github/workflows/build-padavan-4.4-wr1200js.yml` фіксує commit, додає board/DTS overlay і запускає цільову make. Він не виконувався в цьому локальному середовищі; успішність CI не підтверджена.

### Нові технічні висновки

| Параметр | Підтверджено для WR1200JS | Що має бути в Padavan 4.4 |
|---|---|---|
| Flash | 16 MiB; firmware `0x50000 + 0xF70000`; storage `0xFC0000 + 0x40000` у поточному Padavan профілі | окремий layout, не копія K2P (`0xF30000` firmware і storage з `0xF80000`)
| Wi-Fi NVMEM | EEPROM 2.4 GHz `0x0`, EEPROM 5 GHz `0x8000` | знайти vendor-driver mechanism для `RT_FIRST/SECOND_IF_RF_OFFSET` і перевірити точний 7603E+7612E combo
| MAC | LAN `0xe000`, WAN `0xe006` у factory | зіставити з Padavan MT7621 MAC source/board hooks
| USB | один фізичний USB 2.0 порт; Padavan board прапорець USB port swap=1; 4.4 K2P-USB має USB3 PHY=1 і swap=0 | налаштувати лише фізично присутні PHY/port, перевірити image scripts і runtime port
| GPIO/LED | OpenWrt DTS і Padavan board.h розрізняються за LED призначеннями | прийняти робочий Padavan board.h як базу, звірити реальну плату/схему до переносу LED mapping

## Виконана робота 2026-09-30

- Створено `overlay/padavan-4.4/trunk/configs/boards/WR1200JS` на базі WR1200JS профілю fork `vipshmily/padavan-4.4` commit `c25283e915a2a00a763774dd255b14aff997285e`.
- Kernel profile кандидата зберігає MT7603E + MT7612E та offsets 0x0/0x8000; workflow переносить USB/PHY опції з K2P-USB kernel profile у тимчасову копію WR1200JS kernel config, лишаючи radio та інші upstream board options незмінними. У kernel 4.4 чинний символ SPI flash driver — `CONFIG_MTD_M25P80=y`.
- Vendor/product identity лишено за upstream target WR1200JS: шаблон `VENDOR=Ralink`, `PRODUCT=MT7621`, `FIRMWARE_PRODUCT_ID=WR1200JS`. Workflow накладає лише GPIO доповнення board.h та WR partition config, зберігаючи upstream radio/kernel profile.
- DTS відокремлює WR1200JS від K2P layout та додає відомі розділи флеш-пам'яті. Upstream kernel Makefile формує DTB ім'я з CONFIG_RALINK_BUILTIN_DTB_NAME, тож окремий Makefile рядок не потрібен.
- Створено ручний workflow `.github/workflows/build-padavan-4.4-wr1200js.yml`: pinned source, upstream uClibc toolchain, WR DTS/layout, target/kernel config preparation, цільова збірка та артефакт.
- Workflow переносить значення активних CONFIG_FIRMWARE_* ключів, які є в target template, а відсутні додає до summary й unsupported-firmware-options.txt. З 67 активних ключів 33 імена є в template: 32 параметри переносяться, а board product ID лишається upstream WR1200JS. Ще 34 ключі потребують окремого порту; CAKE параметри не підхоплюються.
- Перший пакет опцій (USB/filesystems/HID/XFRM/QoS/IMQ/IFB/IPSet/NFSC та готові пакети) зберігається через це зіставлення. Kernel IFB/IPSet додаються окремо. IMQ 4.4 upstream backport тепер підготовлений як окремий patch, але має пройти застосування до vendor source та збірку.
- Джерело IMQ патчу зафіксовано: [imq/linuximq commit e140b0d](https://github.com/imq/linuximq/commit/e140b0db53e523a3af6af27e0655d23c5d4c0350), файл `kernel/v4.x/linux-4.4-imq.diff`. Він додає kernel IMQ і xt_IMQ; iptables userspace extension у Padavan fork ще треба перевірити.
- WR build workflow також перевірятиме kernel config, DTB signature, firmware image тип і ліміт розділу 0xF70000; CI ці перевірки ще не виконав.
- Додано checksum завантаженого toolchain як build evidence. Upstream GitHub release наразі не публікує digest, тож це фіксує отриманий файл, а не підтверджує його криптографічне походження.
- Локальна статична перевірка пройшла: три inline Python фрагменти компілюються, `git apply --stat` розпізнає IMQ patch, `git diff --check` не знайшов помилок whitespace. Лишилися лише попередження про LF/CRLF у раніше змінених файлах.
- Workflow та образ ще не запущені/зібрані. Жодних апаратних висновків не робимо.

### Наступні кроки

1. Після push змін запустити WR1200JS workflow; виправити конкретні помилки збірки до успішного image.
2. Приймати перший CI-образ лише якщо job підтвердить: commit `c25283e`, застосування IMQ patch, DTB `wr1200js`, MT7603E/MT7612E offsets, USB2 без XHCI, IMQ/IFB/IPSet, TRX та межу `0xF70000`.
3. Переносити активні пакети з `configs.build/wr1200js.config` групами: kernel/network+USB, VPN/security, DNS/proxy, інші сервіси. Для відсутніх функцій спочатку портити package/build hooks; на кожну — статус у матриці.
4. Лише після чистого image та плану recovery переходити до апаратної перевірки; окремо перевірити USB2, LAN/WAN, Wi-Fi калібрування та сервіси.

### Межі поточного підтвердження

Інтернет-джерела дають апаратні адреси, але збірка K2P або аналіз DTS не доводять, що WR1200JS image завантажиться. Перш ніж прошивати роутер, потрібна успішна збірка цільового образу, перевірка його заголовка/розміру/розмітки і план відновлення.
