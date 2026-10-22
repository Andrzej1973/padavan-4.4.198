## Git handoff integration — 2026-10-22

PROJECT_STATUS.md and CODEX_HANDOFF.md are now included in Git together.
Earlier statements below that these files are untracked describe historical
checkpoints and are superseded by this entry. The active local IoT candidate
changes remain separate and uncommitted; publishing these handoff documents
does not publish or validate that candidate. Continue from the latest dated
IoT checkpoint and inspect git status before editing the shared checkout.
## Звірка почергової роботи IoT — 2026-10-22

Sol перевірив AGENTS, bootstrap, правила Sol/DeepSeek, поточну роль, Git-історію tools/iot, локальний diff та unified assembler. Робота ведеться в одній теці й гілці; наступні кандидати використовують попередні queue/error/beacon/MBSS напрацювання через prepare-radio-queue-candidate.py з явною перевіркою перетинів. Окремий production backend не створено. Поточний єдиний автор — Sol; запис передачі DeepSeek сам по собі не підтверджує прийняття або виконання ним коду. Git author Codex/Andrzej1973 не дозволяє достовірно приписати кожний коміт конкретній моделі.

Відкриті спільні кроки: mandatory BSS/main close, узгодження всіх radio/reset/ATE входів, час життя адаптера, обробка CR_ENABLE та rollback, фактична MIPS-компіляція й перевірка IoT DHCP/firewall/ізоляції на пристрої. Host-перевірки в цьому аудиті повторно не запускалися. PROJECT_STATUS.md і CODEX_HANDOFF.md досі untracked: доступні іншим акаунтам у цій теці, але не передаються через GitHub. Історичні блоки містять старі наступні кроки; актуальним є верхній датований checkpoint та пізніші секції IoT contract. Роутер і CI не змінювалися.
## Reset/stop RTNL cycle avoided in candidate — 2026-10-22

Kernel ndo_open/stop paths hold RTNL; reset drain now trylocks RTNL without
waiting, retains pending scope on refusal and holds RTNL around raw reset.
Host wrapper cases passed external RTNL refusal/retry and lock ordering.
This addresses the modeled worker-join lock cycle only; all caller contexts,
radio/ATE writers, observation ordering and adapter retirement remain open.
Next bind mandatory stop using proved outer ownership, never -EBUSY-as-stop.
No production or device mutation. See IoT contract.

## Mandatory stop and teardown trust fixed — 2026-10-22

Linux dev.c clears START and ignores ndo_stop return, so -EBUSY is not a safe
retry. Selective-close model now permits UNVERIFIED/FAULT teardown and preserves
prior trust/readiness plus pending reset; strict host cases passed. Actual stop
binding must complete or pin explicit recovery resources, with last-reference
adapter close decision under the same owner. No driver stop hook installed yet.
See IoT contract for pinned kernel lines and acceptance boundary.

## Actual secondary-BSS open admission staged — 2026-10-22

Unified MBSS wrapper now reserves BSS_OPEN before raw mutations, preserves
abort/refcount repairs, refuses unverified/main/NULL inputs and retires raw
success UNVERIFIED. Final extracted raw+wrapper passed base/MT/HNAT host cases;
ABI equivalents added, not run. Evidence Temp/iot-unified-radio-9h9m7gcq/
bundle-mbss-open. Mandatory close/count/lifetime and CR_ENABLE-result rollback
remain next; no production/device mutation.

## Beacon/error work merged with reset admission — 2026-10-22

Shared queue assembler now incorporates existing error/MBSS/beacon bundle.
Reviewed PCI overlap merges guarded PDMA body (private raw name) and kickout
without erasing reset wrappers. Final hashes/markers, queue, beacon-kickout and
PDMA-gate strict host fixtures passed. Evidence Temp/iot-unified-radio-9h9m7gcq/
bundle-exact, extracted via exact cat-file blobs after archive blob refusal.
Full driver/secondary-BSS admission/retirement/runtime unverified; continue from
this unified bundle. No production/router mutation.

## Real reset wrappers/retry staged — 2026-10-22

Pinned raw PSE/PDMA functions now have public admission wrappers in shared
bundle; nested PSE calls raw PDMA under one ticket. Periodic command-thread
MLME path drains pending work. Host wrapper test and generated nested-call/
hook/hash checks passed; ABI fixture added, not run. Completion remains
UNVERIFIED. Deadline, lifetime, BSS exclusion and merging existing beacon/error
cmm_mac_pci.c edits remain open. Evidence Temp/iot-merged-adapter-07uv56fd/bundle-reset.
No production/router mutation.

## Reset scope/startup request loss fixed — 2026-10-22

Candidate now retains reset during busy START despite physical DOWN phase;
PDMA/PSE kinds coalesce and are captured per admitted RESET ticket. Requests
during active reset remain for next pass with original scope. Strict host
cases passed. Real watchdog/top-level wrappers/retry execution remain unbound;
PSE includes PDMA and must not be silently downgraded. See IoT contract.

## Mandatory reset request retained — 2026-10-22

Added reset_pending admission state, coalesced requests, stale epoch rejection
and second reset retained if requested during current reset. Strict host cases
passed. Source PSE already mutates before nested VOID PDMA call, and watchdog
clears its flag after return: do not add busy-return only in PDMA. Bind one
owner at top-level PSE/direct-PDMA plus explicit retry scheduling next; actual
reset entries remain unmodified. See IoT contract. No router change.

## Actual-driver-header observer compile gate staged — 2026-10-22

WR post-build capacity diagnostic now also compiles observer against rt_config.h
with recorded Kbuild flags and requires ELF32 LE MIPS, preserving command/hash/
object evidence outside source. Self-tests passed runner control cases with
explicitly injected object bytes; no real target compiler executed locally.
Actual-header compile remains CI-pending; no workflow started. Continue source
open/close/reset writer coverage. See IoT contract for scope and limits.

## Bounded MT7603 config observer candidate — 2026-10-22

Added actual-driver-type observer: main/candidate state, flags, one ARB_BCNQCR0
read with all-ones rejection, main-on/candidate-off bits and final flags check.
17 host cases+NULL passed; header carried by shared bundle and host CI added.
This is configuration observation, not RF proof or complete readiness acceptance;
do not promote READY until scope/writers/target headers validated. No device change.

## Same-generation radio verification admission — 2026-10-22

VERIFY now reserves observation and clears readiness until readback completes;
verify_finish accepts only unchanged epoch and uninhibited main. Strict host
cases passed success/failure and main-down/close during reads, with no BSS
admission on rejected results. Hardware reader and real writer coverage remain
unbound. Next bounded MT7603 observation callback, not IRQ-only SANITY_CHECK.
No production/router changes. See IoT contract.

## Real main-open admission staged — 2026-10-22

Shared bundle MainVirtualIF_open reserves START/MAIN_OPEN before AP mutation,
releases short lock for vendor calls, balances rejected/failed refs and retires
failure. Software success publishes UNVERIFIED (IoT stays closed): normal
SANITY_CHECK is IRQ-only, insufficient radio proof. Three actual-wrapper host
variants passed after fixing test macro shadowing; evidence
Temp/iot-merged-adapter-07uv56fd/bundle-main-admission-fixed. Next proper radio
observation plus BSS/reset/close gates and lifetime; production excluded.

## Selected open-path evidence expanded — 2026-10-22

Pinned config defaults IFUP_IN_PROBE off; full target evidence still needed.
Capacity probe now reports IFUP_IN_PROBE/MULTI_CORE_SUPPORT/KTHREAD_SUPPORT
from actual rtmp_chip.o preprocessing, with explicit translation-unit scope
and null when unavailable. Host self-test passed feature-defined (including
=0) and failure cases. No firmware run launched. Continue selected non-probe
main-open admission; probe timeout remains a variant requirement, not proved
active on WR1200JS. See IoT contract.

## Main-open module-reference repair staged — 2026-10-22

Actual pinned MainVirtualIF_open candidate now balances module references on
NULL and VIRTUAL_IF_UP failure; NULL returns failure. Extracted wrapper passed
strict host base/AP-HNAT/probe-success fixtures; ABI checks added, not run.
Shared bundle contains this repair. AP_MAIN_OPEN rollback and unbounded probe
wait remain open; main-open admission still must precede mutations. See IoT
contract. No production/router change.

## MainVirtualIF_close hook staged and checked — 2026-10-22

Shared queue/MCU/adapter bundle now includes actual pinned main-close wrapper:
main-down invalidation under dedicated lock before all existing mutations,
released before teardown. Extracted full-wrapper strict host fixture passed
base/HNAT/IFUP_IN_PROBE; same three checks added to ABI (not run). Evidence
Temp/iot-merged-adapter-07uv56fd/bundle-main-close. Only this entry is staged;
open/reset/secondary-close and retirement still unbound; no production change.

## Main-down with surviving BSS modeled — 2026-10-22

Added main inhibition/epoch invalidation and explicit MAIN_OPEN admission.
Late completion cannot undo newer main-down; selective close can retire guests
without readmitting IoT/reset. Strict host interleaving fixture passed. Bind
main-down before actual main-wrapper mutation and permit explicit reopen only
from existing authorized main-open. Actual driver hooks/lifetime unverified.

## Selective BSS close admission — 2026-10-22

Added BSS_CLOSE separate from adapter CLOSE; strict host test proves exclusion
of concurrent open/reset while successful selective close retains main readiness
and epoch. Source main wrapper mutates before VIRTUAL_IF_DOWN: main-down must
invalidate readiness at wrapper entry even if guests retain adapter references.
Next cover this inhibited-main state and actual wrapper/count bindings. No
production or device change. See IoT contract for evidence and limits.

## Queue/MCU/adapter candidates assembled together — 2026-10-22

Existing radio queue bundle now includes adapter fields/lock init/free. Exact
reviewed init insertion merges with queue rtmp_init.c changes; arbitrary
overlap still refuses. Final markers, unique manifest hashes and actual queue
composition fixture passed strict host GCC. CRLF/LF comparison corrected;
source blob checks retained. Evidence Temp/iot-merged-adapter-07uv56fd/bundle-fixed.
Whole driver/entry admission/retirement unverified. Next bind actual vendor
open/close/reset entries and retirement to the now-shared adapter state.

## Adapter-owned state/lock staged — 2026-10-22

Added pinned prepare-radio-adapter-candidate.py: dedicated adapter fields,
init before successful publication after allocation failure branches, normal
free hook. Exact-source generation/order checks, extracted strict-GCC init/free
fixture and drift refusal passed. Evidence Temp/iot-adapter-candidate-jsmcqyas.
Not production installed; entries/destructor retirement remain unbound. Do not
install free hook before proving all references retire; merge overlap with
other rtmp_init.c/header candidates explicitly. Next actual entry/lifetime binding.

## Partial adapter initialization guarded — 2026-10-22

Pinned allocator failure after stats allocation bypasses normal lock destructor;
transition lock needs matching local unwind, not only RTMPFreeAdapter binding.
Admission candidate now rejects zero/uninitialized epoch for all operations;
strict host lifecycle fixture passed. Real publication/lock lifetime remains
unbound. Next implement adapter field/init/unwind together and prove no caller
can touch the lock before initialization or after teardown. See IoT contract.

## Reconstruction epoch fixed — 2026-10-22

Shared radio admission now advances epoch on START/RESET as well as close;
pre-reset queued BSS work remains rejected after successful reset. Strict host
fixture passed. Source confirms VirtualIfCnt is incremented BEFORE first radio
open, so it is not readiness proof. Lock allocation/free anchors identified;
actual adapter lifecycle binding remains pending. Details in IoT contract.
No vendor driver/production/router mutation.

## Shared radio admission candidate — 2026-10-22

Added tools/iot/radio-transition.h plus strict host fixture: exclusive
START/BSS_OPEN/RESET/CLOSE tickets, close latching, stale epochs/completions,
reset failure and exhaustion. Host passed; ABI host-sanitizer/MIPS steps added,
not run. External common adapter lock/lifetime and all vendor entry bindings
remain required. This candidate is not installed and does not yet establish
real atomic readiness/open. Next bind to adapter lifecycle and specify retry
for mandatory close/reset without holding a lock across worker join.

## Actual pre-suspend notification fragment checked — 2026-10-22

The generated composition fixture now executes the actual unconditional pending
notification walk: two IoT nodes/foreign tail, repeated cancellation, no frees,
retained queue refs, refused start, later retirement. Strict host GCC passed
against exact pinned source using approved local escalation after WinError 5.
Evidence: Temp/iot-queue-notify-mbgqx3al and the IoT activation-gap report.
This supersedes only the missing notification-slice coverage, not full worker
shutdown, concurrency or adapter lifetime. Next: shared open/close/reset
transition admission and suspended-queue retirement. No production/router change.

## Owner checkpoint reaffirmed: atomic radio/BSS open — 2026-10-22

