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

Updated: 2026-10-22 (command shutdown/cancellation gates)

Verified pinned worker/dispatcher/queue source: STOPED blocks enqueue but does
not terminate a CMDHandler already draining; exit frees queued payloads without
an IoT terminal result, and suspended exit skips that cleanup. Added production
contract gates for generation admission, explicit cancellation and retained
lifetime. Existing checked-enqueue candidate already addresses false ACK on
rejection; do not duplicate it. Next integrate cancellation/refcount with
radio lifecycle candidates before installing any transition gate. Evidence:
`docs/evidence/WR1200JS-IOT-ACTIVATION-GAP-2026-10-21.md`.
No router/production mutation, firmware build or executable tests.

Updated: 2026-10-22 (close/command-thread dependency audited)

Pinned source confirms radio close and initialization-failure cleanup join the
command worker through RtmpMgmtTaskExit/RtmpOSTaskKill. Since watchdog reset
can run in that worker, a mutex held across close and awaited by reset risks
a join/lock cycle. Require short nonblocking transition admission and release
before joins/polls; audit queued work/lifetime next. Source evidence and line
references: docs/evidence/WR1200JS-IOT-ACTIVATION-GAP-2026-10-21.md.
No driver/production/router change or build/test in this source audit.

Updated: 2026-10-22 (Sol accepted executor role)

- Owner explicitly assigned Sol; Sol accepted as the sole writer.
- Verified branch `codex/wr1200js-service-webui`, HEAD
  `441138aa8c8b3abf28e0d8eb2401cbac4bb218f8`; tracked tree clean before this note.
- Next independent task: IoT open/close/reset transition ownership and atomic
  main-radio readiness/BSS_UP. Existing #535/device reports were read, not
  revalidated in this role-only step. See `docs/EXECUTION-ROLE.md`.

- Beamforming (2026-10-22): runtime NVRAM shows `wl_txbf=1` (capability) but
  `wl_txbf_en=0` (disabled), `wl_mumimo` unset. "Does not work" is therefore
  explained by it being off, not by a proven hardware fault. Enabling needs
  owner approval plus a BF-capable client test. Factory EEPROM/Config dumps
  are stored privately in `../router-backups/2026-10-22/` with a manifest.

Updated: 2026-10-22 (build 535 green; beamforming controls removed; role handed to Sol)

- Build #535 (`abfd645`) succeeded: `WR1200JS_4.4.198.9-535_e8a8cf98.trx`,
  12 842 033 B, SHA256
  `72d98244bcaed35798bf2ac50a02f2feb3f67e623f0caa9a5932b62f01ffd81d`.
- Final ROMFS has no beamforming controls: `txbf=0`, `row_txbf=0`,
  `mumimo=0`, `row_mumimo=0`; the VPN profile table is intact.
- MU-MIMO removal was added by `abfd645` (board capability policy extended).
- Role handed to Sol in `docs/EXECUTION-ROLE.md`; HEAD `e2c54b1`.
- Device still runs the 2026-10-18 build; flashing #535 needs explicit owner
  approval, then follow `docs/status/WR1200JS-RUNTIME-ACCEPTANCE-PLAN.md`.

Updated: 2026-10-22 (build 519 green; band-steering exit fix verified in CI)

- Firmware build #519 (`a5e01da`) succeeded: TRX 12 842 905 B, SHA256
  `9c79a6b8...b7ba349d`, every uImage structure check true; ROMFS carries the
  VPN profile-table markers and `wr-band-status.js`. Device not flashed.
- CAKE is absent from that image: no `sch_cake.ko` under
  `/lib/modules/4.4.198` (only hfsc/htb/ingress/tbf), and SQM is not selected.
- ABI #504 (`6d1cd45`) succeeded: Wi-Fi lifecycle fixture (including the new
  lost-owner case), live quarantine observation, request staging and firewall
  policy gates all green.
- Band Steering on the device stopped at 18:53:49 on 2026-10-22 and left
  `wr_bs_apply_state=5`. `3587d14` now reports the exit after owner loss;
  supervised re-arm is only a design (`docs/BAND-STEERING-SUPERVISION.md`).
- Device still runs the 2026-10-18 build (uptime >4 days, tunnel healthy,
  steering daemon absent); runtime acceptance of the new fixes is pending.

Updated: 2026-10-22 (IoT main-radio readiness gate and handoff)

- Added candidate operation `WR_IOT_MAIN_RADIO_READY` immediately before
  `WR_IOT_BSS_UP`. Its backend contract must observe the primary 2.4 GHz
  interface UP on the expected adapter and the IoT BSS still DOWN after radio
  preparation. A host fixture confirms missing main-radio readiness aborts and
  rolls back without opening BSS. Strict MinGW fixture passed.
- This observation and the following BSS open are not yet an atomic driver
  transition. Production integration must revalidate readiness under the same
  adapter/BSS transition owner at open time; production callbacks, target driver
  build, image inclusion and router acceptance remain absent/unverified.
- At the owner's direction, role handoff recorded for DeepSeek as next
  executor; this is a repository handoff, not evidence of live acceptance. No router/image
  changes, build, commit or push. Next: establish the adapter-scoped open/close/
  reset transition owner and bind the ready check to BSS open atomically.
  See `docs/evidence/WR1200JS-IOT-ACTIVATION-GAP-2026-10-21.md`.

# Shared project status

Updated: 2026-10-22 (PDMA reset call-path audit)

- Pinned MT7603 source shows periodic timer enqueues command-thread work;
  under selected DMA_RESET_SUPPORT, watchdog reset may reach PDMA through
  gated PSE recovery. Direct PDMA/PSE iwpriv procedures are additional
  reset entries. None owns MBSS open/close transitions. Next trace command
  dependencies before selecting any blocking reset wait. See IoT report.

Updated: 2026-10-22 (IoT dequeue flag writer inventory)

- Radio candidate generator now pins and inventories all three source files
  writing DISABLE_DEQUEUEPACKET; an extra writer stops generation. Thirteen
  merged host fixtures and one negative drift case passed. Manifest still
  marks writer coordination unproven; no production/router change.

Updated: 2026-10-22 (IoT ABI sparse-checkout repair)

- Repaired two missing CI inputs: sparse checkout now includes mt76x3_ap
  Makefile; board selector assertions read tracked WR1200JS overlay config.
  Locally confirmed both selectors and pinned Makefile flags. `git diff
  --check` passed. Edited CI not yet run; full driver remains uncompiled.

Updated: 2026-10-22 (IoT driver transition gate)

- The IoT contract now requires a single per-adapter transition owner,
  first/additional-interface rollback proof, reset/close concurrency,
  exact MIPS driver-object compilation and final-image evidence before
  production installation. The current ABI job checks candidate fragments,
  not an installed full driver. No production/router change.

Updated: 2026-10-22 (virtual-interface rollback source audit)

- Pinned cmm_cfg.c shows VIRTUAL_INF_DOWN calls rt28xx_close when its count
  becomes zero. A naive CR_ENABLE-error rollback could close the radio;
  shared virtual-count ownership and synchronization are not yet proved.
- DISABLE_DEQUEUEPACKET also belongs to radio-off and ATE paths, not only
  reset. Current guards refuse an active disabled state, but do not prove
  atomic IoT opening. Next establish a distinct transition owner/protocol.
  Source evidence is in the IoT activation-gap report; router unchanged.

Updated: 2026-10-22 (CR enable reset guard)

- Pinned isolated secondary CR_ENABLE now refuses an active reset under
  BcnRingLock before touching registers. Focused injected-register fixture
  and thirteen merged strict MinGW host fixtures passed.
- MBSS_OPEN and VIRTUAL_IF_UP still precede CR_ENABLE, whose result the
  wrapper ignores. Full transition/rollback, target compile and RF proof
  remain open; production/router unchanged. See IoT activation-gap report.

Updated: 2026-10-22 (MBSS open reset gate)

- Isolated pinned MBSS_Open now rejects an already active PDMA reset under
  BcnRingLock before changing selected BSS beacon intent. Existing wrapper
  propagates this failure before VIRTUAL_IF_UP. Four focused build variants
  and thirteen merged strict MinGW host fixtures passed.
