# Хто зараз виконавець

Оновлено: 2026-10-17. Правила ролі — `docs/AGENT-HANDOFF-RULES-SOL-DEEPSEEK.md`, розділ 12.

## Поточний виконавець — Sol

- **Виконавець:** Sol (Codex), з 2026-10-17.
- **Підстава:** пряма вказівка користувача «Передай роль Солу» (2026-10-17).
- **DeepSeek:** перевіряльник; подальші зміни коду, коміти й push виконує Sol.
- Роль передано на HEAD `ed735f6` (== `origin/main` на момент передачі); стан
  робочої копії та активне завдання нижче мають пріоритет над історичними
  записами.
- Перевизначення WAN: реалізовано, перевірено компіляцією (збірка №311) і
  моделлю масок у CI; на пристрої не перевірено (`docs/WAN-RUNTIME-ABI.md`).
- Остання повністю перевірена збірка: CI №364 для `1eaa5a5`
  (`docs/evidence/WR1200JS-BUILD364.md`). Повні збірки №373–376 на комітах
  `c8d124a`/`263bdee`/`1605623`/`058f278` ще в процесі станом на передачу;
  їхній стан звіряти в GitHub Actions, а не вважати готовими.
- Поточний блок — незалежні одночасні WG/AWG профілі: транзакція, адреси,
  маршрути, DNS і service/rc-інтеграція вже в коді; не вистачає endpoint
  pinning у виклику, реального тунельного apply на пристрої та WebUI.
- Сторонній diff `tools/prepare-wifi-hwnat-mode.py` і line-ending-only
  `docs/evidence/WR1200JS-BUILD319-STRUCTURE.json` збережено без змін.

### Спільні локальні інструменти агентів

`tools/agent-nim/` містить потоковий фільтр GitHub Actions логів і manifest-
керований помічник вибраного коміту/звичайного push. Обидва агенти можуть
запускати фільтр та перевірки/preview. Помічник перед `--apply` звіряє виконавця
з цим документом: DeepSeek лишається перевіряльником і не публікує зміни, доки
роль явно не передано. Докладний запуск, формат маніфесту та межі безпеки описані
в `tools/agent-nim/README.md`.
## Актуальний стан передачі (має пріоритет над історією нижче)
### Передача DeepSeek → Sol — 2026-10-17

Користувач явно передав роль Sol. DeepSeek завершує лише запис цієї передачі та
його публікацію, далі працює як перевіряльник без конкурентних змін.
Робоча папка: C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\router-guide-work.
Гілка main; код/докази — `ed735f6` (== origin/main на момент передачі).

Що зроблено в цьому блоці (усі зміни вже в Git, service CI зелений):

- `tools/vpn-profiles/config-transaction.c/h` — lock → CAS сесії → apply →
  readback → повторна перевірка сесії; розбіжність відновлює попередній запис,
  і відкат теж мусить пройти читання.
- `runtime-state` — applied-config snapshot `snapshot-<id>` (0600, атомарний
  rename, відмова symlink) як джерело відкату.
- `endpoint-pin.c/h` — hostname → numeric endpoint (ін’єктований resolver); у
  жодному виклику поки не підключений, тому apply відмовляє hostname-endpoint.
- `addr-apply`, `route-apply`, `dns-apply`, `profile-apply` — адреси лише після
  перевірки protected prefixes; маршрути лише в таблиці `20000+id` з одним
  fwmark rule (без `from all`); DNS-файл атомарний 0600; apply зупиняється на
  першій помилці й звітує, які стадії встигли виконатися.
- `plan-report` — безсекретний `plan` з verdict
  ready/no-session/stale/needs-pinning/invalid.
- `service.sh` — `/usr/sbin/wr-vpn-profiles-service start|stop|status`, nvram
  `wrvpn_enabled` (comma ids), `wrvpn_protect`, opt-in `wrvpn_use_dns=1`
  (агрегація в `/etc/storage/dnsmasq/wrvpn.servers` + HUP dnsmasq).
- `profilectl`: create/list/export/observe/plan/apply/up/down.
- rc-інтеграція через `overlay/padavan-4.4/scripts/integrate-vpn-profiles.py`:
  start/stop у `services.c`, `load_user_config(..., "wrvpn.servers", NULL)` у
  `fill_dnsmasq_servers()` (`services_ex.c`); у build `263bdee` крок Apply
  пройшов.

Перевірено (докази, не припущення): service CI на `078a1e9`/`1605623`/`058f278`
зелений із PASS-рядками для транзакції, preview, адрес, маршрутів, DNS,
контролера apply і service-скрипта. Повний образ успішно збирався на `17fb761`,
`b6ed863`, `090cba6`; `263bdee` пройшов Apply-крок. Збірки №373–376 ще йдуть.

Безпека opt-in DNS перевірена читанням бази: `load_user_config()` у
`base-src/trunk/user/rc/common_ex.c:511` при відсутньому `wrvpn.servers` просто
нічого не читає (fopen → NULL), тож вимкнений режим не ламає генерацію серверів
dnsmasq.

Не перевірено: реальний тунель, маршрути, DNS і handshake на пристрої. Пристрій
з пісочниці недоступний (TCP 22 на 192.168.20.1 закритий). Нічого не прошито й
не перезавантажено.

Наступне для Sol:

1. Дочекатися зелених повних збірок №373–376, завантажити пакет, перевірити
   TRX/конфіг/інструкцію тими самими перевірками, що для 294–364, і записати
   `docs/evidence/WR1200JS-BUILDNNN.md`.
2. Підключити `endpoint-pin` до apply-контролера, щоб hostname-endpoint
   резолвився поза тунелем і фіксувався numeric.
3. Далі — WebUI/HTTP-керування профілями й приймання на пристрої лише з
   окремим дозволом користувача за `docs/VPN-PROFILES-ACCEPTANCE.md`.

Робочі сторонні зміни залишені: docs/evidence/WR1200JS-BUILD319-STRUCTURE.json
(лише line endings) і tools/prepare-wifi-hwnat-mode.py (лише CRLF); локальні
untracked fixtures і `__pycache__` зберегти, не додавати через `git add .`.
Оновлення/перезапуск роутера, зміни DNS-служб, чинного тунелю й ZeroTier у цій
передачі не авторизовані. Загальна мета порту 4.4.198 без CAKE залишається
активною.

### Передача Sol → DeepSeek — 2026-10-17

Користувач явно передав роль DeepSeek. Sol завершує лише запис цієї передачі
та його публікацію, далі працює як перевіряльник без конкурентних змін.
Робоча папка: C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\router-guide-work.
Гілка main; код/докази перед передачею — 6fa5796, опубліковано в origin/main.

Підтверджено: повна збірка №364 і service CI №141 успішні для 1eaa5a5.
TRX SHA256 перевірено локально; оригінальні MIPS/QEMU звіти збережені в
 docs/evidence/build364/; підсумок — docs/evidence/WR1200JS-BUILD364.md.
Native readback має окремі WG/AWG helpers у готовому образі. Host fixtures
перевіряють match/drift; MIPS gates — відсутній пристрій та відмови. Це не
доказ одночасних активних тунелів або приймання нової прошивки на роутері.

Наступне: поєднати runtime lock/session/index/owner з apply та readback;
реалізувати numeric endpoint resolution/pinning поза тунелем, незалежні
адреси/маршрути/DNS, rollback і controller/WebUI. config-apply.c/h та
config-plan.c/h поки не підключені до запуску. Зберігати чинний AWG до окремого
підтвердження нового WG. Повний аудит взаємодій служб з target BusyBox відкритий.

Робочі сторонні зміни залишені: docs/evidence/WR1200JS-BUILD319-STRUCTURE.json
і tools/prepare-wifi-hwnat-mode.py; локальні untracked fixtures зберегти.
Оновлення/перезапуск роутера, зміни DNS-служб і чинного тунелю в цій передачі
не авторизовані. Загальна мета порту 4.4.198 без CAKE залишається активною.


### Транзакція конфігурації — 2026-10-17

`tools/vpn-profiles/config-transaction.c/h` поєднує runtime-стан із транспортом:
бере операційний lock, звіряє сесію (id, протокол, ревізія, індекс, nonce) як
compare-and-swap, застосовує конфіг, читає ядро назад і повторно перевіряє, що
сесія все ще наша. Розбіжність читання відновлює попередній запис, і сам відкат
теж мусить пройти читання. `profilectl apply <id>` викликає це для наявної сесії;
адреси, маршрути, DNS і створення лінка лишаються контролеру.

Хостова перевірка `check-config-transaction.py` у службовому CI покриває:
зайнятий lock, відсутню сесію, застарілу сесію, відмову валідації без жодного
виклику транспорту, невідомий результат транспорту, успішне застосування з
незмінною сесією, розбіжність із успішним відкатом і невдалий відкат.
Не перевірено: реальне ядро й мережа, адреси/маршрути/DNS, приймання на пристрої.

### Перевірка артефакту №363 — 2026-10-17

CI №363 і служб №136 успішні. SHA256 завантаженого TRX перевірено локально;
інструкція відповідає моделі, номеру та коміту збірки. Оригінальні звіти й межі
доказів: docs/evidence/WR1200JS-BUILD363.md. MIPS manager fork/exec/store
та окремі WG/AWG control binaries підтверджені CI; старі позначки pending
нижче для цих перевірок історичні. Повний аудит взаємодій служб із BusyBox
та приймання на фізичному роутері залишаються відкритими. Наступний код:
protocol apply/readback, endpoint pinning, адреси/маршрути/DNS і rollback.


### Незалежні одночасні WG/AWG профілі — 2026-10-16

Користувач підтвердив перехід AWG → WG: створити новий профіль через чинний
канал керування, окремо перевірити доступ через WG, потім явно вимкнути й
видалити AWG. Вимога записана в PROJECT-DELIVERY-SCOPE.md. Поточні wg0/wg1
залишаються однопрофільними; новий менеджер ще не інтегрований.

