# WR1200JS: IoT через заздалегідь створений MBSSID

2026-11-07. Нова стратегія дозволена власником. Статус: source/host
feasibility частково підтверджено; implementation/build/runtime НЕ завершені.
ROM ACK protection та чинні admission gates не змінено.

## Встановлено з pinned c25283e vendor source

- `trunk/user/rc/net_wifi.c:control_guest_rt` перевіряє UP Main, режим і radio;
  виконує `wif_control(IFNAME_2G_GUEST,...)`, bridge attach/detach та
  restart_guest_lan_isolation. Саме ця функція не викликає restart_wifi_rt.
  Зміна SSID/security через загальне Apply може мати інший restart path;
  не прирівнювати scheduler toggle до всіх WebUI змін.
- `ap/ap_mbss.c:RT28xx_MBSS_Init` читає BssidNum, обмежує MAX_MBSSID_NUM,
  створює/реєструє додаткові netdev; failure може зменшити BssidNum.
  Це initialization-time creation, не доказ довільного runtime hot-add.
- `ap/ap_mbss_inf.c:MBSS_VirtualIF_Open` викликає MBSS_OPEN, VIRTUAL_IF_UP,
  MBSS_CR_ENABLE і start_queue. Close виконує CR_DISABLE, MBSS_CLOSE,
  VIRTUAL_IF_DOWN. Vendor unchecked return values вже мають окремі reviewed
  candidate wrappers; не повертатися до необмеженого raw open.
- `common/cmm_cfg.c:CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP` за count>0 збільшує
  reference і оновлює beacons; за count0 викликає rt28xx_open(Main).
  DOWN викликає physical close лише коли останній reference зник.
- `ap/ap_mbss.c:MBSS_Close` видаляє клієнтів цільового BSS, bBcnSntReq=FALSE,
  rebuild/update beacons і per-BSS Band Steering notification. Інші BSS також
  проходять beacon rebuild; збереження associations потребує фізичного тесту.
- `mbss_cr_enable` змінює LPON sub-BSSID timing/BCN queue registers. Наявність
  такого коду не доводить безпеку concurrent watchdog/reset.

## Виконана перевірка

`tools/iot/check-mbss-no-radio-restart.py DRIVER` виконує actual extracted
vendor UP/DOWN switch cases із ASan/UBSan, підставленими callbacks і count.
1000 third-reference cycles з count2 зберігають count2 та не викликають
physical open/close; count1 також зберігає Main. First/last reference окремо
перевірені. JSON: docs/evidence/WR1200JS-MBSS-NO-RESTART-HOST.json.
Це не execution повного MBSS open, beacon descendants, IRQ/DMA чи associations.
TemporaryDirectory видалив outputs; нових build trees не залишено.

## Зміни архітектури, які ще потрібні

Поточний `profile-line.h` перетворює BssidNum2->3 на ON і3->2 на OFF;
`radio-profile-state.h` вимагає radio quiescence для profile changes;
`activation.h` включає PROFILE/RADIO_PREPARE з можливим reload. Саме це слід
замінити для нового шляху, а не прибрати ACK/lifecycle gates.

1. Завжди резервувати третій BSS під час звичайного2.4GHz boot profile,
   незалежно від runtime IoT enable. Забезпечити валідні окремі credentials,
   default OFF, ra2 DOWN і відсутність beacon/data доступу до readiness.
   Не використовувати прихований SSID як заміну disabled BSS.
2. Розділити loaded profile generation та saved requested config. Якщо
   credentials відрізняються від loaded BSS, не перезапускати radio приховано:
   дослідити підтримані per-BSS setters і їхні побічні ефекти. Якщо вони
   рестартують AP, окремо спроєктувати cold-boot application/UX; не підміняти
   вимогу повноцінного Apply збереженням без дії.
3. Новий no-reload activation потребує generation-bound доказу: ra2 реально
   існує на потрібному adapter, BssidNum>=3, його loaded security збігається,
   Main READY і не закривається. Наявні `mbss-open-admission.inc` та
   `mt7603-main-observe.h` використовувати як основу; не довіряти одному if_up.
