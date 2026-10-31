# Linux 4.4.198 → 4.4.302: початковий аналіз WR1200JS

Статус: технічний висновок і план від 2026-10-24. Міграцію не розпочато;
поточну прошивку, конфігурацію та роутер не змінено. Це останній, умовний
етап проєкту: його розглядати лише після завершення Mi Mini, решти погодженої
роботи та збереження самодостатнього дерева джерел за
`PROJECT-DELIVERY-SCOPE.md`. Якщо перехід буде окремо погоджено, він
охоплюватиме всі роутери, які на той час додані до проєкту.
Наведені нижче конфігурація, команди збірки
та перевірки пристрою стосуються тільки WR1200JS; до початку міграції треба
додати окремий інвентар, адаптацію та приймання для кожної іншої плати.

## Висновок

4.4.302 — останній опублікований реліз гілки Linux 4.4 (2022-02-03), але
сама гілка більше не отримує звичайних LTS-оновлень. Архів і підпис:
<https://cdn.kernel.org/pub/linux/kernel/v4.x/>. Це оновлення вендорського
ядра Padavan, а не заміна каталогу чистим upstream-архівом.

Поточний CI бере pinned Padavan commit
`c25283e915a2a00a763774dd255b14aff997285e`, накладає локальні патчі та
overlay, готує kernel/board config і виконує
`make WR1200JS TOOLCHAIN=mipsel-linux-uclibc CONFIG_CCACHE=y`.
У наявному WR1200JS kernel config `CONFIG_RAETH=y`, `CONFIG_HW_NAT=y`,
`CONFIG_NET_DSA` вимкнено, `CONFIG_MT76X3_AP=m`, `CONFIG_MT76X2_AP=m`.
Тому активний шлях свічу — vendor RAETH/ESW; наявність upstream DSA
`mt7530.c` не доводить його використання цією платою.

## Ризики, які треба перевірити

1. **MT7603/MT76x2 Wi-Fi:** API мережевих пристроїв, PCI/DMA, skb та
   kernel headers, Kconfig/Makefile, `vermagic`, завантаження обох модулів,
   BSS і робота клієнтів. Не вважати успішний `make` доказом RF-стабільності.
2. **MT7530 через RAETH/ESW:** PHY, VLAN, bridge, WAN/LAN-порти та link
   transitions. DSA-реалізацію перевіряти лише якщо її буде свідомо обрано.
3. **HWNAT/netfilter:** skb, conntrack, hook ordering, взаємодія з VLAN,
   bridge, QoS/IMQ і Wi-Fi offload. Потрібні лічильники реальних offload
   потоків і порівняння CPU під контрольним трафіком.
4. **Патчі:** `overlay/padavan-4.4/patches/linux-4.4-imq.diff`,
   `wan-port-runtime.diff`, `zram-service.diff`, а також зміни Python-скриптів
   і скопійовані overlay-файли. Зсув контексту або вже внесене upstream
   виправлення потребують ручного рев'ю; автоматичний fuzz не є доказом.

Це класи ризику, не підтверджений список конкретних зламаних API.
Точні відмінності отримати з upstream diff `v4.4.198..v4.4.302`, потім
перевірити їх на нашому vendor tree та MIPS toolchain. Перевірка у цьому
документі не виконувалася.

## Послідовність у Git

1. Зберегти всі поточні modified/untracked файли, завершити передачу ролі,
   перевірити чистий `git status`. Не використовувати `reset --hard`, `clean`,
   force push, повторний клон спільного репозиторію чи автоматичний merge.
2. Створити окрему гілку `codex/kernel-4.4.302`. Взяти перевірений архів
   upstream 4.4.302 і зафіксувати SHA256/підпис; зберегти поточну vendor
   основу, DTS, partition layout та ефективні `.config` як контрольний базис.
3. Окремо відділити upstream stable delta від vendor змін до 4.4.198.
   Накладати stable зміни на копію vendor дерева групами: базове ядро,
   MT7621/PCI/DMA, RAETH/ESW, HWNAT/netfilter, Wi-Fi, решта модулів.
   Не замінювати цілий vendor kernel upstream-архівом.