Перший блок коду — tools/vpn-profiles/resources.h: стабільний глобальний ID,
позначення WG/AWG, окремі імена інтерфейсів, таблиці/мітки/пріоритети,
firewall/ipset і шляхи конфігурації/стану/lock. ID-простір не визначає кількість
одночасних тунелів, яку витримає роутер. Це кандидат ресурсів, а не їхнє
резервування; перед активацією потрібна перевірка зайнятості й власності.
Sanitizer fixture для всіх пар ID та міжтипових конфліктів пройшов у CI служб
№122 (`be522d9`, run 38949758058). Це модель, не підключені тунелі.
Наступний блок — tools/vpn-profiles/store.c: приватні незалежні записи,
версійований формат, compare-and-replace за ревізією, неблокуючий flock,
fsync/rename і окремий результат «записано, directory sync не підтверджено».
Видалений ID лишається tombstone без конфігурації й не перевикористовується,
щоб старий запит не зачепив новий тунель. Конфіг тут лише bounded data;
перевірка WG/AWG полів, runtime-власність, керування активними тунелями й
запис /etc/storage у флеш ще не інтегровані. File/sanitizer fixture пройшов
у CI служб №124 (`7182547`, run 38950704857): окремість записів, stale/lock,
write/fsync/rename failures, tombstone та небезпечні шляхи.

Додано кандидат validate-client.c: wrapper для реальних config.c/encoding.c
пакетів WG 1.0.20210914 та pinned AWG tools. Перевіряє quick Address/DNS/MTU,
ключі й native-поля; Endpoint перевіряється синтаксично й замінюється лише
всередині validator на numeric placeholder, щоб не виконувати DNS на імпорті.
Hooks/SaveConfig і ручні Table/FwMark відхиляються: ними має керувати менеджер,
а не сторонній конфіг. Вхід не виконується, секретні diagnostic lines не
виводяться. Native sanitizer CI №125 (`ef3bd02`, run 38951822000) з resolver
guard пройшов для обох pinned parsers. У сховище/образ helper поки не
підключений до образу.

Додано profilectl.c + validate-process.c: CLI create/list/export з’єднує
валідацію через фіксований executable з атомарним записом саме тих байтів,
що перевірялися. Список містить лише ID/label/revision; private export явний.
Validator має тайм-аут, очищене середовище й закриті сторонні FD; невідомий
exit status не приймається за валідний конфіг. CLI поки не має start/stop,
replace/delete чи перенесення legacy NVRAM, щоб до готовності ownership/lifecycle
не зачепити чинний тунель. Native integration fixture пройшов у CI служб
№127 (`e0dcd88`, run 38953022637): реальні pinned validators + store,
окремі AWG1/WG2, FD closure, invalid/unavailable/timeout і незмінність запису
AWG після невдалих WG actions. Це не доказ двох активних тунелів.
Додано пакет tools/vpn-profiles/Makefile + prepare-package.py. Він компілює
CLI та validators з уже вибраних WG/AWG sources, залежить від відповідних
userspace builds і встановлює /usr/sbin/wr-vpn-profile та validators у
/usr/libexec/wrvpn. Нових boot/network hooks немає. WIREGUARD selector
контролює пакет, AMNEZIAWG — додатковий validator.

verify-image.py перевіряє MIPS ELF і виконує упаковані validators під QEMU,
включно з 32-bit H ranges. У wrapper додано decimal bound до strtoul:
AWG tools не перевіряє ERANGE, тому host-64 parsing не доводить відмову
переповнення на MIPS-32. CI ще очікується. CLI input gate тестується без
створення сховища; повний fork/exec + store на target поки не перевірений.
Наступне: перевірити firmware/package CI, далі scoped lifecycle/маршрути/DNS,
HTTP/WebUI та QR; окремо зробити legacy migration без перезапуску чинного AWG.

### VPN profiles: MIPS packaging and read-only interface observation

Full build #358 (4075b79, run 38953992669) failed compiling validate-wg:
linux/wireguard.h was not in the toolchain headers. Added the pinned sources'
uapi/linux paths using the same include precedence as upstream WG/AWG Makefiles.
Native parser checks now use these paths too; target proof still awaits CI.

Added link-observation.c/h and profilectl observe ID: bounded RTM_GETLINK,
kernel sender/sequence checks, distinct absent/unknown results, interface flags.
JSON explicitly reports ownership unverified; an UP interface is not proof of
handshake or routing. Ownership predicate requires canonical name, kind, recorded
ifindex and session alias; lifecycle lock/private runtime record are still pending.
Legacy wg0/wg1 and the live AWG tunnel are untouched. Native sanitizer and MIPS
QEMU fixtures are wired into CI; not yet confirmed. The QEMU query uses the CI
host kernel and is not physical-router acceptance. Next: confirm CI, then private
runtime state and owned lifecycle before routes/DNS, WebUI and QR integration.

### VPN runtime session records — candidate

Service CI #130 (8a687e2, run 38956267461) passed the native observer,
read-only host netlink queries and pinned parser/manager fixtures. Full #359
(run 38956267665) was still running at this update; target proof is pending.

Added runtime-state.c/h: private dirfd-relative records, one nonblocking global
operation lock, 128-bit random session nonce, profile revision/protocol identity,
intent before create (index zero), then one-way acquisition of the observed index.
Updates/clear require the exact prior session; stale/corrupt/foreign file paths
are refused. Atomic rename publishes a whole 48-byte versioned record. This is
volatile /var/run recovery state, not flash persistence; after reboot it is lost.
The API does not create/remove links or inspect ownership by itself. Callers must
hold the operation lock across inventory and network actions, and clear records
only after confirmed link absence. External root actors remain outside this lock.
check-runtime.c covers lock contention, independent AWG/WG records, stale indices,
corrupt files, symlinks/hardlinks/modes and session-owner stability. CI pending.
Not packaged or invoked yet. Next: confirm this fixture, then connect owned
create/configure/stop with recovery and postchecks; routes/DNS and WebUI follow.

### VPN exclusive link action adapter — candidate

Service CI #131 (e3cb0a4, run 38956676783) passed private runtime session checks.
Full #359/#360 were still in progress at this update; no target result claimed.
Added link-actions.c/h: bounded RTM_NEWLINK with CREATE|EXCL and owner alias in
the same request as kind/name; RTM_DELLINK uses the recorded index only after
kind/name/index/session postcheck. Unknown inventory or foreign links are refused.
ACK loss is not treated as proof of failure: query after the action determines
whether the session-owned link exists or removal reached absence. Unknown state
requires keeping the intent/record for recovery. External root controllers can
still race index reuse; this adapter does not claim an atomic kernel ownership CAS.
check-actions.c checks wire requests and action/postcheck decisions using mock
transport; it does not create/delete host links. CI pending. Not packaged or
called yet; lifecycle must save intent, acquire index, configure, rollback/recover
and preserve records on uncertain cleanup before any CLI start/stop is exposed.
Full build header filters now name only packaged VPN headers; unshipped candidate
headers still run service CI. Add package/filter dependencies when wiring them in.

### VPN session/link lifecycle — candidate

Service CI #132 (6d549dd, run 38957031515) passed the action adapter fixture.
Full #359/#360/#361 were still running at this update; do not restart merely
because observation has not yet seen a terminal result.

Added link-lifecycle.c/h joining real private records with link actions under
an already-held operation lock. Acquire records intent before create, independently
checks session ownership, then records ifindex. Recovery handles a lost ACK or
crash before index publication only when nonce/name/kind match; a changed revision
or protocol is refused. Missing recorded links require explicit release, never
silent recreation. Release can recover an intent's owned index and clears its
record only after confirmed absence; unknown cleanup retains recovery identity.
check-lifecycle.c uses real runtime files and mock network callbacks to exercise
two profiles, stale/foreign refusal, lost ACK/index recovery and failed cleanup.
CI pending. No physical network changes. Not packaged/exposed by CLI yet.
This owns a bare interface only: no keys, addresses, routes, DNS, UP/handshake
or connectivity proof. Next: confirm CI, implement protocol configuration and
postcheck, then scoped policy/rollback and connect the complete controller/UI.

### VPN protocol configuration plan — candidate

Service CI #133 (5ee1b34, run 38957399991) passed integrated link lifecycle
with real private files and mock network operations. No two live VPNs are proven.
Added config-plan.c/h: calls the fixed native validation helper before producing
a private setconf payload, separates Address/DNS/MTU from native protocol fields,
and inserts this profile's allocated FwMark. The original Endpoint is preserved;
hostname endpoints are explicitly flagged for resolution and outside-tunnel
pinning before activation. No DNS, IPC, command execution, routes or DNS changes
are performed by this module. Plan contains secrets and must not be logged/served.
Failure leaves caller output unchanged. Native manager fixture now covers both
protocols, numeric IPv4/IPv6, hostname flags, quick-field separation, CRLF and
hook/mark/key rejection using the real pinned helpers. CI pending; not packaged.
Next: confirm CI, endpoint resolution/pinning and protocol apply/readback adapter,
then scoped address/route/DNS policy, rollback and the complete controller/WebUI.

### Shipped MIPS manager integration — pending

Service CI #134 (a3babdc, run 38957784076) passed config-plan with the real pinned
helpers. Full #360 also completed successfully (run 38956677012); its artifacts
have not been re-audited here. Build #359's downloaded MIPS evidence is recorded
in docs/evidence/VPN-PROFILES-BUILD359.md and adjacent original reports.

Added check-target-manager.py: copy exact shipped CLI/validators and image
libraries into a temporary PRoot, execute via static MIPS QEMU, then exercise
actual child exec/validation, private store writes, exact exports/list, invalid
input and missing-helper rejection with unchanged existing profile bytes. Only
synthetic keys/configs are used. Host /proc and /dev/null are the only explicit
binds; host storage and router are not touched. PRoot is test transport, not a
security isolation claim. Firmware workflow installs proot and preserves the
new vpn-manager-mips.json report. This target integration is pending CI and
must not be inferred from the earlier parser-only checks. No network lifecycle
or physical-router acceptance is claimed. Next: inspect this target result,
then continue protocol apply/readback plus independent endpoint/routing/DNS.