4. Зберегти quarantine-before-open: dedicated br-iot/subnet, DHCP/DNS ready,
   scoped firewall/WAN policy до BSS_UP. OFF спочатку підтверджує закриття BSS,
   потім scoped services/network teardown; preserve isolation при uncertainty.
   IPv6 або повна окрема політика, або доведений fail-closed; не допустити
   витоку link-local/LAN через bridge/offload.
5. Обов'язкові перевірки whole existing candidate: no physical open/scan у
   toggles; Main/Guest reference ownership; close/reset/PM/watchdog races;
   beacon/TX callback drain і повторний ON; mixed family5GHz/Band Steering.
6. Target/ROMFS/image gates та фізичні тести окремо. Ordinary startup/restart
   залишається вимогою: ROM blocker можна відокремити від routine IoT toggle
   лише після доказу, що новий шлях його справді не використовує, без регресії
   погоджених звичайних Wi-Fi операцій.

## Наступний крок

Простежити per-BSS SSID/auth/key setter side effects та init profile integration
перед production зміною BssidNum/defaults. Лише після цього реалізувати
стабільну резервацію і новий activation backend. Не оголошувати альтернативу
реалізованою на підставі одного dispatcher host fixture.

## Виконання за докладним завданням власника

Вкладений текст7fac9903... прочитано як пряме завдання. Preferred A обрано
для подальшої реалізації; B (hidden SSID) не замінює disable. C через звичайні
vendor setters не є безперервним рішенням: Set_AP_SSID_Proc викликає
APStop/APStartUp, Set_AP_AuthMode_Proc скидає PortSecured для всіх client entries.
Точні line/hash evidence: evidence/WR1200JS-MBSS-CREDENTIAL-SETTERS.json.
SSID/security provisioning відокремлюється від routine toggle. Жодного
прихованого restart або вигаданого ioctl не додано.

Додано precreated-profile.h: cold-preparation функція завжди формує третій
профіль із валідними IoT credentials, незалежно від requested enable0/1;
не змінює існуючі ON/OFF helper semantics і не викликає radio/service API.
check-precreated-profile.c перевірив однаковий зарезервований профіль для ON/OFF,
Main/Guest/channel/auto-selection preservation і zero-output rejection для
невалідних inputs. GCC ASan/UBSan PASS. Fixture включено до існуючого optional
candidate script; bash-n PASS, GitHub run ще не виконувався.

Це staged component, НЕ інтегрована production резервація. Cold hook,
loaded-profile identity, no-beacon-on-boot і runtime activation backend ще
відкриті. Не подавати цей результат як THIRD BSS RESERVED на firmware/device.

| Критерій | Поточний доказ |
| --- | --- |
| THIRD BSS RESERVED | Cold profile component host-tested; startup integration pending |
| IOT RUNTIME ENABLE/DISABLE VERIFIED | Vendor reference dispatcher host-tested; full candidate/backend pending |
| NO PHYSICAL WIFI RESTART DURING IOT TOGGLE | Reference count branch host-tested; whole call graph pending |
| NO CHANNEL SCAN DURING IOT TOGGLE | Not yet proved for composed backend/beacon descendants |
| MAIN/GUEST REGRESSION TESTED | Host reference-count/profile preservation only; device pending |
| NETWORK ISOLATION VERIFIED | Existing scoped components require composed lifecycle/image validation |
| BUILD VERIFIED | New component host compiled; MIPS/firmware pending |
| PHYSICAL RUNTIME VERIFIED | RUNTIME PENDING; device authorization separate |

Наступна дія: перевірити initial bBcnSntReq/data admission третього BSS та
точний cold profile hook, потім підключити резервацію і backend без reload.
Раніше дозволений контрольований provisioning не є дозволом змінити живий
роутер. ROM ACK issue лишається unresolved окремо.

## Reserved BSS: beacon admission перевірено на candidate