Rechecked: no production backend or proven open/close/reset exclusion exists.
activation.h now explicitly requires readiness/generation recheck within the
same driver transition ownership as BSS_UP. Added injected readiness-loss
between stages: zero opening mutations, successful recovery; strict MinGW
activation fixture passed. This is a backend contract test, not driver locking.
Next remains the shared adapter open/close/reset admission and lifetime protocol;
queue cancellation work is supporting work only. See IoT activation-gap report.

## Pending IoT cancellation candidate — 2026-10-22

Added notification-only cancellation preserving envelope/queue reference; worker
exit generator notifies before suspend-dependent cleanup. Strict MinGW result
fixture passed (reference retention, single notification, start refusal, later
cleanup); generator syntax/whitespace passed. Generated worker/target execution
and suspended-queue retirement remain unverified. Next check actual generated
exit slice and adapter lifetime. Production/router unchanged. See IoT gap report.

## Command shutdown and accepted IoT work — Sol, 2026-10-22

Verified pinned worker/dispatcher/queue source: STOPED blocks enqueue but does
not terminate a CMDHandler already draining; exit frees queued payloads without
an IoT terminal result, and suspended exit skips that cleanup. Added production
contract gates for generation admission, explicit cancellation and retained
lifetime. Existing checked-enqueue candidate already addresses false ACK on
rejection; do not duplicate it. Next integrate cancellation/refcount with
radio lifecycle candidates before installing any transition gate. Evidence:
`docs/evidence/WR1200JS-IOT-ACTIVATION-GAP-2026-10-21.md`.
No router/production mutation, firmware build or executable tests.

## Close/command-thread dependency — Sol, 2026-10-22

Pinned source confirms radio close and initialization-failure cleanup join the
command worker through RtmpMgmtTaskExit/RtmpOSTaskKill. Since watchdog reset
can run in that worker, a mutex held across close and awaited by reset risks
a join/lock cycle. Require short nonblocking transition admission and release
before joins/polls; audit queued work/lifetime next. Source evidence and line
references: docs/evidence/WR1200JS-IOT-ACTIVATION-GAP-2026-10-21.md.
No driver/production/router change or build/test in this source audit.

## Роль прийнята Sol — 2026-10-22

За прямою вказівкою власника Sol прийняв роль єдиного виконавця.
Гілка `codex/wr1200js-service-webui`, HEAD при прийнятті
`441138aa8c8b3abf28e0d8eb2401cbac4bb218f8`; tracked working tree був чистий.
Попередні записи DeepSeek нижче історичні; актуальний виконавець — Sol.
Наступне: IoT transition owner для open/close/reset та атомарний зв'язок
main-radio readiness з BSS_UP. CI/пристрій зараз не перевірялися; прошивання
не дозволене цим прийняттям ролі. Правила одного автора та обох агентів чинні.

## IoT main-radio readiness gate and role handoff — 2026-10-22

Candidate activation order now has `WR_IOT_MAIN_RADIO_READY` after radio
preparation/policy and immediately before `WR_IOT_BSS_UP`. Its production
backend must observe the primary 2.4 GHz interface UP on the expected adapter
and the candidate IoT BSS DOWN. The strict MinGW injected-backend fixture passed,
including a missing-main-radio case that aborts before BSS_UP and rolls back.
This does not prove the backend or radio exists in production. The readiness
observation can race with BSS open unless both are serialized and the state is
revalidated under the same adapter/BSS transition owner.

At the owner's direction, the next executor role is handed to DeepSeek. This
repository note records the handoff but is not evidence that DeepSeek has
accepted the live checkout. Sol and all Codex writers must continue to observe
the one-writer rule. Current
branch `codex/wr1200js-service-webui`, HEAD `a6edff845ddbebd90e2833800445757290c921b9`
(at handoff). No long-running command. No firmware build, router mutation,
commit or push. Next: resolve adapter-scoped serialization across first/additional
open, close and reset, then bind main-radio readiness to the BSS_UP transition.
See `PROJECT_STATUS.md` and the IoT activation-gap evidence report.

# Handoff between Codex accounts and project agents

## PDMA reset call paths — 2026-10-22

Pinned source: periodic timer enqueues MLME command; command handler invokes
watchdogs. With selected DMA_RESET_SUPPORT, stuck PDMA marks PSE reset and
an enabled PSEWatchDog may conditionally call PSEResetAndRecovery then
PDMAResetAndRecovery. Direct
PDMA/PSE iwpriv procedures also invoke reset. No inspected entry coordinates
with an in-flight MBSS open. Trace command dependencies before using any
blocking wait or mutex; never hold BcnRingLock over reset. See IoT report.

## IoT dequeue flag writer inventory — 2026-10-22

`prepare-radio-error-candidates.py` now pins ATE source and inventories
dequeue-disable flag writers in ATE, PCI reset and radio on/off; unknown
writers fail before output. Thirteen merged host fixtures and extra-writer
negative case passed. Manifest explicitly keeps writer coordination false.
This does not solve reset/open serialization or enable IoT. See IoT report.

## IoT ABI source-path repair — 2026-10-22

Local ABI workflow now sparse-checks out mt76x3_ap for its Makefile assertion
and reads MT7603E board flags from the tracked WR1200JS overlay instead of
an absent sparse source path. Both flags and pinned Makefile text were
confirmed locally. CI not run; candidate driver object and image unverified.
No router/production change. See IoT activation-gap report.

## IoT driver integration gate — 2026-10-22

`docs/IOT-WIFI-IMPLEMENTATION-CONTRACT.md` now spells out transition
ownership, separate first/additional virtual-interface rollback, reset/close
exclusion, actual MIPS driver-object compilation and final-image proof.
Current ABI fixtures do not satisfy these gates. Do not install the partial
radio bundle or claim IoT runtime acceptance. No production/router change.

## Virtual-interface rollback source audit — 2026-10-22

Pinned cmm_cfg.c VIRTUAL_INF_DOWN decrements adapter count and closes radio
at zero; VIRTUAL_INF_UP may be the first physical startup or an increment
plus all-BSS beacon rebuild. Never add unconditional VIRTUAL_IF_DOWN after
CR_ENABLE error. DISABLE_DEQUEUEPACKET is also set in radio-off and ATE,
without candidate lock coverage. Current MBSS/CR guards are partial and
the next work is a distinct transition owner across open/close/reset and
failure rollback. No production or router state changed. See IoT report.

## CR_ENABLE reset guard — 2026-10-22

Isolated `prepare-mbss-cr-check.py` now checks the dequeue-disable reset
flag inside BcnRingLock and refuses secondary register writes during active
reset. Focused and all thirteen merged host fixtures passed. The pinned
wrapper still ignores CR_ENABLE failure after VIRTUAL_IF_UP. Do not use
VIRTUAL_IF_DOWN as an unproven rollback; first-radio close may run during
reset. Next design a complete transition/rollback protocol and target
compile. Production/router unchanged. See IoT activation-gap report.

## MBSS open reset gate — 2026-10-22

`prepare-mbss-open-state-check.py` rejects active reset under BcnRingLock
before selected BSS beacon intent is set. Four focused MinGW variants and
thirteen merged host fixtures passed. Owner's radio-ownership check shows
virtual ra0/ra1/rai0/rai1 and loaded mt76x3_ap/mt76x2_ap; device symlinks
cannot map interface ownership. Next handle reset starting between MBSS_Open
and CR_ENABLE, without unsafe VIRTUAL_IF_DOWN during reset, then target
compile. No production/router change or RF proof. See IoT report and runtime
interface report.

## Paired reset/beacon gate candidate — 2026-10-22

Pinned candidate now linearizes PDMAResetAndRecovery SET/CLEAR of
DISABLE_DEQUEUEPACKET with final beacon kickout via BcnRingLock; recovery
also skips beacon restart while reset flag is set. Standalone fixtures and
thirteen merged host fixtures passed. This is partial: CR enable can race
reset, wrapper ignores CR-enable failure, other flag owners exist, and no
MIPS/RF proof exists. Do not install or claim IoT acceptance. See IoT report.

## Reset/lock source audit — 2026-10-22

Pinned MT source confirms QID_BCN cleanup itself holds BcnRingLock, but
PDMAResetAndRecovery releases the lock between beacon-state reset, cleanup
and sync restart. Do not extend the spin lock across reset polls or all
ring cleanup calls. Selected mt76x3_ap Kbuild does not define
MULTI_CORE_SUPPORT; inspected default macros use spin_lock_bh, while
emitted target flags are unverified. Next prove a cross-section transition
protocol and compile the assembled candidate for MIPS. See IoT report.

## BSS-sync ARB candidate — 2026-10-22

Pinned MT ASIC BSS-sync queue-bit RMW now uses BcnRingLock in the isolated
bundle. Pinned grep lists five direct ARB_BCNQCR0 writers, now all covered
by the candidate's short lock sections (CR open/close, recovery, two sync).
Twelve merged host fixtures passed; workflow updated locally, CI and target
compile not run. Reset cleanup and RF quiescence remain open; manifest still
marks close exclusion unproven. No production/router change.

## Isolated first-open rollback — 2026-10-22

`prepare-mbss-abort-open-check.py` pins the MBSS wrapper/helper, dispatcher,
command enum and declaration. It adds an internal abort ioctl for failed
first VIRTUAL_IF_UP; this clears only the selected secondary beacon intent
under BcnRingLock and balances the module reference. The radio bundle now
includes all five candidate files and the abort fixture. Three standalone
rollback variants and eleven merged host fixtures passed. CI, target build,
hardware cleanup and router acceptance remain unverified; no production or
device state changed. Continue BSS-sync/reset synchronization and target
compile review before any live use.

## Bounded MBSS_Open candidate — 2026-10-22

`prepare-mbss-open-state-check.py` pins ap_mbss.c and validates BssidNum
before IdxGet; it rejects BSS 0/invalid indices and serializes secondary
beacon-intent write under BcnRingLock. The lifecycle merger and radio
bundle now include it. Four standalone MinGW variants and ten merged host
fixtures passed; CI and target/device checks were not run. Keep the
first-radio rt28xx_open failure rollback open. No production/router change.

## MBSS_OPEN result candidate — 2026-10-22

`prepare-mbss-open-check.py` now pins the source blob, checks the MBSS_OPEN
ioctl return, and balances the module reference before virtual-up on error.
Its actual-wrapper fixture passed in MT_MAC, MT_MAC+HW NAT and generic
MinGW variants. This leaves the separate first-radio `rt28xx_open` failure
stale-intent path open. AP startup can consume beacon intent, so do not
move its assignment after VIRTUAL_IF_UP without target evidence. See the
IoT activation-gap report. Production and device are unchanged.

## First-radio-open failure path — 2026-10-22

Pinned `ap_mbss_inf.c`, `rt_os_net.h` and `common/cmm_cfg.c` show that
VIRTUAL_IF_UP failure occurs only when the virtual-interface count is zero
and `rt28xx_open` fails. MBSS_Open already set beacon intent; the wrapper
ignores its ioctl status. The isolated module-ref candidate does not clear
intent. Avoid calling MBSS_Close on this failed first-open path without
proving its queue/station/beacon effects safe. Next design a scoped rollback
and verify initial beacon setup. See IoT activation-gap evidence.

## Secondary CR enable candidate — 2026-10-22

`tools/iot/prepare-mbss-cr-check.py` now holds BcnRingLock around the
secondary-BSS enable LPON/ARB block, alongside the prior disable candidate.
Pinned actual-function MinGW fixture passed, including lock assertions on
every register access and a BSS 0 case. This is isolated host evidence;
production source, firmware and router were not changed. Continue with
MBSS_Open intent ordering, BSS-sync and reset writers before claiming a
complete close/open protocol. See activation-gap evidence.

## Partial close/recovery critical section — 2026-10-22

Isolated CR-disable candidate now clears intent and ARB bit under BcnRingLock;
recovery takes the same lock only for final eligibility/restart/IDLE, after
flush polls. Final kickout candidate also rechecks under lock. Nine assembled
host fixtures passed. This is not complete exclusion: open/enable, BSS-sync
and reset writers remain uncoordinated, target/RF unverified. See
activation-gap evidence; no production/device change. Continue remaining
writers and effective lock-context review before live use.

## Final beacon kickout candidate — 2026-10-22

Pinned MT_MAC RT28xx_UpdateBeaconToAsic now has an isolated candidate that
rejects invalid BSS and rechecks BeaconTransmitRequired inside its existing
BcnRingLock before HAL_KickOutMgmtTx. Actual-function injected fixture passed
including nonrunning transition on lock acquisition; nine merged radio host
fixtures passed. ABI workflow updated, not executed. Close intent/ARB writes
are not yet synchronized; no target/RF proof or production/device change.
Continue shared transition protocol from the activation-gap evidence.

## Beacon transition writer inventory — 2026-10-22

Scoped pinned mt76x3 source has five direct ARB_BCNQCR0 writers: secondary CR
enable/disable, recovery restart and two BSS sync functions. Reset calls sync
after unlocking. Final beacon kickout is already under BcnRingLock but lacks
an in-lock active-BSS recheck. Correct next candidate must cover open/close
intent, all relevant RMWs and final kickout; do not lock the flush polls.
Pinned Kbuild has no MULTI_CORE_SUPPORT flag, but exact compiler command is
unverified. Details in activation-gap evidence. No production/device change.