### Separate native WG/AWG control binaries — pending image proof

Confirmed in the pinned AWG source: src/uapi/linux/linux/wireguard.h defines
WG_GENL_NAME as amneziawg; src/ipc-linux.h uses that family for control requests.
The existing AWG romfs rule aliases /usr/bin/wg and /usr/sbin/wg to awg.
That legacy path therefore cannot select the standard WireGuard kernel family.
Added dedicated real binaries /usr/libexec/wrvpn/wg and /usr/libexec/wrvpn/awg
to the independent manager package, using the corresponding already-built pinned
source trees. Existing legacy aliases are retained for their existing callers.
The new controller must choose these fixed protocol-specific paths explicitly.

verify-image.py now checks both controls as MIPS ELF, distinct binary hashes,
family string markers and actual --version execution under image-library QEMU.
This proves packaging/execution only, not successful netlink configuration.
CI pending. The full target manager fork/exec check introduced in 527d6e7 also
remains pending in full build #362; do not infer its result from service CI.
Next: inspect these target gates, then protocol apply/readback plus endpoint
pinning and per-profile address/route/DNS transaction before exposing start.

### WireGuard / AmneziaWG: клієнтський QR та AWG-параметри — 2026-10-16

Повні #355/#356 скомпілювали образ і пройшли загальний BusyBox audit, але
зупинилися в новому export fixture: не було transport wrapper для цільового
`tee`. Аплет у BusyBox є. Додано wrapper та явну попередню перевірку потрібних
аплетів; виправлений target прогін у повному CI №357 успішний. Докази:
`docs/evidence/WG-SERVER-TARGET-BUSYBOX-BUILD357.md`. Посібник доповнено порядком
QR/.conf експорту й AWG server полями; генерація та перевірка посібника пройшли.

Коміти `32ef6aa`, `83bec0d`, `f7c3085` і `d690a6a` містять реалізацію VPN QR,
AWG параметрів і виправлення повторного використання спільних QR assets. Сторінка сервера
використовує спільний локальний UTF-8 QR-renderer замість старого `qrcode.min.js`.
QR і завантажуваний клієнтський `.conf` беруть один і той самий збережений експорт.
Після зміни форми, приховування QR, переходу зі сторінки, помилки або застарілої
відповіді QR/конфіг очищаються; приватний ключ не передається зовнішньому сервісу.

Для AmneziaWG додано серверні поля Jc/Jmin/Jmax/S1/S2/H1–H4, NVRAM defaults та
Apply-рестарт. Спільний builder додає ті самі задані параметри до серверного
`setconf`, створюваного клієнта та експортованого `.conf`/QR; для стандартного
WireGuard їх не додає. Перевіряються числові межі, парність Jmin/Jmax, обмеження
S1/S2 та унікальність H1–H4 до запуску сервера й експорту.

Локально пройшли: Node QR-потік exact-payload/очищення/помилки; підготовка та
перевірка серверної форми; shell fixture реальних `wgs.sh` функцій для AWG/WG,
експорту та відмови на некоректних значеннях; незалежне декодування трьох QR
матриць (WireGuard, AmneziaWG та UTF-8 конфіг). Це host-перевірки. Повна збірка
№352 зупинилася через дубльовану інсталяцію asset; повтор №353 виявив ту саму
умову на сусідньому Wi-Fi кроці. Обидва preparer-и тепер приймають лише точний
збіг asset, а path-фільтр виправлено. Повний CI №354 (`d690a6a`) успішний:
QR preparation, firmware compile, image structure verification та firmware
artifact upload пройшли. Артефакт: `WR1200JS_4.4.198.9-354_d690a6a8_TEST`.
Service checks №119 також успішні. Роутер не змінювався;
браузерна перевірка на пристрої, прошивання та runtime-приймання не виконувались.
QR містить приватний ключ клієнта — не публікувати й приховувати після імпорту.

Artifact #354 завантажено й незалежно хешовано; докази в
`docs/evidence/WR1200JS-BUILD354.md`. Наступне: перевірити новий target BusyBox
server/export gate у повному CI. Окреме фізичне приймання потребує погодженого
вікна тесту; build/host CI не є доказом runtime на роутері.

### WG/AWG setconf exit-status correctness — 2026-10-16

Audit found both inherited controllers tested output for word "error", masking
nonzero exits without that word; client reconnect returned success regardless.
Changed both to capture actual setconf exit status separately from local
assignment, cleanup temp config then branch on status. Reconnect propagates
that status. No claim that setconf success proves handshake or working routes.
Added extracted post-setconf fixture with mocked tool: zero/nonzero exit,
empty output, failure text without error word, benign text containing error,
and reconnect. Local Git host shell fixture PASS in ../wg-setconf-host-fixture;
Python syntax PASS. Added normal full CI step/trigger; target runtime pending.
BusyBox fix full38924582668 polled in_progress. Next verify target results,
then AWG server parameter-to-config/export coverage and lifecycle error paths.


### Handshake observation source UI and CI confirmation — 2026-10-16

Service CI38925181764 on3ec7bf6 SUCCESS: native worker/runtime and HTTP fixtures
passed with separate standard/AWG probes and observer propagation. This is host
CI, not target/device. UI now requires observer enum1/2, shows observation-tool
source separately from configured protocol; unknown/missing/string observer
returns unavailable. EN/UK/RU source label added with translation count guard.
Local Node UI checks PASS including both sources and invalid/missing observer;
translation AST/count check and Python syntax PASS. New full image pending;
BusyBox readlink fix run38924582668 last observed in_progress.
Next verify target restore result, finish AWG server params/export and remaining
VPN cleanup. Hardware, routes, browser and complete-port acceptance still open.


### Protocol-independent observed handshake sampling — 2026-10-16

Worker now probes fixed /usr/bin/wg-standard then /usr/bin/awg against the
observed interface, instead of the overwritten wg compatibility alias. Both
attempts share the existing process-group supervision/3-second deadline; HTTP
handlers still read cache only. Failed attempts preserve caller output; no shell
or configurable executable paths. Observation includes observer=1/2 (tool source,
not configured protocol, verified kernel type or route/connectivity acceptance).
Extended native fixture for primary refusal + alternate success, observer field,
existing malformed/failure/timeouts and HTTP propagation. Native compilation/
execution pending Linux CI (no local C compiler); diff review/check only here.
BusyBox fix full38924582668 last observed in_progress. Next verify CI, surface
observer/freshness appropriately and finish server AWG config/export coverage.


### WG/AWG WebUI and existing Apply integration — 2026-10-16

Added prepare-wg-protocol-web.py after WR pruning: per-role protocol select
(empty compatibility / wireguard / amneziawg), blank defaults and existing
EVM_RESTART_VPNCLI/VPNSVR registration. EN/UK/RU labels and guide explain
requested state and one profile per role; not simultaneous same-role tunnels.
Client AWG-only parameter panel hides for explicit WireGuard. Main type3 title
shows WireGuard / AmneziaWG rather than misleading AWG-only label.
Prepared-source/JS/Apply/defaults check PASS in ../wg-protocol-web-check;
generated guide/check PASS. Full image gate requires controls and linked HTTP
variable names plus separate tools. No browser/target/device acceptance yet.
Protocol-specific status/export and server AWG parameter coverage remain open;
next audit those and verify BusyBox readlink fix in full38924582668/dce43ae
(last observed in_progress). No live router configuration changes.


### Confirmed target BusyBox readlink -f incompatibility / fix — 2026-10-16

Full38922347945/0627db1 completed FAILURE. Synthetic trace confirms serial
hexdump succeeds, uniqueness scan fails at readlink -f with BusyBox usage
"readlink FILE". Pinned boards/busybox.config disables READLINK and FOLLOW;
DoH integrator enables READLINK alone. This explains host PASS vs target FAIL.
Added reviewed target BusyBox preparer enabling only CONFIG_READLINK and
CONFIG_FEATURE_READLINK_FOLLOW after package integration. Exact pinned config
preparation and Python syntax PASS; fixed target build NOT yet verified.
Target audit now requires both effective flags and executes readlink -f on a
synthetic symlink, checking canonical output. Full restore gate remains mandatory.
Next inspect fixed QEMU/restore results, then finish WG/AWG WebUI/Apply/status;
legacy private dependencies and full service audit remain open. No live actions.


### Per-role WG/AWG controller protocol selection — 2026-10-16

wgc/wgs read vpnc_wg_protocol / vpns_wg_protocol: explicit wireguard uses
wireguard+absolute /usr/bin/wg-standard, amneziawg uses amneziawg+/usr/bin/awg.
Empty keeps previous directory-based compatibility selection; invalid value
refused. No new defaults/UI selector installed yet, so old settings stay intact.
Host Bash extracted selector fixture PASS for client/server explicit WG/AWG,
empty/no-module and invalid values. Added repeatable Linux host-shell CI fixture
also checking empty/present module (pending CI). No target/device acceptance.
Still needed: WebUI/Apply registration, correct protocol-specific status/export,
server AWG parameter coverage and real route/handshake checks. No simultaneous
independent client tunnels claimed. Diagnostic38922347945 remains in_progress.


### Separate standard WireGuard tool preservation — 2026-10-16

Source audit: wireguard-tools installs /usr/bin/wg, AmneziaWG replaces it with
awg compatibility symlink; both wgc/wgs currently auto-select module based on
AmneziaWG directory presence. Independent selectable protocols not implemented.
Added WR preparer preserving standard upstream binary as /usr/bin/wg-standard,
without changing existing wg/awg aliases or live behavior. Exact pinned-source
preparation PASS in ../wg-tool-separation-check; Python syntax PASS. Full image
gate requires executable MIPS wg-standard plus awg and different binaries.
New build/gate pending. Next add per-role explicit protocol setting and select
correct tool/module (with validation, observed status, client/server config
coverage); no claim of independent/simultaneous tunnels. Shared settings and
server AWG-specific config omissions require further audit. Physical acceptance
still open. Diagnostic full38922347945 polled: still in_progress.


### Private legacy VPN kernel selectors excluded — 2026-10-16