`check-precreated-beacon.py` витягує фактичну BeaconTransmitRequired з retained
candidate і виконує її з ASan/UBSan у звичайній та WDS конфігурації. За stale
bBcnSntReq=TRUE відсутній або DOWN secondary netdev не проходить predicate;
Main/WDS винятки зберігаються. Відкритий secondary потребує також beacon intent.
Тест підключено після свіжої генерації candidate у наявному optional script.
Локальний retained candidate старіший за HEAD; свіжий CI ще не запускався.

Source audit: APStartUp має окремий AIRPLAY_SUPPORT writer bBcnSntReq;
OID_AIRPLAY_ENABLE теж може його підняти. Тому не покладатися лише на початковий
нуль flag. Existing candidate netdev-running gate потрібний навіть за постійної
резервації. Vendor ap_sync.c перевіряє if_dev/running перед probe response;
ap_auth.c також перевіряє це перед authentication і переходить auth_failure
для DOWN BSS. Association, залишені MAC entries, data paths, recovery queues
та hardware drain ще потребують окремої композиційної перевірки.
Це не доказ повної RF/data тиші або готовності cold startup hook.

## Association/data snapshot guard staged

Source review found association after MacTableLookup checks only VALID_MBSS,
then mutates AuthAssocNotInProgressFlag; an existing client entry could refer
to a now-closed third BSS. Added isolated prepare-precreated-bss-admission.py:
MT7603/MT_MAC/PCI guarded check after BSS lookup, before association mutations;
RX check after PACInquiry for client entries, before data side effects.
Header rejects third BSS if invalid BssidNum, missing/DOWN interface or absent
beacon intent. Main/Guest and other chips retain their paths. No MCU commands,
ID/ACK changes, scans or radio calls introduced.

ASan/UBSan host predicate tests pass; installer tested on a temporary exact
copy of retained candidate with manifest/anchor checks. Copy auto-removed.
CI preparation layer and host fixture added, target compilation pending.
This is snapshot rejection, NOT a replacement for existing peer/transition
ownership across the rest of packet processing. Races, multicast/forwarding,
probe/auth failure responses and complete RF silence need composed review.
Cold startup hook remains unbound until those checks and target build pass.

## No-reload activation controller implemented (backend pending)

`activation.h` now provides `wr_iot_activation_start_precreated` alongside the
unchanged legacy entrypoint. Mode is chosen under the existing lock and retained
through recovery. Reserved start sequence replaces PROFILE/RADIO_PREPARE with
RESERVED_READY; generic dispatch refuses those two legacy operations in reserved
mode. Rollback RESTORE and normal OFF DISABLE_APPLY dispatch distinct reserved
operations. A legacy backend cannot accidentally handle those as a global
profile restore. Reserved operations must retain third loaded profile, restore
only owned network/service state and verify current Main/Guest configuration.

READY requires the actual loaded identity/credentials and closed BSS on the
current adapter generation; mismatch must refuse, never provision implicitly.
QUIESCE/BSS_UP and all network operations retain their existing ownership,
readiness and failure obligations. This controller does not supply a production
backend and therefore does not itself prove no radio restart in backend code.

Host ASan/UBSan: existing activation regression passes; new test executes100
cycles, injected failure at each of11start stages, loaded-profile rejection,
retained failed rollback and OFF retry. No legacy profile/reload/restore operation
reaches the reserved backend. Test receipts are injected; no loaded-driver,
association, DHCP or physical-RF evidence claimed. Both fixtures added to existing
candidate CI. Target/ROMFS/runtime and actual backend remain pending.

## Loaded-profile comparison primitive (unbound)

Source audit confirms SIOCGIWESSID in os/linux/ap_ioctl.c reads actual per-BSS
SSID; OID authentication query reads AuthMode. Neither proves requested PSK.
Some OID SSID cases are APCLI-specific; do not use them as AP2 readback.