## Active MT7603 recovery variant — 2026-10-22

WR1200JS board config selects mt76x3_ap, which compiles ../mt76x3 sources
with DMA_RESET_SUPPORT and TXRXCR_DEBUG_SUPPORT. Earlier fixture lacked these
branches. Recovery fixture now compiles them and covers main-BSS clock loss,
existing busy-DMA reset and debug checkpoint; focused plus eight merged MinGW
fixtures passed. ABI workflow checks board/Kbuild assumption; CI not run.
See activation-gap evidence. Next implement shared close/recovery/reset
transition; do not infer target/RF acceptance. No production/device change.

## Recovery eligibility recheck — 2026-10-22

Isolated recovery candidate calls existing BeaconTransmitRequired after flush
and before restart. With merged secondary guard, already closed/nonrunning BSS
is refused. Two added injected cases and eight merged MinGW fixtures passed;
manifest marks BSS-close exclusion unproven. A concurrent close after the check
can still race the write. Continue full short transition protocol across
open/close/recovery/reset and final kickout. No production/device change.

## Beacon restart/close lock audit — 2026-10-22

Pinned source shows CR disable precedes the bBcnSntReq clear and both ioctl
errors are ignored by MBSS_VirtualIF_Close. Recovery writes the same ARB bit
without exclusion. BcnRingLock already wraps DMA completion and beacon
kickout; a whole recovery/close lock would nest or cover long polls. BSS sync,
secondary enable and reset are other writers. Exact references and required
shared transition protocol in activation-gap evidence. No source candidate or
device change this turn. Next implement short, complete open/close/recovery/
reset ordering with final kickout recheck; do not claim current candidate
solves the race.

## Observed MMIO loss guard — 2026-10-22

Beacon recovery checks observed HALT/NIC and PCI bPCIclkOff at entry and around
direct IO. Extracted tests cover synthetic zero on clock loss, second-poll NIC
loss and final restart-read clock loss; no restart/IDLE. Eight merged bundle
fixtures passed MinGW. Not lock exclusion: change-and-revert and effective IO
variants remain open, DMA_RESET variant untested. Existing CI gates unexecuted.
Next shared restart/disable/clock-reset protocol; no production/device changes.

## Close ordering and MMIO availability — 2026-10-22

Linux clears netif_running before ndo_stop (dev.c:1394,1402,1417-1418), but stale
recovery still needs shared final restart/disable protocol. BcnRingLock already
exists; BH/IRQ macros differ by effective config. Do not hold across polls.
PCI rt_linux.h IO can return synthetic zero/skip writes at bPCIclkOff, so zero
flush bits are not proof without access availability/exclusion. Effective IO
wrapper path still needs confirmation. Exact evidence in activation-gap report.
Next short final critical section and truthful unavailable-device handling;
no new locks installed or target/RF acceptance claim this turn.

## Beacon recovery timeout candidate — 2026-10-22

prepare-beacon-recovery-check.py pins cmm_asic_mt.c; either flush timeout now
returns pretbtt=false before reenable/IDLE. Null/index/HALT guards added.
Radio-error bundle merges only this function into existing DMA candidate.
Eight bundle host tests passed; recovery uses -Wno-sign-compare for inherited
interval comparison (initial strict attempt failed). No DMA_RESET variant,
real threading/RF proof. CI updated unexecuted. Next successful recovery vs
BSS-close lock ordering; concurrent restart race not fixed. No live changes.

## MBSS lifecycle merged into radio bundle — 2026-10-22

prepare-mbss-lifecycle-candidate.py merges reviewed function slices from pinned
init/close/CR candidates, rejects other edits/conflicts, re-extracts final funcs
for tests. prepare-radio-error-candidates now uses merged ap_mbss.c and carries
close/CR additional fixtures. Three merged and seven integrated bundle strict
MinGW tests passed; injected ops, no actual kernel/RF proof. CI gates not run.
Next selective beacon drain/serialization. BSS allocation strategy still unset;
no main/guest runtime acceptance, production install or router change.

## Per-BSS CR bounds — 2026-10-22

prepare-mbss-cr-check.py pins ap_mbss.c, guards null/negative/inactive/array
count before enable/disable register IO and neighbor scan. Strict MinGW actual
functions passed injected register checks and peer queue-bit preservation.
CR disable has no drain poll/readback; zero return is not RF quiescence.
CI gates unexecuted. Next coherent merge of same-file MBSS init/close/CR edits,
then selective beacon drain/synchronization. No live binding/target/device proof.

## MBSS close bounds candidate — 2026-10-22

prepare-mbss-close-check.py pins ap_mbss.c blob 92d3b01b7be6dd7bcdfe2bc8fbc74b6838ac3b9f.
Rejects null/negative/inactive/out-of-array before stop/kick; original bounds
were after kick. Strict MinGW actual-function checks passed invalid no-effects
and secondary slots 1/2 with other beacon intents retained. Initial indentation
fixed; BAND_STEERING, full driver and RF/drain untested. Same-file MBSS init
candidate not merged yet. CI gates not run. Next per-BSS CR disable/beacon
ownership, no global adapter OFF binding or live changes.

## Checked OFF builder only — 2026-10-22

checked-radio-off-builder.inc staged by MCU preparer builds caller-owned checked
no-retry synchronous message; no send or radio flag updates. Strict MinGW actual
builder allocation/init/exact-byte test passed; CI gates not run. Builder hash
tracked by candidate/bundle. Adapter-wide OFF must NOT become per-BSS IoT toggle:
main/guest preservation would be unproven. Next selective BSS lifecycle/exclusion
review; no live issuer/worker binding, production/router changes or RF proof.

## Coherent queue/MCU candidate — 2026-10-22

prepare-radio-queue-candidate.py composes three preparers into disjoint merged
driver changes; source/tool hashes and final manifest last. Ten driver files
plus two fixture assets, explicitly partial/noninstalled/unbound. Same merged
tree passed five strict MinGW extracted/injected tests: ACK, sender, composed
dispatcher, PCI kickout and actual queue/cleanup slices. Initial fixture asset
omission/count expectation fixed before passing. Overwrite/drift refusals and
six original source blobs verified. CI gates added unexecuted. Next reviewed
lifecycle/MCU operation binding in coherent candidate, then target validation;
no real concurrency/RF or whole-driver evidence, no router changes.

## Actual dispatch/shutdown slices — 2026-10-22

prepare-queued-composition-check --cleanup-candidate extracts actual HALT/NIC
condition and dispatch/shutdown free blocks. Base and slice MinGW compositions
passed with staged headers, including NIC loss after enqueue and pending thread
cleanup. Worker operation/OS scheduling injected, full switch/task-kill/real
concurrency untested. New sanitizer/MIPS gates not run. Next coherent candidate
assembly, then MCU operation/lifecycle binding review; no production activation.

## Actual enqueue/result composition — 2026-10-22

prepare-queued-composition-check.py combines staged actual enqueue with result
producer/worker/helpers. Strict MinGW passed failure/ref cleanup, caller-first
timeout, modeled HALT, running uncertainty and worker-before-return cases.
OS primitives/scheduling injected; full CMDHandler/shutdown unexecuted. New CI
sanitizer/MIPS gates unexecuted. Next combine candidate source bundle and
validate actual dispatch/shutdown slices plus lifecycle before MCU binding.
No producer exposure/radio operation/production install or router changes.

## Producer and worker staged — 2026-10-22

queued-work.h adds queue-ref reservation before truthful enqueue; rejection
releases refs. Worker checks/start/finish, leaving queue ref for cleanup.
prepare-queue-cleanup now routes internal tag in CMDHandler before legacy
switch, using NULL operation (failure, no radio binding). Staged-header MinGW
passed early worker completion, allocation/enqueue failures, cancellation and
uncertainty. Enqueue primitive injected, no real concurrency/whole-driver proof.
Next compose actual truthful cmm_cmd enqueue with producer/worker and cleanup;
then review MCU/lifecycle binding. No production installation or device change.

## Actual cleanup hooks staged — 2026-10-22

prepare-queue-cleanup.py pins rtmp_init.c and rt_rbus_pci_drv.c, hooks common
dispatch/skip and pending-thread-exit cleanup before generic buffer free.
queued-cleanup.h handles internal 0x0D73F001 envelope (no pinned tag collision),
origin/size check, pointer clear, cancel and one queue-ref put. Strict MinGW
staged-header helper/result tests and structural hook checks passed; actual
whole driver/functions and kernel concurrency untested. CI preparer gate not
run. No producer/worker/radio binding. Next producer checked enqueue ownership
and actual CMDHandler worker dispatch, retaining result on timeout/cancellation.

## Shared queued-result candidate — 2026-10-22

queued-result.h uses kernel kref/spinlock/completion with caller+queue refs.
Reserve queue ref before enqueue and release on rejection or worker cleanup.
Queued cancellation prevents start; running timeout is UNCERTAIN, never proof
hardware stopped. Terminal result immutable; completion outside lock with ref.
Strict MinGW deterministic injected primitive cases passed; no actual threading,
target or queue binding evidence. CI gates unexecuted. Next actual HALT-skip and
thread-exit envelope cleanup hooks before free. Header remains candidate only.

## Truthful checked enqueue candidate — 2026-10-22

prepare-checked-enqueue.py pins common/cmm_cmd.c blob
c053649a0c8c12edf459300af022b64ff26d2fca. Original final success return hides
stopped-queue rejection after freeing buffer. Candidate uses one common body,
legacy-compatible wrapper plus internal truthful-status wrapper. Strict MinGW
both-wrapper failure/ownership/success fixtures passed after correcting fake
allocator pointer-output aliasing. CI gates added unexecuted. No issuer,
production install or actual queue lifetime proof. Next result refcount and
cancellation before accepted command buffer release on HALT/shutdown.

## Watchdog worker and cancellation — 2026-10-22

Periodic timer only enqueues; watchdog runs in RtmpCmdQTask via CMDHandler.
Consider same-thread checked execution; manual reset remains separate.
Do not add RTNL acquisition in worker while ioctl caller holds RTNL waiting.
Close stops RX tasklets before command thread, task-kill failure only logs.
HALT skips CMDHandler dispatch; thread shutdown frees pending command buffers.
Checked queued work therefore needs explicit cancellation completion and shared
result lifetime on timeout/skip/shutdown before release. Exact ranges in
activation-gap evidence. Next actual queue cancellation/ownership candidate;
no live binding, target compile, runtime exclusion or router change.

## Checked no-replay and RTNL entry — 2026-10-22

Checked sender rejects need_retransmit before queueing; strict MinGW sender
and composed dispatcher fixtures passed including no wait/queue and one free.
Normal commands unchanged. Pinned kernel WEXT dispatch holds RTNL at
net/wireless/wext-core.c:988-990, private net ioctl at net/core/dev_ioctl.c:555-557.
Driver rt28xx_ioctl maps netdev to adapter then AP ioctl. Use this existing
serialization when reviewing proposed issuer lifetime; do not add recursive
RTNL acquisition. Next trace normal close and asynchronous PDMA recovery context;
RTNL alone does not prove exclusion with recovery. No live issuer/target/RF proof.

## Cleanup callers and lifecycle contract — 2026-10-22

Pinned MT7603 coherent recovery returns before QID_CTRL cleanup; PDMA reset
continues after abort-poll failures. Neither is a DMA-stop success receipt.
AndesCtrlPciExit has no waiter drain before queue free/lock destruction.
Exact source ranges and required admission/drain contract are in activation-gap
evidence. Candidate manifest now records post_ownership_retirement_proven=false,
active_waiter_exit_exclusion_proven=false and prerequisites. Next scoped work:
implement/review checked admission lifetime across MCU exit/reset, without
waiting under spinlocks. No production issuer, runtime or router changes.

## Control-ring retirement evidence — 2026-10-22

prepare-control-ring-check.py pins cmm_data_pci.c blob
646beb40bc7acb8ee861190b717f8c9a465d0fae and extracts actual DMA-done handler.
Local MinGW passed no hardware progress retains packet, progress frees once,
repeat, empty and wrap cases. Registers/locks/free injected, no real DMA proof.
Vendor unused FREE counter needs -Wno-unused-but-set-variable; source unchanged.
New sanitizer/MIPS gates unexecuted. Separate QID_CTRL all-slot cleanup exists
at cmm_mac_pci.c:1841-1880. Next trace its callers/DMA exclusion together with
MCU cleanup and active waiters; MCU false sender free vs ACK lifetime unresolved.
No live issuer or production/router changes; activation remains unbound.

## Actual PCI packet ownership check — 2026-10-22

Owner radio-ownership output already saved in runtime interface report; do not
repeat the request. Virtual interface paths and refcnt=1 do not prove ownership
or unload safety. Checked MCU candidate now requires the exact reviewed PCI
callback and marks private packet ownership until ring cell assignment.
Dispatcher treats any nonzero result using this receipt, including MCU loss
after ring ownership (never private force-free). Actual extracted kickout,
sender, dispatcher/sender and receiver passed strict MinGW injected fixtures;
initial fixture field/indentation failures fixed. New sanitizer/MIPS gates not
run. Next: ring retirement after post-ownership failure and lifecycle exclusion;
no issuer bound, target compile, RF acceptance or production/router changes.