WR board kernel template disables PPTP, PPPOL2TP, PPPOLAC, L2TP/L2TP_V3,
NF_CONNTRACK_PPTP, NF_NAT_PPTP and NETFILTER_XT_MATCH_L2TP. PPPOE remains y.
Full CI now refuses effective y/m on these selectors and requires PPPOE y/m.
No claim of size savings before built image; kernel compilation/new gate pending.
PPP/PPP_MPPE and shared crypto/GRE not removed without consumer audit (PPPoE
provider compatibility). XFRM remains pending consumer audit. No live changes.
Diagnostic38922347945 confirmed in_progress; target restore cause remains open.
Next inspect trace, remaining userspace/kernel consumers and WG/AWG selection.


### Repeatable prepared VPN regression gate — 2026-10-16

Added tools/check-wr-vpn-pruning.py after the WR preparer in full CI; checks
exact retained protocol choices, package/plugin selection, backend guard markers,
three translated labels and generated JS syntax. Executes actual generated
initial/Apply snippets against synthetic DOM fields for legacy/empty/supported
values. Local positive PASS on ../wr-wan-stale-type-check; negative reintroduced
PPTP option rejected (fixture restored). This does not execute C guards, entire
browser chains or physical tunnels. Full diagnostic38922347945 still in_progress
when polled; do not restart on observation timeout. Next target trace + residual
kernel/private dependency pruning + separate WG/AWG configuration audit.


### WAN stale legacy protocol explicit selection — 2026-10-16

Source preparer clears WAN selection for saved pptp/l2tp and refuses Apply
unless DHCP/static/PPPoE explicitly selected. Added EN/UK/RU explanatory label.
Saved NVRAM/credentials untouched. Exact-source preparation PASS in
../wr-wan-stale-type-check; Node executed actual generated initial/validation
snippets: legacy selection cleared, supported selection unchanged, unsupported
values refused; full inline JS syntax PASS with server tags substituted.
Not browser/full initial-chain acceptance. Diagnostic full38922347945 checked
live in firmware build; target USBIP failure trace still awaited. Next: target
trace, residual legacy/kernel dependency pruning and separate WG/AWG lifecycle.


### Explicit selection for stale saved VPN types — 2026-10-16

Prepared VPN client/server initial() clears selection when saved type !=3;
enabled validForm refuses empty/unsupported type, while existing disabled-form
return remains first. This prevents silently converting legacy settings to the
first retained option. EN/UK/RU help explains explicit selection and no automatic
conversion. No NVRAM migration performed. Exact-source preparer PASS at
../wr-vpn-stale-type-check; both generated page JavaScript syntax checks PASS
with ASP/template placeholders substituted (not browser behavior proof).
WAN stale-type UX, residual panels, private kernel dependencies and separate
WG/AWG support remain open. Diagnostic full38922347945 confirmed live in Build
WR1200JS firmware; no restart performed. Target failure reason still pending trace.


### Legacy VPN WebUI protocol selection pruning — 2026-10-16

WR source preparer видаляє лише options 0/1/2 у точних vpnc_type/vpns_type
selects та pptp/l2tp у wan_proto; unrelated numeric fields не змінені.
Index-based remove(2) для OpenVPN замінено value-based removal, щоб не
прибрати retained tunnel option після скорочення списку. Перевірено exact
pinned source + overlay pages у ../wr-vpn-ui-check: source preparation PASS,
VPN choice тільки3, PPPoE retained, removed options absent. Browser behavior,
stale saved-type UX, residual legacy panels, backend/kernel cleanup та окремі
WG/AWG режими ще відкриті. Production C compile не підтверджений цим fixture.
Full diagnostic run 38922347945/0627db1 перевірено: in_progress; не перезапускав.


### Legacy VPN start guards and CI trigger repair — 2026-10-16

WR pruning тепер відхиляє enabled VPN client/server type !=3 перед створенням
PPP options/запуском; disabled/AP checks лишаються першими без зайвих logs.
Server reapply legacy типів повертається без генерації PPP options. WAN
launch_wan_pppd відхиляє PPTP/L2TP без зміни NVRAM; PPPoE path збережено.
Це не automatic migration: старий PPTP/L2TP WAN потребує підтримуваного
uplink; конфіг/credentials не переписуються. Exact pinned source preparation
і Python syntax PASS у ../wr-vpn-backend-check; C compile/runtime ще очікують.
Знайдено missing full-build trigger для tools/usbip/check-restore.py:
c70567c запускав лише service CI 38922083803 (in_progress при перевірці).
Додано path у build-multiple-boards, щоб diagnostic target step дійсно виконався.
Наступне: emitted target trace, legacy UI/kernel/remaining L2TP call pruning,
окремі WG/AWG конфіги. Нічого на live router не змінено.


### Target BusyBox restore failure under investigation — 2026-10-16

Full 38918973322 на 9790865 FAILED at check-restore.py expected-success
assertion (line63), not a firmware compile error. Full 38908649608 also failed;
its exact cause not yet inspected. Newer 38921776592/de53d4e and
38921131364/8bb44ff were in_progress when checked. Native passing fixtures
are insufficient. Added bounded synthetic-only shell xtrace on the explicit
expected-success case to expose target stderr; no gate weakened or skipped.
Next: inspect emitted target trace, fix demonstrated incompatibility, then
continue legacy VPN backend/UI/kernel pruning. No physical runtime acceptance.


### Shadowsocks client/server configuration and guide — 2026-10-16

SSREDIR/SSLOCAL залишено y; додано окремий commented SSSERVER (сервер не
вмикався). Розширено інструкції прозорого клієнта, SOCKS5, upstream credentials,
відмінності server/client та незалежності WG/AWG. Окремий server chapter
генерується лише для enabled SSSERVER. Guide generation/check PASS у
../ss-client-guide-check. CI ROMFS gate перевіряє executable MIPS ss-local і
ss-redir при enabled shared package та відсутність ss-server при disabled
server selector. Новий image gate ще очікує збірку; live settings не змінено.
Попереднє незавершене VPN legacy/UI/kernel pruning та WG/AWG audit збережено
в наступному checkpoint, не вважати завершеним.


### Owner VPN scope replacement / first package pruning — 2026-10-16

Пряма вимога: прибрати PPTP, L2TP, EoIP, OpenVPN та лише їхні зайві
залежності; StrongSwan закоментований, розробку скасовано. WireGuard і
AmneziaWG лишити налаштовуваними; fallback лише AWG дозволений, якщо обидва
не підтримуються коректно. ZeroTier без змін. Scope document має пріоритет.
OpenVPN selector прибрано з requested config (merge відхиляє успадковані
optional defaults), EoIP commented. Додано WR-only source pruning poptop,
xl2tpd та PPP pptp/pppol2tp plugin build/install; PPP/PPPoE збережено.
Exact pinned-source preparation PASS у ../wr-vpn-pruning-check, Python syntax
PASS. CI gate вимагає excluded selectors та відсутні відповідні binaries/plugins.
Це ПЕРШИЙ крок, не завершене вилучення: rc/backend/WAN legacy guards,
WebUI choices, kernel/private dependencies, guide і final image ще відкриті.
XFRM тимчасово збережено до аудиту consumers. Існуючий WG type=3 перейменовано
на AWG при found_app_awg; це не доказ окремих configurable WG/AWG тунелів.
Наступний крок — runtime/backend + UI legacy exclusion і WG/AWG lifecycle audit.
На роутері жодних змін, credentials/storage не видаляти.


### USB/IP explicit restore opt-in WebUI — 2026-10-16

Service CI 38908279222 на 83b55f4 success. Додано usbip_restore у чинний
General Apply transaction (EVM_RESTART_SPOOLER/reconcile), окремий Yes/No
select з default-off NVRAM, EN/UK/RU поясненням requested-vs-observed стану,
можливого експорту при Apply/start та відсутності detach при вимкненні.
Збереження таблиці окреме і не запускає дій; тексти виправлено відповідно.
ROMFS verifier тепер вимагає restore select. Локальна Apply fixture PASS
(--workspace ../usbip-restore-web-optin-check); Python syntax/diff check PASS.
Початкова спроба fixture через Windows Temp отримала access denied;
повтор у дозволеному workspace успішний. Новий образ ще не підтверджений,
браузерна/target runtime перевірка opt-in і observed restore status відкриті.
Фізичних дій та зміни налаштувань чинного роутера не виконано.


### USB/IP restore fault coverage — 2026-10-16

Розширено спільну host/target-QEMU fixture: невдала bind-дія припиняє
відновлення без retry/rollback, заміна serial другого пристрою після першої
дії зупиняє batch з явно частковим результатом, mismatch product, oversized,
control/DEL та порожній serial відхиляються до першої дії. Зміни production
скриптів не потрібні; Python syntax PASS, виконання сценаріїв очікує CI.
На момент перевірки 38908111133 (full) та 38908110831 (service) на 1fb6fbf
in_progress. Цей набір перевіряє orchestration з mocked hardware/action,
не доводить роботу драйвера, lifecycle або фізичне приймання всього порту.


### USB/IP target BusyBox restore fixture — 2026-10-16

Service CI 38907533138 на b109c1a success; повна 38907533199 ще in_progress
на момент перевірки. Попередня повна 38906698637 на 7e4090c success.
Додано --target-root до check-restore.py та окремий крок у повній WR-збірці:
точна ROMFS BusyBox sh під QEMU, cat/readlink/hexdump з того самого binary,
PATH без host utility fallback. Host /bin/sh лише транспортує exec wrappers;
USB sysfs, daemon snapshot, export reader і bind залишаються mocks.
Перевіряються disabled/empty, відмова reader/daemon, batch preflight,
успішна dispatch та неоднозначний/відсутній serial. Python syntax PASS;
новий QEMU-крок ще не виконано. Це не фізична перевірка USB/IP чи всієї
служби; opt-in UI/HTTP, restore status і решта BusyBox-аудиту відкриті.


### USB/IP guarded restore controller — 2026-10-16