4. Для кожного патча запускати `git apply --check` з правильним коренем і
   `-p`; конфлікти адаптувати вручну. Після застосування перевіряти diff,
   символи Kconfig та точні CI image gates. Зберегти логи першої помилки
   компіляції з файлом і рядком. Не вимикати глобально `-Werror`.
5. Спершу цільові збірки kernel/modules, потім повний WR1200JS CI image.
   Звірити `kernelrelease`, kernel/module `vermagic`, обидва Wi-Fi модулі,
   HWNAT, DTB, TRX ProductID/checksum і ліміт образу `0xF70000` байт.
6. Лише після окремого дозволу на прошивання і підготовки відновлення
   виконати контрольоване приймання на пристрої. CI/образ не є runtime.

PowerShell, після **завершення й збереження поточної роботи**:

```powershell
$repo = 'C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\router-guide-work'
Set-Location $repo
git status --short --branch
if (git status --porcelain) { throw 'Спершу зберегти всі поточні зміни.' }
git switch -c codex/kernel-4.4.302

$reference = Join-Path (Split-Path $repo) 'kernel-4.4.302-reference'
New-Item -ItemType Directory -Path $reference -ErrorAction Stop | Out-Null
$archive = Join-Path $reference 'linux-4.4.302.tar.xz'
Invoke-WebRequest 'https://cdn.kernel.org/pub/linux/kernel/v4.x/linux-4.4.302.tar.xz' -OutFile $archive
Get-FileHash $archive -Algorithm SHA256
tar -xf $archive -C $reference
```

Обчислений SHA256 слід порівняти з автентифікованим upstream значенням або
перевірити підпис; сама команда `Get-FileHash` не автентифікує джерело.
Перевірка одного патча на **майбутньому підготовленому кандидатному дереві**:

```powershell
$kernel = 'C:\path\to\staged-padavan-4.4\trunk\linux-4.4.x'
$patch = Join-Path $repo 'overlay\padavan-4.4\patches\linux-4.4-imq.diff'
git -C $kernel apply --check -p1 $patch
if ($LASTEXITCODE -ne 0) { throw 'IMQ потребує ручної адаптації.' }
```

Ця команда не застосовує патч. У фактичному CI IMQ має окремий vendor
fallback, який також треба перевірити. Збірка виконується в Linux/WSL або
CI з наявним MIPS cross-toolchain, а не звичайним Windows GCC:

```bash
cd /path/to/staged-padavan-4.4
make clean
make WR1200JS TOOLCHAIN=mipsel-linux-uclibc CONFIG_CCACHE=y
```

`make clean` запускати тільки в ізольованому кандидатному build tree. У
Windows PowerShell 5.1 синтаксис `make clean && make` не підтримується як у
Bash; у PowerShell перевіряти `$LASTEXITCODE` після кожної команди.

## Приймання на WR1200JS після погодженого прошивання

- До запису: backup конфігурації та потрібних flash-розділів, перевірена
  процедура відновлення, SHA256 образу, TRX ProductID/checksum/розмір.
- Після завантаження: `uname -a`, `lsmod`, `dmesg`, kernel panic/oops,
  watchdog/reboot, версії й `vermagic` модулів.
- WAN, усі LAN-порти, VLAN/IPTV, DHCP, IPv4/IPv6 та повторне встановлення
  лінка; контроль без втрати керування роутером.
- HWNAT: не лише наявність модуля або повідомлення в логах, а фактичні
  offload entries/counters під трафіком і порівняння CPU з базовим образом.
- 2,4/5 ГГц: асоціація, тривала передача, повторне підключення, сон
  клієнтів, guest/IoT BSS і журнали драйвера. Перевірити ефективне
  вимкнення 5-ГГц MU-MIMO/LDPC та 2,4-ГГц AMSDU/Greenfield.
- Збереження конфігурації та стан після контрольованого перезавантаження;
  rollback при помилці. IoT приймати окремо лише з готовим production backend.

Джерела: [офіційний архів 4.4.302](https://cdn.kernel.org/pub/linux/kernel/v4.x/),
[правила stable-патчів](https://www.kernel.org/doc/html/v4.13/process/stable-kernel-rules.html),
поточний `.github/workflows/build-padavan-4.4-wr1200js.yml` та
`trunk/configs/boards/WR1200JS/kernel-4.4.x.config` у pinned vendor source.