## Actual checked dispatcher/sender composition — 2026-10-22

prepare-mcu-sender-check --with-dispatcher extracts both actual candidate
functions. Strict MinGW passed with injected queue/kickout/completion, including
flags lost after queueing. Candidate now marks these checked messages
unsubmitted and wakes sender for one-time private cleanup; missing PCI callback
and non-PCI checked requests rejected. Normal commands unchanged. Fixture's
initial alias/indentation errors fixed. Added ABI gates unexecuted. Next actual
queue/ring/lifecycle concurrency and issuer binding; no target/RF acceptance.

## Checked MCU sender/early kickout ownership — 2026-10-22

Pinned PCI kickout's NDIS_STATUS_FAILURE occurs before ring ownership. Checked
candidate keeps this synchronous message alive, records unsubmitted failure,
signals waiter and lets sender force-free private packet/message once. Sender
also requires tx_done plus response_done before accepting status. Actual sender
fixture passed strict MinGW with injected dispatch/wait/queues; receiver rerun
passed. New ABI gates unexecuted. Next test actual dispatcher and lifecycle/ring
concurrency; no non-PCI acceptance claim or live command issuer. Production unchanged.

## Isolated checked MCU ACK plumbing — 2026-10-22

First checked reply is now terminal under ACK lock. Current MinGW fixture
passed success-then-rejection and rejection-then-success duplicate orders,
with unchanged first result and single completion. No real concurrency proof.

prepare-mcu-radio-result stages exact pinned header/core/MT sources separately,
with message-owned result, default-off opt-in and checked-only branch before
ACK unlock. Sender validates opt-in shape and copies result before free/queue.
No command issuer bound. prepare-mcu-result-check extracts actual candidate
branch; strict MinGW injected envelope/sequence/lock-context cases passed.
Original generic callbacks unchanged. ABI sanitizer/MIPS fixture gates not run.
Next actual sender/timeout/teardown ownership verification and full driver
compile; do not claim real concurrency or RF acceptance. Production untouched.

## Direct MCU RX route established — 2026-10-22

Use existing firmware-source-backup/padavan-4.4.git read-only grep/show at pinned
commit for complete local source searches. Direct ACK dispatch traced from
network RX tasklet, distinct from command tasklet; full close kills network
tasks before MCU cleanup. Details/blobs in activation-gap evidence. Next
checked-only short parser/result/completion under ACK lock plus message-owned
result/lifecycle exclusion; generic callbacks must retain existing lock context.
Design not implemented, timeout/waiter ownership not accepted. No production
driver/device change, new clone or backup-repo ref modification.

## MCU callback lifetime scope — 2026-10-22

Teardown does kill command tasklet before cleanup, and BH processes RX before
TX-done frees. However AndesMTRxEventHandler directly calls ACK dispatcher;
matched ACK and temporary RX are distinct objects. Queue lock released before
callback. Next trace direct RX context/shutdown and waiting sender ownership;
do not assert either safety or a validated UAF from the partial trace alone.
Manifest explicitly keeps MCU lifetime/RF/controller false and strategy null.
Source evidence recorded; no driver/device state changes.

## Strict radio-result parser; target environment remains unproven — 2026-10-22

radio-result.h rejects wrong length/ID/nonzero firmware status without aligned
casts or buffer mutation. Strict MinGW parser checks passed. No ON/OFF echo in
payload: transport must tie reply to current OFF and prove callback lifetime.
No production use; new sanitizer/MIPS gates unexecuted. WSL --list --verbose
returned install usage/exit1, no usable distro established; checked PATH lacks
Docker/MIPS compiler and local base-src lacks full kernel Makefile. Do not claim
target compilation. Continue source transport ownership integration; no router
or host environment changes beyond project files.

## Owner radio-ownership result received — 2026-10-22

Full successful owner-run output is in interface runtime evidence. ra2 absent;
ra0/ra1/rai0/rai1 virtual sysfs entries lack inspected device/driver/module
links. Both modules refcnt 1, holders listings empty. This parent lookup cannot
prove ownership or safe unload. Output no longer pending; do not ask owner to
repeat the same check. Continue source/controller lifecycle integration. No
router writes, unload, reload or firmware operation performed.

## Firmware RadioOff response gap — 2026-10-22

Andes command returns transport result; response handler only logs firmware
status, and malformed length may complete wait without callback. Checked OFF
needs exact ID 0x05/eight-byte response/status zero and message-associated
completion, with timeout/late-callback lifetime proven. No existing result
field in cmd_msg; do not install stack-response workaround. Evidence recorded,
QUIESCE contract clarified; transport source unchanged. Owner only printed the
helper path, so radio-ownership output still pending; full command resent.

## Physical radio-off/DMA completion candidate — 2026-10-22

Shutdown source route reaches MTPciMlmeRadioOff under PCI/RBUS/MT guards. Its
void poll does not report timeout and counts cumulative idle; software OFF is
not hardware completion. prepare-dma-idle-check emits separate BOOLEAN helper
with consecutive idle and explicit failure/flag cleanup, leaving old function
and callers unchanged. Strict MinGW injected cases passed; bundle/ABI additions
not executed. Next firmware ack/MAC-PDMA readback and synchronization before
QUIESCE integration. No RF proof or driver/device change; details in evidence.

## Beacon recovery is not RF quiescence — 2026-10-22

APCheckBcnQHandler timeout branches continue to re-enable BSS start bit and set
software IDLE (pinned cmm_asic_mt.c:1339-1394). Do not call it as teardown drain
or accept IDLE/admin DOWN/normal MBSS close return as RF completion. Candidate
decision guard does not serialize already-running queue recovery. Backend
QUIESCE contract clarified; next trace actual physical shutdown/completion.
Source evidence only, no device fault reproduced or router operation performed.

## Closed-secondary beacon decision candidate — 2026-10-22

prepare-beacon-guard-check adds present/RUNNING requirement for secondary
BeaconTransmitRequired, preserving main/WDS behavior. Actual extracted function
passed strict MinGW base/WDS cases. Original ap_connect.c blob
0c7565b84fb202e9a71c1669b4d1ed219ad229eb. Partial bundle now includes fourth
candidate; extended bundle and new sanitizer/MIPS gates not executed. This
guard does not drain queued frames, prove RF silence or establish a safe
reserved-BSS lifecycle. Production unchanged; ownership output still pending.

## Fixed radio-ownership evidence request — 2026-10-22

New helper -Check radio-ownership lists fixed netdevice device/driver/module
links and mt76x3_ap/mt76x2_ap holders/refcnt. AST/fixed-target checks passed,
multiline command normalizes CRLF. SSH not run; owner output requested and
pending. Preserve deny-bin refusal; no direct executable bypass. Missing
links/empty holders/refcnt are limited evidence, not safe unload permission.
Continue source/controller integration independently; router untouched.

## Reviewed radio-error candidate bundle — 2026-10-22

prepare-radio-error-candidates.py accepts exact pinned mt76x3 source directory
and a new separate output. Emits ap_mbss.c/ap_mbss_inf.c/rt_linux.c candidates,
three fixtures and manifest with original blob/candidate SHA256. Refuses drift
before output creation and refuses overwriting existing output. Bundle and
three base MinGW injected fixtures passed; refusal cases passed too. Final
manifest rechecks all source bytes. No production hook or device operation.
Next full effective-board driver compile/review and radio lifecycle decision;
partial bundle must not be presented as an installable driver or IoT acceptance.

## Early netdevice name-failure candidate — 2026-10-22

prepare-netdev-create-check emits isolated rt_linux candidate plus actual-function
injected fixture. Strict MinGW passed device allocation/ops/name failures and
successful ownership retention. Name failure frees private ops before device.
Initial fixture vendor-type/device-name errors fixed before successful run.
Sanitizer/MIPS gates added, unexecuted. Candidate not installed in production.
Next verify full driver/effective guards and combine lifecycle repairs before
real controller binding; these fixtures do not prove kernel/RF behavior.

## Failed-init netdev_ops lifetime — 2026-10-22

Pinned Linux free_netdev does not release driver vmalloc ops; normal driver
Detach does, but also unregisters. Extended isolated init candidate with
unregistered-only ops+device cleanup. Strict MinGW actual-init injected tests
passed exactly-once release and preserving successful devices. Production
unchanged. Create's internal name-allocation failure still leaks the same ops
under the inspected source; trace/repair that separately before integration.
Kernel/target/radio acceptance still pending; evidence in activation-gap report.

## Linux MBSS registration failure candidate — 2026-10-22

Extended isolated prepare-mbss-init-check to handle failed Attach after acquired
wdev registration, without normal Linux detach/beacon cleanup. Strict MinGW
actual-function injected cases passed both error classes at BSS 1/2 and success.
MAC_REPEATER RxTrackingInit traced to embedded-only resets in ba_action.c:2165;
no separate dynamic resource there. Production unchanged. Before integration,
verify serialized registry ownership, kernel register failure unwind and
netdev_ops allocation lifetime; fixture substitutes these operations. Sanitizer/
MIPS gates not executed; no device changes. Details in activation-gap evidence.

## Isolated MBSS_Init index failure repair — 2026-10-22

New prepare-mbss-init-check.py emits separate candidate and actual-function
injected fixture. Strict MinGW passed failed registration at BSS 1/2, lower-BSS
preservation, successful creation and one-time guard. Clears freed if_dev and
reduces BssidNum like allocation failure. Production unchanged. Linux sanitizer
and MIPS fixture gates added, not run. Next resolve failed Linux registration
ownership/teardown and auxiliary registry effects before driver integration.
Pinned wdev registry source inspected; no live driver/radio operations.

## MBSS creation error-path investigation — 2026-10-22

Pinned MBSS_Init source confirms dangling if_dev after failed wdev registration
and discarded Linux registration failure; FlgMbssInit still set. Actual helper
returns failure. See activation-gap report for hashes/lines. Do not use the
flag/count as proof of ra2 creation or retry init blindly. Next trace exact
wdev registry ownership and removal before candidate repair. Existing open
wrapper fixture does not cover init; no kernel fault reproduced or driver edit.

## Final observer desired-state drift — 2026-10-22

Candidate active observer now captures four subnet/DHCP fields before planning
and rechecks them and network/firewall gates after observations. Actual helper
composition passed strict MinGW injected mid-observation gate/network/range
drift cases. This does not provide writer serialization or detect changes that
revert before the final read; caller guard remains required. Linux/ioctl/full
RC and real radio binding remain pending. No device/publication operation.

## Active address observer fixture executed — 2026-10-22

Strict MinGW current helper-composition fixture passed, including mismatch and
second-address-read drift refusal. Uses actual prepare-rc helper literal and
quarantine include with injected inventory/DNS/kernel operations and Winsock
compatibility; not full assembled RC, Linux ioctl or target acceptance. Initial
Windows temp access/header/quoting failures preceded successful execution.
Radio lifecycle/controller binding remains the delivery gap; router unchanged.
PowerShell-created fixture removed. Empty Python-created directory
`.iot-address-check-_w_kqoun` remains: Windows denied its verified-path removal.
Do not change ACL/security settings or delete other files to clean it up.

## Active bridge address observation — 2026-10-22

Candidate final policy observer checks exact owned bridge gateway/mask before
and after service/rule reads via wr_iot_bridge_address_matches. Installed
firewall fixture now supplies that dependency and covers mismatch/drift.
Python syntax and scoped whitespace passed; new executable cases, Linux ioctl
faults and target acceptance remain unexecuted. Continue controller/radio
integration; this observer does not implement automatic RF shutdown or IoT
activation. No router mutation, commit, push or firmware build.

## Actual bridge reader fault coverage — 2026-10-22

prepare-bridge-read-check extracts actual four bridge read helpers. Strict
MinGW injected-I/O checks passed alias/directory read-close errors and exact
IPv6 absence/value cases. ABI sanitizer gate added, not run. Host results do
not validate real sysfs/ioctls or RF, and mutation postcheck cases still need
Linux execution. Temporary fixture removed. Continue real controller/radio
integration rather than treating these reader checks as IoT acceptance.

## IPv6 gate checked at BSS open and active observation — 2026-10-22

bridge BSS-UP/active observer recheck ipv6_disabled before/after. Private Linux
fixture includes drift to enabled and restoration; not executed. Observer
failure is not automatic RF shutdown: real controller needs failure handling
and quarantine. Do not infer full IPv6 isolation from sysctl alone.

## Bridge IPv6 disable readback — 2026-10-22

prepare requires exact complete disable_ipv6=1 readback if IPv6 tree exists.
Only ENOENT counts as absent tree; other access/read/close errors refuse success.
Whitespace checked; Linux fault/runtime execution pending. Preserve retained
quarantine/recovery when readback fails after partial bridge preparation.