Service CI 38907060095 на 9580d8f success. Додано restore.sh під чинний
lifecycle-lock: enable+restore прапорці, owned daemon, capture усього helper
stdout/exit до дій, preflight усіх правил, повторна звірка до кожного bind.
Скан до 256 USB-вузлів відхиляє duplicate VID/PID/serial та недоступний
serial у потенційно однакового пристрою. Чинні mount/swap/NIC/modem guards
залишаються. Bind повторно звіряє exact identity після дії; hotplug може
дати partial/unconfirmed, сліпий rollback не виконується.
Default usbip_restore=0; start/restart/reconcile викликають restore лише при
явному прапорці. WebUI цього прапорця ще не має; runtime не вмикався.
Mock-fixture disabled/empty/reader fail/daemon/batch guard/duplicates додано
в CI; Python syntax PASS, виконання native/target ще очікується.
Наступне — результати CI, явний opt-in UI/HTTP і статус restore, потім
QEMU service-chain/physical приймання. Не оголошувати persistence готовим.

### USB/IP validated restore reader — 2026-10-16

Service CI 38906698630 на 7e4090c success. Додано target export-table --list:
read-only helper читає приватний storage через чинний codec/store, перевіряє
всю таблицю до виводу. Відсутній файл -> empty/0; corrupt/symlink/permissions
-> 2 без правил. stdout приватний (serial), не для публічних журналів.
Компіляцію/ROMFS helper підключено в package Makefile та image ELF gate.
Native sanitizer fixture actual helper перевіряє empty/valid/corrupt/symlink;
виконання нового CI ще очікується. Helper не здійснює bind/restore сам.
Наступне — service restore під чинним lock: capture всього списку з перевіркою
exit status до дій, uniqueness/current identity + preflight перед кожним bind;
окремий default-off дозвіл і UI, потім boot/hotplug приймання.

### USB/IP settings ROMFS gate — 2026-10-16

Додано verify-settings-image.py до повної збірки за USBIP=y: exact inline JS,
UI controls, linked route/EJ/storage/lock/version/save-only markers, усі 16
EN/UK/RU ключів і SHA256 сторінки/httpd/dict. JSON usbip-settings-image,
runtime_verified=false, restore не реалізовано. Синтетична позитивна й
негативна fixture (відсутній linked handler) пройшли; це не реальний образ.
Наступне — CI/пакет інкременту й фактичний report, потім restore з identity
і preflight під чинним lock. Попередні bc7a1a0/Bash-helper builds ще виконуються.

### USB/IP selection settings WebUI — 2026-10-16

Додано settings-view.js / prepare-settings-view.py: read/load таблиці,
додавання свіжого observed пристрою з serial, remove, окремий ack/save,
відмова duplicate bus/identity, збереження чернетки, single request і unknown
після невизначеної відповіді без автоматичного retry. DOM text-only; serial
не показується відкритим текстом. EN/UK/RU help прямо каже save-only,
restore ще не ввімкнено, flash commit окремий через stock storage control.
Node fixture PASS; synthetic prepare/dict fixture PASS, не браузер.
Підключено до build; target compilation/ROMFS/реальний HTTP ще очікуються.
Наступне — результати CI, image gate для settings UI/HTTP, тоді restore.

### Target BusyBox audit first result — 2026-10-16

38845996781 success на 5d04e61. Оригінальний report збережено:
TARGET-BUSYBOX-5D04E61.json — 55 sh scripts, 150 applets, syntax/hexdump/flock
PASS, command builtin відсутній, command -v серед цих scripts не лишилося.
Два Lua та detect.sh були поза scan. Pinned detect.sh має /bin/bash і rc
WAN/firewall виклики. Додано точний prepare-mwan-shell.py: sh + POSIX
арифметика, без зміни routing-команд; локальна трансформація PASS. Новий
target gate перевірить цей script і arithmetic probe. CI ще очікується.
USB/IP UI лишається наступним незавершеним кодовим блоком; audit findings
мають пріоритет при виявленні збоїв. Повний аудит BusyBox не завершено.

### Перший target BusyBox gate — 2026-10-16

HTTP USB/IP settings CI 38845781900 success на 34d0999. Додано
check-target-busybox.py у повну збірку після встановлення QEMU: exact ROMFS
BusyBox/config SHA256, --list, type builtin, синтаксис усіх виявлених sh/ash
скриптів (без виконання lifecycle), hexdump точні argv/bytes і flock FD /
contention через QEMU з бібліотеками образу. Інші інтерпретатори й command -v
із відсутнім builtin фіксуються для подальшого розбору. JSON-артефакт
target-busybox-audit; whole_service_audit_complete=false, runtime_verified=false.
Python syntax PASS; реальне виконання нового gate ще очікується в CI.
Наступне — розібрати report/відмови, потім динамічні service-chain fixtures
і незавершені USB/IP UI/restore. Глобальний аудит BusyBox не оголошувати виконаним.

### USB/IP authenticated settings HTTP — 2026-10-16

Service CI 38845392936 на bba2f77 успішний. Завершено попередній WIP:
http-settings.inc / prepare-export-settings.py підключають safe-session POST,
чинний CSRF+ack, body <=32768 з перевіркою percent/NUL, bounded table_hex,
повний decode/валідацію та settings_save під lifecycle-lock. EJ reader теж
вимагає safe-session. Відповідь saved/synchronized окремо від applied=false
і flash_committed=false. Не виконує bind/restore або flash save.
Headers/route/EJ підключено в build workflow, додано push.paths для нового
production коду. Native fixture використовує фактичний handler і file store:
auth/token/ack/body/table/save-only/private readback; Python generation і
syntax локально PASS, native C sanitizer/target build ще очікуються.
Наступне — CI та ROMFS endpoint checks, потім EN/UK/RU UI й restore.

### Обов'язковий аудит цільового BusyBox — 2026-10-16

Користувач вимагає перевірити всі служби й усі пов'язані скрипти/процеси/
lifecycle-ланцюжки з цільовим BusyBox. Повний контракт внесено в
PROJECT-DELIVERY-SCOPE.md, Mandatory target BusyBox compatibility audit.
Потрібні exact binary/config/build evidence, command providers/options,
shell/process/locks/timeouts, boot/Apply/firewall/DNS/VPN/storage recovery,
цільові fixtures/emulation та окреме фізичне приймання. Host PASS недостатній.
Це відкритий обов'язковий пункт; весь аудит ще не виконано.

Незавершений поточний код: tools/usbip/http-settings.inc та
prepare-export-settings.py і зміни двох build workflow у робочій копії.
Це наш WIP захищеного settings endpoint; ще не перевірений/не закомічений.
Не плутати з готовим пакетом №322. Продовжити native endpoint fixtures,
інтеграцію й target compilation, потім UI/restore. Сторонні diff не чіпати.

### USB/IP settings lifecycle lock — 2026-10-16

Service CI 38845247667 на 46e9b4d успішний. export-settings.h підключає
file-store до фактичного /var/run/wr-usbip.lock (nonblocking, private,
no-follow), storage /etc/storage/usbip. Розрізняє READY/EMPTY/BUSY/UNKNOWN;
невдале/зайняте читання не змінює out, EMPTY дає нульову таблицю. Writer
валідує до lock/створення каталогу; flash commit не викликається. Помилку
перевірки прав каталогу більше не можна сплутати з ENOENT.
Native fixture спільного lock/default-empty/symlink додано в sanitizer CI;
новий результат очікується. Це API ще не встановлено/не викликається з HTTP.
Наступне — автентифікований settings POST/EJ з bounded таблицею й UI.

### USB/IP private file store — 2026-10-16

Service CI 38845108113 на 8b3dadf успішний. Додано export-store.h —
file I/O шар із контрактом caller-held wr-usbip.lock, приватний directory,
O_NOFOLLOW/exclusive temp, повна валідація до запису, renameat, окремий
SAVED/REFUSED/UNCONFIRMED для sync після rename. Reader обмежений, не приймає
symlink/hardlink/неприватні файли; invalid decode не змінює попередній out.
Не викликає MTD/storage-save. Ще не встановлений і не з'єднаний з HTTP/boot.
Native sanitizer fixture: roundtrip, invalid-table preservation, symlink і
directory permissions; додано до CI, результат очікується. Наступне — CI,
підключення під фактичний lifecycle lock і автентифікований writer/UI.

### USB/IP private export format — 2026-10-16

Service CI 38844980761 попереднього валідатора успішний. Додано
export-codec.h: версія wr-usbip-exports-v1, рівно 16 слотів, bounded текст,
disabled-слот канонічний; decode перевіряє всю таблицю до копіювання в out.
Missing/truncated/extra/NUL/невірна версія/некоректні правила відхиляються;
при відмові попередній out не змінюється. Native fixture доповнено roundtrip,
обрізанням/версією/малим буфером/максимальним serial; CI ще очікується.
Це codec, не файловий writer: ще не підключено до storage/restore/UI.
Наступне — перевірити CI, атомарний файл під lifecycle-lock без flash commit.

### USB/IP export rules validator — 2026-10-16

Додано export-rules.h: bounded валідація до 16 правил (enabled, bus,
VID/PID, точний serial_hex). Активне правило без serial/із control-byte,
неканонічним hex/незавершеним рядком відхиляється; дублікати портів та
однакових VID/PID/serial на різних портах відхиляються. Disabled-рядки не
блокують вимкнення. Це лише валідатор, ще не підключений до NVRAM/restore/UI.
Native fixture додано до sanitizer CI; результат очікується. CI 38844859606
попереднього exact serial argv/HTTP guard успішний. Наступне — виконання
нової fixture, потім validated settings writer і restore із повторною звіркою.

### USB/IP serial transport evidence — 2026-10-16

Service CI 38844755717 успішний на ea91264 (hexdump reader). Додатково
посилено fixtures: mock-controller записує реально отриманий argv[5],
батьківський C-тест порівнює exact serial; HTTP-тест відхиляє odd/nonhex/
oversize serial до запуску job. Це усуває слабкість попереднього тесту,
який перевіряв завершення job, але не доставлене значення. Новий CI ще
очікується. Повні target збірки попередніх інкрементів виконуються.