Added precreated-loaded-config.h: internal driver-side matcher of expected
netdev, exact SSID bytes/length, WPA2PSK/AES/group AES/802.1X-disabled and32PMK
bytes against actual BSS_STRUCT. No secret output, log, MCU command or new ioctl.
Expected PMK must come from independent derivation of requested credentials,
not copied from loaded state. Existing configuration/lifetime owner required;
this predicate itself supplies neither serialization nor generation receipt.

Host ASan/UBSan rejects all64single-byte SSID/PMK mutations and wrong device,
length/security fields. Header staged in isolated candidate for actual type
compilation; no production callsite/backend authorization yet. No high-level
claim of loaded identity, PBKDF correctness or runtime credentials verified.
Remaining backend work: actual request-to-driver binding/independent PMK,
read/compare under owner, revalidate ticket/generation before BSS open, fail
mismatch without legacy reload fallback. No arbitrary unsupported vendor
commands added. Current work local and not covered by854/855.

## Independent requested-key derivation

Added precreated-key-match.h: validate8..63printable passphrase or64hex PMK,
derive with existing RtmpPasswordHash from requested SSID/password, compare via
loaded matcher, clear local40byte derived and64byte passphrase buffers using
volatile writes. No radio/MCU command, setter, new ioctl or secret export. This
routine must run in task context outside spinlocks, while a configuration lease
and adapter lifetime pin remain owned; revalidation still mandatory. Existing
vendor crypto local stack cleanup is not changed or claimed here.

check-precreated-key-match.py extracts actual vendor SHA1, HMAC-SHA1, F and
RtmpPasswordHash (not injected hash callbacks). ASan/UBSan PASS; four outputs
match independently computed hashlib PBKDF2-HMAC-SHA1/4096 vectors including
63character password/32byte SSID. Raw64hex path and wrong-password rejection
also pass. Legacy crypto source contains non-UTF8 comments; extraction uses
latin1 then removes comments, preserving executable ASCII source.

Both matcher headers staged for target typecheck; no backend/callsite grant yet.
Host fixture added to CI; target result pending. Full request-to-driver transport,
loaded generation receipt and cold hook remain required. This work does not
claim no-restart physical operation or resolve ROM ACK safety.

## One-use observation binding primitive

precreated-open-proof.h binds a readback window to existing BSS_OPEN claim,
exact netdev registry generation and immutable request generation. Begin and
finish require transition lock; expensive key readback/derivation runs outside.
Finish reuses virtual_open_claim_matches, requires MBSS family and exact IoT
device, consumes the proof even on refusal; no second ticket/refcount mutation.
Task-owned configuration lease and lifetime pin must still span the window;
uncoordinated setters are not made safe by this token.

ASan/UBSan test passes valid case and14failure variants including reset/close,
Main down, PM, retirement, registry generation/family/removal, device/serial,
request change, failed/nonboolean observation and completed virtual-UP. Reuse
of consumed proof always refuses. Added host CI fixture. This token is not yet
bound to a production ioctl/backend; it does not turn injected readback into
hardware evidence. Integration must derive request identity from existing
activation transaction and match requested credentials independently.

## Cold input separate from runtime OFF

precreated-profile-request.h reads/copies validated SSID/key even when runtime
IoT is OFF. Runtime request.h keeps its original OFF behavior (no credentials
or network required). New reader defaults empty enable to OFF, rejects invalid
credentials without writing output, uses existing shared WPA2/AES validator and
copies borrowed NVRAM buffers before next read. No persistence, radio action,
implicit credentials or fallback added. Empty unprovisioned keys still refuse;
production startup must not bind that refusal in a way that breaks Main/Guest.
Initial default provisioning remains a separate unresolved integration item.

ASan/UBSan host fixture passes OFF/ON/empty-enable, shared-buffer mutation,
invalid input output preservation and old runtime OFF regression. Added to CI
host fixtures; current edit local. This is a cold-input building block, not a
startup hook or evidence of actual loaded ra2. Next bind provisioned cold input
to precreated-profile, handling unprovisioned factory configuration safely.