## Bridge address readback and cleanup ownership — 2026-10-22

prepare now verifies exact SIOCGIFADDR/SIOCGIFNETMASK plus owned DOWN empty
bridge before success. Created-resource cleanup also requires ownership; failed
marker write can leave a retained unverified bridge and must not be silently
adopted or deleted. Controller must report/retain recovery for that case.
Whitespace checked, Linux fault-injection/target still pending. No device action.

## Current controller regression checks executed — 2026-10-22

Current actual composition, activation, radio-state, profile-stream and combined
snapshot/stage/service fixtures passed strict MinGW compile/execution. Includes
disable_ready foreign credentials and profile mutation refusal added recently.
Results use injected operations, not real bridge/driver behavior. Python AST
passed updated namespace/preparation scripts. Recent bridge I/O/readback/retry
cases remain Linux-pending; real radio/controller binding still incomplete.
Temporary fixture removed; no router/build/publication operations.

## Observed idempotent attach — 2026-10-22

Already-attached ra2 is accepted only for owned DOWN bridge, DOWN BSS and sole
membership, with final readback. This avoids blocking a legitimate retry after
partial attach success. Active bridge/foreign members remain refused. Namespace
cases extended but not run; no target/runtime claim. Still requires outer
generation ownership and writer serialization, not just matching names/alias.

## Bridge attach/detach readback — 2026-10-22

Attach verifies owned DOWN bridge, DOWN ra2, master br-iot and sole membership
after mutation. Detach verifies owned bridge, DOWN ra2 and no master; both
reject close errors. Failed postcheck may follow partial mutation: retain
recovery, never assume no action occurred. Linux master-link assertions added,
not executed this turn. Whitespace passed; device unchanged.

## Complete bridge owner read — 2026-10-22

owned() now rejects alias read/close errors and data following the first line.
Linux namespace cases include suffix/multiline alias refusal without deleting
bridge; cases not run here. This tightens the marker check, not an unforgeable
resource-generation identity. Actual lifecycle/RF/controller acceptance remains
open. No device change or workflow execution.

## Bridge directory read failures — 2026-10-22

empty_bridge and bridge_set_up now clear/check errno around readdir and reject
closedir failures. An incomplete membership list cannot authorize removal,
attachment or bridge state change. Source/whitespace checked, new execution
not performed; add targeted I/O failure coverage before acceptance. Existing
host namespace lifecycle does not simulate these read errors. Device untouched.

## Settings ownership before profile removal — 2026-10-22

disable_apply_profile now requires request_disable_ready: current expected
values, three exact closed gates and owned held snapshot. A foreign temporary
credential/value after service commit refuses DAT mutation. Fixture cases
extended, not executed this turn; whitespace passed. Continue integration
without treating the unexecuted cases or administrative DOWN as device proof.

## Profile recheck before service mutation — 2026-10-22

disable_apply_services now calls can_remove again before gate/DNS changes,
including retries. Initial capture does not authorize a changed file later.
Strict MinGW actual-context fixture passed refusal without service invocation
before first apply and after commit. This does not replace a shared lock across
all radio writers or prove real filesystem concurrency. Device untouched.

## Module helper Boolean hazard — 2026-10-22

Pinned common_ex.c smart_unload returns 1 when refcount>0 without removal;
smart_load returns 0 when already loaded. Extracted actual functions verified
with injected callbacks. Legacy refcount/presence readers conflate errors;
stop_wifi_all_rt ignores individual errors and start uses current schedules.
Do not use these as successful fresh-adapter/restoration evidence or rewrite
their shared semantics. Strict observed module/interface generation and 5 GHz
preservation are required for a chosen radio path. No device/module actions.

## Archived device MAC condition — 2026-10-22

Private 2026-10-20 network.txt hash matches existing audit manifest. Main byte3
bit5 is set, recorded guest matches Mode4/two-BSS prediction, and count3 would
differ under that mapping. Keep raw addresses outside Git. This is historical
and conditional, not a current mode/register observation. No new SSH/device
action occurred. Creation/migration choice remains open in EXECUTION-ROLE.

## Third-BSS MAC mask transition — 2026-10-22

Pinned ap.c blob matches local; MT7603 defaults HIF_MT/MBSSID_MODE4=4. Actual
address function diagnostic over selected byte 0..255: main unchanged, guest
changes for bit5-set values (128/256) as count grows 2→3. Hardware registers
were injected; no live MAC/mode claim. Creation path remains unselected in
EXECUTION-ROLE. Verify runtime addresses/mapping and preserve or explicitly
document migration before acceptance. No speculative driver mask patch.

## No-write profile preflight at normal-OFF begin — 2026-10-22

Shared profile-scan validates stream or captured bounded bytes. can_remove
checks current snapshot identity and exact owned third fields before any OFF
mutation. Failed validation cancels read-only settings/profile capture; new
disable_mutated marker prohibits cancellation after any attempted setter.
Strict MinGW list/line/stream/radio-state/context/settings groups passed with
declared injected operations. Scanner is staged and identity checked. Real
Linux/target/RF and full dispatch acceptance remain pending; temporary fixture
removed. Do not equate captured DAT with unverified current NVRAM/radio state.

## Composed normal-OFF context — 2026-10-22

disable-controller composes current radio/settings capture, committed normal
DNS, owned profile removal after bridge teardown, and retryable final release.
Read-only radio capture cancel releases private bytes if settings capture fails.
Partial profile-commit/service-finish retry keeps a receipt and never restores
old profile or repeats commit. Strict MinGW injected-adapter/header checks
passed; RC staging/identity and ABI target gates updated, target not run.
Outer RF QUIESCE, quarantine, bridge actions and final live main/guest/service
observation are still required; live activation dispatch remains unbound.

## Retained current-profile OFF transaction — 2026-10-22

radio-profile-state now supports remove_owned/commit_removed using a fresh
current DAT snapshot. Startup generation/restore cannot be reused once removal
starts. Failed noncommitted removal retries only if old identity still matches;
uncertain write-end blocks retry and retains state. Committed file receipt
requires later outer RF/service observation before release. Actual header
injected-file fixture passed strict MinGW; ABI/staged-header compile gates
extended, target/runtime not run. Device unchanged; temporary fixture removed.

## Owned profile file removal API — 2026-10-22

profile_remove now uses the existing private temporary-file replace path with
reverse stream preflight and original identity check. Nonblocking open rejects
FIFO via regular-file validation. Linux fixture extended for ownership and all
file-operation failures, not run. Windows line/stream tests passed; public C
unit syntax checked with POSIX declaration/flag adapters only (no atomicity or
symlink evidence). Real radio binding and full profile generation ownership
still required. Temporary host fixture removed; device untouched.

## Owned third-BSS profile removal — 2026-10-22

Added profile_disable_stream/line and exact third-list removal. They preserve
current first two DAT entries and unrelated keys, validate owned SSID/PSK and
known third values, require unique full profile keys and preflight before output.
Strict MinGW list/line/stream checks passed. Global RC generator also changes
SKU symlink/key_type, so DAT-only rollback does not cover it. New stream avoids
those calls but still needs atomic replacement and real radio binding. Backend
must reconcile current effective DAT with current NVRAM; no MAC/RF guarantee.

## Actual RC preparation checked — 2026-10-22

Full prepare-rc ran successfully on an isolated copy of local base RC files.
Installed disable adapter compiled with strict MinGW; real Make object probes
passed WR/other/no-board selection. Header/source identity checker now rejects
adapter drift before rewriting its output; that refusal was tested. Installed
MIPS object gate added, not run. Full RC link/radio/runtime acceptance still
pending; scope flags remain false. Temporary source/probe fixture removed.

## Composed normal-OFF service adapter — 2026-10-22

disable-services.{h,c} now compose real settings and DNS APIs: begin captures
current owned state; apply closes gates, prepares/commits normal DNS once;
finish forgets credentials after bridge removal and releases its snapshot.
Keep outer service guard until final OBSERVE. A committed step receipt is not
live health. Strict MinGW actual adapter+snapshot test passed prepare/commit
failure/retry, no repeated commit and premature-finish refusal with injected
DNS/NVRAM/bridge operations. RC staging/object and ABI compile updated, target
not run. Real RF/profile/whole-controller callback binding still absent.

## Owned normal-OFF settings adapter — 2026-10-22

Existing request-snapshot now provides disable_take/close_gates/forget. Take
captures CURRENT values and owned bridge identity under guard; close_gates
requires same bridge and BSS DOWN, before DNS disable; forget runs only after
bridge removal. Startup restore/suspend are refused in disable mode. Finish
requires complete clearing and matching values, then wipes retained secrets.
Strict MinGW fixture passed all gate/credential setter failures, nine foreign
field changes and bridge/UP-BSS refusal. Actual Linux/target pending; real
controller/radio callback binding still required. Temporary fixture removed.

## Normal OFF services precede bridge removal — 2026-10-22

Supersedes the earlier absent-bridge DNS precondition: keep owned br-iot alive
until DISABLE_SERVICES commits normal DNS/DHCP, with BSS closed/quarantined and
gates zero. Otherwise the old DNS baseline may not restart after failure.
DNS ready now requires absent/owned bridge plus new administrative bss_is_down
observer; foreign masters are refused. Strict MinGW model/DNS-flow checks
passed. Linux observer cases extended, not run. Real gate-clear and radio
callbacks remain to bind; DOWN is not RF proof. No device operations.

## Idempotent prepared DNS OFF retry — 2026-10-22

disable_prepare retries its own prepared transaction via activation_ready,
without restarting DNS or replacing baseline. All commit observations are
reused; a startup transaction returns EBUSY. Actual extracted flow passed
strict MinGW tests for seven observation errors and recovery to readiness.
Linux service fixture extended; ABI sanitizer/MIPS core checks added, not run.
Actual filesystem/daemon/radio operations still need Linux/device proof.
Temporary fixture cleaned; no device mutation, build, commit or push.

## DNS normal-OFF transaction API — 2026-10-22

Use dns_disable_prepare/commit for post-ACTIVE service regeneration: exact
closed gates, absent bridge and held outer guard required. Existing service
transaction snapshots CURRENT files/leases before raw generation; disabled
commit rechecks readiness plus no br-iot/wr-iot marker in bounded include graph.
Failed validation retains prepared state; activation_abort can recover this NEW
service baseline, without reopening BSS/bridge. Real controller binding pending.
Host actual preflight/marker helpers passed; Linux config/service tests extended
but not run. Marker detection is conservative and does not prove no custom rules.

## Distinct normal-OFF sequence — 2026-10-22

activation.h now distinguishes startup recovery from normal disable. New
DISABLE_SNAPSHOT is read-only under lock before changes; DISABLE_APPLY uses
current config, OBSERVE proves main/guest/service preservation and IoT absence,
COMMIT releases stop state. Failed normal OFF retains disabling/lock/snapshot
and retries completed-step-aware teardown; no startup RESTORE. Strict MinGW
injected-backend checks passed all stage failure/partial-failure cases and
preserved newer main config. Implement these real callbacks before binding;
Linux/MIPS/device results pending. Temporary fixture removed.

## Normal OFF after DNS commit — 2026-10-22

DNS activation commit releases startup files/lease snapshot and guard;
activation_abort only handles pre-commit rollback. Real normal OFF needs a
fresh current-state transaction removing owned IoT configuration while
preserving newer main/guest/service settings. Do not hold startup guard through
ACTIVE or reuse old global snapshots. Source contract clarified; implementation
and acceptance of normal OFF/recovery remain pending.

## Snapshot suspend/resume ownership — 2026-10-22

request-snapshot retains expected[9] values at suspend. Resume compares them
under service guard and refuses foreign changes without writes; baseline is
retained. Overlong expected capture refuses suspension while keeping guard.
Strict MinGW actual stage/snapshot fixture passed all nine changed-field cases
and existing recovery cases using temporary POSIX declaration/Winsock adapters.
Linux/target pending. Matching values do not detect change-and-revert: generation
and writer coordination remain required. Temporary fixture removed.

## ABI fixture coverage aligned — 2026-10-22