### USB/IP target utility correction — 2026-10-16

CI 38844642580 на 37b0738 успішний. Проте source-аудит цільового BusyBox
показав CONFIG_OD вимкнено; без DESKTOP od не має -A/-t/-N. Замінено serial
reader на вже ввімкнений CONFIG_HEXDUMP=y: hexdump -v -n 258 -e для точних
байтів. У ROMFS-gate додано built CONFIG_HEXDUMP і applet link. Попередні
згадки od нижче — історичні. Новий native/target CI ще потрібний; це приклад,
чому host shell PASS не підтверджує shell/appлeти роутера.

### USB/IP serial через WebUI/worker — 2026-10-16

action-view передає observed serial_hex у POST; HTTP і worker перевіряють
lowercase hex/парність/ліміт 512 символів, body <=1024. Worker передає
непорожнє значення окремим argv у controller, без shell. Порожнє/відсутнє
значення зберігає попередню ручну дію; це не дозвіл майбутнього auto-restore.
CSRF/safe-session/ack і lifecycle locks збережені. Node fixture PASS з
перевіркою POST serial. C HTTP/worker fixtures оновлено; CI очікується.
Попередній action guard: service CI 38844475639 success на dc22cf9.
Наступне — перевірити новий CI/цільовий od і повторну ідентичність до
ввімкнення persistence. На роутері bind/unbind не виконувались.

### USB/IP action serial guard — 2026-10-16

wr-usbip bind/unbind отримали необов'язковий п'ятий аргумент serial_hex:
точна звірка до й після дії під чинним lifecycle-lock, bounded od до 258
байтів; missing/oversize/control/invalid token відхиляються. При відсутньому
od дія з serial відхиляється. Старий ручний контракт із чотирма аргументами
збережено. Web worker/UI ще передають старий контракт; persistence не ввімкнено.
Shell syntax PASS; mock-fixture доповнено valid/mismatch/missing/oversize та
заміною serial після bind (unconfirmed без сліпого rollback). Виконання CI
нового mock ще очікується. На пристрої дії не виконувалися.
CI 38844317388 попереднього inventory-кроку успішний; повна збірка
38844317454 ще виконується. Наступне — C/action CI, потім HTTP worker/UI
передавання observed serial і перевірка підтримки od у цільовому образі.

### USB/IP serial observation — 2026-10-16

inventory.inc доповнено bounded serial_hex: до 256 байтів номера, hex JSON,
порожнє значення при відсутньому/завеликому/керувальних байтах або помилці.
Це приватний точний номер у кодуванні, не хеш/анонімізація. Не публікувати
відповідь endpoint. Читання — спостереження, не доказ унікальності чи дозвіл
автоекспорту; device-action та persistence ще не використовують поле.
C-fixture доповнено synthetic serial/oversize/missing; виконання чекає CI.
Наступне — перевірити C/target image, додати звірку до action-контракту під
чинним lock і перевірку неоднозначних однакових пристроїв до persistence.

### Наступний блок USB/IP — 2026-10-16

№322 збережено як тестовий пакет. Для наступного незавершеного USB/IP
збереження експорту перевірено inventory.inc і device-action.sh: лише
busid/VID/PID, без сталої ідентичності після hotplug/reboot. Спершу додати
bounded identity observation/відмову unknown під чинним lifecycle-lock,
потім writer/restore/UI. План і межі дописано до USBIP-HADZHIOGLU.md.
Коротка read-only SSH-перевірка 192.168.20.1:22 завершилася тайм-аутом;
команди на пристрої не виконались, висновку про збій роутера немає.

### Готовий тестовий пакет №322 — 2026-10-16

38842496655 успішний на 4b74897. Завантажено ../build322-final; образ
6/6 структурних перевірок, профіль побайтово збігається, інструкція PASS.
WAN ROMFS — 26/26; оригінальний JSON збережено. Локальний ZIP із трьох файлів
створено й CRC перевірено. Деталі/хеші docs/evidence/WR1200JS-BUILD322.md.
Містить нові WAN/ZeroTier зміни та інструкцію. Наступний блок — фізичне
приймання за окремим погодженням прошивання; код решти погодженого обсягу
залишається в роботі. На пристрої ці зміни ще не перевірені.

### Збирач для фізичного приймання — 2026-10-16

Наявний collect-wr1200js-readiness.sh доповнено запитаним WAN/VLAN/STB і
GET-only switch 67 для WR1200JS, zerotier_enable/PID та метаданими кешу без
identity/membership/token. Старий образ може не підтримувати GET: це unknown.
Git Bash -n пройшов (у пісочниці signal pipe error 5, повтор поза нею success).
На пристрої не запускався. Повний stdout містить адреси/логи — лишати приватним.

### Інструкція нового статусу ZeroTier — 2026-10-16

Генератор посібника доповнено поясненням «Оновлено»/stale/unknown,
відмінністю кешу від справжнього VPN-доступу, ручним/30-секундним оновленням,
очищенням після помилки й лімітом 4096 байтів. Перевірка згенерованих MD/TXT
локально PASS. У 38842196567 інтеграція Apply WR1200JS board port пройшла,
тепер Build WR1200JS firmware in_progress. Сам образ ще не підтверджено.

### Пакет №319 — 2026-10-16

38841465981 успішний на adca670. Пакет завантажено, склад/SHA256/профіль/
версію інструкції перевірено; локальний structural verifier — 6/6.
Оригінальний результат і деталі: docs/evidence/WR1200JS-BUILD319.md.
Це підтверджує повну компіляцію оновлення тексту ZeroTier, але передує
9a7d16d та новому WAN-панелю. Повний 38842196567 на d421350 виконується
(перевірено Install build dependencies); 38841663562 теж компілює прошивку.
Наступне — зняти пакет/ROMFS-звіт останнього інкременту після завершення.

### Виправлення тригера повної збірки — 2026-10-16