- Owner-run read-only radio-ownership output shows ra0/ra1/rai0/rai1 as
  virtual netdevices and both mt76x3_ap/mt76x2_ap loaded. The absent
  /sys/class/net/*/device links cannot establish per-interface module
  ownership. Evidence is in the IoT interfaces runtime report.
- Reset beginning after MBSS_Open, ignored CR_ENABLE errors, other reset
  flag writers, target compile and RF acceptance remain open. No production
  or router changes; see IoT activation-gap evidence.

Updated: 2026-10-22 (paired reset/beacon gate candidate)

- Isolated reset path now sets/clears its dequeue-disable flag under
  BcnRingLock; final beacon kickout checks it under the same lock and
  recovery refuses restart while set. Thirteen merged host fixtures passed;
  CI/target build not run, production/router unchanged.
- CR enable during reset and its wrapper error handling remain open, as do
  other owners of the global flag, DMA/RF proof and device acceptance.
  Bundle manifest still marks close exclusion unproven. See IoT report.

Updated: 2026-10-22 (reset/lock source audit)

- Pinned source shows RTMPRingCleanUp(QID_BCN) locks its descriptor/index
  work, while PDMAResetAndRecovery releases that lock between state reset,
  ring cleanup and sync restart. Selected Kbuild does not define
  MULTI_CORE_SUPPORT; inspected default lock macros map to spin_lock_bh.
  Emitted MIPS flags and target behavior remain unverified.
- Next is a cross-section transition protocol and target compilation,
  rather than holding BcnRingLock across the entire reset. See IoT report.

Updated: 2026-10-22 (BSS-sync ARB candidate)

- Both pinned MT BSS-sync `ARB_BCNQCR0` RMW blocks now have isolated
  BcnRingLock sections, merged with CR and recovery candidates. All five
  direct ARB writers are covered in the assembled candidate; twelve host
  fixtures passed. ABI workflow updated locally, not run in CI.
- Effective interrupt/lock context, reset ring cleanup, target build and
  RF/device behavior remain unverified; `bss_close_exclusion_proven=false`.
  Production/router unchanged. See IoT activation-gap evidence.

Updated: 2026-10-22 (isolated first-open rollback candidate)

- New pinned five-file MBSS_ABORT_OPEN candidate clears selected secondary
  beacon intent under BcnRingLock after failed first VIRTUAL_IF_UP, without
  MBSS_Close side effects; wrapper balances module reference. Three rollback
  variants and all eleven merged host fixtures passed. ABI workflow updated
  locally, CI not run. No production/router change.
- This establishes only modeled software-intent cleanup. Partial hardware
  startup, DMA/RF quiescence, target build and device acceptance remain open.
  See IoT activation-gap evidence.

Updated: 2026-10-22 (bounded MBSS_Open candidate)

- Pinned isolated MBSS_Open candidate bounds BssidNum before IdxGet,
  rejects main/invalid BSS and changes secondary beacon intent under
  BcnRingLock. Four standalone MinGW variants and ten merged radio-bundle
  fixtures passed. ABI workflow locally lists the new fixture; CI not run.
- First-radio rt28xx_open failure still needs narrow intent rollback;
  target compilation and device/RF acceptance are outstanding. No
  production/router change. See IoT activation-gap evidence.

Updated: 2026-10-22 (MBSS_OPEN error propagation candidate)

- Isolated pinned wrapper candidate now rejects a failed MBSS_OPEN ioctl
  before VIRTUAL_IF_UP and balances its module reference. Three MinGW host
  variants passed. AP startup consumes the secondary beacon-request flag,
  so failure rollback after rt28xx_open remains a separate unsolved path.
  See the IoT activation-gap report; no production/router change.

Updated: 2026-10-22 (secondary-open failure path narrowed)

- Pinned mt76x3 call flow shows VIRTUAL_IF_UP can fail only during the first
  radio open when `rt28xx_open` fails. The MBSS wrapper sets beacon intent
  first and ignores MBSS_OPEN ioctl status. Existing module-reference fix
  alone does not clear that intent. Source evidence is in the IoT activation
  gap report. No production/router change.
- Next: design a scoped rollback for that first-open failure and verify its
  interaction with beacon initialization before extending the radio bundle.

Updated: 2026-10-22 (secondary CR enable candidate)

- Pinned `mbss_cr_enable` now has an isolated BcnRingLock candidate around
  secondary LPON/ARB register operations. Its MinGW fixture passed with
  register-access-inside-lock assertions and BSS 0 unchanged. This was a
  host test only; production driver and router are untouched.
- Next: review MBSS_Open intent ordering, then BSS-sync and reset writers.
  Do not treat this as completed IoT activation or RF acceptance.

Updated: 2026-10-22 (partial close/recovery critical section)

- Isolated CR disable now clears selected beacon intent and ARB bit under
  BcnRingLock. Recovery flush polls stay unlocked; its final eligibility,
  ARB restart and IDLE assignment are a short locked section. Existing final
  kickout candidate rechecks under that lock. Nine merged MinGW fixtures pass.
- This is incomplete until open/enable, BSS sync and reset writers follow one
  protocol. Effective kernel locking, target compile, queue drain and RF/device
  acceptance are unverified. No production/router change.

Updated: 2026-10-22 (final beacon kickout candidate)

- Isolated MT_MAC kickout candidate now validates BSS index and rechecks
  BeaconTransmitRequired under the existing BcnRingLock immediately before
  HAL_KickOutMgmtTx. Extracted fixture covers a BSS becoming nonrunning on
  lock acquisition, preclosed/missing cases, active submission and balance.
  All nine merged MinGW radio fixtures passed; ABI workflow lists the ninth
  fixture but was not run. Production source and router unchanged.
- Close/open intent and ARB writers still need one shared lock protocol;
  candidate alone does not establish RF quiescence or IoT acceptance.

Updated: 2026-10-22 (beacon transition writer inventory)

- Scoped pinned-source search found five direct ARB_BCNQCR0 writer locations:
  secondary enable/disable, recovery restart and two BSS sync functions.
  Reset calls sync after releasing BcnRingLock. Final beacon kickout already
  holds that lock but does not recheck selected BSS state before submitting.
- A complete transition must coordinate intent, each ARB read/modify/write,
  recovery and final kickout, with long flush polls outside the lock. Pinned
  Kbuild does not define MULTI_CORE_SUPPORT; exact target compiler flags and
  interrupt context still require confirmation. Evidence updated; no driver,
  image or device mutation this turn.

Updated: 2026-10-22 (active MT7603 recovery variant covered)

- Pinned WR1200JS Kbuild selects mt76x3_ap, whose MT7603 branch sets
  DMA_RESET_SUPPORT and TXRXCR_DEBUG_SUPPORT; the separate mt76x3 config.mk
  default does not control it. Recovery fixture now compiles those macros and
  covers main-BSS clock loss, vendor reset branch and diagnostic checkpoint.
  Focused and eight assembled MinGW fixtures passed; ABI workflow gained
  source/config guard, not run on CI. Exact target command/module unverified.
- Shared BSS transition locking, full driver compilation, image and device
  acceptance remain open. No production/router change.

Updated: 2026-10-22 (recovery checks current beacon eligibility)

- Isolated recovery candidate now reuses BeaconTransmitRequired after both
  flushes and before ARB restart. The merged secondary decision rejects a
  closed or nonrunning BSS. Two new injected cases and all eight assembled
  radio fixtures passed MinGW; bundle manifest records close exclusion false.
- This does not serialize a close that begins after the check. Shared
  open/close/recovery/reset ordering, final kickout, target compile and device
  acceptance remain open. No production or router change.

Updated: 2026-10-22 (beacon restart/close lock audit)

- Pinned source confirms CR disable clears ARB_BCNQCR0 before MBSS_Close clears
  bBcnSntReq; the close wrapper ignores both ioctl results. Recovery can set
  the same bit and mark IDLE during this interval. Existing BcnRingLock also
  protects DMA completion and beacon kickout, so whole-function locking would
  nest and encompass flush polls. Other ARB writers in BSS sync/open and PDMA
  reset need a shared transition protocol; a two-function lock is insufficient.
- Exact call sites and limits recorded in the activation-gap evidence. This
  turn inspected pinned source and ran git diff --check; no code, image or
  router changes. Next: design and implement the complete short transition
  protocol, including final kickout and reset ordering, before device testing.

Updated: 2026-10-22 (observed beacon MMIO loss fails closed)

- Recovery candidate now rejects observed HALT/NIC loss and PCI clock-off at
  entry and around direct MMIO reads/writes. A synthetic zero returned during
  observed clock loss cannot progress to restart/IDLE. Existing success kept.
- Extracted function passed clock-off before access, clock loss during first
  poll, NIC loss during second poll and clock loss during final restart read,
  plus prior timeout/success cases. Eight merged radio-bundle MinGW fixtures
  rerun passed; IO/flags are injected, inherited sign-compare warning suppressed
  only for recovery. Existing CI gates cover generator, not run here.
- Before/after checks are not exclusion: transient change-and-revert, effective
  target IO wrappers and DMA_RESET_SUPPORT variant remain unverified. Next
  shared restart/disable/clock-reset lock protocol. No production/device changes.

Updated: 2026-10-22 (close order and MMIO availability evidence)

- Pinned Linux clears/commits netif_running before ndo_stop; it does not exclude
  already-running recovery. BcnRingLock initialization and BH/IRQ macro variants
  traced. Prospective final restart/disable critical section must be short and
  exclude flush polls; caller/writer audit still required before implementation.
- PCI IO macros can synthesize zero reads and skip writes when bPCIclkOff.
  Zero flush status is not hardware receipt without proved MMIO availability.
  Effective target wrapper selection/NIC-clock exclusion remains unproven.
- Evidence records exact ranges; no new locking or runtime claim. Next final
  restart/disable protocol plus truthful device-access failure handling.

Updated: 2026-10-22 (beacon recovery timeout fails closed)

- Pinned APCheckBcnQHandler timeout branches previously break then restart queue
  and mark IDLE. Candidate returns with pretbtt=false on either flush timeout;
  rejects null/index-out-of-range/HALT before access. Successful flow retained.
- Merged function into DMA candidate by exact original function replacement,
  preserving separate checked DMA poll. Eight radio-bundle MinGW fixtures passed.
  Recovery fixture suppresses only inherited vendor signed-comparison warning
  after initial strict compile exposed it; register IO injected. CI gate updated,
  not run. DMA_RESET_SUPPORT variant, real concurrency and RF unverified.
- Next lock/order for successful recovery vs secondary BSS close. This patch
  does not prevent a concurrent close/restart race or prove selective drain.
  Production and router remain unchanged.

Updated: 2026-10-22 (MBSS lifecycle merge integrated into radio candidate bundle)

- New pinned lifecycle assembler merges only reviewed close/CR functions into
  init candidate, rejecting other edits/conflicts. Re-extracts final init,
  close and CR functions into fixtures. Radio-error bundle now uses this merged
  ap_mbss.c and exposes close/CR fixtures without overwriting init repairs.
- Three merged-function and seven integrated radio-bundle strict MinGW tests
  passed (init/close/CR/open/netdev/beacon decision/DMA poll). Underlying hardware,
  allocators and locks injected; no target/full-driver or RF proof. Added
  bundle sanitizer/MIPS gates unexecuted. BSS allocation strategy remains unset.
- Next selective beacon queue drain and serialization; global radio OFF is
  still not an IoT switch. No production/router changes.

Updated: 2026-10-22 (per-BSS register index/count guards)

- Traced CR_DISABLE through AP ioctl to mbss_cr_disable. It clears selected
  timing interrupt bits and selected ARB_BCNQCR0 start bit, without drain poll
  or completion readback; return zero is not RF-stop evidence.
- Added pinned candidate early device/adapter/index/active-count/array-count
  bounds to both CR enable/disable before register IO/neighbor loop. Strict
  MinGW actual-function tests passed invalid/no-IO, non-MT bypass and selected
  queue-bit preservation with other BSS timing retained on disable.
  Register constants/IO injected, not hardware validation. CI gates unexecuted.
- Next combine MBSS init/close/CR candidates without overlapping whole-file
  replacement; then selective beacon queue drain/synchronization. Production
  radio operation remains unbound; no target build/device change.

Updated: 2026-10-22 (selective MBSS close early bounds candidate)

- MBSS_Close originally validates upper array bound after MbssKickOutStas.
  Pinned candidate now rejects null device/adapter, negative, inactive and
  out-of-array index before queue stop/client kick. Valid selected secondary
  beacon intent changes only its slot; existing all-beacon rebuild retained.
- Actual extracted function passed strict MinGW invalid/no-effect and valid
  secondary index 1/2 cases. Initial indentation warning fixed with braces.
  BAND_STEERING branch, hardware drain and RF silence unverified. Added
  sanitizer/MIPS gates unexecuted. Isolated from MBSS init candidate for now;
  these edits to same source file still require a coherent merge.
- Next per-BSS hardware disable/queued beacon ownership and ordering before
  claiming selective IoT stop; adapter-wide OFF remains unbound.

Updated: 2026-10-22 (checked adapter-OFF builder, not IoT toggle)

- Staged wr_iot_prepare_radio_off allocates/initializes a checked synchronous
  no-retry message with eight-byte result and exact four-byte OFF payload.
  It returns caller-owned message and never sends/queues or changes radio flags.
  Strict MinGW extracted builder allocation/payload/initialization test passed;
  added sanitizer/MIPS gates unexecuted. Builder input hash in bundle manifest.
- This is adapter-wide OFF, not per-BSS IoT control. Do not bind it to IoT
  enable/disable or claim main/guest preservation. Selective BSS lifecycle and
  source-level exclusion remain open, along with target/device acceptance.
  Next review per-BSS quiesce/ownership integration rather than expose global OFF.

Updated: 2026-10-22 (coherent queue/MCU candidate assembly)

- Added prepare-radio-queue-candidate.py: stages three pinned preparers, rejects
  overlapping outputs, copies ten driver files plus two labeled fixture assets,
  checks source/tool stability and writes final manifest last with hashes.
  Partial tree explicitly has no production/issuer/radio/target/runtime binding.
- Five strict MinGW fixtures passed against the same merged changes: ACK,
  sender, dispatcher/sender, PCI kickout and actual queue/cleanup composition.
  Initial check miscount and omitted ACK fixture asset corrected; rerun passed.
  Overwrite and source drift refused; original six source blobs preserved.
  These are extracted/injected host tests, not a full driver/real concurrency.
- Added assembly/composition sanitizer/MIPS gates, not run. Next reviewed
  lifecycle/checked MCU issuer binding in coherent candidate, before any live
  enable. Full target driver and recoverable device acceptance remain required.

Updated: 2026-10-22 (actual dispatch/shutdown cleanup slices)

- Composition generator now accepts --cleanup-candidate and extracts actual
  HALT/NIC admission expression plus generic CMDHandler free block and pending
  RTPCICmdThread shutdown free block. Both base and slice compositions passed
  strict MinGW using staged headers; HALT, NIC loss after enqueue and pending
  shutdown cancel result and release queue ref/buffers once.
- Worker operation/scheduling/OS primitives remain injected, not full switch,
  task kill or real threading. Added sanitizer/MIPS slice gates unexecuted.
  Next coherent candidate assembly and reviewed MCU operation/lifecycle binding;
  production activation remains unbound, target/RF acceptance absent.

Updated: 2026-10-22 (actual enqueue composed with result producer/worker)

- Added fixture generator combining actual staged cmm_cmd enqueue body with
  queued-work producer/worker and result cleanup. Strict MinGW passed NIC and
  each allocation failure, stopped queue, no-operation failure, timeout/HALT
  cleanup, caller leaving first, running uncertainty, worker completing before
  enqueue returns. Result and queue-buffer refs/frees checked independently.
- OS allocation/locking/wakeup and worker scheduling are injected; HALT path is
  modeled with actual helper, not full CMDHandler execution. No real threading,
  target or RF evidence. New sanitizer/MIPS composition gates not executed.
- Next compose staged source bundle and compile actual dispatch/shutdown slices;
  review lifecycle exclusion before checked MCU binding. No production changes.

Updated: 2026-10-22 (queued producer and worker staged)

- queued-work.h reserves queue ref before truthful enqueue and releases both
  refs on rejection. Worker starts only queued result, completes once, leaves
  queue ref for unconditional cleanup. Candidate CMDHandler dispatches internal
  tag before legacy switch; NULL radio operation fails closed. No live issuer.
- Strict MinGW staged-header tests passed allocation/enqueue rejection,
  pre-start cancellation, running uncertainty, no-operation failure, normal
  success and worker finishing before producer returns. Actual enqueue is
  injected here, not composed with cmm_cmd.c yet; no whole-driver/concurrency
  proof. Structural checks passed dispatch/switch/unconditional-cleanup order.
- Next compose truthful enqueue implementation with producer/worker and actual
  cleanup paths, then bind reviewed checked MCU issuer only after lifecycle
  exclusion. Candidate remains separate; no target build or router changes.

Updated: 2026-10-22 (actual dispatch/shutdown cleanup hooks staged)

- Added pinned preparer for CMDHandler and RTPCICmdThread: candidate calls
  wr_iot_queue_cleanup before existing generic buffer release on dispatch/skip
  and pending shutdown cleanup. Internal command tag 0x0D73F001 had no matches
  in pinned mt76x3 search. No producer accepts user pointers or queues it yet.
- Envelope cleanup checks internal tag/origin/size, clears result pointer,
  cancels unfinished result and drops queue ref once; no sleeping operation.
  Copied staged headers compiled in strict MinGW result/helper fixture; passed
  unrelated/origin/size bypass, cancellation, duplicate cleanup/ref accounting.
  Structural checks verified both hooks precede generic free. Full functions,
  real kernel locking and target driver are not compiled/tested here.
- Added preparer CI gate, not run. Next producer enqueue/ref-transfer and
  actual worker dispatch with terminal completion; cancellation helper alone
  does not establish adapter lifetime or RF operation. Production untouched.

Updated: 2026-10-22 (shared queued-result candidate)

- Added kernel queued-result header using kref, spinlock and completion, not
  installed/bound. Caller and queue retain separate refs; queued cancellation
  prevents start, running cancellation is UNCERTAIN rather than stopped. First
  terminal result wins; completion occurs outside state lock while ref held.
- Strict MinGW deterministic state/order tests passed allocation failure,
  rejected enqueue ref release, caller-first timeout, queued cancellation,
  running late success rejection, worker-first success/failure and one-time free.
  Kernel primitives injected; no real threading, target compilation or queue
  integration proven. Added sanitizer/MIPS fixture gates, not executed.
- Next hook actual CMDHandler HALT skip and command-thread shutdown cleanup
  before buffer free; retain result ref across accepted envelope ownership.

Updated: 2026-10-22 (truthful checked enqueue candidate)

- Pinned common/cmm_cmd.c RTEnqueueInternalCmd frees a command rejected by
  stopped queue, yet returns success at line 177. Added isolated preparer with
  one shared implementation, legacy wrapper preserving behavior and new internal
  checked wrapper returning actual status. No production files/issuer changed.
- Strict MinGW injected NIC/allocation1/allocation2/queue-reject/success tests
  passed for both wrappers, checking frees, wake and copied buffer ownership.
  Initial fixture failed because pointer-output aliasing in fake allocator;
  corrected fake allocator with memcpy before passing. Target/real concurrency
  untested. Added sanitizer/MIPS gates, not executed.
- Next accepted-command result refcount/cancellation in dispatch skip and
  shutdown paths. Truthful enqueue alone does not solve queued result lifetime.

Updated: 2026-10-22 (watchdog context and queued-cancellation requirements)

- Proved periodic timer enqueues work; watchdog runs through CMDHandler on
  RtmpCmdQTask, not directly in timer callback. Existing thread is a possible
  checked-command serialization point; manual reset still needs exclusion.
- Close stops RX tasklets before command thread; MCU ACK may time out.
  Task-kill failure is log-only, and HALT dispatch skip/thread-exit frees can
  discard queued work without a custom completion. New synchronous work needs
  caller/worker lifetime and cancellation before free, no worker RTNL recursion.
- Exact ranges and design obligations recorded in activation-gap evidence.
  Next implement/review actual queued cancellation/result ownership before
  binding issuer. This is source evidence, not runtime exclusion proof.

Updated: 2026-10-22 (checked no-replay and ioctl serialization trace)

- Candidate checked sender now rejects need_retransmit before queueing.
  Both extracted sender and composed dispatcher/sender passed strict MinGW,
  including retry-enabled request rejected with one private free, no queue/wait.
  Normal command retransmission remains unchanged; no production issuer bound.
- Exact target kernel WEXT dispatch holds RTNL at wext-core.c:988-990;
  SIOCDEVPRIVATE dispatch does so at dev_ioctl.c:555-557. Driver rt28xx_ioctl
  gets adapter then routes to AP ioctl. This narrows process-entry lifetime
  design; it does not serialize asynchronous PDMA recovery. Next trace recovery
  context and normal close under RTNL before adding a separate lifecycle lock.
  No target build, router change or runtime acceptance.

Updated: 2026-10-22 (cleanup callers and lifecycle contract)

- Pinned RX coherent recovery returns early for MT7603 before QID_CTRL cleanup.
  PDMA reset has abort-poll failures that log and continue cleanup/reenable;
  it cannot serve as a successful DMA-stop receipt.
- AndesCtrlPciExit clears flags, kills command tasklet and frees queues/locks
  without a waiter-drain operation in that function. Full-close IRQ/ring order
  is established, but admission exclusion with checked callers remains unproven.
  Evidence has exact source ranges and the required admission/drain contract.
- Candidate manifest now explicitly records missing post-ownership retirement
  and active-waiter exclusion, plus integration prerequisites. No runtime fix
  or target acceptance claimed. Next implement/review admission lifetime across
  exit/reset before binding issuer; never wait holding ACK/ring spinlocks.

Updated: 2026-10-22 (control-ring retirement evidence)

- Pinned RTMPHandleTxRing8DmaDoneInterrupt (cmm_data_pci.c:2602-2658)
  frees/unmaps packets only while TxSwFreeIdx differs from hardware DMA index.
  Extracted actual handler passed local MinGW no-progress, progress, repeat,
  empty-slot and wrap checks with injected registers/locks/free operations.
  Initial strict compile rejected vendor's unused FREE counter; only that
  warning was suppressed, extracted source unchanged. Added CI gates, not run.
- QID_CTRL cleanup (cmm_mac_pci.c:1841-1880) has a separate locked all-slot
  release path. Its call ordering/DMA exclusion is not yet proven for an active
  checked request. MCU false sender branch frees the message, while timeout
  unlinks ACK only when MCU_INIT is set: teardown/waiter lifetime remains open.
  Do not interpret normal DMA completion as post-failure retirement proof.
- Next: trace QID_CTRL cleanup callers and MCU queue cleanup/waiter exclusion
  together before implementing a live issuer. No production/router changes.

Updated: 2026-10-22 (actual PCI packet ownership check)

- Owner-run radio-ownership output is preserved in the runtime interface report:
  virtual ra0/ra1/rai0/rai1, absent ra2, both module refcnt=1. These observations
  do not establish interface/module ownership, unload safety or RF silence.
- Checked candidate now requires the reviewed PCI kickout callback and records
  private ownership before submission, clearing it at ring packet assignment.
  Dispatcher uses that receipt for any nonzero kickout result: a second MCU
  availability failure occurs after ring ownership and must not force-free it.
- Strict MinGW extracted kickout, sender, composed dispatcher/sender and receiver
  fixtures passed. Initial fixture field mismatch and candidate indentation
  corrected before success. DMA/queues/locks/wait are injected; no kernel races
  or target/RF behavior verified. Added sanitizer/MIPS CI gates, not executed.
- Next: prove post-ownership failure/ring retirement and lifecycle exclusion
  before binding a command issuer. Production activation remains unbound;
  no router, Git publication or full firmware build changes.

Updated: 2026-10-22 (actual checked dispatcher/sender composition)

- Extended sender fixture to extract actual dispatcher too. Strict MinGW
  composed functions passed early PCI failure and permission/NIC loss after
  queueing, plus success/timeout/no-response/invalid-state cases. Queue, hardware
  kickout and completion primitives remain injected, not real kernel concurrency.
  Initial fixture alias/indentation compile errors fixed before success.
- Candidate now marks checked permission-rejected messages unsubmitted and
  signals sender for private one-time cleanup. Checked sender rejects non-PCI
  builds/missing kickout callback. Original normal command behavior unchanged.
- Added composed sanitizer/MIPS gates, not run. No live issuer, target compile,
  lifecycle exclusion or IoT/RF acceptance yet; production/router untouched.

Updated: 2026-10-22 (checked MCU sender and early kickout ownership)

- Pinned PCI kickout returns NDIS_STATUS_FAILURE before descriptor/ring packet
  ownership (full ring/null source buffer). Existing dequeue force-frees that
  message even for a synchronous sender, which then continues waiting on it.
  Candidate checked-only path now records unsubmitted failure/completes sender;
  sender force-frees its private packet/message once instead of normal TX-done.
- Checked sender now requires tx_done and an actual terminal response before
  accepting firmware status. Extracted actual sender fixture passed strict
  MinGW response/timeout/no-response/kickout/invalid-state/precondition cases;
  receive fixture rerun passed. Dispatch/queue/wait operations are injected,
  so actual dispatcher integration, ring ownership races and MCU teardown are
  not proven. ABI sanitizer/MIPS gates added, not run. No production/device change.

Updated: 2026-10-22 (isolated checked MCU ACK plumbing)

- Follow-up: first checked response is terminal under ACK lock; duplicate
  success/rejection cannot overwrite it or complete twice. Both duplicate
  orders passed the current extracted-branch MinGW fixture. Real concurrency
  remains untested.

- Added pinned-source candidate preparer for message-owned result fields,
  default-off opt-in, checked sender preconditions/result copy before release,
  and checked-only bounded ACK parse/completion before original lock release.
  Generic callbacks retain original lock context; no command issuer is bound.
- Extracted branch passed strict MinGW injected envelope/payload/sequence and
  generic-bypass cases, asserting completion under modeled lock. Initial include
  anchor mismatch refused safely before output, then corrected. Parser now has
  kernel-compatible include/types. No full driver compile or real concurrency
  verified. Added sanitizer/MIPS fixture gates, not run; production unchanged.
- Lifecycle exclusion, command-message release races and RF/controller binding
  remain mandatory. Source outputs are isolated and manifest explicitly false.

Updated: 2026-10-22 (direct MCU RX route established)

- Read-only pinned git grep/show in existing bare backup proved network RX
  tasklet -> packet parser -> chipOps event -> direct ACK callback, separate
  from command tasklet. Full close kills network tasks before MCU cleanup.
  Exact paths/blobs recorded; active timeout/callback ownership still open.
- Next scoped design is checked-only non-sleeping parse under ACK lock and
  message-owned result, with lifecycle exclusion. Do not move generic response
  hooks under lock or add stack-result callbacks. No transport edit yet.
- Full pinned source objects are locally available in existing bare backup;
  no new clone/checkout/ref mutation occurred. Linux/target runtime still absent.

Updated: 2026-10-22 (MCU callback ownership scope)

- Verified teardown kills command tasklet before queue cleanup; BH handles
  RX before TX-done frees. Also verified direct MT event handler invokes ACK
  dispatch, whose queue lock is released before callback. Same-tasklet-only
  lifetime is therefore not proven without direct RX caller/context trace.
  No reproduced/validated UAF claimed; exact source evidence recorded.
- Candidate manifest now explicitly marks MCU lifetime/RF quiescence/controller
  binding unproven and BSS strategy unselected. Syntax/whitespace checks passed;
  no transport production change, target build or device operation.

Updated: 2026-10-22 (strict radio-result payload parser)

- Added unbound radio-result.h with exact eight-byte/ID 0x05/status-zero
  validation, alignment-independent little-endian byte reads and no receive
  buffer writes. Reserved bytes ignored as unspecified. Payload has no ON/OFF
  echo, so request/sequence binding and callback lifetime remain mandatory.
- Strict MinGW parser checks passed lengths, all command IDs, rejection status
  bytes and unaligned/nonmutating reads. ABI sanitizer/MIPS gates added, not run.
  Not wired to production or presented as firmware/RF acceptance.
- Environment probe: WSL list --verbose returned install usage, exit 1; no
  usable distro established. Docker/MIPS compiler absent from checked PATH;
  inspected base-src lacks kernel Makefile. No installation/security changes.

Updated: 2026-10-22 (owner radio-ownership runtime result received)

- Owner successfully ran fixed check in ordinary PowerShell; full output saved
  in WR1200JS-IOT-INTERFACES-RUNTIME-2026-10-21.md. ra2 absent; ra0/ra1/rai0/rai1
  are virtual netdevices without inspected device/driver/module parent links.
  Both modules exist, refcnt 1, holders listings empty. Parent lookup does not
  establish module ownership and these counts do not authorize safe unload.
- Supersedes pending-output notes above/below. No more rerun request needed
  for this check. Continue source/controller work without changing the router.

Updated: 2026-10-22 (firmware RadioOff response gap)

- Pinned Andes sources show RadioOff returns transport result, while firmware
  status is merely logged. Length mismatch can complete the wait without the
  response handler. Recorded ID/layout/status and exact source evidence; zero
  transport result cannot satisfy QUIESCE. Callback/result lifetime must be
  reviewed before changing this shared transport. No firmware/device change.
- Owner's radio-ownership attempt printed a quoted path only, not executed
  helper/SSH. Reissued complete powershell.exe -File ... -Check radio-ownership
  command; runtime output remains pending. Do not classify this as SSH failure.

Updated: 2026-10-22 (physical radio-off/DMA completion candidate)

- Traced guarded shutdown route to MTPciMlmeRadioOff; existing void DMA poll
  accumulates nonconsecutive idle and logs timeouts without failure status.
  NIC disappearance can leave its poll flag set. Software RADIO_OFF does not
  prove firmware/DMA/RF completion; exact pinned source route recorded.
- Added separate checked DMA-poll candidate, original callers unchanged.
  Strict MinGW extracted-function injected cases passed consecutive idle,
  TX/RX/intermittent busy, disappearance and preowned flag. Initial fixture
  macro/indentation failures fixed. Added candidate bundle/ABI gates, not run.
  No actual register reads, target compilation or device changes occurred.

Updated: 2026-10-22 (beacon recovery excluded from quiescence proof)

- Actual APCheckBcnQHandler source continues after both flush timeouts, restarts
  the BSS queue and marks software IDLE. It cannot be reused as a safe teardown
  drain or success receipt. Normal MBSS close also discards driver ioctl results.
- Recorded exact pinned lines/blob in activation-gap evidence; clarified
  backend QUIESCE contract. Secondary decision guard still lacks synchronization
  with already-running recovery/queued frames. Next trace real physical shutdown
  and completion, keeping RF acceptance open. No runtime fault reproduced.

Updated: 2026-10-22 (closed-secondary beacon decision candidate)

- Rechecked pinned ap.c/ap_connect.c: main startup leaves the secondary beacon
  request flag untouched without AIRPLAY; BeaconTransmitRequired checks that
  flag but not the secondary netdevice state. Prepared isolated guard requiring
  present RUNNING secondary interface, preserving original main/WDS decisions.
- Actual extracted decision function passed strict MinGW base/WDS cases for
  absent/down secondary, stale true flag, active secondary and original main/
  WDS exception. This is a source decision test, not hardware queue drain or RF
  silence. Production unchanged. Added candidate to partial bundle and ABI
  sanitizer/MIPS gates; extended bundle/full target gates not run here.

Updated: 2026-10-22 (fixed radio-ownership device evidence request)

- Added read-only helper check radio-ownership: fixed five netdevice sysfs
  paths and fixed two module holders/refcnt paths. No module/interface writes.
  Normalizes multiline CRLF to POSIX LF before SSH. Existing deny-bin and
  identity/endpoint protections retained. PowerShell AST/fixed-target checks
  passed; remote shell/SSH execution not performed by this executor.
- Asked owner for ordinary-PowerShell output to investigate actual device/
  driver association before radio lifecycle selection. Output pending; do not
  infer unload safety from empty holders/low refcnt or absent device symlink.
  Source/controller work can continue independently while waiting.

Updated: 2026-10-22 (reviewed radio-error candidate bundle)

- Added prepare-radio-error-candidates.py to assemble three candidate files
  outside the driver source, with original git-blob identities and candidate
  SHA256 manifest. Checks all pinned input bytes before creating output;
  refuses existing output or source-contained destination. No production hook.
- Local bundle preparation and three base strict-MinGW fixtures passed, along
  with output-overwrite/source-drift refusal before output creation. A fixture
  copy's extra trailing newline initially triggered the expected identity
  refusal; exact pinned bytes then passed. Source remains unchanged.
- Bundle is partial source, not a driver/firmware package. Full effective-board
  compilation, radio creation/silence/MAC preservation and controller binding
  remain open; kernel/RF behavior is not established by injected fixtures.

Updated: 2026-10-22 (early netdevice name-failure candidate)

- Added isolated prepare-netdev-create-check.py for actual RtmpOSNetDevCreate:
  failed name allocation now frees/clears its private ops before device free.
  Strict MinGW injected allocation/ops/name failure and success tests passed.
  Fixture's initial missing vendor types and device declaration were corrected
  before success; IN annotation marks intentionally unused vendor arguments.
- Added Linux sanitizer/MIPS fixture gates, not run. No production installer
  invokes this candidate. Full-driver compile, effective guards, kernel/RF
  lifecycle and binding to activation remain pending; router unchanged.

Updated: 2026-10-22 (failed-init private netdev_ops lifetime)

- Inspected pinned target Linux register/free paths and driver Detach. Kernel
  free_netdev does not free the driver's vmalloc netdev_ops; normal Detach does.
  Earlier isolated candidate leaked ops on both registration-failure branches.
- Candidate now releases private ops without normal Detach, then frees device.
  Strict MinGW injected checks passed single release and lower-BSS retention.
  Production unchanged. Earlier Create name-failure cleanup is still separate;
  real kernel callbacks/target/radio/controller acceptance remain pending.

Updated: 2026-10-22 (Linux MBSS registration failure candidate)

- Traced MAC_REPEATER RxTrackingInit to pinned ba_action.c:2165: embedded-field
  resets only, no allocation/timer/hardware operations. Board template enables
  repeater, so this source check matters to failed registry cleanup.
- Isolated init candidate now handles failed Linux Attach: removes acquired
  wdev slot, clears pointer/count and frees unregistered device, preserving
  lower BSS. Strict MinGW injected actual-function cases passed indices 1/2
  for both failure classes and success. Production driver unchanged.
- Serialized registry ownership, real registration unwind/netdev_ops lifetime,
  other effective guards and kernel/radio acceptance remain pending. See
  activation-gap report; no firmware build/device/publication operation.

Updated: 2026-10-22 (isolated MBSS_Init index failure repair)

- Traced actual wdev registry: failed full-list insertion returns -1 without
  acquiring a slot; success inserts the wdev, and unregister removes it under
  irq_lock (pinned wdev.c blob c3967f59f470bdaf3afdab8f3eec8fefba12aea7).
- Added prepare-mbss-init-check.py: separate candidate clears freed if_dev and
  truncates BssidNum on failed index registration, preserving prior BSS.
  Strict MinGW actual-function injected checks passed failures at indices 1/2,
  success and one-time retry refusal. No production patch installed.
- Added Linux sanitizer/MIPS fixture gates, not executed. Registry auxiliary
  MAC_REPEATER effects, Linux-registration failure, beacon lifetime and target
  integration still require work; fixture does not prove those paths.

Updated: 2026-10-22 (MBSS creation failure source trace)

- Pinned driver MBSS_Init leaves a freed wdev->if_dev on failed wdev-index
  registration, ignores Linux netdevice registration failure, then sets its
  one-time initialized flag. Actual RtmpOSNetDevAttach returns failure; the
  caller discards it. Evidence and exact blobs/lines recorded in activation
  gap report. This is source evidence, not a reproduced on-device fault.
- Controller creation proof must observe actual registered identity/ownership;
  retrying MBSS_Init alone cannot recover. Next trace wdev registry cleanup
  before implementing error-path repair. No driver/router mutation.

Updated: 2026-10-22 (final observer desired-state drift refusal)

- Final candidate policy observation captures gateway/mask/DHCP range before
  planning and rechecks all four values and both permission gates after live
  service/rule/address reads. A changed desired configuration cannot inherit
  the earlier successful observation. Caller must still serialize writers;
  change-and-revert is not detected and no atomic NVRAM snapshot is claimed.
- Strict MinGW helper-composition checks passed firewall gate, network gate
  and DHCP-end drift during rule observation, plus prior cases. Uses injected
  kernel/DNS/inventory operations and Winsock compatibility, not installed full
  RC/Linux/radio acceptance. Radio/controller binding still missing.

Updated: 2026-10-22 (active address observer fixture executed)

- Strict MinGW compile/execution passed the current candidate firewall helper
  composition, including address mismatch and second-read drift refusal.
  Fixture used actual helper literal plus quarantine include, Winsock address
  compatibility and injected inventory/DNS/kernel operations. This was not a
  full prepare-rc assembled tree or Linux ioctl/target test.
- Initial Python temporary-directory attempt hit Windows access denial;
  PowerShell-created fixture worked. Linux-header dependency and command
  quoting failures were resolved before the successful run. No device action.
- Working fixture removed; empty `.iot-address-check-_w_kqoun` remains because
  Windows denied removal. No ACL/security changes attempted.

Updated: 2026-10-22 (active bridge address observation)

- Candidate active-policy observation now checks the owned bridge's exact
  IPv4 gateway and mask before and after service/rule observation. Socket,
  ioctl and close errors refuse success. This closes an address-drift gap in
  the observer; it does not bind the still-missing live radio controller.
- Updated the installed-firewall fixture for address mismatch and mid-check
  drift. Python syntax and scoped whitespace checks passed; these new runtime
  cases and Linux/target checks have not run. Router untouched; no publication.

Updated: 2026-10-22 (actual bridge reader fault cases executed)

- Extracted actual owned/empty/sole-member/IPv6 readers into injected-I/O
  fixture. Strict MinGW compilation/execution passed read/close failures,
  trailing alias data, foreign/missing membership and IPv6 absent/error/value
  cases. Initial fixture macro collision fixed before successful run.
- Added ABI sanitizer execution, not run. This closes host fault-path coverage
  only; real sysfs/ioctl/namespace and target/radio acceptance remain pending.
  Temporary fixture removed; no device/build/publication operation.

Updated: 2026-10-22 (live bridge IPv6 gate observation)

- BSS-UP and active administrative observer now require verified IPv6-disabled
  bridge both before and after their operation/reads. A later IPv6 gate change
  cannot inherit the initial bridge-preparation success.
- Added private Linux namespace gate-drift/refusal/restoration cases, not run.
  Does not automatically close an already-open radio or prove packet isolation;
  outer runtime controller must handle failed observation. Whitespace passed.

Updated: 2026-10-22 (bridge IPv6 disable readback)

- Bridge prepare now reads back exact disable_ipv6=1 with complete successful
  read/close before success. Missing IPv6 sysctl tree is accepted only for
  ENOENT; permissions/other lookup failures cannot masquerade as IPv6 absence.
- Whitespace checked; Linux/sysctl failure injection and target runtime remain
  pending. This does not prove packet isolation or vendor-radio quiescence.
  No device change or firmware build occurred.

Updated: 2026-10-22 (bridge address readback and owned cleanup)

- Bridge prepare now rechecks owner, DOWN/empty topology and exact IPv4
  address/mask after setters before returning success. Failed preparation
  cleanup requires current ownership; an uncertain owner-marker write retains
  the resource rather than deleting an unverified object.
- Source whitespace check passed. Existing namespace test checks address/mask;
  injected setter/readback/owner-write failures still lack runtime coverage.
  No Linux/target/device success claimed; router untouched.

Updated: 2026-10-22 (current controller regression checks executed)

- Strict MinGW compile/execution passed current composition, activation,
  radio-removal, profile-stream and combined settings/stage/service fixtures.
  This includes previously unexecuted disable_ready foreign-value/profile-step
  refusal cases. Injected adapters remain explicitly scoped; settings fixture
  used declaration/Winsock compatibility headers only.
- Python AST passed updated bridge namespace/source-preparation scripts.
  Recent bridge owner/membership I/O and attach readback/retry changes still
  lack Linux execution. No target/driver/device acceptance follows. Temporary
  fixture removed; no build, commit, push or device state change.

Updated: 2026-10-22 (observed attach retry)

- Attach now accepts an already attached ra2 only when owned bridge and BSS
  are DOWN and ra2 is the sole member, then repeats final ownership/topology
  observation. This supports retry after successful ioctl but failed readback
  without a second membership mutation. Foreign/active topology is refused.
- Added Linux namespace retry/extra-member/active-bridge cases and repeated
  detach case, not executed this turn. Whitespace check passed. No device action.

Updated: 2026-10-22 (bridge membership mutation readback)

- Attach now rechecks owned DOWN bridge, DOWN ra2, correct master and sole
  membership after ioctl. Detach rechecks ownership, DOWN ra2 and no master;
  close errors refuse success. A successful syscall alone no longer advances
  these operations. Partial mutation still requires retained controller recovery.
- Linux namespace assertions now explicitly inspect master after both actions;
  not executed here. Whitespace check passed. Target/RF/runtime unverified.

Updated: 2026-10-22 (complete bridge ownership receipt)

- Bridge owner read now requires EOF after the single alias line and successful
  read/close. Trailing data, truncated aliases and I/O failure cannot authorize
  bridge mutations. Extended isolated Linux cases for suffix/multiline aliases;
  not executed here. Source whitespace check passed; no device operation.

Updated: 2026-10-22 (bridge membership I/O errors refuse mutation)

- Found empty_bridge and bridge_set_up ignored readdir/closedir failures,
  unlike the active observer. Both now reject incomplete/error membership
  observations before bridge creation cleanup/removal/attachment/state change.
- Whitespace check passed; no new test execution in this turn. Existing
  namespace cases do not inject directory I/O errors, so failure-path runtime
  proof remains pending. No device or firmware changes.

Updated: 2026-10-22 (settings ownership before profile removal)

- Added read-only disable_ready checking held snapshot guard, closed gates and
  all current expected temporary values. Profile removal now requires that
  observation before changing DAT, refusing foreign settings after DNS commit.
- Extended composition/settings fixtures for refusal on changed credentials;
  these new cases were not executed this turn. Whitespace check passed.
  Real radio/controller integration and Linux/target acceptance remain open.

Updated: 2026-10-22 (profile recheck before service mutation)

- Normal-OFF service adapter now revalidates the captured current profile
  immediately before gate/service changes, including service retries. A changed
  profile refuses the step without calling service apply or discarding state.
- Strict MinGW actual composition fixture passed changed-profile refusal both
  before initial service apply and after service commit. Adapters injected;
  real concurrent writer serialization and Linux/target execution remain open.

Updated: 2026-10-22 (legacy module helper lifecycle semantics)

- Pinned common_ex.c confirms smart_unload returns 1 for busy/no command,
  while smart_load returns 0 for already loaded. Actual extracted helper
  diagnostics passed under strict MinGW with injected callbacks. Refcount and
  presence helpers also conflate malformed/unreadable/missing cases.
- Radio lifecycle contract now requires strict module/interface observations
  and exact main/guest/5 GHz preservation; void Wi-Fi wrappers are not proof.
  No shared return semantics or router modules were changed. Creation path
  remains open; source evidence saved in activation-gap report.

Updated: 2026-10-22 (MAC transition checked against archived device data)

- Verified private 2026-10-20 network.txt SHA256 against audit manifest. Derived
  booleans only: recorded main byte3 bit5 is set, Mode4/two-BSS guest prediction
  matches recorded ra1, and three-BSS prediction differs for that main address.
- Historical evidence strengthens the guest-MAC migration concern but is not a
  current runtime-mode/register reading. Raw addresses remain private. Creation
  path still requires mapping/preservation or explicit migration evidence;
  no device access, source activation or configuration change occurred.

Updated: 2026-10-22 (third-BSS MAC mask transition confirmed in source)

- Pinned MT7603 defaults HIF_MT/MBSSID_MODE4. Verified ap.c blob matches local
  reference and extracted its actual address function. Strict MinGW diagnostic
  over 256 selected-byte values found main unchanged but guest changed in 128
  cases when count grows 2→3 (bit 5 condition). Register operations injected.
- This is not the router's runtime mode/MAC result. Contract and executor
  decision record now require address/mapping preservation or explicit migration
  evidence before choosing radio creation path. No driver/device mutation.

Updated: 2026-10-22 (profile ownership preflight before OFF mutations)

- Normal-OFF begin now validates captured current DAT against owned SSID/PSK,
  full required-key uniqueness and exact third-list values before service/gate
  changes. Shared scanner serves streams and captured bytes; no temporary file
  is needed for this read-only preflight. Failed preflight cancels read-only
  settings/profile captures; cancellation is refused after attempted setters.
- Six strict MinGW fixture groups passed, covering buffer/stream consistency,
  NUL/duplicate/ownership refusal, cancellation and existing partial failures.
  Source staging/identity includes new scanner. Linux/target/radio binding still
  pending; no firmware or device changes.

Updated: 2026-10-22 (composed settings/services/profile OFF context)

- Added disable-controller context composing fresh current profile and settings
  snapshots, services-before-bridge teardown, owned profile removal and staged
  final release. Read-only capture can cancel without writes; a partial final
  release receipt prevents repeating profile commit on service-cleanup retry.
- Strict MinGW actual composition and profile-header tests passed with injected
  adapters/file operations. Initial fixture indentation warnings fixed before
  successful execution. RC object/header staging and identity/MIPS gates updated,
  not run on target. RF quiescence/final main/guest observation and live dispatch
  remain unbound; no production/runtime completion claimed.

Updated: 2026-10-22 (retained current-profile OFF transaction)

- Added owned removal and commit to radio-profile state. Uses a NEW current
  file snapshot, never restores IoT startup baseline. A failed uncommitted
  removal retries only if pre-attempt identity still matches; uncertain capture
  retains the snapshot and blocks replay. Successful removal is not repeated.
- Actual header flow passed strict MinGW injected-file tests for ownership,
  retry, no duplicate removal, guard loss and no old-profile restoration.
  Staged-header probe and ABI sanitizer/MIPS fixture gates extended, not run.
  Radio quiescence/application and full controller binding remain pending.

Updated: 2026-10-22 (owned profile removal file API)

- Added public profile_remove through the existing temporary-file replacement
  path, reusing complete reverse-stream preflight, fsync and original identity
  check before rename. Input open is now nonblocking before regular-file check.
- Linux file fixture extended for ownership/create/sync/close/rename failures
  and FIFO refusal; not executed here. Strict MinGW line/stream checks passed;
  profile.c syntax passed with explicit POSIX declaration/flag adapters only.
  This is not Linux atomicity/symlink proof. RC manifest records API installation;
  real radio/controller binding and target/device checks still pending.

Updated: 2026-10-22 (owned third-BSS profile removal stream)

- Source audit found global 2.4 GHz generator also replaces SKU symlink and may
  mutate key_type NVRAM, outside the DAT-only snapshot. Added a separate reverse
  stream transform removing only exact owned third-BSS fields from current DAT,
  preserving current first two entries and unrelated radio/QoS bytes.
- Strict MinGW list/line/stream tests passed exact roundtrip, newer main SSID
  preservation, credential ownership and malformed-list/bounds refusal before
  output. Atomic file replacement/radio application not bound yet; effective DAT
  is not proof of current NVRAM or runtime. No device or production change.

Updated: 2026-10-22 (actual prepared RC disable adapter verified)

- Ran full prepare-rc.py on a separate fresh copy of local base RC sources.
  Installed adapter/header mapping and manifest flags matched; installed adapter
  object compiled under strict MinGW. Actual GNU Make selected its object for
  WR1200JS only, excluding other/no-board modes.
- Extended staged-header checker for adapter/header identity and candidate scope.
  Source drift was rejected without overwriting the existing generated probe.
  Added installed-object MIPS gate, not run. No full RC link/target/runtime proof,
  and real controller/radio binding remains false. Temporary fixture removed.

Updated: 2026-10-22 (composed normal-OFF service adapter)

- Added disable-services adapter composing existing current snapshot/gate
  closure with DNS OFF prepare/commit and post-bridge credential cleanup.
  Failed prepare/commit retains settings/guard; recorded commit is not repeated.
  Snapshot finish cannot run before successful service commit and bridge removal.
- Actual snapshot/stage/adapter compiled and ran under strict MinGW, with
  injected DNS/NVRAM/bridge callbacks. Prepare/commit retry and no premature
  cleanup cases passed. Candidate RC source/object staging and ABI compile
  commands updated, not run on target. Full controller/radio binding remains
  false; this is no production/runtime acceptance. No device operations.

Updated: 2026-10-22 (owned normal-OFF temporary settings)

- Added normal-OFF mode to the existing request snapshot adapter: captures
  current bounded values/owned bridge index, closes only three temporary gates
  after BSS DOWN, and forgets credentials/ranges only after bridge removal.
  It refuses startup restore/suspend and retains state on writes/readback errors.
- Strict MinGW actual stage/snapshot execution passed three gate failures, six
  credential failures, all nine foreign-value refusals, replaced bridge/UP-BSS
  refusal and prior snapshot cases. Host NVRAM/bridge reads injected; Linux/
  target/device pending. No persistent config or device state was changed.

Updated: 2026-10-22 (retain bridge until normal-OFF services commit)

- Corrected normal-OFF ordering: DISABLE_SERVICES now runs under quarantine
  with BSS closed while the owned bridge remains, allowing current DNS baseline
  recovery on failure. Only then tear down bridge/profile. DNS preflight now
  permits absent/owned bridge but requires administrative BSS DOWN/absent.
- Strict MinGW activation and actual DNS-flow fixtures passed, including
  service-stage failure retaining bridge, foreign bridge and UP-BSS refusal.
  Added read-only bridge DOWN observer and Linux cases, not executed here.
  Real gate-clear/radio/service callback binding remains unimplemented.

Updated: 2026-10-22 (DNS disable retry reuses prepared transaction)

- Refactored final service readiness from commit into a read-only helper.
  Repeated disable_prepare now re-observes its own prepared OFF transaction
  without stopping/regenerating service or replacing its current baseline.
  Prepared startup transactions are not adopted by normal OFF.
- Actual extracted prepare/readiness/commit flow passed strict MinGW checks
  for seven observation failures, retry, no regeneration and guarded refusal.
  Initial fixture naming collision was fixed before successful compile/run.
  Real Linux fixture extended; sanitizer/MIPS core gates added but not run.
  Real radio/controller binding and physical acceptance remain incomplete.

Updated: 2026-10-22 (normal-OFF DNS transaction API)

- Added DNS disable prepare/commit using a fresh current service transaction.
  Requires held service guard, exact closed gates and absent br-iot. Commit
  also refuses generated IoT markers across bounded includes; failed validation
  retains prepared recovery rather than announcing success.
- Actual preflight/quote-decoded marker helpers passed strict MinGW execution.
  Extended Linux config and service fixtures for include markers and disable
  commit refusal/retry; not executed here. Preparation manifest records candidate
  API, not completion. Real disable callback/radio binding still absent.

Updated: 2026-10-22 (normal OFF sequencing separated from startup rollback)

- Activation model now takes a fresh read-only DISABLE_SNAPSHOT before normal
  OFF and uses separate APPLY/OBSERVE/COMMIT operations. Startup RESTORE is
  never invoked by normal OFF. Partial stop failures retain lock/snapshot and
  retry teardown without reopening IoT or replaying the old startup baseline.
- Strict MinGW execution passed every stop stage before/after partial mutation,
  lock/snapshot refusal, preserved newer modeled main config, plus prior startup
  rollback cases. Actual callbacks are still unbound: this is sequence evidence,
  not real DNS/radio disable or router acceptance. Existing ABI model gates cover
  the changed source when run. No build/commit/push/device mutation occurred.

Updated: 2026-10-22 (post-commit OFF differs from startup rollback)

- Traced DNS activation commit through service-state/transaction finish: it
  releases original files/leases and its guard. Startup abort is unavailable
  afterward. A real normal-OFF path must create a fresh guarded transaction
  against current settings rather than reuse startup abort or old global files.
- Clarified this distinction in DNS API and IoT contract; recorded source proof
  in activation-gap report. Do not retain startup guard indefinitely in ACTIVE.
  This is an integration requirement still unimplemented, not a runtime result.

Updated: 2026-10-22 (temporary snapshot resume preserves foreign values)

- Snapshot suspend now captures expected current values for all nine temporary
  fields. Resume reacquires guard and refuses any mismatch before restoration,
  keeping baseline intact and making no writes. Oversized capture retains the
  existing guard and refuses suspension.
- Actual snapshot/stage fixture compiled and executed under strict MinGW with
  temporary net/if declarations and Winsock inet adapter: all nine changed-field
  cases plus existing rollback cases passed. Linux/target execution pending.
  Current-value matching cannot detect change-and-revert; all writer generation
  coordination still needed. No router change or production integration.

Updated: 2026-10-22 (candidate ABI coverage alignment)

- Checked pinned sparse checkout includes mt76x3 sources before candidate
  generation; tools/iot changes trigger ABI. Added missing status-core MIPS
  fixture compilation alongside dispatch; normalized shell-block indentation.
- Python AST and targeted workflow source/order checks passed. These do not
  constitute YAML/shell validation, MIPS execution, full driver compilation or
  a CI run. No workflow dispatched. Real radio lifecycle/backend/observer and
  full device acceptance still required before IoT production integration.

Updated: 2026-10-22 (activation receives transaction identity)

- Found that activation previously received only request settings, losing the
  claimed ID/time needed for transaction-bound observation/recovery. Changed
  the strong backend interface to accept the complete claimed envelope and
  updated dispatch/channel fixture consistently.
- Actual extracted dispatch compiled/executed under strict MinGW: ID/time and
  settings reach the backend, queue lock is released, uncertain outcomes retain
  recovery, open failures and terminal cleanup do not replay execution.
  IPC/backend injected. ABI sanitizer/MIPS checks added, not run. Real backend
  and observer remain absent; no router change, build, commit or push.

Updated: 2026-10-21 (secondary close and main-reference preservation)

- Extended isolated MBSS fixture with the actual original close wrapper.
  Strict MinGW execution passed base/MT/HNAT cases: successful open/close
  balances references; closing a secondary retains an existing main-interface
  reference and does not trigger its modeled hardware close.
- Added MIPS compilation of the extracted wrapper fixtures to ABI workflow;
  not executed here. This is not full driver compilation or RF recovery proof.
  Real activation/observation and partial-open beacon recovery remain open.

Updated: 2026-10-21 (isolated secondary-open reference repair)

- Added prepare-mbss-open-check.py: produces a separate driver candidate fixing
  the failed-open module reference leak without an extra virtual-count decrement.
  It never overwrites input driver or existing outputs and is not production
  preparation. Beacon/hardware failure recovery is still unresolved.
- Extracted repaired wrapper compiled/executed with strict MinGW in base,
  MT_MAC and MT_MAC+HNAT modes: all passed failure/success reference and queue
  checks. Driver actions injected, not target runtime. Added Linux sanitizer
  fixture to ABI, not run. No production driver or router state changed.

Updated: 2026-10-21 (secondary open-failure rollback hazard)

- Traced MBSS wrapper failure after beacon intent/module reference acquisition.
  Its early return omits normal cleanup. Pinned common/cmm_cfg.c confirms the
  virtual count is already rolled back on first hardware-open failure, so a
  naive VIRTUAL_IF_DOWN cleanup would double-decrement it.
- Saved exact evidence in activation-gap report. Next establish driver resource
  lifetime and targeted failure cleanup before binding real radio callbacks.
  Quarantine/recovery must remain when administrative DOWN is insufficient.
  No speculative driver patch, build or device mutation was performed.

Updated: 2026-10-21 (beacon reuse constraint confirmed)

- Located pinned tx_rx/wdev.c via the driver object list. Its beacon-buffer
  initializer has the bBcnSntReq reset commented out; repeated initialization
  cannot establish a silent third BSS. Saved blob ID/link in activation-gap
  evidence and tightened the lifecycle contract.
- Association/group-TX local entry checks do not independently prove DOWN
  interface exclusion. Continue full dispatch/close-open tracing; no unsafe
  reserved-BSS/profile change was made. No runtime claim, device mutation or
  firmware build. Whitespace check passed.

Updated: 2026-10-21 (inactive third-BSS alternative traced)

- Traced secondary beacon flag, DOWN-interface probe and authentication guards
  in local mt76x3 sources. Initial creation of reserved DOWN ra2 is a concrete
  alternative to live module replacement, not yet proved safe or implemented.
- Activation-gap report lists exact paths and missing initialization/security/
  receive/MAC allocation/target/RF evidence. Current device lacks ra2, so this
  would not repair its existing adapter without a lifecycle transition.
  No driver/profile/device change or new test execution in this source audit.

Updated: 2026-10-21 (actual status core executed on Windows)

- Added prepare-status-check.py extracting the actual control-client status
  function. Strict MinGW compile and execution passed observation failure/
  noncanonical values, all four record changes, both open/read failures,
  non-applied states and queue-lock release before observer invocation.
- Mailbox/observer reads are injected: this is actual status-core evidence,
  not Linux locking, real network observation or target acceptance. Added
  Linux sanitizer execution to ABI workflow; not dispatched/run here.

Updated: 2026-10-21 (status recheck after unlocked observation)

- Candidate client reopens the mailbox after observing APPLIED and compares
  transaction ID, state and both timestamps. Replacement/update while the
  observer holds no queue lock now returns unknown, not the old success.
- Channel fixture now submits a new request inside the fake observer and
  requires rejection of the old result plus visibility of the new queued ID.
  Linux execution remains pending; whitespace check passed. This does not
  implement the missing real observer or serialize all live radio writers.

Updated: 2026-10-21 (candidate applied-result observation gate)

- control-client now refuses to return APPLIED from a historical mailbox
  record unless a strong read-only transaction/live-state observer returns
  exactly 1. Missing implementation prevents production linking; no success
  fallback was added. Observation runs after releasing the mailbox lock.
- Extended Linux channel fixture for failed/error/noncanonical observations
  and lock release; fixture was not executed in Windows. Whitespace check
  passed. Real observer/snapshot generation and legacy-writer coordination
  remain unimplemented. No firmware build, commit, push or device change.

Updated: 2026-10-21 (legacy radio event coordination gap)

- Traced base restart_wifi_rt and watchdog: profile reload queues schedule
  resynchronization; it does not reload the module. Separate watchdog events
  can outlive activation and invalidate its earlier ACTIVE result. Existing
  candidate quiescence hooks do not coordinate controller state with them.
- Recorded the missing integration/acceptance requirement in the IoT contract
  and activation-gap evidence. Next bind legacy radio writers to recovery and
  status invalidation while preserving scheduled/manual radio-off intent.
  This is source evidence only; no device mutation or firmware build.

Updated: 2026-10-21 (owner supplied live module evidence)

- Owner successfully ran the fixed SSH helper with `-Check modules` in normal
  Windows PowerShell. Both mt76x3_ap (1266612, refcount 1) and mt76x2_ap
  (1130402, refcount 1) are loaded. Full supplied output and evidence limits:
  `docs/evidence/WR1200JS-IOT-INTERFACES-RUNTIME-2026-10-21.md`.
- This confirms the owner's SSH path, not direct Codex SSH access. Module
  presence does not prove Beamforming, active offload, or safe module reload.
  Continue owned 2.4 GHz adapter lifecycle/rollback investigation; no module
  unload, router change, firmware build, commit or push was performed.

Updated: 2026-10-21 (IoT explicit radio creation dependency)

- Added explicit RADIO_PREPARE after quarantine and before attachment/DHCP in
  the candidate activation sequence. Strict MinGW failure/partial-open/recovery
  model checks passed; actual radio callbacks remain unimplemented.
- Verified the local mt76x3 MBSS source hashes against pinned GitHub blobs.
  Repeated MBSS_Init is guarded by FlgMbssInit; MBSS_Remove does not reset it.
  Do not assume profile BssidNum changes plus ordinary interface down/up create
  ra2 on an already initialized two-BSS adapter.
- Next trace owned fresh-adapter/module lifecycle or prove safely reserved
  inactive third-BSS creation before implementing the real radio backend.
  Evidence: existing IoT activation-gap report. No module/device mutation,
  commit, push or full firmware build occurred.

Updated: 2026-10-21 (IoT final active-filter observation)

- Found that the existing pre-mutation policy readiness rejects UP ra2, so it
  cannot serve the activation state machine's final OBSERVE step. Added separate
  read-only administrative BSS/current-filter observers while retaining the old
  mutation guards. Bridge membership reads now reject directory read/close errors.
- Extracted actual observer code compiled/executed under strict MinGW with
  injected reads. Python syntax and whitespace checks passed. Existing Linux
  namespace and installed firewall fixtures were extended, not executed here.
- Real radio lifecycle/rollback, NAT/offload observation, persistence and the
  strong activation backend remain open. Evidence:
  `docs/evidence/WR1200JS-IOT-ACTIVATION-GAP-2026-10-21.md`.
  No commit/push/full build/device mutation occurred.

Updated: 2026-10-21 (IoT channel bound into candidate sources)

- `prepare-control.py` now binds HTTPD/RC channel objects and the exact fixed
  notification branch. CGI and metadata code also have the matching board
  guard. The strong activation backend remains absent; readiness flags are false.
- Actual GNU Make object-selection probes passed for WR1200JS/other/no-board
  on both Makefiles. Installed dispatch fixtures passed with and without the
  board define; metadata and Python syntax checks passed. Repeated preparation
  refused without changing the checked RC source. These are source/host checks.
- ABI installed-object MIPS and Linux runtime gates were added, not executed.
  Next implement real guarded activation/rollback and persistence, then complete
  source/image/device acceptance. Production remains excluded. Evidence is in
  the IoT HTTP CGI candidate report. No commit/push/full build/device change.

Updated: 2026-10-21 (private IoT control channel candidate)

- Implemented private single-request mailbox and HTTPD/RC source adapters.
  Submission now has candidate implementations for the previously external
  submit/status functions. RC claims once, publishes RUNNING and calls a strong
  activation backend symbol that remains unimplemented. Recovery blocks new
  requests; terminal cleanup can retry without executing activation again.
- Strict local MinGW syntax-only probes passed with POSIX declarations. Actual
  Linux filesystem/lock/channel runtime and MIPS compile/link remain unverified;
  ABI sanitizer fixtures and MIPS object gates were added but not run.
- Next install/link the adapters into candidate HTTPD/RC, add fixed notification
  dispatch and implement complete guarded activation/recovery. Production IoT
  remains excluded. Evidence is in the existing IoT CGI candidate report.
  No commit, push, firmware build or router mutation occurred.

Updated: 2026-10-21 (IoT request records and result CGI)

- Added bounded versioned request encoding/decoding and ID/freshness-bound
  explicit result states in `tools/iot/control-record.h`. Registered a candidate
  authenticated result CGI that returns unknown for stale/missing/future data.
- Strict MinGW record, CGI and extracted-metadata fixtures passed. ABI Linux
  sanitizer/MIPS checks were extended but not executed locally or remotely.
- Actual private HTTPD/RC transport, `wr_iot_rc_submit`/`wr_iot_rc_status`, fixed
  RC notification/dispatch and full activation/recovery remain open. The CGI
  code therefore remains excluded from production. Detailed evidence is in
  `docs/evidence/WR1200JS-IOT-HTTP-CGI-CANDIDATE-2026-10-21.md`.
  No commit/push/full build/device change occurred.

Updated: 2026-10-21 (dedicated IoT CGI source candidate)

- Added source preparation for exact authenticated token/Apply CGI routes,
  real request method/Content-Type observation and bounded no-NVRAM body input.
  The handler validates safe session/CSRF/fields and reports transport acceptance
  only. Its RC submit symbol remains unimplemented, so this cannot link as an
  HTTP-only working feature.
- Local source preparation, strict MinGW metadata/handler fixtures, and Python
  syntax checks passed. ABI Linux sanitizer/MIPS checks are scheduled in the
  modified workflow but not yet run. Production firmware preparation is untouched.
- Continue with bounded serialized RC request ownership and authenticated
  observed-result reporting, followed by complete real activation/recovery.
  Evidence: `docs/evidence/WR1200JS-IOT-HTTP-CGI-CANDIDATE-2026-10-21.md`.
  No commit/push/full build/device mutation occurred.

Updated: 2026-10-21 (direct IoT request staging)

- `wr_iot_request_stage_from()` now feeds an in-memory field reader into the
  existing RC staging validator under the same service guard. Dedicated
  submission can avoid writing intermediate candidate NVRAM keys. The existing
  NVRAM entry point delegates to this same implementation.
- Strict MinGW compilation and execution passed for staging and snapshot
  fixtures. Direct input is verified independently of stale candidate keys;
  empty SSID, missing reader, busy guard and live-network refusal cause no
  writes. Existing nested snapshot/recovery checks still pass.
- Integration remains incomplete: the authenticated HTTPD route, bounded
  inter-process request ownership, RC dispatch, real activation callbacks and
  observed result/recovery are still required. No production IoT enablement,
  commit, push, full firmware build or router mutation occurred.

Updated: 2026-10-21 (IoT authenticated request boundary candidate)

- Added `tools/iot/http-request.h`: a no-write boundary combining the fixed
  form parser, explicit authentication, POST/content-type checks, server-owned
  CSRF comparison and existing credential/subnet/mode validation. Rejected
  requests leave the caller's output unchanged.
- Strict MinGW compilation and the host fixture passed using a temporary
  Windows socket-header adapter. Linux sanitizer execution and MIPS compilation
  were added to the ABI workflow but have not run for this local change.
- This is candidate code, not a registered HTTPD handler. Next: bind a dedicated
  authenticated route to serialized RC submission, observed result/recovery and
  the real activation backend. IoT remains excluded from production firmware.
- No commit, push, firmware build or router change was performed.

Updated: 2026-10-21 (full retained Actions failure census)

## GitHub Actions failure review

- Queried all 960 retained Actions runs through monitor run `39646683016`
  (`#127`, skipped). Of 148 failed workflow runs, 90 were firmware builds,
  two were failed workflow-definition runs with no failed job returned, 28
  were Band Steering ABI checks, 27 service-runtime checks, and one was the
  Agent build failure monitor. The monitor is not a firmware build.
- Firmware #514 (`39644862386`, commit `a6edff8`) is the latest firmware run
  and all four jobs passed, including the corrected Privoxy image gate. Latest
  ABI #489 (`39644862372`) and service-runtime #249 (`39616973001`) also passed.
- The latest preceding ABI failure (#458) was a bounded-source-parser fixture
  assertion; the latest preceding service-runtime failure (#236) was a DNS
  fixture compile mismatch (`wr_process_present` used but not defined). Both
  workflows later passed. Monitor #125 failed before analysis because its Nim
  setup download returned `curl: (7) Couldn't connect to server`; #127 was
  skipped. These are not firmware build failures.
- The reviewed failure causes and subsequent passing runs are recorded in
  `docs/evidence/WR1200JS-ACTIONS-FAILURE-CENSUS-2026-10-21.md`. The #513
  Privoxy checker issue is already fixed in `a6edff8`; no second fix is needed.
- The checkout remains dirty with independent local changes, not included in
  #514. Preserve them; do not infer their CI status from that build. No
  workflow was cancelled/restarted, no commit/push was made, and the router
  was not changed.

Updated: 2026-10-21 (IoT dedicated form parser candidate)

## IoT authenticated WebUI prerequisite

- Added a bounded, no-write parser for the eight allowed IoT POST fields and
  an adapter to the existing request validator. The host fixture passed a
  strict MinGW compile and execution; its executable was removed.
- This is candidate code only. A dedicated authenticated CGI route must still
  check POST and CSRF, validate live mode/routes, serialize and submit the
  request to RC, then report observed activation or recovery. The generic
  Apply path is unsuitable. Evidence:
  `docs/evidence/WR1200JS-IOT-HTTP-FORM-CANDIDATE-2026-10-21.md`.

Updated: 2026-10-21 (IoT stage/snapshot host fixtures completed)

## IoT candidate verification checkpoint

- The current stage and snapshot sources both compiled under MinGW with
  `-std=gnu11 -Wall -Wextra -Werror -O2` and both fixture executables passed.
  This includes the new refusal of active or malformed service gates.
- The controlled compatibility-header probe directory and both older empty
  probe directories were removed. Earlier notes below about blocked linked
  execution and pending cleanup are historical and now superseded.
- Production authenticated submission, RC backend, full service/radio
  rollback, image inclusion and device tests remain open. Evidence:
  `docs/evidence/WR1200JS-IOT-CANDIDATE-NAMESPACE-2026-10-21.md`.

Updated: 2026-10-21 (IoT partial-failure recovery fixture)

## IoT activation model

- The candidate activation fixture now injects a failure after each modeled
  startup mutation and requires complete retained recovery. MinGW GCC compiled
  it with warnings as errors; the fixture ran successfully and its local
  executable was removed.
- This verifies only the injected backend model. Production RC callbacks,
  dnsmasq rollback, real radio lifecycle and device acceptance remain open.
  Evidence: `docs/evidence/WR1200JS-IOT-ACTIVATION-GAP-2026-10-21.md`.

Updated: 2026-10-21 (IoT active-gate refusal)

## IoT request staging during recovery

- Candidate `wr_iot_request_stage()` now refuses open or malformed profile,
  network and firewall gates before any write, even when `br-iot` is absent.
  The host fixture covers each gate at `1` and `stale` with zero writes.
- The fixture source passed MinGW syntax checking with warnings as errors;
  `git diff --check` passed. The linked host fixture was not rerun because
  Linux network headers are absent and temporary compatibility directories
  remain inaccessible in this executor. This is not production or device
  validation. Evidence: `docs/evidence/WR1200JS-IOT-CANDIDATE-NAMESPACE-2026-10-21.md`.

Updated: 2026-10-21 (IoT Apply result-path audit)

## IoT authenticated submission requirement

- Pinned HTTPD flow confirms generic `apply.cgi` can write NVRAM before RC
  activation and its script callback reports `done_committing()` without an
  observed IoT result. Candidate-key registration in that path alone would
  create a misleading Apply result.
- The implementation must use a dedicated authenticated, serialized
  submission/result path with full-request validation and fixed RC dispatch.
  Detailed source evidence: `docs/evidence/WR1200JS-IOT-APPLY-CONTROL-PLANE-2026-10-21.md`.
- The Windows snapshot fixture passed `gcc -fsyntax-only` with warnings as
  errors. Full linked fixture execution is still pending because temporary
  probe-directory access was denied. No router or firmware change was made.

Updated: 2026-10-21 (Windows fixture follow-up)

## IoT candidate fixture portability

- `tools/iot/check-request-snapshot.c` now uses `NUL` on Windows and
  `/dev/null` on Linux for its guard-descriptor probe. This changes only the
  host fixture, not firmware or router behavior.
- `git diff --check` passed. A fresh compile/run was blocked by denied access
  inside new probe directories; see the exact paths and cleanup note in
  `docs/evidence/WR1200JS-IOT-CANDIDATE-NAMESPACE-2026-10-21.md`.
- The candidate fields are still not registered in authenticated HTTPD Apply;
  no RC action or activation/rollback controller exists in production. IoT
  remains excluded and OFF.

Updated: 2026-10-21 17:50 UTC

## IoT candidate request isolation — 2026-10-21

- The candidate `wr_iot_request_stage()` now reads only seven fixed
  `wr_iot_request_*` keys. Active enable/SSID/password fields remain distinct
  in the host fixture and unchanged after staging. Host staging and snapshot
  checks passed with Windows-only network/test-path adapters; temporary probe
  files were removed. Source whitespace check passed.
- This is a local, uncommitted prerequisite. No authenticated form, RC
  dispatch, activation controller or complete rollback has been added; the
  production image still excludes IoT. Next: bind the candidate namespace
  through authenticated HTTPD Apply to a fixed RC action, then implement the
  transactional activation backend and full rollback before image inclusion.
- Evidence: `docs/evidence/WR1200JS-IOT-CANDIDATE-NAMESPACE-2026-10-21.md`.

Updated: 2026-10-21 17:46 UTC

## Firmware #514 successful after recent failure chain — 2026-10-21

- GitHub Actions [#514](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39644862386)
  completed successfully at `a6edff8`: build, selected-board requirement,
  downloads and firmware ZIP all passed. The Privoxy final-image gate that
  stopped #512/#513 passed, along with target BusyBox, Stubby QEMU DNS, DoH,
  discovery/KMS, StrongSwan and ZeroTier checks. Band Steering ABI #489 passed.
- A verified CI image/download artifact exists for #514; physical-router
  runtime remains unverified. Full run, artifact IDs and causal history:
  `docs/evidence/WR1200JS-BUILD514-RECOVERY-2026-10-21.md`.
- Next: continue the selected-service runtime and final-WebUI acceptance
  audit without treating this CI result as proof on the router. Keep all
  unrelated local changes intact.

Updated: 2026-10-21 17:34 UTC

## Firmware failure review through #513 — 2026-10-21 17:34 UTC

- Reviewed completed failed firmware jobs #489, #491, #493–#496,
  #498–#500 and #505–#513. #489/#491 had a missing toolchain `nm` path;
  #494–#496 had a KVR emitter fixture getter mismatch; #498 had KVR options
  missing from the effective build-tree config; #499/#500 had MT76x3 WNM/FT
  compile guards. Builds #501–#504 later succeeded, confirming progress past
  those earlier blockers. #505–#508 failed VPN pruning; #509–#511 passed that
  step but failed the QEMU dnsmasq random-seed check; #512/#513 passed those
  steps but failed the Privoxy Apply-order image gate. The downstream EoIP,
  diagnostics-upload and selected-image failures are consequences, not
  independent first causes. See the per-build evidence under `docs/evidence`.
- The #513 Privoxy verifier correction was committed alone as `a6edff8` and
  pushed to `codex/wr1200js-service-webui`. AST parsing and staged whitespace
  check passed; prior pinned-source in-memory fixture passed. GitHub started
  firmware #514 (run `39644862386`) and Band Steering ABI #489 (run
  `39644862372`) for this commit. ABI #489 later completed successfully;
  firmware #514 was still compiling at the latest check. CI has not yet
  established a new complete image. No router changes or full local build.
- Next: inspect the first Actions run for `a6edff8` through all final-image
  gates and downloads. If another gate fails, diagnose its original job log
  before changing source. Preserve unrelated local changes.

Updated: 2026-10-21 17:28 UTC

## CI monitor notifications — 2026-10-21

- At the owner's request, paused the Codex `padavan-ci` heartbeat. It no longer
  starts a chat turn every minute. A heartbeat cannot be triggered directly by
  a GitHub Actions failure, so automatic Codex wake-up on failure is not active.
- Locally narrowed `.github/workflows/monitor-agent.yml` to completed firmware,
  service-runtime and Band Steering ABI workflows. Removed its schedule, push
  and manual triggers; its job runs only when the triggering workflow failed.
  GitHub still creates a skipped monitor run when a watched workflow succeeds.
- The workflow change is uncommitted and not on GitHub. Until it is published,
  the existing remote monitor behavior continues. GitHub failure reporting
  remains available through Actions; this does not directly message Codex.

Updated: 2026-10-21 17:22 UTC

## IoT authenticated Apply/RC control-flow audit — 2026-10-21

- Pinned Padavan source confirms `apply.cgi*` is registered with auth, invokes
  `do_apply_cgi`, writes registered values through `nvram_set`, and dispatches
  `action_script` before redirect. RC consumes separate notification events.
- `sys_script` contains a generic `/tmp/<name>` fallback; any IoT trigger must
  use an exact fixed-name branch. Candidate settings must not overwrite active
  NVRAM before activation succeeds; rollback must retain the previous profile.
- No production IoT notification consumer/controller has been implemented.
  Detailed source evidence and integration requirements:
  `docs/evidence/WR1200JS-IOT-APPLY-CONTROL-PLANE-2026-10-21.md`.

## IoT interface runtime snapshot — 2026-10-21

- Owner-provided output from the fixed `interfaces` helper check shows `br0`,
  `ra0`, and `rai0` up; `ra2` and `br-iot` are not listed. Thus this snapshot
  does not show a live separate IoT AP/bridge. It cannot establish driver
  capability or DHCP/firewall isolation. `wg1` and WAN `eth3` are up as shown.
- Cumulative receive/transmit error/drop counters are recorded without
  attributing cause; a single `ifconfig -a` snapshot cannot show whether they
  are increasing.
- Full findings and boundaries:
  `docs/evidence/WR1200JS-IOT-INTERFACES-RUNTIME-2026-10-21.md`. Next work
  remains implementation of the production authenticated Apply/controller and
  complete rollback, with IoT OFF and excluded until verified.

## IoT activation integration checkpoint — 2026-10-21

- Read-only source/call-site audit confirms the activation state machine has no
  production backend/caller; the request-stage function has no authenticated
  WebUI/CGI caller; the prepared workflow reports activation and dnsmasq
  rollback incomplete; and the production WR1200JS workflow explicitly rejects
  the candidate IoT RC source. This means the current successful firmware
  profile cannot provide IoT.
- No source, router, firmware, or service was changed and no test/build was run
  in this inspection. Evidence and the required next integration dependency:
  `docs/evidence/WR1200JS-IOT-ACTIVATION-GAP-2026-10-21.md`.

## SSH config syntax correction — 2026-10-21

- User-run PowerShell helper reported that OpenSSH could not parse
  `%USERPROFILE%\\.ssh\\config` line 10: `BatchMode yes` had
  `IdentityFile ~/.ssh/id_ed25519` appended on the same line. Split these into
  separate directives, preserving the existing `github` host block and all
  other router options. Re-read the file to confirm the corrected layout.
- This was a local config-parser failure; the router was not contacted by that
  attempt. The user subsequently confirmed `ssh -G wr1200js` resolves the
  intended ASUS/192.168.20.1:22 identity, and the helper's read-only `identity`
  check returned Linux WR1200JS 4.4.198. See
  `docs/evidence/WR1200JS-SSH-USER-RUNTIME-2026-10-21.md`. Direct SSH remains
  blocked in the managed Codex executor; the user-run Windows path works.

## Cross-agent router diagnostics rule — 2026-10-21

- Added a project-wide rule in `AGENTS.md`: agents use only fixed named
  read-only checks, and when an executor cannot access Windows OpenSSH they
  ask the owner to run the exact helper command and return output. No bypass,
  key exposure, unsupported claims, or router mutation is allowed.
- The owner confirmed the `identity` helper works from ordinary Windows
  PowerShell. The next outstanding read-only check is `interfaces`; see
  `CODEX_HANDOFF.md` for the command.

## Scoped read-only router helper — 2026-10-21

- Added `tools/wr1200js-readonly.ps1` and `docs/WR1200JS-READONLY-SSH.md`.
  The helper fixes the destination to ASUS at `192.168.20.1:22`, uses the
  previously recorded `%USERPROFILE%\\.ssh\\id_ed25519` identity without
  printing or copying it, and exposes only named read-only status commands.
  It disables TTY and port forwarding and refuses to run when Codex's SSH
  deny-bin is first in command resolution.
- PowerShell parser and trailing-whitespace checks passed. Invoking the helper
  in this managed executor stopped at its deny-bin guard with the intended
  message and exit code 1, before launching any SSH process. No SSH connection
  was attempted; the helper still needs to be run from ordinary Windows
  PowerShell to confirm the current key file, host key and route. Router state
  was not changed.
- A Codex chat-level network allowlist alone does not grant the helper access
  to the private key or remove the executor's SSH command block. Do not expose
  the key file to agents or bypass `.sbx-denybin`. Direct agent access requires
  an approved managed permission/process path; the local helper is for
  user-run inspection and does not provision access for all Codex/DeepSeek
  identities.

Updated: 2026-10-21 17:07 UTC

## CI failure monitor cadence and access boundary — 2026-10-21

- The existing `Padavan CI: виявити й виправити падіння` heartbeat is active
  and now checks GitHub Actions every minute, targeting this local Codex chat.
  It ignores unchanged state and already handled run/attempt IDs, and remains
  quiet when no actionable failure appears. This is periodic polling, not an
  event-driven webhook; expected detection delay is up to about one minute
  plus task startup time.
- On a new failure it should inspect the exact failed job/log, diagnose the
  cause, make a minimal safe local fix when supported by evidence, run focused
  checks, and update this file plus `CODEX_HANDOFF.md`. It must not change the
  router, alter Codex/Windows security settings, bypass the sandbox, cancel or
  restart workflows, or commit/push without separate authorization.
- The heartbeat is attached to one Codex thread. It does not grant access or
  automatically coordinate all seven Codex accounts or Sol/DeepSeek; the
  existing single-writer handoff rules remain in force. The SSH deny-bin still
  intercepts normal SSH before negotiation, and no SSH executable was invoked
  by bypassing it. No router, Windows firewall, sandbox, key, or GitHub setting
  was changed.

Updated: 2026-10-21 16:59 UTC

## Privoxy verifier source-shape validation — 2026-10-21 16:59 UTC

- Confirmed the Privoxy Apply-response patch anchor against pinned upstream
  `web_ex.c` revision `c25283e915a2a00a763774dd255b14aff997285e`. An in-memory
  simulation of that response replacement plus the shared-Wi-Fi `&shared`
  call rewrite passed the current parser's Apply/failure ordering, callback,
  restart-clear, abort and success-order checks.
- No fixture files were created. This does not run the full integration
  pipeline or ROMFS image verifier. Fresh image confirmation remains pending.
- Evidence: `docs/evidence/WR1200JS-BUILD513-SERVICE-AUDIT.md`.

## DNS audit status wording refreshed — 2026-10-21 16:58 UTC

- Corrected stale DNS audit rows that still described the #513 target DNS
  parser/BusyBox checks as pending. #513 passed the Stubby ROMFS gate, an
  authenticated Stubby DoT lookup under QEMU, the combined target dnsmasq
  parser, and target BusyBox listener-conflict scenarios.
- The same run failed at Privoxy before the DoH-specific ROMFS/guard identity
  gate, which was skipped. The audit now keeps that DoH evidence open and
  separates it from #504's older DoH packaging result. No device runtime claim.

## Build #513 DNS gate evidence — 2026-10-21 16:57 UTC

- Re-read the exact GitHub Actions job steps and relevant log lines. #513
  passed DNS listener-conflict scenarios, target dnsmasq parsing of the
  combined DoT/DoH config under QEMU, the Stubby lookup check and the exact
  target BusyBox shell audit.
- The run later failed its Privoxy final-image gate; DoH packaging and
  discovery/KMS checks were skipped. No verified downloadable image resulted.
  DoH packaging, simultaneous live DNS behavior and router runtime remain open.
- Details: `docs/evidence/WR1200JS-DNS-LISTENER-CONFLICT-GUARD-2026-10-21.md`.

## Selected-service audit map — 2026-10-21 16:56 UTC

- `python tools/check-target-busybox-map.py` passed: 12 active-service-map
  coverage fixtures and their negative cases; all 43 active WR1200JS `INCLUDE`
  selectors have a service/component classification. Shadowsocks aliases,
  SFE/QoS exact-image requirements and WPAD/ZRAM gate order are covered.
- This is the source-level audit-map gate only. It does not prove the BusyBox
  binary or service contents of a new ROMFS, nor runtime behavior. Image and
  device acceptance remain open.

## Service audit continuation — 2026-10-21 16:53 UTC

- Live GitHub Actions query: firmware #513 remains the newest firmware run and
  failed after compile/QEMU at the Privoxy final-image gate. Run #125 is the
  separate Agent build failure monitor, not a firmware build. No newer image
  exists to verify current local changes.
- Local service-navigation verifier, WR1200JS CPU-watchdog fixture and
  in-memory Privoxy parser fixtures for both Apply signatures pass. `git diff
  --check` reports no whitespace errors; only existing CRLF normalization
  warnings remain.
- The active WR1200JS build config maps to service links for Stubby, DoH,
  WireGuard/AmneziaWG, ZeroTier, Shadowsocks, Privoxy, WPAD/PAC, HTTP/HTTPS,
  SSH, Telnet, iPerf3, Cron, KMS, LLTD and ASUS Info Discovery. EoIP is
  selector-disabled and CPU watchdog is board-excluded. This remains source
  expectation pending exact-image inspection.
- No local `padavan-4.4/trunk/romfs` is available, so no final-image gate was
  run. Device checks remain stale because the Codex executor's SSH command is
  blocked before SSH negotiation. Router unchanged.
- Next: obtain a permitted path for read-only SSH, then include current source
  in a WR1200JS image workflow and inspect the exact Privoxy/watchdog/final-ROMFS
  evidence. Continue other independent service-source audits without waiting
  for a build.

## Padavan Modern dashboard reference — 2026-10-21 16:40 UTC

- Added the user's Ukrainian neon dashboard image as an additional future
  Padavan Modern homepage reference in `docs/WEBUI-MODERN-HOME-SCOPE.md`.
- Captured its main dashboard layout and capability/data-truth requirements,
  including truthful `Н/Д` temperature values and DEMO-only preview data.
  The small page mockups in the image are design references only; this request
  does not authorize implementing those pages now.
- The accepted order is unchanged: finish and verify IoT first, then finalize
  the Modern homepage design, then build the Modern title/home page. Classic
  remains unchanged. This was a documentation update only.

## SSH executor diagnosis — 2026-10-21 16:39 UTC

- Normal `ssh -V` and GitHub `ssh -T` invocation in Codex Desktop both resolve
  first to `.sbx-denybin\ssh.bat`/`.cmd` and return the literal text
  `off\r\nexit /b 1\r\n`. System OpenSSH exists later in PATH but was not
  invoked. The process stops before SSH/network negotiation; this is a
  sandbox/executor command-policy block, not evidence of a key or router
  network failure. See
  `docs/evidence/WR1200JS-SSH-CODEX-EXECUTOR-BLOCK-2026-10-21.md`.
- No SSH keys/configuration, GitHub, security settings, or router state were
  changed. The latest authenticated router evidence remains 16:18 UTC.

## Latest service continuation — 2026-10-21 16:38 UTC

- GitHub build #513 (`39632923432`, source `8ff6016`) completed compilation,
  then failed the Privoxy final-image gate. The `privoxy-image-checks`
  artifact confirms only `save_failure_apply_order` failed; its assignment
  matcher did not account for the later shared-Wi-Fi transform adding
  `&shared` to `validate_asp_apply`. The remaining failure callback, restart
  clears and abort predicates were present. No verified downloadable image
  resulted. Details and artifact digest are in
  `docs/evidence/WR1200JS-BUILD513-SERVICE-AUDIT.md`.
- Updated `overlay/padavan-4.4/ports/privoxy/verify-image.py` to match either
  valid Apply signature and inspect ordering inside the nested Save/Apply
  response block. An in-memory fixture for the transformed signature passed;
  a new final ROMFS run is still required.
- The WR1200JS CPU-watchdog board change and corrected Privoxy gate are both
  absent from #513; neither is yet image-verified. Router SSH retried from
  this executor but was intercepted by the managed deny-bin, so the latest
  authenticated device observations remain the 16:18 UTC read-only snapshot.
- No router state changed; no firmware was flashed or rebooted. Item 4 remains
  active. Next: run the corrected final-image gates in a later workflow, then
  continue the enabled-service/BusyBox audit and device checks when SSH is
  available.

## Service capability follow-up — 2026-10-21 16:30 UTC

- Revalidated the unsupported `watchdog_cpu` path against the pinned Padavan
  source and the 16:18 read-only device sample. On WR1200JS it requests the
  absent optional `rt_timer_wdg` module; it is distinct from the built-in
  MT7621 watchdog. A board-scoped transform now removes the enable control,
  makes the legacy lifecycle inert, and changes the WR1200JS factory default
  to off while preserving the generic default for other boards. The diagnostic
  status row remains; the navigation link is excluded for this board.
- Added a per-board capability manifest, source fixture, and final-ROMFS gate.
  In-memory transform check and navigation verifier passed; pinned source
  anchors matched exactly once. The image gate has not run in CI, and physical
  UI/runtime verification remains pending. No device state changed.
- Build #513 predates these edits; inspect its completion for the existing
  source before launching a later build that includes this change.
- Evidence: `docs/evidence/WR1200JS-CPU-WATCHDOG-CAPABILITY-2026-10-21.md`.

## Previous refresh — 2026-10-21 16:26 UTC (superseded above)

- The router answers TCP port 22 at `192.168.20.1`, but a new SSH command
  from this managed Codex executor was intercepted by its `ssh.bat`/`ssh.cmd`
  deny-bin (`off\r\nexit /b 1`). The Windows OpenSSH binary exists, but was
  not invoked directly. No authenticated SSH session or remote command ran;
  the 16:18 service observations remain the latest device snapshot.
- GitHub run #513 (`39632923432`) is still in progress. Its firmware build
  job passed the pre-build WebUI/service checks and remains at
  `Build WR1200JS firmware`; final image gates have not run.
- No router state changed. See the latest connection evidence in
  `docs/evidence/WR1200JS-SERVICE-READONLY-CHECK-2026-10-21.md`.

## Earlier state snapshots — retained for history

The snapshots below were current at their timestamps and are superseded by the
16:38 continuation update above.

### Live refresh — 2026-10-21 16:16 UTC

- GitHub firmware build #513 (`39632923432`) is in progress for HEAD
  `8ff6016947bcb19363a7f0ddbc502a217432868b`; its WR1200JS build job is still
  compiling and the image audit steps have not started. The separate Band
  Steering ABI run is also in progress; it is not a firmware build.
- Fresh SSH attempts to `192.168.30.1` and `192.168.20.1` both timed out on
  port 22. No remote command ran, and no device state was read or changed in
  this refresh. Previous successful read-only observations remain historical,
  not a current service-state confirmation.
- See the latest attempt in
  `docs/evidence/WR1200JS-SERVICE-READONLY-CHECK-2026-10-21.md`.

### SSH retry succeeded — 2026-10-21 16:18 UTC

- SSH access to `ASUS@192.168.20.1` is restored. KMS flag/process agree as
  enabled/present; LLTD, ASUS Discovery and Cron agree as disabled/absent.
  `watchdog_cpu=1`, but optional module `rt_timer_wdg` is absent. A distinct
  `/sbin/watchdog` process and built-in `/dev/watchdog` node exist; timer
  servicing remains unproven. Current filtered system logs had no matching
  entries. The installed Services page still has generic Cron/Watchdog/
  Discovery links and no row anchors for those controls. No device state was
  changed. Full observations are in the read-only service evidence file.
- Firmware build #513 remains in progress; service image gates have not run.

- Current checkout: branch `codex/wr1200js-service-webui`, HEAD `8ff6016`.
- Firmware run #512 (run `39624109819`, HEAD `22431a94`) completed the full
  firmware compile. The repaired Stubby combined-config DNS test under QEMU
  passed. The image audit then failed at Privoxy `save_failure_apply_order`
  (`false`); other listed Privoxy image checks passed. The downloads job
  consequently rejected the incomplete selected-build set, so no verified
  downloadable image was produced. The verifier now records each subcondition
  (call/branch order, save-failure flag, callback, restart clears, abort) in its
  report. The local transformation reproduction passes all eight conditions,
  but is not the exact CI prepared tree and does not explain CI's false
  aggregate. Use the next run's subcondition report before changing behavior.
- Builds #509, #510 and #511 all passed the formerly failing VPN preparation
  step, then failed at `Resolve names through the image Stubby under QEMU`.
  The final combined-config `dnsmasq --test` under `qemu-mipsel-static` exited
  5 after `dnsmasq: failed to seed the random number generator: Success`.
  The downloads index has no verified image (`images: []`,
  `missing-or-ambiguous`). The pinned dnsmasq source reads 176 bytes from
  `/dev/urandom` to seed its parser process. The checker now gives QEMU a
  temporary sysroot overlay with host-CSPRNG bytes at that guest path and
  exposes the generated config under guest `/tmp`; it leaves ROMFS untouched.
  Python AST parsing and whitespace checks pass; target QEMU and final-image
  verification are still pending. See
  `docs/evidence/WR1200JS-BUILD506-507-VPN-HOOK-2026-10-21.md` and
  `docs/evidence/WR1200JS-QEMU-DNSMASQ-SEED-FIX-2026-10-21.md`.
- A fresh read-only SSH check succeeded via `192.168.30.1`, verified against
  the already-trusted host key for `192.168.20.1`. KMS flag/process agree as
  enabled/running; LLTD and ASUS discovery agree as disabled/stopped; Cron is
  disabled with no `crond`; `/sbin/watchdog` is running but its saved flag was
  not found in the queried key set. The served page still has generic,
  unanchored System navigation and lacks separate KMS/ASUS links. `buildno` is
  empty, so installed image identity remains unknown. Browser auth at the
  alternate address failed; all device inspection was read-only.
  See
  `docs/evidence/WR1200JS-SERVICE-READONLY-CHECK-2026-10-21.md`.
- At the earlier #512 checkpoint, no commands or firmware builds were running;
  #513 later entered and completed as described above. At that time, item 4's
  next action was to diagnose the Privoxy Apply/save-order gate. Preserve Sol
  and DeepSeek roles and the single-writer rule.

## Workspace and handoff

- Repository: `Andrzej1973/padavan-4.4.198`
- Shared checkout: `C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\router-guide-work`
- Branch at this checkpoint: `codex/wr1200js-service-webui`
- HEAD at the earlier account-organization checkpoint: `35d70beaba42bb4ef6aad57ad337cb3d1ff58823`; current HEAD is recorded above.
- The checkout was already dirty: 64 entries in `git status --porcelain` before
  this handoff setup and 68 afterward. Existing changes and untracked files
  were preserved; the four added entries are the account-handoff files and
  helper. Recheck status before doing any work; counts are dated snapshots.
- One account/agent writes at a time. Sol and DeepSeek's existing rules and
  roles remain active alongside the sequential Codex-account process.
- DeepSeek (also called DeepSeeC by the owner) is an occasional continuing
  participant; preserve its handoff rules and role history for future visits.
  The seven-account ledger tracks Codex logins only, not Sol or DeepSeek.
- The read-only handoff helper was run on 2026-10-21: branch
  `codex/wr1200js-service-webui`, HEAD `35d70be`, 72 changed/untracked paths.
  This is a live snapshot only; no existing path was cleaned or reset.
- No account-switch test between two signed-in accounts has been performed.

## Project checkpoint

- Continue the approved WR1200JS project sequence from the current service
  audit (delivery item 4); account handoff organization does not reorder it.
- Per the owner's report, firmware builds #501–#504 passed and #498–#500 failed.
  #504 is the latest successful firmware build. The Actions entry named
  “Agent build failure monitor” is not a firmware build.
- A newer firmware workflow attempt, #505 (run `39465298056`), failed on
  2026-10-20 before compilation. Its `build-wr1200js` job failed at
  “Exclude legacy VPN userspace”; later compiler and firmware steps were
  skipped. `tools/prepare-wr-vpn-pruning.py` reported
  `VPN protocol option changed: vpncli.asp 0` and exited 1. Root cause:
  `tools/vpn-profiles/prepare-web.py` had already removed PPTP/L2TP, then the
  later pruning stage required those options again. IMQ patch rejects were
  printed earlier, but they were not the fatal exit. This source issue is now
  corrected locally with an idempotent removal helper and a strict final
  selector gate; see `evidence/WR1200JS-BUILD505-FAILURE.md`. The in-memory
  regression fixture, Python syntax parse, and whitespace check passed.
  Later builds #509–#511 verified the preparation fix, but failed at the
  subsequent QEMU combined-dnsmasq validation described above.
- Build #504's CI/image evidence, including the Stubby DoT QEMU check, does not
  prove runtime service behavior on the physical router. The VPN list change
  noted in the owner's report was not included in the PR or verified by #504.
- A source review of #504's exact `check-target-busybox.py` and
  `target_lua_audit.py`, plus its passing Actions job log, confirms its selected
  image Lua gate passed under QEMU: Lua 5.1, cjson/nixio ELF closure, bundled
  Lua syntax checks, JSON converter round-trip and malformed-input rejection.
  Lua-consuming service behavior and `nixio` operations remain unverified.
- PR #2 was observed open at head `35d70be...` during this checkpoint. Refresh
  its state before making delivery decisions.
- The router was not changed in this account-organization task. Do not flash,
  reboot, or change live services without the project's existing authorization.

## GitHub integration diagnostic

- SSH authentication to `git@github.com` succeeded for `Andrzej1973` during
  the prior investigation; GitHub does not provide shell access over SSH.
- The GitHub connector can read public repository metadata and PR #2, but the
  collaborator-permission endpoint returned `403 Resource not accessible by
  integration`.
- This does not establish that repository visibility or the user's GitHub
  access is missing. It only establishes that this connector invocation could
  not access that endpoint. A missing GitHub App `Metadata: read` permission
  is one possibility; connector endpoint limitations are another. No
  permissions or authentication settings were changed. The owner may inspect
  the connector's GitHub App permissions/reconnection if that endpoint is
  needed; do not change them without approval.
- Local `gh auth status` had reported an invalid keyring token. This is separate
  from the successful SSH transport and the GitHub connector's own connection.
  No token was read, copied, or replaced.

## Next session checklist

1. Read `AGENTS.md`, `CODEX_HANDOFF.md`, `docs/AGENT-BOOTSTRAP.md`,
   `docs/AGENT-HANDOFF-RULES-SOL-DEEPSEEK.md`, and the current top block of
   `docs/EXECUTION-ROLE.md`.
2. Recheck branch, HEAD, and all modified/untracked paths. Do not clean the
   existing worktree.
3. Refresh Actions to distinguish firmware runs from monitor runs; #504 was
   the last confirmed successful image and #505's exact fatal check is above.
4. Continue the next authorized service-audit task independently of any
   running build unless that task specifically depends on its artifact.
5. Update this file and `CODEX_HANDOFF.md` before handing writes to another
   Codex account, Sol, or DeepSeek.

## Service WebUI progress — 2026-10-21

Rechecked current Actions: #505 (`39465298056`, source SHA `35d70be`) remains a
failed firmware build at `Exclude legacy VPN userspace from WR1200JS`; the
compiler and image checks were skipped. The latest run is the unrelated Agent
build failure monitor #113, not a firmware build. The newer Service runtime
state checks #247 passed selected lifecycle/USBIP/WAN/VPN profile checks on
source SHA `35d70be`; it is not a firmware build and does not test the local
VPN selector correction below.

Commit `25ca366` was pushed through SSH on 2026-10-21 with the correction for the #505 failure:
the later VPN-pruning stage accepts PPTP/L2TP already removed by the earlier
transform, still removes OpenVPN, and leaves the final strict selector gate in
place. A focused in-memory fixture passed for client and server order
equivalence, WG-only output, and missing/duplicate OpenVPN rejection. This is
source/host evidence only. The correction has not been tested by the full
`check-web.py` against a prepared Padavan source tree, by a confirmed post-fix CI result, or in a final
image. No router state was changed. Continue the independent service audit;
do not wait for a build unless the next action needs its image.

Build #504 log review additionally confirmed its settings-backup ROMFS and
synthetic browser-behavior checks; the evidence and remaining physical-router
checks are recorded in `docs/evidence/WR1200JS-BUILD504-SERVICE-AUDIT.md` and
`docs/SERVICE-PORT-AND-SETTINGS-AUDIT.md`.
The separate successful service-state run #247 on `35d70be` covered selected
SSH/iPerf3/Privoxy, Cron, LLTD/ASUS/KMS/Watchdog, VPN-profile and USB/IP
fixtures. It is source-level/mock evidence only; see
`docs/evidence/WR1200JS-SERVICE-STATE-CHECKS-247.md`.

Next item 4 action: collect the Stubby/DoH target BusyBox, QEMU and final-image
gates in the next WR build, and continue the remaining enabled-service sweep.
Privoxy source review found a persistence-feedback gap: its WebUI file handler
logged a failed `mtd_storage.sh save` but still allowed an Apply success
callback. The source transform now emits a localized failure callback and
suppresses the pending restart/success response. The editor remains open for
retry; files may already have changed in RAM. An in-memory integration run
applied event-bank extension, Privoxy file routing and incomplete-POST
protection in their production order and confirmed the response markers.
Details and limits are in `overlay/padavan-4.4/ports/privoxy/PORT-CONTRACT.md`.
The specific correction and check record is in
`docs/evidence/WR1200JS-PRIVOXY-SAVE-FEEDBACK-2026-10-21.md`.
Target compilation, forced save-failure browser behavior and reboot persistence
remain open. The #247 Privoxy process-state fixture does not cover these cases.

The next selected-service source review found that ZeroTier's durable-state
hash pipeline could hide a per-file read/hash failure. The lifecycle
preparation now fails closed before startup or membership synchronization and
keeps a pending-save marker if hashing fails after a change. The image gate
requires those guards. Python syntax, host shell syntax, three synthetic
host hash cases and diff checks passed; target BusyBox, image, actual storage
fault and router persistence checks are open.
The next image workflow now runs a bounded QEMU fixture against the shipped
ZeroTier helper and BusyBox, covering hash/save failures and pending-marker
retry. Its assembled shell syntax passed locally; CI execution is pending.
Commits `25ca366` (the #505 VPN selector correction) and `029b230` (Stubby/DoH,
Privoxy and ZeroTier service checks) were pushed via SSH to
`codex/wr1200js-service-webui` on 2026-10-21. No post-push CI or final-image
verdict has been collected yet. Independent source/service review continues.
The next independent iPerf3 audit expanded its image gate from status-only to
target binary, lifecycle helper, compiled RC/HTTP Apply route and factory-off
default, plus recursive ELF dependency closure. Commit `e806465` was pushed
via SSH on 2026-10-21. Local syntax/source and diff checks passed; the new image gate and physical
start/stop/client test remain open. See
`docs/evidence/WR1200JS-IPERF3-IMAGE-LIFECYCLE-GATE-2026-10-21.md`.
Firmware builds #506–#508 failed before compilation at the VPN capability
hook. The current Classic pages already use value-based OpenVPN removal; the
later transform required an old index-based form. Commit `63dfd1d` accepts
exactly one existing value-based hook or upgrades exactly one old hook, with
fail-closed fixture coverage. It was pushed via SSH. The previously fatal
preparation step passed in #509–#511; all three runs later failed at the QEMU
combined-dnsmasq validation. No final image was produced. See
`docs/evidence/WR1200JS-BUILD506-507-VPN-HOOK-2026-10-21.md`.
Commit `2e73d22` adds System navigation links to capability-gated KMS and ASUS
Info Discovery, and names LLTD separately. It was pushed via SSH. Local
navigation/older-ROMFS anchor checks passed; new-image and physical browser
acceptance remain open. See
`docs/evidence/WR1200JS-SERVICE-NAV-SYSTEM-LINKS-2026-10-21.md`.
Commit `fe02f7e` additionally requires the prepared client/server pages to
retain exactly one value-based OpenVPN hook. It was pushed via SSH; its CI,
image and physical browser results remain pending.
See `docs/evidence/WR1200JS-ZEROTIER-PERSISTENCE-HASH-2026-10-21.md`.
Keep live DNS behavior, service restart/persistence and physical browser
acceptance explicitly open; do not start optional DNSCrypt work until this
active-service sweep is done.

The 2026-10-21 source audit found no cross-service listener collision guard.
A shared check is now wired into Stubby and DoH startup, rejecting overlapping
configured listener ports/addresses while allowing distinct specific binds and
the default port ranges. Both prepared-package integrations install the shared
source at service-specific ROMFS paths. Added host-fixture and target BusyBox
QEMU coverage plus source/image identity checks. All 17 host scenarios now
pass, including invalid-peer rejection and a Stubby system port. The initial
sandbox signal-pipe error was resolved for these checks by an approved run
outside the sandbox; Windows settings were not changed. The actual Stubby
configuration fixture and syntax checks for seven shell files also passed.
Stubby startup, guard and dnsmasq emitter now match the form's 1024..65535
range; stored values are preserved, and invalid listeners keep `no-resolv`.
Corrected the image runner's nonexistent DoH guard source path to dns-common.
CI target BusyBox/image checks have not run. Next: continue the remaining
service lifecycle/Apply sweep and collect the target checks in the next image.
The router was not changed.
Detailed results and CI scope are in
`docs/evidence/WR1200JS-DNS-LISTENER-CONFLICT-GUARD-2026-10-21.md`.

### Stubby/DoH combined dnsmasq source review — 2026-10-21

Inspected the pinned Padavan dnsmasq 2.90 source (`c25283e...`). Its forwarding
code uses eligible upstreams as one shared pool; retry/failover and occasional
parallel forwarding mean enabling both router-DNS modes does not select one
exclusive service or guarantee DoT/DoH preference. Both existing emitters also
write duplicate `no-resolv` and NTP-bootstrap entries. Default listeners do not
overlap. The initial source review found no cross-service port-conflict check;
the runtime guard is now implemented, with its image-level validation pending.

Added `tools/check-encrypted-dnsmasq-combination.py` and a build-workflow gate:
compile the actual C emitters, cover DoT-only, DoH-only, combined and standalone
Stubby cases, verify the final `services_ex.c` integration and parse the
combined config with the built MIPS dnsmasq under QEMU. This is source/config
syntax coverage, not a live DNS-path check. The checker now supports native
Windows execution rather than unconditionally skipping it. Actual native GCC
compilation and execution passed ten scenarios: four mode combinations and six
Stubby port boundaries. A strict-compiler truncation warning in the validated
bootstrap IPv4 copy was fixed in both emitters. Temporary fixture files were
removed by the helper. Final prepared-source integration and the built MIPS
dnsmasq/QEMU parser gate remain pending; do not describe the combined path as
router-runtime-tested.
Detailed evidence/limits: `docs/SERVICE-PORT-AND-SETTINGS-AUDIT.md`, section
“Combined Stubby/DoH dnsmasq routing review”.