Sparse checkout contains mt76x3 before MBSS candidate generation; tools/iot/**
is an ABI trigger. Both actual status and dispatch cores now have MIPS compile
gates, alongside MBSS variants. Python AST/source-order checks passed, not CI
or YAML/shell validation. No workflow launched. Next substantive dependency is
real radio lifecycle and transaction-bound observer, not another success label.

## Activation transaction identity — 2026-10-22

Strong activation_execute now accepts const wr_iot_control_request*, not just
wr_iot_request*. Retain its ID/time for observation/recovery records; do not
persist credentials solely for status. All source declarations/callers updated.
Actual dispatch-core fixture passed strict MinGW injected-IPC execution for
identity propagation, lock release, failures and no terminal replay. ABI
sanitizer/target fixture checks added, not run. Strong backend/observer remain
unimplemented. Temporary host fixture removed; device and production unchanged.

## Actual secondary close fixture — 2026-10-21

MBSS candidate fixture now extracts the unchanged close wrapper as well.
Strict MinGW checks passed base/MT/HNAT: paired success balances references,
existing main reference remains, and no modeled hardware close occurs while
main stays open. MIPS fixture compile added to ABI, not run. Operations remain
injected, not a complete driver/target or RF test. Temporary fixture removed.

## Isolated MBSS reference repair checked — 2026-10-21

prepare-mbss-open-check.py creates a separate candidate and extracts its wrapper
for checks. It balances RT_MOD_INC_USE_COUNT on VIRTUAL_IF_UP failure without
calling VIRTUAL_IF_DOWN. Strict MinGW execution passed base/MT/HNAT variants.
Linux sanitizer added to ABI, not run. This fixes only module reference balance;
beacon/hardware cleanup needs its own lifecycle proof before production binding.
No production driver input changed. Temporary fixture cleaned after checks.

## Secondary-open failure lifetime hazard — 2026-10-21

MBSS_VirtualIF_Open sets beacon intent/acquires module reference before
VIRTUAL_IF_UP, then returns early on failure without normal cleanup. Pinned
cmm_cfg.c already decrements its virtual count on hardware-open failure: never
add unconditional VIRTUAL_IF_DOWN cleanup. Verify resource validity before
MBSS_CLOSE/beacon cleanup after failed open. Detailed source proof is in the
activation-gap report. This is a real partial-open recovery requirement;
driver/firmware/device behavior was not modified or tested in this audit.

## Beacon initialization preserves prior intent — 2026-10-21

Pinned tx_rx/wdev.c blob c3967f59f470bdaf3afdab8f3eec8fefba12aea7
contains a commented bBcnSntReq reset in wdev_bcn_buf_init. Do not treat repeated
buffer initialization as a silent-BSS reset. Full association/data dispatch
and close/open reset remain to trace before reserved-BSS selection. Contract
and activation-gap report updated with exact source evidence; no driver/device
change, no runtime acceptance. Source findings are progress, not IoT completion.

## Reserved DOWN third-BSS investigation — 2026-10-21

Local mt76x3 source shows secondary beacons gated by bBcnSntReq and probe/
initial-auth rejection for non-RUNNING BSS netdevices. Board template disables
AIRPLAY. Initial reserved DOWN ra2 deserves investigation but is not selected
or safe by assertion. Trace beacon-buffer initialization, complete RX/data
paths, third-entry security defaults and MAC effects before implementation;
verify effective target guards. Current live adapter has no ra2. Exact source
locations and evidence limits are in the activation-gap report. No mutation.

## Actual status-core host execution — 2026-10-21

prepare-status-check.py extracts control-client's real status function for a
portable fixture. Strict MinGW compile/execution passed refusal, record changes,
open/read failures, non-applied states and unlocked observation. ABI workflow
includes sanitizer execution, not run yet. Linux mailbox behavior and real
transaction-bound live observer remain pending; injected results do not prove
them. Temporary local fixture removed after successful execution.

## Status recheck across observation — 2026-10-21

After unlocked APPLIED observation, client rereads the mailbox and checks ID,
state, created and observed timestamps before returning the record. Added a
Linux fixture case that replaces the transaction inside the observer: old ID
must become unknown, new ID remains queued. Not executed on Windows; whitespace
check passed. Live observer and writer serialization remain outstanding; a
successful query is a point-in-time observation, not a future-state guarantee.

## Applied-result observation gate — 2026-10-21

Candidate control-client requires strong wr_iot_activation_result_observed
before returning APPLIED, outside the mailbox lock; only exact 1 succeeds.
Implement a read-only transaction-bound expected-state observer, covering
enabled/disabled requests and serialization with legacy writers. It is absent
deliberately: do not add a weak success stub or treat module presence as proof.
Linux channel fixture extended for refusal/error values and lock release,
not executed here; whitespace check passed. Production remains excluded.

## Legacy radio events and stale ACTIVE risk — 2026-10-21

Base-source restart_wifi_rt performs interface/auth/profile restart, not module
replacement. Watchdog interprets reload_svc_rt as schedule resynchronization
and queues radio/guest controls independently of RC activation. Candidate stop
hooks close IoT gates but do not update controller/mailbox ACTIVE state. Before
production binding, coordinate legacy events with recovery/status invalidation;
preserve user/scheduled OFF intent. Pending transition cases and exact source
locations are in the activation-gap report and IoT implementation contract.
No radio restart or module operation was executed.

## Owner-supplied live module check — 2026-10-21

The owner ran `tools/wr1200js-readonly.ps1 -Check modules` successfully in
ordinary PowerShell. Full lsmod output is preserved in the existing IoT
interface runtime evidence report. mt76x3_ap and mt76x2_ap are loaded, each
with reference count 1; do not interpret those counts as clients or permission
to unload. Owner SSH works; Codex deny-bin remains a separate executor limit.
Continue selective 2.4 GHz lifecycle ownership/rollback source investigation.
No Beamforming/offload verdict follows from this list; no device changes made.

## IoT radio creation dependency — 2026-10-21

Activation now explicitly orders RADIO_PREPARE after quarantine and before
attachment/DHCP. Strict MinGW model checks passed for each mutation, partial
radio opening, retained failed restoration and retry. This is not a real driver
binding. Pinned mt76x3 sources were verified via GitHub blob IDs: MBSS_Init has
the one-time FlgMbssInit guard, and MBSS_Remove does not reset it. Ordinary
profile rewrite/down-up cannot be assumed to grow a live two-BSS adapter.
Next trace fresh-adapter/module ownership/lifecycle or prove a safe inactive
third-BSS reservation before choosing the real creation path. Do not unload
modules on the device or add an unverified restart fallback. Details and hashes:
existing IoT activation-gap report. Production backend/exclusion are unchanged.

## IoT final filter observation — 2026-10-21

The old readiness helper requires BSS DOWN and must remain a mutation guard.
For the activation OBSERVE operation, use the new read-only
`wr_iot_active_filter_observed_current()` path. It checks exact gates/services,
expected installed filters, stable WAN and an owned UP bridge with sole UP ra2
before/after. This is administrative/filter evidence, not RF/NAT/offload proof.
The extracted actual core function passed strict MinGW compile/execution with
injected reads. Linux bridge/netfilter and installed source fixtures were
extended; actual Linux/MIPS/device results remain pending. Continue with the
real radio lifecycle and retained rollback before binding the strong activation
backend. Details: existing IoT activation-gap report. Production remains excluded.

## IoT channel source binding — 2026-10-21

`prepare-control.py` installs the client/mailbox and server/mailbox objects
under the WR1200JS condition and adds exact fixed RC notification dispatch.
HTTP routes/metadata now have the same board guard. Actual GNU Make selection
checks passed for WR1200JS/other/no-board on both installed Makefiles; strict
MinGW installed-dispatch fixtures passed in both board modes. Metadata/Python
checks passed; repeat preparation refused without changing checked RC source.
Linux runtime, installed MIPS compile/link and image/device gates are pending.
Continue with real `wr_iot_activation_execute` startup/rollback/persistence;
the source binding deliberately does not provide that strong backend symbol.
Production exclusion remains. Details: existing IoT HTTP CGI evidence report.

## Private IoT control channel candidate — 2026-10-21

`control-mailbox.c` provides private atomic records and one outstanding request;
`control-client.c` implements submit/status with fixed RC notification;
`control-server.c` claims once and requires strong
`wr_iot_activation_execute`. RUNNING/RECOVERY are retained and never replayed;
terminal cleanup can retry separately. Local strict syntax-only probes passed
with POSIX declarations; actual Linux runtime/MIPS/link results are pending.
ABI fixtures cover ownership, corruption/publication refusal and channel state
with a fake activation backend. Next install/link into candidate HTTPD/RC and
register fixed dispatch, then implement the real guarded activation backend.
Production exclusion remains. See the existing IoT HTTP CGI candidate evidence.

## IoT request records and observed-result CGI — 2026-10-21

Added `control-record.h` (portable bounded secret request record and explicit
ID/freshness-bound result states) plus authenticated `wr_iot_result.cgi` source
candidate. Strict MinGW record, CGI and installed-metadata fixtures passed;
ABI sanitizer/MIPS results are pending. Missing/stale/future/mismatched data
returns unknown; queued/running/recovery never imply applied. Requests contain
credentials: the next private transport must never put records in argv/logs.
Implement private owned request transport, fixed RC dispatch, result storage
and the declared submit/status functions, then real activation/recovery.
Production exclusion remains; evidence is in the existing CGI candidate report.

## Dedicated IoT CGI source candidate — 2026-10-21

`tools/iot/prepare-http.py` now installs exact authenticated token/Apply routes
in a separate source candidate, with safe-session/POST/MIME/CSRF checks and a
bounded one-shot body. It calls the deliberately unimplemented
`wr_iot_rc_submit`; production preparation does not invoke the transformer.
Source extraction and strict MinGW metadata/CGI fixtures passed. Linux sanitizer
and MIPS checks added to ABI are pending. Continue with bounded RC request
ownership and observed-result endpoint, then real activation/recovery. Preserve
the distinction between queue acceptance and applied state. Evidence:
`docs/evidence/WR1200JS-IOT-HTTP-CGI-CANDIDATE-2026-10-21.md`.

## Direct request input into RC staging — 2026-10-21

`wr_iot_request_stage_from(reader, context, modes...)` uses the same guarded
validation/staging code as the retained NVRAM entry point. It permits dedicated
submission to avoid intermediate candidate-key writes. Strict MinGW staging
and snapshot fixtures both passed. Direct input ignores stale candidate keys;
invalid input, missing callback, busy lock and network conflict perform no
writes. Temporary compatibility headers/executables were removed after checks.
Next integrate bounded request ownership between authenticated HTTPD and RC,
then bind real activation/recovery and observed results. This change alone
does not expose an endpoint or activate IoT; production exclusion remains.

## IoT authenticated request boundary — 2026-10-21

`tools/iot/http-request.h` now combines fixed form decoding with authenticated
POST/type checks, server-owned CSRF comparison, and the existing request
validator. Its strict MinGW host fixture passed, including refusal without
changing output for auth/token/method/type/mode/radio/subnet failures. The ABI
workflow now schedules Linux sanitizer execution and MIPS compilation; those
results are pending for this uncommitted change. The temporary Windows header
adapter is verification-only. Production HTTPD registration, serialized RC
submission, observed activation/recovery and real callbacks remain open.
Continue from that integration; keep IoT excluded from the production image.
No commit/push/build or device mutation was performed.

## Actions failure census — 2026-10-21

Reviewed all retained Actions run summaries (960 total) and the job summaries
for failed firmware/build-workflow runs through monitor run `39646683016`
(`#127`, skipped). Latest firmware #514 (`39644862386`, `a6edff8`) passed
selection, build, downloads and ZIP; latest ABI #489 and service runtime #249
also passed. The prior #513 failure was the Privoxy image-checker signature
mismatch, already fixed in `a6edff8`. No new firmware fix is outstanding in
the built revision. Full categories, historical failure clusters, all
firmware run numbers and source evidence:
`docs/evidence/WR1200JS-ACTIONS-FAILURE-CENSUS-2026-10-21.md`.

The latest earlier ABI and service-runtime failures (#458 and #236) were also
followed by successful runs (#489 and #249). Monitor #125 failed at Nim setup
because the runner could not connect to download it; this was not a firmware
failure. The next monitor run #127 was skipped.

Current checkout still contains unrelated uncommitted changes absent from
#514. Preserve them and re-check each changed workflow/code path when the
corresponding changes are included in a future CI run. Nothing was committed,
pushed, cancelled, restarted, or changed on the router during this review.

## IoT dedicated HTTP input candidate — 2026-10-21

`tools/iot/http-form.h` parses only bounded, allowlisted IoT POST fields
without writes and adapts them to `wr_iot_request_read()`. Its host fixture
compiled and passed; executable removed. It is **not** registered in HTTPD or
production firmware. Next bind it to a dedicated authenticated POST route
with CSRF comparison, serialized RC submission and observed result/recovery;
do not use generic Apply success. Evidence:
`docs/evidence/WR1200JS-IOT-HTTP-FORM-CANDIDATE-2026-10-21.md`.

## IoT host fixtures verified and probe folders removed — 2026-10-21

The current `check-request-stage.c` and `check-request-snapshot.c` were both
compiled with strict MinGW flags and executed successfully. The stage check
includes active/malformed service-gate refusal. The controlled probe folder
and both older empty directories have been removed. Older pending-test and
cleanup statements below are superseded. Source/runtime boundary and exact
method: `docs/evidence/WR1200JS-IOT-CANDIDATE-NAMESPACE-2026-10-21.md`.
Next: dedicated authenticated submission/result path and complete serialized
RC activation/rollback. The production image still excludes IoT.

## IoT partial-failure recovery fixture — 2026-10-21

`tools/iot/check-activation.c` now models failures after each startup
mutation. The strict MinGW host compile and execution passed; the temporary
executable was removed. This does not install production RC callbacks or prove
real router recovery. Continue with the dedicated authenticated submission,
serialized RC backend and complete DNS/radio rollback. Evidence:
`docs/evidence/WR1200JS-IOT-ACTIVATION-GAP-2026-10-21.md`.

## IoT request staging guard — 2026-10-21

The candidate stage now refuses active or malformed `wr_iot_profile_t`,
`wr_iot_network_t` and `wr_iot_firewall_t` before any write, including when
`br-iot` is absent. Fixture cases cover each gate at `1` and `stale`; source
syntax and whitespace checks passed, linked execution is still pending in a
Linux-capable executor. No firmware/router inclusion or state change. See
`docs/evidence/WR1200JS-IOT-CANDIDATE-NAMESPACE-2026-10-21.md`.

## IoT Apply control-plane finding — 2026-10-21

Source inspection shows generic `apply.cgi` persists registered fields before
RC activation, while `action_script` can emit `done_committing()` without an
observed IoT result. Build a dedicated authenticated and serialized
submission/result path; registering candidate names in the generic service
table is insufficient. See
`docs/evidence/WR1200JS-IOT-APPLY-CONTROL-PLANE-2026-10-21.md`.
The changed Windows snapshot fixture passed MinGW C syntax checking only;
linked execution remains pending due temporary-directory access denial.

## IoT snapshot fixture portability follow-up — 2026-10-21

The host snapshot fixture now chooses `NUL` on Windows and `/dev/null` on
Linux; production code is untouched. `git diff --check` passed, but a fresh
compile/run did not start because this executor cannot access newly created
probe directories. Two empty directory paths and the removal failure are
recorded in `docs/evidence/WR1200JS-IOT-CANDIDATE-NAMESPACE-2026-10-21.md`.
An authorized executor should clean up those exact paths and rerun the fixture.
Continue with authenticated candidate-form registration and fixed HTTPD/RC
dispatch; do not expose IoT as operational before full activation/rollback.

## IoT candidate request isolation — 2026-10-21 17:50 UTC

`tools/iot/request-stage.c` now maps only `wr_iot_request_*` candidate keys
to the existing validated request parser and temporary stage gates. Two host
fixtures were updated; staging and snapshot checks passed locally with
Windows-only adapters, and temporary files were removed. This is uncommitted
candidate work, excluded from the firmware. The next production dependency is
an authenticated form and fixed HTTPD-to-RC action followed by a complete
activation/rollback controller. Keep IoT OFF and do not expose the page as
functional until source, image and device gates pass. Details:
`docs/evidence/WR1200JS-IOT-CANDIDATE-NAMESPACE-2026-10-21.md`.

## Build #514 passed — 2026-10-21

Firmware #514 (run `39644862386`, commit `a6edff8`) completed successfully:
Privoxy image verification, build job, downloads and ZIP passed. ABI #489 also
passed. The #489–#513 failure chain is summarized with original first causes
and subsequent passing gates in
`docs/evidence/WR1200JS-BUILD514-RECOVERY-2026-10-21.md`.
No router setting or firmware was changed. Continue service/WebUI runtime
acceptance and remaining local work; do not repeat historical CI repairs or
claim device acceptance from #514.

## Firmware failure review and Privoxy correction — 2026-10-21 17:34 UTC

Failed firmware jobs through #513 were grouped by first causal step. Earlier
toolchain, KVR and MT76x3 failures were followed by successful #501–#504.
VPN pruning in #505–#508 is followed by a passing preparation step in
#509–#513; the QEMU DNS failure in #509–#511 is followed by passing DNS in
#512/#513. #512/#513 reach the Privoxy gate and fail its obsolete Apply-call
matcher. Its isolated correction is now commit `a6edff8`, pushed to the
existing PR branch. Python syntax and staged whitespace checks passed, and
the earlier pinned-source in-memory parser fixture passed. A fresh exact
image verdict is pending. Next action: inspect the first run for `a6edff8`,
then address any new first failure from the original job log. Keep unrelated
working-tree files untouched. GitHub started firmware #514 (`39644862386`)
and Band Steering ABI #489 (`39644862372`). ABI #489 subsequently passed;
firmware #514 was still compiling at the latest check. No router state changed.

## CI monitor cadence change — 2026-10-21 17:28 UTC

The owner clarified that "AVI" meant ABI checks and asked to stop the
once-per-minute Codex interruptions. The `padavan-ci` app heartbeat is now
PAUSED. The local `monitor-agent.yml` keeps failure-triggered handling for
firmware, service-runtime and Band Steering ABI workflows, with schedule,
push and manual triggers removed. Its job is gated on a failed conclusion;
GitHub may still show a skipped monitor run after a successful watched run.
The workflow edit is uncommitted and not yet live on GitHub. The app cannot
currently wake this chat solely on a GitHub failure; do not claim automatic
Codex remediation while the heartbeat is paused.

## IoT production activation gap — 2026-10-21

Read-only call-site inspection found no production caller for
`wr_iot_activation_start/stop()` or `wr_iot_request_stage()`; their current
callers are test fixtures. The prepared RC report still marks production
activation false and dnsmasq rollback incomplete, and the main WR1200JS
firmware workflow asserts that the IoT RC sources are absent. No tests/builds
were run and no state was changed. See
`docs/evidence/WR1200JS-IOT-ACTIVATION-GAP-2026-10-21.md`. Next required work is
the authenticated Apply-to-controller binding with complete radio/service
snapshot and rollback; retain default-OFF and image exclusion until end-to-end
gates are implemented. The pinned authenticated Apply/RC control flow has now
been mapped, including the `sys_script` shell fallback hazard and the need to
stage candidate values separately from active NVRAM. See
`docs/evidence/WR1200JS-IOT-APPLY-CONTROL-PLANE-2026-10-21.md`.

## SSH config syntax correction — 2026-10-21

The user-run `wr1200js-readonly.ps1 -Check identity` stopped before connecting
because `~/.ssh/config` line 10 contained both `BatchMode yes` and
`IdentityFile ~/.ssh/id_ed25519` on one line. That malformed line was split
into two directives. The existing `Host github` block and other router options
were preserved and the config was re-read. The user then ran `ssh -G wr1200js`
successfully and the fixed helper returned the WR1200JS Linux 4.4.198 identity
from ordinary Windows PowerShell. User-run read-only SSH is now confirmed; the
managed Codex SSH deny-bin remains active. Evidence:
`docs/evidence/WR1200JS-SSH-USER-RUNTIME-2026-10-21.md`.

## Cross-agent router check procedure — 2026-10-21

All agents/accounts should follow the router-diagnostics rule in `AGENTS.md`:
try only the named read-only helper checks when the current executor permits
them; if SSH is blocked or the owner identity is unavailable, give the owner
the exact command to run in ordinary Windows PowerShell, then record the
verbatim result and provenance. Do not bypass sandbox controls, expose keys,
or say a check passed without output. The owner has confirmed that the fixed
`identity` check succeeds through Windows OpenSSH. Next requested diagnostic:

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File "C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\router-guide-work\tools\wr1200js-readonly.ps1" -Check interfaces
```

This inspects interfaces only; it does not modify router state. The returned
output was received and recorded in
`docs/evidence/WR1200JS-IOT-INTERFACES-RUNTIME-2026-10-21.md`. It does not list
`ra2` or `br-iot`; this confirms no active separate IoT interface/bridge is
shown in this snapshot, not whether the hardware or driver can create one.
Next source task remains the production Apply/controller and rollback path;
keep IoT OFF and excluded until its gates pass.

## Read-only SSH helper — 2026-10-21 17:13 UTC

Added `tools/wr1200js-readonly.ps1`, with fixed target `ASUS@192.168.20.1:22`
and a `ValidateSet` of read-only checks; it disables TTY/forwarding and refuses
to run when the Codex SSH deny-bin is first in PATH. See
`docs/WR1200JS-READONLY-SSH.md` for the ordinary Windows PowerShell invocation.
PowerShell parsing/whitespace checks passed. Running the helper in this managed
executor produced the expected deny-bin error and exit code 1 before launching
SSH; no connection was attempted, and the key file/router route remain
unverified. Do not remove the deny-bin or expose the private key to the agent.
Direct in-agent SSH requires a supported, approved executor permission/process
path; the helper does not grant access to all seven Codex accounts or
Sol/DeepSeek.

## CI monitor and executor boundary — 2026-10-21 17:07 UTC

The existing Padavan CI heartbeat is active at a one-minute interval and is
attached to this Codex thread. It silently checks for new completed failures,
distinguishes firmware/service workflows from the monitor itself, and may make
safe local fixes with focused verification and status updates. Polling can take
about one minute plus startup time; it is not a GitHub event webhook. It does
not grant access to all seven Codex accounts or Sol/DeepSeek and does not
override the one-writer rule. No Codex or Windows sandbox/security settings
were changed; the SSH deny-bin remains effective. Do not bypass it. Device
checks remain blocked until a permitted read-only SSH route is available.
Automation cannot change the router, cancel/restart CI, or commit/push without
the separate permissions described in its instructions.

## Privoxy verifier validation — 2026-10-21 16:59 UTC

The current Privoxy image verifier was exercised against the actual pinned
upstream `web_ex.c` Apply response in memory. Its exact Save/Apply anchor
matched; after simulating the failure-response replacement and shared-Wi-Fi
`&shared` call rewrite, the parser verified ordering, callback, restart clears,
abort and success ordering. No files were created. This narrows the #513
failure to the old gate's source-shape matcher; a fresh full source/ROMFS run
is still required.

## DNS audit boundaries refreshed — 2026-10-21 16:58 UTC

`SERVICE-PORT-AND-SETTINGS-AUDIT.md` now reflects #513: target BusyBox guard
cases, the combined target dnsmasq parser, the Stubby final-ROMFS gate and an
authenticated Stubby DoT QEMU lookup passed. The DoH-specific ROMFS/guard
identity step was skipped after Privoxy failed; #504's earlier DoH package
result does not cover the later listener-guard source. Physical DNS runtime,
preference/failover and persistence remain open.

## Build #513 DNS gate evidence — 2026-10-21 16:57 UTC

Run #513 passed its DNS listener-conflict scenarios, the target dnsmasq
combined DoT/DoH config parse under QEMU, the Stubby lookup check and the exact
target BusyBox audit. It subsequently failed the Privoxy image gate, so DoH
packaging and discovery/KMS checks were skipped; no verified ZIP/image was
produced. Do not generalize the successful DNS checks to live router behavior
or claim DoH packaging. Full log interpretation is recorded in
`docs/evidence/WR1200JS-DNS-LISTENER-CONFLICT-GUARD-2026-10-21.md`.

## Selected-service audit map — 2026-10-21 16:56 UTC

`python tools/check-target-busybox-map.py` passed. Its fixtures cover all 12
active-service maps and reject missing/omitted/failed mappings; all 43 active
WR1200JS `INCLUDE` selectors have an explicit classification. It also checks
Shadowsocks aliases, SFE/QoS exact-image conditions, and WPAD/ZRAM verifier
ordering. This is source-level coverage, not exact-image or device acceptance.
Continue with the next selected-service source/image audit; do not claim a new
image until a workflow actually builds and verifies one.

## Service audit continuation — 2026-10-21 16:53 UTC

- GitHub Actions confirms #513 is still the latest firmware run; it failed
  after compile/QEMU at the Privoxy image gate. The latest overall Actions run
  #125 is an Agent build failure monitor, not a firmware build.
- Locally, `tools/services-nav/check-verifier.py`,
  `tools/check-wr1200js-cpu-watchdog.py`, and an in-memory Privoxy Apply parser
  fixture for the original and shared-Wi-Fi signatures pass. `git diff --check`
  has no whitespace errors (only existing CRLF warnings).
- The active WR1200JS config expects links for Stubby/DoH, WG/AWG, ZeroTier,
  Shadowsocks, Privoxy, WPAD/PAC, access and diagnostics, Cron, KMS and both
  discovery tools. EoIP is disabled by selector and CPU watchdog excluded by
  board policy; confirm the generated navigation in the next exact image.
- No `padavan-4.4/trunk/romfs` exists locally; final image checks cannot run
  until a later firmware workflow includes these changes. Router state is
  unchanged; the executor still blocks SSH before negotiation.
- Next: continue independent service-source audits, arrange permitted
  read-only SSH, and validate the next exact ROMFS/image before treating these
  changes as image-verified.

## Padavan Modern dashboard reference — 2026-10-21 16:40 UTC

The new attachment `Неоновий дашборд роутера Padavan українською.png` is now
recorded in `docs/WEBUI-MODERN-HOME-SCOPE.md` as an additional Padavan Modern
homepage reference. It specifies a Ukrainian neon dashboard with compact
navigation, band/IoT selector, status cards and quick-service tiles. Preview
values must stay marked DEMO; unsupported temperatures should show `Н/Д`, and
tiles must not imply service health or start services. The other page mockups
are reference only, not current implementation approval. Preserve the existing
order: complete and verify IoT, finalize the Modern homepage, then implement
the Modern title page. Padavan Classic stays untouched.

## Current service continuation — 2026-10-21 16:38 UTC

- Workflow #513 (`39632923432`, HEAD `8ff6016`) built firmware successfully,
  then failed the final Privoxy image gate; no verified image was published.
  Its artifact shows the save-failure callback, restart clears and abort were
  present. Only the checker’s exact Apply-call spelling failed after the
  shared-Wi-Fi transform added `&shared`.
- The Privoxy image verifier now accepts the transformed adapter signature
  and preserves strict ordering/abort checks. An in-memory transformed-call
  fixture passes. This correction and the WR1200JS CPU-watchdog change still
  need a later complete image run. Evidence:
  `docs/evidence/WR1200JS-BUILD513-SERVICE-AUDIT.md`.
- A fresh router SSH attempt was intercepted by the managed deny-bin before
  handshake/authentication. Do not refresh the device snapshot; the successful
  16:18 UTC read-only observation remains current evidence. Nothing on the
  router changed.
- Continue service WebUI/BusyBox item 4. Next concrete step: arrange a normal
  permitted SSH path for read-only device checks and ensure the corrected image
  gate runs in the next WR1200JS build. Preserve single-writer ownership and
  the Sol/DeepSeek rules.

## SSH executor check — 2026-10-21 16:39 UTC

Codex Desktop PowerShell executes, but PATH resolves `ssh` first to its
`.sbx-denybin` BAT/CMD wrappers, which return `off\r\nexit /b 1\r\n`. The
Windows OpenSSH binary exists later in PATH and was not run. Neither `ssh -V`
nor `ssh -T` reached the SSH client or network; this confirms a sandbox command
policy interception but says nothing about router reachability or keys. No
security or connection settings were changed. Evidence:
`docs/evidence/WR1200JS-SSH-CODEX-EXECUTOR-BLOCK-2026-10-21.md`.

## CPU watchdog capability finding — 2026-10-21 16:30 UTC

- Added WR1200JS-only removal of the unsupported `watchdog_cpu` enable control,
  inert handling of legacy stored values, factory default off, and exclusion
  from service navigation. The read-only status row is retained for diagnosis.
  Other boards keep the generic source/default behavior.
- Exact anchors were checked against pinned Padavan revision `c25283e`; the
  in-memory source fixture and nav verifier pass. A per-board manifest and
  final-ROMFS gate are added, but CI has not built or checked these changes.
  Physical UI/runtime verification is pending. Details:
  `docs/evidence/WR1200JS-CPU-WATCHDOG-CAPABILITY-2026-10-21.md`.
- Build #513 was already running before this implementation; inspect its
  terminal result, then rely on a later image run for this new gate.

This handoff shares repository context, not Codex chat history, account
credentials, GitHub tokens, or agent identity. The project continues to use one
local checkout and the existing Sol/DeepSeek roles.

Sol and DeepSeek (DeepSeeC) are continuing project participants, separate from
the seven Codex account slots. DeepSeek may return periodically. Keep
`docs/AGENT-HANDOFF-RULES-SOL-DEEPSEEK.md` and the role history in
`docs/EXECUTION-ROLE.md` intact; each returning agent reads them before work.
Do not silently transfer roles or assign simultaneous writers. The one-writer
rule below applies to Codex accounts, Sol, and DeepSeek alike.

## Previous WR1200JS service checkpoint — through 2026-10-21 16:26 UTC

The following snapshots are historical and superseded by the 16:38 update at
the top of this file.

### Managed-executor SSH retry — 16:26 UTC

- TCP port 22 at `192.168.20.1` is reachable from the executor, but its SSH
  command resolves first to a managed deny-bin stub and returns
  `off\r\nexit /b 1`. The installed Windows OpenSSH binary was not called
  directly, so this was not an authenticated SSH attempt. Do not treat the
  prior 16:18 device snapshot as refreshed. No router state changed.
- Firmware run #513 passed its pre-build checks and is still compiling; final
  image gates have not run. Continue source work independently.

### Live refresh — 16:16 UTC

- Firmware build #513 (`39632923432`) is in progress for HEAD `8ff6016`;
  WR1200JS is still compiling and the image gates have not run yet. A separate
  Band Steering ABI workflow is also in progress.
- A fresh read-only SSH attempt to both known router addresses timed out on
  port 22. The previous service observations are not refreshed by this failed
  connection; no command ran on the device and no state changed. See the latest
  attempt appended to the service read-only evidence file.

### SSH retry succeeded — 16:18 UTC

- SSH is available at `192.168.20.1`. Fresh read-only checks show KMS
  enabled/present; LLTD, ASUS discovery and Cron disabled/absent. `watchdog_cpu`
  is set to 1 but `rt_timer_wdg` is absent. `/sbin/watchdog` and the separate
  built-in `/dev/watchdog` path exist; watchdog timer servicing remains
  unverified. Current filtered logs have no matching entries.
- Installed service navigation still has generic Cron/Watchdog/Discovery links
  and no row anchors for those controls. No router state changed. See the
  latest successful check in the evidence file. Build #513 is still compiling.

- Shared checkout branch `codex/wr1200js-service-webui`, HEAD `8ff6016`.
- Firmware run #512 compiled the image and passed the repaired Stubby/QEMU
  combined DNS test, then failed the Privoxy image assertion
  `save_failure_apply_order`. Its diagnostics show the other listed Privoxy
  image checks passing. No verified downloadable image resulted. The verifier
  now emits component-level Apply/save predicates in the report; an available
  local transformation fixture passes all eight, but is not the exact CI tree.
  Use the component report from the next image run to identify the mismatch
  before deciding whether the gate or production behavior is wrong.
- A fresh read-only router inspection connected at `192.168.30.1` using the
  known host-key identity previously used for `192.168.20.1`. KMS is enabled
  and running; LLTD, ASUS discovery, and Cron are disabled/stopped. The
  `/sbin/watchdog` process is present, but its saved UI flag was not established.
  Service navigation on the installed page remains generic; exact installed
  firmware build is unknown (`buildno` empty). Browser authentication failed
  at the alternate address. No router changes were made.
- Evidence: `docs/evidence/WR1200JS-SERVICE-READONLY-CHECK-2026-10-21.md`;
  firmware run `39624109819` and artifact `privoxy-image-checks`.
- Next action: resolve the Privoxy assertion, preserve strict validation of
  save-failure behavior, then rerun the selected image workflow. Continue
  independent item 4 service review; do not wait on builds unless needed.

## Switch accounts safely

1. The current writer stops editing and records its task, branch/HEAD, checks,
   and next action in `PROJECT_STATUS.md` and this file. Do not stage, commit,
   discard, or clean unrelated changes just to hand off.
2. Confirm no other Codex account, Sol, or DeepSeek session is editing this
   checkout. Only one writer is allowed at a time.
3. In Codex Desktop, use its official sign-out control and sign in normally to
   the intended account. Codex Desktop currently has no built-in instant
   multi-account switcher; do not copy session data or tokens. See the official
   [account switching guidance](https://help.openai.com/en/articles/20001068-use-multiple-accounts-with-account-switching).
4. Open the same local folder in Codex Desktop. The installed `codex app`
   command supports a folder path; run the included helper with `-OpenInCodex`
   to launch the desktop app on this checkout. Opening a folder does not import
   another account's chat history. See [Codex Desktop local folders](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex).
5. The next writer reads `AGENTS.md`, `PROJECT_STATUS.md`, this file,
   `docs/AGENT-BOOTSTRAP.md`, `docs/AGENT-HANDOFF-RULES-SOL-DEEPSEEK.md`, and
   the current top block of `docs/EXECUTION-ROLE.md`; then checks Git status.
6. Verify the signed-in account in the app UI, then work only on the recorded
   next task. Never assume GitHub authentication transfers with the folder.

For seven accounts, repeat this same manual sign-out/sign-in process and label
the selected account in the handoff note. OpenAI's account switcher is currently
documented for ChatGPT web and at most two accounts per session; it is not
available in Codex Desktop. The local-folder workflow therefore uses manual
official sign-in, not seven simultaneous accounts.

## One-writer protocol

- Shared checkout: `C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\router-guide-work`
- Do not make seven clones or worktrees.
- Do not allow parallel writes from Codex accounts, Sol, or DeepSeek.
- Do not run `git reset --hard`, `git clean`, force-push, auto-merge, or change
  remotes/Git configuration.
- At handoff, list any long-running commands/builds and identify whether they
  block the next task. A running firmware build does not block independent
  source or documentation work.
- Preserve all pre-existing modifications and untracked files. Review the
  precise target files before edits and never use a broad staging command.
- Never put passwords, OAuth tokens, private keys, browser sessions, or
  credential-store data in these documents or the helper.

## Account validation ledger

No two-account sequential switch has been witnessed yet. Mark an account pair
validated only after the user has manually signed into each account and each
session has opened this exact folder and observed the same branch and working
tree. Do not claim seven accounts were tested unless each was actually checked.

| Account | Signed in and same checkout verified | Date / operator |
|---|---|---|
| 1 | Pending | |
| 2 | Pending | |
| 3 | Pending | |
| 4 | Pending | |
| 5 | Pending | |
| 6 | Pending | |
| 7 | Pending | |

## Current handoff snapshot

- Updated: 2026-10-21
- Current writer: Codex continuing the WR1200JS service audit; existing
  Sol/DeepSeek role assignments are not changed.
- Branch: `codex/wr1200js-service-webui`
- HEAD: `2e73d22` (VPN gate and KMS/ASUS service links pushed 2026-10-21).
- Existing dirty paths: 64 before this handoff setup, 68 after it; recheck with
  the helper. The original 64 paths were preserved.
- Prior read-only helper check on 2026-10-21: 72 changed/untracked paths at
  HEAD `35d70be`; all were preserved. This snapshot predates the current
  continuation and is not the current path count.
- Sol's and DeepSeek/DeepSeeC's rules and role history remain active. DeepSeek
  may join periodically and follows the same one-writer handoff protocol.
- Project next step: continue the approved service-audit sequence at item 4.
- Latest local DNS checkpoint: 17 listener guard cases, Stubby configuration
  fixture, seven shell syntax checks and ten native C-emitter cases passed.
  Stubby ports match WebUI (1024..65535); source/image runner fixes are local.
  Target BusyBox/QEMU, final-image and physical runtime acceptance remain open.
  See `docs/evidence/WR1200JS-DNS-LISTENER-CONFLICT-GUARD-2026-10-21.md`.
- Privoxy save-feedback source fix: failed `mtd_storage.sh save` now uses a
  localized page callback and suppresses the Apply success/restart response.
  In-memory transform integration passed; target compilation, browser
  fault injection and reboot persistence remain open. See
  `docs/evidence/WR1200JS-PRIVOXY-SAVE-FEEDBACK-2026-10-21.md`.
- ZeroTier persistent-state hash now propagates file/sort/hash failures and
  blocks startup until retry. Host shell syntax and three synthetic hash
  cases passed; target/image and device checks remain open. See
  `docs/evidence/WR1200JS-ZEROTIER-PERSISTENCE-HASH-2026-10-21.md`.
  The next image build includes a new exact-image BusyBox/QEMU failure fixture;
  it has not run yet.
- Recent pushed commits include `25ca366`, `029b230`, `e806465`, `63dfd1d`,
  `fe02f7e` and `2e73d22`. Builds #506–#508 failed before compilation on an
  obsolete VPN index-hook expectation; #509–#511 pass that preparation step
  but fail later in the QEMU combined-dnsmasq validation. The pinned target
  dnsmasq seeds from `/dev/urandom`; the checker now supplies a host-CSPRNG-seeded
  temporary guest file and guest-visible config path without changing ROMFS.
  Source syntax and whitespace checks pass, but a target-QEMU rerun is needed
  before treating the fix as verified. Their downloads indexes contain no
  verified image. See
  `docs/evidence/WR1200JS-QEMU-DNSMASQ-SEED-FIX-2026-10-21.md` and
  `PROJECT_STATUS.md`.
- iPerf3 image gate now requires binary/lifecycle/Apply inclusion and ELF
  dependency closure; pushed, but not yet confirmed by a new image. See
  `docs/evidence/WR1200JS-IPERF3-IMAGE-LIFECYCLE-GATE-2026-10-21.md`.
- System service navigation now links selected KMS and ASUS Info Discovery;
  old ROMFS anchors and local fixture checked, new image/browser pending. See
  `docs/evidence/WR1200JS-SERVICE-NAV-SYSTEM-LINKS-2026-10-21.md`.
- Last owner-confirmed successful firmware build: #504. Builds #509–#511 have
  no verified downloadable image; #511 is the latest observed firmware run.
- Read-only SSH later succeeded on 2026-10-21: KMS flag/process agree as
  enabled/running; LLTD and ASUS Info Discovery flags/processes agree as
  disabled/stopped. The live service page still has generic unanchored System
  links and no separate KMS/ASUS links. Build number is empty, so its exact
  image cannot be identified. No router state changed; see the evidence file.
- Commands still running for this account-organization task: none known.
- GitHub collaborator-permission endpoint: connector returned 403; no
  permissions/authentication changed. Details are in `PROJECT_STATUS.md`.