Запуск 38841964174 на cde23db виявився lifecycle CI (success), а не повною
збіркою: tools/wan-port/** був відсутній у push.paths build-multiple-boards.yml.
Попереднє формулювання «повний запуск 38841964174» нижче — помилкове.
Додано tools/wan-port/** та tools/check-zerotier-state.py до повного тригера.
Наступне — звірити новий запуск саме Build selected router firmware з цією
правкою, його target compilation та ROMFS/пакет. №317 лишається останнім
завантаженим доказом WAN UI без нового effective-name панеля.

### Пакет №317 — 2026-10-16

Повна збірка 38840756322 і CI 38840755902 успішні на fb54199. Пакет №317
завантажено: склад/хеші/профіль/ідентичність версії інструкції перевірені.
Оригінальний WAN ROMFS-звіт збережено: 15/15, runtime_verified=false.
Деталі docs/evidence/WR1200JS-BUILD317.md. Це доказ інтерфейсу вибору й
компіляції виправленого контролю кабелю, але не нового cde23db-панеля чи
наступних ZeroTier-змін. Наступне: повний запуск 38841964174 на cde23db.

### Фактичний WAN-порт у вебці — 2026-10-16

prepare-web.py додає read-only EJ wr_wan_effective_port: для WR1200JS читає
GET 67 через наявний httpd mtk_esw_ioctl, повертає тільки 0..4 або -1.
Сторінка показує фактичний WAN/LAN, невідомий стан та пояснення розбіжності
зі збереженим вибором EN/UK/RU. Немає SET, CLI або автоматичного повторного
застосування. Дані — знімок на завантаження сторінки, після Apply оновити її.
Node-модель перевірила unknown/original/matched/mismatched; інтеграція на
pinned-копії пройшла. C-компіляція, ROMFS і фізичний тест ще очікуються.

### Перевірка C-hook ZeroTier — 2026-10-16

Подальша правка: кеш відкривається open(O_RDONLY|O_NONBLOCK|O_NOFOLLOW),
тип/час перевіряються fstat до fdopen/читання. Некоректний файл відхиляється
без блокуючого fopen; дескриптор закривається й на відмові. У C-фікстуру
додано перевірку прапорців відкриття та нерегулярного типу. Локальна JS-
перевірка пройшла; нова C-компіляція/повний образ ще очікуються.

У запуску 38841465981 на adca670 крок «Check ZeroTier status semantics before
compilation» завершився success. Це виконує tools/check-zerotier-state.py
--cc gcc: Node mock і компіляція/виконання згенерованого C-hook з окремим
JSON-парсером. Підтверджено escaping, fresh/stale/future/missing/disabled
і ліміт 4096 байтів. Повна збірка в цьому запуску ще виконується;
попередній 38840756322 також виконує Build WR1200JS firmware. Не перезапускали.
Це не фізичне приймання; наступне — кінцевий статус/ROMFS/пакет цих запусків.

### Доказ пакета №315 — 2026-10-16

38840408246 успішний на 78efe0d. Пакет завантажено, SHA256/склад перевірено;
профіль побайтово збігається, інструкція відтворюється з effective config
з точністю до LF/CRLF. ZeroTier ROMFS-звіт: усі 7 перевірок успішні,
runtime_verified=false. Деталі docs/evidence/WR1200JS-BUILD315.md.
Це проміжна збірка: новіші виправлення WAN/ZeroTier до неї не входять.
Наступне — звірити повний запуск 38841044821 на bdf1d5d і його пакет.

### Дозвіл щодо ZeroTier — 2026-10-16

Дороблено оновлення тексту статусу ZeroTier: раніше AJAX міняв лише позначку
та вік, а текст вузла/мережі залишався початковим. JSON тепер містить до 4096
символів із того самого відкритого кеш-файлу, з JSON-екрануванням. WebUI
вставляє через text(), після помилки/невідомого стану очищає попередній текст.
Node mock-перевірка пройшла; у повній CI додано компіляцію саме згенерованого
C-hook із mock-файлами та незалежним JSON-парсером. Її результат ще очікується.
На живому пристрої не виконувалося; CLI в HTTP не запускається.

Після зняття заборони виправлено семантику статусу: свіжий кеш позначається
«Оновлено», а не «Працює»; він не доводить роботу демона або з'єднання.
JSON перевіряє діапазон стану/цілий вік і узгодженість fresh <=60/stale >60.
Майбутній mtime, некоректний час або не звичайний файл дають unavailable.
check-zerotier-state.py виконує JS із транспортними mock: коректні/некоректні
відповіді, помилка, прихована вкладка, один активний запит; локально PASS.
Перевірку підключено до повної збірки; компіляція нового C/ROMFS і runtime
ще не підтверджені. Змін на живому роутері не виконувалося.

Користувач прямо дозволив: «змінювати ZeroTier можна уже». Попередню
заборону від 2026-10-14 знято; згадки про замороження нижче — історичні.
Дороблення ZeroTier знову дозволено. Окреме погодження прошивання та
перезавантаження роутера, захист приватних конфігів/ключів і збереження
доступу залишаються чинними. Сам цей дозвіл не є доказом runtime-перевірки.

### Продовження Sol — 2026-10-16

Додано verify-web-image.py у повну збірку: перевіряє готову ROMFS-сторінку
WAN, унікальні непорожні EN/UK/RU-пояснення/підтвердження та безпечне
вставлення підтвердження в JS; звіт wan-web-image-checks.json містить SHA256
і runtime_verified=false. Фікстура та негативні контролі (відсутній маркер,
дублікат перекладу) локально пройшли. Node-перевірка також виконує Apply:
скасування/згода/незмінений порт/підтвердження повернення WAN.
CI 38840600386 успішний на 177d37a; повна збірка 38840600419 ще виконується.
Наступне — перевірити повний образ і звіт нового інкременту, зняти пакет.

Наступний інкремент: перевірка кабелю в rc і HTTP-індикатор WR1200JS тепер
запитують логічний WAN драйвера, а не запитаний LAN. Це усуває розбіжність
при відмові через VLAN: драйвер може повернути заводський порт. Старі моделі
збережено. Локальна інтеграція rc та Node-перевірка пройшли; нова компіляція
ще потрібна. Попередня повна збірка 38840408246 на 78efe0d виконується;
її не перезапускали. Фізичних змін не було.

Додано WebUI-інтеграцію WR1200JS: «Джерело WAN» видиме без IPTV,
WAN/LAN1–LAN4 доступні незалежно від STB, незбережений вибір зберігається
при зміні IPTV. Перед зміною — підтвердження втрати зв'язку/перенесення
кабелю, пояснення EN/UK/RU. Для інших моделей залишено стару поведінку.
Виправлено подію wan_src_phy: EVM_RESTART_SWITCH_VLAN замість FALSE,
щоб зміна самого поля запускала застосування. Підключено до повної збірки.
Локальна Node-перевірка на перетвореній pinned-сторінці пройшла; це модель
DOM, не браузер і не фізичний тест. Нові CI/ROMFS/пакет ще не підтверджені.
Наступне: перевірити повну збірку нового UI та фактичне застосування/відмову
при VLAN-конфлікті; пристрій і ZeroTier не змінювалися.

### Передача ролі Sol (2026-10-15)

Виконавцем знову стає Sol. Передаю стан роботи над перепризначенням WAN-порту.

Коміти в `main`: `88813f3` (ABI і план), `e4f2c47` (докази збірки №310),
`09b08f9` (runtime-перевизначення в драйвері), `b7e8fa1` (підключення `rc`),
`ba890e0` (команди `switch 66/67`), `9c0549a` (модель масок у CI), `3c9d6ee`
(доказ компіляції №311), `807668f` (розділ про заміну порту в посібнику).

Реалізовано й перевірено CI:

- `overlay/padavan-4.4/patches/wan-port-runtime.diff`: `WAN_PORT_X` став
  runtime-змінною з ініціалізацією із заводських макросів, додано команди 66/67,
  заводський роз'єм ізолюється (`get_isolated_port_x`), LAN-маски його не
  містять.
- `overlay/padavan-4.4/scripts/integrate-wan-port.py`: `rc` переносить роль WAN
  на сокет із `wan_src_phy` перед перебудовою моста, відмовляється займати
  роз'єм із правилом VLAN/IPTV, повертається на заводський при некоректному
  значенні; `switch 66/67` показують і змінюють фактичний порт.
- `tools/wan-port/verify-runtime-patch.py` і `verify-service-integration.py` —
  структурні перевірки з негативним контролем: на чистому дереві падають.
- `tools/wan-port/check-runtime-model.c` — `PASS` у CI: інваріанти ізоляції для
  штатного стану і чотирьох виборів.
- Повна збірка **№311** (run 38804963887, `09b08f9`) — success: драйвер
  компілюється під MIPS/uClibc.
- Посібник моделі: розділ «Заміна порту WAN» обов'язковий, перевірено прямий і
  зворотний випадок локально.

Не зроблено:

- Повний пакет збірки, що відповідає поточному `main`, не знято й не звірено.
  Збірки на `b7e8fa1` і `ba890e0` на момент передачі ще компілювались, `807668f`
  у черзі.
- Поле «Джерело WAN» на сторінці WAN показується лише в режимі STB/IPTV, тож
  сценарій «замінити пошкоджений роз'єм» поки не має очевидного входу в UI;
  підтвердження перед застосуванням і рядки EN/UK/RU теж не додані.
- Фізичного приймання не було: пристрій недосяжний із пісочниці, прошивання й
  перезавантаження не виконувались.

Межі чинні без змін: не прошивати й не перезавантажувати роутер та не чіпати
ZeroTier без окремого дозволу; не публікувати приватні логи, конфіги, ключі й
QR-коди; не чіпати сторонній CRLF-diff `tools/prepare-wifi-hwnat-mode.py`.
Мої робочі копії лежать поза Git у `C:\Users\ANDRZEJ\Documents\Codex\2026-09-29`:
`base-src`, `wanrc`, `wanpatch`, `wanpatch-check`, `wane2e`, `build310-evidence`.

### Історія прийняття ролі DeepSeek

Прийняв роль виконавця за прямою вказівкою користувача. Перед прийняттям
незалежно перевірив пакет збірки №310 на `5e3c62e`: TRX проходить структурний
верифікатор образу (6/6), `wr1200js.config` байт-у-байт збігається з
`configs.build/wr1200js.config`, інструкція проходить `check-router-guide.py`,
топологічний JSON збігається з sha256 `kernel-effective.config` тієї збірки, а
`eoip-image-checks.json` і `web-route-checks.json` побайтово ті самі, що в
№309. Деталі — `docs/evidence/WR1200JS-BUILD310.md`.

Закрито попередній «pending»: фікстури WAN-планувальника вперше виконалися в CI
на `c38ec51` (`PASS WAN external-port plan`, `PASS WAN VLAN plan`, ASan/UBSan).
Повної збірки на `c38ec51` поки немає. Два хеші заголовків драйвера зі звіту
топології лишаються непідтвердженими: самих заголовків немає ні в артефактах,
ні в робочій копії. Пристрій із пісочниці недосяжний (TCP 22 на `192.168.20.1`
закрито); прошивання й перезавантаження не виконувалися.

### Продовження Sol після прийняття ролі

WAN: додано кандидат перетворення VLAN-таблиці зі збереженням CPU/тегів,
правил IPTV інших портів і PVID; конфлікт зайнятого роз’єму не очищає
налаштувань. Окремо обчислюється фактичне LAN-членство й резервовані порти.
Новий CI-тест ще очікується. Планувальники не підключені до драйвера;
не показувати перепризначення як готову функцію. Наступний крок —
звірити топологічний JSON збірки №310 та проектувати runtime ABI/застосування.

WAN planner CI `38793467150` успішний. У фактичному kernel-effective.config
№309 WAN=0, LAN1..4=1..4; джерельний esw_common.h додатково задає топологію
CPU WAN=5 / LAN=6 через GE2_INTERNAL_GMAC_P5. Додано обчислення фактичних
макросів заголовків і JSON-звіт у повну збірку; перший запуск ще очікується.
Далі — прочитати цей звіт і реалізувати узгоджений runtime ABI драйвера,
маски/VLAN та перевірки конфліктів. Не підміняти це лише wan_src_phy.

Наступний кодовий блок після перевіреного EoIP №309: перепризначення WAN.
Звірено базову карту WR1200JS (WAN=0, LAN1..4=1..4) і різницю між
wan_src_phy та реальними switch/VLAN masks. Додано непідключений чистий
планувальник зовнішніх портів з ізоляцією старого WAN та CI-фікстуру;
виконання нового тесту очікується. Деталі й наступні залежності —
`docs/WAN-PORT-REASSIGNMENT.md`. Driver/RC/WebUI ще не реалізовано;
на фізичному роутері порти не змінювалися.

Поточна доказова точка: повна збірка №309 і CI успішні на `82bee9f`.
Пакет завантажено, конфіг/інструкцію/контрольні суми й ZIP перевірено;
ROMFS має 211 структурних EoIP-перевірок, усі 259 вебфайлів мають маршрути.
Див. `docs/evidence/WR1200JS-BUILD309.md` та два оригінальні JSON-звіти поруч.
Це вже пакет із редактором і preflight, на відміну від №294. Фізична
перевірка/збереження/reboot/віддалений EoIP і браузерний вигляд не підтверджені.
Далі — решта погодженого коду WR1200JS та підготовка приймання; не прошивати
роутер і не змінювати ZeroTier чи вимкнені DNS-служби без чинного дозволу.

CI редактора `38789306379` на `af41ec0` успішний. Додано повний структурний
EoIP ROMFS verifier і окремий JSON-артефакт; перевірка самого verifier на
синтетичному образі локально пройшла. Застосування verifier до нового образу
ще очікується. Візуальний перегляд локального file:// макета заблокований
політикою браузерного інструмента; перевірку браузера не зараховувати.

Останній інкремент: редактор EoIP зі зчитуванням NVRAM під operation-lock,
окремим підтвердженням Apply та незалежним вимкненням; словники EN/UK/RU.
Локальні Node-перевірки редактора й генерації сторінки пройшли; новий інкремент
ще потребує CI та цільової компіляції. Попередній HTTP writer перевірений
CI `38788594497` на `df9c8d8`. Далі перевірити актуальні CI/повну збірку,
підтвердити сторінку й маршрути у ROMFS, потім браузерний вигляд/поведінку.
Фізичний тест EoIP потребує сумісного віддаленого вузла та окремого дозволу.

Підтверджено й завантажено пакет №294 (`6f8e33e`), склад/ідентичність
інструкції/конфіг і SHA256 перевірені: `docs/evidence/WR1200JS-BUILD294.md`.
Він передує apply-table та HTTP-сторінці. Сторінка спостереження EN/UK/RU
і HTTP collector вже підключені в коді, але їхня повна компіляція ще очікувалася
на момент перевірки. Не плутати №294 з поточним HEAD. Наступний блок:
перевірка нової сторінки/збірки та автентифікований запис параметрів EoIP
зі спільною серіалізацією. Усі фізичні обмеження залишаються чинними.

Поточне продовження: `apply-table` / `stop-table`, структурований `status-json`,
повне блокування керованих операцій та shell policy перевірені CI до `2c1f7fb`
(`38784871587`, success). Інструкція EoIP розширена в генераторі. Додано кандидат
JS-відображення статусів з локально успішною Node-перевіркою; HTTP-джерело,
автентифікований запис NVRAM зі спільною серіалізацією та повна сторінка EN/UK/RU
ще не підключені. Не видавати цей кандидат за завершену WebUI. Повні збірки
потрібно звірити за GitHub; фізичні EoIP-тести не виконувалися.

Додано defaults восьми слотів, перевірку конфліктів таблиці та `boot-table`
у воркері. Підключено пакування `wr-eoip-boot` і умовні RC boot/stop hooks;
головний перемикач за замовчуванням 0. Нові hooks ще не підтверджені збіркою.
CI служб `38783437373` на `fd3b029` успішний, повна збірка `38783437472`
ще виконувалася під час перевірки. Далі перевірити збірку інтеграції, додати
серіалізацію Apply/таблиці, керування EN/UK/RU та інструкцію. Живий роутер
не змінювався. Старі записи нижче — контекст попередньої передачі.

- Код перед передачею: `cc140d3` (останні два коміти — лише документація: `d7aa09b`, `96f09aa`), гілка
  `main`; робоча копія `C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\router-guide-work`.
- Активний блок: EoIP. Читати `docs/EOIP-SERVICE.md` і `tools/eoip/`.
- **EoIP — реалізовано й перевірено CI:** валідація конфігурації, read-only netlink-запит,
  owned create/remove CLI, приватні runtime-записи, оркестрація lifecycle, configure-адаптер
  (`configure.h`), контролер (`controller.h`: мапінг слота на `wr-eoip<slot>` і alias
  `wr-eoip:<slot>:v1`, реальні ops з інжектованим транспортом), службовий вхід `worker.c`
  (start/stop/status; `ENABLED=0` зупиняє слот тим самим шляхом очищення).
- **Пакування підтверджено повною збіркою:** `integrate-eoip.py` збирає `/usr/bin/eoip-service`
  поряд із `eoip-ctl`; повна збірка 289 (`cc140d3`) завершилась УСПІШНО, тобто воркер компілюється
  під MIPS/uClibc. Попередня збірка 288 впала на `worker.o` (sysroot uClibc: `linux/if_tunnel.h`
  вимагає `IFNAMSIZ` і `struct iphdr`), виправлено в `cc140d3`.
- Успішні CI служб: 38772832369 (configure), 38775647354 (контролер), 38776214864 (фікстура воркера),
  38776427458 (фікстура + димовий запуск реального бінарника: `slot absent 0`), 38778372364 (фікс include-ів).
- **Наступний крок — persistence + default-off boot.** Розвідка вже зроблена:
  - схема ключів на слот: `eoip_enable` (майстер, default `0`) і для кожного слота 0..7 —
    `eoip_slotN_enable`, `_autostart`, `_local`, `_remote`, `_id`, `_mtu`, `_keepalive`, `_retries`, `_bridge`;
    усе за замовчуванням вимкнено;
  - рядки defaults додаються у `trunk/user/shared/defaults.c` (формат `{ "key", "value" },`;
    придатні унікальні якорі поблизу: `{ "help_enable", "1" },`, `{ "vpns_type", "0" },`);
  - поля WebUI — у `trunk/user/httpd/variables.c` (формат `{"key", "", NULL, EVM_RESTART_*},`),
    тому потрібен біт події; біти `EVM_RESTART_*` оголошені в `trunk/user/httpd/common.h`, зайнято
    0..15 і 17..33 — **біт 16 виглядає вільним**, але це треба перевірити перед використанням;
  - обробку події робити за зразком `overlay/padavan-4.4/ports/stubby/services-stubby.c`
    (`is_<svc>_run` / `stop_` / `start_` / `restart_`, підключення з `rc/services.c`) і моделі
    `overlay/padavan-4.4/scripts/add-amneziawg-nvram.py` для застосування схеми;
  - потім EN/UK/RU WebUI та інструкція.
- Не чіпати сторонній diff `tools/prepare-wifi-hwnat-mode.py` (лише CRLF) і не додавати untracked
  фікстури/cache у Git.
- ZeroTier заморожено; прошивання й reboot роутера потребують окремого дозволу; приймання на пристрої
  не завершене — жодного EoIP-інтерфейсу на жодному роутері не створювалося.
- Середовище: `gh` працює (у пісочниці треба очищати `HTTP(S)_PROXY`); `apply_patch` працює; пошук
  логу невдалого кроку: `gh api .../jobs/<id>/logs --allow-escape-sequences`; профілі налаштувань і
  перемикач режимів — `codex-mode-switch.ps1`; виключення Defender заблоковані (обліковий запис не
  адміністратор); скрипти `codex-repair-thread-index.py` і `codex login --with-api-key` чекають запуску
  користувачем.


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
| 2026-10-15 | Роль передано DeepSeek | Користувач: «Візьми собі роль виконавця». Sol — перевіряльник. Прийняття на HEAD `c38ec51`; перед прийняттям перевірено пакет збірки №310. |
| 2026-10-15 | Роль повернено агенту Sol | Користувач: «Передай роль Солу». DeepSeek — перевіряльник. Передано на HEAD `807668f` із переліком виконаного, доказів і відкритих пунктів вище. |

| 2026-10-17 | Роль передано DeepSeek | Пряма вказівка користувача «Передай роль DeepSeek». Код/докази 6fa5796; збірка №364 і service №141 успішні. Sol — перевіряльник. |
| 2026-10-17 | Роль передано агенту Sol | Пряма вказівка користувача «Передай роль Солу». DeepSeek — перевіряльник. Передано на HEAD `ed735f6` (== origin/main); стан блоку WG/AWG профілів і наступні кроки — в актуальній передачі вище. |

## Як змінювати цей запис

Оновлення робить лише агент, який отримав роль, і лише після явної вказівки
користувача. Зупинка мети ставить роль на паузу; відновлення мети тим самим
агентом повертає роль без нового погодження.

### Protocol configuration transport candidate — 2026-10-17

Added config-apply.c/h: revalidate and render the chosen record, refuse unresolved
hostname endpoints, execute the fixed WG/AWG control with canonical wrvpn<ID>
and setconf arguments. Input uses a 0600 temporary file unlinked before keys are
written; the child reads its inherited regular descriptor through procfs. No
shell, inherited management descriptors, environment credentials or child output
are exposed. Bounded child wait returns UNKNOWN after failed/uncertain execution;
zero exit is only ACKNOWLEDGED and is not configuration readback/connectivity.
This primitive is deliberately not packaged or connected to startup: caller-side
session ownership checks, endpoint pinning, readback, routing/DNS and rollback
must be integrated before enabling it. Service CI now tests transport with real
pinned validators and fake controls (no network mutation). CI pending.

Service CI #137 for 2857ca2815a5462996974e272ebd5c1b025e3197 completed successfully:
https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38982959450
The job log confirms PASS apply transport for both protocols, private unlinked
input, FD/environment isolation, secret-output suppression and refusal/failure/
timeout paths, compiled with address/undefined sanitizers. This supersedes the
pending status above. No real control netlink mutation, MIPS adapter execution,
readback or physical runtime acceptance has yet been tested for this candidate.

### Native protocol readback candidate — 2026-10-17

Added config-readback.c, compiled separately against pinned WG/AWG parsers and
IPC: compare private key, fwmark, requested listen port, exact peer membership,
preshared keys, keepalive, requested endpoint and normalized AllowedIPs sets.
AWG-specific requested fields, including header ranges and newer optional fields,
are compared with their presence flags. Dynamic counters/handshakes are excluded.
A missing device or changed interface index is UNKNOWN, not a match. Numeric-only
getaddrinfo prevents DNS resolution in the readback process. The bounded transport
now has fixed readback-wg/readback-awg helpers and distinct match/mismatch/unknown
results. Parent must still check session ownership around the operation. A match
is only the requested protocol snapshot; address/routes/DNS/connectivity remain
separate gates. New helper is not packaged or exposed yet. CI tests pinned native
IPC compilation and a missing real device, with synthetic observed devices for
field drift; no physical-kernel configuration is claimed. CI pending.

Service CI #140 for 618a68e5d59f1087e040dfcc3f2becfa06887099 passed:
https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39003287058
Both pinned native readback checks passed after supplying upstream RUNSTATEDIR
and curve25519 IPC dependencies (earlier #138/#139 failed fixture compilation).
Added readback-wg/awg packaging and MIPS image gates for missing-device,
legacy-name and hostname rejection. Packaging is pending full firmware CI.
Helpers are read-only and have no startup hook. The apply/controller candidate
remains unintegrated; real session ownership, endpoint routes, protocol mutation,
readback on a configured physical interface and address/route/DNS rollback remain.

Build #364 and service #141 passed at 1eaa5a5. Downloaded TRX SHA256 and original MIPS readback/manager reports verified; see docs/evidence/WR1200JS-BUILD364.md. This supersedes pending packaging above. Configured physical interface readback and concurrent network lifecycle remain unverified.
