## 2026-10-31 role accepted by Sol; next concrete step is target/feature compile

Accepted single execution ownership after confirming local/remote SHA match at
`c56e056c548ed746692b73d70f18df78776dcad6` and a clean working tree. The two
CI runs on that SHA (firmware #643 run 41199593428; Band Steering ABI run
41199593458) were in progress at acceptance. Next: reproduce committed IoT
candidate generators/evidence from source, complete remaining lifecycle and
ownership work, and perform target/feature compilation against the actual MIPS
toolchain and feature guards. Host replay (86 variants) is not a firmware
build. Device flash/reboot/service changes remain unauthorized.

## 2026-10-31 execution handoff to Sol after published checkpoint

Owner request: finish the current work chunk, record it, publish everything
suitable to GitHub and avoid leaving accumulated local artifacts.

Published code checkpoint:
`61c634b5508ffc29648e522da8444c882cf0abc7`
(`feat(wr1200js): checkpoint IoT ownership and Modern WebUI`). It contains 506
files, 39,105 insertions and 235 deletions. This document is in the direct-child
handoff commit; verify the final remote SHA instead of assuming the handoff SHA
from this text.

What was completed:

- IoT candidate82 and the auxiliary exact-ticket retry scheduler are published
  with their generators, strict host fixtures, source auditors and evidence.
  The final extracted host replay passed all 86 variants.
- Modern WebUI has the full eleven-page local preview plus a production-shell
  installer for `/modern/index.html`, private assets and authenticated
  `/wr_modern.json`.
- Current rechecks passed: Python compileall; JavaScript syntax; DEMO HTTP
  verification; production static-shell validation; host live-JSON emission;
  production-shell HTTP verification; and the IoT scheduler fixture. The
  scheduler recheck used a release build because local MinGW lacks ASan runtime
  libraries.
- Public WAN/ISP addresses and VPN endpoint details were redacted. Private
  SSH/PCI evidence is local-only and ignored, not published.
- Reproducible local scratch was removed, including `.iot-local-check`, CI
  artifact extracts, temporary build/test directories and Python/Node caches.
  Tracked source content was preserved.

The project is not complete. IoT still lacks target/feature compilation,
ROMFS/image validation, callback/timer/DMA quiescence proof and device runtime.
Open lifecycle work includes WDS/peer completion identity, failed insertion
cleanup, timer/callback joining and one coherent adapter/peer/radio/PCI
lifetime owner. The Modern production shell is not wired into the firmware
workflow and is neither MIPS-compiled nor ROMFS/device verified.

Sol is now the single execution owner. After explicitly accepting, Sol must
check `git status`, local/remote SHA and CI, then continue in this order:

1. Finish IoT ownership/lifecycle and target feature compilation.
2. Verify the Modern production shell, Zapret2 and the final TRX, SHA256,
   ROMFS contents and release gates.
3. Request fresh authorization before any device-side testing, flash, reboot,
   service restart or configuration change.

Preserve Band Steering and its required functionality; only evidence-backed
log-noise reduction is permitted. IoT remains mandatory in the release
objective. CAKE remains excluded. Do not reuse the deleted scratch trees as
proof; use the committed evidence and reproduce tests from source when needed.

## 2026-10-31 Modern production shell prepared; build wiring open

Added a repeatable production installer for `/modern/index.html`, private
assets, shared-Wi-Fi planner and authenticated `/wr_modern.json`. The live JSON
emitter returns selected NVRAM/system values, memory and uptime only; no
secrets or logs. Host fixture generated valid11-page JSON and a disposable
source install passed asset/route checks. Browser production-shell fixture
loaded in LIVE READ-ONLY mode with no console errors. Next: wire installer into
WR1200JS build workflow, target-compile/link httpd, inspect ROMFS and run
authenticated read-only device smoke tests after authorization. No build,
router change or publication in this step.

## 2026-10-31 Modern WebUI full reference structure; local preview PASS

Expanded `tools/webui-preview` from dashboard/Wi-Fi into11 informational pages:
WAN, IoT, LAN, VPN, DNS/proxy, services, monitoring, firewall, QoS, system,
log. Added header band switcher, WAN traffic graph, process rows, explicit
`Н/Д` temperatures and fixed contradictory USB DEMO state. Service tiles route
to local VPN/DNS/Services preview groups while retaining Classic destinations.
All11 pages and representative Wi-Fi/IoT routes rendered with no console error.
Desktop and390x844 widths matched document/scroll width; viewport reset after
test. node checks,15-route Wi-Fi test, six reference hashes and
`verify_preview.py` passed. This is local DEMO only; production ASP/CGI,
NVRM/services/DHCP/firewall/IoT runtime and firmware Modern integration remain
open. No router mutation, build or publication.

## 2026-10-31 DeepSeek resumed IoT; auxiliary retry scheduler82 host PASS86

Role accepted in `docs/EXECUTION-ROLE.md`; local/remote HEAD `13ce368` matched
at acceptance. Existing dirty work was preserved. Four stale IoT auditors were
repaired. Fresh candidate81 passed85 host variants. Scheduler82 adds
APCLI/Monitor deferred exact-ticket retry with `dev_hold`, module-pin retention,
locked terminal completion, adapter-release fencing and PCI stop/join paths.
Full82 passed86 extracted variants. A fresh whole-chain rebuild has585 files,
0 byte differences from the tested scheduler tree, and passed6 focused replay
variants. Evidence:
`docs/evidence/WR1200JS-IOT-AUX-RETRY82-2026-10-31.md`.
No MIPS/ROMFS/runtime acceptance. Canceled/failed work is retained without an
automatic reaper. Next: target/feature compilation and callback/timer completion
receipts, then final child/root/PCI release. No router mutation or publication.

## 2026-10-31 handoff to DeepSeek; Sol stops writing

Owner requested handoff to DeepSeek. Same local checkout and branch
codex/wr1200js-service-webui, published HEAD13ce368. Acceptance by DeepSeek
is not yet verified. DeepSeek must explicitly accept before becoming writer.
Do not use a fresh clone: extensive uncommitted/untracked work exists only here.
Read AGENTS.md and docs/AGENT-HANDOFF-RULES-SOL-DEEPSEEK.md first; preserve
all existing work and use one writer only. Goal remains paused until resumed.

Supersedes RUNNING markers below: sessions35118/58858 completed. Full79 host
report full79-cycle80-host-20261030/result.json passed83 variants. Fresh79
peer-retirement-chain79-20261030 has72 preparers/584 files byte-identical to
owner-down79-20261030; receipt full79-comparison81.json. Retry81 targeted
report aux-retry81-targeted/result.json passed11 variants. These reports
are under .iot-local-check and are host/source evidence, not target/runtime.

Latest unfinished work: tools/iot/aux-family-close-retry.inc,
prepare-aux-family-close-retry.py and prepare-aux-family-retry-check.py.
Isolated candidate .iot-local-check/aux-retry81-20261030 exposes direct exact-
ticket continuation after unmutated DOWN failure without family/HNAT replay.
Main preparer now includes81, but fresh full81 preparation/replay is pending.
Next verify complete candidate81, then bind recovery scheduling with adapter/
netdev/module lifetime and stop/join. Completion-after-DOWN, uncertain family
failure, first/last auxiliary physical ownership, callback retirement and final
child/root/PCI release are still open. Do not claim IoT production-ready.
No target/firmware build or device validation was established by these tests.
No flash, reboot or router state change without separate owner authorization.
No automatic bulk stage, reset, clean or unrelated commit/push. Sol ceases
editing after this handoff. No DeepSeek process was launched or messaged.

## 2026-10-30 actual auxiliary OPEN-to-CLOSE cycle80 host PASS

Actual APCLI/Monitor OPEN+claim-only dispatcher+owned CLOSE+checked DOWN now
compose in one executable; auxiliary OWNED is created by real OPEN, not seeded.
Strict base/HNAT passed normal/removing/reopen/new-token cycles and uncertain
OPEN/failed CLOSE retention without replay. Main readiness/kernel/IO mocked.
Evidence docs/evidence/WR1200JS-IOT-AUX-OPEN-CLOSE-CYCLE80-HOST-2026-10-30.md.
Full host RUNNING session35118 (.iot-local-check/full79-cycle80-host-20261030).
Fresh whole source79 RUNNING session58858 (.iot-local-check/peer-retirement-chain79-20261030).
Resume exact handles, then compare final source hashes to tested incremental79.
Next exact-ticket continuation of proven unmutated DOWN failure, without
family/HNAT replay, then callback/family/root/PCI retirement. Sol sole writer.
No target/runtime proof, router change, firmware build, dispatch, commit/push.

## 2026-10-30 legacy DOWN79 bypass rejected; full78 host PASS80

No remaining C unclaimed DOWN callers. Pinned legacy DOWN case now rejects
without count/physical-close effects; direct checked-ticket function unchanged.
11 targeted variants passed incl actual owned close/DOWN and native/ABL bridge.
Full78 session35851 terminal exit0:80 passed host variants, full_suite=true.
Evidence docs/evidence/WR1200JS-IOT-VIRTUAL-DOWN-OWNER79-HOST-2026-10-30.md.
Main chain/suite include79; fresh whole79/replay pending. Last fresh76 has69
preparers/584 identical files. All check/preparation sessions terminal.
Next actual OPEN-to-CLOSE cycle creating auxiliary OWNED via real OPEN, then
retained continuation/callback/PCI lifetime binding. No target/runtime claim.
Sol sole writer; preserve work. No router mutation/build/dispatch/commit/push.

## 2026-10-30 virtual UP78 unclaimed bypass rejected; host cases PASS

Source audit found no remaining C VIRTUAL_IF_UP callers. Pinned actual
UP dispatcher now rejects NULL/zero owner before count/hardware/beacon effects.
Actual claim-only case passed strict base/AP host tests for zero/stale/exact/
replayed main and auxiliary claims. Request layout unchanged; target ABI unproved.
Main chain/suite include78. Full78 host RUNNING session35851,
output .iot-local-check/full78-host-composition-20261030. Resume same handle.
Evidence docs/evidence/WR1200JS-IOT-VIRTUAL-UP-CLAIM78-HOST-2026-10-30.md.
Next unclaimed DOWN bypass (no remaining C callers) and full OPEN-to-CLOSE
composition, then retained recovery/first-last close/callback/PCI retirement.
Last fresh source76:69 preparers/584 identical files; last full host76:77.
Sol sole writer. No target/image/runtime acceptance, router change or push.

## 2026-10-30 claimed APCLI/Monitor OPEN77 host PASS; fresh76 identical

Session70190 terminal exit0. Fresh76 has69 preparers/584 files byte-identical
to tested76b; manifest verified (.iot-local-check/full76-comparison77.json).
77b binds APCLI/Monitor OPEN to exact AUX_OPEN claims and checks family ioctl;
late invalidation retains uncertain pins and skips family call if observed
before it. Strict actual three-family OPEN +5 targeted variants passed.
Evidence docs/evidence/WR1200JS-IOT-AUX-OPEN77-HOST-2026-10-30.md.
Main chain includes77; fresh77/full host replay pending. No VIRTUAL_IF_UP C
callers remain, but legacy inline/dispatcher zero-owner fallback still exists.
Next review direct CMD/native/ABL consumers, reject unclaimed bypass, check
OPEN-to-CLOSE composition then bind retained recovery/callback/PCI completion.
All current test/preparation sessions terminal. Sol sole writer; preserve work.
No target build/image/runtime acceptance, router change, commit or push.

## 2026-10-30 full76 host PASS77; fresh source preparation remains live

Session46448 terminal exit0; full76-host-composition-20261030/result.json
confirms77 passed full-suite host variants. No target/runtime acceptance.
Source prep session70190 still live, last at wds-outer; output
.iot-local-check/peer-retirement-chain76-20261030. Resume same handle.
Next compare fresh tree to tested76b when preparation completes. In parallel
migrate APCLI/Monitor OPEN away from zero-owner count fallback, preserving
post-attempt uncertain pins. Full source audit/evidence in
 docs/evidence/WR1200JS-IOT-OWNED76-COMPOSITION-OPEN-AUDIT-2026-10-30.md.
Sol sole writer; all local work preserved. No router change/build/push.

## 2026-10-30 candidate76 composition underway; OPEN bypass confirmed

9 targeted legacy/shared/new-owned/removing variants passed. Legacy fixture
now delegates new endpoint coverage to actual-owned composition tests; mixed
endpoint implementations are rejected. Main chain includes76.
Full76 host RUNNING session46448 (.iot-local-check/full76-host-composition-20261030).
Fresh full source chain76 RUNNING session70190 (.iot-local-check/peer-retirement-chain76-20261030).
Resume these exact handles; do not restart on observation timeouts.
OPEN audit: APCLI/Monitor are the only remaining unclaimed VIRTUAL_IF_UP C
callers; dispatcher zero-owner fallback mutates count outside shared owner.
Next migrate both OPEN wrappers to claim+family-result/uncertain-pin handling,
then remove/reject the unclaimed bypass after complete caller/ABI review.
Evidence docs/evidence/WR1200JS-IOT-OWNED76-COMPOSITION-OPEN-AUDIT-2026-10-30.md.
Close test seeded OWNED records are not live OPEN evidence. Sol sole writer.
No target build, router change, dispatch, commit or push in this step.

## 2026-10-30 isolated owned APCLI/Monitor close76b host PASS

Pinned five-file preparer binds both ndo_stop wrappers to shared family owner
before ioctl, with per-slot device/generation/serial/epoch/token state.
Family failure/DOWN failure retain owner/pin; repeated entry cannot replay.
Actual DOWN atomically rejects stale epoch before count mutation. Strict
actual-wrapper/helper/DOWN host base/HNAT variants passed incl last-close
refusal and reset interleavings. Stronger family identity model also passed.
Evidence docs/evidence/WR1200JS-IOT-AUX-FAMILY-OWNER76-HOST-2026-10-30.md.
Candidate .iot-local-check/aux-owned76b-20261030 is isolated; main chain ends75.
Next adapt legacy endpoint fixtures and broad composition; bind/verify actual
APCLI/Monitor OPEN registry acquisition, same-ticket deferred recovery and
last-close/callback/PCI completion. No target ABI/runtime acceptance; model
seeded OWNED records are not real OPEN proof. All test sessions terminal.
Sol sole writer. No router mutation, firmware build, dispatch, commit or push.

## 2026-10-30 exact removing auxiliary owner75 admission PASS

Fixed candidate composition refusal: mark-removing before dev_close made
old count-match reject the same WDS OWNED record. New pinned aux-close header
permits only that exact still-owned target; refuses foreign removal/duplicate
identity/post-unregister/count mismatch. General registry checker unchanged.
Strict candidate assertion and6 targeted WDS/aux variants passed. First
old-header test failed due quoted include precedence; candidate-copy rerun
passed. Failed process terminal; no live work remains from these checks.
Evidence docs/evidence/WR1200JS-IOT-AUX-REMOVING-ADMISSION75-HOST-2026-10-30.md.
Main chain includes75; fresh full75 not yet prepared/replayed. Last full74
host76, source composition70. Next bind APCLI/Monitor family-close owner and
same-ticket continuation; callback/PCI retirement remains incomplete.
Sol sole writer. No target/runtime/router change, commit or push.

## 2026-10-30 full74 host replay PASS76

Session42924 terminal exit0; full74-host-resumed-20261030/result.json confirms
76 passed variants, full_suite=true. Target/runtime/lifecycle acceptance false.
This supersedes the running marker below. Main preparer includes74; fresh
whole-chain74 source preparation still pending. Last reproduced full70 tree
has65 preparers/582 files. Evidence docs/evidence/WR1200JS-IOT-RESUMED74-RECOVERY-BOUNDARY-2026-10-30.md.
Next exact-generation/serial family-close owner binding before APCLI/Monitor
side effects, same-ticket continuation, callback retirement and PCI receipts.
No router change, firmware build, dispatch or publication. Sol sole writer.

## 2026-10-30 resumed after publication13ce368; candidate74 integration

Goal active again. Added74 to main preparer/common suite.9 targeted variants
passed; recovery-owner and family-stage models also passed, without worker
binding. APCLI MLME and Monitor RX-filter side effects require separate
family result/ownership and exact-ticket continuation before callback release.
Full74 replay RUNNING session42924, output .iot-local-check/full74-host-resumed-20261030;
last poll confirmed live. Resume same handle, do not restart for timeout.
Evidence docs/evidence/WR1200JS-IOT-RESUMED74-RECOVERY-BOUNDARY-2026-10-30.md.
Last full source reproduction70 remains65 preparers/582 identical files;
fresh full74 prep not yet run. Next exact-owner family-close binding and
retained callback retirement. No target/runtime claim. Sol sole writer.
No router mutation, firmware build, dispatch, commit or push this step.

## 2026-10-30 auxiliary remove73 close refusal guard PASS

Pinned two-file candidate adds explicit APCLI/Monitor close + actual registry
IDLE check before unregister/free. Failed ndo_stop now retains netdev and
vendor state; RTNL is released. MBSS has existing IDLE/terminal admission.
Strict actual-remove/actual-helper host test passed;7 adjacent/seam variants
also passed. Evidence docs/evidence/WR1200JS-IOT-AUX-REMOVE-CLOSE73-HOST-2026-10-30.md.
Success-path callback retirement remains UNPROVED; retained failure retry is
UNBOUND. Do not treat this guard as completion of child teardown.
Main preparer includes73; fresh full73 not yet prepared/replayed. Last full
verified composition70:65 preparers/582 identical files,72+1 host results.
Next common callback retirement evidence and retained family completion,
then root/final-work/PCI release. Sol sole writer; preserve all local changes.
No target build, router change, dispatch, commit or push in this step.

## 2026-10-30 full70 fresh composition verified; child retirement72 next

Session31378 ended exit0. Fresh main chain:65 preparers/582 files, all bytes
identical to tested incremental70d and manifest hashes match. Evidence
.iot-local-check/full70-comparison72.json and
 docs/evidence/WR1200JS-IOT-FULL70-AND-CHILD-RETIREMENT72-2026-10-30.md.
72 full-suite host variants plus1 separate injected-exit variant passed on
these bytes. Chain now ends70, not64; draft65 remains excluded. No target,
image or runtime acceptance. No production overlay installation claimed.
Next concrete gap: MBSS/APCLI/Monitor still free after unregister without
matching registry callback-retirement receipt; WDS instead retains and fails.
Bind common callback retirement evidence and per-family completion/retry,
then root/final-work/physical PCI release receipts. Never invent completion
from a successful remove return. WSL probe returned installer usage exit1;
no target toolchain established. Sol sole writer; all local work preserved.
No router changes, firmware build, dispatch, commit or push in this step.

## 2026-10-30 caller71 and composed host replay PASS; fresh preparation RUNNING

Host suite on incremental70d passed72 variants (full70-host-attempt3-20261030).
A separately registered injected-exit check passed1 variant; do not call this
one73-variant report. Caller err2/HIF unwind passed every enabled OS_ABL init
failure in base/extended fixtures. Correct CONFIG_ANDES_SUPPORT is covered.
Updated old void-return host stub/anchor; initial attempt1 failed that obsolete
verifier, then12 targeted checks and full72 passed. No target/runtime proof.
Evidence docs/evidence/WR1200JS-IOT-NETTASK-CALLER71-HOST-2026-10-30.md.
Main preparer now includes67–70 after64 (draft65 excluded). Fresh preparation
is RUNNING via exec session31378, output .iot-local-check/peer-retirement-chain70-20261030,
source .iot-local-check/full-driver-overlay4-20261029. Last poll confirmed live.
Resume that handle or inspect terminal manifest; do not restart on observation
timeout. Next compare all prepared files to incremental70d, inspect terminal
manifest and reconcile test scope before target validation. PCI terminal
receipt and child callback retirement remain open. Sol sole writer.
No router change, firmware build, dispatch, commit or push in this step.

## 2026-10-30 network-task partial initialization70 host PASS

Confirmed ignored OS_ABL allocation failures; isolated pinned preparer now
checks each task init, records successes and reverses partial cleanup before
releasing init reservation. No scheduling on failure; retry is tested.
Strict native base/extended and OS_ABL every-enabled-failure base/extended
fixtures passed on70d.70c exposed macro index double evaluation, corrected
with a local task pointer. Correct CONFIG_ANDES_SUPPORT also passed69 rerun.
Evidence docs/evidence/WR1200JS-IOT-NETTASK-INIT70-HOST-2026-10-30.md.
Extracted mocked host tests only; no target/ABI/runtime claim. Chain ends64;
67–70 isolated. Next whole-caller unwind/composed fixture adaptation; terminal
PCI receipt and child callback retirement still open. Sol sole writer.
No router change, build, dispatch or publication in this step.

## 2026-10-30 network tasklet release69 host checks PASS

Isolated69c reserves initialization under the tasklet owner lock and requires
joined/blocked/drained/no-init before permanent release/reopen fencing.
Fresh strict host tests passed base/extended scheduling and base/WSC release
gates; added duplicate-init reservation and close refusal assertions.
Evidence: docs/evidence/WR1200JS-IOT-NETTASK-RELEASE69-HOST-2026-10-30.md.
Mocks are not target ABI or kernel concurrency proof. Chain still ends64;
67–69 isolated,65 excluded. Next adapt composed fixtures and review init
failure/OS_ABL paths before coherent target validation. PCI terminal receipt
and child callback retirement bindings remain open. No device changes.
Standalone model/test/report published as fec63dd; remaining changes local.
Sol sole writer; full delivery goal remains incomplete.

## 2026-10-30 network tasklet schedule68b bound in isolated candidate

Pinned seven-file transform from67 binds35 network-cookie scheduling sites
with dedicated IRQ-safe owner/lock, waitqueue and joined marker. Submission
API outside lock; exit blocks/drains (5000ms, process context), preserves
early kills, returns failures via67. Repeated exit idempotent; init refuses
live/unjoined before mutations and opens only after initialization.
Actual helper/Init/Exit base+extended feature host variants passed strict GCC;
wait/locks/alloc/scheduling and callback ABI mocked, no target/ABL proof.
Evidence docs/evidence/WR1200JS-IOT-NETTASK-SCHEDULE68-HOST-2026-10-30.md.
Next final owner proof in adapter-release gate, lock-order/init-unwind review,
full fixture adaptation/replay and coherent target compile. Existing OS_ABL
allocation failure handling remains unverified; init relies on outer serial.
67/68 isolated; chain ends64,65 excluded. No router/build/dispatch/commit/push.
Sol sole writer; preserve all dirty work.

## 2026-10-30 net-task exit67 result propagation prepared; injected close test PASS

Pinned four-file prepare-nettask-exit-result.py from64 changes declaration +
PCI/RBUS/SDIO definitions to INT and checks all3 direct calls. Early failure
stops init/close teardown; checked records stage3, legacy retains latch.
Extracted both actual close bodies/wrappers passed strict host failure/retry/
success checks before MlmeHalt/management/ring release; init/SDIO source-only.
Evidence docs/evidence/WR1200JS-IOT-NETTASK-EXIT67-HOST-2026-10-30.md.
Scheduling fence/drain still UNBOUND. Producers may hold LockInterrupt/vendor
locks: dedicated short IRQ-safe submission lock, no waiting there. Network
cookie tasklets separate from MCU/recovery/polling lifecycles.
67 isolated, chain ends64; latest full64/68 host checks. Next bind producer
leases + block/drain before preserved early kill and init/reopen ownership.
No target/runtime/router/build/dispatch/commit/push. Sol sole writer.

## 2026-10-30 resumed: tasklet schedule66 model and expanded inventory PASS

Confirmed full64 completed61 preparers/580 identical files and68 host variants.
Draft65 excluded: moving kill late loses early RX drain before management
teardown. Preserve early join; first fence all scheduling submissions.
Expanded inventory44 lexical APIs/8 files (36 macro,2 direct tasklet,4 work,
2 delayed work); wrapper/optional/recovery sites need lifecycle classification.
New tasklet-schedule-owner.h + strict GCC model passed admission/block/drain/
reopen/corruption cases. Counts submissions only; actual callback kill still
required. Driver binding ABSENT, not a completed synchronization fix.
Evidence docs/evidence/WR1200JS-IOT-TASKLET-SCHEDULE66-HOST-2026-10-30.md.
Next classify/bind producer calls and early join with shared IRQ-safe owner,
audit lock order and feature/ABL branches; MCU/recovery lifecycles separate.
Chain ends64;65 excluded. No target/runtime/router/build/dispatch/commit/push.
Sol sole writer; goal active, all dirty work preserved.

## 2026-10-30 private netdev_ops lifetime64 corrected; targeted checks PASS

Pinned six-file preparer moves private ops free from Detach to common netdev
Free, clears pointer before free_netdev, removes duplicate create/name/MBSS/
AP-client/WDS/Monitor/PCI failure frees. Registered callers must finish returned
RTNL/reference drain first; arbitrary external misuse not newly enforced.
Actual Create/Detach/Protect/Free fixture passed registered deferred release,
NULL/allocated ops failures, allocation/name failures and successful creation.
Three selected suite checks plus pinned kernel/RTNL source verifier passed.
Evidence docs/evidence/WR1200JS-IOT-NETDEV-OPS-LIFETIME64-HOST-2026-10-30.md.
Next vendor callback/reference retirement, family completion, cold unwind and
full regression. Step63 is source audit, not transform. Chain includes64 but
latest full replay58. No target/runtime/router/build/dispatch/commit/push.
Sol sole writer; preserve all dirty work.

## 2026-10-30 kernel netdev retirement63 source semantics verified

Read existing pinned donor archive, confirmed Makefile4.4.198; extracted only
dev.c/rtnetlink.c/netdevice.h to new scratch, recorded member hashes. New
check-kernel-netdev-retirement.py passed exact hashes/source-order checks.
rtnl_unlock -> netdev_run_todo -> RCU barrier + accounted-ref drain before
return. WDS receipt follows returned Protect(0); NETREG_UNREGISTERED alone
is insufficient (set before wait), and wait can be indefinite. Vendor raw
refs/timers/tasks/hardware/DMA not covered by this kernel-accounted proof.
Evidence docs/evidence/WR1200JS-IOT-KERNEL-NETDEV-RETIREMENT63-SOURCE-2026-10-30.md.
Next netdev_ops allocation is currently freed inside Detach BEFORE final
returned RTNL/reference drain; audit/defer its ownership across all probe/
create/free paths, then vendor retirement and family completion. Do not
replace existing kernel drain with invented callback counter or arbitrary sleep.
No driver/kernel change or target/runtime/router/build/dispatch/commit/push.
Latest full replay58. Sol sole writer; preserve all dirty files.

## 2026-10-30 PCI published child snapshot62 begin bound; two host checks PASS

After WORK_JOINED, before parent detach, snapshot exact published registry
families under transition lock with retire/inflight/identity checks. Multiple
MBSS records aggregate one bit. Begins DRAINING only; no close/completion claims.
Two strict host checks passed snapshot cases and actual preceding join/order.
Evidence docs/evidence/WR1200JS-IOT-PCI-CHILD-SNAPSHOT62-HOST-2026-10-30.md.
Audit: WDS retains allocation after unregister pending callback reaper; MBSS/
AP-client/Monitor still unregister/free without equivalent bound final registry
receipt. Do not accept successful return as callback retirement. Next reconcile
those family lifetime paths and vendor/registry coverage before completion
bits, root callbacks and final PCI receipt. Cold unwind also open.
62 in chain, latest full replay58. No target/runtime/router/build/dispatch/
commit/push. Sol sole writer; preserve all dirty files.

## 2026-10-30 PCI first-work receipt61 bound after actual cancellations

Pinned prepare-pci-first-work-receipt.py checks stop transition and records
WORK_JOINED only after actual two sync cancellations, reconciliation, stop
fence and zero deferred owners. Extracted block host test passed missing
stop, injected owner, successful receipt and replay refusal. Kernel work mocked.
Evidence docs/evidence/WR1200JS-IOT-PCI-FIRST-WORK61-HOST-2026-10-30.md.
Audit: wr_iot_children is initialized but never advanced by real removals.
Do NOT infer child/root callback completion from removal return. Next exact
family teardown/callback ownership, root detach, final join and physical
observation before terminal receipt. Cold probe/free separate. Chain/test
includes61; latest full replay58, no full59-61 yet. No target/runtime/router/
build/dispatch/commit/push. Sol sole writer; preserve all dirty work.

## 2026-10-30 initialized pre-destructor release60b bound; four host checks PASS

Pinned controller gate before first destructor. Requires terminal PCI release
receipt + actual modeled radio/child/registry/join conditions, then checks peer
owners under MacTabLock and permanently poisons table admission on claim.
No nested locks/waits; relies on terminal receipt never being revoked.
Four strict host variants passed: actual helper with/without WSC, plus actual
controller/native/ABL seams with early-gate refusal before all destructors.
Audit observes pre-destructor order but release remains UNACCEPTED. PCI path
currently does not produce terminal receipt; cold direct-free paths separate.
Evidence docs/evidence/WR1200JS-IOT-PRE-DESTRUCTOR-RELEASE60-HOST-2026-10-30.md.
Next real final retirement receipt/callback joins/physical observation, cold
probe ownership, target ABI and full composed checks. Latest full replay58;
59/60 in chain not full-replayed. No router/build/dispatch/commit/push.
Sol sole writer; preserve all dirty files.

## 2026-10-30 fallible adapter-free result59 prepared; native/ABL seams PASS

Pinned prepare-adapter-free-result.py changes native/ops/definition to BOOLEAN,
propagates three free and two controller-exit call results. Two strict host
variants passed actual controller body + exact caller seams with free mocked.
Source audit observes propagated result and no bare direct release calls,
but pre-destructor release claim is still FALSE. Test explicitly observes
controller destructors still precede free. Existing early free failures can
follow partial lock destruction: no blind retry or recovery acceptance.
Evidence docs/evidence/WR1200JS-IOT-ADAPTER-FREE-RESULT59-HOST-2026-10-30.md.
Next pre-destructor retirement/admission fence, cold-probe versus initialized
release ownership, callback/peer/task/registry/DMA proof and coherent target ABI.
59 in chain but not full-replayed; latest full58. No target/runtime/router/
build/dispatch/commit/push. Sol sole writer; preserve all dirty files.

## 2026-10-30 full58 replay +61/2/23 host PASS; adapter release OPEN

Full chain completed56 preparers/578 files, rejected57 excluded. Fresh58
versus incremental58 differs ONLY by marker macro in delete include; all C
bodies identical. Full61 suite passed on incremental58 (including five ABL/
DIAG/HNAT bridge variants); both resume contracts rerun on fresh58 passed;
23 composed WDS tests passed on fresh58. Seven ASTs and targeted diff check PASS.
Evidence docs/evidence/WR1200JS-IOT-FULL58-HOST-AND-RELEASE-AUDIT-2026-10-30.md.
Existing PCI release source preflight still exits1. New lexical audit lists
five unchecked release calls (includes optional SDIO source, not board enable).
RTMPFreeAdapter native/OS_ABL ABI is VOID; RtmpRaDevCtrlExit performs destructors
before free and returns TRUE without refusal propagation. A late guard in
free alone would be unsafe. Next claim before first controller destructor,
propagate status through ABI/callers, distinguish cold probe unwind, prove
peer/task/callback/registry/DMA retirement and fence new admission.
No target/image/kernel/runtime acceptance or router/build/dispatch/commit/push.
Sol sole writer; HEAD9cb154a; preserve all dirty files.

## 2026-10-30 replacement deletion execution58 preserves WDS resume

Built from56, excluding rejected57. New adapter synchronous deletion flag
spans full normal body/tails, then clears on return; existing per-entry WDS
retention/recovery unchanged. Parent-reset serial forwarded and not released.
Related insertion/WDS/reset/open/close/repeater/EZ gates check flag under
MacTabLock. Exact twelve-file pins in prepare-peer-delete-execution.py.
Previously failing resume contract now passes, including lease and parent
serial checks. Five admission/close/reset checks plus seven checkpoint/reset/
lease variants passed strict GCC. Updated stale extractor/type anchors.
Evidence docs/evidence/WR1200JS-IOT-DELETE-EXECUTION58-HOST-2026-10-30.md.
Chain includes58, excludes57; no fresh full58/default suite yet (latest54).
Next full vendor delete/body integration and consolidated regression, then
adapter-release/remaining writers and callback/DMA lifetime. Host synthetic
checks do NOT prove target/runtime. No router/build/dispatch/commit/push.
Sol sole writer; preserve all dirty work.

## 2026-10-30 delete57 REJECTED: WDS resume regression reproduced

New check-peer-delete-resume-contract.c compiled strict GCC and exited1 on57:
retained ordinary table owner blocks the existing WDS checkpoint retry before
its body (calls=1). This is regression evidence, NOT passing acceptance.
Removed57 from preparer chain; preserved all draft source/scratch/tests.
Chain ends56, latest completed full replay54. Do not publish/install57.
Updated docs/evidence/WR1200JS-IOT-NORMAL-DELETE57-HOST-2026-10-30.md with
explicit rejection; prior three narrow test passes did not cover recovery.
Next implement separate synchronous deletion writer lease/count, preserve
per-entry WDS checkpoint recovery and parent-reset serial; run this contract
first, then full vendor/delete/reset checks. Adapter release still open.
No router/build/dispatch/commit/push. Sol sole writer; all files preserved.

## 2026-10-30 whole ordinary deletion57 reserved; three selected checks PASS

Pinned prepare-peer-normal-delete.py renames unchanged private body and binds
wrapper. Ordinary deletion reserves exclusive table serial through unlocked
tails; parent-reset deletion forwards exact parent serial without releasing it.
Failure retains ordinary owner (recovery NOT implemented). Invalid input is
rejected before reservation. Close wrappers reject unrelated active table owner
before APShutdown while permitting own close-serial retry. Raw reset gate
already blocks active table ownership.
Three selected strict GCC checks passed: wrapper/private body mock, actual
close paths and actual reset fragment. Evidence:
docs/evidence/WR1200JS-IOT-NORMAL-DELETE57-HOST-2026-10-30.md.
Next update broad extractors for renamed deletion body, test whole vendor
delete/reset call chain and retained-failure recovery; adapter release open.
Steps55-57 in chain but full replay latest54. No target/runtime/router/build/
dispatch/commit/push. Sol sole writer; preserve all local changes.

## 2026-10-30 whole normal insertion56 counted through unlocked tail

Source confirmed insertion and deletion finishing after MacTabLock release.
Pinned prepare-peer-normal-insert.py replaces only public insertion wrapper:
executor-idle check plus balanced table transaction spans full private body
and unlocked TX-burst tail. Explicit startup WDS API unchanged.
Three targeted checks passed: new wrapper (private body mocked), existing
private peer-ready order and startup lease gate. Strict GCC.
Evidence docs/evidence/WR1200JS-IOT-NORMAL-INSERT56-HOST-2026-10-30.md.
Next ordinary deletion: cannot reuse transaction count blindly because its
existing gate rejects nonzero count; preserve exact reset-owned serial.
Adapter-release and slot/callback/DMA lifetime still unproved. Steps55/56
added to chain but no full replay yet; latest full54. No target/firmware/
runtime/router/build/dispatch/commit/push. Sol sole writer; preserve dirty files.

## 2026-10-30 counted WDS/close/reset exclusion55 checked locally

Pinned prepare-peer-wds-executor.py applied to verified full54. Normal WDS
checks executor idle atomically with transaction enter; close wrappers check
transaction count before executor claim; raw reset checks count/table admission.
Three selected host checks passed both directions before body/APShutdown/raw
work and verified pending reset executes after WDS count reaches zero.
Evidence docs/evidence/WR1200JS-IOT-WDS-EXECUTOR55-HOST-2026-10-30.md.
Added55 to chain; no fresh full55 replay yet. Latest full54 remains accepted
for host composition only. Ordinary non-WDS insertion/deletion, remaining
radio admissions and adapter-release/callback/DMA lifetime still open.
No target/image/runtime/router/build/dispatch/commit/push. Sol sole writer.

## 2026-10-30 consolidated full54: 53 preparers,576 files; 54+4+23 host checks PASS

Fresh full chain from full-driver-overlay4-20261029 completed all53 steps to
peer-retirement-chain54-20261030/peer-reset-executor. All576 files match
incremental54. Stages51-54 now included in prepare-peer-retirement-chain.py.
Broad54 extracted variants passed; four new executor tests passed separately
with --only (current default suite includes58); composed WDS23 passed.
Preserved old native/OS_ABL, checked/physical/MBSS close assertions using shared
synthetic adapter support and actual private bodies plus executor wrappers.
Updated stale APShutdown extractor anchor; corrected run passed. Ten Python
scripts AST-parse and targeted git diff --check passed.
Evidence docs/evidence/WR1200JS-IOT-FULL54-HOST-COMPOSITION-2026-10-30.md.
No claim of one default58 run or target ABI/kernel/DMA/runtime acceptance.
Next: remaining peer/radio admissions and adapter-release lifetime claim;
configured WDS retained-failure recovery and config/address lifetime remain.
No router/build/dispatch/commit/push. HEAD9cb154a; Sol sole writer; preserve dirt.

## 2026-10-30 reset executor54 bound; target still unverified

Public raw reset wrapper now claims same MacTabLock-protected executor as
both close paths. Running/retained close defers reset without losing pending
request; raw reset excludes close; failed software ticket retirement retains
execution fence. No spinlock across raw work; RTNL try-lock preserved.
Passed actual reset-fragment fixture (including retirement failure), both-close
regression and extended model with strict GCC. Initial failed injection used
DOWN radio and never reached raw reset; corrected UNVERIFIED fixture passed.
Evidence docs/evidence/WR1200JS-IOT-RESET-EXECUTOR54-HOST-2026-10-30.md.
Candidate .iot-local-check/peer-reset-executor54-20261030 from pinned53.
Next cover remaining peer/radio admissions and adapter-release lifetime;
normal peer writers not serialized by this guard. Stages51-54 local, not in
consolidated chain. No target/full replay/runtime/router/build/commit/push.
Sol sole writer; preserve all dirty files.

## 2026-10-30 close executor53 bound locally; composed host checks PASS

Added shared adapter close executor around BOTH legacy and checked function
bodies. MacTabLock protects admission/completion, never held across body work.
Partial checked close retains exact serial; only matching retry can continue.
Initial invalid ticket with no effects releases new claim; partial legacy
failure retains exclusion. Main-open ioctl checks same executor atomically.
Passed strict GCC model, extracted BOTH-body competing-call fixture and actual
main-open dispatch fixture; three Python scripts parsed. Evidence:
docs/evidence/WR1200JS-IOT-CLOSE-EXECUTOR53-HOST-2026-10-30.md.
Candidate .iot-local-check/peer-close-executor53-20261030 from pinned52.
Next: all-radio reset/admission serialization and adapter-release lifetime
claim; RTMPFreeAdapter still frees MacTabLock without peer-owner gate.
Host primitives/layout/hardware mocked; no kernel concurrency, MIPS/OS_ABL,
full replay, DMA/callback/runtime acceptance. Stages51-53 not in main chain.
No router/build/dispatch/commit/push. Sol sole writer; preserve all dirty work.

## 2026-10-30 legacy close52 candidate: replay and reopen checks passed locally

Pinned prepare-peer-legacy-close.py generated peer-legacy-close52-20261030
from51b. Adapter latch uses MacTabLock, rejects partial legacy retry and makes
completed close idempotent. Actual main-open dispatch refuses retained latch;
only admitted reopen after completed close clears it. Legacy dequeue polling
is bounded; failed radio-off now returns failure before freeing rings.
Actual legacy function host fixture passed APShutdown failure/retry, completed
close/retry, radio-off refusal and dequeue timeout. Actual ioctl dispatch test
passed retained-close exclusion, wrong-device preservation and admitted reopen.
Checked-close regression passed on52. GCC C11 O2 Wall Wextra Werror.
APShutdown, layouts, lock primitives, tasks and hardware remain mocked.
Important remaining gap: legacy latch and checked/radio transition admission
are not yet one atomic owner; check-then-unlock alone does not prevent races.
RTMPFreeAdapter directly frees MacTabLock without peer-owner admission. Need
shared lifecycle claim and release/callback/DMA proof before target acceptance.
No target build/full replay/runtime/router changes/commit/push in this step.
Sol sole writer. Preserve dirty work; stages51/52 not yet in consolidated chain.

## 2026-10-30 close-table51b: checked-close refusal replay fixed locally

Found hold refusal after APShutdown left shutdown_stage zero, permitting replay.
prepare-peer-close-table.py now marks checked-close refusal stage3.
Fresh peer-close-table51b-20261030 generated from pinned50b.
New prepare-peer-close-path-check.py extracts actual checked close and table
helpers into synthetic AP/PCI fixture. PASS: reservation during MlmeHalt,
management join, ring free and UserCfgExit; join-failure retry preserves serial;
completed-close seal blocks normal admission; explicit reopen advances serial;
post-APShutdown hold refusal does not replay stage zero.
Seven focused owner/reset/open/dispatch/startup/WDS tests also passed strict
GCC C11 O2 Wall Wextra Werror. APShutdown/hardware/locks/layout remain mocked.
No target, DMA, module ABI, full replay or runtime acceptance. Legacy close
refusal/retry and adapter-release binding remain next; stage51 not in chain.
No router/build/dispatch/commit/push in this step. Sol sole writer.

## 2026-10-30 publication confirmed: 9cb154a

Published five isolated experimental peer-ownership model/test/report files.
Both standalone host tests passed strict GCC C11/O2/Wall/Wextra/Werror.
Remote branch verified at 9cb154a37a08d44331022f88312930838ecf841e.
See docs/evidence/WR1200JS-IOT-OWNER-MODELS-PUBLICATION-2026-10-30.md.
Other dirty files remain local; candidate51 binding is unfinished and unpublished.
No target/runtime acceptance, router changes or manual build dispatch.
Sol remains sole writer; continue complete-close fixtures and adapter-release review.

# Current handoff — 2026-10-25 (updated)


## 2026-10-30 early outer-open/config table admission50b bound locally

Pinned prepare-main-open-table-claim.py binds BEGIN in rt28xx_open before
WIFI_DIAG/profile/IRQ effects; refusal returns -EBUSY without init unwind.
Explicit request pointer added consistently to rt28xx_init function, native
prototype and OS_ABL ops field. Inner CONFIG_CHECK rejects stale reservation
before hardware/tasks/config mutations. Reservation spans config/table clear;
START/DONE releases it before ordinary APStartUp (or final success for non-AP).
Outer error attempts FAIL before its own IRQ cleanup; partial init retains owner.
Config completion does NOT prove radio readiness. Configured WDS uses separate
interface open48, so main does not wait on closed WDS.

Admission seam/client/dispatch and mock ops type test passed, not full vendor
open/init execution. Previous53 regression variants passed on candidate50.
Latest50b differs ONLY by explicit peer-open-request.h include in rt_os_net.h;
admission test rerun passed. Evidence:
docs/evidence/WR1200JS-IOT-MAIN-OPEN-CLAIM50-HOST-2026-10-30.json.
Added50 to chain and admission check to suite (next suite has54 variants).
No fresh full50 replay yet; last full49 (48 preparers,571 files). Target ABI/
modules/kernel concurrency/runtime unverified; coherent target rebuild required.
Next protect full shutdown clear and adapter release; failed WDS-open recovery
and config/address writer lifetime still open. Latest scratch
main-open-table-claim50b-20261030. No router/firmware build/dispatch/commit/push.
Sol sole writer; HEAD/remote9af5697. Preserve all existing dirty work.


## 2026-10-30 consolidated candidate49: full replay +53/23 host checks PASS

Added draft41/42/44-49 preparers to prepare-peer-retirement-chain.py. There are
48 actual preparer steps (protocol43 is a header, not a separate transform).
Fresh peer-retirement-chain49-20261030/wds-table-transaction completed all48;
ALL571 files match the incremental49 candidate. Last full replay is now49.

53 extracted host variants passed on fresh candidate (full49-host53-20261030),
plus23 composed variants (full49-composed-20261030). Strict optimized GCC.
Initial broader run stopped on old peer-ready extractor public insertion anchor;
changed to actual private insertion body without weakening initialization/order
assertions. Updated APShutdown/legacy close fixture expectations for adapter-
owned MacTabLock lifetime. Prior42 baseline then passed, followed by expanded53.
Added new owner/reset/phase/dispatch/startup/WDS transaction/configured-loop/
actual WDS-only ndo_open checks. Five changed Python scripts parse successfully.
Evidence: docs/evidence/WR1200JS-IOT-FULL49-HOST-COMPOSITION-2026-10-30.json.

These are source transforms and mocked host tests, NOT target/module/firmware,
real kernel concurrency/DMA or router acceptance. Outer open/config clear
admission, full table clears/free bypass, failed WDS-open owned-state recovery
and configuration/address writer lifetime remain open. Next work can use this
consolidated verified tree, not disconnected draft scratch. No router/build/
dispatch/commit/push. Sol sole writer; HEAD/remote9af5697. Preserve dirty files.


## 2026-10-30 synchronous WDS/table exclusion49 locally bound

Added table owner transactions counter and balanced synchronous enter/leave.
Exclusive reset begin now refuses any active normal WDS transaction; ordinary
zero-token delete also refuses while count nonzero. Overflow/underflow poison
admission. This is structured synchronous balance, NOT callback completion
identity. New pinned prepare-wds-table-transaction.py wraps ALL normal identity
transaction callers, including configured interface open, around vendor body,
finish tails and dev_put. Startup-ticket path still relies on its separate
claimed lease. No MacTabLock held across vendor work.

Latest scratch wds-table-transaction49-20261030. Eight strict optimized targeted
host checks passed: actual new wrapper/delete gate with mocked vendor body,
owner/reset fragment, phase, dispatch, startup insertion/transaction and
configured-open helper regressions. Nested count balance, failure, reset/delete
refusal and counter poison covered. No full vendor body/kernel concurrency
proof. Evidence: docs/evidence/WR1200JS-IOT-WDS-TABLE-TRANSACTION49-HOST-2026-10-30.json.

Next consolidate draft41-49 into full preparer chain and adapt/exercise earlier
whole-body extractors before further lifecycle edits. Last full replay remains40;
none of draft41+ is in main chain yet. Full table clear/reopen/free admission,
config/address mutation lifetime and failed WDS-open recovery remain open.
No firmware build/dispatch/router/commit/push. Sol sole writer; HEAD9af5697.


## 2026-10-30 configured WDS completion tied to exact interface open48

Architecture correction: retaining MAIN startup waiting for closed WDS would
cycle, because WdsVirtualIF_open requires nonzero physical vendor count and a
ready main radio. No background worker/global main wait added. New pinned
prepare-wds-configured-interface-open.py binds configured peer completion
AFTER exact WDS record OWNED, BEFORE HNAT/queue start. New helper passes exact
device/generation into counted transaction; transaction rechecks identity before
dev_hold/body. Unconfigured/lazy interface does not invent a peer.

Two strict optimized host checks passed: actual helper with mocked lower
transaction and whole actual WDS ndo_open with mocked configured helper.
Configured failure keeps module pin/count/owned record and suppresses HNAT/
queue. Failed-open recovery is NOT implemented; no guaranteed ndo_stop on this
failure. Original three-family fixture rejected existing legacy APCLI open;
added explicit --wds-only mode, kept its claim assertions, no APCLI/Monitor
verification claimed. Evidence:
docs/evidence/WR1200JS-IOT-WDS-CONFIGURED-OPEN48-HOST-2026-10-30.json.

Latest generated scratch wds-configured-open48-20261030; draft48 outside full
chain. Next reconcile failed-open ownership/recovery and config/address writer
lifetime, then main open/config clear ownership/full table clears. Normal WDS
tails vs reset owner exclusion remains open. No whole vendor transaction,
broad regression, target/runtime acceptance. Last full replay40. No router/
firmware build/dispatch/commit/push. Sol sole writer; HEAD/remote9af5697.


## 2026-10-30 checked configured WDS loop47 and first-open ordering gap

Added pinned prepare-wds-startup-loop.py, scratch wds-startup-loop47-20261030.
New wr_iot_wds_startup_table takes explicit ticket, verifies STARTUP before and
after loop, passes ticket to startup transaction and returns FALSE on required
peer failure. Legacy AsicUpdateWdsRxWCIDTable remains text-equivalent, including
continue-on-failure behavior. Whole legacy/checked loop host fixture passed
-O2 -Wall -Wextra -Werror; mocked lower insertion, not whole vendor execution.
Cases: invalid slots, no active entries, lazy PHY CCK/OFDM/HTMIX, stop vs continue,
stale/null ticket and final retained phase. Evidence:
docs/evidence/WR1200JS-IOT-WDS-STARTUP-LOOP47-HOST-2026-10-30.json.

Source assertions confirm first-open gap: inner rt28xx_init/APStartUp precedes
outer RT28xx_WDS_Init; counted transaction requires published WR_REF_OWNED WDS
record. Do NOT simply wire checked loop into APStartUp and declare success.
Next explicit pending/deferred configured-peer completion after record ready,
with exact open identity and adapter/netdev references; no registry bypass or
false ready state. APStartUp/outer open binding still absent. Full clear/free,
normal WDS tail/reset exclusion, broad regression and target compile remain
open. Draft47 not in full chain; last replay40. No router/build/commit/push.
Sol sole writer, HEAD/remote9af5697. Preserve all dirty/scratch files.


## 2026-10-30 WDS startup transaction46b lease binding

Pinned prepare-wds-startup-transaction.py adds explicit
wr_iot_wds_insert_startup. It claims exact open insertion lease under MacTabLock,
passes ticket/lease through counted WDS transaction into startup MAC insertion,
then ends lease only after finishing tails and dev_put. Normal transaction
wrapper supplies NULL/0. No waiting or nested MAC/transition locks added.
Failed transaction retains open owner. Found result-after-retention hazard:
46b rechecks open phase after transaction so a peer pointer cannot be returned
as success after the open was retained during the body. Older46 scratch lacks
that final phase check; latest is wds-startup-transaction46b-20261030.

Four strict optimized host checks passed: wrapper (lower counted body mocked),
phase owner, dispatch and startup insertion. Source assertions verify ticket
flow and finishing/dev_put order. Whole vendor WDS body/parallel lifetime NOT
executed/proved. Evidence:
docs/evidence/WR1200JS-IOT-WDS-STARTUP-TRANSACTION46-HOST-2026-10-30.json.
Next bind APStartUp/configured loop and outer open handoff. New startup entry
has no APStartUp caller yet. Check record readiness before WDS netdev publication;
normal WDS tail vs reset ownership also remains open. Full clear/free gates,
broad regression/extractor adaptations and target build absent. Draft stages
outside full chain; last replay40. No router/build/commit/push; Sol sole writer.


## 2026-10-30 explicit startup insertion45b, one-use authorization

New pinned prepare-peer-startup-insertion.py splits original insertion into
private wr_iot_mac_insert_entry plus unchanged public signature supplying
NULL/0 and new wr_iot_mac_insert_startup_wds fixing WDS/AP type with ticket/
lease. Actual private-body gate under MacTabLock precedes entry/timer reset.
Added peer-startup-insertion-gate.inc. Exact device/operation/STARTUP/lease
required; ordinary caller still blocked during reservation. Found replay risk
if same active lease used twice; peer-open-owner.h now tracks lease_admitted
and admission consumes it exactly once. End clears admission, not retained
ownership. Output45b includes updated header; older45 scratch lacks this fix.

Three strict optimized host tests passed: new gate refusal/one-use cases,
phase protocol regression and dispatch regression. Source wrapper/gate-order
assertions passed. No whole insertion execution, target or kernel concurrency
proof. Evidence: docs/evidence/WR1200JS-IOT-STARTUP-INSERTION45-HOST-2026-10-30.json.
WDS caller lease claim/pass and outer open/config handoff STILL ABSENT. Next
bind WDS transaction body with explicit ticket and exact lease cleanup, then
outer startup; do not ambiently authorize other callers. Full clears/free and
insertion extractor anchor adaptations remain open. No full45 replay/broad
regression; draft stages not in main chain, last full40. No router/build/
commit/push. Sol sole writer; HEAD/remote9af5697; all edits local.


## 2026-10-30 resumed: core open-ticket transport44 host checks passed

Latest separate scratch peer-open-transport44-20261030 prepared before pause,
now tested. Added versioned internal peer-open-request.h and actual dispatch
fragment; pinned prepare-peer-open-transport.py binds owner/init/core switch.
Command 0x7f20 appended outside existing enum; previous enum/sentinel text is
identical. Non-null wrq/subcmd refused. BEGIN checks exact main netdevice, zero
count, no live Content entry and no failed unpublished TR setup under MacTabLock.
START/DONE/FAIL validate phase/device/serial; failure retains ownership.

Two strict optimized host checks passed: actual dispatch include with synthetic
adapter/locks and actual extracted core ioctl case. Null/version/size/device,
unknown action, occupied/failed table, stale ticket, premature/active insertion
finish, duplicate, retention and overflow cases covered. Not whole core handler,
OS_ABL binary ABI, callback/DMA quiescence or target proof. Evidence:
docs/evidence/WR1200JS-IOT-OPEN-TRANSPORT44-HOST-2026-10-30.json.
Next bind outer rt28xx_open begin before side effects, carry config/startup
handoff and explicitly pass authorized startup ticket to WDS insertion. These
calls are still ABSENT. Full clear/shutdown/free ownership remains open. Draft
41-44 not yet in full chain; last replay40. No broad regression/firmware build,
router changes, commit or push. Sol sole writer; HEAD/remote9af5697.


## 2026-10-30 open phase protocol43, standalone only

Added peer-open-owner.h and check-peer-open-owner.c. Protocol wraps table owner
with exact device/serial CONFIG -> STARTUP -> completion; ordinary insertion
remains denied, explicit startup caller can claim one serialised insertion
lease. Success cannot finish with active lease. Failure retains table; exact
late lease completion can drain its lease but cannot release retention. Wrong
device, stale operation/lease, duplicate transition/finish and lease exhaustion
fail closed. Caller must hold MacTabLock and pin adapter/netdevice lifetime.
Strict optimized host model test passed; no threading/kernel proof.
Evidence: docs/evidence/WR1200JS-IOT-OPEN-PHASE-PROTOCOL43-2026-10-30.json.
NOT bound into driver/OS_ABL or chain. Next transport ticket through core ioctl
before rt28xx_open side effects, validate config clear phase, explicitly pass
startup ticket to configured WDS path, then protect shutdown/full clears/free.
Latest generated candidate still draft42; last full replay40. No firmware,
router, commit or push. Sol sole writer; HEAD/remote9af5697. Goal incomplete.


## 2026-10-30 outer open/WDS startup admission boundary corrected

Extended audit-peer-reopen-unwind.py and all source assertions passed. Admission
must begin before rt28xx_open side effects, NOT merely rt28xx_init: outer open
already does WIFI_DIAG init, MCU sleep clear, profile load, IRQ request/init;
its generic init-failure path releases IRQ. Rejection must avoid that unwind.

Second verified dependency: rt28xx_init -> APStartUp ->
AsicUpdateWdsRxWCIDTable -> wr_iot_wds_insert_transaction -> MacTableInsertEntry.
Holding a blanket insertion-blocking table reservation through all startup
would refuse configured WDS peers. Do not implement that proposed whole-init
reservation unchanged. Need explicit owner handoff from exclusive config/table
clear to authorized startup admission, with exact operation identity and no
blanket bypass for other threads. Existing table owner has no such phase yet.
Evidence: docs/evidence/WR1200JS-IOT-OUTER-OPEN-AND-WDS-ADMISSION42-2026-10-30.json.
Feature branches/source only; no on-device startup reproduction. Previous
requirements saying reserve only before inner init are superseded by this
outer-boundary evidence. Full clear/open binding still unimplemented; next
implement boundary transport through existing core ioctl/OS_ABL rather than
assuming OS module can dereference private adapter layout. Preserve published
ABI IDs and require coherent target modules. No router/build/commit/push.


## 2026-10-30 reopen admission must precede rt28xx_init side effects

New audit-peer-reopen-unwind.py passed actual source ordering assertions on
local draft42. hif_sys_init, RtmpNetTaskInit, RtmpMgmtTaskInit and MlmeInit all
run BEFORE rtmp_cfg_init. A config failure jumps err5 -> rtmp_cfg_exit ->
UserCfgExit, then MlmeHalt, all timer release, management/net task exit and
hif exit. Therefore a standalone UserCfgInit denial would incorrectly enter
cleanup of retained resources; do not implement that as the admission boundary.

Next reserve table ownership before first rt28xx_init side effect and distinguish
admission refusal (direct return, no unwind) from partial initialization failure.
Carry exact serial through configuration and remaining init, retaining on partial
failure; cover shutdown/full clears/free with same lifetime contract. No such
binding is implemented yet. UserCfgInit has a column-zero nested brace: do not
extract its body using first newline closing brace. Auditor uses next routine
boundary and confirms no early return in the full reviewed body.
Evidence: docs/evidence/WR1200JS-IOT-REOPEN-UNWIND42-2026-10-30.json.
Source-only audit, not target/runtime proof. Draft42 remains latest candidate;
last full replay40. No router/build/dispatch/commit/push. Sol sole writer.


## 2026-10-30 whole reset owner tests adapted and passed

Adapted prepare-peer-failed-delete-check.py to detect owner-bound reset bodies.
It now extracts whole MacTableReset/MacTableResetWdev from draft42, uses actual
reservation helpers and verifies exact owner serial at mocked deletion. Two
strict optimized variants (PCI on/off) passed, including nested reset attempt
inside deletion, success releases, failed allocation/deletion retains owner,
and subsequent reset refusal. Locks/layout/deletion injected; no real kernel
parallelism, callback, DMA or lifetime proof. Evidence:
docs/evidence/WR1200JS-IOT-TABLE-OWNER42-WHOLE-RESET-2026-10-30.json.
This supersedes prior note that whole reset execution was not tested; broad
regression suite still not run. Draft41/42 remain outside full chain. Full
clear/UserCfgInit reopen admission is still unbound and is next. No production,
router, build/dispatch, commit or push. Sol sole writer; HEAD9af5697.


## 2026-10-30 local draft42: MacTabLock survives radio reopen

Found UserCfgInit recreated MacTabLock, while UserCfgExit and APShutdown freed
it during the same adapter lifetime. Added pinned prepare-peer-lock-lifetime.py
on draft41, output peer-lock-lifetime42-20261030. Initialization moved to final
nonfailing fresh adapter publication section before owner init; intermediate
frees removed; one free added to RTMPFreeAdapter alongside transition lock.
This does NOT prove RTMPFreeAdapter callers have retired all references.

Source assertions for unique init/free and ordering passed; actual reset owner/
insertion/deletion fragment host test passed with -O2 -Wall -Wextra -Werror.
No full regression suite or target compile. APShutdown fixture lock-free counts
need adaptation to new lifetime. Draft41/42 are NOT in full chain yet; last
verified complete chain40. Full table clears/reopen admission still unbound.
Next reserve table owner across full clears and reject retained owners before
UserCfgInit mutations, without holding spinlocks across waits. Evidence:
docs/evidence/WR1200JS-IOT-MACTAB-LOCK-LIFETIME42-DRAFT-2026-10-30.json.
Sol sole writer; HEAD/remote9af5697; all edits local. No router, firmware build,
workflow dispatch, commit or push. Goal remains active and incomplete.


## 2026-10-30 resumed: table owner stage41 draft locally prepared

Sol remains sole writer; HEAD/remote9af5697. After pause, removed two dead
Python draft lines and prepared peer-table-owner41-20261030 separately.
Adapter-owned state initialized once outside MacTab; reset preflight and serial
reservation share MacTabLock. Main/repeater insertion and ordinary/WDS resume
check admission. Reset private deletion supplies exact owner serial. Easy Setup
lookup/type mutation now inside MacTabLock. Failure retains owner; no implicit
retry reset. No waits added under locks.

Two strict optimized host tests passed: pure serial/retained/overflow owner and
actual reservation/insertion/delete fragments with injected locks/layout.
Source binding assertions passed. Whole reset execution and full regression
suite NOT run; existing fixtures still need adaptation. Stage41 not added to
full chain yet. Full table clear/reopen/release admission remains UNBOUND;
state survival after clear does not make such a clear safe. Next close those
bypasses, adapt extracted whole reset tests, then replay/regress. Evidence:
docs/evidence/WR1200JS-IOT-TABLE-OWNER41-DRAFT-2026-10-30.json.
No production driver/firmware/router change, commit or push. Goal active.

## 2026-10-30 full40 replay verified; shared table-owner scope corrected

Sol sole writer; HEAD/remote9af5697. Fresh complete40 preparation passed:
.iot-local-check/peer-retirement-chain40-20261030/legacy-close-result.
ALL560 files match incremental40b; its42 extracted host variants remain
applicable. Fresh tree additionally passed23 composed variants in
chain40-composed-host-20261030. Last complete replay is now40, not36.
Source preparation only, no MIPS/firmware compile or runtime acceptance.

Added audit-peer-table-writers.py:32 lexical mutation/setup sites in8 files,
comments/strings excluded; no complete alias/feature proof. New critical scope:
RTMPInsertRepeaterMacEntry is a second same-table allocator under MacTabLock,
with old timer cancellation/memory clear and unchecked hardware add. Easy Setup
ez_set_entry_apcli_mt7603 changes looked-up EntryType without local MacTabLock.
Fresh init and both close paths clear whole MacTab. State inside MacTab would
be erased, so fresh-adapter-only owner must be outside that memory region.

Next implement/bind common owner across main/repeater insertion, ordinary and
reset-owner deletion, WDS resume, Easy Setup type mutation and full clears.
Atomic reservation+failed-setup preflight under MacTabLock; no timer/callback
wait under any MAC/IRQ/transition lock. Preserve failed ownership on retry.
Owner not yet implemented; current preflight is still observation only.
Evidence: WR1200JS-IOT-PEER-TABLE-WRITERS-2026-10-30.json and
WR1200JS-IOT-FULL40-AND-WRITER-AUDIT-2026-10-30.json in docs/evidence.
All edits local; no router/build/dispatch/commit/push. Preserve scratch/dirty work.

## 2026-10-30 stage40 local — legacy close result no longer discarded

Sol sole writer, HEAD/remote still 9af5697. New pinned
prepare-legacy-close-result.py added to chain as40. Latest incremental scratch
legacy-close-result40b-20261030 includes both remaining VIRTUAL_IF_DOWN callers;
earlier scratch legacy-close-result40-20261030 lacks those two guards, preserve
but do not use as latest. RTMPDrvClose returns INT status; native declaration
and OS_ABL field updated together. rt28xx_close -> -EIO on failure before
DiagProcExit. PCI close guard -> -EBUSY before module decrement/power-down.
Virtual ioctl/wrapper propagate failure; Monitor/APCLI keep module ref on it.

42 strict optimized extracted host variants passed in
legacy-close-result40b-host-20261030. Whole legacy close, bridge, virtual wrapper
and both endpoints extracted; PCI is only a guard seam. Ops field/prototype/
assignment/macro compiled in mocked table for native/ABL, WIFI_DIAG and HNAT.
No actual target struct layout/binary ABI proof; coherent target module rebuild
required. Evidence: docs/evidence/WR1200JS-IOT-LEGACY-CLOSE-RESULT40-HOST-2026-10-30.json.

Next shared reset/insertion exclusion and retained retry ownership. Legacy
close repeats partial work if directly retried; zero virtual count prevents
immediate wrapper retry but is not a release/lifetime proof. PCI/Monitor/APCLI
pre-refusal effects remain partial; ndo_stop errno is not netdev lifetime.
Do not bind failed-peer cleanup or accept release yet. Full40 replay not run;
last full replay36. No target compile/runtime/image acceptance. No router,
firmware build/dispatch, commit or push this step. Preserve all dirty work.

## 2026-10-30 local stage39 — APShutdown failure reaches retained MBSS close

Sol remains sole writer; HEAD/remote 9af5697. New pinned
prepare-ap-shutdown-result.py is stage39. Scratch ap-shutdown-result39-20261030.
APShutdown/prototype now BOOLEAN; both callers check. Legacy close returns
locally; checked close marks shutdown_stage=3 under transition lock and returns
NDIS_STATUS_FAILURE before later task/Mlme/mgmt/ring teardown. Retry does not
replay stage zero. Pre-refusal effects, including earlier MlmeRadioOff, remain.

37 extracted optimized strict host variants passed in
ap-shutdown-result39-host2-20261030. Whole checked-close + whole APShutdown
bodies extracted; lower operations still injected. Feature variants PCI/non-PCI,
WDS/IGMP/WNM; checked close, virtual-down and last MBSS refusal/retry tested.
MBSS remains CLOSING with module ref held; bridge close_notified stays false.
First suite failed on missing test RT_DEBUG_TRACE constant, fixed and whole
suite rerun passed; predecessor38 close fixture also passed. Evidence:
docs/evidence/WR1200JS-IOT-AP-SHUTDOWN-RESULT39-HOST-2026-10-30.json.
Fresh full39 replay not run; last full replay36. No target/runtime acceptance.

Next RTMPDrvClose legacy VOID/OS_ABL ABI and rt28xx_close caller: the latter
still returns success after legacy close early refusal. Inspect all references
and ops declarations before changing. Higher scan/ATE/SDIO/VOID callers and
reset/insertion serialization remain open. No failed-peer cleanup bound; no
wait under MAC/IRQ/TimerQLock. No build/dispatch/router/commit/push this step.

## 2026-10-30 stage38 local — checked AP stop direct consumers

Sol sole writer; HEAD/remote 9af5697. New pinned prepare-ap-stop-result.py is
stage38 in the chain. Incremental scratch ap-stop-result38-20261030 changes
APStop/APStopBssOnly to BOOLEAN and guards all 26 direct APStop callers.
Important distinct failure exits: WSC UFD sets -EBUSY and still frees filename;
auth/WEP ioctl cases set -EBUSY and break; CMDHandler break reaches command
cleanup; USB rescan uses NDIS_STATUS_FAILURE; ATE -1; setters FALSE; VOID paths
return locally. No rollback of earlier state changes or lifetime acceptance.

30 extracted host variants passed, including 26 call-site branch seams and two
reset checkpoints. New checks do NOT execute whole APStop or caller bodies;
void return is adapted to a sentinel in the int host fixture. Source assertions
cover UFD filename cleanup and CMD queue cleanup order. Strengthened assertions
rerun after full suite passed. Evidence:
docs/evidence/WR1200JS-IOT-AP-STOP-RESULT38-HOST-2026-10-30.json.
Fresh full38 replay not run; last complete replay is36. No target compile.

Next APShutdown result and two common/rtmp_init_inf.c callers: currently VOID,
callers continue net task/Mlme/mgmt thread teardown after refusal. Also trace
outer scan/ATE/SDIO/VOID parents. APShutdown calls MlmeRadioOff before checked
APStop, so pre-refusal effects are partial. Reset/insertion serialization and
failed-peer cleanup owner still unbound. No wait under MAC/IRQ/TimerQLock.
No router state changes, firmware build/CI dispatch, commit or push this step.

## 2026-10-30 local stage37 — reset result reaches all direct callers

Sol remains sole writer. HEAD/remote still 9af5697. Added pinned
prepare-peer-reset-result.py to chain as stage37; generated candidate:
.iot-local-check/peer-reset-result37-20261030. Both reset APIs/prototypes now
BOOLEAN. All five direct calls checked: two AP stop tails return early, two
MAP channel paths and disconnect-all return FALSE. PMF disconnect-all branch
also checks individual deletion. Correction: earlier "PMF setter" references
actually refer to Set_DisConnectAllSta_Proc, not a PMF setting operation.

29 extracted host variants passed in peer-reset-result37-host-20261030:
actual reset return/alloc-failure paths and actual disconnect-all PMF on/off;
AP stop guard ordering is a source assertion, not full runtime execution.
Evidence: docs/evidence/WR1200JS-IOT-RESET-RESULT37-HOST-2026-10-30.json contains
source hashes and next APStop call inventory. New preparer initially rejected
the forward declaration anchor before writing; fixed to match the definition.
Full37 replay not performed; full36 replay remains the last complete replay.

Next APStop parent propagation: both AP stop APIs remain VOID and their callers
can restart/free/report success after early return. Inspect every call in the
inventory, including feature-gated shutdown/reset paths, before accepting end
to end refusal. Earlier side effects remain partial. Reset/insertion exclusion
and failed-peer cleanup owner still unbound. Do not call timer join under locks.
All new edits local. No commit/push/build/dispatch/router state changes here.

## 2026-10-30 chain36 reset refusal checkpoint — Sol remains writer

HEAD/remote: 9af5697, experimental timer helpers/tests publication. Remaining
dirty work is preserved; do not bulk-stage, clean or publish vendor scratch.

Local prepare-peer-failed-delete-gates.py is now stage36 in
prepare-peer-retirement-chain.py. Failed setup ordinary deletion refuses before
callbacks; reset loops observe failed setup before side effects and abort on
deletion refusal instead of terminal counter clearing. No atomic reset freeze
or caller return propagation yet. Reset API remains VOID. No cleanup owner bound.

Fresh .iot-local-check/peer-retirement-chain36-20261030/peer-failed-delete passed
36 preparation stages and matches all 560 incremental candidate files.
27 extracted variants in peer-failed-delete36-host-20261030 and 23 composed
variants in chain36-composed-host-20261030 passed (-O2 -Wall -Wextra -Werror).
Public evidence: docs/evidence/WR1200JS-IOT-FAILED-PEER-RESET36-HOST-2026-10-30.json.
All are mocked host tests; target/runtime/lifecycle acceptance false.

Next inspect/propagate reset refusal through APStop/APStopBssOnly (ap/ap.c),
PMF setter (ap/ap_cfg.c) and MAP channel changes (common/cmm_info.c). Parent
operations currently continue shutdown/reinitialization after VOID reset.
Then prove exclusive reset/insertion ownership before process-context cleanup.
Do not wait under MacTabLock/IRQ/TimerQLock or call join from timer callbacks.
Preflight observation alone cannot prevent concurrent new failed insertion.
No firmware build/dispatch/flash/reboot/router change in this step; local only.

## 2026-10-30 explicit process-context timer join API candidate

Added timer-os-join.inc, timer-checked-join.inc and pinned preparer (stage35).
Latest candidate timer-checked-join35-20261030. Linux utility boundary supports
native and OS_ABL_FUNC timer/task objects; checks atomic/IRQ context, always
calls del_timer_sync even for a not-pending timer, and identifies current timer
task in KTHREAD and Linux4.4 legacy PID modes. Utility prototypes/exports bound.
Core API checks exclusive timer/adapter ownership prerequisites, fences future
scheduling, OS-syncs, removes ALL duplicate queued instances, waits for task
owner outside locks, OS-syncs again for possible late task rearm, removes queued
instances again and rechecks owner. It never frees a timer or peer. Task wait
is capped at 5000 ms; del_timer_sync has NO timeout and may still block on a
hung callback. Do not describe the whole operation as bounded.

23 composed strict optimized host variants passed. New join tests cover direct/
task, context/self/unknown-task refusal, missing object, timeout, poisoned owner,
all/head/middle/tail duplicate removal preserving other timers, late queue after
first drain, admitted-task late rearm and busy final owner refusal. OS helpers
passed native/ABL x legacy/KTHREAD matrix. Initial test-only dangling-pointer
warning fixed by static mock PID storage. No warning suppression. Prototype/
export/include source assertions passed. Receipt:
docs/evidence/WR1200JS-IOT-TIMER-JOIN35-HOST-2026-10-30.json.

All Linux scheduling/timer waits and type layouts injected; no target compile,
real kernel timing/deadlock, symbol-link or on-device proof. Exclusive timer,
queue, adapter/module lifetime is a CALLER contract, not established by this
API. No failed-peer cleanup caller yet. Next bind claimed process-context failed
insertion owner and initialized-timer resource list; do not wait under MAC/IRQ/
transition/TimerQLock or from timer callback. Old reuse, DMA/TxS and partial
hardware recovery remain open. Fresh full35 chain not replayed. No router
change, full firmware build, CI dispatch, commit or push. Goal incomplete.

## 2026-10-30 timer-task callback has stable adapter-owned execution identity

Added timer-task-owner.h, prepare-timer-task-owner.py (stage34) and
check-timer-task-owner.c. Latest isolated candidate timer-task-owner34-20261030.
An adapter-owned current timer/serial is claimed while TimerQLock still protects
queue pop, before callback/periodic rearm. Release/wakeup occurs under that lock
AFTER final timer-object use. This state survives peer/timer memory clearing.
It is initialized once before adapter publication, never by timer-queue reopen.
Concurrent executor collision/serial exhaustion poison the owner and prevent
false idle acceptance. Wrong/stale serial cannot clear a newer callback.

Worker now resets pTimer and serial for every inner iteration; previously an
empty queue observed after locking could leave the prior local timer pointer
and invoke it again. Source assertions verify reset and pop-before-unlock order.
Direct/task extracted macro tests were adapted for actual tracked worker block;
inside callback they assert the execution owner remains busy. Pure owner tests
cover wrong pointer/serial, same-address new serial, collision and overflow.
17 composed and 25 extracted host variants passed on this candidate. Receipt:
docs/evidence/WR1200JS-IOT-TIMER-TASK-OWNER34-HOST-2026-10-30.json.

No full kernel-thread/concurrency, MIPS or device proof. Existing deletion paths
that do not honor this owner are NOT made safe by tracking alone. Next a bounded
process-context checked join: fence scheduling, unconditional Linux timer sync,
remove all queued instances, wait for task owner, recheck possible late rearm
and identity before releasing any resource. Never wait while holding MAC/IRQ/
transition/TimerQLock or from the executing callback itself. Adapter/module
pins, old WCID reuse, DMA/TxS and failed insertion cleanup still open.
No fresh 34-stage replay, full firmware build, CI dispatch, router change,
commit or push. Goal remains active and incomplete.

## 2026-10-30 timer fence candidate verified after resume

Goal resumed from user pause. Fixed missing FALSE in dispatch fixture;
direct and timer-task actual macros/worker-block tests passed. Init/Set/Mod/
fence extracted API test also passed after host ULONG adaptation to uintptr_t
(Windows pointer width differs from target). No target ABI claim.

New audit-peer-timer-arms.py excludes comments/strings and inventories balanced
calls: 21 peer-timer init/arm sites, 8 initialization sites inside insertion,
zero direct insertion arms. RTMPInitTimer and Linux timer init do not directly
arm. See WR1200JS-IOT-PEER-TIMER-ARMS-2026-10-30.json. This narrows the failed
insertion case but does NOT prove old timer/WCID reuse or transitive readers
cannot leave callbacks active. Do not infer never-armed lifetime from this scan.

Added stage33 prepare-peer-timer-fence.py with exact timer-source pins,
peer-failed-timer-fence.inc and scheduling/dispatch fixtures. Latest isolated
source: peer-timer-fence33-20261030. Failed MT insertion fences exactly its
initialized timer branches (client/APCLI/WDS variants) before MAC unlock.
TimerSemLock serializes fence vs Init/Set/Mod; valid retiring timers cannot
be reinitialized/rearmed there. Direct/task wrappers and worker check retiring
before dispatch/rearm. Repeat/State also suppress normal recurrence. No join,
free or SET_ENTRY_NONE is performed; an already-admitted callback/rearm race
still needs a proper process-context drain and lifetime ownership.

16 composed variants passed, including branch-specific fences, plus 25 extracted
variants with real timer APIs/macros/worker block and injected OS/kernel actions.
See WR1200JS-IOT-TIMER-FENCE33-HOST-2026-10-30.json. These tests model zeroed
fresh timer storage; audit actual construction/reinitialization callers before
production integration. Expanded global critical-section/callback contexts,
old reuse, timer-task execution join and failed-entry cleanup remain open.
Fresh full 33-stage replay and MIPS build not run. No router change/full firmware
build/CI dispatch/commit/push. Goal active, not accepted as complete.

## 2026-10-30 failed insertion cleanup requires real timer callback join

Audited initialized resources before failed hardware insertion: TR queues,
EnqueueStartForPSKTimer, conditional client/APCLI retry/PMF/WSC timers,
UAPSD initialization, committed client/MAC counters and key-side effects. WDS
only initializes the unconditional EAPOL-start timer in this insertion path;
do not assume every timer exists for every entry type.

Found __RTMP_OS_Del_Timer in os/linux/rt_linux.c calls del_timer_sync ONLY if
timer_pending is true, otherwise reports cancelled TRUE. New
audit-timer-delete-join.py extracted the actual function and strict optimized
host witness reproduced running+not-pending -> cancelled TRUE with zero join,
while pending control does synchronize. This uses injected kernel states,
not an on-device race. timer_join_accepted remains FALSE. Evidence:
docs/evidence/WR1200JS-IOT-TIMER-JOIN-WITNESS-2026-10-30.json.

RTMPReleaseTimer drops TimerSemLock before OS deletion, but does not drop a
caller's MacTabLock. Blindly making every call synchronous risks callback/lock
or self-cancel deadlock and requires caller-context audit. With
RTMP_TIMER_TASK_SUPPORT, RtmpTimerQThread pops a node under TimerQLock then calls
handle outside it and may rearm Repeat/State; RtmpTimerQRemove only scans queued
nodes and does not join an executing handler. Therefore ordinary release/queue
removal is not sufficient acceptance proof for freeing failed peer resources.

Next process-context per-entry retirement with rearm fence, executing timer-task
callback ownership and unconditional direct-timer synchronization after releasing
MAC/IRQ/transition locks; only then timer/resource-specific cleanup and counters.
Do not add automatic SET_ENTRY_NONE/free based on current timer return value.
No global timer implementation changed, no full build/CI schedule/router change,
commit or push. Existing retained failure stays retained; goal not complete.

## 2026-10-30 fresh chain31 verified; MT insertion failure publication blocked

Fresh 31-stage composition from full-driver-overlay4-20261029 succeeded:
peer-retirement-chain31-20261029/wds-ageout-recovery. On that exact final source,
13 composed WDS variants and 22 extracted control-flow/hardware variants passed.
This confirmed composition, not target/runtime acceptance.

Review found RTMP_STA_ENTRY_ADD in MacTableInsertEntry still discarded checked
hardware result, so busy/partial insertion could publish hash and TRUE caps.
Added peer-hardware-insert-result.inc, pinned preparer and focused test (stage
32). Latest isolated candidate peer-hardware-insert32-20261029 records observed
setup result in two new TR fields, reset before setup. MT/HIF_MT failures close
caps under irq_lock and return NULL before hash/readiness publication. Preserve
entry type, initialized queues/timers and committed counters to prevent unsafe
WCID reuse; no blind rollback after possible hardware/key side effects. Legacy
non-MT/HIF paths retain old behavior.

15 composed variants and 22 extracted variants passed on stage32, plus source
ordering before hash/capability publication. New tests cover NOT_WRITTEN,
PARTIAL, success and legacy paths with injected hardware/types/locks. Shared
publication test now recognizes checked consumer ordering; its order check
alone does not prove failure handling. Summary receipt digests/counts:
docs/evidence/WR1200JS-IOT-PEER-CHAIN31-32-HOST-2026-10-30.json.
Stage32 was applied to fresh chain31; no new full 32-stage replay. No MIPS build,
real kernel/MMIO, layout/ABI or RAM measurement; TR layout changed and requires
coherent full-module compilation. No router changes/full firmware build/CI
schedule/commit/push.

Next implement exact ownership/cleanup for failed unpublished insertion; it
currently consumes a retained WCID with timers/counters and cannot be accepted
as a complete lifecycle. PARTIAL deletion recovery, DMA/TxS identity, global
locking and adapter/module lifetime remain open. Goal remains incomplete.

## 2026-10-29 lazy WDS maintenance resumes no-write failures and finalizes exact slot

Added wds-ageout-recovery.inc and prepare-wds-ageout-recovery.py (stage 31).
Latest isolated source: wds-ageout-recovery2-20261029. Existing periodic lazy
maintenance first handles retained ownership. It snapshots exact saved identity
under WdsTabLock -> MacTabLock -> transition; only observed effective NOT_WRITTEN
gets a netdev pin and calls explicit resume outside those locks. PARTIAL,
unobserved, active claim and ambiguous duplicate owners stay retained; normal
fresh age-out is skipped for handled retained slots. No new worker/service.

Finalizer rechecks device/generation/serial/index/WCID/address, phase-4 software
completion, NONE entry, disabled caps, valid slot/count and active radio credit
under all three locks. Only then consumes owner, clears slot/address, decrements
occupancy and releases one radio credit. Repeated/competing finalization cannot
consume again. Wake occurs after unlock and dev_put is after final adapter use.
This is not a proof of adapter/module pinning or DMA/TxS retirement.

13 composed WDS host variants passed, including recovery with injected explicit
resume. Focused expanded recovery test also passed direct phase-4 completion,
missing radio credit refusal, ambiguous duplicate owner refusal, repeated busy,
PARTIAL no-repeat, slot mismatch and actual lazy-loop dispatch. Existing source
resume tests separately exercise actual admission/observer/result/finish blocks;
these are NOT a fully linked target-driver or hardware end-to-end test.
Receipt: .iot-local-check/wds-ageout-recovery-checks-20261029/result.json;
expanded fixture/executable wds-ageout-recovery-expanded in scratch.

Fresh full 31-stage replay still pending. Next PARTIAL recovery policy without
blind replay, full chain/target build and global lock/adapter/DMA/TxS acceptance.
Mode change outside lazy maintenance and shutdown with a retained operation
still need a controlled drain path; do not call all lifecycle failures solved.
No router changes, full firmware build, CI dispatch, commit or push this turn.

## 2026-10-29 explicit WDS NOT_WRITTEN checkpoint continuation

Added prepare-wds-delete-resume.py (stage 30), wds-delete-resume-admission.inc,
and prepare-wds-delete-resume-check.py. Latest candidate:
wds-delete-resume-20261029. Original public MacTableDeleteEntry remains a
normal wrapper around private implementation. New explicit
wr_iot_wds_resume_delete requires device/generation/serial/address identity,
WDS peer, disabled admission caps and retained observed NOT_WRITTEN. It claims
stage 3 under transition lock and jumps directly to the hardware checkpoint,
setting the required wdev local, bypassing previous callbacks/timers/BA effects.
PARTIAL, unobserved failure, wrong identity and duplicate claims refuse.

Saved owner now tracks retry count/result separately from immutable first
hardware result. NOT_WRITTEN retry failure returns to retained stage 2;
PARTIAL prevents another no-write retry. Success marks stage 4 only after
actual software entry becomes NONE with disabled caps, before MAC unlock.
Radio/removal ownership is NOT released by this API; no automatic caller,
WDS-slot finalizer or DMA/TxS reaper is bound yet.

12 composed WDS host variants passed, plus 22 extracted control-flow/hardware
variants including resume test. Resume fixture uses actual admission, delete
gate, observer, hardware-result include and extracted real finish block;
callbacks/vendor software cleanup/locks/hardware are injected. It confirms no
replayed notifications/timers/BA, one hardware attempt on success, ordinary
retained-delete refusal, stale generation/serial/address/caps rejection,
PARTIAL rejection, repeated busy retry and exactly one software finish.
Source-order assertions confirm checkpoint entry precedes callbacks and jumps
to hardware. This is not full target function compilation for all feature flags.
Receipts: .iot-local-check/wds-delete-resume-wds-checks-20261029/result.json and
.iot-local-check/wds-delete-resume-chain-checks-20261029/result.json.

Next exact-slot finalizer and controlled caller for retained no-write recovery;
PARTIAL needs separately proven recovery. Fresh full 30-stage replay, target
build, reverse-lock/adapter/module audit and DMA/TxS completion remain open.
No router changes, full build, CI dispatch, commit or push this continuation.

## 2026-10-29 checked WTBL update shares pre-write admission/PCI lock span

Added prepare-wcid-update-busy-admission.py as stage 29. Latest isolated source:
wcid-update-busy-20261029. Checked insertion/update now takes IndirectUpdateLock
before any direct WTBL/queue write and refuses initial IU_BUSY as NOT_WRITTEN.
Removed its two later nested acquisitions/intermediate success unlock; one PCI
lock spans direct writes, queue STOP/START and all indirect commands. First
poll-timeout queue restart happens before unlock. Existing other timeout exits
release once. Removed tautological USHORT WCID>=0 wrapper without behavior change.
Reviewed actual MtAsicACQueue body: direct MMIO only, no lock acquisition/callback.
This does not audit every external AC-queue writer or firmware interaction.

Added prepare-wcid-update-check.py extracting the complete actual update body
with synthetic unions/MAC layout/MMIO/queue primitives. Tests check zero writes
and no queue stop on initial busy, all four command timeouts, balanced lock,
exactly one queue restart, success, missing table, invalid/zero capacity.
Four PCI/MT_PS variants passed. The expanded shared hardware runner passed
21 extracted variants on this same candidate. Receipt:
.iot-local-check/wcid-update-busy-chain-checks-20261029/result.json.
An initial fixture compile failed for a missing synthetic DW15 member and
misleading indentation; corrected fixture, strict GCC then passed.

No MIPS/kernel/MMIO hardware acceptance. A larger single critical section may
increase lock hold time; real IRQ/latency impact remains unmeasured. Non-PCI
paths get busy refusal but no new cross-thread serialization. Full fresh
29-stage replay was not performed in this continuation. Next explicit retained
partial-delete checkpoint continuation, global reverse-lock/other-writer review,
adapter/module lifetime and DMA/TxS retirement. No router changes, full build,
CI dispatch, commit or push.

## 2026-10-29 checked WTBL delete refuses an unresolved prior command

Added pinned prepare-wcid-delete-busy-admission.py and stage 28 in the peer
chain. Latest isolated candidate wcid-delete-busy-20261029. For each WCID,
IndirectUpdateLock (PCI) is acquired before direct WTBL writes, initial WIUCR
busy is checked before any write, and the lock remains held through indirect
counter clears and address readback. Busy returns NOT_WRITTEN (or PARTIAL if
an earlier WCID in ALL already changed); no extra polling under the lock.
No automatic retry/resume is authorized by this admission gate.

Expanded whole checked-deletion extractor test: every PCI write must hold the
lock; initially busy produces zero writes/commands/delays; busy at later ALL
entry reports PARTIAL with prior command count unchanged. Existing timeout,
readback corruption, invalid/zero bounds and 255-entry ALL tests remain.
All 17 extracted host variants passed on new candidate, including with/without
PCI+MT_PS deletion variants. Result receipt:
.iot-local-check/wcid-delete-busy-chain-checks-20261029/result.json.
Tests use synthetic MMIO/layout, not actual hardware/kernel concurrency.

Literal source inventory found WIUCR writes in cmm_asic_mt.c only: three rate/
statistics writers already take IndirectUpdateLock and poll before issue; four
checked-update and three checked-delete command sites. WTBL1OR direct writes
exist in checked update and deletion. This is a literal scan, not proof against
aliases/macros or firmware writers. Checked insertion/update still writes direct
WTBL before its indirect lock and issues a command without initial busy refusal;
review/align that path before claiming global serialization or safe resume.

Stage 28 was applied to the existing predecessor; a fresh complete 28-stage
replay was not run in this continuation. No target build/runtime acceptance,
router changes, full build, CI dispatch, commit or push. Next shared update
admission/serialization, then exact partial-deletion continuation and DMA/TxS.

## 2026-10-29 normal deletion cannot replay retained WDS retirement

Reviewed partial-delete resume feasibility. Existing early delete gate ignored
retirement_stage, so another ordinary MacTableDeleteEntry could replay timer,
notification and BA effects on a retained failed age-out. Fixed WDS admission:
only no saved retirement or original stage 1 is accepted; retained stage 2 and
future claimed stage 3 refuse before any side effect. A continuation must use
an explicit checked path, not ordinary deletion.

Updated wds-peer-delete-gate.inc, its regression, exact reviewed hash acceptance
in the identity preparer, and final hardware-consumer preparer to install the
matching gate atomically. Latest isolated source:
wds-retained-delete-refusal-20261029. All 12 composed strict optimized host
variants passed. Additional focused test explicitly passed original stage-1
admission and stage-2/3 refusal with no mutation/lock leak. No MIPS/runtime proof.

Further source finding: wr_iot_delete_wcid_checked performs direct WTBL writes
before taking IndirectUpdateLock, then polls shared WIUCR only after issuing
its first counter-clear command. After PARTIAL timeout, blind retry could write
while the previous indirect operation is unresolved. Before implementing
resume, review whole-command serialization and pre-write busy admission,
including all writers sharing IndirectUpdateLock. Do not infer retry safety
from the status descriptor or idempotent-looking address clears.

Next hardware command busy/lock ownership, then explicit partial-delete
checkpoint continuation. Existing 27-stage receipt applies only to historical
hashes. No router changes, full build, CI dispatch, commit or push this turn.

## 2026-10-29 precise hardware outcome retained in WDS age-out identity

Added retirement_hardware_observed/result to the saved owner; unobserved stays
distinct from APPLIED=0. New wds-hardware-delete-observer.inc records the first
result under MacTabLock -> transition only when device/generation/WCID/address
match the saved retirement. Wrong identity leaves state untouched; repeated
or retained-stage observations cannot replace the first hardware result.
The consumer records NOT_WRITTEN for refused WCID narrowing and records checked
hardware result before returning FALSE or continuing software release.

Updated prepare-wds-hardware-delete-consumer.py to install observer and owner
header atomically with the consumer. Added check-wds-hardware-delete-observer.c
and composed-runner case. Latest candidate: wds-hardware-observed-20261029;
all 12 strict optimized host variants passed, including observer identity,
immutable first result and four MT/WDS feature combinations. Results:
.iot-local-check/wds-hardware-observed-checks-20261029/result.json.
This run updates final-stage composition only, not a fresh full 27-stage replay.
Earlier 27-stage/17 extracted-test receipt remains historical evidence for
its own hashes. New tests inject hardware/kernel operations; no target/runtime
or callback/DMA lifetime acceptance.

Next resume partial deletion only from a proven checkpoint without replaying
notifications, timer cancellation or BA cleanup. Precise hardware outcome is
a prerequisite, not permission for automatic retry. Source-chain target build,
reverse-lock review, adapter/module lifetime and DMA/TxS join remain open.
No router changes, full build, CI dispatch, commit or push this continuation.

## 2026-10-29 complete 27-stage peer candidate reproduced and tested

Extended prepare-peer-retirement-chain.py through all recent WDS caller,
delete, slot, close, age-out, lock-lifetime, identity-owner and hardware-consumer
stages. Fresh complete run from full-driver-overlay4-20261029 succeeded with
27 stages and 550 candidate files. Final source:
peer-retirement-chain27-20261029/wds-hardware-consumer.

Fixed exact-version acceptance in prepare-wds-peer-delete-identity.py: full
chain installs the reviewed identity gate earlier; accept its specific pinned
hash as well as the historical predecessor, not arbitrary helper contents.
Added check-wds-composed-candidate.py; 11 strict optimized host variants passed
against the final candidate headers. Updated check-peer-hardware-chain.py to
use candidate headers first and choose actual parent child-failure propagation
for retained WDS source instead of the inapplicable old freed-pointer witness.
All 17 extracted hardware/queue/control-flow variants passed on that SAME final
source. The child replacement test does not prove retained-netdev reaping.

Receipt digest/count summary:
docs/evidence/WR1200JS-IOT-PEER-CHAIN27-HOST-2026-10-29.json.
All tests use injected kernel/vendor/MMIO primitives; lifecycle_accepted,
target_compiled and runtime_verified remain FALSE. No downloaded/generated
vendor source published. No full build, router changes, CI dispatch, commit
or push. Next exact partial-failure continuation and DMA/TxS lifetime proof;
full MIPS build/image/device acceptance still required after integration.

## 2026-10-29 WDS consumes checked hardware deletion result

Actual MacTableDeleteEntry called RTMP_STA_ENTRY_MAC_RESET, whose MT macro calls
VOID AsicDelWcidTab and discards wr_iot_delete_wcid_checked result. Therefore
software NONE could follow a failed hardware deletion. Added WDS-only MT
consumer wds-hardware-delete-result.inc and pinned preparer
prepare-wds-hardware-delete-consumer.py. Latest isolated source:
wds-hardware-delete-consumer-20261029.

For MT+WDS entries, NOT_WRITTEN/PARTIAL/other non-APPLIED results now release
MacTabLock and return FALSE before timer release/software NONE/counter release.
WCIDs at/above WCID_ALL refuse before narrowing into UCHAR, preventing an ALL
sentinel alias. Other peer types and non-MT/WDS builds retain original macro.
Existing age-out failure descriptor and fences therefore remain retained.
Prior notifications/timer cancellation/BA/queue effects may already have run;
this change does not make failed deletion safe to replay or prove DMA retirement.

Strict C11/O2/Wall/Wextra/Werror host tests passed MT+WDS, MT-only, WDS-only,
neither: success, NOT_WRITTEN/PARTIAL propagation, non-WDS legacy path and
sentinel/narrowing refusals. Source assertions place the gate before
RTMPReleaseTimer and SET_ENTRY_NONE. Hardware function injected in these new
consumer tests; no new hardware/target execution or full driver build.

Next preserve precise failure outcome in retained ownership and bind a checked
continuation without replaying partial vendor work. Complete chain integration,
lock-order/adapter/module review and DMA/TxS proof remain required. No router
change, full firmware build, CI dispatch, commit or push in this continuation.

## 2026-10-29 failed WDS age-out retains exact transaction identity

Extended wds-peer-operation.h with retirement serial/stage/index/WCID/address.
Save occurs before vendor deletion under transition lock; serial never repeats
within a registration and overflow refuses before deletion. Completion matches
device, registration generation, serial, slot, WCID and address. A failed
postcheck retains stage 2 and existing radio/removal fence rather than losing
the identity on return. Unchecked release of retained stage 2 is rejected.
Added prepare-wds-ageout-identity-owner.py and check-wds-retirement-identity.c.
Latest isolated source: wds-ageout-identity-owner-20261029.

Strict optimized host GCC passed saved-identity tests (wrong device/generation/
slot/WCID/address, stale serial, repeated completion/retention, fresh serial),
original peer-operation regression, and expanded generated age-out/maintenance
test including saved identity during deletion, retained failure stage and
serial-overflow rollback without radio/devref leak. No target build or real
kernel concurrency test. No claim that registration identity identifies DMA
association completions or proves callback retirement.

Next bind a single checked continuation to retained stage 2 with explicit
partial-deletion outcomes; never replay vendor deletion based solely on TRUE,
NONE or this descriptor. Global lock ordering, table resets, adapter/module
pins, DMA/TxS join and complete source chain remain open. No router changes,
full build, CI dispatch, commit or push in this continuation.

## 2026-10-29 WDS lock initialized once before adapter publication

Added prepare-wds-lock-lifetime.py. Latest isolated candidate:
wds-lock-lifetime-20261029. Moves NdisAllocateSpinLock(WdsTabLock) from late
WDS_Init (after child netdev registration) into RTMPAllocAdapterBlock beside
the transition lock, guarded by WDS_SUPPORT and before *ppAdapter publication.
Repeated WDS_Init no longer reinitializes a published table lock.

Confirmed actual Linux OS_NdisAllocateSpinLock expands to spin_lock_init;
OS_NdisFreeSpinLock is do{}while(0). Existing APShutdown free call is retained;
this candidate is Linux-specific, not a portable lock-lifetime claim.
Source assertions passed unique initializer across candidate C files, correct
WDS_SUPPORT guard, ordering before adapter publication and no WDS_Init reinit.
Strict optimized host age-out/maintenance regression passed with newest headers.
No target build, kernel lockdep or on-device lifecycle test was performed.

This resolves the observed late/repeated initialization issue in the isolated
candidate. Still open: adapter free vs outstanding callbacks, failed age-out
continuation, initialization table reset vs active peers, global reverse-lock
review and complete source-chain integration plus DMA/TxS retirement. No router
changes, full build, CI dispatch, commit or push in this continuation.

## 2026-10-29 lazy WDS maintenance stops carrying stale peer pointers

Latest isolated candidate: wds-lazy-maintenance-20261029. Extended the age-out
helper include with wr_iot_wds_lazy_maintenance and an early lazy-mode dispatch
in WdsTableMaintenance. For each slot, Valid/WCID (both MAC and TR array bounds),
peer type/WCID/wdev/address and mode are checked under WdsTabLock -> MacTabLock.
Idle counters advance only below the age-out threshold, preventing overflow.
No raw peer pointer survives unlock; age-out rechecks identity and eligibility.
The static-WDS legacy path has not received this lifetime conversion.

Strict optimized host test against generated headers passed earlier age-out
cases plus threshold crossing, MAC-valid/TR-invalid WCID, address mismatch,
sparse slot index 1 with occupancy 1, saturated counters and no second deletion
after a retained refusal. Tests inject vendor deletion, locks and types; no
claim of target compilation, concurrency, real traffic or hardware acceptance.

Source search found the remaining WdsEntryDel call only inside
rtmp_read_wds_from_file, called by RTMPSetProfileParameters through
RTMPReadParametersHook in initialization. APWdsInitialize also clears the table.
This narrows the writer audit; it does NOT prove those initialization paths
cannot overlap live radio. WDS_Init allocates WdsTabLock late, after netdev
registration, so initialization/lock lifetime ordering needs explicit review.

Next retain exact failed age-out continuation, review initialization/remaining
writers and global lock ordering, integrate the complete chain and prove
adapter/module/DMA/TxS lifetime. No router change, full build, CI dispatch,
commit or push. Published checkpoint remains 81122cd; these changes are local.

## 2026-10-29 WDS lazy age-out owns reservation through slot cleanup

Added wds-ageout-transaction.inc, prepare-wds-ageout-transaction.py and
check-wds-ageout-transaction.c. Latest isolated source:
wds-ageout-transaction2-20261029. Lazy maintenance now invokes the helper;
no production source/image installation occurred.

Under WdsTabLock -> MacTabLock -> transition, helper rechecks lazy mode,
valid slot, WCID bounds, exact peer/wdev/address/idle threshold and published
owned registration. It reserves peer_operation.removing, holds radio activity
and netdev reference, then calls deletion outside those locks. Post-delete
cleanup revalidates registration generation, slot device/WCID/address and NONE
MAC entry under the same lock order before clearing the slot/count. A false
result, vendor TRUE/no-op or identity mismatch retains reservation/radio
activity for recovery; no release/recovery implementation exists yet. The
netdev pin is released after final adapter access; adapter/module lifetime
still requires full binding proof.

Maintenance scans MAX_WDS_ENTRY instead of the shrinking occupancy count and
checks valid/WCID bounds before its first Content access. Those checks do not
make the legacy idle-counter/static-WDS path atomic; remaining stale access
and other configuration writers still require review.

Strict C11/O2/Wall/Wextra/Werror host test against generated headers passed:
success, delete refusal, TRUE/no-op, changed slot address, occupied WCID,
changed registration generation, changed slot WCID, active operation refusal,
radio-busy rollback, invalid WCID/index, low idle count and NULL adapter.
Injected delete verifies reservation rejects insertion/close, holds radio
activity, and runs outside locks. Source assertions passed maintenance binding,
sparse-slot scan and WCID guard ordering. These are sequential injected tests,
not MIPS, concurrent kernel or hardware proof.

Next: retained failure recovery with exact transaction identity; serialize
remaining WDS table writers and legacy maintenance accesses; global reverse-lock
review, full chain integration, adapter/module pins and DMA/TxS retirement.
Do not equate NONE MAC entry with DMA completion. No router changes, full build,
CI dispatch, commit or push in this continuation. Goal remains incomplete.

## 2026-10-29 WDS delete rejects wrong peer address before side effects

Reviewed actual MacTableDeleteEntry: address comparison occurs after vendor
notifications/timer cancellation, and the function returns TRUE even when the
address does not match. MacTableDeleteWDSEntry directly forwards that result.
Therefore a TRUE result alone cannot authorize WDS slot cleanup.

Extended WDS-only early delete admission to reject null/mismatched pAddr before
any timer/vendor side effects. Non-WDS behavior preserved. Added pinned,
receipt-checked prepare-wds-peer-delete-identity.py; latest isolated source is
wds-delete-identity-20261029, retaining the previous close/removal gates.

Strict optimized host GCC passed both repository helper test and test against
the generated include: wrong/null address no mutation, active operation refusal,
exact address admission, missing registration refusal and unchanged non-WDS
path. Source-order assertions confirm gate before notifications and timers.
Target MIPS/concurrency/hardware were not tested. Terminal-state validation,
exact slot reservation spanning age-out, and DMA/TxS retirement remain open.
No router changes, full build, CI dispatch, commit or push in this continuation.

## 2026-10-29 WDS retirement blocks close and registration release

Added prepare-wds-retirement-close-gate.py and
check-wds-retirement-close-gate.c. On the isolated slot-allocation predecessor,
ref begin_close, registry begin_remove/release and auxiliary close reservation
now reject peer_operation.removing as well as active operations. Refusal is
before radio-ticket mutation. Latest scratch: wds-retirement-close-gated-20261029.

Actual generated headers passed strict optimized Windows host GCC regression:
retained removal blocks close without changing radio/registration; idle registry
cannot begin removal or release; fresh state still permits close. Predecessor
failed the new assertion at begin_close, establishing regression sensitivity
(Windows assertion process was stopped after reporting the failure). Existing
interface-registry and auxiliary close-claim tests also passed on new headers.

Age-out acquisition/release is still unbound. This is not DMA/TxS quiescence,
MIPS build, concurrency proof or production integration. Next reserve exact
registration/slot identity across peer delete and WDS table cleanup; review
lock ordering and other configuration writers. No router changes, build/CI
dispatch or publication in this continuation. Published HEAD remains 81122cd.

## 2026-10-29 WDS slot allocator observes runtime retirement fences

Added wds-slot-allocation-gate.inc and receipt-authenticated preparer. Actual
WdsEntryAlloc now checks published device/generation/family and registration /
peer_operation removing flags under transition lock while holding WdsTabLock,
before Valid/PeerWdsAddr/Size mutation. Pre-netdev configuration allocation
remains allowed. Latest scratch wds-slot-allocation-gated-20261029.

Extracted complete allocator strict optimized C11 test passed pre-netdev
configuration, registration-removing refusal, peer-retiring refusal, normal
runtime allocation and same-address existing-slot lookup without Size increase.
No lock leak and refusal leaves table unchanged. Kernel/up-check/types injected;
not target or concurrency proof. WdsTabLock -> transition edge added; global
reverse-lock review remains required before integration.

Age-out has not yet acquired peer_operation.removing across delete/table-cleanup;
this gate provides the allocator half only. Next bind temporary retirement
reservation to exact registration/slot identity and clear only after ownership
continuation; never infer DMA/TxS retirement from this flag. Other config-table
writers remain to cover. No router/build/CI dispatch/commit/push. diff check passed.


## 2026-10-29 lazy WDS age-out preserves config on peer refusal

Added prepare-wds-maintenance-refusal.py from exact peer-delete-gated input.
Lazy age-out now snapshots WCID/MAC locally, invokes MAC peer deletion first,
and clears WDS table only if deletion reports success. Previous unconditional
WdsEntryDel before refused deletion was inconsistent with active-operation gate.
Latest scratch wds-maintenance-refusal-20261029, not production/full-chain.

Extracted actual sequence strict optimized C11 test passed refusal with no
WDS cleanup, success with one cleanup using saved address even after injected
peer deletion clears original address. Actual peer/table functions injected;
no atomicity/concurrency proof. Snapshot itself is still outside a complete
WDS+MAC ownership transaction; reallocation between accepted deletion and
WDS-table cleanup can target a new same-address link. Must gate that reuse
before calling age-out race solved. Another configuration parser WdsEntryDel
call remains to review separately.

Next exact identity reservation spanning age-out and WDS slot reuse, callback/
queue/DMA/TxS retirement and retained-netdev completion. No router/build/CI,
commit/push. git diff --check passed.


## 2026-10-29 peer deletion refuses active WDS transaction

Added wds-peer-delete-gate.inc and exact-pinned prepare-wds-peer-delete-gate.py.
Latest isolated wds-peer-delete-gated-20261029 inserts gate under MacTabLock
immediately after peer selection, before notification/vendor/timer mutations.
WDS requires a current published registration by exact wdev/netdev identity
and nonzero generation with no active peer operation. Failure releases MAC
lock; non-WDS path unchanged. Transition check nested MAC -> transition, no
wait. Full reverse-lock audit still required.

Strict optimized C11 check-wds-peer-delete-gate.c passed active refusal with
no mutation, inactive acceptance, absent generation/null wdev fail-closed,
and non-WDS preservation. Source ordering assertion passed gate before
BAND_STEERING side effects and RTMPCancelTimer. Injected state/locks, not full
vendor deletion or real concurrency. Deferred retry responsibility remains.

Important remaining pre-call mutation: lazy WdsTableMaintenance calls WdsEntryDel
before MacTableDeleteWDSEntry, clearing WDS Valid/address/table size before the
new peer gate can refuse. Need gate/transaction ownership across that earlier
WDS-table mutation as well; do not claim all age-out races resolved. Callback/
DMA/TxS retirement/reaper, adapter lifetime and target acceptance remain open.
No router/build/CI dispatch/commit/push. diff --check passed.


## 2026-10-29 actual moved WDS rate helper checked across modes

Added prepare-wds-finish-peer-check.py extracting complete moved finish helper.
Strict optimized C11 compile/run passed base and DOT11_N_SUPPORT+DOT11_VHT_AC
variants. Checks mode0 compatibility no update, NULL refusal, mode1 MCS-only
without changing SupportRateMode, and mode2 expected CCK/OFDM/HT/unspecified/
unknown PhyMode values for 2G-capable and other bands. Actual vendor MCS call
is injected/counted; real rate negotiation/RF and target ABI not tested.
This supersedes only the previous missing mode0/mode1 finish control-flow
coverage, not hardware acceptance. Tests use valid index and pinned adapter.

Next close successful returned-entry race against MacTableDeleteEntry: WDS
maintenance can delete a peer independently of netdev close/remove, so the
registry outer counter must also gate that peer-deletion admission under the
reviewed MAC -> transition order before any timer/hardware mutation. Then
callback/queue/DMA/TxS retirement and retained-netdev completion remain open.
No router/build/CI dispatch/commit/push. git diff --check passed.


## 2026-10-29 RX/configured caller MCS tails moved into counted transaction

Added prepare-wds-caller-transaction.py from receipt-authenticated caller-refusal
source. RX uses finish mode1 (MCS only), configured-link loop mode2 (MCS and
existing rate-mode switch); public 3-argument insertion compatibility wrapper
uses mode0. Common internal transaction runs finish helper before peer/radio
leave and netdev put. NULL guards remain at caller boundaries. Latest scratch:
wds-caller-transaction-20261029; not integrated into full chain/production.

Source assertions pass no MCS call remains in either caller and configured
rate switch moved byte-for-byte. Extracted actual transaction with injected
finish/vendor body compiled/executed strict optimized C11: mode2 finishing
observes both counters and netdev ref held, no short lock held; NULL body does
not invoke finish; prior gate/refusal checks remain passing. Real moved MCS/
rate code and mode1/mode0 runtime not compiled/executed by this fixture. No
claim full WDS function/target build.

Returned peer pointer use beyond these MCS tails, concurrent peer deletion/
reassociation, adapter pinning and retained-netdev final reaper remain open.
Need actual peer-generation ownership and callback/DMA/TxS drain before free.
No router/build/CI dispatch/commit/push. git diff --check passed.


## 2026-10-29 both direct WDS callers handle refused insertion

Caller audit found FindWdsEntry and AsicUpdateWdsRxWCIDTable continue into
RTMPSetSupportMCS after MacTableInsertWDSEntry returns NULL; configured path
also directly writes pEntry->SupportRateMode. Added exact-pinned
prepare-wds-caller-refusal.py: RX returns NULL before updates; configured-link
loop continues, preserving eligibility of later links. Latest scratch
wds-caller-refusal-20261029. This is necessary with new legitimate admission
refusals and does not solve successful returned-entry lifetime.

Source-order assertions and extracted guard fixture strict optimized C11
compile/run passed: NULL RX no update, non-NULL RX update, failed configured
link skipped while next eligible link updates. Actual rate/hardware functions
injected; full caller functions/target not compiled. Need move or cover
successful MCS/rate tail under operation ownership before claiming full race
closure. No router/build/CI dispatch/commit/push. diff --check passed.


## 2026-10-29 WDS outer wrapper holds explicit Linux netdev reference

Extended outer-operation preparer with dev_hold under transition lock only
after registration/radio admission succeeds, and dev_put after all adapter
access/wakeup on structured exit. Existing Linux source already uses these
APIs; this new common-file use still requires target compile/OS scope review.
Latest isolated source wds-netdev-operation-20261029, not full-chain rebuild.

Repeatable extracted wrapper strict optimized C11 test passes one reference
held through vendor body, balanced hold/put on success and NULL body, no hold
when radio/registry admission refuses. dev_hold/put mocked; no kernel lifetime
or memory-order proof. Adapter lifetime is not implied by child-netdev reference;
PCI/module ownership needs independent verification before acceptance.

Caller inventory: two direct insertion callers in ap_wds.c, RX FindWdsEntry
and configured-link creation. Configured-link creation performs additional
peer/rate-field writes after MacTableInsertWDSEntry returns; the current wrapper
count does not span that caller tail. Returned raw MAC entry likewise lacks
association-generation lease. Next extend ownership to actual caller transaction
and check adapter teardown while those returned pointers remain in use.
No router/build/CI dispatch/commit/push. git diff --check passed.


## 2026-10-29 WDS outer hardware work also holds shared radio activity

Extended outer-operation preparer: after exact registration enter, acquire
existing wr_iot_radio_tx_enter under same transition lock. Refusal rolls back
only the newly acquired peer count and never invokes vendor body. Normal
structured leave decrements radio count only after matching peer leave succeeds;
identity failure conservatively retains radio activity. Latest isolated output:
wds-radio-operation-20261029. This is activity admission, not a netdev/module
reference or proof of pending DMA completion.

Updated repeatable outer fixture to real candidate radio-transition header.
Strict optimized C11 extracted-wrapper compile/run passed: active outer body
blocks requested PSE reset admission; already busy radio refuses body and
restores peer count; success/NULL body release both counters and wake waiters.
Reset request in mock body is a simulated interleaving restored by fixture,
not a runtime reset. Initial extractor assumed one peer leave and refused new
rollback branch; now asserts two reviewed leave sites plus one radio enter/leave.

Chain16 prior manifest remains historical; updated final stage run separately,
full 16-stage rebuild not repeated. Remaining lifetime pin/bypass-path audit,
retained WDS reaper, callback/queue/DMA/TxS retirement and target/device gates
remain open. No router/build/CI dispatch/commit/push. diff --check passed.


## 2026-10-29 sixteen-stage source composition and shared-header regression

Extended peer-retirement-chain.py with retained WDS owner, peer fence and whole
outer-operation binding. Rebuilt all 16 stages from pinned full-driver-overlay4
successfully: peer-retirement-chain16-20261029/wds-outer; final manifest records
all source hashes. Added reusable prepare-wds-outer-operation-check.py with
local test template; extracts actual wrapper, no vendor internal body copied.

Against final candidate: strict optimized C11 outer wrapper and peer-ready
publication tests passed. Copied existing registry and auxiliary-close tests
to scratch to ensure candidate headers (not source-directory old headers) used.
New nested operation state exposed {{0}} missing-braces under -Werror; changed
those test zero initializers to {0}, then both registry and aux-close suites
passed. This is host regression evidence, not target/module/device acceptance.
Full old aggregate runner is not compatible with retained WDS remove witness;
do not claim it ran on chain16. Four specific checks ran this turn.

Next actual retained-netdev completion/reaper and all WDS writer/lifetime paths;
peer hardware partial recovery and old DMA/TxS drain remain open. Adapter reset
must not erase operation state while active. No production/router/build/CI
or commit/push changes. git diff --check passed.


## 2026-10-29 active WDS peer operation fences auxiliary close

Extended outer-operation preparer: insertion requires registry OWNED state;
wr_iot_ref_begin_close refuses active peer_operation, and aux_close_reserve
checks active count before radio ticket admission. All changed input headers
now pinned, including aux-close-claim. Latest scratch:
wds-outer-close-fenced-20261029. No source chain/production installation.

Re-extracted actual new outer wrapper and compiled/executed against modified
candidate headers successfully (prior preliminary fixture used old wrapper,
superseded by actual-check). Dedicated aux-close fixture passes active-operation
refusal with unchanged radio serial/busy and OWNED phase, followed by successful
close reserve after leave. Strict optimized C11; kernel/concurrency mocked.
WDS close wrapper currently supports non-last auxiliary close; last-close
physical ownership and whole adapter reset/PM/module lifetime remain separate.

Next inventory bypass writers and bind resumable retained-netdev retirement;
callback/vendor queue and DMA/TxS drain still unproved. No claim of final WDS
or IoT acceptance. No router/build/CI dispatch/commit/push. diff --check passed.


## 2026-10-29 whole WDS insertion wrapper bound to registration operation count

Added prepare-wds-outer-operation.py from exact wds-peer-fenced source. It
embeds peer_operation in each registry reference with fresh initialization,
refuses begin_remove/release while active, and wraps the entire original
MacTableInsertWDSEntry body (renamed static) with one enter/leave cleanup path.
Registry/device/generation/family and PM/removal checked under transition lock.
All original internal early returns now flow back through outer leave. Source:
wds-outer-operation-20261029; not integrated into chain13/production.

Extracted actual wrapper compiled/executed strict optimized C11 using modified
candidate registry headers: success and NULL body return both release active
count/wake; simulated removal/release during body refused without mutation;
post-removal and invalid-index calls do not enter body. Internal vendor body
and kernel primitives injected; no real concurrent execution or target proof.

This closes the modeled outer-tail admission gap through the reviewed wrapper,
not every path globally. Need full caller/module/adapter pin audit, all bypass
writers, callback/vendor packet quiescence and retained-netdev reaper. Count
leave errors retain ownership but currently lack explicit recovery diagnostics;
no claim of automatic eventual cleanup. Source receipt covers changed source,
helper copied locally; target compile and firmware/runtime acceptance open.
No router/build/CI dispatch/commit/push. git diff --check passed.


## 2026-10-29 per-registration WDS operation counter contract staged

Added wds-peer-operation.h and strict host check-wds-peer-operation.c. State
tracks exact device/generation, active outer operations and removal admission.
Tests pass nested operations, active-operation removal refusal without marking,
wrong generation/device release refusal, zero-count underflow refusal,
post-removal entry refusal and unsigned overflow refusal. This is a sequential
candidate contract, not installed in registry or vendor wrapper yet.
Caller owns exactly one enter/leave pair; counter is not a unique per-operation
token and cannot detect duplicate leave while other operations remain. Wrapper
must have one structured cleanup path. Fresh init is only permitted quiescent.

Dedicated per-registration count avoids coupling WDS removal to unrelated
Wi-Fi TX. Next embed state in registration with explicit fresh initialization,
wrap entire MacTableInsertWDSEntry (including lookup return and setup tail),
and atomically share removal admission under transition lock. Adapter/netdev
lifetime pin and global lock order require binding proof. Full WDS retirement,
peer DMA/TxS completion and target/runtime acceptance remain open.
No router/build/CI dispatch/commit/push. git diff --check passed.


## 2026-10-29 WDS common insertion/removal gate bound in isolated source

Added wds-insertion-gate.inc and prepare-wds-peer-fence.py. On retained-owner
scratch, common MacTableInsertEntry checks WDS published exact-generation
registry identity/removing/PM/retirement under transition lock while already
holding MacTabLock. WDS_Remove marks removal first, drops transition lock,
then invokes exact-wdev current peer closure before kernel close/detach.
Source staged as wds-peer-fenced-20261029, not chain13/production.

Strict host check-wds-insertion-gate.c passed ordinary admission, removal mark
before check, already removing, PM/retiring, missing generation/wrong family,
and unchanged non-WDS behavior. Existing exact-wdev closure test reran passed.
Locks injected/sequential scheduling; full global lock-order audit still open.

Important incomplete transaction: MacTableInsertWDSEntry continues configuring
peer state and MacTabMatchWCID after common insertion returns, outside the common
MAC lock. New common gate does not cover this tail. Next use outer WDS operation
ownership/inflight tracking spanning the full wrapper and removal wait/refusal;
otherwise outer tail can race retirement. Do not call the insertion/removal race
fully closed, and do not free retained netdev. Callback/vendor queue retirement,
completion drain and reaper remain open. No router/build/CI/commit/push.


## 2026-10-29 exact-wdev WDS queue admission helper checked

WDS stores MacTabMatchWCID, but stale/zero index cannot safely identify a peer
for cleanup. Added candidate wds-peer-admission.inc scanning current MAC entries
by exact embedded wdev pointer under MacTabLock; validates every matching
nonempty entry is WDS with matching WCID/in-range TR before any mutation.
Then closes only those enq/deq caps under irq_lock, preserving existing MAC ->
IRQ order. This helper is not bound to removal/insertion yet: new WDS insertion
must first be excluded, and no callback/DMA completion join is claimed.

check-wds-peer-admission.c strict optimized C11 compile/run passed exact peer
selection, unrelated main/other wdev and slot0 preservation, wrong family,
mismatched WCID, TR out-of-range and NULL refusal without partial mutation.
Locks and structures injected, no target concurrency proof. Caller must pin
adapter/wdev and not hold these locks. Zero slot is never selected for mutation.

Next bind insertion admission to registry removal under a proven lock order,
then use helper before WDS vendor/queue retirement and actual completion drain.
Do not treat cap closure as ownership/reuse proof. No production/router/build,
CI dispatch, commit or push. git diff --check passed.


## 2026-10-29 retained WDS failure propagates to parent exit

Source trace on wds-detached-owner successor confirms WDS_Remove failure ->
AP ioctl return failure -> RT28xx_WDS_Remove -> RtmpPhyNetDevExit FALSE.
PCI remove directly returns when RtmpPhyNetDevExit refuses, before later
adapter/CSR/root-netdev release operations. This is retention, not eventual
cleanup: parent remove remains incomplete until child reaper can finish.

Added prepare-child-remove-propagation-check.py extracting whole parent exit.
Strict optimized C11 fixture passed failure at each APCLI/WDS/MBSS/monitor
child: later children and main detach are skipped, transition lock released.
Success reaches all four children and main detach. Child functions/kernel
primitives are injected; PCI and ioctl propagation checked by exact source
assertions, not full PCI execution. No claim of module-unload lifetime proof.

Next resumable stage1 WDS completion with real callback/vendor quiescence;
retain adapter ownership through the whole continuation. Current retained
candidate intentionally cannot complete removal and is not production.
No router, firmware/CI dispatch, commit/push. git diff --check passed.


## 2026-10-29 WDS post-unregister allocation retained in isolated candidate

Added prepare-wds-detached-owner.py from exact chain13 WDS source. After actual
detach it records registry_after_unregister under transition lock, retaining
netdev allocation and vendor registration instead of freeing while registry
still publishes identity. Returns failure until a real callback join/reaper
is bound. Existing mark-removing admission rejects a second detach/unregister.
Latest scratch wds-detached-owner-20261029; this is an incomplete ownership
stage, not a working final WDS removal and not integrated into chain13.

Extracted new WDS_Remove with injected kernel primitives passed strict C11:
one detach, stage1 retained, no vendor unreg/free, second invocation no repeat
detach/close, close failure no detach/free. First fixture lacked nonzero registry
generation and assertion failed (correct refusal); corrected fixture generation
then passed. Mark-removing behavior is mocked to match current refusal rule;
no claim of full kernel callback proof. Standalone fixture not shared runner.

Next bind callback/vendor/queued-packet quiescence and finish retirement before
netdev free; add resumable completion owner, adapter lifetime retention and
partial multi-entry removal handling. Returning failure alone is not completion
or eventual cleanup. No production/router/build/CI/commit/push.


## 2026-10-29 WDS checks rerun on thirteen-stage final candidate

Extracted WDS checked-close and WDS_Remove from chain13 hardware-delete and
compiled/executed strict optimized C11 with current host helpers. Checked close
passes same-ticket retry/post-DOWN completion; remove passes refusal retention
and its existing known-defect witness. That witness confirms registry still
holds a published freed device identity after simulated success; this is not
accepted lifecycle behavior. No attempt to manufacture callback/drain proofs.

Added both checks to shared hardware-chain runner, with lifecycle_accepted=false,
explicit known_open_issues and per-test known_unsafe_retirement_witness flag.
Full expanded runner not rerun here; two WDS fixtures ran independently and
prior 14-test report plus separate layout evidence retain their stated scope.
Next implement real post-unregister registry retirement with callback/vendor
quiescence before freeing device, and peer retention/completion protocol.
No production/router/build/CI dispatch/commit/push. git diff --check passed.


## 2026-10-29 actual vendor WTBL address layout checked on host

Added prepare-wtbl-address-layout-check.py extracting real wf_wtblon.h DW0/DW1
unions rather than synthetic fixture layout. Strict optimized C11 compile/run
passed sizeof=4, address bytes4/5 at low16, all 16 address bits visible, all
higher bits excluded, and DW1 full32 address representation. rv/rc_a2 flags do
not pollute the address mask. This is little-endian host compiler evidence,
not MIPS ABI or big-endian verification. Added this fixture to shared runner;
new layout test ran individually, full updated 15-variant runner not rerun.

Periodic CMDTHREAD_MLME_PERIOIDC_EXEC invokes reset drain only under MT7603 +
DMA_RESET_SUPPORT. That is a candidate recovery execution point, not a peer
completion/reuse certificate; RTNL trylock refusal must retain requests and
adapter lifetime must outlive queued work. No direct reset under MacTabLock.
Next derive retained peer ownership and completion drain before insertion
binding. Existing 13-stage source and 14-test report remain valid for prior
scope; production/target/runtime remain open. No router/build/CI/commit/push.


## 2026-10-29 thirteen-stage candidate reproduced; fourteen host checks pass

Extended prepare-peer-retirement-chain.py to include invalid-BSS unlock,
WTBL setup status/refusal, caller-ready publication, checked hardware add and
checked bounded deletion/address readback. Rebuilt all 13 stages from pinned
full-driver-overlay4 into peer-retirement-chain13-20261029/hardware-delete;
peer-chain.json records script and final file hashes. Layout guard executed.

Added check-peer-hardware-chain.py, running extracted fixtures against one
final candidate. Fourteen strict optimized C11 host variants passed; report
.iot-local-check/peer-hardware-chain13-checks2-20261029/result.json includes
flags and fixture hashes. Covers peer-ready, full delete, hardware preflight,
timeout, deletion admission, EOSP, UAPSD, reset and dequeue variants.
First run stopped at the reset extractor's obsolete VOID setup boundary;
updated it to accept exactly one reviewed VOID or BOOLEAN declaration, reran
whole suite successfully. Failure results are retained; runner initializes
passed=false and only marks true after every test succeeds.

This is reproducible source/host composition, not whole driver/target compile.
WDS wrapper/removal tests not in this 14-test batch. Hardware checked functions
are not bound to insertion or retained-peer recovery; old-completion identity,
DMA/TxS drain, APCLI/monitor composition and release/image/device gates remain
open. Next explicit recovery ownership and exact bind before target build.
No router, firmware/CI dispatch, commit or push. git diff --check passed.


## 2026-10-29 checked deletion verifies zero peer address by readback

Extended prepare-wcid-delete-result.py with end-of-entry MMIO readback before
IndirectUpdateLock release: DW0 low16 (address bytes4/5) and DW1 (bytes0..3)
must be zero; residual address returns PARTIAL with lock release. Reviewed
wf_wtblon.h endian declarations and added layout-shape refusal in preparer.
Mask does not compare mutable status/flags. Latest isolated successor is
wcid-delete-readback-20261029. This intentionally strengthens prior bounded
candidate; whole-source reconstruction claim no longer applies.

Updated whole deletion fixture with independent corruption of either address
word. Strict optimized C11 PCI+MT_PS and base variants passed all prior timeout,
range/ALL and lookup cases plus both readback mismatches -> PARTIAL, balanced
locks. Synthetic MMIO/layout, not actual WTBL hardware or target ABI proof.
The layout-shape guard added after successful generation was syntax-reviewed;
it has not been exercised by regenerating the entire source in this turn.

Address-clear readback is only one retirement condition: keys/BA state, queued
packets, in-flight DMA and delayed TxS/completion identity remain independent.
Do not release partial WCID or call IoT accepted based on these tests.
Next bind retention/recovery and verified old-completion drain. No router,
build/CI dispatch, commit/push. git diff --check passed.


## 2026-10-29 bounded deletion prevents WTBL helper aliasing

mt_wtbl_get_entry234 only calculates addresses and silently clamps out-of-range
widx to the final WTBL entry; it does not read hardware contents. Checked
deletion now refuses an empty table/invalid individual WCID before lookup and
bounds WCID_ALL to actual UINT8 table count. Latest scratch:
wcid-delete-bounded-20261029. This intentionally changes legacy wrapper behavior
for invalid input/ALL beyond physical table, eliminating repeated aliased writes;
previous blanket preservation/reconstruction claim is historical, not this stage.

Updated full deletion fixture and ran strict optimized C11 PCI+MT_PS and base
variants successfully. Includes prior failure injections, four-entry ALL bound,
invalid individual and zero-table no-lookup/no-write refusals, and maximum
255-entry ALL termination (765 commands). Synthetic layout/MMIO; no target proof.

Deletion zero-initializes its local WTBL words; address helper fills locations,
not previous contents. No direct peer-address readback is currently performed.
Next verified address-clear readback under established ownership plus old
completion drain; command completion alone must not release retained WCID.
No router/build/CI dispatch/commit/push. git diff --check passed.


## 2026-10-29 whole checked deletion failure injection passes on host

Added prepare-wcid-delete-check.py extracting the complete checked deletion
function, not just timeout tails. Synthetic MMIO, WTBL lookup and register
layout permit strict host compilation; this is not target layout/ABI evidence.
Tests passed with PCI+MT_PS and without both: lookup failure before writes ->
NOT_WRITTEN; each of three poll-command timeouts -> PARTIAL with 100 delays;
single-entry success; WCID_ALL second lookup failure after first entry writes
-> PARTIAL; all 255 entries success with 765 command submissions. PCI acquire/
release balance verified. No real register-readback or DMA/TxS drain claimed.

Initial fixture helper triggered misleading-indentation under -Werror;
braces corrected, then both strict optimized C11 variants compile/run passed.
Final fixture is reproducible from candidate using the new generator. These
checks strengthen failure-control-flow evidence but do not authorize releasing
WCID after partial hardware state or after successful command polling alone.

Next retain ownership until verified hardware clear plus old completion drain,
and bind asynchronous recovery with adapter pin/retirement discipline. Target
compilation and device acceptance remain open. No router/build/CI dispatch,
commit or push. git diff --check passed.


## 2026-10-29 checked hardware deletion result staged

AsicDelWcidTab also has VOID early returns: WTBL lookup failure plus three
post-write busy timeouts. Added exact-pinned prepare-wcid-delete-result.py,
staging wcid-delete-result-20261029. INT wr_iot_delete_wcid_checked returns
NOT_WRITTEN until first register write, PARTIAL after any write, APPLIED after
existing loops complete. The wrote flag is outside the WCID_ALL loop, so a
later entry lookup failure cannot hide earlier writes. Legacy VOID wrapper
is retained and the declaration is within existing MT guard.

Structural checks passed four result returns and flag-before-first-write;
undoing result conversion/flag instrumentation exactly reconstructs the original
complete deletion function. No target C compile or MMIO/driver test performed.
Existing register, lock and bounded polling operations are unchanged. APPLIED
is not hardware readback, DMA/TxS drain or permission to reuse a peer slot.
The original WCID_ALL semantics are preserved, not newly validated.

Next full-function failure-injection and verified clear/drain boundary before
binding recovery to peer reuse. No insertion recovery binding or production
installation yet; no router/build/CI dispatch/commit/push.


## 2026-10-29 reset owner cannot yet release partial WCID

Reviewed reset-admission.inc: wr_iot_radio_reset_drain uses rtnl_trylock,
transition ticket and raw PSE/PDMA call, then finish_unverified. Raw VOID return
is explicitly not hardware success. Existing main-open recovery owner owns a
netdev close/open ticket and module pin, not a peer WCID. Neither is currently
a WCID reuse/drain certificate. Never call reset-drain while holding MacTabLock:
this would add RTNL acquisition inside the MAC lock and can perform long reset.
A peer failure hook must only queue an owned request after exact lock/lifetime
review; software pending bit alone does not establish eventual recovery.

Reran strict optimized C11 check-radio-transition.c successfully; sequential
reset/readiness model remains fail-closed. This does not test real reset/WCID
hardware. Added prepare-wcid-preflight-check.py to replace prior ad-hoc fixture;
actual header UINT8[4] and USHORT widths are checked. Extracted preflight GCC
compile/run passed unavailable table/out-of-range refusals and valid indices.

Next derive explicit per-peer retention plus asynchronous adapter recovery
binding with pinning and a verified hardware-clear/completion-drain boundary.
Do not clear retained WCIDs on finish_unverified. Full implementation/target
build/runtime remains open. No router, CI/build dispatch, commit/push.


## 2026-10-29 four hardware timeout branches extracted and tested

Added prepare-wcid-timeout-check.py, extracting all four actual poll/timeout
branches from strict checked WCID candidate. Strict optimized C11 host tests
passed PCI and non-PCI variants: busy through 100 reads returns PARTIAL with
100 bounded 50us delay calls; clear on read 100 succeeds with 99 delays;
clear immediately succeeds with one read. PCI timeout releases IndirectUpdateLock;
first timeout restarts AC queues after that release. Follow-up PCI fixture
explicitly checks restart lock state. MMIO/delay/locks injected, no real timing.

Successful extracted block intentionally retains the lock, matching that its
normal release exists outside the extracted timeout block. These tests do not
claim full-function transaction ordering or partial hardware cleanup. Other
three timeouts do not issue AC restart locally because earlier success path
already restarted queues. Full driver compile and target MMIO acceptance open.

Next bind PARTIAL to an explicit retained WCID/adapter recovery owner before
insertion integration; never mark partial hardware state reusable based solely
on these return/lock checks. No router, firmware build, workflow dispatch,
commit or push. git diff --check passed.


## 2026-10-29 checked WCID preflight refuses multicast aliasing

Updated prepare-wcid-hardware-result.py: checked result API now refuses WCID
outside the available table before register writes. Legacy VOID wrapper alone
retains historical invalid-index -> MCAST_WCID mapping. Latest isolated output
wcid-hardware-strict-20261029 supersedes the earlier clamping checked output.
No insertion binding or PARTIAL recovery owner is claimed.

Extracted actual preflight compiled and passed zero table, boundary index,
maximum USHORT refusal (no simulated write), and valid first/last entries.
Initial fixture used incorrect signed int table count and hit -Werror; inspected
actual rtmp.h UINT8 wtbl_entry_cnt[4], corrected mock to unsigned char[4] and
WCID to unsigned short, then strict optimized C11 test passed. This tests only
preflight, not MMIO body/legacy wrapper behavior on hardware. Prior exact whole
function reconstruction applies only to the earlier mechanical version; strict
API intentionally differs at index validation. Do not extend old proof.
No router, build, CI dispatch, commit/push. Next PARTIAL ownership/recovery and
full-function fixture before binding to insertion.


## 2026-10-29 MT WCID checked result candidate preserves legacy wrapper

Inspected all AsicUpdateRxWCIDTable returns: two before any register writes
(PSE unavailable, WTBL lookup failure), four busy timeouts after partial writes.
Added prepare-wcid-hardware-result.py; isolated wcid-hardware-result-20261029
exposes INT wr_iot_update_rx_wcid_checked with NOT_WRITTEN/PARTIAL/APPLIED.
Legacy VOID AsicUpdateRxWCIDTable wrapper remains and ignores result, preserving
existing callers. MT-only declaration/constants avoid claiming RLT support.
Original clamping behavior remains; checked caller must still validate WCID.

Source verification passed: two prewrite and four partial-write returns; undoing
only mechanical status conversion reproduces the original complete function
exactly. All existing register, bounded poll, lock release and AC queue restart
operations are preserved. This is structural verification, not C compilation,
MMIO success or a hardware test. APPLIED reflects existing observed command
completion, not WTBL readback, peer lifetime or security installation proof.

Not yet bound to insertion: PARTIAL must retain/recover an owned WCID rather
than use preallocation rollback/reuse. Other hardware-key errors still return
VOID. Next implement recovery ownership for partial hardware installation and
bind statuses with full initialized-resource unwind. No router/build/CI,
commit or push; production driver unchanged.


## 2026-10-29 insertion side-effect path and repeatable publication check

MT PCI RTMP_STA_ENTRY_ADD maps to VOID AsicUpdateRxWCIDTable; MT_ADDREMOVE_KEY
maps to VOID CmdProcAddRemoveKey. AsicUpdateRxWCIDTable in cmm_asic_mt.c
returns early if PSE WTBL entry count is zero or mt_wtbl_get_entry234 fails;
caller cannot distinguish this from success. Therefore the prior TR setup
BOOLEAN fix does not prove hardware installation succeeds. Do not enable
acceptance merely because final cap stores run. Hardware WCID status/rollback
needs its own review across shared callers before changing its ABI.

Optional wf_fwd_add_entry_inform_hook runs before the new publication point;
no assignment/implementation was found in this driver source. Its external
contract and effective target feature flags remain unverified. Do not infer
absence from the driver-only search. MTFWD event also precedes publication.

Added reusable prepare-peer-ready-publication-check.py (previous fixture was
scratch-only). It validates source ordering and extracts actual final block.
Strict optimized C11 compile/run passed NULL refusal and two IRQ-held TRUE
stores. Hardware status/callback behavior deliberately excluded. This check
is now reproducible without the earlier ad-hoc extraction command.
No target build, firmware, router, CI dispatch, commit or push. Next examine
hardware-add return paths and target feature flags, then adapt publication
and failure unwind together; stale completion identity remains open.


## 2026-10-29 caller-ready unicast publication staged and checked

prepare-peer-ready-publication.py pins the fenced WTBL-result input and stages
peer-ready-publication-20261029. Unicast TR setup explicitly disables caps
under irq_lock before field writes and no longer publishes TRUE. The insertion
caller publishes only for non-NULL pEntry at its final MacTabLock-owned point,
after timers, UAPSD initialization and hash insertion. Multicast publication
is unchanged. Prepared source has matching BOOLEAN setup prototype from prior
stage. No claim that disable alone permits safe TR reinitialization.

Source-order assertions pass for timers/UAPSD/hash before publication and no
TRUE stores in unicast setup. Extracted final block strict optimized C11 host
test passes NULL/no-publication and non-NULL/two locked TRUE stores with IRQ
release. This is not full function, kernel lock/concurrency or target proof.

Remaining before accepting this ordering: preceding RTMP_STA_ENTRY_ADD,
MT_ADDREMOVE_KEY and optional forwarding notification hooks may produce side
effects/traffic while caps are closed. Audit their contracts before production
integration. Prior readiness audit assumes VOID signature and is now obsolete
for this successor; retain it as historical finding witness, not current gate.
Whole-function setup failure/feature unwind, completion identity/drain, target
build and runtime acceptance remain open. No router/build/CI/commit/push.


## 2026-10-29 WTBL setup result and prepublication refusal staged

prepare-tr-setup-result.py changes the exact-pinned TR function/prototype to
BOOLEAN, returns FALSE on WTBL failure/out-of-range, TRUE after setup. Sole
insertion caller checks failure before timer initialization/hash publication.
An explicit counted-client flag reverses only actual StaCount/EntryClientCount
increments. Failure disables both caps under irq_lock, marks TR/MAC NONE,
releases MacTabLock and returns NULL. No normal deletion/free of uninitialized
queue locks/timers or borrowed APCLI pointers is attempted.

Latest scratch tr-setup-result-fenced-20261029 supersedes unfenced first output.
Extracted failure branch strict C11 optimized host test passes count rollback,
non-counted refusal, success continuation, one MAC unlock and IRQ-held FALSE
stores clearing prior TRUE caps. Earlier unfenced branch also passed AP/noAP
variants; final fenced variant was checked with CONFIG_AP_SUPPORT only.
Source assertions confirm WTBL failure precedes queue-lock allocations.
This is not full-function compile, target ABI or full-resource lifetime proof.

UAPSD initialization/publication order, stale completion/reuse ownership,
feature-specific borrowed references and full insertion unwind still need
review; final driver/image/device acceptance remains open. No router, firmware
build, workflow dispatch or new commit/push. Next move publication to the
actual caller-ready boundary and verify setup failure with whole-function
fixtures before integration.


## 2026-10-29 invalid-BSS insertion lock leak repaired in candidate

WTBL unwind review found another concrete early-return defect: ENTRY_CLIENT
insertion holds MacTabLock but func_tb_idx >= HW_BEACON_MAX_NUM returns NULL
without releasing it. Added exact-pinned prepare-insertion-bss-unlock.py;
isolated insertion-bss-unlock-20261029 now releases the lock on that refusal.
Extracted actual branch compiled with strict optimized C11 and passed invalid
index (one unlock, NULL) and valid index (lock retained, entry returned).
This is a branch fixture, not complete insertion or hardware validation.

Before WTBL setup, client StaCount/EntryClientCount have already incremented;
APCLI feature branches may copy key/cache/ECDH pointers. Do not perform generic
MacTableDeleteEntry on WTBL failure: TR queue locks and timers are not yet
initialized. Next design exact prepublication unwind, decrement only actually
incremented counters and distinguish borrowed pointers. WTBL status propagation,
UAPSD-before-publication, callback/reuse identity remain open.
No firmware/target build, CI dispatch, production/router change, commit/push.


## 2026-10-29 full eight-stage composition verified; insertion not ready

Rebuilt prepare-peer-retirement-chain.py from full-driver-overlay4 into
.iot-local-check/peer-retirement-chain8-20261029/publication. All eight source
stages completed and the final manifest was written. Nine extracted strict
C11 optimized host variants passed on that final output: publication, delete
with/without UAPSD, EOSP, reset with/without reserve, UAPSD insertion, dequeue
base/combined features. checks/result.json records actual host evidence.

Added audit-tr-insertion-readiness.py. --require-ready correctly exits 1 for
the current candidate, with two concrete source findings: WTBL lookup failure
returns from VOID tr_tb_set_entry before queue initialization while insertion
continues without a status; caller UAPSD_MR_ENTRY_INIT follows the callee's TR
publication. Thus previous final-TR-field ordering fix is partial, not complete
MAC/peer readiness. The audit deliberately never grants readiness; it is a
bounded finding recorder, not a complete acceptance verifier.

Next propagate setup failure with exact resource unwind and defer enable until
required caller initialization completes; account for feature-conditional
pre-insertion resources before clearing/reusing any entry. Then continue actual
completion identity/drain. No target build/device/production acceptance and no
new commit/push, firmware build or router changes.


## 2026-10-29 CI 637 green; final TR publication candidate checked

GitHub reads confirm commit 88938ffed3db5bbe6fdd7363213322467c833a6d:
firmware #637 run 40915970985 success; ABI 40915970699 success; service checks
40915960152 success. These use committed sources, not the dirty local peer
chain or the new publication candidate. No final artifact/device acceptance
was performed in this turn.

Added prepare-tr-capability-publication.py with exact mgmt_entrytb.c input
hash. In isolated tr-publication-20261029 it moves both unicast/multicast TRUE
caps to the end of TR setup after bssid/queue/lock/counter initialization,
using WRITE_ONCE under irq_lock. Moves DATA_QUEUE_RESERVE initial values into
unicast TR setup and removes duplicate writes in its insertion caller.
prepare-tr-capability-publication-check.py verifies source order and extracts
both real final publication blocks: strict optimized C11 compile/run passed
IRQ-held stores and balanced unlock. This is not full-function/target or
concurrency acceptance. TR reinitialization ownership and WTBL-failure unwind
remain unproved; no claim that all MAC entry initialization is now complete.

The peer chain preparer now lists this as eighth stage, but that updated full
chain was not rerun here; the standalone eighth stage was run on the verified
seven-stage final output. Next integrate submission/completion generation or
verified drain and target-active ownership, retaining lock order. No router,
firmware build, CI dispatch, commit/push after the checkpoint publication.


## 2026-10-29 DMA packet ownership inventory and lock-order constraint

Added audit-peer-dma-ownership.py and ran against the composed peer candidate.
Local peer-dma-ownership-reviewed-20261029.json records 76 lexical slot writes
in six C files (42 primary, 34 secondary; 63 NULL stores), with source hashes,
paths and line numbers. Equality comparisons are excluded. Counts include RX,
comments/inactive feature branches; they are coverage leads, not 76 active
transmit sites. No vendor source text is embedded in the report.

MT branch of RTMPHandleTxRingDmaDoneInterrupt calls RTMPFreeTXDUponTxDmaDone
with irq_lock held; that completion invokes UAPSD_SP_PacketCheck. Deletion
already takes MacTabLock -> irq_lock. Therefore a naive completion change
acquiring MacTabLock would invert this order. RTMP_DMACB has both pNdisPacket
and pNextNdisPacket: any generation metadata must cover both, every write/clear,
reset cleanup and management paths. DMA identity is not proof of later hardware
TxS/FIFO report identity. Current code adds no such metadata yet.

Next derive target-active submission/recycle sites from this pinned inventory,
then implement a generation or verified drain protocol without reverse nested
locks. TRUE capability publication, failed deletion recovery and remaining
auxiliary families/target image/device checks remain open. No firmware build,
CI dispatch, router changes, commit or push. git diff --check passed.


## 2026-10-29 seven peer-retirement stages composed and tested together

Added prepare-peer-retirement-chain.py. From the full-driver-overlay4 input it
reproducibly stages WDS reconciliation -> dequeue -> PS -> UAPSD -> reset
writer -> deletion join -> three EOSP rejection fixes. Every child preparer
retains its exact input checks. Successful workspace:
.iot-local-check/peer-retirement-chain-20261029, final candidate eosp/.
peer-chain.json records scripts and SHA256 of every final file. This remains
local vendor scratch, not publishable source or an accepted production merge.

Eight strict optimized C11 host variants passed against extracted final-source
blocks: deletion admission with/without UAPSD, three EOSP rejection tails,
reset with/without DATA_QUEUE_RESERVE, UAPSD insertion, dequeue base and
MAX_CONTINUOUS_TX_CNT+DATA_QUEUE_RESERVE+MT_PS. Results in checks/result.json.
Initial dequeue compile lacked the helper include path; corrected test command
uses -Itools/iot, then all eight compile/run checks passed. No target compile.
WDS source preparation passed, but its full wrapper/removal checks were not
rerun in this batch; do not extend the eight-test claim to WDS runtime.

RTMP_DMACB has pNdisPacket/pNextNdisPacket software ownership slots, a possible
place for per-submission identity without guessing spare skb CB bytes. Actual
submission/recycle/second-packet paths and MT completion support still need
review before adding metadata. TR TRUE publication and late-completion/reuse,
APCLI/monitor and remaining driver merge/image/runtime gates are open.
No firmware build, CI dispatch, production install, router change, commit/push.


## 2026-10-29 late-completion identity gap reproduced with extracted lookup

Added prepare-uapsd-lookup-reuse-check.py, extracting the actual vendor
MacTableLookup from the current EOSP successor. Optimized strict C11 GCC
compile/run passed a witness: a saved pointer observes a reallocated slot,
and a fresh delayed lookup by the old MAC address resolves the replacement
association. Generation is an injected test field only, not a driver feature.
This models the problematic interleaving; it is not on-device reproduction.

Source chain: common/cmm_data_pci.c passes DMA packet/frame data into
UAPSD_SP_PacketCheck and UAPSD_QoSNullTxMgmtTxDoneHandle; common/uapsd.c
looks up Addr1 before UAPSDEOSPLock (lines 645 and 904 in scratch). The lookup
returns a raw pointer without a lease. mac/rtmp_mac.c also resolves FIFO WCID
directly before UAPSD_SP_AUE_Handle, but this legacy path's active target
configuration is unproved. include/os/pkt_meta.h stores WCID in CB offset 2;
that byte alone is not association generation. Do not allocate spare skb CB
bytes without complete shared-layout/clone-path review.

Next work must provide packet/ring submission identity and completion ownership,
or an actual bounded DMA/completion drain preventing reuse; a caps check,
MAC recheck or short UAPSD lock alone cannot reject an old completion after
same-MAC reassociation. Also audit publication: tr_tb_set_entry currently
publishes TRUE caps before PsTokenFlag/bssid final initialization; multicast
has another writer. Do not fix only FALSE writers and claim protocol complete.
Existing isolated queue fixes remain candidates; full source integration,
MIPS build and device acceptance are open. No router, build, CI, commit/push.


## 2026-10-29 stale EOSP ownership fixed in isolated successor

Source audit found three enqueue-failure early returns that released the shared
pUAPSDEOSPFrame but left its pointer non-NULL: UAPSD_SP_PacketCheck,
UAPSD_QoSNullTxMgmtTxDoneHandle and UAPSD_SP_AUE_Handle (the last has
UAPSD_SP_ACCURATE feature guards; target applicability not asserted).
A later retirement could release this stale pointer again. Added exact-pinned
prepare-uapsd-eosp-release.py: only these three failures now clear shared
ownership and release the already captured pPkt. Full inventory comparison
confirms only common/uapsd.c changed relative to deletion-joined scratch.
Authoritative new scratch: .iot-local-check/uapsd-eosp-release3-20261029;
its sibling -eosp-release.json authenticates changed source bytes. Earlier
two-site scratch is superseded, retained without deletion.

prepare-uapsd-eosp-release-check.py extracts all three actual rejection tails.
Strict C11 -Wall -Wextra -Werror -O2 host compilation/execution passed:
shared pointer NULL at release, exactly one release, balanced unlock and no
remaining EOSP ownership for subsequent cleanup. Locks and packet handling
are injected; this is not the full callback or target build. No production,
router, CI dispatch, firmware build, commit or push changes.

Remaining: callback reference lifetime and stale completion identity across
WCID reuse; trigger/reinitialization admission; disabled-entry failure recovery;
WDS/APCLI/monitor removal composition, full prepared-source merge, target build
and device acceptance. Do not treat the queue fixes as proof of whole peer
retirement. Next inspect lookup-before-UAPSD-lock and completion identity,
then bind an actual retirement/reuse protocol rather than relying on booleans.


## 2026-10-29 deletion admission checked on host

Verified existing isolated uapsd-delete-joined-20261029 scratch output against
its three source hashes and exact helper bytes. Added repeatable extractor
prepare-uapsd-delete-join-check.py for the actual admission block following
the verified peer-address branch, before TR destruction. Strict optimized
C11 host GCC checks pass with and without UAPSD_SUPPORT: disabled caps under
IRQ lock, helper after IRQ unlock with MAC owner held, helper failure releases
MAC owner and bypasses the simulated destructive continuation. Independent
queue helper test passes again. Original ral_ps.c/mt_ps.c bytes are unchanged.
The preparation receipt now includes the helper hash for future outputs;
the existing scratch receipt remains the earlier three-file receipt.

Scope is narrow: surrounding earlier notifications/timer cancellations are
not rolled back; failure retains a disabled entry without a recovery owner.
Injected locks do not prove callback quiescence, DMA/RX drain, WCID reuse or
whole MacTableDeleteEntry transaction safety. Candidate is not production.
Next audit UAPSD service-period callbacks and initialization/reuse against
this admission; resolve ownership/recovery before merging full driver.
Branch codex/wr1200js-service-webui, HEAD fcf45d7. git diff --check passed.
No target build, workflow dispatch, commit/push or router changes.


## 2026-10-29 dedicated UAPSD retirement helper staged

Global UAPSD_MR_ENTRY_RESET cannot be replaced indiscriminately: callers also
exist in ral_ps.c and mt_ps.c during PS transitions. The macro itself performs
queue/EOSP cleanup without taking UAPSDEOSPLock. QueueMaintenance returns
immediately and is not an available retirement join.
Added isolated uapsd-retire-queues.inc: caller must pin MAC entry/exclude WCID
reuse and disable caps; helper checks caps under UAPSD lock, detaches four
queues/EOSP and resets SP fields, unlocks, then releases private packets.
No irq_lock nesting or packet free while UAPSD lock is held. Dedicated host
test passes enabled-cap refusal, five exact releases, cleared shared queues,
idempotence and invalid/null entry rejection with strict optimized C11 GCC.
ABI step stages sanitizer/MIPS helper tests but no run dispatched.
Helper is unbound: service-period callbacks after unlock, initialization/reuse,
MAC ownership and actual lock-context integration still need proof. This
joins queue mutation only, not DMA/RX or the entire peer lifetime.
Next bind narrowly to deletion-only flow with exact lock/lifetime ownership;
retain existing power-save macro behavior elsewhere. No production/router,
MIPS result, firmware build, workflow dispatch, commit or push changes.


## 2026-10-29 reset capability writer staged under queue lock

Pinned C inventory has one tr_tb_reset_entry caller, MacTableDeleteEntry,
under MacTabLock. Existing rtmp_tx_swq_exit already establishes MacTabLock ->
irq_lock edge. prepare-wcid-reset-writer.py now stages WRITE_ONCE(FALSE) for
both caps under irq_lock, releasing it before cleanup (which locks itself).
Output wcid-reset-writer-20261029; no WDS removal/writer binding yet.
prepare-wcid-reset-writer-check.py extracts actual reset: strict C11 GCC base
and DATA_QUEUE_RESERVE tests pass locked stores, unlocked cleanup/free-lock
sequence, NONE-repeat and out-of-range rejection. Caller locking and real
cleanup are injected, not concurrency proof. Input/output hashes in writer
receipt. Initialization TRUE publication and UAPSD join still unverified;
this partial change must not be called a complete capability protocol.
Next inspect UAPSD entry reset/service-period references and bind the separate
post-disable join without inverse nested locks, then initialization/reuse.
DMA/RX, final scheduler accounting and device acceptance remain open.
No router, target build, workflow dispatch, firmware build, commit or push.


## 2026-10-29 isolated UAPSD insertion fence tested

prepare-wcid-uapsd-fence.py pins common/uapsd.c and inserts READ_ONCE(enq_cap)
plus WCID bound/capacity checks under UAPSDEOSPLock immediately before actual
head/tail insertion. No nested irq_lock introduced. Existing source has
UAPSD-lock -> rtmp_enq_req(...FALSE) -> irq_lock paths (uapsd.c:297/313/330);
retirement must not introduce inverse nested order. Writer/join remains unbound.
prepare-wcid-uapsd-check.py extracts actual insertion function; strict C11 GCC
passes disabled admission, allowed tail/head, capacity changed at lock entry,
invalid WCID and null entry with balanced mock lock and single packet drops.
Output wcid-uapsd-fenced-20261029 and wcid-uapsd-insertion-20261029.c/.exe.
READ_ONCE/locks are injected host primitives; kernel concurrency, current
writer publication and joining active UAPSD operations are not established.
Next bind capability writers under normal queue lock, then separate UAPSD
join without holding irq_lock, before selective cleanup. Other UAPSD service
period producers/consumers, DMA/RX and scheduler report accounting remain open.
No production binding, router, MIPS build, workflow, commit or push changes.


## 2026-10-29 legacy/MT PS producer fences staged

prepare-wcid-ps-fence.py verifies the preceding dequeue receipt and pinned
legacy PS source, then inserts enq_cap plus capacity check inside the actual
irq_lock before legacy PS enqueue. MT PS-retrieve capacity branch also checks
enq_cap under its existing IRQ lock. Output wcid-ps-fenced-20261029 is isolated;
no writer fence/removal binding or UAPSD claim. UAPSD enqueue uses a different
UAPSDEOSPLock, so it needs explicit lock-order reconciliation.
Actual RtmpInsertPsQueue extracted and tested with non-UAPSD delivery: blocked
admission drops once, allowed enqueue succeeds, capacity filled at lock
acquisition rejects without insertion, lock balanced. Strict C11 GCC passed.
Reproducible extractor added: prepare-wcid-legacy-ps-check.py. MT retrieve
change is source-only (full parser fixture/target compile pending).
Next verify same-lock capability writers and UAPSD synchronization, then full
scheduler accounting/DMA/RX. No production, MIPS/runtime, firmware-build,
router, workflow dispatch, commit or push changes.


## 2026-10-29 actual dequeue selector candidate bound and host-tested

All pinned deq_cap writers were reviewed: FALSE only during tr_tb reset;
TRUE during initialization. New prepare-wcid-dequeue-fence.py pins the exact
queue source and stages a separate tree. Targeted selection refuses disabled
WCID; global selection drops only its scheduling tokens in place and skips
holes using bounded helper scans, preserving other packet FIFO indices.
No production tree change and no WDS removal binding yet.
prepare-wcid-dequeue-check.py extracts actual rtmp_deq_req between reviewed
function boundaries. Strict C11 GCC tests pass base, MAX_CONTINUOUS_TX_CNT,
DATA_QUEUE_RESERVE and MT_PS variants: disabled peer head, neighboring peer,
empty/full ring, targeted refusal and malformed WCID. Kernel locks/PS request
callbacks injected; full dequeue/report packet accounting still not proved.
Outputs wcid-dequeue-fenced-20261029 and wcid-dequeue-selector-20261029 plus
variant binaries under .iot-local-check. Producer fences (normal/PS/UAPSD),
writer locking, DMA/RX and exact-generation removal remain necessary before
admission. Next reconcile those producer paths and test full scheduler report
accounting; do not treat source selector pass as complete peer drain.
No router, MIPS build, workflow dispatch, firmware build, commit or push.


## 2026-10-29 noncompacting WCID FIFO helper candidate

Added wcid-fifo-retirement.h: under caller-owned IRQ lock and externally
established peer fences, removes only matching tokens in place, then locates
next nonzero slot with a bounded full-ring scan. Companion selector supports
holes regardless of MAX_CONTINUOUS mode without relocating packet indices.
check-wcid-fifo-retirement.c exhausts 2592 four-slot layouts/index pairs/peer
choices, checks survivor positions, empty/full ambiguity, idempotence and
invalid-input nonmutation. Strict optimized GCC execution passed.
ABI successor step now stages sanitizer host execution and MIPS object check;
workflow not run. This helper is not yet bound to vendor enqueue/dequeue or
WDS removal; it does not free packets, prove DMA/RX retirement or authorize
WCID reuse. Next source integration requires complete same-lock producer
fences and mode-specific token/accounting review before binding cleanup.
No production state, router, firmware build, workflow dispatch, commit/push.


## 2026-10-29 WCID queues and global scheduler tokens must retire together

rtmp_deq_req has separate targeted-WCID and global-FIFO selection. Existing
rtmp_tx_swq_exit frees peer tx_queue/PS packets but does not touch tx_swq WCID
tokens. Extended extracted host fixture with FIFO witness: target packets
freed, neighboring queues preserved, target scheduling tokens unchanged.
Strict C11 GCC execution passed (wds-queue-token-witness-20261029.c/.exe).
Under MAX_CONTINUOUS_TX_CNT, enqueue stores FIFO index on packet and dequeue
report accesses CurSwqIdx. Therefore naive FIFO compaction can invalidate
other peers' packet indices. Merely zeroing a slot also differs between modes
(the basic selector treats zero at deqIdx as empty, while extended mode skips).
Receipt wds-global-fifo-audit-20261029.json. Next define same-lock retirement
of peer queues AND scheduler tokens, respecting mode-specific index/accounting
and refusing WCID reuse until DMA/RX identities retire. Do not call existing
cleanup a complete WDS drain. No production patch, MIPS/runtime acceptance,
router, firmware build, workflow dispatch, commit or push changes.


## 2026-10-29 selective enqueue/dequeue fence gaps established

rtmp_enq_req checks enq_cap while holding irq_lock (or caller-supplied lock).
RTMPDeQueuePacket holds irq_lock through select/gather/hard_tx but deq_cap is
only a TODO at cmm_data.c:3688, not enforced. PCI rtmp_inf_pcirbs.h:26/27
START/STOP_DEQUEUE macros are empty. DeQueueRunning is therefore not a proven
PCI per-peer consumer counter. PS producers ps.c:79 and MT retrieve
cmm_data.c:750 enqueue under irq_lock without enq_cap. Queue cleanup takes
that lock per queue but cannot prevent subsequent re-enqueue by itself.
Receipt/hashes: wds-enqueue-dequeue-fences-20261029.json.
Next candidate must enforce same-lock per-peer admission across normal/PS
producers and consumers, preserve FIFO accounting, and then establish DMA/RX
lifetime separately. Merely clearing enq_cap/deq_cap or polling PCI running
flags is insufficient. No speculative shared networking change made; the
existing selective-cleanup host test remains selection-only evidence.
Production lifecycle/target/runtime remain unverified. No router, workflow,
firmware build, commit or push changes.


## 2026-10-29 selective vendor WCID cleanup verified on host

Found existing rtmp_tx_swq_exit in cmm_data.c:2715: explicit WCID selects
only that tr_entry's WMM/PS queues; WCID_ALL is separate. tr_tb_reset_entry
(mgmt_entrytb.c:76) disables enq_cap/deq_cap then invokes it and frees queue
locks; cleanup has its own TODO about enq_cap protection. Do not call the
whole reset as a selective drain proof without producer/consumer joining.
New prepare-wds-queue-check.py extracts actual cleanup into injected host
queues. Strict C11 GCC run passed: WCID1 frees only its three fixture packets,
other two peers untouched, invalid WCID rejected and ENTRY_NONE skipped.
Output .iot-local-check/wds-queue-selectivity-20261029.c/.exe.
This establishes selector behavior only, not concurrent admission, dequeue
ownership, DMA completion, RX retirement or netdev callback quiescence.
Next reconcile per-peer enqueue/dequeue fences and in-flight work before
using this vendor primitive in exact-generation WDS removal.
No production binding, MIPS compile, firmware build, router, workflow,
commit or push changes.


## 2026-10-29 WDS OS-TX lease is not queue/DMA retirement

WDS ndo_start_xmit is rt28xx_send_packets. Its transition active_tx lease
covers rt28xx_packet_xmit return, and AUX_CLOSE admission refuses active_tx.
This protects the synchronous entry only. ApWdsAllowToSendPacket stores the
wdev index on packets; RTMPSendPackets invokes tx_pkt_handle and bounded
RTMPDeQueuePacket(MAX_TX_PROCESS), so return is not queue-empty evidence.
Additional dequeue entrypoints exist in UAPSD and other paths outside the
OS-entry lease. Direct WDS TX readers can therefore outlive the lease via
queued packets. Source inventory/hashes at wds-tx-queue-audit-20261029.json
includes raw comments/definitions/inactive branches, not target-active count.
Do not bind callbacks_quiescent or registry release to active_tx==0 alone.
Next design selective WDS queued-packet admission/drain and RX/callback lease
proof (or a verified adapter-wide quiescent lifecycle) without stopping main
Wi-Fi as a substitute. Then integrate exact-generation retirement before free.
Current isolated host tests remain valid for their narrower ownership/order
scope; full lifecycle, target build and device acceptance remain open.
No router, workflow, firmware-build, commit or push changes.


## 2026-10-29 vendor reader inventory narrowed

Inventoried 44 raw wdev_list C occurrences across 16 pinned source files,
with line numbers/roles and file hashes in wdev-list-sites-20261029.json.
This includes writers/debug/inactive guards, not 44 proven active readers.
Earlier named lookup families are conditional: WH_EZ_SETUP (CONFIG_EASY_MOD)
and MBO_SUPPORT (CONFIG_MT7603E_MBO); effective current Kbuild not yet proven.
Independent direct path ap_data.c:618 reads wdev then checks WDEV_TYPE_WDS;
wdev_rx.c:226 reads VLAN_VID immediately after index-bound check without a
null test. Thus simply clearing wdev_list before draining vendor RX/TX is
not sufficient and may expose null/dangling accesses. No speculative change
to shared driver locking or callback-proof flags was made.
Next trace WDS TX/RX admission/queues and their shutdown/drain owners; bind
post-unregister slot retirement only with those exact-path proofs.
No production, MIPS or runtime claim; no router/remote/build changes.


## 2026-10-29 WDS retirement source audit

Pinned vendor source: rt_linux.c:1500 dev_close, :1619 unregister_netdevice
then netdev_ops vfree; wdev.c:30 idx-unreg clears under irq_lock. Separate
readers wdev.c:195 use WdevListLock and return an unlocked pointer, :231
reads without that lock. Callers exist in cmm_data.c:918/1935 and wnm.c:3204.
Prepared kernel net/core/dev.c rollback_registered_many has synchronize_net
at 6431/6473; unregister also queues netdev todo completion. These are network
core barriers, not proof that all vendor reader lifetimes ended. Do not set
callbacks_quiescent=1 solely on detach/idx-unreg return.
Exact input hashes saved in wds-vendor-quiescence-audit-20261029.json.
Strict C11 registry contract test passed; it rejects wrong WDS close stage,
missing callback/vendor proof and wrong generation. Those booleans remain
unbound to proven vendor operations. Next inspect effective target reader
paths and pin/lease lifetime before binding registry slot release. This is
source evidence only; no runtime, MIPS, production or full-lifecycle claim.
No router, workflow, firmware-build, commit or push changes.


## 2026-10-29 reproducible WDS removal test and retirement witness

Added tools/iot/prepare-wds-remove-check.py, which checks exact operation
counts/order and extracts candidate WDS_Remove plus its real phase helper.
Strict C11 GCC fixture passed close/mark/inflight failures and success.
Explicit success-path witness confirms the registry still retains published
device identity after injected free: slot retirement is NOT implemented.
Source search finds registry_release only in attach-failure paths, not WDS
removal. Thus prior phase-gate pass proves failure retention/order only,
not a complete lifecycle or safe repeated interface creation.
Outputs .iot-local-check/wds-remove-reproduced-20261029 and
wds-remove-retirement-witness-20261029 (.c/.exe). Kernel callbacks are injected.
Next bind exact-generation post-unregister/vendor completion and slot release
with callback lifetime evidence; never simply clear a slot before quiescence.
Other auxiliary families and whole-driver MIPS acceptance remain open.
No router, workflow, firmware build, commit, push or production changes.


## 2026-10-29 WDS pre-unregister close gate composed and tested

WDS reconciliation now also inserts reviewed close-phase helper/declaration
and explicit close+idle gate under netdev protection before WDS detach/free.
New output wds-remove-reconciled-20261029 preserves all unrelated bytes;
receipt records four changed files and one added helper header.
Extracted actual WDS_Remove and actual phase helper into
.iot-local-check/wds-remove-phase-fixture-20261029.c. Strict optimized C11 GCC
compiled and execution passed: close failure, mark-removing failure and
inflight registration never detach/free; success closes, checks, detaches,
unregisters and frees with balanced protection. Shared callback primitives
are injected; this is not Linux RTNL/driver runtime proof. Header/dispatcher
and on-device lifetime still require target acceptance. Open/close-only
candidate receipt is superseded by this isolated WDS lifecycle successor.
Next make the removal fixture reproducible in tools, verify WDS registration
identity/registry retirement and reconcile AP-client/monitor paths. No merge
whitelist expansion, MIPS build, router, workflow, commit or push changes.


## 2026-10-29 WDS dispatcher verified; removal gate still absent

Extracted current reconciled common virtual-UP branch passes strict C11 GCC:
MBSS/AUX claim acceptance and replay rejection. No source ABI change needed
for that increment path. WDS remove audit found a separate missing safety
step: current WDS_Remove marks removing, detaches then frees; v39 explicitly
closes under netdev protection and checks wr_iot_netdev_close_phase_idle
before detach/free. Linux unregister does not propagate ndo_stop errors, so
passing WDS close tests alone cannot justify the current remove path.
Receipt .iot-local-check/wds-dispatch-remove-audit-20261029.json.
Next compose reviewed pre-unregister close + phase gate with its declaration,
registration helper, RTNL constraints and failure-retention tests. Do not
publish/reclassify the WDS-only successor as a complete safe lifecycle.
AP-client/monitor ownership also remain open. No production merge admission,
MIPS compile, firmware build, workflow dispatch, commit, push or router change.


## 2026-10-29 isolated WDS ownership reconciled

New prepare-wds-recovery-reconciliation.py pins the exact later WDS input,
reuses reviewed OPEN/CLOSE generator fragments, preserves INT remove ABI and
all other files, and adds aux-close-claim.h. Current shared headers must match;
radio-transition is pinned to the reviewed radio-off-stage successor hash.
Output wds-reconciled-20261029 has 72 files: one changed WDS source, one added
header. Receipt records every before/after hash. No whole-tree replacement.
Updated close-fixture extractor to accept exactly one reviewed VOID or INT
remove boundary (body still checked). Extracted close and auxiliary-claim
fixtures pass strict optimized C11 GCC: same-ticket retry/post-DOWN completion.
Tests use the reconciled candidate's own headers. Production/target/runtime
remain false. Next verify WDS open/dispatcher and remove coupling, then
reconcile AP-client/monitor and common request ABI; do not admit merge yet.
No firmware build, workflow dispatch, router change, commit or push.


## 2026-10-29 auxiliary ownership regression found before merge admission

Do NOT extend assembler whitelist to 64/39 yet. Current reconstructed v25b
is a separate branch of development, not a superset of v39. Inventory adds
seven headers but removes include/aux-close-claim.h (net +6 paths versus v39).
Current AP-client and WDS still call VIRTUAL_IF_DOWN(pAd); v39 WDS has
wr_iot_aux_close_reserve and checked finalization/retry ownership. Existing
caller-coverage pass is therefore not proof that older family lifecycle
fixes survived. Source comparison receipt:
.iot-local-check/current-v39-ownership-gap-20261029.json.
Next reconcile the v39 family ownership/close/remove changes with the new
main recovery/producer chain before preparing a production merge or Kbuild
candidate. Do not discard v39 safety logic or broaden a count-only gate.
Assembler whitelist intentionally unchanged; staged ABI successor tests remain
isolated source/fixture checks. No target, runtime or production acceptance.
No router change, firmware build, commit, push or workflow dispatch.


## 2026-10-29 prepared-source merge bridge identified

Existing firmware candidate Kbuild step builds vmlinux/modules only after
assemble-prepared-candidate.py merges IoT with six prepared source overlaps
(RSSI and other integrations). Direct raw overlay replacement is unsuitable.
Full-overlay preparer now emits a separate merge-input manifest with 64
candidate SHA256 records and 39 pinned original blobs. All hashes verified
against overlay4; full output bytes equal overlay3. No source merge performed.
Current assembler whitelist stops at 60/39, so new 64/39 composition needs
explicit shape/delta review and tests before enabling it. Candidate addition
includes recovery-owner/release/PCI observer headers absent from old overlay.
Next review/extend that gate and test prepared-source merge, then use the
existing isolated configured-kernel Kbuild path. Full MIPS module compilation,
production backend and runtime acceptance remain open. No workflow dispatch,
router change, commit, push or firmware build.


## 2026-10-29 successor ABI workflow wiring staged

Added a separate Verify current IoT recovery successor on host and MIPS step
before diagnostic upload. It regenerates from pinned source, prepares full
scratch overlay, runs successor host suite and compiles extracted ledger,
checked-close and post-open fixtures with the existing MIPS toolchain.
Vendor source/preparation directories live in RUNNER_TEMP outside uploaded
abi-results; only host fixtures/logs, hash receipts and MIPS objects enter
that artifact. Explicit scope text denies whole-driver Kbuild/runtime proof.
YAML parsing, unique-step placement, artifact-path and compile-loop structure
checks passed; git diff --check passed. No CI run was dispatched and no MIPS
result exists for this local change. Local Windows still lacks usable MIPS
compiler/make environment. Next full-module Kbuild integration must use the
actual configured kernel and companion mt76x3_ap Makefile; fixture objects do
not close that gate. No router, firmware build, commit or push changes.


## 2026-10-29 scratch include closure checked

Full-overlay preparer now checks every quoted wr-iot-* include in the merged
source against local/include/mcu paths before copytree. Overlay3 passes and
all output hashes equal overlay2. Missing-include negative fixture updates
its candidate receipt yet is rejected by dependency validation before output.
This prevents the earlier manifest fixture-label issue recurring silently.
Existing ABI evidence uses extracted MIPS fixtures and selected Kbuild probes;
it does not establish whole-driver compilation of this successor. Next build
integration must use actual mt76x3_ap Kbuild flags/config and keep source
scratch outside uploaded abi-results. No MIPS compile or runtime claim;
no workflow, firmware build, commit, push or router change.


## 2026-10-29 full scratch driver overlay prepared

New prepare-full-driver-overlay.py verifies candidate generation receipt,
reviewed inventory/fixture classification, pinned original blob IDs and
relative paths; refuses symlinks and existing/nested outputs. It copies full
source to a new scratch tree, applies driver files only and verifies every
output byte. Run full-driver-overlay2-20261029 passed; sibling overlay receipt
records all base/output SHA256 values and excludes seven fixture files.
A corrupt original blob is rejected before output creation.
This is a full scratch source layout, NOT a target-compiled module or accepted
production driver. Only original blobs named by the composition are pinned;
full_upstream_inventory_authenticated=false is explicit. Vendor source stays
local/outside future public diagnostic artifact roots. Next target CI wiring
must preserve this boundary and verify actual MIPS Kbuild dependencies.
No router, remote, firmware build, commit or push changes.


## 2026-10-29 generated-only preparation verified end to end

Executed default prepare-current-recovery-chain.py from pinned mt76x3 source,
without any historical candidate input. Receipt at
.iot-local-check/generated-current-full-20261029/preparation.json records
historical_comparison_used=false, dependency_remaining=false; all final
hashes match independently verified current output. Exact-output successor
host suite passes at generated-current-full-suite-20261029/result.json.
Preparation scripts parse successfully. Target/production/runtime remain false.
ABI workflow currently uploads all abi-results recursively. Future successor
vendor-source workspaces must stay outside that artifact root; upload only
bounded diagnostics/manifests, not new vendor source copies. Workflow unchanged.
Next prepare a validated full-source scratch overlay for MIPS module checks,
with provenance and publication boundary preserved. No workflow dispatched,
firmware built, router changed, commit or push performed.


## 2026-10-29 historical open dependency removed

Queue/main-open composition now extracts claimed-UP and auxiliary-dispatch
literals from the reviewed virtual-open preparer and combines MAIN_DISPATCH
from the main-owner preparer. Generated fragments exactly match historical
fragments; output from current queue matches all 64 files of previous
historical-input composition. No copied vendor dispatcher/header required.
prepare-current-recovery-chain.py now uses generated fragments by default;
optional historical input remains hash-checked for comparison. Argument/help
parse checked. Full default-entrypoint rerun is the next verification; prior
full suite was on the identical composition with historical input.
No target/module/runtime claim. No router, remote or firmware-build changes.


## 2026-10-29 unified current queue/recovery entrypoint

New prepare-current-recovery-chain.py verifies the two reviewed open-input
hashes, prepares current queue from pinned source, composes main-open and
runs all later stages in a separate workspace with bounded commands/logs.
Executed at .iot-local-check/current-unified-preparation-20261029;
all final hashes match the independently prepared current candidate.
Exact-output successor host suite passed at
.iot-local-check/current-unified-suite-20261029/result.json.
Receipt explicitly retains historical_open_dependency_remaining=true and
complete_driver_tree/target/production/runtime=false. It is not a pristine
upstream-only or buildable full-module claim. Next eliminate the two-file
historical dispatcher/header dependency using reviewed transformations,
then prepare target CI overlay. Hardware TxS retirement and production
backend remain unresolved. No router, remote, commit or firmware build.


## 2026-10-29 current queue reaches corrected v25b

All preceding current-source stages now complete. Final delta accepts only
exact old or corrected TxS/readiness hashes; corrected inputs are preserved.
changed_files reflects actual differences (zero for current queue).
Exact current candidate passed successor host suite at
.iot-local-check/current-v25b-suite-20261029/result.json.
Historical delta regression initially detected whitespace added while nesting
the multiline insertion; corrected it and verified all historical output
hashes match previous corrected v25b (historical-v25b-delta-recheck2-20261029).
Next integrate initial queue/main-open generation into the unified entrypoint.
MIPS compilation, hardware TxS retirement, production backend and device
acceptance remain open. No router/remote changes or firmware build.


## 2026-10-29 current main-close/reset composition compatibility

Main-close preparer now accepts already-staged one-shot stop/recovery headers
only when they equal the complete reviewed current helpers; legacy inputs
still work. Extracted current-source main-close fixture passes strict C11
GCC and exact-ticket/deferred-execution cases; main-stop owner test passes.
Current chain progressed through v17 before encountering already-present
reset wake. Reset preparer now preserves only an exact complete shared reset
template, otherwise performs and validates the historical transformation.
Current reset output succeeds; historical reset bytes match saved v18 and
historical main-close output remains unchanged. No weakening of timeout or
one-shot protection. Next rerun full current chain to expose/reconcile final
TxS/readiness already-applied corrections. Target/production/runtime remain
unverified; no router, remote, commit or firmware-build changes.


## 2026-10-29 current radio-off bounded-close integration fixed

prepare-composed-mt7603-radio-off.py now accepts exactly the reviewed legacy
wait loop or current already-bounded loop. It preserves current 1000-poll
stage3 timeout failure. Radio-off failure replacement is anchored to its
specific DBGPRINT/lock context, so it cannot alter the queue-timeout branch.
Current source prepares successfully; extracted checked-close passes strict
optimized C11 GCC. Historical output remains byte-identical across 64 files.
Negative fixture changes the bound to 1001 with an updated manifest: rejected
before output creation, demonstrating the guard is not merely a hash check.
Outputs: current-radio-off-fixed-20261029; current-radio-off-close-20261029.exe;
negative source radio-off-bad-bound-20261029, all under .iot-local-check.
Next reconcile already-present one-shot main-close and later reset/readiness
changes through the current queue chain. No target compile, firmware build,
production binding, runtime acceptance, commit, push or router change.


## 2026-10-29 current queue/main-open reconciliation

prepare-queue-main-open-compose.py succeeds on current regenerated
full-queue-20261029e/driver using the exact hash-reviewed dispatcher/header
from combined-open-v15-20261025. Output current-queue-main-open-20261029
has 64 files; seven differ from historical main-open (receipt
.iot-local-check/current-main-open-comparison-20261029.json).
The current chain stops BEFORE output publication in radio-off preparation:
its unbounded DeQueueRunning anchor is absent because current checked-close
already has the reviewed 1000-poll failure/stage3 bound. Exact diagnostic:
ValueError common/rtmp_init_inf.c changed anchor (0 matches).
Next adapt radio-off preparation to accept the exact already-bounded form
without weakening the bound; then reconcile already-present one-shot main
close and reset-wakeup changes. Never revert current safety fixes just to
match historical inputs. Existing successful historical replay does not
prove current-queue integration or target/runtime operation.
No firmware build, router change, commit or push.


## 2026-10-29 main-open through corrected v25b reproduced

Radio-off preparation reproduces all 64 saved v2 files. Current main-close
preparer imports two later recovery helper functions in one header; these
converge to identical final output through the RTNL/reaper stages.
Unified preparer now accepts --input-stage main-open and replays radio-off,
main-close and adapter work before its v7-and-later stages. Executed at
.iot-local-check/main-open-full-chain-20261029; all final corrected hashes
match the independent v7 chain. Exact-output host suite passes at
.iot-local-check/main-open-full-chain-suite-20261029/result.json.
Next: regenerate the queue/main-open composition itself from pinned donor
inputs instead of the preserved main-open bundle. Target compilation,
production backend, selective hardware TxS retirement and device acceptance
remain unverified. No router change, firmware build, commit or push.


## 2026-10-29 v7 unified chain and preceding work stage

Unified preparer now accepts --input-stage v7 plus --source-tree; it runs
PCI detach/joins/observation and pinned-header auxiliary composition before
the previously verified v11-to-v25b stages. Executed full chain hashes match
the independent v11 run, and the exact output passes the host suite at
.iot-local-check/v7-full-chain-suite-20261029/result.json.
Separately replayed v6-to-v7 adapter work initialization/probe-unwind join:
all 64 files match saved v7. Receipt .iot-local-check/v6-v7-replay-20261029.json.
Next unresolved source reconstruction starts at v6 deferred-close composition;
then clean donor/base replay and target build remain necessary.
Hardware TxS retirement, production backend and device acceptance remain open.
No firmware build, commit, push or router changes.


## 2026-10-29 PCI/auxiliary composition reproduced

v7-to-v9/v10 source replay matches saved candidates; intermediate v8 differs
only in a root-detach diagnostic printk and converges at v9.
prepare-remove-result-composition.py now accepts mutually exclusive
--source-tree or existing --source-git. Both paths validate exact pinned
Git blob IDs for ap_wds.h and ap_apcli.h and the donor revision.
Using full pinned local source, v11 reproduces all 67 saved files exactly.
A corrupt header is rejected before output creation. Receipts:
.iot-local-check/v7-v10-replay-20261029.json and v7-v11-comparison-20261029.json.
Next: fold this verified v7-to-v11 segment into the unified chain, then
reproduce earlier main-open/close/recovery inputs. Target/production/runtime
and hardware stale-TxS gates remain unproven. No router or remote changes.


## 2026-10-29 checked-stop/claimed-open chain reproduced

Replayed v11-to-v12 checked MBSS stop and v11/v12-to-v14 claimed open.
All 67 files match each saved candidate. Receipt:
.iot-local-check/v11-v14-replay-20261029.json.
Unified preparer accepts --input-stage v11 with validated canonical sibling
manifest and reproduces the corrected v25b output exactly as the v14 chain.
The exact output passes the successor host suite:
.iot-local-check/v11-full-chain-suite-20261029/result.json.
No target compilation, production binding or hardware acceptance is claimed.
Next: reconstruct v11 and its earlier ownership/recovery composition stages.
Existing hardware TxS identity/drain and production-backend gaps remain.
No router change, firmware build, commit or push.


## 2026-10-29 v14-to-v19 replay and full later chain

Five steering/wakeup transitions reproduced saved v15b, v16b, v17, v18,
and v19 exactly (67 files each). Receipt:
.iot-local-check/v14-v19-replay-20261029.json.
prepare-later-recovery-chain.py now accepts --input-stage v14, validates
claimed-open provenance and generates its own v19 manifest for rollback.
Full v14-to-corrected-v25b run passed; final hashes equal the independent
v19 chain. Successor host suite passed on this exact regenerated output:
.iot-local-check/v14-full-chain-suite-20261029/result.json.
Next unresolved preparation segment is upstream/base-to-v14. This remains
source/host evidence only; target compile, hardware TxS retirement,
production activation/backend and on-device acceptance are not established.
No router change, commit, push or firmware build.


## 2026-10-29 later recovery chain automated

New tools/iot/prepare-later-recovery-chain.py validates the complete v19
input inventory/stage and replays seven preparers plus the PCI ordering check
in a new workspace. It records preparer hashes, bounded subprocess logs,
input/output file hashes and explicit target/production/runtime false.
Executed at .iot-local-check/later-chain-script-20261029; output matches the
independently generated corrected candidate. Its successor host suite passes
at .iot-local-check/later-chain-script-suite-20261029/result.json.
The current v22 header delta converges to exact saved v25b after reaper;
all 71 final pre-correction files match. No manual historical delta is needed
for v19 onward. Upstream-to-v19 preparation is the next unresolved CI chain
segment; hardware stale TxS identity and production backend remain open.
No router change, firmware build, commit or push performed.


## 2026-10-29 VERIFY/rollback replay and portable manifest

v19-to-v20 VERIFY and v20-to-v21 checked rollback reproduce saved file hashes.
Rollback now accepts --prior-manifest, retaining its historical default and
all existing stage/hash checks. Explicit-path output matches saved v21;
wrong-stage manifest is rejected before output creation.
Current v22 preparer differs from saved v22 only in main-open-recovery-owner.h:
it imports the later canceled-before-run recovery helper needed by v23b.
Do not claim exact historical v22 reproduction. Next verify the regenerated
v22 through reaper/drain/producer against saved v25b, then trace earlier stages.
Receipt: .iot-local-check/v19-v22-chain-replay-20261029.json.
Target compilation, production activation and device acceptance remain open.


## 2026-10-29 three-stage recovery/producer replay

From the preserved v22 RTNL candidate, replayed main-recovery reaper,
PCI recovery drain and beacon producer preparers into new local directories.
Full SHA256 file comparisons match saved v23b (67 files), v24c (69 files)
and v25b (71 files); the receipt records actual counts and equality at
`.iot-local-check/v22-v25b-chain-replay-20261029.json`.
The PCI checker also passed all 69 hashes and retire/drain/stop/join ordering.
Current preparers reproduce v23b/v24c despite their older generic stage names.
This closes manual-delta uncertainty for these three transitions only.
Next: reproduce v22 and earlier composition from verified inputs. No target
compile, production activation, hardware TxS retirement or runtime acceptance
is established; no router or remote state changed.


## 2026-10-29 producer-stage replay verified

Replayed `prepare-beacon-producer-candidate.py` from preserved
`.iot-local-check/mt7603-pci-recovery-drain-v24c-20261028` into new
`.iot-local-check/v25b-producer-replay-20261029`. SHA256 comparison against
saved `tools/iot/candidates/mt7603-v25b-beacon/source` confirms 71/71 files,
no missing, extra or differing bytes. Comparison receipt:
`.iot-local-check/v25b-producer-replay-comparison-20261029.json`.
This verifies only the last producer stage from the preserved v24c input;
it does not establish clean upstream-to-v24c replay or target compilation.
Next: reproduce preceding recovery-drain/reaper stages with their manifests,
then construct the full CI chain without publishing vendor source copies.
Router, firmware image, commits and GitHub were not changed.


2026-10-29 target environment rechecked: no local MIPS GCC or Docker found;
wsl --list --quiet returns installation/help rather than a runnable distro.
Existing ABI workflow builds the base queue candidate, not the local 71-file
v25b successor. Therefore dispatching unchanged remote HEAD would not verify
the successor. Need reproducible later-chain CI preparation before target
claim; preserve vendor source publication restriction and dirty worktree.

2026-10-29 successor suite now includes extracted bounded checked-close;
all checks pass in v25b-successor-fullchecks-20261029/result.json. Evidence
consolidated in WR1200JS-IOT-V25B-SUCCESSOR-2026-10-29.md. Host-only; target,
production backend and hardware stale-report gate remain unresolved.

2026-10-29 reproducible successor host suite added: check-v25b-successor.py
verifies full preparation receipt, caller coverage, extracted ledger and
WR_IOT_V40 post-open with strict GCC and 30-second process bounds. Executed
successfully; logs/result at .iot-local-check/v25b-successor-checks-20261029.
Result records candidate hashes and explicit target/production/runtime false.

2026-10-29 successor source audits pass: five virtual caller families/five
checked registration paths, plus all 71 receipt hashes with exactly txs.c
and virtual-open-claim.h changed. Preserve later source stages; target and
runtime ownership proof remain open. Output v25b-generation-readiness-20261029.

2026-10-29 close delta reconciliation: v25b already bounds checked close via
waited++ >=1000U and stage3 retention. No close-source replacement needed.
Extractor now recognizes both reviewed counter names; v25b generation/readiness
successor checked-close fixture passes strict GCC/exit0 on own headers.
Legacy vendor close remains unbounded; checked-path success does not prove
all callers are bound. Preserve this scope in target review.

2026-10-29 v25b delta preparer now also carries current READY demotion;
exact old header hash and removal-of-only-new-block comparison constrain the
replacement. Output .iot-local-check/v25b-generation-readiness-20261029
passes intended WR_IOT_V40 post-open test on its own include tree. Two changed
files recorded; all later stages preserved. Target and TxS retirement pending.

2026-10-29 later-chain generation fix staged reproducibly with
prepare-v25b-generation-bound.py: exact TxS input hash, all-file before/after
receipt, only txs.c changed, line endings preserved. Output
.iot-local-check/v25b-generation-20261029 passes extracted strict GCC ledger
with exhaustion expectation. Other v25b files preserved; target not compiled
and hardware stale-report identity still unresolved.

2026-10-29 base/later reconciliation inventoried by SHA256:
fresh base has 63 files, saved v25b 71; 26 shared files differ, 8 later-only,
no base-only. Report .iot-local-check/base-v25b-reconciliation-20261029.json.
Do not replace later source with base output: that would drop recovery,
steering and producer stages. Reconcile named stage chain and apply current
generation/close/readiness deltas with provenance-preserving manifests.

2026-10-29 admission now explicitly covers successful BSS readback but vendor
count mismatch: retain owned reference, demote to UNVERIFIED/main_ready false.
Final-source strict GCC fixture passes. This guards count reconciliation;
not a live BSS or target result.

2026-10-29 intended post-open variant verified: -DWR_IOT_V40 with saved v25b
include tree passes strict GCC. Temporary include overlay containing current
virtual-open-claim.h also passes readback/count/reset and steering-publication
fixtures. Header delta is exactly the READY demotion block. This establishes
host compatibility of that delta, not full later-chain regeneration/target.

2026-10-29 post-open test scope resolved: check-mbss-post-open.c expects
steering-ready + intent-race publication stages from the separately verified
v14 successor chain (prepare-mbss-steering-ready-candidate.py et al.). The
fresh radio-queue bundle lacks these later stages. Do not remove unused
publication helpers to make that different-source test pass. Need compose
reviewed later stages into regenerated chain with preserved input manifests;
current base-admission/close passes do not establish steering publication.

2026-10-29 shared virtual-open-claim host fixture passed strict GCC after
READY demotion fix. Separate check-mbss-post-open.c standalone build fails
unused publish_ready/down helpers; it has conditional WR_IOT_V40/source
variants and is not selected by current ABI workflow search. Inspect intended
source variant before editing fixture or suppressing diagnostics. No target
claim and no successful standalone post-open test this turn.

2026-10-29 close extractor now rejects absent dequeue bound before management
join, preventing the known unbounded regression from hanging CI. Current
generated source accepted; temporary source with bound removed rejected with
explicit diagnostic. Behavioral close tests remain separate evidence.

2026-10-29 HNAT variant of final MT_MAC/PCI open-close fixture passes strict
GCC/exit0. Consolidated scope in WR1200JS-IOT-MBSS-FIXTURE-ALIGNMENT-2026-10-29.md.
Still injected IO; no offload traffic/device or MIPS acceptance.

2026-10-29 MT open/close fixture now passes strict GCC on final generated
source. Main reference matches baseline count, begin-close captures ownership,
and success checks existing retirement (no double finish). Pending/fault
DMA/TxS cases preserve references; main stays owned on successful IoT close.
Hardware operations injected; target/late-report retirement still pending.

2026-10-29 MT open/close fixture now compiles with shared observer/count/wait
model; removed duplicate virtual-UP increment, binds MBSS family and uses
actual begin-close. It still fails begin-close count admission because baseline
VirtualIfCnt=1 lacks a corresponding owned main registry slot (only IoT slot
modeled). Add realistic main ownership/capacity before rerun; do not weaken
registry count matching. Diagnostic generated line532, run interrupted.

2026-10-29 invalidated READY fix propagated: full candidate regenerated at
.iot-local-check/full-queue-20261029e. Updated admission fixture compiled
against its final include directory and passed strict optimized GCC. This
confirms generator propagation, not MIPS/device behavior. Continue downstream
MT_MAC open-close fixture alignment and hardware TxS retirement gates.

2026-10-29 BSS readback/reset fix: observed finish could leave phase READY
with reset_pending/main_ready false after reset during raw UP. Shared helper
now demotes invalidated READY to UNVERIFIED, retaining owned reference for
checked close. Updated admission fixture with real family/count and failed
BSS observation passes strict GCC using current tools/iot headers. Regenerated
driver header is still old; full regeneration and target tests required.

2026-10-29 admission fixture now models BSS observer, virtual count and MBSS
family; first compile/run passed before adding family/readiness assertions.
Stronger run exposed stale mode9 reset-phase expectation at generated line225;
interrupted after assertion. Inspect wr_iot_bss_open_finish_observed and
radio_finish reset priority before finalizing assertions. Not a passed updated
fixture yet; downstream open-close fixture still needs count-model alignment.

2026-10-29 admission-model contract review: current wrapper performs BSS
readback after raw open outside transition lock, then checks observed BSS
and vendor reference count together under that lock. Fixture must model
both independently, including failed readback after successful count acquire;
do not merely return constant success or assert open return proves readiness.
No updated admission-model execution has passed yet.

2026-10-29 MT_MAC open/close fixture does not compile current generated
source: missing injected wr_iot_mt7603_bss_config_observed, VIRTUAL_IF_NUM
before open wrapper, ticket wait field/wake primitive. Base admission fixture
also predates current BSS observation/count contract. Update its behavioral
model and assertions rather than suppress warnings or weakening production
checks. Generated diagnostic: .iot-local-check/mbss-mt-check-20261029.c.

2026-10-29 last-close assertion resolved by current fixture provenance:
MBSS family and wr_iot_mbss_begin_close generation capture. Updated wait/wake
model checks exactly one successful wake, no failure wake. Final-source
fixture passes strict GCC/exit0. Workers/hardware injected; target pending.

2026-10-29 last-close fixture compile drift fixed: added ticket wait field
and injected wake counter. Execution then failed first close assertion at
generated line 698. Fixture begins via wr_iot_radio_begin_stop rather than
current wr_iot_mbss_begin_close provenance capture; inspect before changing
production code. Run interrupted after explicit assertion; no pass claim.

2026-10-29 live GitHub check: latest Band Steering driver ABI #586 run
40562762027 succeeded on fcf45d747ea17e6b719e421db1cc10f3053bcf33.
Current dirty candidate fixes are not in that commit, so it does not verify
them. Recent overall Actions entries are successful monitor runs, not builds.
No workflow dispatched. Do not confuse ABI #586 with earlier firmware #586.

2026-10-29 bounded-close final close-chain fixture passed strict GCC/exit0.
See WR1200JS-IOT-DEQUEUE-CLOSE-BOUND-2026-10-29.md for exact host scope,
1000-poll versus wall-clock distinction, retained uncertainty and remaining
target/hardware gates. No production/router operation.

2026-10-29 close hang fixed in prepare-checked-close.py: bounded 1000-poll
dequeue wait enters retained stage 3 instead of continuing/freeing. Actual
full-queue-20261029d final checked-close fixture now passes strict GCC (exit0).
No target or device claim; broader close chain still pending.

2026-10-29 checked-close fixture on full-queue-20261029c did not complete:
10-second subprocess timeout; owned test processes stopped. Generated
.iot-local-check/current-checked-close-20261029.c contains vendor polling
while DeQueueRunning at line 129. Inspect injected flags/delay callback before
rerunning; no passing close result and no close-chain run yet. Diagnostic
variant also did not return; no target or device claim.

2026-10-29 generated close wrapper has no RX wait under BcnRingLock and
releases transition lock before vendor/snapshot work. Yet zero DMA/TxS
snapshots still precede reference retirement without a hardware drain proof;
keep production gate. See current close review in TxS retirement report.

2026-10-29 PCI lock order: RX ring lock spans parse_rx_packet_type and
therefore beacon TxS callback. Future drain must not hold BcnRingLock while
waiting for RX/tasklet completion; release after stop publication and
revalidate after bounded synchronization. See TxS retirement report.

2026-10-29 pinned MT dispatch resolved: MT7603 HIF_MT chooses
AndesMTRxEventHandler for RX_EVENT; RX_TXS calls ParseTxSPacket separately.
MT handler does not re-enter generic parser. Generic direct caller is RLT
path. No extra MCU beacon-TxS owner demonstrated for ordinary MT routing;
continue PCI RX/hardware/callback retirement proof. Source-only conclusion.

2026-10-29 Andes reachability refined: full C/header search found rx_doneq
consumer but no queue producer. Direct AndesRxProcessCmdMsg caller is in
andes_rlt.c; MT uses separate AndesMTRxEventHandler. Generic parser reference
is not proof of active MT7603 TxS route. Inspect effective dispatch guards
before adding drain machinery; runtime exclusion remains unproved.

2026-10-29 parser coverage: AndesRxProcessCmdMsg also calls the common RX
type parser under MT_MAC. Check whether MCU RX can carry beacon TxS; include
its queue in a drain or prove exclusion. PCI rx tasklet alone is insufficient
as an assumed exhaustive owner map. See TxS retirement report.

2026-10-29 DMA caller context: pinned source calls beacon DMA completion
only from bcn_dma_done_tasklet (rt_rbus_pci_drv.c:575); hard IRQ schedules
the task (1595). Do not call this a direct hard-IRQ BcnRingLock user based
on the function name. Other callers/WORKQUEUE_BH remain to be verified.

2026-10-29 saved target evidence found: artifacts-634-v42/merged-capacity.json
has all nine lock units preprocessed, site activity complete, MULTI_CORE=false.
Both lock forms use BH in that build. Do not normalize names based solely on
the 12/9 inventory; current candidate flags and hard-IRQ caller safety still
need verification. This is saved build evidence, not live router behavior.

2026-10-29 lock semantic audit: SEM/IRQ both use BH helper when MULTI_CORE
is absent; IRQ changes to irqsave when defined. Found config.mk definition
is BB_SOC/TC3262-conditional, not WR1200JS effective proof. Need exact target
preprocessor flags and caller-context audit before changing lock forms.

2026-10-29 reviewed expanded manifest stages and refreshed strict inventory
shape to 515/55/37/9/21/12/9. Full-source audit passed with original hash and
candidate hash checks retained. Report full-source-lock-reviewed-20261029.json
under .iot-local-check. Mixed-lock semantic/target proof remains pending.

2026-10-29 download session 85180 completed (515 files). Raw full-source
lock inventory verified 37 original blobs/candidate hashes: 21 sites, 9 units,
12 SEM/9 IRQ. Strict shape gate rejects overlay/base counts 55/37 versus
46/32; review added files before any gate update. Raw report is
.iot-local-check/full-source-lock-inventory-20261029.json; full source in
.iot-local-check/mt76x3-full-pinned-20261029. No lock-correctness/runtime claim.

2026-10-29 full source acquisition in progress: codeload pinned revision
c25283e archive returned HTTP 200. Streaming extraction selects only regular
mt76x3 files with checked relative paths into
.iot-local-check/mt76x3-full-pinned-20261029. Exec session 85180 confirmed
running at last poll; completion receipt not yet present/verified. Poll same
handle before retrying or using tree. No full-source acceptance yet.

2026-10-29 fixed missing original hash for overlaid include/rt_os_net.h.
Regenerated candidate full-queue-20261029c successfully. Full-lock audit now
stops at sparse input coverage (38 versus required 515 files); obtain complete
pinned driver tree, preserve auditor gate. This is not a passed lock audit.

2026-10-29 full queue candidate now prepared successfully at
.iot-local-check/full-queue-20261029b after collecting nine nested inputs.
Final-source status and extended ledger/parser strict GCC fixtures both pass
with exhaustion refusal. Manifest exists; it remains a partial source bundle,
not a target module or production implementation. Hardware stale-report gate
is still unresolved; no router changes.

2026-10-29 full queue preparation started: fetched 29 top-level source inputs
from pinned GitHub revision into .iot-local-check/txs-pinned-20261029.
Preparation reached nested radio-errors stage then refused missing ap/ap_mbss.c;
output .iot-local-check/full-queue-20261029 is incomplete, without acceptance.
Next collect nested preparer inputs and use a NEW output directory; preserve
the incomplete diagnostic tree and exact source hash guards.

2026-10-29 ABI now selects extended TxS ledger/parser after full queue
preparation, with sanitizers, explicit generation-exhaustion expectation and
saved output. YAML/order check passed; not run or published. A passing
negative witness must not be interpreted as safe BSS retirement.

2026-10-29 extended parser result resolved: add existing handler-snapshot
stage after callback-ledger/claimed-slot. Fresh stage is
.iot-local-check/txs-handler-20261029; extended ledger/parser now passes
strict GCC with --expect-generation-exhaustion. Earlier missing-stage run's
remaining owned process was stopped. Stale report identity gate remains open.

2026-10-29 actual regenerated TxS + callback ledger + claimed-slot stages
are in .iot-local-check/txs-claimed-20261029. CI-used status fixture passed
strict optimized GCC. Extended parser fixture did not return and was
interrupted (session 95035); do not call it passing. Complete queue composition
and remaining parser transformations before repeating broader checks.

2026-10-29 base input resolved: GitHub connector fetched four pinned files;
exact blob hashes passed. TxS stage fully regenerated under
.iot-local-check/txs-regenerated-20261029. Queue composition and target build
still pending; keep downloaded vendor source local and outside publication.

2026-10-29 regeneration input check: available local candidate trees are
already transformed; sources/archives has no mt76x3 base archive. The strict
generator requires four exact pinned blobs, so do not feed v25b back as base
or weaken hashes. New manifest records generation-exhaustion rejection.
Next obtain pinned base through the existing source pipeline, then regenerate
the complete queue candidate and run the CI-used status fixture.

2026-10-29 generation regression is also in the CI-used status extractor:
UINT32_MAX must refuse with untouched outputs/free slot and unlocked ledger.
Strict GCC temporary-composition execution passed. Full regeneration/target
CI remains pending; no workflow dispatch or router operation performed.

2026-10-29 ledger extractor accepts explicit --expect-generation-exhaustion
for regenerated candidates. It requires rejection at UINT32_MAX with unchanged
outputs/slot and unlocked ledger. Strict GCC run passed on a temporary source
composition using the generator's exact guard; full regeneration still needed.

2026-10-29 generation fix: prepare-txs-status-candidate.py now rejects
UINT32 exhaustion under lock before allocation. Extracted new guard composed
into the host fixture passed strict GCC; full candidate regeneration and target
compile remain pending. Existing v25b source is unchanged and still wraps.

2026-10-29 extracted TxS fixture now also demonstrates UINT32 generation
wrap repeating cancellation identity 1. Strict GCC host run passed. Resolve
identity exhaustion/drain before production cancellation; no driver edit.

2026-10-29 current TxS witness revalidated: extracted v25b ledger/parser
compiled with strict optimized GCC C11 and executed; injected old PID report
still consumes a newer BSS slot. Host model only, no hardware occurrence
claim. Keep selective-close production gate until identity/drain proof.

2026-10-29 TxS option: permanent PID quarantine exhausts the finite UINT8
allocator; uncertainty-only quarantine leaves normal-completion stale-report
reuse unresolved. Do not use it to claim selective retirement. Identity or
hardware/software drain proof is still required; driver unchanged.

2026-10-29 negative HTTP source checks passed: missing session-reset hook is
rejected, and repeated preparation preserves the existing source. No live
HTTP session was executed; Linux handler/target verification remains open.

2026-10-29 HTTP CI: standalone form fixture is now selected by the existing
Linux ABI HTTP request step with sanitizers. YAML/selection and targeted diff
checks passed; workflow not published or run. Handler session reset/replay
case awaits that Linux execution. Preserve the production activation gates.

2026-10-29 IoT CGI preparation: the candidate now refuses differing or linked
`wr-iot`/shared-validation destinations before writing source. Temporary
fixture with a conflicting header refused and preserved the header, HTTPD
and WebUI bytes; Python and targeted diff checks passed. No production
install, backend, image or router result. See CGI candidate evidence.
The candidate disable form now accepts only its enable=0 field plus token;
SSID/password extras are rejected. Strict C11 form test and isolated positive
HTTP preparation passed. Combined request fixture could not compile with
Windows GCC because POSIX `arpa/inet.h` is unavailable; Linux CI is pending.
HTTPD source candidate now calls `wr_iot_http_session_reset()` from stock
`reset_login_data()` to invalidate old IoT CSRF/body state at logout, timeout
or login reset. Isolated source preparation/check passed; Linux handler
execution, target link and real session behavior remain unverified.

2026-10-29 Classic IoT navigation: `state.js` has independent main and guest
2.4/5 GHz shortcut pairs. The isolated candidate now adds IoT beside both;
the original handlers/classes remain. Node 14-route check, JS syntax and
targeted diff check pass. It is not installed in production and does not
establish IoT activation, save, isolation or router behavior. See Classic
navigation evidence. Next retain the TxS retirement and backend safety gates.
The dynamic asset now defers mounting until after Classic's `body onload`
constructs the banner and tab menu; Node covers loading and complete states.
This still needs rendered and image verification before any production claim.
Preparation now fails closed if the original four main/guest shortcut IDs or
the twelve Wi-Fi `initial()` load hooks drift. Extracted ROMFS source shows
4/4 IDs and 12/12 hooks; Python/Node/targeted diff checks pass. No build,
production installation or router change.

2026-10-29 TxS SN check: isolated v25b records only PID/software generation
with the reservation; its beacon descriptor writer does not set SN/SN-valid,
and the TxS parser does not compare report SN. The MLME Sequence assignment
is a different path. Do not claim a source-proven SN identity; hardware
experiment or real drain proof remains necessary. See TxS retirement report.

2026-10-29 TxS source decision: do not disable beacon host TxS as a shortcut.
In v25b, DMA completion sets `BCN_TX_DMA_DONE`, whereas `BcnTxSHandler`
sets `BCN_TX_IDLE`; normal update/deinit require IDLE. The exact report
identity or selective drain gate remains. See the TxS retirement report.

2026-10-29 combined host fixture: injected SIGTERM sets the RC shutdown
marker after RADIO_PREPARE; the activation callback observes it, prevents
`BSS_UP`, recovers the snapshot and retains the pending signal. Strict C11
GCC run passed. This models the future binding but does not install it or
prove bounded target operations. Local WSL has no runnable distribution;
Linux signal branches await CI.

2026-10-29 IoT activation candidate: a required backend
`cancel_requested` callback now gates entry after LOCK, every START operation and the final
ACTIVE transition. Host checks pass for mid-start/after-OBSERVE cancel and
retained quarantine on failed recovery. Next bind it to the RC shutdown
marker under a real bounded backend and shared driver transition owner;
the host check is not production or on-device evidence.

2026-10-29 dispatch fixture now exercises SIGTERM and conditionally SIGQUIT
and SIGPWR, checking deferred normal shutdown against immediate power
handling. Strict Windows C11 run passes, but that host only defines the
SIGTERM branch; Linux CI still must exercise the other branches. No backend,
image or router acceptance follows.

2026-10-29 power-signal review: the isolated RC marker now defers only
SIGTERM/SIGQUIT (`sys_exit`/`sys_stop` in pinned source). SIGPWR remains
immediate, as do process faults. Strict C11 host admission and dispatch
fixtures pass. Production still needs fail-closed recovery if SIGPWR/fault
interrupts activation, plus a bounded backend and target/device checks.

2026-10-29 follow-up: isolated RC shutdown `end()` now clears `active`
before reading the deferred slot, preventing a late signal from being erased
unseen. Local source preparation passed using pinned RC plus an HTTP fixture
with a stub Makefile; strict C11 admission and injected dispatch tests pass.
Do not claim real Makefile selection, Linux CI, MIPS build or device success.
Next: validate generated source and signal behavior under Linux, then design
bounded backend cancellation and common driver transition ownership.

2026-10-29 RC signal candidate: `rc-shutdown-admission.h` and updated
`control-server.c`/`prepare-control.py` defer normal shutdown signals during
an IoT RC dispatch and re-raise after result publication. Windows host marker
and extracted dispatch tests pass; edited Linux CI has not run. Do not ship
until the backend is bounded/cancelable, generated RC MIPS builds and normal
shutdown plus crash recovery are tested. Process faults are never deferred;
driver transition/TxS gates remain open. See RC signal evidence.

2026-10-29 signal-gate detail: pinned RC catches SIGTERM/SIGQUIT/SIGPWR
and process faults in its direct shutdown handler. Do not blanket-mask
fatal signals in `wr_iot_rc_dispatch`; a stuck backend would block reboot
and process faults must remain visible. Contract now calls for bounded
normal-shutdown admission/cancellation and a shared driver owner. See the
top of `docs/IOT-WIFI-IMPLEMENTATION-CONTRACT.md` and the RC signal evidence.

2026-10-29 RC ownership correction: PID 1's SIGUSR1 notification loop is
sequential, but its fatal-signal handler invokes `shutdown_router()` outside
that loop. The host-only activation check does not fence shutdown. Before
binding `wr_iot_activation_execute`, design and test common teardown
admission/cancellation with the driver owner; do not equate one RC worker
with complete radio serialization. See
`docs/evidence/WR1200JS-IOT-RC-SIGNAL-OWNERSHIP-2026-10-29.md`.

2026-10-28 activation candidate: `activation.h` now rechecks inactive
admission after backend LOCK and rejects stale stop generation; the host
fixture covers those logical interleavings and existing rollback paths with
strict C11/GCC. State access still requires one serialized RC control worker;
this is not a thread-safe public API or a production backend. No image/device
claim follows.

2026-10-28 TxS identity refinement: v25b MT-MAC beacon writer uses WCID 0
for all BSSs, and the descriptor writer copies it to `wlan_idx`. The report's
WLAN index cannot distinguish old from new BSS after PID reuse. Do not bind
selective close using that field alone. Exact source locations and limits are
in `docs/evidence/WR1200JS-IOT-TXS-RETIREMENT-OPTIONS-2026-10-24.md`.

2026-10-28 v25b source review: a 71-file duplicate was copied into the
untracked `tools/iot/candidates/mt7603-v25b-beacon/` and verified against
the local parent/delta manifests. It is not production or target compiled.
Ralink source notice says unpublished/all rights reserved; review
redistribution rights before staging or publishing it. Automatic command
approval rejected removal of this newly created copy (`blocked by policy`),
so it remains locally; do not bulk-stage it. The original local candidate
and all other shared work were preserved.

Owner decision 2026-10-28: keep BusyBox 1.24.2 for WR1200JS; do not upgrade
for applet novelty. `hexdump -C -n 4096` was observed on the router. Continue
the exact-image/per-service BusyBox audit; the installed image identity is
still unconfirmed. See `docs/PROJECT-DELIVERY-SCOPE.md`.

The existing Band Steering ABI workflow now includes strict host checks for
the IoT registry and MBSS removal selector. Local optimized GCC runs and
YAML parsing pass. This workflow edit has not run on GitHub; the tests are
host-only and do not provide a v25b MIPS driver compile or TxS drain proof.
`tools/iot/check-beacon-producer-composition.py` now validates the complete
v24c→v25b inventory and hashes: 69 parent files, seven changed/added files,
71 output files. The local check passes. Both source trees are still scratch
inputs; this does not make the composition reproducible from GitHub alone.
The v22→v24c preparers and `pci-recovery-drain.inc` are currently untracked;
only the v25b beacon preparer is tracked. Before CI target compilation,
package the exact 71-file v25b source or track and review its complete
preparation chain. Do not bulk-stage the dirty worktree to achieve this.

## Sol IoT exact netdev detach registry contract — 2026-10-28

Latest v25b extracted host fixtures compile with `-std=c11 -Wall -Wextra
-Werror` and run. DMA snapshot passes; TxS fixture has a negative witness:
an old report on a reused PID invokes the new BSS callback and clears its
slot. This is a modeled possible ordering, not proof of an actual duplicate
on WR1200JS. Do not mark selective BSS TxS drain safe or bind production
close based on `TXS_CLAIMED`, callback counts, or a timeout alone. Next
obtain exact report identity on hardware or prove a hardware plus RX drain
barrier while preserving the other BSSs. See the detach evidence and
`docs/evidence/WR1200JS-IOT-TXS-RETIREMENT-OPTIONS-2026-10-24.md`.
The host-only `mbss-remove-resume.h` now takes a separate `reports_drained`
proof and refuses vendor teardown/final release without it, even if callback
quiescence is true. The C11 fixture passes. Do not source this flag from
`WrBeaconTxSOutstanding == 0`: that is a software snapshot. v25b supplies
no proven value yet; no production path is bound.
The registry's other finalization entry points now enforce the same MBSS
proof, including retries after unregister. Tests cover false-proof retention
and WDS independence. Do not bypass these by calling the raw release helper
from a production child remove loop; that helper remains a lower-level
primitive, not the MBSS removal contract.
Local Windows tool check found no MIPS cross compiler, Docker or Podman;
`wsl.exe --status` exits 50. v25b remains host-tested only. Do not report
target compilation until a pinned CI driver build actually compiles its
exact source hashes and publishes diagnostics.

`tools/iot/interface-registry.h` now offers a one-shot exact
`wr_iot_registry_release_after_detach` contract. The strict C11 fixture
rejects missing callback/unregister/vendor proof, an owned reference, wrong
generation and duplicate release. See
`docs/evidence/WR1200JS-IOT-NETDEV-DETACH-REGISTRY-CONTRACT-2026-10-28.md`.
It is not bound to child removal. The pinned Padavan base `c25283e` was
inspected: `rtnl_unlock` calls `netdev_run_todo`, which completes unregister
and drains netdev refs; the local IMQ patch does not alter those functions.
Vendor checked-close and callback proof, final assembled kernel comparison
and post-unregister failure ownership remain required before binding.
The contract now rejects stale `IDLE` records with acquired opens unless
family-specific checked close completed: main/MBSS stage 4 or reviewed WDS
candidate stage 2. WDS stage 4 is unfinished; AP-client/monitor have no
accepted terminal state yet. Strict host GCC regression passes. v24c
AP-client and WDS `ndo_stop` still discard the virtual-down result.
The v39 WDS checked-close wrapper was compared with v24c: it retains a
ticket/pin on failed DOWN, but its recovery functions have no bound worker.
Do not copy it alone. Implement the retained owner and post-unregister
finalizer before binding child release/free.
The registry contract now records post-unregister stage 1 even while checked
close is pending, then permits one-shot release only after close/callback/
vendor proofs. Failed proofs retain identity and stage for continuation;
no production continuation owner is bound. Host fixture covers this split.
Source audit locates the MBSS stage-1 binding after protect-off returns in
`ap/ap_mbss.c`; the current loop has no resume branch after beacon teardown
and unregister. Bind only with a retained netdev owner and stage-1 resume
path, before vendor index unregister and free.
Pinned kernel `netdev_run_todo` waits for all netdev refs during protect-off.
Do not retain `dev_hold` across that call: use driver-owned allocation
lifetime and release temporary kernel refs before protect-off.
Pinned `free_netdev`/`netdev_release` source permits delayed driver free
after unregister reaches `NETREG_UNREGISTERED`; the candidate has no
exclusive owner for that delayed free yet. Do not use `dev_hold` as one.
Host MBSS resume selector now requires callback-quiescence proof before
vendor/release; the driver must supply that proof from real worker drains.
`wr_iot_wait_tx_idle` covers OS TX entries only; registration wait covers
registration only. Neither is the required MBSS vendor callback proof.
PCI-wide main recovery joins are also insufficient alone. Audit/join the
actual beacon/DMA producers before binding the finalizer.
The beacon/TIM producer gate was restaged from v24c into isolated v25b
(`.iot-local-check/mt7603-pci-recovery-drain-v25b-beacon-20261028`). The
preparer now accepts exact LF/CRLF anchors. Host gate fixture passes;
manifest says no target compile or production install. A partial failed v25
scratch directory remains because deletion was policy rejected; never use
it as source. v25b still needs target compile and complete vendor
callback/DMA ownership before MBSS release binding.
V25b source review found the two expected producer wrappers and MBSS
close/remove gate calls; kernel-adapter host fixture passed. Do not treat
these checks as late DMA/TxS drain or a target build.
Host-only `mbss-remove-resume.h` now models that stage choice and passes a
strict C11 fixture. It is not wired into v24c and supplies no netdev pin or
callback quiescence proof. Next integrate it with a retained removal owner,
then target-compile and inspect the assembled driver.
Its destructive steps now refuse wrong family/generation and pending close;
the strict host fixture verifies those cases. No v24c binding yet.
The combined detach helper also records stage 1 before checking later
proofs; its retry path continues the same generation without unregistering
again. Strict host fixture passed after this correction.

## Sol IoT v24c child netdev release gap — 2026-10-28

The four normal child remove loops call detach/free without normal-path
registry completion. The attach bridge's release covers failed attach only.
See `docs/evidence/WR1200JS-IOT-V24C-CHILD-NETDEV-RELEASE-GAP-2026-10-28.md`.
Implement exact per-netdev checked close, unregister/callback quiescence and
registry release before free; account for a post-unregister failure without
repeating unregister. Only then bind family and PCI release receipts.

## Sol IoT v24c release binding audit — 2026-10-28

Source inspection found `wr_iot_children` initialized but never advanced in
vendor C. The PCI retirement receipts after drain are also not called before
`RtmpRaDevCtrlExit`. See
`docs/evidence/WR1200JS-IOT-V24C-RELEASE-BINDING-AUDIT-2026-10-28.md`.
Bind actual checked child-family completion and callback/registry evidence
before the PCI release gate. The stalled-owner finalizer is a separate
one-shot remove lifetime blocker. v24c remains isolated and nonproduction.

## Sol IoT v24c queued callback drain gate — 2026-10-28

v24c is the current isolated PCI drain composition. It corrects v24b's
premature `COMPLETE` when deferred owners reach zero but a delayed reaper is
still queued/running. The bounded drain now joins that instance or stalls.
69/69 hashes, focused source checks and strict C11 host fixtures pass. See
`docs/evidence/WR1200JS-IOT-V24C-PCI-DRAIN-QUEUED-CALLBACK-2026-10-28.md`.
Do not install: the one-shot remove still lacks a stalled-owner finalizer,
the release gate is unbound, and there is no target/image/device proof.

## Sol IoT v24b PCI recovery drain — 2026-10-28

Isolated `.iot-local-check/mt7603-pci-recovery-drain-v24b-20261028` stages
bounded, owner-checked reaper draining before the PCI stop request. Its
69-file manifest, focused source checks and strict C11 drain scenarios pass.
The source-order checker confirms retire → drain → stop → join. No local
MIPS GCC was discovered on PATH; WSL distribution availability was not shown.
See `docs/evidence/WR1200JS-IOT-V24B-PCI-RECOVERY-DRAIN-2026-10-28.md`.
The stalled-owner path still returns from one-shot PCI remove without a
finalizer; release gate remains unbound. No target/image/router proof. Keep
nonproduction and resolve the stalled-owner lifetime before installation.

## Sol IoT v23b main recovery reaper — 2026-10-28

Isolated `.iot-local-check/mt7603-main-recovery-reaper-v23b-20261028`
connects failed main VERIFY to an exact recovery owner, netdev hold, work
submission and a delayed external reaper. The reaper joins the main work
before retry or complete; canceled pending work is made retained first.
67/67 hashes and focused/broad source plus strict owner/reaper C11 fixtures
pass. The extracted actual `MainVirtualIF_open` host fixture also passes
three failed-VERIFY close paths and confirms exact queued recovery ownership.
See `docs/evidence/WR1200JS-IOT-V23B-MAIN-RECOVERY-REAPER-2026-10-28.md`.
This is nonproduction. Incomplete owners still block PCI removal, and
admission failure/exhausted retry have no complete drain. A false delayed-work
queue result may mean already pending; the idle-rejection mock was removed.
PCI source review confirms remove stops the reaper before checking retained
owners; an early return has no in-driver continuation. The state machine has
a retirement-close admission path, but PCI does not use it before stop.
The owner fixture now verifies retire -> exact retirement queue -> close
ticket -> preclose receipt; it does not bind the PCI callback or hardware.
The host PCI state contract additionally rejects stop before a joined,
zero-deferred-owner drain; both focused C11 fixtures pass.
The failed-VERIFY fixture confirms a queued recovery close can begin after
the retirement fence if stop has not yet been requested.
Upstream Linux 4.4.198 `flush_delayed_work` covers only the last queueing
instance; a self-rearming reaper needs a bounded owner-checked PCI drain.
The host PCI decision for completion, another pending instance or stalled
owner is now C11-tested; it is not wired to vendor PCI remove.
No MIPS build,
image or router proof. Next fault-inject the extracted PCI and recovery
callbacks together, then finish PCI lifetime/release before installation.

## Sol IoT v22 recovery RTNL trylock — 2026-10-28

Isolated `.iot-local-check/mt7603-main-recovery-rtnl-v22-20261028` adds
nonblocking RTNL admission to the recovery callback and a retained-owner
transition when RTNL is unavailable. Extracted actual callback and owner-state
host fixtures pass; 67/67 composition hashes match. See
`docs/evidence/WR1200JS-IOT-V22-RECOVERY-RTNL-TRYLOCK-2026-10-28.md`.
Queue/schedule submission, joined retry, netdev hold/release, adapter fence
and PCI teardown remain open. Nonproduction; no target/image/router proof.
The extracted callback fixture now models queue-before-`ndo_open`-RTNL-release:
the first callback can retain the owner, and only an external joined retry
can progress after RTNL is available. Next bind owner submission and external
reaper together with PCI release; a bare queue call is insufficient.

## Sol IoT v21 main VERIFY checked rollback — 2026-10-28

Isolated `.iot-local-check/mt7603-main-recovery-steering-rollback-v21-20261028`
adds synchronous checked close after failed main VERIFY. The main `ndo_open`
still owns RTNL; only completed close releases the module pin. All 67 source
hashes match the manifest. Focused/broad source checks and strict main-recovery,
MBSS and virtual-open host fixtures pass. The extracted actual main-open body
also passes complete-close and three fault-injected close stages with mocked
VERIFY/close helpers. See
`docs/evidence/WR1200JS-IOT-V21-MAIN-VERIFY-CHECKED-ROLLBACK-2026-10-28.md`.
This is nonproduction. Partial close still has no bound recovery worker;
RTNL/netdev/adapter lifetime and PCI removal remain open. Next bind
recovery/removal as one protocol. Do not install this driver or claim
image/router acceptance.
Source call-graph audit confirms no queue/schedule/requeue/complete caller
for the main recovery owner; PCI remove can return after joining with retained
ownership and no subsequent release path. Resolve queue, RTNL admission,
netdev/adapter lifetime and PCI release together. Evidence:
`docs/evidence/WR1200JS-IOT-V21-RECOVERY-REMOVE-CALLGRAPH-2026-10-28.md`.

## Sol IoT v20 main-readiness reconciliation — 2026-10-28

v19 did not include the parallel v44 main-readiness VERIFY producer.
Isolated `.iot-local-check/mt7603-main-recovery-steering-verify-v20-20261028`
adds it after main-open ownership and before HNAT/queue admission. Exactly
one of 67 staged files differs from v19. Focused structure, broad source,
MBSS host and virtual-open ownership checks pass. This is nonproduction;
failed VERIFY still retains an owner without a recovery drain. No target
compile, image or router proof. See
`docs/evidence/WR1200JS-IOT-V20-MAIN-VERIFY-RECONCILIATION-2026-10-28.md`.
The callback exists but has no queue/schedule caller and its close executor
does not acquire RTNL. Do not add a bare `schedule_work`: PCI remove joins
the worker, so blocking RTNL and adapter/netdev lifetime need one protocol.
`tools/iot/check-main-verify-recovery.c` passes against v20 headers and
models the failed VERIFY -> retained owner -> rejected schedule -> joined
retry path; it is not an actual workqueue or device test.

## Sol IoT Band Steering intent race — 2026-10-28

The strict `check-mbss-post-open.c` fixture reproduced false per-BSS ready
publication in v18 when reset arrived during BSS readback. Isolated v19
`.iot-local-check/mt7603-main-recovery-steering-race-v19-20261028` checks
pending reset/main-down/PM intent before ready and compensates with down if
intent arrives during the unlocked publisher. The strict fixture now passes
guest/IoT success, failed readback/count, partial open, reset and main-down
injections; broad source gate accepts v19 and rejects v18. One staged file
changed, 67/67 hashes match, nonproduction. Evidence:
`docs/evidence/WR1200JS-IOT-MBSS-STEERING-INTENT-RACE-2026-10-28.md`.
The daemon can briefly see ready before a compensating down. No target
compile or device verification; recovery owner/PCI release remain open.
The staged Band Steering session accepts status for configured primary
interfaces only (`ra0`/`rai0`); per-BSS `ra1`/IoT `ra2` delivery and IoT
exclusion remain unverified. Do not infer runtime convergence from the host
fixture or enable IoT steering by default.

## Sol IoT reset ticket wakeup — 2026-10-28

The shared `tools/iot/reset-admission.inc` and isolated v18 tree
`.iot-local-check/mt7603-main-recovery-reset-wake-v18-20261028` conditionally
wake waiters after a real reset-ticket retirement and after releasing both
transition and RTNL locks. The strict host fixture passed with mocked
hardware; 67/67 source hashes match. The broad virtual-call source gate now
passes v18 and rejects v17 for the missing reset wake; its stale whole-file
main-open count and direct-DOWN assumption were corrected. Evidence:
`docs/evidence/WR1200JS-IOT-RESET-TICKET-WAKE-2026-10-28.md`.
No target compile, image or router test. Continue focused race/failure checks,
recovery owner and PCI release; do not install the isolated candidate.

## Sol IoT MBSS ticket wakeup — 2026-10-28

The isolated v17 tree `.iot-local-check/mt7603-main-recovery-mbss-open-wake-v17-20261028`
adds five conditional wakeups after MBSS-open ticket retirement and after the
transition IRQ lock is released. One file differs from v16b; 67/67 hashes
match and `production_installed=false`. The broad source gate now stops at
`include/wr-iot-reset-admission.inc`, which lacks reset ticket wake coverage.
Next inspect reset retirement, add post-unlock wakeups, then test failure/race
behavior. This is not a MIPS build or device acceptance; do not install.

## Sol IoT MBSS open / Band Steering correction — 2026-10-28

Isolated v16b `.iot-local-check/mt7603-main-recovery-mbss-steering-v16b-20261028`
adds the matching MT7603 BSS1/BSS2 down event after successful checked
virtual DOWN with the close ticket held and no transition IRQ lock during
notification. Only two files differ from v15b; 67/67 hashes match. The broad
source gate now fails at MBSS-open ticket retirement wakeups. Bind and verify
those wake paths next. No MIPS compile, daemon race or device proof; do not
install v16b. The v16 draft is superseded by this comment-corrected output.

Isolated v15b:
`.iot-local-check/mt7603-main-recovery-mbss-ready-v15b-20261028` is a
67-file hash-verified, nonproduction successor. It moves MT7603 BSS1/BSS2
ready publication after claimed open, BSS observation and owned/count checks,
with the BSS_OPEN ticket still held and the IRQ lock released for the event.
Other boards/BSS retain their original vendor notification. The source gate
now fails on the old down notification preceding checked DOWN, which is the
next work item. First v15 draft was superseded because it excluded more BSS
than it replaced. No target compilation or device result; do not install.

The isolated v14 composition
`.iot-local-check/mt7603-main-recovery-mbss-open-v14-20261028` passes the
existing MBSS ticket/generation into `VIRTUAL_IF_UP_CLAIM` and retains the
module pin on failed vendor abort. No production install or target build.
The broad virtual-call gate now stops at the vendor Band Steering call.
Source audit corrected an earlier handoff assumption: `BndStrg_SetInfFlags`
tracks **each BSS** and emits an interface-named daemon status message, not a
single band-wide flag. The current MBSS ready message is premature (before
claimed UP/CR_ENABLE); its down message is premature (before checked DOWN).
The gate wording now reports these ordering faults. Do not simply delete the
per-BSS events; bind them to committed ownership and test failed UP/DOWN and
reset/close races. Evidence:
`docs/evidence/WR1200JS-IOT-BAND-STEERING-BSS-OWNERSHIP-2026-10-28.md`.
The gate also requires replacement notifications in checked open admission
and close execution, so removal alone cannot create a false pass. This is a
source presence guard, not proof of ordering or delivery.
The earlier v5/v6 handoff text below is retained as historical evidence and
is superseded on this specific Band Steering point. Recovery owner and PCI
release remain unbound; preserve the dirty shared worktree.

## Sol IoT auxiliary remove-result composition — 2026-10-28

The existing `prepare-mbss-checked-stop-candidate.py` was corrected for the
pinned driver's CRLF source and applied to v11. The separate v12 output
`.iot-local-check/mt7603-main-recovery-mbss-stop-v12-20261028` changes only
`ap/ap_mbss_inf.c`, routing MBSS `ndo_stop` through the checked close executor.
Its 67-file copy comparison, changed-file SHA256 and eight-pair remove ABI
pass. Full virtual-call coverage still fails on v11 and v12 for the same
uncomposed MBSS open path. Recovery owner and PCI release remain unbound;
do not install v12 or interpret a kernel `dev_close()` return as checked DOWN.

Source audit found a concrete partial unbind sequence despite checked return
values: a prior AP-client/WDS or MBSS netdev can be freed before a later
non-idle MBSS beacon refuses teardown. `rt_pci_remove` cannot cancel PCI
unbind by returning from its void callback. See
`docs/evidence/WR1200JS-IOT-PCI-PARTIAL-CHILD-REMOVE-2026-10-28.md` before
binding a release claim. The next change needs all-child checked close and
producer drain before destructive teardown, per-device completion receipts,
and an explicit post-mutation failure policy.
Pinned kernel `dev_close()` discards `ndo_stop` status and returns 0, so it
cannot supply that checked close. The active MBSS registry is OWNED while
`wr_iot_mbss_begin_remove` requires IDLE before unregister; use a driver-owned
checked DOWN plus recovery reconciliation and registry recheck.

`check-pci-remove-release-gate.py` now checks all four child-removal result
guards in `RtmpPhyNetDevExit`, with one negative mutation check per family.
The v11 source passes those guards but still fails the ordered PCI release
claim. A guarded `return FALSE` after earlier child mutation is not a safe
rollback or a successful PCI unbind; do not promote the candidate on this
source check alone.

The nonproduction v10 overlay omitted `include/ap_wds.h` and
`include/ap_apcli.h`, so the older WDS/AP-client/monitor remove-result
preparers could not be applied directly. The new
`tools/iot/prepare-remove-result-composition.py` verifies all input hashes,
reads those headers from pinned Git revision `c25283e915a2a00a763774dd255b14aff997285e`,
and runs both existing preparers plus their eight-pair ABI gate before
publishing the v11 output. All 67 output hashes match. The PCI release gate
still reports an absent ordered release claim; target compilation and device
behavior remain unverified. Continue with the PCI retirement/child teardown
producer and actual callback/DMA quiescence evidence before any production
integration. The failed direct attempt left an ignored partial scratch folder
`mt7603-main-recovery-wds-result-v11-20261028`; do not treat it as the v11
composition or delete it as part of unrelated cleanup.

## Sol IoT main-open claim composition — 2026-10-28

Important correction: after checked virtual DOWN decrements `VirtualIfCnt`,
the recovery owner must compare the actual count with the recorded pre-DOWN
count by `virtual_down_stage`. The earlier contract incorrectly required the
pre-DOWN value, so it could reject a retained ticket after physical-close
failure. `wr_iot_main_recovery_vendor_count_matches` now handles stage 0,
last-close stage 1 at zero, and stage 2 at N-1. Targeted strict GCC host
checks and the existing failed-open owner check passed. This remains a
host-only header until composed with the Linux worker.

`main-open-recovery-owner.h` now has `wr_iot_main_recovery_queue_close` for a
failed CLOSING `ndo_stop`. It admits only the recorded ticket, count and
retirement owner; stage 1 is reconcile-only, stage 2/3 can continue checked
DOWN. New `check-main-close-recovery-queue.c` and the existing failed-open
owner test both passed strict host GCC. This is still a contract, not a Linux
workqueue binding. The composed driver has not received the changed header.

The partial main close is now composed only into
`.iot-local-check/mt7603-main-close-composed-v1-20261028` by
`tools/iot/prepare-composed-main-close.py`. It verifies every input hash and
changes only `os/linux/rt_main_dev.c`; all 64 output hashes match. A fixture
extracted from that actual composed callback passed strict GCC host execution.
`main_close_recovery_bound=false`, `pci_release_gate_bound=false`, and
`production_installed=false` remain explicit; PCI release gate exits 1.

New uninstalled `tools/iot/main-close-checked.inc` models main `ndo_stop`
using the shared main ticket/record and checked DOWN. The extracted function
passed a strict GCC host fixture for last close, non-last close, failed DOWN
retaining pin/ticket, and replay rejection. This is not in the composed driver
because Linux ignores `ndo_stop` failure and no bound recovery worker or PCI
release gate can yet resolve retained ownership. Do not install it alone.

New isolated successor: `.iot-local-check/mt7603-main-open-radio-off-composed-v2-20261028`.
`tools/iot/prepare-composed-mt7603-radio-off.py` adds the reviewed MT7603
radio-off and bounded dequeue wait to the earlier queue/main-open bundle.
Only `radio-transition.h`, `rtmp.h`, `cmm_asic_mt.c`, and `rtmp_init_inf.c`
changed; all 64 manifest hashes match. Existing radio-off fault fixture and
extracted final checked-close strict GCC fixture passed. Physical RF/device
proof, main `ndo_stop`/recovery binding and PCI two-phase join are still open.
The PCI release source gate still exits 1 with the same three failures.

Exact release blocker: in the composed `os/linux/rt_main_dev.c`, a failed
`RT28xx_MBSS_Remove` makes `RtmpPhyNetDevExit` return `FALSE`; the call in
`os/linux/pci_main_dev.c::rt_pci_remove` discards that value and immediately
releases adapter, mapping and root netdev. No synchronous recovery-work join
or final deferred-owner gate exists there. Bind stop/close recovery and the
two-phase PCI join before allowing any such release; do not interpret a
host-only owner contract as the Linux operation.
`tools/iot/check-pci-remove-release-gate.py` is now an executable negative
gate: it exits 1 on this bundle and prints the discarded return, missing
join/release order and absent synchronous work join. A future pass would only
establish source ordering; control-flow, target and runtime evidence remain.

The composed dispatcher physical/main branch was also extracted and run in a
strict C11/GCC host fixture: first radio start, physical-open failure rollback,
ticket replay rejection, and later main open passed. The driver remains a
partial candidate; deferred checked close and Linux/PCI joins are next.

`tools/iot/prepare-queue-main-open-compose.py` now creates a separate partial
queue bundle with the reviewed main-open reservation, claimed virtual-UP ABI,
ticket wait queue and retained-pin failure path. The newer MBSS CR and Band
Steering files remain byte-identical to the queue input. Preparation and the
extracted strict GCC virtual-UP fixture passed. This is not a complete driver:
legacy auxiliary callers, deferred checked close, worker/PCI joins, target
build and device behavior remain open. See v43 preflight evidence.
The composer now rejects queue inputs whose file digests or pinned source
revision differ from its manifest. Fresh composition and all 64 output digest
checks passed. Next bind the actual checked-close work item and final PCI
join, then test the composed main callback; no kernel worker exists yet.
The actual composed main callback was then extracted and executed in a strict
host fixture. Early failure, post-mutation failure, success and late main-down
invalidation passed pin/registry assertions. Vendor and kernel actions were
injected; workqueue, checked close and PCI retirement remain open.

## Sol IoT full-bundle main-open audit — 2026-10-28

Fresh exact pinned-source queue assembly passed, but its `MainVirtualIF_open`
still decrements the module pin on failed virtual UP after AP main-open. The
separate main-open owner candidate is not composed. Manifest explicitly marks
virtual-open claim, owner composition and failed-open pin retention false;
full driver and
production installation remain false. See v43 preflight evidence. Compose
the missing command ABI and claim/registry path with a real checked deferred
owner and PCI join before
target compilation or packaging; do not treat adapter storage as recovery.
The older combined-open v27 provides the command ABI but cannot be copied
wholesale: it omits recovery-owner storage, weakens the newer MBSS CR result
handling and removes Band Steering readiness hooks. See the v43 preflight
file list and preserve newer behavior during composition.

## Sol IoT active-filter guard — 2026-10-28

The isolated RC generator now retains direct `ra2` INPUT/FORWARD drops
before `br-iot` allow rules even in the active-policy path. The
installed-helper fixture asserts their order. Python syntax and scoped diff
checks passed. The updated helper was spliced into a separate copy of the
previously prepared RC source; the fixture extractor included it. This does
not verify full generation, Linux C execution, target packet behavior or
firmware. Preserve the dirty worktree and validate before production activation.

## Sol IoT pre-bridge firewall candidate — 2026-10-27

The isolated RC generator now emits direct `ra2` INPUT/FORWARD drops when
`br-iot` is not yet owned; its installed-helper fixture expects that state.
Fresh local RC source generation passed. Windows GCC cannot compile the
extracted fixture (`arpa/inet.h` missing); run the existing Linux CI gate.
These rules alone do not prove isolation if `ra2` is already enslaved to a
different bridge. Keep BSS activation gated on owned bridge and policy proof.
Evidence: `docs/evidence/WR1200JS-IOT-ACTIVATION-GAP-2026-10-21.md`.

## Sol IoT bounded dequeue close — 2026-10-27

The isolated MT7603 checked-close generator now fails closed after a bounded
TX dequeue wait, before AP/IRQ/ring release. Exact generated-function GCC
fixture passed including stuck-queue and no-retry cases. Legacy void close,
PCI remove lifetime ownership, target compilation and router acceptance are
still open. See `docs/evidence/WR1200JS-IOT-MT7603-MAC-STOP-READBACK-2026-10-27.md`.

## Sol IoT release gate follow-up — 2026-10-27

The host release gate now requires a PCI observation tagged with the current
radio epoch; stale and missing observations are rejected in GCC fixtures.
Production must capture/recheck the epoch around the actual PCI operation,
while fencing all writers, before the gate can be bound.
Added a host-only final-remove bus-master clear/readback operation with failure
and silent-write tests. Do not call it for normal Wi-Fi down/reopen; no vendor
or kernel PCI binding exists yet.
The host-only adapter and PCI retirement gates require a clear PCI transaction
observation in addition to their prior inputs; four strict GCC fixtures passed.
The observer additionally rechecks bus master after the poll; fault injection
passed for re-enable and final-read failure. Inherited close callers discard
physical failure before PCI remove, which also ignores failed netdev exit.
This is still unbound to production and is not DMA quiescence proof. Next:
implement checked bus-master disable/readback and complete ring, IRQ, callback
and work retirement under one adapter lifetime owner before any vendor free.
Evidence: `docs/evidence/WR1200JS-IOT-PCI-TRANSACTION-OBSERVER-2026-10-27.md`.

## Sol IoT PCI transaction observation — 2026-10-27

Added host-only `tools/iot/pci-transaction-observer.h` and a strict GCC
fault-injection fixture. It rejects active bus master, invalid config reads,
all-ones data and Transaction Pending timeout; saved live Device Status was
`0x0010` on both endpoints at capture time. This is not a physical DMA receipt
and has no driver binding. Next: design checked bus-master disable/readback
and independent ring/callback/IRQ/work drain while retaining ownership on
uncertain outcomes. Evidence:
`docs/evidence/WR1200JS-IOT-PCI-TRANSACTION-OBSERVER-2026-10-27.md`.

## Sol BusyBox od inclusion — 2026-10-27

The WR1200JS build preparation now enables `CONFIG_OD=y` in the pinned
BusyBox config with `CONFIG_DESKTOP` still off. Image and QEMU gates were
added. See `docs/evidence/WR1200JS-BUSYBOX-OD-INTEGRATION-2026-10-27.md`.
Build #636 passed. Its exact-image audit confirms BusyBox 1.24.2, the `od`
applet and link, and target QEMU `od -b` on known bytes. The live router is
unchanged; exact image-size delta and device behavior remain unverified.
Continue the IoT priority.

## Sol IoT checked-stop follow-up — 2026-10-27

The isolated MT7603 radio-off builder now reads back both MAC TX/RX disable
bits after MCU radio-off and before PDMA disable; the host fixture passed
silent-write and invalid-read faults. Evidence:
`docs/evidence/WR1200JS-IOT-MT7603-MAC-STOP-READBACK-2026-10-27.md`.
No production binding, MIPS compile, image or device test. Continue the
adapter-wide callback/IRQ/work/DMA and PCI removal gate; do not release
resources from this MAC receipt alone.
The preserved close path logs radio-off failure but still reaches ring release;
PCI remove ignores `RtmpPhyNetDevExit()` failure. The idle poll only samples
DMA busy bits. The next candidate needs one owned release path with ring,
in-flight PCI, callback/IRQ/work, and adapter lifetime evidence. See the
source follow-up in the MAC stop readback evidence note.

## Sol BusyBox checkpoint — 2026-10-27

After the owner restored SSH, fixed `busybox-version` and `busybox-image`
checks exited 0. Live BusyBox is v1.24.2 with `hexdump -C/-n`, no `od`, and
SHA256 `87a15a8c1b06577c874f1a05edd80291991fd0d234c0e0d55a7a92df4335ecc0`.
Build 583's saved image also has version 1.24.2 but a different binary hash;
installed-build equivalence remains unknown. Earlier timeouts predated the
owner's restored connection. No router state was changed.
See `docs/evidence/WR1200JS-BUSYBOX-HEXDUMP-VERSION-2026-10-27.md`.
Continue IoT lifecycle work; identify installed build separately if needed.

## Sol continuation — live PCI config collection — 2026-10-27

The fixed read-only helper now ran successfully from Codex: `pci-config`,
`pci`, and `pci-dump-tools` all completed; the earlier pasted shell syntax
error did not reproduce. Live PCI mapping: `0000:01:00.0` is `14c3:7603`
(`mt7603_drv`), `0000:02:00.0` is `14c3:7662` (`rtpci`), plus two MTK
`0e8d:0801` host-bridge functions. BusyBox applet listing contains
`hexdump`, `base64`, `dd`, and `strings`, not `od`. The PCIe Device
Capabilities values read at offset `0x74` are `0x00008fc0` on both Wi-Fi endpoints;
`PCI_EXP_DEVCAP_FLR` is `0x10000000` in pinned
`include/uapi/linux/pci_regs.h`, so FLR bit 28 is clear for both endpoints.
Their conventional capability chains are PM at `0x40`, MSI at `0x50`, and
PCIe at `0x70`, with no PCI Advanced Features capability for AF FLR. PCIe
flags report version 2/type 0 (Endpoint) for both `14c3:7603` and
`14c3:7662`. Earlier `0x0042`/`0x00008000` values were mistakenly taken from
MTK host bridge 00:00.0. Sysfs places 01:00.0 under MTK 00:00.0 and 02:00.0
under MTK 00:01.0. Raw topology output is saved
at `docs/evidence/WR1200JS-LIVE-PCI-TOPOLOGY-2026-10-27.txt`.
Pinned `drivers/pci/quirks.c` has no device-specific reset entry for MediaTek
`14c3:7603`. PM D3hot-to-D0 is a generic reset candidate because PMCSR at
`0x44` read as zero, but that
kernel path does not check config writes or wait for pending transactions.
`pci_reset_function()` restores saved config including PCI_COMMAND, so it is
not a terminal bus-master-off action. PCI_COMMAND was `0x0006` on both Wi-Fi
functions at capture time. Raw helper output (140 lines) is saved at
`docs/evidence/WR1200JS-LIVE-PCI-CONFIG-2026-10-27.txt`.

No router state was changed. No standard PCIe FLR or conventional AF FLR is
advertised, and the pinned device-specific reset table has no MediaTek entry.
PM reset remains unproven as a DMA stop; no reset was invoked. This read does
not prove bus-master write/readback, in-flight transaction drain, or DMA
quiescence, and does not exclude vendor reset mechanisms. Continue the active IoT PCI/DMA terminal-removal analysis;
do not bind a remove fallback or free live resources based only on this dump.
Exact evidence and limits:
`docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.

## Sol continuation — failed-main-open owner contract (host-only) — 2026-10-27

Added `tools/iot/main-open-recovery-owner.h` and strict fixture
`tools/iot/check-main-open-recovery-owner.c`. The contract captures exact main
netdev/generation/open-token identity, requires netdev and adapter-release pins
before queueing, routes acquired main references to exact checked-close tickets,
and refuses to turn `UNCERTAIN_OPEN` into a guessed virtual DOWN/count decrement.
Release requires the per-record checked completion receipt, original module-pin
release and joined worker. Strict GCC C11 (`-Wall -Wextra -Werror`) passed.

This remains a host-only contract, not a production workqueue/RTNL/PCI binding,
MIPS compile, firmware image or router test. Next, establish a real deferred
owner ordering after failed `ndo_open` exits RTNL and before unregister/free,
with netdev/module/adapter pins preserved through worker cancellation and PCI
remove. Separately prove physical DMA/callback quiescence before any resources
are released. The open IoT PCI/DMA terminal-removal gate remains active; queued
BusyBox hexdump/version review does not take priority. Preserve all other local
changes and keep Sol the sole writer.

## Queued for Sol: BusyBox `hexdump` versus `od` — 2026-10-27

Owner reports that the WR1200JS has the BusyBox `hexdump` applet but no
standalone `od`. The existing delivery-scope note records a successful live
read-only `busybox hexdump -C -n 4096` PCI-config collection, but does not
identify the exact running BusyBox version or prove parity with `od`.

After the active IoT PCI/DMA terminal-removal gate, Sol should establish the
exact BusyBox version/source revision and image `.config`, inspect the image
binary hash, applet links and supported `hexdump` options, determine why `od`
is unavailable, and compare these with the router evidence. Decide whether the
specific read-only diagnostic can safely use `hexdump` in the firmware/helper;
record the command, output and limits in the existing BusyBox audit evidence.
No arbitrary SSH command, router mutation or image change is authorized by
this audit. Sol remains the sole writer; this queued task does not displace the
current IoT work or change project order.

## v43 MBSS preflight and pinned PCI/DMA audit — 2026-10-27

Local `47abc0a` and `4d8373e` prepare isolated v43 MBSS preflight and a
construction lease; strict extracted-source host fixtures passed. They are
not in the ordinary image. The PCI work-joined receipt has no producer.

New source audit used the exact build-pinned kernel commit
`c25283e915a2a00a763774dd255b14aff997285e`. In its `drivers/pci/pci.c`,
`pci_clear_master()` only calls the helper that reads `PCI_COMMAND`, clears
`PCI_COMMAND_MASTER`, and writes it; the helper ignores config read/write
status and does not read back the result. Pinned MT7621 config ops serialize
access but unconditionally report success. Thus this is not yet evidence that
all outstanding DMA is drained. Vendor `MTPciMlmeRadioOff()` logs poll timeout
and continues, while `wr_iot_pdma_reset_raw()` is a recovery routine that
re-enables DMA and IRQs. Neither is a terminal fallback.

Next prove the exact terminal remove policy: checked/stable device-side TX/RX
idle, bus-master inhibit and its readback/ordering limits, outstanding PCIe
transaction behavior, then worker/IRQ/TX-status/beacon quiescence before ring,
MMIO or adapter release. PCI `remove` is void and unbind continues, so a failed
stage needs a safe bounded fallback; do not bind v43 or free live resources
until that is established. The pinned MT7621 root reset path is probe-time and
not a per-device recovery API. Keep the candidate isolated. No target build,
firmware build, router mutation or runtime test was performed for this audit.
Evidence and source links are in
`docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.

## GitHub branch published — 2026-10-27

Standard fast-forward push moved `origin/codex/wr1200js-service-webui` from
`0641d96` to `84b2f12d2b653057e6806c824e7123757161a191`; remote head
was read back. Other local modified/untracked files remain in the shared
checkout. CI/image and router acceptance for the new host-only IoT contracts
have not been established by this push.

## IoT MBSS close proof — 2026-10-27

Commit `4cc18ad` adds host-only per-BSS registry proof for the existing
child-teardown close gate. Strict C11 fixture passes. Next: inspect how the
vendor driver can supply the exact published MBSS count and join checked
close/recovery under its adapter lock before `RT28xx_MBSS_Remove`; do not infer
production or device acceptance from this host model. Evidence:
`docs/evidence/WR1200JS-IOT-MBSS-CLOSE-EVIDENCE-2026-10-27.md`.
Follow-up `84b2f12` enforces checked DOWN stage 4 for every acquired MBSS.
The prepared v42 driver supplies count/registry candidates, but
`rt_pci_remove` ignores failed child exit then frees adapter/MMIO. Next owner
must solve close/join and terminal PCI failure handling before binding this
preflight; the host proof alone cannot make remove safe.

## RM2100 donor reviewed — 2026-10-27

Follow-up `be8b3f0` establishes that two of three PPP donor patches are
already in the pinned Padavan source; only peer-gateway population is a
conditional WAN-stage candidate. Our board selector already validates recipes.
See `docs/evidence/LJZKIRITO-PPP-AND-BOARD-SELECTOR-COMPARISON-2026-10-27.md`.
No production/network change was made. Preserve this handoff file's other
uncommitted work when preparing the next batch.
Optional IoT v42 run `40527671413` completed successfully on `0641d96`;
do not report that as device acceptance. The follow-up WAN overlay check found
no current PPP-gateway consumer, so patch 340 is deferred outside the image.

Commit `be8b3f0` includes three documentation-only audits of the archived
RM2100 Actions repository and all 38 public repositories from this owner.
Those commits are now published through `84b2f12`. Optional IoT v42 run
`40527671413` on its earlier head `0641d96` completed successfully.
The Actions wrapper has no firmware source tree; the owner's Padavan fork
differs mainly in RM2100 defaults, CI and user firewall rules. Do not copy
those addresses, ports, overclock or moving-source workflow into WR1200JS.
Only the conditional PPP peer-gateway patch remains for the WAN stage. See both
`docs/evidence/LJZKIRITO-*-AUDIT-2026-10-27.md` records.

## Isolated v42 candidate prepared — 2026-10-27

Commit `91a4537` versions the host child/PCI teardown models and requires
checked-close proof before family removal. Three GCC C11 fixtures passed;
kernel binding, MIPS target compile of this change and runtime remain open.

Source follow-up in
`docs/evidence/WR1200JS-IOT-V42-PCI-REMOVE-ORDER-2026-10-27.md`:
`MBSS_Remove` checks IDLE before child netdev detach, so an active IoT BSS
requires explicit checked close and joined deferred owner *before* removal.
The void PCI callback currently ignores `RtmpPhyNetDevExit(FALSE)` and frees
the adapter. A worker alone does not repair this order.

Run #634 (`40527671413`) passed and its `iot-merged-driver-probe` artifact
was downloaded and checked: isolated v42 `mt76x3_ap.ko`, 5,225,808 bytes,
SHA256 `46ef52aea556529ca4f711f267c5308f11978b223197dd2c2e85ce595d3cab3c`,
ELF32 MIPS32r2/O32. See
`docs/evidence/WR1200JS-IOT-V42-CI-634-TARGET-COMPILE-2026-10-27.md`.
This settles target compilation only. Next: bind and join deferred MBSS
recovery, fence PCI release, then prove late DMA/TxS lifetime safety. The
ordinary image and router still do not run v42.

Sol remains the sole writer. A new preparer layers a per-BSS beacon/TIM
producer gate on checked-stop v41 without installing it in the ordinary
image. The four coherent commits through `0641d96` were pushed together.
Local source preparation, host checks and isolated MIPS v42 compilation pass;
recovery/PCI binding and device acceptance remain open. #584 ABI and #633
firmware passed on `0641d96`. Optional v42 target run `40527671413`
passed on that SHA; do not duplicate it. #632 passed
on the earlier `5ebf69d`. See the beacon producer gate evidence file for exact scope and
verification. Preserve all unrelated worktree changes.

## Beacon producer lifetime follow-up — 2026-10-27

Sol remains single writer. Host-only `beacon-producer-gate.h` and its strict
C11 test now model a generation-bound pin from before beacon/TIM packet access
through final submit or cancel. The optional v42 source candidate binds it;
the production driver/image does not. See
`docs/evidence/WR1200JS-IOT-BEACON-PRODUCER-GATE-2026-10-27.md`. Bind all
producer paths, drain before buffer deinit, and complete deferred recovery/PCI
release gating before optional target acceptance. No router change occurred.

## Optional IoT #629 failure and fix — 2026-10-27

The next source audit identified a PCI teardown hole: the current isolated
`rt_pci_remove` ignores `RtmpPhyNetDevExit(FALSE)` and proceeds to adapter/MMIO
release. See
`docs/evidence/WR1200JS-IOT-V41-MBSS-RECOVERY-RELEASE-AUDIT-2026-10-27.md`.
The host recovery model now blocks registry reuse until the matching deferred
owner joins; strict C11 fixture passed. It is not yet bound in the driver.
The final submission paths share `BcnRingLock` with close intent, but
pre-close beacon/TIM producers hold packet pointers during preparation outside
it. DMA/TxS snapshots cannot prove those producers drained; the same audit
records the exact paths.
Do not install v41 until recovery is joined and PCI release is gated.

Optional IoT v41 #631 passed on `3868270`; the isolated MIPS32r2/O32 module
and manifest hashes match. See
`docs/evidence/WR1200JS-IOT-V41-CI-631-TARGET-COMPILE-2026-10-27.md`.
It is not in the ordinary image and has no on-device acceptance. Next: bind
deferred MBSS recovery to a kernel worker with netdev/adapter lifetime and
PCI release gating, then prove beacon DMA/TxS quiescence.

Firmware #630 and ABI #582 passed on `3868270`. Optional IoT-only v41
#631 (`40511894915`) was dispatched on that SHA and later passed.

Sol remains the single writer. #629 (`40447432208`) failed in a host-only
fixture compile: `check-mbss-close.c` did not mock the new ticket wait/wake.
The fixture now checks the successful and unsuccessful wake paths; three
strict C11 local variants pass. See
`docs/evidence/WR1200JS-IOT-V41-CI-629-HOST-FIXTURE-2026-10-27.md`.
No #629 MIPS module exists. Publish the narrow fix, verify ordinary gates,
then dispatch one optional v41 run. Do not install the candidate on a router.

## Recovery receipt and optional #629 — 2026-10-27

Sol remains the single writer. Firmware #628 and ABI #581 passed on published
`48ffaef`; optional IoT-only v41 #629 (`40447432208`) is running on that SHA.
Separately, the host-only MBSS recovery model now accepts the exact durable
stage-4 record receipt even if a later radio ticket has started or retired;
strict C11 compile/execution passed. See
`docs/evidence/WR1200JS-IOT-MBSS-RECOVERY-RECEIPT-2026-10-27.md`.
Do not infer a bound worker, image inclusion or runtime success. Preserve all
unrelated dirty files and wait for #629 before another candidate dispatch.

## Isolated v41 ticket wake — 2026-10-27

After #627's successful isolated target compile, source review found a
missing wait-queue wake after checked MBSS ticket retirement. The candidate
source and caller gate now require one wake after adapter-lock release, and
fresh v40/v41 local checks plus negative mutations pass. See
`docs/evidence/WR1200JS-IOT-V41-TICKET-WAKE-2026-10-27.md`.
Compile these new bytes in the next isolated v41 run after ordinary CI on
their published SHA. The recovery owner, PCI release fence and beacon
quiescence remain required; do not install the candidate. Preserve unrelated
dirty worktree files. Sol remains the single writer.

## Published gate repair and optional v41 run — 2026-10-27

Commit `e73f9dc` is published to PR #2. Ordinary firmware #626
(`40431336149`) and ABI #580 (`40431336135`) passed on that SHA. Optional
IoT-only v41 #627 (`40443241354`) was dispatched after both finished and is
successful. The downloaded MIPS module and manifest were verified separately:
`docs/evidence/WR1200JS-IOT-V41-CI-627-TARGET-COMPILE-2026-10-27.md`.
Continue the recovery owner and PCI lifetime binding; do not treat #627 as
production image or router acceptance. Sol remains the single writer;
preserve all unrelated dirty files.

## IoT v41 #625 gate repair — 2026-10-27

Sol remains the single writer. Optional #625 (`40429949035`) failed before
MIPS compilation: the caller-coverage gate expected v40's direct MBSS DOWN,
while v41 binds one checked executor. The original job log, local v40/v41
checks and negative mutation evidence are in
`docs/evidence/WR1200JS-IOT-V41-CI-625-COVERAGE-GATE-2026-10-27.md`.
Publish the coherent checker repair and local admission-failure owner test;
wait for ordinary CI on that SHA, then dispatch exactly one IoT-only v41
candidate run. Recovery owner and PCI release remain unbound, so do not put
v41 into the firmware or infer router acceptance. Preserve all other dirty
files in this shared checkout.

## IoT v41 next handoff — 2026-10-26

Sol remains the single writer. Firmware #623 (`40391518751`) and ABI
`40391518761` passed on `f1960a8`. The next local commits `a3f57e4`,
`b7b0f65`, `99b670b` add only an isolated checked MBSS stop binding and its
optional CI selector. The local generator verified a fresh 58-file v40 source
copy and changed only `ap/ap_mbss_inf.c`; YAML and Python syntax passed.
Recovery after failed `ndo_stop`, child quiescence and PCI release remain
unbound. The v41 candidate is not in a production image and has no MIPS or
router verification yet. After publication, reuse the automatically triggered
ordinary CI; once it finishes, dispatch one optional IoT-only v41 compile on
that SHA. Preserve all preexisting modified and untracked files.

## CI after IoT-only repair — 2026-10-26

Optional #622 (`40387415111`) succeeded on `b2ec889`. Isolated v40
`mt76x3_ap.ko` is ELF32 MIPS32r2/O32, 5,212,832 bytes, with independently
matched SHA-256. See
`docs/evidence/WR1200JS-IOT-V40-CI-622-TARGET-COMPILE-2026-10-26.md`.
It is not in the production image and has no on-device proof. Next: resolve
owned close/recovery and PCI lifetime binding before image inclusion.
Firmware #621 (`40385894396`) and ABI `40385894121` passed on published
`b2ec889`; #621 is an ordinary image build, not the optional candidate check.
Artifact details: `docs/evidence/WR1200JS-BUILD621-IOT-BASELINE-2026-10-26.md`.
Exactly one optional v40 run #622 (`40387415111`) was then dispatched on that
same SHA and completed successfully. Preserve all unrelated worktree changes.
No production IoT driver or device acceptance follows from #621.

## Optional IoT CI #620 — 2026-10-26

Run `40381625442` failed before candidate compilation: `candidate_scope=iot`
skipped the full Band Steering step that previously created
`$RUNNER_TEMP/wr1200js-steering-driver-probe`; the IoT step's first driver-tree
check then exited 1. The ordinary firmware image built and uploaded, but no
IoT candidate artifact exists. The published workflow repair prepares that isolated
tree directly for IoT-only scope; YAML and scoped diff checks passed, and #622
confirmed target compilation. Keep candidate, production image
and physical-router acceptance distinct. Preserve unrelated dirty files.
The failure monitor named the correct step but sampled the start of the long
job log; a local bounded-tail parser change and >16-MiB offline fixture passed.
Its workflow uses default-branch code, so publication on this feature branch
alone will not activate the parser change in the GitHub monitor.

## IoT v40 CI — 2026-10-26

Separately from published CI, a fresh local v40 candidate plus extracted
checked-close fixture passed strict C11 host execution in plain and MT_MAC
modes after adding the missing synthetic MT radio-off/adapter stubs. This
local fixture and HALT/PM generator edit are still dirty; no assembly
manifest or target compile was produced for those local bytes.

Firmware #619 (`40377110297`) and ABI `40377110309` passed on `676b020`.
Optional run `40381625442` was dispatched once for WR1200JS IoT v40 only on
that SHA and is in progress. Check its target compile/artifact result before
claiming candidate evidence. The pending local `1c400bd` and `c469f5a`
commits remain unpublished to avoid starting a second build while it runs.

## Actions storage / Mi Mini — 2026-10-26

Mi Mini isolated radio CI evidence is in local commit `1c400bd` and
`docs/evidence/MI-MINI-RADIO-PROBE-CI-2026-10-26.md`; the two old artifacts
were already unavailable. Thirty oldest WR1200JS ccache entries were removed,
leaving 14 recent compiler caches. Workflow history/artifacts were retained.
The local WR1200JS workflow change selects one UTC-day cache key and skips
saving on an exact hit; YAML/static checks passed, CI not yet run. Evidence:
`docs/evidence/ACTIONS-STORAGE-AUDIT-2026-10-26.md`. Ordinary firmware
`40377110297` on `676b020` was still active at the last check. Do not push
the local commit or workflow edit until it completes; then publish as one
coherent change set and verify new CI. Preserve all unrelated dirty files.

## CI candidate compilation scope — 2026-10-26

Independent local check: v39 checked-close synthetic fixture extracted; its
missing MT_MAC mock fields/functions were added locally. Both plain and
MT_MAC variants now pass strict C11 host compilation/execution. The fixture
always defines PCI support; v40 optional target job remains the next relevant
target compile evidence.

Firmware `40374656513` and ABI `40374656233` passed on `721fe60`. The three
local IoT commits and workflow commit `676b020` were published together by
normal fast-forward push; branch HEAD is `676b020`. CI for that SHA and one
optional v40 target compilation remain to be checked. Do not duplicate an
already queued/running workflow on this SHA.
Ordinary firmware `40377110297` and ABI `40377110309` are already in progress
on `676b020` at the latest check.

Changes in the two WR1200JS build workflows make optional manual
candidate checks IoT-only by default; selecting `all` runs the prior full
suite. Ordinary PR firmware/image checks are unchanged. YAML and scoped
conditions passed local static checks; no build has validated these workflow
edits. Preserve the unrelated dirty worktree. Verify the scope in one
subsequent optional IoT candidate run, without dispatching duplicates.

## Latest IoT handoff — 2026-10-26

Published `1ac816a` serializes the checked MBSS close executor per registration;
the host fixture injects a same-ticket reentrant call during vendor close.
Published `690206d` adds the field to the actual v40 generator's copied header.
Fresh generated source passed plain, MT_MAC and MT_MAC/PCI strict host close
fixtures; interface-reference/recovery-owner fixtures and Python syntax also
passed. Ordinary firmware `40374656513` on parent `721fe60` passed. Run one
optional v40 target check for new SHA `676b020`. Production worker,
PCI lifetime binding, image inclusion and device test remain open.

Published `472c2ca` adds MT_MAC without PCI to the optional close host gate and
fixes its DMA stub declaration for that compile mode. Plain, MT_MAC and
MT_MAC/PCI strict C11 fixtures passed; YAML and scoped diff checks passed.
Ordinary firmware `40374656513` and ABI `40374656233` on parent `721fe60`
passed; do not duplicate them. Run one optional v40 check for new SHA `676b020`.

Published commit `721fe60` adds an optional v40 host gate covering MT_MAC/PCI
beacon DMA and TxS pending close. Plain and MT_MAC/PCI strict C11 fixtures
passed; workflow YAML parsing and scoped diff check passed. Optional v40 run
`40368551644` passed on parent `bd9f49a`, including target compilation.
Ordinary firmware `40374656513` and ABI `40374656233` were in progress on
`721fe60` at the latest check; they do not select v40. Recheck them before
dispatching a candidate check on `721fe60`.
The new gate tests host control flow; it is not production binding or device
acceptance.

Optional v40 workflow `40360064346` passed on `59db347`, including isolated
MT7603 candidate compilation. Sol then pushed `bd9f49a` with operation/count
and reset-kind ticket validation for checked MBSS close and the recovery-owner
model. Both focused strict C11 host fixtures passed; scoped `git diff --check`
passed. The local host close fixture does not define MT_MAC vendor stubs, so
that mode did not compile locally. Await CI for the new SHA; its normal firmware
build does not select v40. Real close owner/worker, `ndo_stop` and PCI lifetime
binding, final image inclusion and device acceptance are still pending.

Ordinary firmware `40357156009` and ABI `40357155947` passed on `59db347`.
Ordinary firmware `40363573850` and ABI `40363573442` were in progress on
`bd9f49a` at the latest check; neither selects optional v40. Do not dispatch
duplicate runs on either SHA.

The v40 generator now copies a checked MBSS close helper that records full
ticket provenance in the interface ref at admission and rejects altered
epoch/prior state before vendor mutation. The existing host recovery owner
validates the recorded ticket and copies it for continuation, including
main-down epoch drift. Fresh v40 generation and both focused C11 tests passed;
`check-mt7603-checked-off.py` and `git diff --check` passed. Code/test commit
`59db347` is published. These changed bytes have not yet had a fresh target
MIPS compile or a production binding. This documentation update remains local
with other pre-existing edits.

Updated `tools/iot/mbss-close-recovery-owner.h` to retain and copy the full
checked-close radio ticket, instead of retaining only its serial. The host
fixture now rejects missing or wrong-epoch tickets in the normal phase and
copies the original ticket if main-down advances the epoch during admitted
close. Strict GCC C11 test and `git diff --check`
passed. This is still a host contract: the next implementation step is an
actual adapter/netdev-pinned worker and `ndo_stop`/remove binding.

Optional v40 workflow `40350468431` succeeded on `cde9846`, including the
isolated MT7603 candidate compile. It does not install that driver into the
ordinary image. Source review found `MBSS_Remove` can deinitialize beacon
storage before a successful checked close. Its current `RtmpOSNetDevClose`
wrapper returns void, and PCI remove ignores `RtmpPhyNetDevExit` failure, so
neither a bare preclose call nor an early failure return is a safe complete
fix. Bind a retained close/recovery owner, gate beacon deinit on verified
close, and fence adapter release before promoting the candidate.
`RtmpOSNetDevProtect(1)` takes RTNL; `RtmpOSNetDevDetach` calls
`unregister_netdevice` under it. Keep a future explicit `dev_close` and
removal admission in one RTNL-protected sequence without nesting the existing
protect wrapper. The separate adapter transition lock must guard the matching
generation/ticket and close receipt. The current AUX pre-unregister pattern
checks a consumed registry reference after void `RtmpOSNetDevClose`; for MBSS
it cannot succeed on an opened BSS until checked close is actually bound.

Published HEAD `cde9846` has the v40 final-RX-read disappearance guard.
Fresh isolated generation and generated-source host fault tests passed. The
ordinary firmware #611 on parent `54061d3` succeeded. Firmware #612
(`40344805795`) and ABI `40344805641` also completed successfully on
`cde9846`; neither selects v40. Optional run `40350468431` later passed the
isolated candidate step. This is not a production image or device test.

Owner decision: HTOP/MTR are not required in the standard WR1200JS image.
Their WR1200JS selectors are commented and may be enabled individually only
for a separately checked diagnostic build. Older mandatory-item-4 wording
below is superseded; continue IoT first.

Sol remains the single writer. HEAD `6bae503` is published; it adds the
generated-source DMA fault fixture to optional v40 CI. The strict local host
test passed, including NIC disappearance in both TX and RX loops. Ordinary
firmware `40335749228` was queued and ABI `40335749283` in progress when last
checked; neither selects v40. Recheck their live state before any dispatch.
The next substantive driver task is an actual retained close/recovery owner
and PCI lifetime binding: generated `MBSS_VirtualIF_Close` still discards
checked status, and replacing that callback alone is unsafe because netdev
teardown can continue after a failed close. See the PCI retirement evidence.
Preserve all other local changes. No router write or reboot occurred.

Sol is the single writer. Read `AGENTS.md`, `PROJECT_STATUS.md`,
`docs/AGENT-BOOTSTRAP.md`, `docs/EXECUTION-ROLE.md` and `git status -sb`
before changing files. Preserve every unrelated local modification.

1. Current local and GitHub branch HEAD is documentation commit
   `ba118ea9916b17572d756253cc493f4338572af5`; source baseline
   `a71e8abedf4c2a6c1fd5df2917002db990df84e2` is the code
   revision built by run #600 (`40216625327`). That run completed successfully: the
   WR1200JS firmware and isolated merged IoT MT7603 v40 target compile both
   passed. The candidate `.ko` is ELF32 MIPS32r2/O32, 5,202,152 bytes,
   SHA-256 `f01a3272ac60769dd08a312fbe67622284fa590a533285335a749a300b75a4e5`.
   One non-fatal `modpost` section-mismatch warning remains unidentified. Full
   evidence: `docs/evidence/WR1200JS-IOT-V40-CI-600-TARGET-COMPILE-2026-10-25.md`.
   Firmware #601 (`40218879277`) and service ABI `40218879240` on
   documentation-only parent `c2b1d48` passed. ABI `40219026319` on current
   HEAD passed; firmware #602 (`40219026350`) was still in progress at the
   2026-10-25 check. None selects another IoT candidate compile.
2. v40 remains an **isolated candidate**, not the production driver. The normal
   firmware image is built before this probe and does not include it. No router
   runtime was tested. Continue with the PCI remove/adapter lifetime blocker,
   including actual worker join and checked child/root quiescence. Then follow
   the remaining IoT acceptance sequence in `docs/PROJECT-DELIVERY-SCOPE.md`.
   A source reachability review also found that `MainVirtualIF_close` still
   uses the legacy unchecked DOWN dispatcher, while the separate main-open
   owner candidate finishes `UNVERIFIED` and cannot authorize BSS open.
   Serialize all vendor count writers and bind a real main-radio readiness
   observation before considering that candidate for packaging. Exact paths
   and evidence are appended to the #600 target-compile report.
   The local MT7603 main observer now checks beacon-queue bit 17 for IoT BSS
   2, matching the pinned driver's `BssId + 15` mask. A targeted host fixture
   failed with the old mask and passes with the corrected one. Regenerate and
   target-compile a candidate before treating this as integrated; no router
   or production image was changed. Details are in the #600 evidence report.
   The same observer no longer requires IoT `!netif_running`: the pinned
   kernel sets START before calling its `ndo_open`, where staged MBSS admission
   invokes the observer. A host fixture reproduced the prior false rejection
   and passes after removing that condition. Keep all admission owners bound
   before using this local predicate in production.
   The optional candidate CI step now checks the staged observer header and
   enables its MIPS compile probe. Local YAML and host checks passed; await a
   new candidate run for target evidence.
   Guest-first open still blocks IoT: each successful staged BSS open ends in
   UNVERIFIED, and raw CR_ENABLE discards its result. A local post-open
   guest/IoT queue/readback observer plus strict host cases now exists, and
   the target probe compiles both observer entry points. Bind only after
   checked CR_ENABLE and retained partial-failure ownership are resolved;
   details are in the #600 evidence report.
   The local assembler now checks CR_ENABLE and treats a post-UP failure as
   uncertain open, retaining the pin before HNAT/queue publication. Only
   Python syntax and the pinned source anchor were checked locally; regenerate
   and target-compile before crediting this path. Recovery after failed
   `ndo_open` and post-open READY publication remain unbound.
   The shared transform is `tools/iot/mbss_cr_enable.py`; the generated-C host
   fixture `check_mbss_cr_enable.py` passed five strict MinGW C11 paths,
   including failed CR_ENABLE with retained pin/count and no queue. This does
   not replace the required MIPS build or recovery proof.
   The optional candidate workflow now executes that fixture on the assembled
   source before MIPS build. Workflow YAML parsed; no new run has tested the
   gate yet.
   The local `wr_iot_main_radio_verify_owned` helper now checks the owned MAIN
   record and count while retiring a VERIFY ticket; its strict C11 host
   fixture passed. It has no vendor call site or MIPS/image evidence yet.
   The follow-up source check confirms that `rt_pci_remove` still ignores the
   child-teardown result. Resolve the persistent-failure ownership of its
   `void` callback before binding a worker; the ordered gate and exact source
   path are recorded in `docs/evidence/WR1200JS-IOT-PCI-RETIREMENT-OWNER-2026-10-25.md`.
   Host-only stop-request-before-join phase checking and its C11 fixture pass;
   this is not a vendor work cancellation or PCI release implementation.
   Also bind checked main stop: current `MainVirtualIF_close` returns success
   and releases its module pin without verified physical-close completion.
   `RTMPInfClose` returns void, and the existing checked close proves software
   shutdown only. Do not fabricate `physical_verified` when connecting the
   main-stop host contract; add an RF/DMA-quiescence observer and
   retained-ticket recovery first.
   Source trace found the immediate MT7603 blocker: checked close calls
   `RT28xxPciAsicRadioOff`, which unconditionally rejects `HIF_MT`; MT7603
   sets that type. `MTPciMlmeRadioOff` is void and discards probe outcomes.
   Implement a checked MT-specific stop before treating any shutdown receipt
   as proof of physical quiescence. The isolated v40 source overlay now target-
   compiles and has host fault-injection coverage, but its physical/RF evidence
   and production owner bindings remain open. See the PCI-retirement evidence.
   Ordinary firmware #598 (`40215206293`) and Band
   Steering ABI (`40215206230`) have both passed. Neither selects v40. Published
   commits `83289bd`, `b1953b2` and `8fe91c0` expose and check the v40 path.
   Python generation, YAML parsing and the eight-pair remove ABI check passed
   locally. Follow-up commits `83289bd`, `b1953b2`, `8fe91c0`, and `a71e8ab`
   are pushed. Candidate compile is not production-image inclusion or runtime
   evidence.
   The generated checked-off C body also passed a strict host GCC fault fixture
   for poll, MCU, PDMA and register-readback failure ordering. Production-image
   integration and hardware acceptance remain pending. The fixture and CI hook
   are in `b1953b2`.
   Five-family virtual-interface call coverage also passed on v39 and v40 after
   updating its WDS remove signature boundary for the reviewed `INT` return.
   The main-stop host contract now keeps a failed CLOSE ticket busy for v40's
   same-ticket retry; strict C11 fault/retry fixture passed. This is model
   evidence only; its dependent files remain local with modified shared
   headers. Caller-coverage gate is in `8fe91c0`.
   `MainVirtualIF_close` and PCI lifetime are not source-bound.
   HTOP/MTR were later changed to optional, default-off diagnostics by the
   2026-10-26 owner decision; no package inclusion is claimed.
3. Do not rerun #600 or claim device acceptance from CI. Do not write, flash or
   reboot the router without separate authorization. Keep the one-minute
   Codex heartbeat paused and inspect original diagnostics for new failures.

Evidence: `docs/evidence/WR1200JS-IOT-V39-CI-595-TARGET-COMPILE-2026-10-25.md`.
Older entries below are preserved for traceability; their old queue states and
next-step instructions are historical, not current commands.

## Historical handoff entries (superseded by current handoff above)

## Sol accepted single-writer role — 2026-10-25

Sol accepted the user's explicit transfer after DeepSeek's documentation-only
handoff `6f459de`. Branch `codex/wr1200js-service-webui` matched GitHub at
that commit; 177 working-tree entries remain preserved and unstaged for this
role record. Finish IoT first, then review Zapret2 and Modern WebUI. Firmware
run `40190118803` was still in progress; no image or router acceptance claimed.

## Zapret2 build #586 evidence — 2026-10-25

Sol inspected successful run `40190599321` on `5953fc4`, downloaded its
firmware and target audit artifacts, and verified the TRX SHA256 plus all
Zapret2 package, service, WebUI and dependency-closure image gates. See
`docs/evidence/WR1200JS-BUILD586-ZAPRET2-2026-10-25.md`. Packaging is
confirmed; no router runtime or traffic/rollback test was performed. Continue
IoT first under the user's delivery order; later device acceptance needs
separate authorization.

## IoT deferred close completion receipt — 2026-10-25

The host-only deferred WDS owner now snapshots checked completion under the
adapter lock; after worker join it no longer depends on a possibly newer
global `retired_serial`. C11 fixture covers wrong serial, duplicate claim,
later ticket and release gate. Next: source-bind the PCI release fence and
retained worker together; no production, image or router change yet.

## IoT deferred close lifetime contract — 2026-10-25

Host-only `tools/iot/aux-close-recovery-owner.h` and its C11 fixture now
model retained adapter/netdev ownership through failed WDS close retries.
Release needs checked completion and a joined worker; stop/cancel alone is
insufficient. Next executor must enforce this fence in real PCI remove,
unbind and adapter free paths before scheduling any kernel work. No
production driver, image or router change.

## IoT WDS partial-DOWN reconciliation candidate v33 — 2026-10-25

Generated `.iot-local-check/wds-close-v33-20261025`. Its checked WDS close
and continuation reconcile both a failed, unmutated DOWN and a successful
DOWN followed by failed ticket finish; the latter never repeats DOWN.
Extracted host C11 and v31-v33 source gates passed. Next: bind a pinned
retained worker with adapter/netdev lifetime, cancellation and drain before
release; then AP-client/monitor stop and target compile. Still no production
binding, image or device verification.

## IoT WDS retained retry candidate v32 — 2026-10-25

Generated `.iot-local-check/wds-close-v32-20261025` with the updated
reference header and exclusive same-ticket WDS continuation. Strict host
C11 extraction against candidate headers, five-family coverage and Python
syntax passed. Next: a pinned retained worker with release/drain semantics,
then reconcile partial completion after successful DOWN; bind AP-client and
monitor stop before target/image integration. No router action.

## IoT AUX_CLOSE retry gate — 2026-10-25

The non-last WDS close model records the admitted AUX_CLOSE ticket identity
for a later retry after a failed, unmutated checked DOWN. Same-ticket host
C11 tests pass; reset/epoch/count/stage mismatch is refused. Next owner must
bind a retained recovery worker and reconcile a DOWN that may have succeeded
before wrapper failure, then extend AP-client/monitor stop. This is not in
the production driver, image or router.

## IoT prepared-source overlap handoff — 2026-10-24

The #542 full candidate is pinned to clean upstream MT7603. A new read-only
gate, `tools/iot/check-overlay-conflicts.py`, verifies its hashes and checks
overlays against any supplied prepared driver tree. The pristine tree passes;
the partial ABI RSSI query fixture has four modified overlapping paths and is
incomplete. A verified full upstream source copy then passed 20 precompiler
Band Steering stages and all five RSSI stages. Five complete-tree conflicts:
`ap/ap.c`, `ap/ap_cfg.c`, `common/rtmp_init.c`, `hw_ctrl/cmm_asic_mt.c`,
`include/rtmp.h`. Target compiler absent locally; later Band Steering probe
and package stages were inspected but not executed. Do not overlay the
candidate wholesale or call this a target compile. Merge those five files,
then compile the merged candidate in isolation. Evidence:
`docs/evidence/WR1200JS-IOT-OVERLAY-CONFLICTS-2026-10-24.md`.
An LF-normalized three-way probe cleanly text-merged four paths and exposed
one actual conflict in `common/rtmp_init.c` before `*ppAdapter`: keep both
RSSI observer/birth and IoT transition/reference initialization. Review all
five files for semantics; none is production installed.
`tools/iot/assemble-prepared-candidate.py` now stages a hash-guarded full
candidate under sibling `iot-merged-candidate-20261024`. It retained both
initialization sequences; 45 output hashes match its manifest and conflict
markers are absent. This is source evidence only. Review the merged driver,
then use the exact WR1200JS target configuration for isolated compilation;
keep the candidate out of the firmware image until remaining gates pass.
The current local generator output normalized to LF matches the #542-based
merged output hashes. Optional target-probe workflow step was pushed in commit
`5a09fc7`; its shell passes local `bash -n`. Once baseline checks for this
commit finish, dispatch one `run_candidate_checks=true` build if none already
exists. The optional step never installs IoT into the production image.
Current handles: baseline firmware #543 run `40045468630`; ABI run
`40045468649`, both in progress at last read. Reuse these results, then check
the queue before one optional dispatch. No optional target compile has run.
Both baseline checks finished successfully. The one optional candidate run is
`40046513315` at head `5a09fc7`, in progress at last read. Inspect its exact
failed step/log or its `iot-merged-driver-probe` artifact; do not dispatch a
duplicate. A green baseline image does not prove this candidate or runtime.

## Beacon DMA failure handoff — 2026-10-23

Pinned RtmpDrvPciMapSingle returns 0 on DMA mapping error, while
RtmpPCIMgmtKickOut ignores that result and advances the descriptor/index with
unconditional zero return. Existing beacon PID may already be reserved.
Partial manifest now has ring admission/submit accounting false. Next: checked
capacity under BcnRingLock, real map/submit status and PID rollback or
quarantine before using TxS for IoT retirement. No router/driver installation.

## Beacon ring admission handoff — 2026-10-23

ap_connect.c:614 prechecks free ring outside BcnRingLock, reserves TxS PID
while building TMAC, then cmm_mac_pci.c kickout later holds ring lock with no
capacity recheck or PID rollback. RtmpPCIMgmtKickOut returns zero after index
advance, without reviewed ring-full/DMA-error branch. Treat failed/uncertain
enqueue as unknown completion; do not release IoT BSSID from TxS counts.
Next: tie locked ring admission to reservation and checked rollback/quarantine.
See IoT contract. No production/device change in this audit.

## TxS occupied-PID handoff — 2026-10-23

Candidate now covers four TMAC AddTxSStatus callers, shared allocator and
header. Occupied PID is skipped; full table suppresses host TxS without
overwriting live metadata. Local extracted Add/Remove fixture passed; unified
bundle ../iot-unified-txs-no-overwrite-v2-20261023 assembled. Missing host
status must quarantine BSS retirement. Reused-PID late responses, enqueue
failure, shutdown quiescence, target compile and device proof remain open.
Candidate is not production installed. See IoT contract.

## TxS metadata lock handoff — 2026-10-23

Partial candidate now stages pinned txs.c/mt_mac.h metadata lock for global
Add/Remove, initialized/freed with the TxS table. Unified bundle
../iot-unified-txs-lock-v2-20261023 and extracted Add/Remove local GCC fixture
passed. This does not resolve occupied PID overwrite, callbacks racing table
shutdown, actual IRQ timing, MIPS build or IoT retirement. Keep production
binding off. See IoT contract for evidence and next gates.

## TxS fixture/CI handoff — 2026-10-23

Generated host fixture uses the candidate's actual RemoveTxSStatus; strict
MinGW GCC run passed completed/duplicate/unused PID and rate indexing. Added
generation/compile/run to ABI workflow after unified assembly. CI still awaits
push/run; this fixture does not prove parser, concurrency, MIPS or hardware.
See IoT contract and sibling iot-txs-status-check-20261023.c/.exe.

## Pinned TxS parser candidate handoff — 2026-10-23

Exact blob ece66c6 TxS parser stage added to unified partial assembler.
Generated source rejects unknown/unused completion PID and corrects rate
index; local standalone/unified manifests exist in sibling workspace dirs.
This is not target compiled or production installed. Add/Remove synchronization,
occupied-PID collision policy, late-result semantics, beacon producer stop and
DMA/TxS drain remain required before IoT BSS reuse. See IoT contract.

## Global TxS allocator audit handoff — 2026-10-23

All four AddTxSStatus sites are in mac/mt_mac.c; management and data share the
256 PID slots. cmm_data.c:611 is the common completion entry. RemoveTxSStatus
does not reject unused PID; parser ignores its result. Do not patch only the
beacon callback or count completions as proof. Next implementation must cover
global allocation, parser validation, synchronization and hardware PID-reuse
semantics; then prove producer/DMA/TxS quiescence. See IoT contract.

## Beacon TxS PID reuse handoff — 2026-10-23

Pinned ap_connect.c uses TxSPriv=apidx; TxS status table has wrapping UINT8
PID and overwrites TXS_USED entries. A generation tag in Priv cannot establish
retirement after collision/wrap. Next design checked PID ownership and explicit
overflow/unknown-result handling across all TxS producers, then prove producer
stop and DMA/TxS drain before registry vendor_done. See IoT contract for exact
source lines. No production/device change.

## Beacon completion audit handoff — 2026-10-23

Sol traced pinned beacon DMA and TxS dispatch. DMA ring completion clears packet
pointers under BcnRingLock; TxS callback uses only BSSID index. Recovery flush
re-enables beacon, and ExitTxSTypeTable is adapter-wide. Do not release/reuse an
IoT BSSID slot from CR_DISABLE, IDLE, DMA completion or recovery flush alone.
Next: design/prove per-BSS producer stop plus DMA/TxS drain under pinned adapter
lifetime; then bind registry vendor_done. See IoT contract. Candidate remains
uninstalled; no target compile, image or router mutation. Separate source-tree
consolidation stage is scheduled after firmware acceptance in delivery scope.

## Beacon/TxS retirement gap confirmed — 2026-10-23

CR_DISABLE only clears queue-start/TBTT; IDLE also written by reset/recovery.
TxS callbacks use BSSID index, not registry generation. Cannot mark vendor_done
from disable success or idle sample; selective slot reuse needs real DMA/TxS
retirement proof. Next inspect flush/completion paths before binding registry
release. Scope unchanged, no production/device changes. See IoT contract.
## Target TU artifacts now preserved for future CI — 2026-10-23

Local WSL/toolchain inventory did not confirm usable target environment;
#535 capacity evidence lacks rt_linux macros. Probe now saves exact Kbuild bytes,
preprocessing argv and macro stdout/hashes. Six synthetic controls passed with
artifact assertions, evidence Temp/iot-task-config-controls-0cbvt2ag.
Actual MIPS proof pending; no workflow/system/router changes. Continue lifecycle
binding and retained-resource/ndo_stop work. See IoT contract.
## Last-MBSS checked physical close chain passed — 2026-10-23

Final-source integration passed failed-join retention, successful one-time ref/
module consumption and radiooff failure quarantine without repeated hardware.
Repeatable extractor/ABI equivalent saved. Evidence Temp/iot-unified-radio-
9h9m7gcq/bundle-mbss-open-close/check-last-close.c. Actual adapter pinning,
ndo_stop recovery/PCI removal and MIPS/runtime remain pending. No router change.
## Final MBSS open/close chain verified — 2026-10-23

Composed final raw/admitted open, checked close and real candidate DOWN; three
strict host variants passed failed UP, successful acquisition, selective close,
count/reference/module consume once and repeated close. Fixed test-only VOID*
cast and close-ioctl owner assertions before successful rerun. Evidence Temp/
iot-unified-radio-9h9m7gcq/bundle-mbss-open-close/check-open-close-owner.c.
ABI equivalent staged; actual ndo_stop recovery/other families/runtime pending.
No production/router changes.
## Checked MBSS close reference consumption implemented in candidate — 2026-10-22

Staged separate checked MBSS close: owns acquisition once, preserves per-step
progress, propagates CR/direct-MBSS/DOWN failures, consumes reference/module ref
only after successful DOWN. Three strict host variants passed failure/retry/
stale/duplicate cases. Legacy ndo_stop unchanged; generated composition, actual
retained-resource continuation and MIPS/device verification remain next.
No production/router changes. See IoT contract.
## MBSS open now acquires registration reference in candidate — 2026-10-22

Published IDLE record reserved with BSS_OPEN ticket before raw mutations;
reviewed failed-UP paths leave IDLE, successful vendor UP marks OWNED while
radio stays UNVERIFIED. Full bundle generation and three final-source strict
host variants passed. Evidence Temp/iot-unified-radio-9h9m7gcq/bundle-mbss-reference.
Next MBSS close consumes once; other families/lifetime/target still pending.
No production/router change.
## Published registry release requires removal milestones — 2026-10-22

Published records cannot release merely because IDLE: require removal intent,
consumed reference, kernel unregister done then vendor quiescence done. Intent
blocks new acquisition; failed unpublished attach rollback retained. Three
strict host suites passed, including active-close refusal and milestone order.
Actual unregister/drain binding still pending. No production/router change.
## MBSS unregister boundaries confirmed — 2026-10-22

Kernel reference drain occurs at protected RTNL unlock after Detach; wdev
index unregister merely clears array entry. Beacon deinit may return FALSE
when busy, currently ignored. Cannot release registry unconditionally: need
checked stop/kernel/vendor-beacon milestones and no duplicate unregister on
retry. Source evidence in IoT contract; next checked removal checkpoints.
No production/router changes.
## Final MBSS registry constructor check passed — 2026-10-22

Generated full registry-attach bundle, extracted final MBSS_Init with final
bridge/header and passed strict constructor failure/success host cases. No
failed-current slot leak; prior successful BSS retained. Repeatable tool and ABI
sanitizer equivalent staged. Evidence Temp/wr-iot-mbss-registry.c and bundle-
registry-attach. Next successful unregister retirement and other family binding.
No target/device acceptance. See IoT contract.
## MBSS candidate attach now reserves registry before publication — 2026-10-22

New checked registration bridge bound to reviewed MBSS_Init source in assembler.
Host prepublication/failed-attach/retry-generation/full/duplicate/retiring cases
passed. Other family constructors ignore some attach failures and need review
before binding; successful unregister registry release not implemented. Final
composition/target checks pending. No production/router change. See contract.
## Interface registry helpers passed host cases — 2026-10-22

Bounded slot mapping now rejects full/duplicate registration and active release;
reuse gets new generation, stale callbacks refuse. Persistent strict host cases
passed after initializing fixture dummy identities. Adapter bundle carries
registry header; actual registration/unregister and quiescence proof pending.
Next bind registry lifetime to netdevice paths without resetting live records.
No production/router changes. See IoT contract.
## Adapter-owned interface records staged — 2026-10-22

Storage candidate uses WDEV_NUM_MAX+1 (extra monitor), separate from MBSS
reset memory; registration generation and idle slots initialized only at fresh
adapter publication. Exact generation passed. Target layout/compile and actual
registration/five-family mapping remain pending. Evidence Temp/iot-unified-radio-
9h9m7gcq/adapter-interface-storage. No production/router change.
## Interface-reference acquisition model checked — 2026-10-22

Added device+registration-generation+monotonic-token ownership model. Failed UP
cannot authorize DOWN; owned ref consumed once only after checked close success.
Host identity/stale/duplicate/exhaustion cases passed. Registration generation
kept distinct from reset radio epoch. Storage/capacity and five-family binding
still pending. No production/router change. See IoT contract.
## Per-interface reference ownership cannot use beacon flags — 2026-10-22

MBSS_Open sets beacon intent before successful UP; AirPlay also affects it.
netif_running cleared before stop, wifi_dev inspected fields provide no owned
UP reference proof. Need netdevice+generation acquisition/consume bookkeeping
for all families, preserving pending last close; do not decrement by count or
beacon flag alone. Source details in IoT contract. Next adapter-owned ownership
integration. No production/device changes.
## Final close-result chain composed and host-checked — 2026-10-22

Full generation passed; final down + rt28xx bridge + DrvClose tested together
with final header. Single decrement, failed join/retry, stale ticket, radiooff
failure retention passed. Repeatable extractor saved and ABI equivalent staged.
Evidence Temp/wr-iot-down-chain.c and bundle-down-chain. Actual family/PCI
retention/ndo_stop binding and MIPS compile still pending. No router changes.
## Checked virtual DOWN candidate added — 2026-10-22

Added explicit result chain from virtual down to checked physical close;
last-reference decrement happens once, pending retry permits count0 without
underflow. Persistent host fixture passed selective/last/failure/retry/stale
cases. Legacy dispatcher not redirected; generation/target and all-writer
ownership/PCI retention still pending. No production/device changes.
## Physical-close result bridge added and host-checked — 2026-10-22

Separate checked rt28xx bridge forwards failure and performs successful diag
cleanup once; fresh START clears notification latch. Persistent host fixture
passed invalid inputs/failure/success/repeat. Not redirected legacy callback;
new composition/target compile pending. Next checked final-reference dispatcher
and outer retention/recovery. No production/router change. See IoT contract.
## Repeatable final checked-close fixture saved and passed — 2026-10-22

Template/extractor now live in tools/iot; full final bundle generation and
strict extracted AP/PCI fixture passed all current failure/retry cases,
including final log-preserving radiooff ordering. ABI equivalent staged with
sanitizers, not run. Evidence Temp/iot-unified-radio-9h9m7gcq/bundle-close-final.
Next actual outer close-result/retention binding and prejoin safety. No router.
## PCI radio-off failure guarded in checked candidate — 2026-10-22

Radio-off failure now retains stage3 and skips downstream cleanup; repeated
call refuses rather than repeats partial hardware work. Extracted AP/PCI host
failure case passed. Final diagnostic-preserving ordering syntax checked but
needs regeneration. Evidence Temp/iot-unified-radio-9h9m7gcq/checked-close-radiooff.
Outer retained MMIO/adapter recovery still mandatory; no production/device change.
## AP/PCI close branches host-checked — 2026-10-22

AP/PCI injected fixture passed partial-failure retry and single cleanup; base
and AP/PCI now reject invalid shutdown stage instead of claiming completed.
Evidence Temp/wr-iot-physical-close[-ap-pci].c. IRQ active/radiooff failure,
MT_MAC, real headers and hardware still unverified. Next outer close-result
propagation and prejoin resource safety. No production/router changes.
## Checked physical-close base host retry passed — 2026-10-22

Generated-function base fixture confirmed failed join defers final cleanup,
retry skips preparation, completed call does not repeat cleanup. Fixed unused
net_dev for configurations without IRQ use; TRUE fix was fixture only.
Evidence Temp/wr-iot-physical-close.c. AP/PCI/real headers and outer free
retention unverified. Next extend generated fixture/config coverage and actual
close-result chain. No router change.
## Checked physical-close candidate generated — 2026-10-22

Added staged checked DrvClose variant preserving legacy function: pre-join
preparation once, resumable checked worker joins, post-join cleanup once.
Failure keeps stage/ticket for continuation. Exact generation/syntax passed;
full function target/host compile unverified. Prejoin worker safety, actual
caller/result propagation and outer PCI retention still mandatory. Evidence
Temp/iot-unified-radio-9h9m7gcq/checked-close-stage. No production/device change.
## Resumable management joins candidate passed host cases — 2026-10-22

Added per-adapter joined-worker bits and checked management helper requiring
owned CLOSE ticket. Command/WSC successful stages not repeated on retry; short
lock released across joins. Host partial-failure/retry/idempotence/invalid-ticket
cases passed, evidence Temp/wr-iot-mgmt-stop.c. Next staged physical-close
propagation and retained-resource path; legacy production close unchanged.
## WSC failed-join cleanup guarded — 2026-10-22

Found WscThreadExit BOOLEAN result ignored by MgmtTaskExit; original frees WSC
buffers/locks even after kill failure. Candidate now returns FALSE before
those frees on non-success, exact transform passed. Outer adapter retention,
result propagation and partial-close resume remain open. Evidence Temp/
iot-unified-radio-9h9m7gcq/task-wsc-retention. No WSC runtime/target proof.
## Shutdown bundle composition repaired and verified — 2026-10-22

Resolved actual rt_linux overlap by explicit netdev-create function transplant
preserving task retention; unknown changes remain rejected. Final bundle hash
checks and final extracted checked-stop host cases passed. Evidence Temp/
iot-unified-radio-9h9m7gcq/bundle-shutdown-merged. Next actual outer shutdown
result/resource-retention chain; target compile/runtime still pending.
No production/router changes. See IoT contract.
## Task-config controls passed; future CI collection staged — 2026-10-22

Six synthetic host controls passed; effective rt_linux macro probe added to
postbuild capacity step with artifact preservation. No workflow launched and
no actual MIPS macro evidence yet. Scope/evidence in IoT contract. Next checked
close-chain propagation and retained-resource integration. No router changes.
## rt_linux task-config probe prepared — 2026-10-22

Added standalone exact-TU Kbuild preprocessing probe with compiler/source checks,
macro report and hashes; fails closed on unavailable evidence. Syntax passed.
Not run on target toolchain or connected to CI yet. Next verify probe controls,
then gather actual rt_linux macros before checked close-chain integration.
No device/production changes. See IoT contract.
## Physical-close result chain and PM artifact scope — 2026-10-22

rt28xx_close returns zero after VOID DrvClose; dispatcher and VOID DOWN also
discard results. Failure retention must cross all layers plus PCI remove.
Direct PM callbacks bypass wrappers, but preserved #533/#535 effective kernel
configs disable CONFIG_PM (line498). Excluded only for those artifacts; recheck
new candidate config. Next implement checked close/result chain without relying
on ndo_stop return. Evidence in IoT contract; no production/device mutation.
## Checked command-thread stop candidate added — 2026-10-22

New checked helper preserves STOPED on failed join, reports failure explicitly,
and publishes UNKNOWN only after success; no queue lock across kill. Exact
helper host cases passed failure/retry/missing handle. Legacy VOID caller still
unchanged; next propagate checked result through close/remove, including WSC,
timers and retained resources. Evidence Temp/wr-iot-command-stop.c. No device.
## Task-retention transform and host cases passed — 2026-10-22

Exact-source reverse-diff passed. Extracted generated task-kill wrapper passed
failed-join retention, successful retry/free-once, missing-content refusal.
Evidence Temp/iot-unified-radio-9h9m7gcq/task-retention-check. Next checked
MgmtTaskExit failure/state propagation through outer close/remove. Not target
kernel join proof; no production/device change. See IoT contract.
## Failed-join task storage retention staged — 2026-10-22

Pinned rt_linux wrapper candidate frees task storage only on successful kill;
shared assembler includes it. Outer adapter/resource retention and shutdown
failure propagation remain mandatory before production. KTHREAD source default
is n; effective target TU config unverified. Python syntax/whitespace passed,
new transform and target execution pending. See IoT contract.
## Worker-join failure path confirmed — 2026-10-22

MgmtTaskExit logs failed task kill but returns VOID and continues. Legacy kill
may skip completion wait, and one wrapper frees task storage even on failure.
Cannot treat this return as quiescence. Next checked shutdown propagation and
resource retention through close/free; verify effective KTHREAD/wrapper config.
Exact source lines/order in IoT contract. No production/device changes.
## Physical-exit retirement intent staged and host-checked — 2026-10-22

Actual candidate RtmpPhyNetDevExit publishes retirement before child/main
unregister with short lock released before teardown. Exact generated function
passed strict host removal-order fixture (five injected paths). Fixture missing
stddef.h fixed locally; evidence Temp/iot-aux-ref-6h3p3gr8/adapter-retire.
Worker retirement/active-ticket completion and real stop binding remain open.
No target/runtime/production claim. See IoT contract.
## Removal admission latch modeled and checked — 2026-10-22

Added retiring latch that rejects new work/reset while allowing selective and
last-reference teardown. Strict host cases passed idempotence, late completion,
selective/final close and no reopen. Destructor itself does not join workers;
actual remove hook/producer quiescence and mandatory-stop binding still pending.
No production/router changes. See IoT contract.
## PCI remove lifetime boundary traced — 2026-10-22

Normal family hooks register ndo callbacks; exact-name search found no direct
calls. PCI removal unregisters families/main then destroys adapter and unmaps
MMIO, without continuous RTNL protection across destruction. Reset trylock is
not an adapter lifetime reference. Need removal intent plus producer/worker
retirement while permitting mandatory stops. Next trace RtmpRaDevCtrlExit and
timer/worker shutdown. Source evidence in IoT contract; no device changes.
## Unified IoT candidate assembled and checked — 2026-10-22

Full candidate assembly passed with counter, AP-client/WDS and monitor fixes
alongside prior queue/reset/beacon/MBSS work. Final manifest unique paths and
all hashes verified; six strict extracted main open/close host variants passed.
Evidence Temp/iot-unified-radio-9h9m7gcq/bundle-counter-aux.
Not full-driver/MIPS/runtime proof. Next actual family/stop ownership and adapter
lifetime integration. No production changes or publication. See IoT contract.
## Auxiliary and monitor failure-reference repairs verified — 2026-10-22

Monitor repair merged into existing adapter preparer without losing lock-free
insertion. Exact-source execution passed AP-client/WDS reverse-diff and monitor
composition checks. Evidence Temp/iot-aux-ref-6h3p3gr8; AUX fixture name failure
resolved by auxiliary destination. No target compile/runtime. Next actual
shared admission/mandatory stop integration. See IoT contract.
## AP-client/WDS failed-open reference repair staged — 2026-10-22

Verified hook-to-ndo registration and pre-DOWN mutations for auxiliary families.
Added pinned AP-client/WDS failed-UP module-ref balance preparer to unified
bundle. Optional monitor equivalent still needs merge with rt_profile adapter
edits. Python syntax/whitespace passed; generated transform and target/runtime
not checked. Next complete monitor repair and outer family admission; see contract.
## Counter transform verified on exact pinned source — 2026-10-22

Actual preparer execution passed guard ordering, exact reverse-diff identity
and unchanged source checks. Evidence Temp/iot-counter-stage-spp2g2oc.
Sandbox nested-directory WinError 5 resolved using approved local-only run.
No MIPS compile/runtime. Next shared dispatcher ownership and stop completion;
count guards alone remain insufficient. See IoT contract.
## Stop-reservation host verification — 2026-10-22

Strict GCC host fixture passed zero/selective/last/busy-last close cases,
including repeated closing epoch and retry after older owner retirement.
Python AST parse passed counter preparer and unified assembler. Source
transform execution, real MIPS driver and device remain unverified. Continue
actual shared dispatcher/family ownership and mandatory stop completion.
No production changes or Git publication. See IoT contract for exact scope.
## Counter bounds staged in unified candidate — 2026-10-22

Pinned dispatcher preparer now guards UP at UINT maximum and DOWN at zero;
unified assembler includes stage. Synchronization/stop result propagation remain
unproven, so this is not production acceptance. Whitespace check passed; no
bundle generation, tests, compilation or device operations. Continue shared
ownership and mandatory-stop lifetime/result work; see IoT contract.
## Shared count coverage includes AP-client/WDS/sniffer — 2026-10-22

Pinned call inventory found five families using the counter dispatcher:
main, MBSS, AP-client, WDS and optional sniffer. Existing main/MBSS candidate
is incomplete for count ownership. DOWN is VOID and discards dispatcher status;
a return-error/underflow guard alone cannot complete stop. Record source lines
and integration boundary in IoT contract. Next audit all family entry contexts
and pre-dispatch mutations before shared dispatcher/wrapper ownership changes.
Source review only; no tests, build, router changes or Git publication.
## IoT stop reservation candidate — 2026-10-22

Inventoried all direct mt76x3 VirtualIfCnt mutations in pinned cmm_cfg.c.
Added begin_stop: zero refused, last reference requests/reserves adapter CLOSE,
others reserve BSS_CLOSE. Caller must stabilize count/ownership and resolve
mandatory stop internally; no actual stop binding or target verification yet.
Next integrate shared count ownership across dispatcher callers before using
helper in production. No tests/build/device operations this turn.
## IoT last-secondary close source audit — 2026-10-22

Pinned MBSS close calls VIRTUAL_IF_DOWN, whose common/cmm_cfg.c dispatcher
unconditionally decrements VirtualIfCnt and physically closes the adapter at
zero. Secondary close cannot always use selective BSS_CLOSE: classify last
reference under common ownership before raw mutations. Audit count writers,
zero-count handling and lifetime before binding mandatory stop. Reset call
inventory also includes !DMA_RESET_SUPPORT fallback at cmm_mac_pci.c:2151.
Source audit only; no runtime/build/test. See IoT implementation contract.
Correction and next candidate: `ap/ap.c:967,1412` are `APStartUp` and `APStop`
respectively; PCI `APShutdown` calls `APStop`. `APStopBssOnly` at line 1580
has no caller in the pinned driver tree. The newer isolated bundle
`..\iot-unified-ap-state-lock-20261023` stages PCI `BcnRingLock` for the
start/stop IDLE writes and records a pinned blob and generated hash. Assembler
completed; generated source and manifest inspected. Callback drain, stale PID
and reset/deinit lifetime are open. No target build, production installation
or router action. Next prove producer retirement before binding the driver.
Newer isolated bundle: `..\iot-unified-beacon-recovery-stop-20261023`.
The existing radio-error stage already locks `APCheckBcnQHandler` final
hardware re-enable and IDLE publication. The newer bundle adds a STOP guard
under that existing lock; its generated diff against the radio-error stage
contains exactly one added condition, and its manifest has one final record
for `hw_ctrl/cmm_asic_mt.c`. Do not use the intermediate recovery-lock or
merged bundles: they attempted a second lock or overwrote previous changes.
Target compile, production installation and device acceptance remain false.
Latest isolated bundle: `..\iot-unified-beacon-debug-guard-v2-20261023`.
It adds bounds and full-width state validation to the DBG `BcnStateCtrl`
ioctl and moves its state decision under IRQ-safe `BcnRingLock`, logging only
after unlock. It retains the recovery STOP guard and radio-error stage, with
one final manifest record per modified file. The first debug-guard bundle is
superseded. Local saved MIPS GCC is an ELF binary; WSL list returned exit 1
without a distro, and Windows tar lacks its xz filter. No target compile,
production installation or router action. Next secure a real target compile
environment and resolve callback/PID/BSS lifetime before binding this driver.
Newest isolated bundle: `..\iot-unified-beacon-lock-forms-20261023`.
It rejects debug BSS state changes after STOP/HALT/NIC disappearance and
records SEM/IRQ forms of `BcnRingLock` in each partial-bundle C file. The
previous v2 debug bundle is superseded. Pinned lock macros differ under
MULTI_CORE_SUPPORT; effective WR1200JS flags and users outside the partial
bundle remain unverified. Manifest keeps lock semantics, target compile,
production installation and runtime acceptance false. Do not install yet.
## Заплановано після завершення прошивки — 2026-10-22

Власник погодив окремий завершальний етап: повне дерево джерел у нашому
репозиторії, усунення зовнішніх залежностей завантаження, впорядкування та
перевірена збірка на Ubuntu 24.04, включно з офлайн-перевіркою. Атрибуцію
й ліцензії зберегти. Деталі й критерії — PROJECT-DELIVERY-SCOPE.md,
розділ «Самодостатній репозиторій після завершення прошивки».
Поточний порядок виконання не змінено; міграцію й збірку не запускали.
## Repository organization, phase 1 — 2026-10-22

Compared nilabsent/padavan-ng root, README and Docker inputs with our pinned
source/overlay build. Added CONTRIBUTING.md, docs/README.md and
REPOSITORY-STRUCTURE.md, linked from root README. Existing Sol/DeepSeek roles,
IoT sequence, source archives and runtime/CI code preserved. Whitespace check
passed; no build or runtime tests run for this documentation change.
Full-source/offline/container migration remains separate and unverified.
New organization documents are local; no commit/push performed for this phase.
Resume the existing IoT lifecycle checkpoint after this organizational task.
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

## IoT next action — 2026-10-23

The pinned source confirms beacon TxS PID reservation precedes ring enqueue.
`RT28xx_UpdateBeaconToAsic` is `VOID`, and its big-endian branch changes the
descriptor in place before kickout. Do not infer PID ownership by reparsing
packet bytes after a failed enqueue. Carry a typed PID/valid reservation token
to the locked admission boundary, check ring space and DMA mapping before
publication, and roll back only a proven unsubmitted reservation. See the
contract's “Beacon PID ownership at the submit boundary” section. This is
source analysis only; existing candidate remains partial and uninstalled.

The separate `prepare-txs-status-candidate.py` now stages a generation-tagged
`CancelTxSReservation` API; the focused strict-GCC host fixture passed.
Its beacon caller is deliberately unbound. Next: propagate the generation
from TMAC construction to a checked, locked beacon enqueue path, then cancel
only if publication was definitively skipped. Target compile and router
verification remain open.

Subsequent partial stage: `MAC_TX_INFO` now exposes the allocated generation
without changing `write_tmac_info`'s signature. The unified bundle is
`..\iot-unified-txs-token-output-20261023`. Its manifest still says
`beacon_cancel_caller_bound=false`, `production_installed=false`,
`target_compiled=false`. Capture PID plus generation in the beacon wrapper
before endian conversion, then connect it only to a checked pre-publication
failure path.

Use only `..\iot-unified-beacon-generation-v2-20261023` for the beacon-builder
stage. The first non-v2 output contained an early legacy return and is
superseded. The MT_MAC builder returns the TxS generation; main beacon caller
still ignores it. Next capture PID plus generation before endian conversion
and pass a typed token to checked enqueue. No target compile/device proof.

The later isolated candidate `..\iot-unified-beacon-token-v3-20261023` does
pass the PID/generation token through `RT28xx_UpdateBeaconToAsic` in all ABI
variants. Use only this completed token bundle; v1/v2 token outputs failed
assembly. The submit functions currently discard the token. Next make the
locked ring and DMA enqueue return an explicit pre-publication result and
cancel only that exact failed reservation. Do not infer completion from the
existing unconditional kickout return. Firmware and router remain untouched.

Latest isolated candidate: `..\iot-unified-beacon-admission-v2-20261023`.
It stages locked final ring admission, PCI DMA-map failure before ring-cell
publication, and generation-matched cancellation on definite pre-submit
failure. The earlier non-v2 admission output has stale flags. Do not install
yet: cancellation refusal lacks quarantine, submit is still `VOID`, and no
target compile/IRQ/ring/device proof exists. Next propagate an explicit
submit result to the beacon caller and define safe BSS quarantine for
ambiguous or failed cancellation; preserve late-TxS uncertainty.

Current isolated bundle: `..\iot-unified-beacon-submit-offload-guard-20261023`.
The MT PCI submit path now returns 0 only after CPU-index publication, -1 on
known pre-publication rejection and -2 when reservation cancellation fails;
the beacon caller stops on nonzero. Other PCI/SDIO ABI variants were updated.
Pinned `config.mk` defaults MCU beacon offload to `n`; the candidate explicitly
fails compilation if PCI and MCU beacon offload are both enabled, because the
rollback would be unsafe. Target compile, effective board flags, quarantine,
late TxS and runtime proof remain pending. Do not install this partial tree.

Next: the existing post-build `tools/iot/check-capacity.py` now records the
effective beacon-offload and PCI macros from the MT7603 `rtmp_chip.o` Kbuild
command in its CI artifact. Pinned source/workflow do not explicitly enable
`HAS_BCN_EVENT_UPDATE_SUPPORT`, but the actual beacon-submit TU flags remain
unverified. Inspect `cmm_mac_pci.o` flags before deciding candidate viability.
No build, production install or router action occurred in this step.

The inspector now also reads `.cmm_mac_pci.o.cmd` and preprocesses the actual
beacon submit TU into a separate `beacon_submit_probe` result. A missing or
ambiguous Kbuild command stays unavailable. Local self-test could not create
its fixture directory (WinError 5 in both system and workspace-local temp),
so CI or an allowed host must execute it; syntax parsed in memory and
`git diff --check` passed. No target build or device action occurred.

The same targeted self-test subsequently passed (exit 0) under approved
elevated local execution; the compiler-timeout `UNAVAILABLE` line is its
injected failure case. Continue with actual `cmm_mac_pci.o` Kbuild evidence
and candidate target compilation. Host synthetic tests do not prove either.

Pinned source audit found `BcnTxSHandler` indexed `MBSSID` from `Priv` without
a bound and then set beacon idle. The completed isolated bundle
`..\iot-unified-beacon-txs-bound-v2-20261023` stages a pre-cast bound against
`BssidNum` and `MAX_MBSSID_NUM`; inspect its manifest/source. This does not
solve 8-bit PID reuse or stale TxS callback BSS lifetime. Next establish a
report/callback retirement rule and failed-cancel quarantine before installing
the driver. No target compile, production change or router action occurred.

Newer isolated bundle: `..\iot-unified-beacon-dma-bound-20261023`. Beacon
DMA completion now rejects unknown `own_mac` and out-of-range BSS indices
before `MBSSID` access while still reclaiming its ring cell. Its manifest
records both TxS and DMA index bounds true; target/production remain false.
Pinned source confirms DMA, beacon TxS and beacon deinit write state without
one shared lifetime lock. Type 1 TxS releases its type lock before callback,
and the report has PID but no reservation generation. Next establish a
shared beacon-state owner, retirement barrier and PID reuse/completion rule.
Do not install or claim IoT acceptance yet.

Teardown ordering matters: pinned `RTMPFreeAdapter` frees `BcnRingLock`
before main `wdev_bcn_buf_deinit`; secondary deinit is in `MBSS_Remove`.
Do not add a lock acquisition to deinit without first proving producer
quiescence and keeping the lock alive through both calls. An ignored failed
deinit remains unsafe. This was a source audit only, no build/device change.

Latest isolated bundle is `..\iot-unified-beacon-lock-order-20261023`:
main PCI beacon deinit is staged before `BcnRingLock` free; non-PCI cleanup
remains at its original site. Generated source/manifest were inspected.
This is only an ordering prerequisite. Lock lifetime, partially initialized
PCI probe failure, ignored deinit failure, IRQ/TxS quiescence and PID reuse
are unproved. Next trace producer shutdown and stage one shared beacon-state
owner before any production binding. No target compile or router action.
Normal PCI remove enters netdev exit before adapter free; `RTMPDrvClose`
disables Tx/Rx, releases IRQ and later exits the TxS table. This is not a
verified callback barrier or proof for a selective IoT BSS close. The PCI
probe error path calls `RTMPFreeAdapter` directly.

Latest isolated bundle: `..\iot-unified-beacon-state-lock-v2-20261023`.
It stages one PCI `BcnRingLock` for beacon DMA, TxS state/index update, and
deinit `IDLE -> STOP`, with the callback rejecting STOP. The first non-v2
bundle is superseded. Source review shows successful adapter allocation
initializes the lock before PCI probe publication, but this does not prove
callback quiescence, selective IoT BSS close, stale PID safety or failed
deinit handling. Manifest keeps target/production/runtime false. Next audit
all other beacon-state writers and close paths before installing anything.

## Latest IoT handoff — 2026-10-23

Use `..\iot-unified-beacon-lock-forms-20261023` as the latest isolated bundle.
It rejects debug state changes from STOP/HALT and inventories SEM/IRQ uses of
`BcnRingLock`; it is a partial driver tree. The CI capacity inspector now
reports the effective `MULTI_CORE_SUPPORT` macro for `cmm_mac_pci.o` only.
Targeted self-test passed; its injected timeout line is expected. No target
compile, production driver installation, firmware image or router action.
Next obtain actual flags for the other lock users, then prove callback/PID
retirement and BSS lifetime before binding any driver changes.

Deferred after firmware: the owner wants one self-contained repository with
the verified exact sources, dependencies and toolchain material. Follow the
separate stage in `docs/PROJECT-DELIVERY-SCOPE.md` after WR1200JS and Mi Mini
acceptance; do not start migration while the current IoT/firmware work is open.

Current IoT continuation: `tools/iot/check-capacity.py` now reports effective
`MULTI_CORE_SUPPORT` separately for each source unit acquiring `BcnRingLock`
from that unit's actual `.o.cmd`; absent evidence is null/unavailable. Targeted
synthetic self-test passed (injected timeout expected); no target build or
router change. Obtain real per-unit Kbuild evidence and settle callback/PID/BSS
lifetime before integrating the isolated driver candidate.

New TxS source finding: the pinned 8-bit PID slot is overwritten while
`TXS_USED`, and removal clears the slot without checking state/identity.
The report contains no reservation generation, so a software-only epoch
cannot prove stale-report safety after reuse. Exact lines and required
drain/identity gate are in `docs/IOT-WIFI-IMPLEMENTATION-CONTRACT.md`.
Do not bind the beacon candidate until this is resolved; no target or device
runtime check was performed.

TxS report delivery is via RX packets (`common/cmm_data.c`); the normal
close path's RX-drain call is commented out and does not prove selective
IoT close. Do not substitute beacon TX-ring cleanup for report retirement.

TxS additionally carries a 12-bit SN, but the current beacon reservation
does not match it and the callback only records it under `DBG`. Investigate
whether hardware SN can be bound safely to a submitted beacon; account for
wraparound. Do not treat this field alone as proof of stale-PID safety.

MT7603 follow-up: current beacon `write_tmac_info_beacon` sets `NSeq` and
`TxSPriv=apidx`, while `write_tmac_info` zeroes TMAC and does not explicitly
set `txd_3->sn`/`sn_vld` in this path. No expected SN is stored with PID.
Keep SN as an unproved hardware investigation, not an implemented fix.

Selective close finding: `MBSS_Close` only clears that BSS beacon request
and rebuilds all beacons; it does not retire outstanding TxS. The unused
`APStopBssOnly` disables shared interrupts/TBTT and is not an IoT-close
shortcut. Design the barrier on the actual MBSS path without disrupting
main/guest BSSs.

Latest isolated bundle is now
`..\iot-unified-beacon-selective-gates-20261023` (pinned `c25283e9`,
51 generated files with verified manifest hashes). It supersedes the
lock-forms bundle only as a candidate snapshot. New manifest gates for
SN matching and selective TxS retirement are explicitly false; PID reuse,
target compile, production install and runtime remain unproved. Do not
install it as a complete driver.

Newest isolated bundle: `..\iot-unified-beacon-cr-readback-20261023`.
The assembler adds a target-BSS LPON/ARB control-bit readback after
`mbss_cr_disable`; only generated `ap/ap_mbss.c` differs from the preceding
bundle and all 51 manifest hashes verified. It does not prove RF silence,
drain RX TxS, or bind the checked close into mandatory `ndo_stop`.
Target compile, production integration and router runtime remain open.

Current candidate: `..\iot-unified-beacon-cr-readback-v2-20261023` replaces
the earlier CR readback bundle. Its generator fixes a signed comparison in
the BSS capacity guard. The new host fixture extracted the generated
`mbss_cr_disable`, compiled with GCC `-Wall -Wextra -Werror`, and passed
normal and sticky-register cases plus peer-bit and invalid-index checks.
All 51 manifest hashes match; `git diff --check` passed. This proves only
host control-flow behavior. Keep target, runtime, RF, selective TxS and
production gates false. Next solve the BSS-scoped pending-report/callback
retirement barrier and verify actual target compile flags before binding.

Flush-command audit: pinned `mcu/andes_mt.c:1997-2024` sends
`EXT_CMD_FLUSH_FRAME_WCID` without response wait; its only caller is the
station-delete `FAST_DETECT_STA_OFF` path in `ap/ap.c:2427-2431`.
Beacon `TxSPriv` is a BSS index, not a proved BSS-specific WCID. Do not
substitute this command for the RX TxS retirement/callback barrier.

Latest isolated bundle: `..\iot-unified-beacon-txs-ledger-v5-20261023`.
The new per-BSS ledger bridges the window between PID-slot release and
beacon callback completion and fails closed on accounting mismatch.
Extracted allocation/removal/parser/query functions passed a strict GCC
host fixture including normal, missing and mismatched handler paths. All
51 bundle hashes verified; only TxS source/header differ from the previous
CR-readback bundle. Do not install yet: the query is a software snapshot,
the 8-bit PID late-report identity and bounded close wait are unproved,
and target compile, production binding and device acceptance are open.

Current candidate supersedes the ledger-only bundle:
`..\iot-unified-beacon-txs-close-gate-v2-20261023`. The checked BSS-close
fragment now gates HNAT deregistration and virtual-reference consumption on
the TxS ledger snapshot. Pending work retains stage 2 for retry; an error
enters the uncertain stage. Extracted MBSS close and TxS parser host
fixtures passed strict GCC checks, and all 51 manifest file hashes match.
The manifest deliberately keeps `beacon_txs_close_barrier_bound=false`:
there is no bounded drain/wakeup, producer exclusion or late-PID identity
proof. This partial driver is not installed or MIPS compiled. Next establish
a source-backed hardware/report completion rule and integrate a bounded,
fail-closed close path before any router acceptance.

Current successor bundle: `..\iot-unified-txs-claimed-slot-v2-20261023`.
`TXS_CLAIMED` prevents allocation of the same PID until the accepted parser
path exits. The extracted TxS parser/status and checked-close host fixtures
passed strict GCC checks; all 51 file hashes and preparer hashes matched.
This resolves only the in-callback reuse window. Delayed/duplicate reports
after later PID reuse, hardware drain/identity, bounded close, producer
exclusion, target compilation and device acceptance remain open. Keep the
manifest `txs_pid_reuse_safety_proved=false` and do not install the partial
driver into firmware yet.

Negative host witness, 2026-10-23: the updated extracted TxS fixture models
an old duplicate report after PID reuse for another BSS. The old report
consumes the new BSS's status slot and invokes its handler; the actual new
report is unmatched. GCC `-std=c11 -Wall -Wextra -Werror` compile/run passed
as an expected failure scenario. This does not assert that hardware emits
duplicates; it shows why the current candidate cannot be installed without
report identity or a proven producer/DMA/RX drain. The prior bundle was not
regenerated after the fixture edit. Next inspect the hardware report path and
establish a close-time rule that prevents old PID reports crossing reuse.

Receive-path audit, 2026-10-23: ring-0 `GetPacketFromRxRing` reaches TxS
parsing, and an Andes MCU queue has a second source call to the same parser.
The latter's effective use on WR1200JS remains unverified. The normal RX
tasklet has radio/reset/startup exits and bounded batches; MT `StopDmaRx`
returns unsupported. Next obtain effective target config and MCU routing,
then design a barrier covering every active report queue/callback before PID
reuse while preserving main/guest. Exact lines are in the IoT contract.

The capacity inspector now emits `txs_receive_units_probe` for the four
receiver/MCU translation units using each unit's real `.o.cmd`; a missing
command produces `unavailable`, never a guessed false macro. Synthetic
self-test passed including missing Andes command. Existing #535 artifacts
contain effective kernel config but no receiver `.o.cmd` files, so actual
per-unit macros and whether MCU messages carry beacon TxS remain open.
Collect the next exact CI report before narrowing the barrier design. No
firmware build or router mutation in this step.

## Відкладений етап джерел — 2026-10-23

Після приймання прошивки WR1200JS та наступного етапу Mi Mini виконати окремий
пункт `docs/PROJECT-DELIVERY-SCOPE.md` «самодостатній репозиторій після
прошивок»: впорядкувати дерево, зібрати точні джерела й залежності у власному
репозиторії, зберегти походження, ліцензії та контрольні суми і довести збірку
без зовнішніх завантажень. Посилання на авторів лишаються для атрибуції, а не
як обов'язкова залежність збірки. Зараз джерела не переносити; поточний етап
IoT і погоджений порядок доставки не змінюються.

IoT candidate update, 2026-10-23: Type 1 TxS used a registration pointer
after unlock even though removal can free it. The new isolated bundle
`..\iot-unified-txs-handler-snapshot-v2-20261023` snapshots its handler under
lock. Extracted strict GCC fixture with unlock-time registration poisoning
passed; 51 file and 75 preparer hashes matched. This is a narrow host proof.
The old-report/reused-PID negative witness still fires; callback quiescence,
MIPS build, production binding and router acceptance remain open. Continue
the source-backed report identity/drain design before installing the driver.

Additional teardown gate: `ExitTxSTypeTable` changes `TxSValid` before it
frees the TxS registration/status locks, but the parser reads that flag before
acquiring those locks. A previously admitted parser or snapshotted callback
can overlap exit. Prove a shared admission-stop and callback/RX/MCU completion
barrier before freeing the tables; whole-radio source order and the commented
RX-drain call are insufficient. Keep IoT-only close scoped to its BSS.

Correction from pinned source: normal `RTMPDrvClose` calls
`RtmpNetTaskExit` first, killing PCI RX tasklets; Andes MCU exit kills its
message tasklet before TxS table exit. These are real whole-radio quiescence
calls, pending effective compile-flag and producer review. Do not stop shared
RX/MCU tasklets merely to close IoT; a BSS-selective barrier is still needed.

Beacon TxS follow-up: `BcnTxSHandler` returns the BSS beacon state to idle;
normal beacon update and buffer deinit depend on that state. Do not disable
IoT beacon TxS as a shortcut. `APCheckBcnQHandler` is a recovery flush that
re-enables beacon start; its polls do not prove RX/MCU report drain or safe
PID reuse. Continue a BSS-specific producer-stop and report-retirement design.

TxS identity follow-up: `TXS_STRUC` has PID/SN but no `own_mac`/BSS field;
all beacon descriptors use WCID 0, so TxS `wlan_idx` is not a BSS identity.
The BSS in `TxSPriv` is looked up from the current software PID slot.
No expected SN is saved for matching, and software `Generation` is absent
from hardware reports. Prove SN assignment/matching or a real old-report
drain before permitting PID reuse across an IoT close.

Producer-gate review: checked close clears the IoT beacon request and
disables/readbacks target TBTT/queue bits before `MBSS_Close`; PCI submit
rechecks `BeaconTransmitRequired` under `BcnRingLock` before kickout. This
addresses new software submissions in the staged path, not pending reports.
The partial tree mixes SEM/BH and IRQ forms on `BcnRingLock`; the effective
`MULTI_CORE_SUPPORT` compile flags and complete lock ownership are not yet
proved. Do not promote atomicity or selective TxS retirement manifest gates.

TIM queue-producer checkpoint, 2026-10-23: pinned `ap/ap_nps.c` can submit
TIM packets to `Q_IDX_BCN` under its own `bTimSntReq` flag, which candidate
`mbss_cr_disable` does not clear. `ap_nps.o` is listed for AP builds, and
`TimEnable` is a development-only private command. The only source call to
`APMakeAllTimFrame` is inside `RTMPHandlePreTTTTInterrupt`; no caller of that
handler was found, so runtime activity is unproved. The pinned PCI
`WF_MAC_INT_4` branch only reads/masks interrupt status and never calls or
schedules PRETTTT, so no live software call chain was found in this source.
Confirm effective target dispatch and cover any active TIM producer before claiming beacon-queue
admission exclusion. TIM uses `PID_MGMT`; do not equate it with Type 1 beacon
TxS. No production/router change. Exact anchors in IoT contract.

Full pinned-source `BcnRingLock` inventory, 2026-10-23: seven live sites,
five SEM/BH and two IRQ-form, across `ap_nps`, `ap_cfg`, `cmm_mac_pci`,
`cmm_data_pci`. The mixed forms predate IoT; normalizing only the partial
candidate would leave original owners inconsistent. Exact site/function map
is in the IoT contract. Before changing locks, establish target per-unit
`MULTI_CORE_SUPPORT` and actual callback contexts; update every compiled
owner coherently. No target build or router mutation.

Next: extend `tools/iot/check-capacity.py` to inventory every live owner with
function/context and exact per-object `.o.cmd` macro evidence; add an in-memory
self-test for all seven pinned sites and missing object commands. Inspect the
full exact CI artifacts before selecting a single compatible lock discipline.
Do not edit driver lock forms until target macros and contexts are evidenced.

Stage-1 interim: `check-capacity.py` now emits line/form for each discovered
`BcnRingLock` acquisition, including unavailable `.o.cmd` units. Python
syntax and whitespace checks passed. Function/context mapping and exact
target macro evidence remain open; the six-stage report is at the end of
`PROJECT_STATUS.md`. No driver or router change.

Next interim stage-1 update: capacity report now includes a heuristic
function name or null per lock site. An in-memory missing-`.o.cmd` check
passed; a filesystem fixture could not write under Windows Temp. Interrupt
context and complete seven-site verification remain open.

Read-only pinned-source run of the inspector found all seven expected lock
sites and correct function names: ap_cfg 14608, ap_nps 77, cmm_data_pci
2681, cmm_mac_pci 1490/1890/2069/2710. Forms match the manual inventory.
Exact WR1200JS `.o.cmd` macro and execution-context evidence is still open.

Caller trace: `RTMPHandleBcnDmaDoneInterrupt` runs from
`bcn_dma_done_task`; `RT28xx_UpdateBeaconToAsic` is called by
`APUpdateBeaconFrame`; `PDMAResetAndRecovery` has debug-proc and watchdog
callers and invokes `RTMPRingCleanUp`. These are source paths, not complete
target runtime context proof. See latest PROJECT_STATUS.md entry.

Owner reporting rule, 2026-10-23: follow the six IoT stages listed near the
end of PROJECT_STATUS.md in order. After completing each stage, update its
status and evidence there, then tell the owner separately what that stage
accomplished. Label interim work as interim; do not report the next stage as
done until its acceptance evidence is present. Keep CI/image evidence separate
from on-router acceptance.

Stage-1 evidence update: `tools/iot/check-capacity-selftest.py` now has a
filesystem-free seven-site `BcnRingLock` inventory case. Its direct run,
Python syntax check, and whitespace check passed. The complete fixture suite
could not create a Windows temporary directory, including under the checkout
(`PermissionError`), so it has no passing result in this executor. Do not
claim exact target `MULTI_CORE_SUPPORT` or full callback-context proof; obtain
the real per-unit `.o.cmd` report from a future exact build before changing
production lock forms. No driver, image, or router mutation in this step.

Stage-1 guard correction: the seven reported locks are source-text sites,
not seven proven compiled paths. `Set_BcnStateCtrl_Proc` is exposed under
`DBG` in `ap_cfg.c:1295`; ring-free usage can depend on
`RESOURCE_PRE_ALLOC`. TIM update is reached through `APMakeAllTimFrame` and
the source `RTMPHandlePreTTTTInterrupt`, but target interrupt dispatch is not
established. Keep these conditions explicit when evaluating a unified lock
scheme. The #535 IoT capacity artifact predates this per-unit lock report and
contains no `beacon_lock_units_probe` or raw `.o.cmd` files.

Stage-1 inspector continuation: exact per-unit Kbuild commands are now also
used with GCC `-E -fdirectives-only`; source markers restrict matching to the
target file, then unique function/form pairs map surviving `BcnRingLock`
calls to `active_after_directives` (true/false). Missing commands,
preprocessor errors, or a missing target marker yield null/unavailable.
Targeted in-memory seven-site and marker tests, Python syntax, and whitespace
checks passed. A future exact CI run is needed for WR1200JS evidence; #535
predates this report. No production driver or device change.

The full IoT capacity self-test now passes when run with access to its Windows
Temp fixtures. It exercises actual host-GCC preprocessing of both `DBG`
branches for the synthetic `ap_cfg.c` lock site, plus an absent-command owner
that stays unknown. This supersedes the earlier sandbox Temp failure only for
the self-test; target MIPS per-unit flags and router behavior are still open.

The RESOURCE_PRE_ALLOC fixture exposed a GCC blank-line offset after `#endif`;
the earlier line-count mapping was replaced with unambiguous function/form
matching. Duplicate source owner pairs fail to unknown. The full host-GCC
self-test now passes both DBG and RESOURCE_PRE_ALLOC branches plus missing
`.o.cmd`; exact WR1200JS target macros still need a new CI artifact.

#535 local artifacts contain a kernel-effective config with
`CONFIG_MT7603E_WIFI_WORK_QUEUE` unset, but no MT7603 `.o.cmd`, `.ko`, or
per-unit lock report. Pinned `config.mk` adds RESOURCE_PRE_ALLOC to WFLAGS
and limits MULTI_CORE_SUPPORT to a separate platform branch; do not infer
actual per-TU flags solely from those source/config clues.

Further lock-context source trace: beacon submit is reachable via MT MAC
`mt_mac_int_3_tasklet` -> `RTMPHandlePreTBTTInterrupt` ->
`APUpdateAllBeaconFrame` -> `APUpdateBeaconFrame`, and also from multiple
configuration handlers in `ap_cfg.c`. Beacon DMA completion is reached from
`bcn_dma_done_tasklet`. RX-coherent handling contains ring-cleanup calls but
returns early for MT7603 before them; the reset paths remain relevant.
`WORKQUEUE_BH` may change the deferred-handler mechanism;
its target setting is unproved. See latest PROJECT_STATUS.md anchors. A final
lock discipline needs full target macro evidence and path review.

Recovery-path correction: `PDMAWatchDog` calls PDMA reset only without
`DMA_RESET_SUPPORT`; `PSEResetAndRecovery` also calls PDMA reset.
`PciMlmeRadioOn` returns via `MTPciMlmeRadioOn` on `HIF_MT` before its
legacy `RTMPRingCleanUp` calls. RX-coherent also returns before cleanup on
MT7603. Do not treat those legacy call sites as active WR1200JS evidence.

CI handoff, 2026-10-23: PR #2 remote head remains `675be3e`; successful
firmware #537/run `39838016889` has the old IoT capacity JSON only. Local
commit `0852a2e` contains the reviewed inspector and full passing self-test;
all other dirty files remain unstaged. GitHub SSH from Codex still resolves
to the deny-bin output `off\r\nexit /b 1\r\n`; no push or remote change was
attempted. Push this exact branch from an authorized Git executor after
reviewing local status, then use one resulting CI run's
`wr1200js-iot-radio-capacity` artifact for exact per-unit lock evidence.

Partial-candidate lock audit: the current
`../iot-unified-txs-handler-snapshot-v2-20261023/driver` has 19 source-text
`BcnRingLock` sites in eight units (10 SEM, 9 IRQ); pinned `ap_nps.c` is not
part of this partial tree. Machine-readable inventory with manifest hash is
`docs/evidence/WR1200JS-IOT-CANDIDATE-BEACON-LOCK-INVENTORY-2026-10-23.json`.
The inspector now recognizes `INT32` owners in TxS/beacon submit, and counts
duplicate function/form pairs: zero surviving sites means false for each,
all surviving means true, a partial count means null for each. Full host-GCC
self-test passed. No target compilation or production binding occurred.
The candidate inventory and parser correction are local commit `0f567ed`;
both it and `0852a2e` remain unpushed because the Codex SSH executor is
blocked. Preserve the dirty status/handoff and unrelated files.

CI transport update, 2026-10-23: the current Codex executor now uses system
OpenSSH, and GitHub authenticated as Andrzej1973. The two local commits
`0852a2e` and `0f567ed` were pushed by fast-forward to
`codex/wr1200js-service-webui`; `git ls-remote` confirmed `0f567ed`.
ABI run `40010694921` then failed in `check-capacity-selftest.py` because
the candidate `tools/iot/mt7603-main-observe.h` existed only as an untracked
local file and was absent from the CI checkout. The full local self-test
passed. Commit `9727933` adds only that candidate header, and a second
fast-forward push succeeded. ABI run `40010959283` and firmware build #539
(`40010959461`) started for `9727933`; inspect their terminal results and
the new radio-capacity artifact before claiming target macro evidence.
The header remains a probe candidate, not production driver integration.
All other pre-existing dirty files remain unstaged.

Evidence boundary for #539: the pushed workflow runs the existing radio
capacity probe and should report per-unit beacon lock owners from exact
Kbuild commands. The local uncommitted workflow additions
`--check-main-observer` and `check-task-config.py` are not in `9727933`;
do not credit #539 with compiling the candidate observer or checking the
separate rt_linux translation unit. On the latest read, ABI
`40010959283` had passed the formerly failing capacity self-test and was
running its host-kernel isolation step; #539 was pending behind #538.

ABI outcome: run `40010959283` completed successfully for `9727933`.
This resolves the missing-header CI fixture failure, but it does not prove
target MT7603 lock macros or physical IoT behavior. Firmware #538 was still
building the older `0f567ed` image and #539 remained pending on the last
check. Do not dispatch duplicate builds; inspect #539's exact artifact.

Correction: #538 at `0f567ed` already contains the per-unit beacon lock
inspector and does not enable the still-local `--check-main-observer` flag.
Its artifact may provide exact Kbuild lock-owner evidence before #539 if
the build succeeds. Inspect the first completed matching artifact from
#538 or #539; neither run proves observer compilation or the separate
rt_linux translation unit. #538 is currently running its firmware build
step on a GitHub-hosted runner, not waiting for a runner.

Build #539 (`40010959461`, `9727933`) completed successfully. Its
`wr1200js-iot-radio-capacity/mt76x3.json` confirms 16 source/config BSS,
but all four target beacon-lock units are unavailable because GCC
`-fdirectives-only` emitted byte `0xa1` outside valid UTF-8. The exact
artifact SHA256 and limits are in
`docs/evidence/WR1200JS-BUILD539-IOT-LOCK-PROBE.md`. Commit `160a1bc`
changes only directive-output decoding to UTF-8 `surrogateescape`, adds a
real-subprocess invalid-byte regression case, and records the evidence.
The full local capacity self-test, syntax check, and whitespace check passed;
`160a1bc` was pushed fast-forward. Inspect the next CI artifact before
selecting a production lock form. Keep the rest of the dirty tree unstaged.

ABI `40016197273` for `160a1bc` completed successfully. Firmware #540
(`40016197462`) was still installing build dependencies at the last check;
its corrected per-unit lock artifact is not available yet. ABI success
verifies the script fixture, not target lock safety or router runtime.

The #540 artifact is now available. Its four baseline MT7603 lock units
have effective `MULTI_CORE_SUPPORT=false`, all per-site directive states
available, and six of seven source sites surviving; the SEM
`RTMPFreeTxRxRingMemory` site is excluded. Exact rows, artifact SHA256,
and limits are in
`docs/evidence/WR1200JS-BUILD540-IOT-BEACON-LOCK-UNITS.md`.
This does not cover the 19-site partial IoT candidate, hard-IRQ reachability,
or production lock safety. The overall #540 workflow was still running
post-build checks when the artifact was read. Stage 1 stays open.

Final #540 status is success: select, WR1200JS build, downloads, and firmware
ZIP all passed. The partial candidate manifest still says
`complete_driver_tree=false`, `target_compiled=false`, and
`beacon_lock_forms_complete_tree=false`; it excludes unchanged `ap/ap_nps.c`.
Next assemble the pinned full MT7603 tree with candidate changes overlaid,
inspect all compiled `BcnRingLock` owners with exact Kbuild flags, and audit
callback contexts. This is stage 1 work; the baseline CI image is not an IoT
image. Keep all other dirty files intact.

Full-tree source inventory is now available at
`docs/evidence/WR1200JS-IOT-FULL-CANDIDATE-BEACON-LOCK-INVENTORY-2026-10-23.json`.
The exact pinned `c25283e` source archive was checked against all 31 source
Git blobs recorded by the candidate manifest (31/31 matched). A separate
scratch tree overlays 45 candidate driver files on 515 pinned MT7603 files.
The resulting source-text scan finds 20 lock sites in 9 files (11 SEM, 9 IRQ),
including the previously omitted `ap/ap_nps.c`. This does not prove that
all sites survive target preprocessing. Next capture candidate target Kbuild
commands for these nine units, then audit IRQ/callback contexts and lock
lifetime before any production integration. No router or production driver
change was made.

One caller-context path is now source-verified. The MT7603 hard IRQ handler
queues `bcn_dma_done_task`; the deferred tasklet/work callback alone calls
`RTMPHandleBcnDmaDoneInterrupt`, whose `BcnRingLock` site uses SEM form.
See `docs/evidence/WR1200JS-IOT-BEACON-DMA-CONTEXT-2026-10-23.md`.
Do not extrapolate this to other lock owners or target candidate macros.

The full-tree source audit is now reproducible with
`tools/iot/audit-full-beacon-locks.py`. Local output matched the prior 20-site
inventory across 9 units and verified all 31 pinned Git blobs. A deliberate
wrong blob was rejected. The current, still-uncommitted ABI workflow calls
the audit after producing `iot-radio-queue-bundle` and uploads its JSON with
`abi-results/`. Python syntax and `git diff --check` passed locally. CI has
not run this new call; target candidate Kbuild preprocessing/compilation and
the other callback contexts remain open. Preserve all unrelated dirty files.

Publication update: focused commit `51c0776` contains only the reusable
source audit and its ABI workflow call; fast-forward push to
`codex/wr1200js-service-webui` succeeded. Unrelated dirty files remain.
ABI run `40020039665` and firmware build #541 (`40020039819`) started for
that HEAD and were queued at first inspection. Check the ABI artifact
`abi-results/iot-full-beacon-locks.json` after completion. This still will
not prove target candidate Kbuild activity or physical IoT behavior.

Independent candidate call-path audit found a nested lock order for beacon
TxS reports: `GetPacketFromRxRing` holds `RxRingLock` while calling
`parse_rx_packet_type` -> `ParseTxSPacket` -> `BcnTxSHandler`, which takes
`BcnRingLock`. The Type 1 TxS registry lock is released before the handler,
but the RX ring lock is not. Evidence is appended to
`docs/evidence/WR1200JS-IOT-BEACON-DMA-CONTEXT-2026-10-23.md`.
Check the reverse `BcnRingLock` -> `RxRingLock` order and exact target
preprocessor branches before accepting candidate lock safety. No deadlock
or safety conclusion yet.

ABI run `40020039665` succeeded, but its downloaded lock JSON covers only
10 overlay files, 6 source blobs and 7 lock sites in 4 units. The local full
candidate has 45 overlay files, 31 blobs and 20 sites in 9 units. The green
run validates the narrower committed generator, not the full local candidate.
Artifact is outside the repository at `../iot-abi-541-artifact/`.
In the inspected cleanup/reset paths, `QID_RX` and `QID_BCN` lock sections
are separate, and PDMA reset releases `BcnRingLock` before `QID_RX` cleanup.
This does not establish global absence of lock inversion. Preserve dirty
files; next reproduce the full candidate in CI and capture target Kbuild
commands for all nine lock units before integrating production code.

Confirmed CI/local scope gap: current `prepare-radio-queue-candidate.py`
adds 691 and removes 9 lines versus HEAD. Its manifest has 75 preparer
inputs; 29 are untracked and four tracked inputs are locally modified.
The generator now includes its own SHA-256 in `preparer_inputs`. Fresh local
preparation at `../iot-full-dependency-closure-20261023/` completed, and the
independent audit again verified 31 blobs, 45 driver-overlay files and
20 lock sites in 9 units. This is not target compilation or CI validation.
A coherent dependency closure must be reviewed and published together before
claiming full-candidate CI coverage. Preserve every dirty file.

Isolated closure proof: `git archive HEAD tools/iot` plus exactly 34 local
candidate inputs reproduced a byte-identical manifest and all 51 generated
files. The independent audit again found 20 sites in 9 units. Those 34
inputs are now in local commit `b44ab21`, not pushed while #541 is running.
All other dirty files are preserved. This is experimental candidate source,
not an installed driver or device acceptance.

Local commit `569bccb` adds a fail-closed ABI gate for the reviewed full
candidate shape (515 source files, 45 overlays, 31 blobs, 9 lock units,
20 sites, 11 SEM, 9 IRQ). It accepts the isolated full candidate and rejects
the narrower #541 ABI artifact with exit 2 and no evidence JSON. Commits
`b44ab21` and `569bccb` are local only while firmware #541 is running.
Preserve all remaining dirty files; publish the two commits together once
queue discipline allows, then inspect the new ABI artifact rather than only
the run status.

Inventory precision: 45 overlaid source-directory paths comprise 41
`purpose=driver` records and four helper `include` fragments marked
`purpose=fixture`; six further fixtures are outside those directories.
Local commit `ab19045` makes the lock audit verify SHA-256 for all 51
candidate files. The intact isolated candidate passed; a copy with a
modified `include/rtmp.h` was rejected without output JSON. Commit remains
local. No target compile or runtime conclusion follows from this check.

Publication: previous firmware #541 (run `40020039819`, SHA `51c0776`)
completed successfully; it does not contain the experimental IoT candidate.
After it finished, commits `b44ab21`, `569bccb`, `ab19045` were pushed
fast-forward to PR #2, remote HEAD `ab19045`. New ABI run `40021678711`
and firmware build #542 (`40021678720`) started. Download and inspect the
new ABI lock JSON and downstream steps; expected coverage is 45 overlay
source-directory paths, 31 pinned source blobs and 20 lock sites. Do not
claim device IoT runtime from CI. All unrelated dirty files remain.

Downloaded successful #541's `wr1200js-iot-radio-capacity/mt76x3.json` to
`../iot-capacity-541/`. Baseline image has recorded Kbuild commands and
complete directive probes for four beacon-lock units; all report
`MULTI_CORE_SUPPORT=false`. The four TxS receive units report effective
MT_MAC/PCI/Andes support. This is baseline-only: the nine-unit experimental
candidate was not installed in #541. See the beacon DMA evidence document.

ABI run `40021678711` for `ab19045` completed successfully. Downloaded
artifact `../iot-abi-542-artifact/` reports 515 pinned source files, 45
overlay paths, 31 verified blobs, and 20 lock sites in 9 units (11 SEM,
9 IRQ). A local re-audit of the downloaded candidate produced semantically
identical JSON. Manifest remains `target_compiled=false` and
`production_installed=false`; next gather candidate-specific Kbuild commands
and prove compilation/lock context before production binding. Firmware #542
is a separate baseline image run; do not infer router behavior.

Firmware #542 (run `40021678720`, head `ab19045`) completed successfully.
Downloaded `board-build-status-wr1200js` reports success, and its MT7603
capacity JSON is semantically identical to #541: four baseline lock units
with Kbuild probes and `MULTI_CORE_SUPPORT=false`. Candidate source tooling
is in the repository, but the firmware workflow does not install it into
the production module. #542 is not candidate target-compile evidence.

2026-10-24 continuation: run #544 (`40046513315`, head `5a09fc7`)
failed only at isolated merged IoT MT7603 target compilation. The artifact
`../iot-merged-probe-544/build.log` shows the first compiler error:
`ap/ap_cfg.c:14639-14642 -Werror=misleading-indentation` in the candidate
debug setter. Fixed the generator's inherited return indentation; regenerated
and merged locally with only `ap/ap_cfg.c` changed among 45 output paths.
Commit `236dedb` also adds per-unit beacon-lock Kbuild evidence after the
isolated compile and was pushed to PR #2. Automatic firmware #545
(`40047701330`) and ABI (`40047701287`) were queued at last check. Do not
dispatch a duplicate manual candidate run while they occupy the branch;
after they finish, run one optional candidate check for `236dedb`, inspect
its artifact, and fix the next exact compiler error if any. Other dirty files
remain untouched. No router, production-driver, or firmware installation.

Update: #545 (`40047701330`) and ABI (`40047701287`) completed successfully.
The queue was empty, so one manual candidate run `40048878570` was dispatched
for `236dedb` with `run_candidate_checks=true`. It was queued at last read;
inspect this run and its `iot-merged-driver-probe` artifact before making a
target-compile claim. The local corrected candidate still has 20 beacon-lock
sites in nine units with 31 pinned blobs. No duplicate run was dispatched.

Update: that manual run `40048878570` failed in the isolated IoT target
compile at `common/cmm_mac_pci.c:2740`: vendor `GET_BCNRING_FREENO` ends in
`;` and cannot be used in a conditional expression. Its log is at
`../iot-merged-probe-546/build.log`. Replaced this in the candidate generator
with an equivalent ring-index comparison under `BcnRingLock`; all 400 index
pairs for the 20-slot ring were checked locally, and the new 45-file merge
changed only `common/cmm_mac_pci.c`. Commit `22df59a` was pushed to PR #2.
Automatic baseline firmware `40049984099` and ABI `40049984130` were queued
for this SHA. Do not duplicate them. After they finish, run one manual
`run_candidate_checks=true` for `22df59a` and inspect the isolated artifact;
target compile and safe lock semantics are still unproved. Preserve other
dirty files; no router or production-driver change was made.

ABI `40049984130` completed successfully. Downloaded its artifact to
`../iot-abi-548-artifact/`: 45 overlay paths, 31 verified pinned blobs,
20 lock sites in 9 files (11 SEM, 9 IRQ). A local re-audit of the downloaded
candidate matched its JSON exactly. This remains source evidence only;
`target_compiled=false` and `production_installed=false`. Automatic firmware
run `40049984099` was still building at last check. Wait for its terminal
result before one optional isolated candidate run for `22df59a`.

That baseline firmware run completed successfully. With the queue empty,
one manual candidate run `40051068385` was dispatched on `22df59a` with
`run_candidate_checks=true`; it was in progress at last read. Inspect its
`iot-merged-driver-probe` artifact for the exact target compiler result.
Do not dispatch another copy of this run.

Run `40051068385` completed successfully. Downloaded
`../iot-merged-probe-550/`: isolated `vmlinux modules` generated a
5,106,508-byte ELF32 MIPS `mt76x3_ap.ko`. All 45 merged-source hashes match
the local candidate; effective config was unchanged by the compile. Its
`merged-capacity.json` has nine complete Kbuild units, 20 source sites,
19 active sites (10 SEM, 9 IRQ), and `MULTI_CORE_SUPPORT=false` in every
unit. The one inactive site is the `RTMPFreeTxRxRingMemory` SEM acquire.
Both lock forms therefore use the BH wrapper in this target build, but
callback-context safety, selective BSS TxS retirement, production binding
and router behavior remain unproved. See the overlay-conflict evidence doc.
Next: inspect callback contexts and all remaining lifetime/rollback gates
before considering production integration. No router state was changed.

Follow-up: source-traced beacon DMA tasklet and RX/TxS callback paths; they
reach SEM and IRQ forms respectively, both mapped to `spin_lock_bh` in the
current target configuration. This does not close other callback and lifetime
risks. Commit `5da2e60` adds a fail-closed optional CI gate for exactly
19 active lock sites (10 SEM, 9 IRQ) across 9 Kbuild units and rejects
`MULTI_CORE_SUPPORT` drift while the forms remain mixed. Local shell syntax,
the gate against run #550 JSON, and diff checks passed. Pushed to PR #2;
automatic firmware `40053080982` and ABI `40053080975` started. After the
queue empties, run one optional candidate check for this SHA to exercise the
new gate. Preserve all other dirty files and device state.

ABI `40053080975` succeeded. Baseline firmware `40053080982` was still
building at last check, so no manual candidate run for `5da2e60` was
dispatched. Once that run is terminal and the branch queue is empty,
dispatch exactly one `run_candidate_checks=true` run and inspect its
`iot-merged-driver-probe` artifact. A source trace also excluded one
reverse-lock concern: `RTMPHandleRxCoherentInterrupt` returns early on
MT7603 before ring cleanup. Other reverse paths remain to be audited.

Update: automatic firmware `40053080982` succeeded. With the queue empty,
one optional candidate run `40054121188` was dispatched for `5da2e60`;
it was building the firmware at last check. Inspect that exact run and its
`iot-merged-driver-probe` artifact; do not dispatch a duplicate. The linked
module from prior successful candidate run `40051068385` contains a direct
`RTMPHandlePreTTTTInterrupt` → `APMakeAllTimFrame` MIPS call relocation.
The TIM chain can submit to the shared beacon ring. No direct caller of
the interrupt handler was found; its sole `R_MIPS_32` reference is in
diagnostic `.rel.pdr`, and the `WF_MAC_INT_4` branch only reads/masks
`HWISR4`/`HWIER4`. This excludes direct dispatch by that reviewed branch
in the isolated module, not all indirect paths or a later production build.
Retain `beacon_ring_admission_atomic=false` for the other active producer
and teardown gaps. The narrower reference-tree
search that missed this handler was corrected in the evidence document.
Preserve all other dirty files; production IoT and device were not changed.

Update: optional run `40054121188` finished `success`. Downloaded its
`iot-merged-driver-probe` artifact to `../iot-merged-probe-550-guard/`.
The new guard executed against nine complete Kbuild units, 20 source lock
sites and 19 active sites (10 SEM, 9 IRQ), with `MULTI_CORE_SUPPORT=false`
in every unit. The target compiled a 5,106,508-byte ELF32 MIPS
`mt76x3_ap.ko`. The merged source manifest and capacity report SHA-256
match the preceding successful candidate run; one pre-existing `modpost`
section mismatch warning remains. This is isolated candidate/guard proof,
not production IoT or device acceptance. Next: resolve selective BSS
TxS/DMA retirement, lifecycle and producer admission before production
integration. Do not duplicate the completed run or touch the router.

New source audit: `docs/evidence/WR1200JS-IOT-TXS-RETIREMENT-OPTIONS-2026-10-24.md`.
The candidate report has a 12-bit SN, but its beacon descriptor does not
set or retain an expected SN. Upstream Linux MT7603 clears `SN_VALID` for
ordinary beacons; its `HZ/4` post-DMA status timeout is a recovery policy,
not a vendor-hardware drain guarantee. Do not turn a timeout or an SN field
alone into `selective_bss_txs_retirement_proved=true`. Next: prove a usable
report identity on the target, or a producer/DMA/TxS/RX drain barrier before
PID/BSS reuse. No production or router state change in this audit.

Scoped cleanup audit: `RtmpNetTaskExit` kills shared RX/beacon-DMA tasklets
at adapter teardown; `RTMPRingCleanUp(QID_BCN/QID_RX)` resets whole rings.
Neither can serve as a selective IoT close barrier without affecting main
and guest BSS. Beacon DMA completion reads `own_mac`, so per-BSS DMA
accounting may be staged there, but TxS/RX retirement remains separate.
See the TxS retirement evidence file. No driver edit in this step.

2026-10-24 IoT continuation: `tools/iot/prepare-radio-queue-candidate.py`
now invalidates `bss_idx` for every beacon DMA descriptor before decoding
`own_mac`; previously an unknown owner could inherit the prior cell's BSS.
Pinned-source candidate assembly and source inspection passed. See
`docs/evidence/WR1200JS-IOT-BEACON-DMA-OWNER-2026-10-24.md`. This is an
isolated candidate only; target compile of this edit, selective TxS drain,
production integration and router verification remain open. Preserve all
other dirty and untracked files; current branch `codex/wr1200js-service-webui`,
HEAD `5c17e5a`, Sol remains the sole writer. The isolated owner-reset fix and
its evidence were pushed to PR #2. CI run #551 (firmware) and the matching
Band Steering ABI run started for that commit; neither result had completed
when this handoff line was updated. Do not dispatch a duplicate build.

Follow-up source map: beacon DMA ownership is published via
`RtmpPCIMgmtKickOut` under `BcnRingLock` on the reviewed call path, but cells
also exit through adapter reset/free and `RTMPRingCleanUp(QID_BCN)`.
Per-BSS DMA accounting must cover all exits and cannot use a global cleanup
for selective IoT close. See the TxS retirement evidence update. The ordinary
PR run #551 has `run_candidate_checks=false`; it is not an isolated candidate
target compile. Wait for its terminal result before considering a separate
candidate-check dispatch on the same revision.

2026-10-24 next IoT candidate: a fail-closed per-BSS beacon DMA ring
snapshot is staged and called by checked MBSS close before the TxS snapshot.
It scans current ring cells instead of keeping a counter across global
cleanup paths. Host C and close fixtures pass; see
`docs/evidence/WR1200JS-IOT-BEACON-DMA-SNAPSHOT-2026-10-24.md`.
No target compile or production/router acceptance for this revision.
`beacon_ring_admission_atomic` and selective TxS retirement remain false.
Current branch `codex/wr1200js-service-webui`, HEAD `5c17e5a`;
new snapshot edits are uncommitted. Sol remains the sole writer.

CI update: firmware #551 and matching ABI for `5c17e5a` finished `success`.
They predate the DMA snapshot edits and do not prove their target build.

Publication update: `7df3e9c` contains only the isolated DMA snapshot,
checked-close binding, host fixture and evidence; it was pushed to PR #2.
Firmware #552 (`40066799333`) and ABI `40066799319` were queued at last
check. Do not dispatch a duplicate while either relevant run is active.
Other local changes remain untouched. Current HEAD `7df3e9c`.

2026-10-24: firmware #552 passed. ABI run `40066799319` failed at the
beacon-lock inventory shape guard because the new DMA snapshot added one SEM
site. `tools/iot/audit-full-beacon-locks.py` now expects 21 sites (12 SEM,
9 IRQ); local replay against pinned source and assembled candidate passed.
See `docs/evidence/WR1200JS-IOT-ABI-552-BEACON-LOCK-GATE-2026-10-24.md`.
Only this gate and its evidence should be included in any follow-up commit;
preserve unrelated dirty files. Sol remains sole writer. Candidate MIPS
compile, TxS retirement and production/device acceptance remain open.
The gate fix and evidence were pushed as `06b2620` to PR #2. Check its
new CI run before claiming ABI recovery; do not dispatch a duplicate build.
Matching runs are firmware #553 (`40067873712`) and ABI `40067873711`;
both were in progress at the last check.
Pinned `common/cmm_data.c` receives multiple TxS reports in one RX packet
and calls the parser with PID but no reservation generation. The local TxS
retirement evidence now records this receive-batch gap. Keep selective
retirement unproved until exact report identity or a real drain barrier is
established; do not treat the DMA snapshot as that barrier.
ABI `40067873711` on `06b2620` passed, including the repaired IoT mailbox
step. Firmware #553 was still running when checked. Candidate MIPS compile
with `run_candidate_checks=true` remains pending after that run is terminal.
Additional isolated candidate work: TIM frames also publish to `Q_IDX_BCN`.
`prepare-radio-queue-candidate.py` now guards secondary TIM submission with
the close request under `BcnRingLock`; host race fixture and full source
inventory pass. See `docs/evidence/WR1200JS-IOT-TIM-ADMISSION-2026-10-24.md`.
Production and router are untouched. `beacon_ring_admission_atomic` remains
false pending all producer/lifetime review and target compile.
Local commit `1ae2408` contains the TIM guard, its host fixture, inventory
shape update and evidence. It has not been pushed while firmware #553 is
still running on the previous remote head. Preserve other dirty files.
Publication update: firmware #553 and ABI `40067873711` both passed on
`06b2620`, then `1ae2408` was pushed to PR #2. Check the new run IDs and
results. The ordinary PR build will still skip isolated candidate MIPS
compilation unless dispatched with `run_candidate_checks=true` after its
same-ref run is terminal.
New runs for `1ae2408`: firmware #554 (`40068837518`) and ABI
`40068837433`, both in progress at last check. Do not duplicate them.
Both runs passed. One optional candidate run `40071175138` was dispatched
for the same SHA with `boards=wr1200js` and `run_candidate_checks=true`.
Inspect its `Compile isolated merged IoT MT7603 candidate` step and artifact
before claiming MIPS candidate compilation; it was in progress at last check.
Do not dispatch another run for this SHA.

Run `40071175138` is terminal `failure`: optional candidate assembly stopped
before MIPS compilation because its exact-shape gate still expected 45/31,
while the reviewed TIM `ap/ap_nps.c` overlay makes 46/32. The assembler gate
was updated and local full assembly passed with five merges. See
`docs/evidence/WR1200JS-IOT-555-ASSEMBLY-GATE-2026-10-24.md`. After the
targeted fix is published, dispatch one optional compile for its new SHA;
do not claim target compilation from the local assembly.
Targeted fix and evidence were pushed as `1a15f6e` to PR #2. PR firmware
`40073309681` and ABI `40073309606` were queued at first check. Wait for
their terminal results; then dispatch exactly one optional candidate compile
for this SHA when no same-ref build is active. Preserve all unrelated dirty
files.
Both PR runs passed. Optional candidate build `40074321999` was dispatched
once for `1a15f6e` with `boards=wr1200js` and `run_candidate_checks=true`.
Inspect its isolated MT7603 candidate compile step and artifact. Do not
dispatch a duplicate for this SHA.

Separate future kernel work: the WR1200JS Linux 4.4.198 → 4.4.302 risk
analysis, staged Git/build plan and device acceptance checklist are in
`docs/KERNEL-4.4.302-MIGRATION-PLAN.md` (local commit `5d41827`). This is
after priority firmware/IoT acceptance and does not reorder current work.
The document commit has not been pushed while optional run `40074321999`
is active. Do not interpret the plan as a completed migration.

Optional IoT run `40074321999` is terminal failure *after* candidate MIPS
module link. Its merged lock gate had stale 20/19/10/9 expectations; CI
capacity artifact proves 21/20/11/9, including new active `ap/ap_nps.c` SEM
site. The workflow gate has been updated as a separately staged hunk;
unrelated earlier workflow edits remain unstaged. See
`docs/evidence/WR1200JS-IOT-556-MIPS-LOCK-GATE-2026-10-24.md`.
After publishing the narrow fix, wait for PR runs and dispatch at most one
optional candidate build for the new SHA to verify the downstream ELF/copy
and hash checks. Production and router runtime remain unverified.
Gate fix/evidence `6eec863` and migration-plan commit `5d41827` were pushed
together to PR #2. Firmware `40075915187` and ABI `40075915089` started for
head `6eec863`; both were in progress at first check. Inspect their results
before one optional candidate run on this SHA. Preserve all unrelated dirty
files, including the unstaged workflow hunk.

User confirmed Stage 2 Zapret scope on 2026-10-24: after baseline WR1200JS
acceptance, enable both Zapret and Zapret2 selectors and port their real
dependencies, service/configuration, strategy data and WebUI into the image.
Verify image contents and flash size. The decision is recorded in
`docs/PROJECT-DELIVERY-SCOPE.md`; keep both selectors disabled in Stage 1.

PR firmware run `40075915187` and ABI run `40075915089` succeeded on
`6eec863`. Exactly one optional IoT candidate run, `40077253251`, was
dispatched after those jobs completed and no active duplicate remained. Its
WR1200JS job was still running at this checkpoint. Inspect its exact
`Compile isolated merged IoT MT7603 candidate` result and downstream
ELF/copy/hash gates; do not dispatch a duplicate. The owner placed the
possible 4.4.302 migration as the final project stage, immediately after
Mi Mini and all other agreed work. If separately approved, it covers every
router added to the project by then, with per-router analysis, build and
device acceptance. Kernel remains 4.4.198 until that stage. The scope and
initial WR1200JS analysis are local documentation changes; preserve them.

Run `40077253251` completed successfully. Its isolated candidate step and
artifact confirm MIPS `.ko` link and passed merged-lock, source-copy/hash,
ELF and unchanged-config gates. See
`docs/evidence/WR1200JS-IOT-557-OPTIONAL-MIPS-CANDIDATE-2026-10-24.md`.
Proceed with remaining production safety work (atomic ring admission,
selective TxS retirement and lifecycle), not another duplicate build.

Source audit after the green optional build found that
`mbss-open-admission.inc` does not revalidate actual main-radio state between
its transition ticket and `wr_iot_mbss_open_raw()`. The existing observer
must run under a pinned exclusive ticket outside the short transition lock,
then ticket/epoch/close/reset intent must be checked again before raw mutation.
All external mutators must share that owner; the wrapper alone is insufficient.
See `docs/evidence/WR1200JS-IOT-558-MBSS-OPEN-REVALIDATION-GAP-2026-10-24.md`.

The candidate now has `wr_iot_radio_abort_bss_open_unmutated()` and the MBSS
wrapper uses it instead of writing `busy=0` when interface reservation fails.
The existing local, untracked `check-radio-transition.c` was extended for
stale ticket, reset, main-down and close cases; GCC `-Wall -Wextra -Werror`
host test passed. Preserve that untracked file. This does not yet bind the
actual main-radio observer before raw open or every close/reset writer.

Follow-up candidate code now calls the existing MT7603 observer for the IoT
slot after ticket reservation, outside the short transition lock, and checks
serial/epoch/readiness/close/reset intent again under that lock before raw
open. Failed observation aborts only an unmutated ticket. Guest BSS bypasses
the IoT observer. New injected-IO host test passed with `-Werror`; the
existing generated MBSS admission fixture has been extended but awaits the
next full candidate/CI run. This is not yet all-mutator atomicity, target
compile proof for this revision, or device runtime acceptance.

Commit `3095603` (candidate revalidation and tests) plus documentation
commits `a332f11` and `7152d25` were pushed together to PR #2. Firmware
run `40079234854` and ABI run `40079234798` started for this head and were
in progress at first check. Inspect both results; only after completion and
no active duplicate, consider one optional candidate build for MIPS proof.
Keep the production/device boundary explicit.

Local follow-up `010fc2c` adds a passing host case for interface-ref
reservation refusal after the BSS-open ticket; it has not been pushed.
Latest observed CI state: ABI `40079234798` in host-kernel IoT isolation,
firmware `40079234854` in WR1200JS build, both still running. Reuse these
handles, do not dispatch duplicates or infer a terminal result from elapsed
time. Push the small test with the next coherent batch after reviewing CI.

Both PR runs for remote `3095603` completed successfully: ABI `40079234798`
and firmware `40079234854`. One optional candidate run `40080616642` was
then dispatched on that same remote head with `run_candidate_checks=true`.
Inspect its exact MIPS module build and uploaded diagnostic artifact. The
local `010fc2c` only extends a host test and is not in the remote run.

Optional `40080616642` completed successfully on remote `3095603`. Its
downloaded MIPS module/ELF and merged capacity artifact were inspected;
details are in
`docs/evidence/WR1200JS-IOT-559-MBSS-REVALIDATION-MIPS-2026-10-24.md`.
The next safety work is all-mutator transition ownership plus beacon DMA
admission and TxS retirement; do not infer production IoT support from the
green isolated compile. Local test-only `010fc2c` remains unpublished.

The next concrete owner gap is main close: the candidate inserted
`wr_iot_radio_main_down()` before main-close mutations but did not admit
main close under the same exclusive ticket or defer mutation until an active
BSS-open ticket retires. See
`docs/evidence/WR1200JS-IOT-560-MAIN-CLOSE-OWNER-GAP-2026-10-24.md`.
Do not claim atomic BSS-open versus main-close until this is fixed and
interleavings are exercised. No production/device state was changed.

Correction to the main-close finding: pinned `ap_mbss_inf.c:79-80` binds
MBSS open/close hooks and `rt_linux.c:1676-1677` maps them to
`ndo_open/ndo_stop`; main hooks use the same mapping. RTNL serializes normal
netdevice callbacks, so a race between those normal ndo paths was asserted
too broadly. Evidence 560 is corrected. Next inventory direct calls and
PM/watchdog/error/reset paths outside RTNL before inserting any wait or
close-owner mutation.

Pinned MT7603 source was sparsely fetched outside the repo and searched.
No direct C calls to main/MBSS open/close beyond their ndo registration
were found; reset has private/debug, PCI and watchdog entry paths outside
RTNL. Candidate reset request/trylock plus periodic retry exists but does
not prove bounded completion or all lower-level reset coverage. See
`docs/evidence/WR1200JS-IOT-561-RTNL-RESET-ENTRY-INVENTORY-2026-10-24.md`.


### IoT MBSS-open intent interleaving — 2026-10-24

Current checkout HEAD `f0b995de9ec8db6a8d2e0aa985426f86a145e6d9`, branch
`codex/wr1200js-service-webui`; one writer remains Sol. Local uncommitted changes
include the MBSS revalidation fixtures plus prior workspace work. Standalone
`check-mbss-open-revalidation.c` passed with GCC `-std=c11 -Wall -Wextra
-Werror`. The generated admission fixture also passed after assembling the
candidate from exact Git blobs at pinned source
`c25283e915a2a00a763774dd255b14aff997285e`; generated test confirms reset/close
inside raw `VIRTUAL_IF_UP` keeps the interface reference owned and readiness
false. Python AST parse and targeted `git diff --check` passed. Initial attempt
using a Windows checkout failed the pinned Git-blob hash because CRLF conversion
changed bytes; this was corrected by hydrating source blobs with `git cat-file`
outside the repository. No firmware build, CI dispatch, router action, commit, or
push was performed. Next inspect bounded/liveness guarantees for reset drain after
the admitted BSS-open owner retires; existing periodic retry is not yet proven
to survive worker/timer teardown. Preserve all unrelated modified/untracked files.


### IoT deferred reset retry liveness — 2026-10-24

Source evidence `docs/evidence/WR1200JS-IOT-562-RESET-RETRY-WORKER-LIVENESS-2026-10-24.md`
records that retry is tied to periodic `RTPCICmdThread` command processing. The
pinned worker can exit on `RtmpOSTaskWait` failure, sets HALT, and clears queued
commands; init failure and halt stop timers/MLME and call task exit. This means
no eventual reset drain is proven after the retry worker disappears. Radio state
remains not-ready while pending, so this is an unresolved liveness/teardown gap,
not proof of device failure. Next trace reset entry paths through suspend, worker
wait failure and adapter teardown, then define lifetime-safe completion or
fail-closed teardown and test the interleavings. No production code/image/router
was changed for this audit. Preserve existing dirty files.

Close-path follow-up completed by Sol: staged `wr_iot_drv_close_checked` is
not wired in place of legacy `rt28xx_close`; outer lifetime retention remains
unproven. Its success is software close completion, not proof of hardware/RF
quiescence, yet the transition helper clears `reset_pending` on successful
`WR_RADIO_CLOSE`. Do not treat this as a safe terminal reset path or wire it to
production until the whole close/PM/error caller chain, hardware quiescence and
adapter lifetime are established. Evidence 562 records the finding. This turn
was source inspection only; no tests/build/CI/router operation. Continue from
the unresolved lifetime-safe teardown/drain design; preserve dirty files.

PM follow-up from pinned source `c25283e915a2a00a763774dd255b14aff997285e`:
`pci_main_dev.c:80-123` suspend calls `RTMP_DRIVER_PCI_SUSPEND`, then
`rt28xx_close`, then disables PCI. The legacy close invokes void `RTMPDrvClose`
and returns 0 even if `RT28xxPciAsicRadioOff` failed; that failure is only
logged. The candidate's periodic reset retry is therefore removed before PCI
power-down, and close success is not evidence of radio quiescence. Evidence
562 has the exact caller trace. Next design a lifetime-safe reset owner spanning
RTNL deferral, worker exit, suspend/resume and teardown; retain pending intent
and deny READY until verified recovery. No implementation, test/build/CI or
router action this audit. Preserve dirty files; Sol remains sole writer.

Teardown owner confirmed at pinned revision: PCI remove calls `RtmpPhyNetDevExit`
then `RtmpRaDevCtrlExit`; the latter calls `RTMPFreeAdapter`, which frees adapter
locks/resources and memory. The candidate's `adapter-free.inc` assumes callers
already quiesced work; it does not cancel or join a retry executor. Evidence 562
now records the lifecycle requirement: initialize before any cleanup path,
prevent enqueue after retirement, synchronously drain/cancel before free, use
nonblocking RTNL in worker, preserve pending reset while PCI is suspended, and
only resume BSS admission after verified recovery. Continue by deriving the
state transitions and caller ordering before integrating a workqueue. No code,
test, build, CI or router changes this turn.

Exact resume order is now in evidence 562: PCI D0/restore/enable, device attach,
`rt28xx_open`, PCI-resume notification, then queue wake. The transition candidate
does not bind to that PM callback, and `rt28xx_open` is driver init, not radio
verification. Next settle how queues and BSS admission remain fail-closed until
pending reset/readback completes, and whether attach must move or can remain
gated. Only then implement the PM-bound owner/workqueue lifecycle.

### Final project stage: kernel 4.4.302 — 2026-10-24

The owner reconfirmed the kernel change belongs at the very end, after Mi Mini,
all other agreed work and source consolidation. It is conditional; decide at
that point whether to proceed. If approved, scope it to every router added to
the project by then, with per-board review/build/device acceptance. Keep all
routers on 4.4.198 until then. Canonical plan:
`docs/PROJECT-DELIVERY-SCOPE.md`; technical analysis:
`docs/KERNEL-4.4.302-MIGRATION-PLAN.md`. Documentation order only; no migration
or build started.

### IoT isolated suspend/resume transition model — 2026-10-24

Sol added candidate-only PM states and helpers in `tools/iot/radio-transition.h`
and race cases in `tools/iot/check-radio-transition.c`. Suspend fences new
operations, preserves reset kinds across an in-flight RESET/PM window, and
requires all tickets to retire before marking SUSPENDED. Resume starts
UNVERIFIED; reset/readback gates BSS admission. Strict local MinGW C11 compile
and both transition/reset-admission fixtures passed. Local ASan/UBSan link was
unavailable (`libasan` and `libubsan` missing). No CI, target/MIPS build, router
or production-driver integration.

Pinned callback audit: device PM suspend/resume and remove use `device_lock`,
but PCI PM calls `rt28xx_close/open` directly rather than via RTNL-asserting
netdev open/stop. Resume calls `netif_device_attach` before `rt28xx_open`, and
the kernel helper wakes TX queues for a running netdev. The current candidate
does not gate packet TX; this makes attach/queue safety an explicit blocker.
The device lock alone does not drain the proposed retry worker. Further pinned
source: main, MBSS, AP-client, WDS and monitor netdevs share
`rt28xx_send_packets`, whose running check only reads `IFF_UP`; direct PCI
close does not invoke their stop callbacks. Moving main attach later leaves
virtual-interface TX exposed. Evidence 562 now includes an ordering contract
for adapter-wide TX admission/drain, all-netdev quiescence, worker cancellation,
checked close, and fail-closed resume.

Limits remain: sequential model only; no proof of driver callback integration,
worker cancellation/liveness, adapter lifetime, queue/TX gating or radio-off.
Do not wire it into the driver yet. Next: prove virtual-netdev enumeration and
active-TX drain/lock ordering, then implement a separate candidate for the PM
failure unwind, worker cancellation and queue gate before PCI power-down and
`RTMPFreeAdapter`. Evidence and source lines:
`docs/evidence/WR1200JS-IOT-562-RESET-RETRY-WORKER-LIVENESS-2026-10-24.md`.

Registry follow-up: the candidate registration bridge is bound only in
`ap/ap_mbss.c`; registry entries are raw pointers, with no pinned iterator
or proof of callback quiescence across PM. Do not use it yet for an
all-interface stop/detach pass. First map main/MBSS/AP-client/WDS/monitor
attach and teardown, then establish referenced snapshots and active-TX drain
before changing PCI suspend/resume. This is source-audit progress only.

The pinned-source map is now in evidence 562. In particular, AP-client, WDS
and monitor ignore `RtmpOSNetDevAttach` return, and monitor index-registration
failure leaves a stale `wdev->if_dev` after free. Repair and test those
lifetimes before making the registry a PM iterator. No vendor driver edit.

Sol staged `tools/iot/prepare-monitor-lifetime-candidate.py` to correct the
two monitor failure paths on exact pinned source bytes. It frees the separate
ops allocation, unregisters a successfully allocated wdev index after attach
failure, and clears the stale netdev pointer. Staging and Python syntax passed;
target C and image are untested. It is now in the combined candidate assembler;
the full assembler passed on a clean LF archive generated with
`core.autocrlf=false`. Do not feed it the Windows CRLF checkout: its exact TxS
blob gate fails before reaching monitor. Continue AP-client/WDS and referenced
PM enumeration next.

AP-client/WDS follow-up: `prepare-aux-netdev-lifetime-candidate.py` is now
included in the full candidate assembler. It handles wdev-index and netdev
attach failures in both families and corrects the AP-client partial-init
flag. The full exact-LF bundle preparation passed; generated failure paths
were inspected. No target C compile, fault injection or installed driver.
Next prove main/MBSS and all-interface referenced PM traversal plus TX drain.

Main/MBSS follow-up: the MBSS candidate already has attach-failure rollback
and a host fixture. `prepare-pci-probe-lifetime-candidate.py` now fixes the
main PCI attach-failure leak and stale `pci_set_drvdata`; full LF-source bundle
preparation passed. It is still a partial candidate, without target C compile
or kernel fault injection. Focus next on pinned netdev references across
unregister/free and an active-TX drain before PCI PM integration.

Source correction: do not retain `dev_hold` across remove. Linux 4.4
`netdev_run_todo()` waits for all refs, and vendor detach reaches it at RTNL
unlock. Virtual init occurs in `rt28xx_open`, reached directly by PCI resume
outside the normal netdev open wrapper. The next candidate must establish
bounded snapshot/RTNL/adapter-lock ordering and active-TX drain, not assume
the current raw registry or a long-held reference is safe. Evidence 562.

TX gate model: `radio-transition.h` now counts admitted OS TX entries and
blocks suspend completion and close/reset admission until they retire.
`check-radio-transition.c` passed strict MinGW C11 cases for suspend, close
and reset against in-flight TX. The source-pinned adapter candidate now wraps
the common `rt28xx_send_packets` entry under the shared adapter lock; an
extracted host fixture passed READY/PM/UNVERIFIED, packet-drop and lease
balance cases. This is still host software evidence: bind PCI PM and teardown,
bound queue ordering, and verify DMA completion
separately before production use. No target or device validation.

Last-TX wakeup is now staged: adapter allocation initializes
`wr_iot_tx_drain_wait`; the common TX wrapper wakes it after the final lease
leaves and after releasing the spinlock. The extracted fixture and full
exact-LF candidate preparation passed. A PCI PM waiter, bounded timeout,
failure unwind and adapter-free synchronization are still missing. No target
or device validation.
IoT PCI PM follow-up (2026-10-24): pinned suspend callback detaches only the
main netdev, calls direct legacy `rt28xx_close`, then disables/powers down PCI.
The legacy close always returns zero, so before binding the staged TX waitqueue
add a bounded timeout/failure unwind and reliable physical-close result; keep
all-interface queue ordering and adapter lifetime in the same review. The
candidate manifest now correctly says `tx_wakeup_bound=true` and
`pm_waiter_bound=false`. Exact-source staging and Python syntax passed. See
evidence 562. No production install, target build or router change.

The isolated `wr_iot_radio_abort_suspend()` now covers a pre-close wait
failure without publishing READY; host C11 fixture and full exact-LF bundle
preparation passed. It refuses abort while an exclusive ticket is busy, so
the PM callback still needs join/timeout and queue unwind before binding.
After abort, the model now refuses VERIFY/MAIN_OPEN and all other new radio
operations until any surviving TX lease retires. Strict C11 fixture passed;
the pinned checked-close bridge exists but PCI PM still uses legacy void
close and needs a distinct reviewed binding before PCI power-down.
The adapter candidate now contains unbound `wr_iot_wait_tx_idle()` with a
spinlock-protected predicate and bounded wait. Strict generated host fixture
and full exact-source IoT bundle preparation passed. PM callback still must
publish the fence, join exclusive work, quiesce all queues, handle timeout
and checked physical close before PCI power-down; no DMA/radio proof yet.
Pinned PCI ioctl path sets HALT/RADIO_OFF before legacy close; failure unwind
must restore consistent vendor flags/queues as well as transition state.
Checked-close bridge host fixture now tests admitted CLOSE ticket, stale
serial refusal and propagated failure; strict C11 passed. PCI PM binding
remains absent and must not be inferred from this fixture.
Unmutated pre-close PM timeout has a separate candidate rollback: prior READY
can be restored with in-flight TX only before queues, vendor flags or hardware
are touched and if no reset/close/exclusive operation intervened. After any
mutation use fail-closed UNVERIFIED abort. Strict C11 fixture and exact-LF
bundle passed; PCI PM still has no production binding or target build.
PCI/AP registration candidate now routes main, MBSS, AP-client, WDS and
monitor attach through the same checked registry bridge. Full exact-LF bundle
and strict registration fixture passed. Do not iterate these raw records in
PM yet: unregister/removal and referenced snapshots are unbound. SDIO attach
is a separate non-target path; `VirtualIfCnt` remains only a count.
Pinned ioctl dispatch also removes MBSS/AP-client/WDS/monitor dynamically,
so PCI device_lock alone cannot stabilize registry entries. Candidate attach
now tracks registration in flight and rejects attach after PM fence; a bounded
registration-idle wait helper is staged but not bound. Host fixtures and full
exact-LF bundle passed. Next bind dynamic remove retirement and a short
referenced PM snapshot without holding dev refs over unregister waits.
The candidate registry now has a short snapshot selector with caller-supplied
nonblocking pinning under the common lock. Host fixture checks exclusion and
pin balance; full exact-LF bundle passed. It is not a kernel `dev_hold/dev_put`
binding. Bind remove intent before every dynamic unregister, release snapshot
refs before waits/RTNL, then verify target build and lifetime behavior.
Dynamic virtual removal intent is now staged for MBSS/AP-client/WDS/monitor
before RTNL unregister. Host fixture verifies snapshot exclusion and full
exact-LF candidate assembly passed. Do not install yet: slot release and
vendor callback quiescence are not proven, so repeated remove/recreate would
leave tombstones and exhaust registry capacity. Main PCI release is separate.
Candidate `wr_iot_stop_registered_queues()` now uses actual `dev_hold/dev_put`
around the short registry snapshot and queue stop, with no wait or RTNL while
refs are held. Host fixture and exact-LF bundle passed. This is not PCI PM
integration: caller must first fence PM and drain registration, then handle
failure restoration; dynamic remove slot release still blocks installation.

Pinned PCI suspend sets vendor HALT/RADIO_OFF flags before close, while the
legacy close clears HALT unconditionally. The isolated checked-close stage now
preserves HALT during `pm_suspending` and clears it for ordinary close. Full
exact-LF candidate assembly and two strict C11 extracted fixtures passed.
No production binding, target build, CI or router change. Next: stage bounded
PCI PM drain/unwind and resolve dynamic registry retirement before installation.

Follow-up: model `suspend_complete()` now refuses failed CLOSE state CLOSING;
after ticket retirement, failed CLOSE or later PCI failure can abort to
UNVERIFIED without reopening admission. Strict C11 transition fixture and
full exact-LF candidate assembly passed. PCI callback unwind is still absent:
vendor flags, PCI availability and netdev queues must be reconciled before
returning a real error. No target build or router change.

MBSS remove now marks the netdev as removing before beacon-buffer teardown in
the isolated candidate. Exact-LF assembly and generated-source order check
passed. Do not release registry slots yet: vendor callback/queued-reference
quiescence after unregister remains unproved, and repeated remove/recreate
would exhaust fixed slots. No production binding or router change.

Source review adds a prior MBSS removal gate: `wdev_bcn_buf_deinit()` may
return FALSE while `bcn_state` is non-IDLE, yet `MBSS_Remove()` ignores it and
continues unregister/free. `MBSS_VirtualIF_Close()`/`MBSS_Close()` do not
unconditionally publish IDLE. Next executor should make beacon retirement
mandatory with a fail-closed retry before any registry slot release, then
prove vendor callback/TxS quiescence. Evidence 562; no production change.

The isolated registry now has an unmutated removal-cancel primitive with PM,
generation and stage guards; strict C11 fixture and full exact-LF candidate
assembly passed. It is unbound. Failure must propagate across `MBSS_Remove`
→ ap_cfg ioctl → VOID `RT28xx_MBSS_Remove` → `RtmpPhyNetDevExit` → PCI remove;
these current callers ignore results before adapter teardown. Do not patch
only the leaf and treat it as safe. Evidence 562; no production/router change.

The staged adapter bridge now cancels an unmutated removal mark under the
common lock with PM/retirement checks. Strict registration fixture covered
suspend refusal, post-abort success and post-unregister refusal; full exact-LF
assembly passed. It remains unbound at MBSS remove. Next: propagate checked
deinit/removal failures through ioctl and PCI teardown before enabling retry
or registry release. No target build, image or router change.

Owner rule, 2026-10-24: IoT must be built into every released router profile,
including WR1200JS, Mi Mini and future boards. No config option to exclude it.
Require per-board real support and isolation proof; current IoT-excluded images
remain development checkpoints. See AGENTS.md and the IoT contract. The
isolated MBSS removal leaf now refuses failed beacon deinit and propagates
status to ap_cfg; strict C11 fixture and exact-LF assembly passed. Wrapper,
RtmpPhyNetDevExit and PCI remove still discard failure, so do not bind this
candidate or claim a safe remove. No target build or router change.

The latest isolated bundle now returns checked MBSS removal status through
the OS wrapper and `RtmpPhyNetDevExit`; syntax check and exact-LF assembly
passed. PCI `rt_pci_remove` still ignores the BOOLEAN and frees the adapter.
Do not bind this candidate. Next executor must resolve all-child removal and
PCI lifetime ownership together, then test target compilation and failure
paths. See evidence 562. No firmware or router state change.

Two-BSS strict host fixture confirms a second-BSS refusal after the first
was freed; retry repeats the first beacon deinit. Treat current removal as
non-idempotent. Next: design and test all-BSS retirement under the shared
transition owner, then resolve the PCI VOID-remove lifetime boundary before
binding. No target build or router test was performed.

Source audit: AP-client, WDS and monitor removal wrappers are also `VOID`;
AP-client/WDS are removed before MBSS and monitor after MBSS. A failed MBSS
leaf already can leave earlier children freed, so do not treat the current
physical-exit `FALSE` as an atomic rollback. Evidence 562 contains the
call order and two-BSS reproduction. Next work needs one all-child teardown
ownership model, not another local leaf-only retry.

An unbound all-child teardown state model now exists in
`tools/iot/all-child-teardown.h`; strict C11 fixture passed. It refuses
adapter release after partial failure and requires caller-proven quiescence
after all AP-client/WDS/MBSS/monitor families complete. It does not perform
or prove those operations. Next: per-BSS irreversible milestones and actual
common transition-owner binding, then PCI lifetime resolution. Evidence 562.

`tools/iot/mbss-retirement.h` now models generation-keyed stages per BSS;
both strict host fixtures pass, and the all-child fixture waits for both BSS
vendor-done states. This is unbound software state only. Next executor must
attach stages to actual beacon/netdev/callback events under the common lock,
prove no repeat teardown on retry, and resolve PCI remove ownership. Evidence 562.

Isolated adapter storage for all-child/per-BSS state is staged and initialized
before publication; generated files and full assembly were checked. No
driver lifecycle path updates that storage. Bind only after generation,
lock, callback-retirement and PCI ownership rules are proven. Evidence 562.

The shared candidate attach bridge now publishes MBSS generation under the
adapter lock before OS registration, with matching rollback on failed attach.
Strict host fixture and full assembly passed. Existing radio-error stage
already handles MBSS attach failure cleanup. Next: bind removal intent and
beacon/kernel/vendor milestones to this generation, then verify PM race and
PCI lifetime. No target build or router state change. Evidence 562.

The host registration fixture now covers PM fencing during MBSS attach and
passes. It does not prove PCI safety: pinned `rt_pci_suspend()` omits the
staged registration wait. Bind a common-lock PM fence plus bounded wait before
mutating queues/radio, with failure unwind, then test real target build.
Evidence 562; no router state change.

The partial PCI PM candidate now fences open/reset/attach and waits for
in-flight registrations before carrier/queue/radio mutation; generated order
and full assembly passed. Do not install yet: TX/DMA drain, all-interface
queues, checked close result, suspend-complete and resume/failure unwind are
missing. Evidence 562. No target build or router change.

Generated PCI PM barrier now has an extracted strict C11 fixture covering
success, timeout before mutation, and reset-during-wait refusal; it passed.
Local MIPS compiler and usable WSL distribution were unavailable in this
session. This is not target/kernel proof. The next binding needs checked
queue/TX/radio close and PM completion/unwind before any production install.

MBSS removal in the isolated candidate now uses generation-matched begin,
unmutated cancel and beacon-done helpers under the shared adapter lock.
Strict host fixtures and full assembly passed. Kernel/vendor retirement and
safe retry remain unbound; do not interpret this as safe PCI remove. Evidence 562.

Extracted two-BSS test now passes after the candidate skips an already
removed (`if_dev == NULL`) BSS; it avoids repeated beacon deinit. Do not
advance registry kernel/vendor-done from detach alone: IDLE and callback
quiescence remain unproved, as does PCI removal failure handling. Evidence 562.

MBSS remove-begin now refuses OWNED/CLOSING reference state and active OS TX;
host test and full candidate assembly passed. Actual checked `ndo_stop` is
still unbound, so expect refusal for an open BSS. Do not mark kernel/vendor
done from detach; bind and prove close/quiescence first. Evidence 562.

\r\n
## IoT MBSS stop ownership handoff — 2026-10-24

Sol audited pinned MT76x3 stop ownership. `MBSS_VirtualIF_Close` calls a
VOID `VIRTUAL_IF_DOWN`; the ioctl decrements `VirtualIfCnt` before the
last-interface close and ignores its result. No shared transition lock
stabilizes this count against other interface families. Do not bind
`wr_iot_mbss_close_checked` directly to ndo_stop yet. Add one transition owner
for all UP/DOWN writers and checked result propagation,
then test main/MBSS/reset interleavings. See the top IoT contract section.
Inventory now confirms main, MBSS, AP-client, WDS and optional sniffer as the
five families; they share `CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP/DOWN`. The isolated
candidate's arithmetic guards already reject zero/overflow, but do not
serialize transitions or preserve count on failed close. Next action is the
shared owner and result path, not another independent arithmetic guard.
Correction after candidate inspection: `virtual-down-checked.inc` already
retains the last-close stage/count for retry under its ticket; the arithmetic
guards alone do not. The helper is staged but not bound to the legacy ioctl
dispatcher/callers. Reuse that helper when integrating shared ownership;
do not create a parallel count reservation mechanism.
Host `check-virtual-down.c` compiled with MinGW GCC `-Werror` and ran with
exit 0 on 2026-10-24. This is only host model evidence. Temporary executable
remains at `C:\Users\ANDRZEJ\AppData\Local\Temp\iot-virtual-down-check.exe`
because the command tool rejected cleanup; it is outside the repository.
Additional pinned-source finding: legacy `rt28xx_close` returns 0 even with no
adapter and calls `VOID RTMPDrvClose`; forwarding that return from the ioctl
cannot prove stop success. The existing MBSS admission wrapper has a ticket,
but raw `VIRTUAL_IF_UP` still enters the unconverted shared dispatcher. Bind
the common dispatcher and checked close milestones under one owner across all
interface families before promoting this candidate.
No production, MIPS image or router change in this audit.


## IoT reserved-open removal gate — 2026-10-24

The isolated registry now rejects begin_remove during WR_REF_RESERVED. This
prevents generic removal from racing admitted MBSS open before raw UP. Host
`check-interface-registry.c` and `check-netdev-registration.c` both compiled
with MinGW GCC strict C11 `-Werror` and ran with exit 0. Generic shared
UP/DOWN owner, checked stop propagation, MIPS image and runtime remain open.
No production or router change.
Follow-up: assembled MBSS removal calls begin_remove before beacon deinit and
returns on refusal. Expanded fixture proves RESERVED blocks generic and
MBSS-specific admission while BSS stays LIVE; strict host compile/run passed.
Other-family generic removal is not bound.
Full exact-source isolated candidate assembled with exit 0 at
`.iot-local-check/reserved-removal-20261024`; generated header contains the
RESERVED guard and generated MBSS removal calls admission before beacon
deinit. No target compilation, image or router proof.
## IoT atomic MBSS close admission — 2026-10-24

The isolated MBSS begin-close helper now captures the published OWNED
registration generation and reserves CLOSE/BSS_CLOSE under the same adapter
lock as `VirtualIfCnt`. It fails on unpublished/zero-count/busy state without
returning a generation. Direct and both composed strict C11 fixtures passed.
The caller must keep this ticket/generation through retries; production
`ndo_stop` and the other four families remain unbound. No firmware or router
change. Next: one common UP/DOWN owner/checked result path for all families.

## IoT MBSS close post-call revalidation — 2026-10-24

Isolated checked MBSS close now revalidates the pinned device generation and
radio ticket after each unlocked operation, before close-stage writes and
reference consume; the uncertainty branch is guarded too. A direct host
fixture injected slot reuse during `MBSS_Close` and passed, as did composed
open/close/down and physical last-close strict C11 fixtures. This stops stale
bookkeeping but does not prove vendor callback quiescence or safe reuse.
Continue with shared owner/teardown binding; do not install this fragment in
the production driver on this evidence alone. Router/firmware unchanged.

## IoT MBSS close generation check — 2026-10-24

The isolated checked MBSS close takes an expected registration generation;
zero/stale generation fails before mutation. Direct, composed open/close/down
and last-close physical-chain strict C11 fixtures passed. The combined
fixture's old raw-UP and duplicate ApCfg assumptions were corrected and
rerun successfully. The caller must preserve/pin that generation across the
whole ticket and shared owner, including unlocked vendor work. Production
netdev hooks, target module/image and router are unchanged/unverified.

## IoT shared openable registry lookup — 2026-10-24

The isolated `interface-registry.h` now provides
`wr_iot_registry_find_openable`; `mbss-open-admission.inc` uses it under the
existing transition lock. Registry and composed MBSS admission host fixtures
passed strict C11 `-Werror` compile/run. Use the returned generation when
carrying pinned identity into the future shared UP request, and revalidate
under the same lock before count mutation. This does not yet bind the other
four family callers or the common dispatcher. No production/device change.

## IoT all-family caller gate — 2026-10-24

Before editing the private UP/DOWN request ABI, run
`python tools/iot/check-virtual-if-call-coverage.py <staged-MT76x3-root>`.
The gate was added and passed on `.iot-local-check/reserved-removal-20261024/driver`:
five caller families, one UP and DOWN each; `py_compile` also passed. It
fails closed on extra/missing call locations. This is source coverage only;
binding checked identity/results and target/runtime validation remain open.

## IoT common ioctl identity gap — 2026-10-24

Additional source finding: `include/rtmp_cmd.h` defines the shared
`RT_CMD_INF_UP_DOWN` request with only `rt28xx_open/close` callbacks; the
`include/rt_os_net.h` wrappers pass no netdev or generation and DOWN is
`VOID`. Thus `common/cmm_cfg.c` cannot prove which of the five families owns
each count transition. Before binding a common owner, extend the request and
all callers together with pinned identity/generation and checked completion.
Do not use `pAd->net_dev` as the caller identity. Exact boundary is recorded
at the top of `docs/IOT-WIFI-IMPLEMENTATION-CONTRACT.md`. No production edit.

## IoT shared dispatcher coverage — 2026-10-24

Pinned/candidate inventory: main and MBSS open have radio tickets; AP-client,
WDS and sniffer UP remain raw, and every legacy DOWN remains unconverted.
Pinned AP-client ignores APC_OPEN status after VIRTUAL_IF_UP. Integrate one
owner across all five families with checked completion/rollback; MBSS-only
binding would leave races. See top IoT contract section. No target/device
acceptance or production edit.
Further source proof: ApCli_Open returns FALSE if no table device matches,
after legacy virtual UP and a possible packet-forward probe. A bare error
return would leak count/module reference; validate generation before UP and
retain checked rollback ownership for any post-UP failure.
## Zapret2 source-base handoff — 2026-10-24

### IoT caller identity continuation

Correction: the upstream ready flag is per band, so clearing it on IoT abort
can affect the main 2.4-GHz BSS. Generator now keeps vendor abort limited to
beacon intent and rejects a Band Steering `FALSE` call in the extracted-body
gate. Prior v4 candidate containing that call is superseded. Isolated v5 was
generated from the v2 identity tree: five-family source gate and strict C11
extracted abort fixture passed. It clears IoT beacon intent while preserving
main beacon intent. Band-level ownership, daemon convergence, target compile
and runtime checks remain open; do not bind production ndo_open yet.

Isolated v6 builds on v5: secondary MBSS open/close no longer set or clear
band-wide Band Steering readiness; main AP paths retain their updates. The
five-family source gate passed and rejects readiness calls in secondary
open/abort/close. The v5 extracted abort fixture remains applicable; target
compile, shared main-radio transition owner and runtime evidence are missing.

Main-close race located in isolated driver: `MainVirtualIF_close` publishes
main-down, then mutates `RTMPInfClose`/`VIRTUAL_IF_DOWN` without waiting for an
admitted IoT-open ticket. Host helper `wr_iot_radio_begin_main_stop` now latches
main-down and claims exclusive teardown under one lock; C11 interleaving
tests pass. It is not bound to the vendor close. Next add a bounded ticket
drain wakeup and checked close/count handoff before allowing any production
driver build. No device state was changed.
Host-only `wr_iot_registry_count_matches` and `wr_iot_main_stop_owned` now
refuse main close unless registry-owned references exactly match the vendor
count and the closing netdev is the owned main interface. C11 tests cover
missing owner, mismatch, in-flight record, wrong device, busy IoT open and
retry. This is not bound into vendor code: all five family UP/DOWN paths must
first share the same count/ref owner.
Five-family source audit is recorded at
`docs/evidence/WR1200JS-IOT-VIRTUAL-REF-CALLERS-2026-10-25.md`.
Shared legacy dispatcher still changes `VirtualIfCnt` outside the owner lock,
and void DOWN loses physical close errors. Main, AP-client, WDS and monitor
references stay IDLE after attach; binding the new stop gate now would strand
teardown. Migrate all families to claimed count/ref transitions before
binding `MainVirtualIF_close`; preserve the IFUP_IN_PROBE variant.
Main `ra0` open has a host-only claim predicate and unmutated ticket-abort
helper, both C11 checked. No vendor wrapper binding yet: zero-count
`rt28xx_open` can fail after partial hardware mutation, while the current
dispatcher reports only generic failure. Design checked physical-open rollback
and uncertain ref/module retention before migrating main UP to claimed ABI.
Physical first-open audit found ignored `RtmpOSIRQRequest` status. Isolated
v10 checks the return before driver IRQ initialization, does not release an
IRQ that was never acquired, and exits optional `WIFI_DIAG` on both failures.
Generator and source gate passed; no MIPS compile or firmware packaging.
`rt28xx_init` has staged cleanup labels, but they do not establish hardware
quiescence, so main claimed-UP rollback/uncertain ownership remains open.
Main-stop helper retry is now idempotent while `main_inhibited` remains set;
the C11 test confirms the epoch does not advance on a repeated busy claim.
Transition model now publishes `retired_serial` on successful finish and
unmutated abort. Ticket-specific wait predicate and C11 stale-abort/IoT-open
checks pass. The later isolated v8 adds queue/wakeup wiring, but production
`MainVirtualIF_close` still does not use it.
Isolated v8 adds ticket wait queue storage/init and wakeups after MBSS,
main-open and reset ticket retirement. The helper rechecks under the common
lock and uses a bounded kernel wait. C11 host fixture and five-family source
gate passed. v7 was partial scratch due CRLF anchor mismatch and is superseded.
No main-close binding yet; first stabilize all-family count/ref ownership and
checked close result. Do not package v8 or infer on-device behavior.

The v4 MBSS raw abort-failure path now returns `-2`, retains the module pin,
and marks its record `WR_REF_UNCERTAIN_OPEN` rather than reusing an uncertain
vendor BSS. Registry removal/reopen fail closed. Host reference/registry
checks and source gate passed. Next design a bounded, generation-owned
recovery with observed teardown before any production ndo_open binding; do
not leave a permanent pin in a release image.

`tools/iot/prepare-virtual-open-dispatch-check.py` extracts the claimed UP
branch from v4 `cmm_cfg.c`. Its strict C11 fixture now proves one count
increment per ticket and rejects replay, wrong device and a partial claim.
`virtual_up_stage` is part of the isolated radio owner and is set under the
same lock as `VirtualIfCnt`. Keep the v4 target-build/runtime boundary:
other families and active DOWN are still legacy paths.

Latest isolated candidate: `.iot-local-check/virtual-open-claim-v4-20261025`.
It carries the MBSS wrapper's existing ticket through the private request
and checks it in `cmm_cfg.c` before count increment. Reproduce with
`tools/iot/prepare-virtual-open-claim-candidate.py`; five-family gate passed
against this and prior identity candidate. v4 also overlays the current
transition, registry, checked-close and DOWN fragments; v3 inherited stale
copies and is superseded. v1/v2 directories are incomplete scratch attempts;
native deletion was rejected by executor policy. Do not package v4: other
families and the active DOWN wrapper still use unsynchronized legacy paths,
and no target compile or hardware evidence exists.

New host-only `tools/iot/virtual-open-claim.h` verifies the single wrapper
ticket at dispatcher admission; `check-virtual-open-claim.c` passes strict
C11 including stale generation, reset and auxiliary first/later open cases.
It is not wired into `RT_CMD_INF_UP_DOWN` or `cmm_cfg.c`. Next bind the claim
across that ABI with one owner and reviewed count/rollback ordering; do not
mistake this predicate for a complete open transaction.

Do not add an independent `wr_iot_radio_begin` in `cmm_cfg.c`: MBSS already
owns that ticket before `MBSS_OPEN` and `VIRTUAL_IF_UP`. Integrate a single
outer ticket across both layers, with device/generation validation, then
extend equivalent admission to main/AP-client/WDS/monitor. This conflict is
confirmed in the isolated source; no production driver change was made.

Read the new consumer audit in `docs/IOT-WIFI-IMPLEMENTATION-CONTRACT.md`.
The staged dispatcher ignores `if_dev`, uses only `VirtualIfCnt` and the main
netdev, and cannot report failed close. Before binding the candidate, connect
device plus generation to the common owner and settle wrapper side-effect
rollback for AP-client/WDS/monitor. No vendor-driver change in this step.

The isolated AUX_START race check now includes main-interface DOWN. A late
successful finish stays `UNVERIFIED` and inhibited; strict C11 auxiliary test
passed on 2026-10-25. Do not bind this model into vendor wrappers before the
five-family owner and close/reset serialization are established.

Auxiliary ticket model now handles reset requested during `AUX_START` or
`AUX_OPEN`: late success yields `UNVERIFIED` with pending reset retained.
Both interleavings passed strict C11; production reset worker and hardware
verification are still unbound.

Corrected first-open finding: every child initializer has a redundant-init
guard, so a blanket zero-count auxiliary rejection was overbroad. The isolated
radio owner now uses `AUX_START` at zero count, establishing physical readiness
without falsely marking the main interface ready; `MAIN_OPEN` later promotes
main readiness. Strict C11 test passed. Vendor wrappers and full teardown/
reinit idempotence still need source, target-build and runtime validation.

New isolated AUX_OPEN/AUX_CLOSE model in `tools/iot/radio-transition.h` and
`virtual-down-checked.inc`; strict C11 `check-aux-radio`, existing radio and
virtual-DOWN fixtures passed. Next bind AP-client/WDS/monitor wrappers to
generation-aware registration plus these tickets, with explicit first-open
behavior and retained failure cleanup. No vendor production integration yet.

Latest DOWN audit: all five legacy wrappers hide DOWN failure; common
dispatcher decrements count before physical close and drops its result.
See the per-family table in `docs/IOT-WIFI-IMPLEMENTATION-CONTRACT.md`.
Do not simply change DOWN to `INT` and return an error after resources have
already been released. Bind all families to one generation-aware owner and
define retained uncertain-close/retry semantics first.

The five-family gate now also checks checked netdev attach paths; both staged
and isolated candidate trees passed. Only MBSS currently advances registry
reference phases. Next writer should bind the other four families to the same
generation-aware owner and make the common DOWN result observable; do not
assume a published registry slot means it owns a physical-open reference.

IoT next step: use `tools/iot/prepare-virtual-if-identity-candidate.py` and
`.iot-local-check/virtual-if-identity-v2-20261024` as an isolated candidate.
All five caller families now pass their `netdev` in virtual UP/DOWN; main host
fixtures passed strict C11. The common request consumer does not yet validate
the caller or serialize count changes with registry generation/reset. Keep
this out of the production build until that owner path is proven.

The source base is now repeatably verifiable offline: run
`python tools/zapret2/verify-source-base.py` in this checkout. It passed on
2026-10-24 for all 253 files (2,516,830 bytes); the upstream pinned commit
was also confirmed on GitHub. Do not mistake this for a MIPS build or an
enabled firmware feature. Keep Stage 2 after baseline WR1200JS acceptance.

Sol imported a complete pinned `bol-van/zapret2` source snapshot (commit
`4a33055448ce5f4e7acc704e1fbe0d8a8a6aa08d`) into
`third_party/bol-van/zapret2/`. See `docs/ZAPRET2-SOURCE-BASE.md` and
`third_party/bol-van/zapret2-source-manifest.json`; all 253 file hashes were
checked against the downloaded archive and local files. This is source
preservation only, not a port. Current branch `codex/wr1200js-service-webui`,
HEAD `f0b995d`; the shared tree remains dirty with existing unrelated work.
No commit, push, firmware build or device modification in this step. Next
Zapret2 action at Stage 2: verify target NFQUEUE/Lua/library support before
adding Padavan build and lifecycle hooks. IoT and WR1200JS acceptance remain
ahead of Stage 2 in the agreed delivery order.

## Zapret scope handoff — 2026-10-24

Only Zapret2 is in the agreed Stage 2 scope. The old selector is named
`CONFIG_FIRMWARE_INCLUDE_ZAPRET` in this tree, not `...ZAPRET1`; it was
removed from both board configs and the WebUI config inventory. The delivery
scope now supersedes older instructions to enable both variants. Do not
reintroduce Zapret 1. No firmware build or device change was made.
candidate and host fixture must be checked before any production binding;

## Zapret2 source-base handoff — 2026-10-25

Local HEAD `9e56bc6` on `codex/wr1200js-service-webui` commits only the
pinned Zapret2 source base (`docs/ZAPRET2-SOURCE-BASE.md`, manifest,
`third_party/bol-van/zapret2/`, offline verifier). The verifier passed for
253 checkout files. Seven upstream Windows files have CRLF checkout bytes and
Git-normalized index bytes; preserve the vendored `.gitattributes`.
No GitHub push, MIPS build, image integration or router action occurred.
Continue the agreed IoT/WR1200JS work before Stage 2 Zapret2 integration;
preserve every pre-existing dirty file in this shared checkout.

## IoT main-open ownership handoff — 2026-10-25

The current main wrapper calls `AP_MAIN_OPEN` before virtual UP. Treat all
subsequent failed opens as possibly mutated, including failed IRQ request or
`rt28xx_init`. Host model now has `wr_iot_ref_complete_main_open` and a strict
C11 fixture for unmutated, acquired and uncertain outcomes; the fixture
passed. Next: reserve main registration before `AP_MAIN_OPEN`, pass its ticket
to the common dispatcher, retain the module pin on uncertain failure, and
design checked recovery before any production binding. Do not infer that the
existing `rt28xx_init` err labels prove full hardware rollback. Current
driver/image/router remain unchanged.

The next host-only gate is `wr_iot_main_open_reserve` in
`tools/iot/virtual-open-claim.h`: ticket plus main `ra0` registry record are
reserved under one adapter lock before vendor mutation, with unmutated abort
on failed reservation. C11 test and regenerated isolated v11 source gate
passed. `MainVirtualIF_open` and common virtual-UP still do not call it;
bind both together and preserve uncertain failure/pin ownership before any
production build.

Isolated v12 (`.iot-local-check/main-open-owner-v12-20261025`) now wires the
main ra0 reserve helper into `MainVirtualIF_open` and START/MAIN_OPEN handling
in the common virtual-UP dispatcher. Reproduce it with
`python tools/iot/prepare-main-open-owner-candidate.py
.iot-local-check/virtual-open-claim-v11-20261025
.iot-local-check/main-open-owner-v12-20261025-new` (choose a new output path).
The five-family source gate passed. It is still non-production: legacy
auxiliary UP/DOWN and main close bypass the shared owner; physical-open
rollback can race them; uncertain-open recovery and MIPS build are absent.
Continue with all-family count ownership and main-close ticket drain before
binding anything to the shipped driver.

Main-stop host gate correction: `wr_iot_main_stop_owned` now latches
main-down before rejecting a count mismatch caused by a RESERVED/uncertain
secondary reference; it does so only for an owned main netdev with nonzero
vendor count. Repeated attempts keep one epoch bump. The strict C11
main-stop and radio-transition fixtures passed. Do not simply make
`MainVirtualIF_close` wait on the ticket queue: inspect ndo_stop/RTNL and
the pending ticket's callback context first, then bind checked DOWN and
all-family count ownership together. No driver/image/router change.

Linux v4.4 `__dev_close_many` ignores `ndo_stop` return while holding RTNL
and clearing `IFF_UP`. Do not rely on an error return from main close for a
retry, and do not wait on a ticket in ndo_stop until its retire path is proven
RTNL-independent. New host `wr_iot_main_stop_complete` keeps CLOSING/pin on
failed or physically unverified close; strict C11 check passed. See
`docs/evidence/WR1200JS-IOT-NDO-STOP-RTNL-2026-10-25.md`. Next source step:
trace ticket retirement callbacks for RTNL dependence, then design a
nonblocking recovery owner before production binding. Router untouched.

Ticket/RTNL trace for v12: main and MBSS open tickets are owned by
`ndo_open` callbacks; reset admission uses `rtnl_trylock` and releases RTNL
only after ticket retirement. The kernel ignores `ndo_stop` return. Do not
add a direct ticket wait in main close; design an adapter-pinned deferred
recovery owner for unmatched/busy close and verify its lifetime against
command-worker failure, PCI suspend and remove. See
`docs/evidence/WR1200JS-IOT-TICKET-RTNL-CONTEXT-2026-10-25.md`.
Host gate now exposes `wr_iot_main_stop_request`: WAIT_TICKET includes exact
serial, NEEDS_RECOVERY covers unmatched state without a busy ticket, and
ADMITTED owns the stop ticket. No waiting or scheduling occurs in the helper.
Its strict C11 fixture passed. Next agent must provide a real deferred owner
with retained adapter/module lifetime before using these outcomes from
`MainVirtualIF_close`.

PCI remove lifetime finding: `rt_pci_remove` ignores the BOOLEAN failure
from `RtmpPhyNetDevExit` and calls `RtmpRaDevCtrlExit`/`RTMPFreeAdapter`
regardless. A netdev hold is insufficient for a deferred worker using the
adapter. Host-only `wr_iot_adapter_release_gate` and strict C11 fixture now
require child/radio/reference/worker quiescence before adapter free. See
`docs/evidence/WR1200JS-IOT-PCI-REMOVE-DEFERRED-OWNER-2026-10-25.md`.
Next: design the single retirement owner and join it with close/reset/PCI
remove before any production deferred worker; do not just return early from
the `void` PCI remove callback on error.

AP-client follow-up (2026-10-25): `ApCli_VirtualIF_Open` drops the failure
returned by `CMD_RTPRIV_IOCTL_APC_OPEN` after virtual-UP; APCLI close drops
`APC_CLOSE` and virtual-DOWN results. Source evidence:
`docs/evidence/WR1200JS-IOT-APCLI-OPEN-RESULT-2026-10-25.md`. Next isolated
candidate must reserve AUX ticket/record before virtual-UP and retain lifetime
for an uncertain APC_OPEN/partial-close result. Audit WDS and monitor peers
with the same count before production binding. No target build/router action.
The host-only `wr_iot_aux_open_reserve` now reserves `AUX_START`/`AUX_OPEN`
with the exact device record under one lock before vendor mutation; strict
C11 `check-virtual-open-claim` passed. Continue with checked APCLI result and
shared dispatcher binding in an isolated candidate. This is not a production
driver patch.
Host-only `wr_iot_ref_complete_aux_open` now retains the record and module
pin whenever an attempted required OPEN path fails.
For WDS the helper now explicitly requires only virtual-UP because there is
no family OPEN. Monitor still ignores SNIFF_OPEN status, and its inner OPEN
returns TRUE even for a mismatched netdev; validate identity separately.
Source-pinned isolated monitor identity candidate was generated by
`tools/iot/prepare-monitor-open-identity-candidate.py`; its strict C11
fixture passed for both identities. This does not bind the wrapper, which
still ignores SNIFF_OPEN status. See the APCLI open-result evidence file.
Host registry now stores netdev family from `priv_flags` and AUX reservation
requires APCLI/WDS/MONITOR family equality. C11 registration, registry and
claim fixtures passed. The next isolated dispatcher candidate must carry and
verify that family under the adapter lock before incrementing VirtualIfCnt;
v12 driver copy does not yet include this model change. No MIPS build/device
operation.
Strict C11 reference fixture passed. Real APCLI wrapper must check ioctl
status and use a retained adapter/netdev recovery owner; do not merely return
an error after virtual-UP or call unchecked DOWN and release the pin.
Host `wr_iot_virtual_aux_open_claim_matches` now fences family, main device,
ticket/reset and zero/nonzero vendor count at the prospective dispatcher
mutation. Strict C11 fixture passed. Source `rt28xx_open` has side effects
before failure; do not insert an AUX_START path with decrement-only rollback.
Retained recovery ownership remains necessary before v12 driver binding.

## IoT auxiliary dispatcher checkpoint — 2026-10-25

The isolated `prepare-virtual-open-claim-candidate.py` now admits a claimed
`AUX_OPEN` increment alongside MBSS only after an exact family/record/ticket
check under the transition lock. Generated `.iot-local-check/virtual-open-claim-v14-20261025`
from the pinned identity candidate; extracted dispatcher fixture compiled with
strict C11 warnings and passed MBSS/AP-client increments and replay refusal.
`AUX_START` remains refused until checked first-open failure recovery exists.
No production wrapper, image, router or runtime state changed. Evidence:
`docs/evidence/WR1200JS-IOT-APCLI-OPEN-RESULT-2026-10-25.md`.

## IoT combined isolated open candidate — 2026-10-25

Generated `.iot-local-check/combined-open-v16-20261025` by preserving the
reviewed v12 main START/MAIN_OPEN owner and adding the claimed MBSS/AUX_OPEN
branch with current family-tagged registration fragments. Extracted branch
passed strict C11 fixture; five-family source/attach coverage passed. This is
not a target build or production binding. APCLI/WDS/monitor wrappers, DOWN,
AUX_START first-open recovery and adapter release still need one owner before
image integration. Evidence: `docs/evidence/WR1200JS-IOT-APCLI-OPEN-RESULT-2026-10-25.md`.

## IoT WDS open candidate — 2026-10-25

Generated `.iot-local-check/wds-open-v17-20261025` with a WDS non-first
AUX_OPEN ticket, exact family/record claim, checked dispatcher call and
conservative module-pin retention after uncertain open. HNAT/queue start only
after owned success. Five-family source coverage passed for v16/v17; Python
syntax passed. The complete driver was not target-compiled. WDS close and
other auxiliary wrappers remain legacy, so v17 is not safe to package.
Evidence: `docs/evidence/WR1200JS-IOT-APCLI-OPEN-RESULT-2026-10-25.md`.

## IoT AP-client open candidate — 2026-10-25

Generated `.iot-local-check/apcli-open-v18-20261025`: AP-client non-first
open reserves an exact AUX_OPEN claim, checks both virtual-UP and APC_OPEN,
and retains an uncertain record/module pin after attempted failure. HNAT and
carrier actions require owned completion. Five-family source coverage passed
on v17/v18; Python syntax passed. The complete driver has not been
cross-compiled, close/recovery paths remain unbound, and no router state was
changed. See `docs/evidence/WR1200JS-IOT-APCLI-OPEN-RESULT-2026-10-25.md`.

## IoT monitor open candidate — 2026-10-25

Generated `.iot-local-check/monitor-open-v19-20261025` with monitor
AUX_OPEN claim, checked SNIFF_OPEN result and retained uncertain-open pin.
The monitor identity correction matches the separately tested source hash.
Five-family source coverage, Python syntax and C11 identity fixture passed.
No target driver compile or router action. All five open caller families now
have candidate claimed paths; their close/reset/lifetime and first-open
recovery paths are still incomplete. Evidence:
`docs/evidence/WR1200JS-IOT-APCLI-OPEN-RESULT-2026-10-25.md`.

## IoT late auxiliary-open success gate — 2026-10-25

The v17-v19 isolated wrappers could publish OWNED after `wr_iot_radio_finish`
returned success even when reset/close/suspend had invalidated readiness.
Added shared `wr_iot_aux_open_accepted` under the transition lock and rebuilt
v23 WDS, v24 AP-client, v25 monitor candidates. C11 radio-transition tests
passed normal AUX_OPEN and rejected late reset/close success; v25 five-family
source gate and Python syntax passed. No local MIPS compiler or target build;
CI candidate path exists but v25 is not integrated into it. Close/recovery
and first-open still block image integration. Evidence:
`docs/evidence/WR1200JS-IOT-APCLI-OPEN-RESULT-2026-10-25.md`.

## IoT main-open late-success guard — 2026-10-25

Added `wr_iot_main_open_accepted` to distinguish expected UNVERIFIED main
open from an invalidated reset/close/suspend result. The isolated main
wrapper retains UNCERTAIN_OPEN and its module pin on invalidated completion.
C11 normal/reset/close model tests passed. Regenerated main v26, combined
v27, WDS v28, AP-client v29 and monitor v30 isolated trees; five-family
source gate and Python syntax passed on v30. No target compile, production
binding or router action. Evidence:
`docs/evidence/WR1200JS-IOT-APCLI-OPEN-RESULT-2026-10-25.md`.

## IoT extracted auxiliary open wrappers — 2026-10-25

Extracted the exact WDS/AP-client/monitor open function bodies from isolated
v30 into a host C fixture. Strict C11 compilation and execution passed each
family's normal claimed open, virtual-UP refusal, and late reset after count
increment; AP-client/monitor also passed failed family OPEN. Failures kept
UNCERTAIN_OPEN/pin and skipped HNAT. This is stronger than source-text coverage
but is still a mocked host execution, not MIPS compilation or router runtime.
Next: bind checked close and recovery across all families before packaging.
Evidence: `docs/evidence/WR1200JS-IOT-APCLI-OPEN-RESULT-2026-10-25.md`.

## IoT non-last auxiliary close admission — 2026-10-25

Added host-only `wr_iot_aux_close_reserve` for WDS/AP-client/monitor. It
requires exact family, published OWNED reference and registry/vendor count
match under one lock, then reserves AUX_CLOSE plus CLOSING record. Last
physical close is refused here. Added an unmutated AUX_CLOSE ticket abort;
strict C11 fixture passed admission/refusal/abort cases. No stop wrapper or
recovery worker is bound, and no target compile/router change occurred.
Evidence: `docs/evidence/WR1200JS-IOT-AUX-CLOSE-ADMISSION-2026-10-25.md`.

## IoT WDS close handoff — 2026-10-25

v31 at `.iot-local-check/wds-close-v31-20261025` contains isolated non-last
WDS checked stop. `prepare-wds-close-wrapper-check.py` extracted and passed
the exact wrapper under host GCC C11 for success, failed DOWN and last-close
refusal. `check-virtual-if-call-coverage.py` passes v30 and v31. Next owner:
design retained recovery for failed `ndo_stop`, then extend checked stop to
AP-client and monitor; only afterward consider target compile/packaging.
No firmware or router changes. Evidence:
`docs/evidence/WR1200JS-IOT-AUX-CLOSE-ADMISSION-2026-10-25.md`.

## Current IoT release boundary — 2026-10-25

Branch `codex/wr1200js-service-webui`, HEAD `df2605a` at this audit; preserve
all pre-existing tracked and untracked changes. Pinned v33 source inspection
found that AP-client, WDS and monitor remove paths return `VOID` and hide
skipped child teardown. PCI remove ignores the MBSS-capable parent result and
still frees the adapter. Implement checked removal outcomes and joined
close/recovery ownership for each child before binding deferred work or an
adapter release gate; separately audit probe-error unwind. Details and exact
source anchors: `docs/evidence/WR1200JS-IOT-PCI-REMOVE-DEFERRED-OWNER-2026-10-25.md`.
No target compile, image, CI or router verification was performed in this audit.
The isolated v35 WDS removal result chain was generated and source-checked.
Isolated v36 also propagates AP-client and monitor refusal results; source
chains and exact file-diff inventory passed. Next, join each close/recovery
owner and prove registry/callback quiescence before PCI adapter release;
do not bind v35/v36 into firmware until these lifetimes are closed together.
The failed partial v34 output was removed.
The v37 isolated candidate adds a post-unregister close-phase check before
freeing WDS/AP-client/monitor netdevs. It retains incomplete children but is
not a complete teardown because PCI still frees the adapter on parent
failure. Complete worker join and all-family registry retirement next;
source checks passed, target/image/router checks were not run.
OS-helper inspection invalidated v37's ordering: detach frees `netdev_ops`.
Use v38 as the next isolated base. It calls close and checks idle under RTNL
before unregister; refusal leaves the interface registered. Its source
ordering and four-file diff passed, but lock order, recovery worker,
registry/callback retirement and PCI release remain unproved.
The pinned Padavan 4.4.198 source calls `ndo_stop` once for an UP netdev and clears
`IFF_UP` regardless of its result. Thus v38's registered-but-down failure
cannot be retried by `dev_close` again; bind the retained same-ticket
continuation through an adapter-fenced worker, or redesign close ownership.
The local IMQ transforms do not touch these close functions; compare the
final generated build tree before target claims.
The host-only recovery owner now selects `RETRY_DOWN` for stage 1 and
`COMPLETE_AFTER_DOWN` for stage 4 only with matching device/generation/serial
and a running owner. Strict C11 fixture passed. Next integration step is
actual pinned worker plus adapter release fence, not another `dev_close`.
Do not copy the WDS stage machine to AP-client/monitor: their legacy stops
call APC_CLOSE/SNIFF_CLOSE before virtual DOWN and discard the result, with
possible earlier family mutation. The WDS owner rejects both families in
host tests. Next, define checked family-close and uncertain-side-effect
reconciliation separately before adding their worker continuations.
The host-only `aux-family-close.h` now enforces that split for AP-client and
monitor; its C11 fixture passed. Bind checked APC_CLOSE/SNIFF_CLOSE results
and reconcile uncertain side effects before allowing their virtual DOWN or
worker retry. No production driver, image or device test resulted.

## Zapret2 handoff to DeepSeek — 2026-10-25

User explicitly transferred Zapret2 integration to DeepSeek. Sol pushed
`codex/wr1200js-service-webui` to `df2605a264b8aa0ec7a25b2b1c662bab97983a9c`.
Pinned Zapret2 source is in commits `9e56bc6` and `df2605a`; verifier passed
for 253 files and 2,516,830 bytes at upstream `4a33055448ce5f4e7acc704e1fbe0d8a8a6aa08d`.
The push also included five earlier IoT commits; uncommitted IoT and other
files remain local and untouched. DeepSeek should read `AGENTS.md`,
`PROJECT_STATUS.md`, `docs/EXECUTION-ROLE.md`, and `docs/ZAPRET2-SOURCE-BASE.md`,
check `git status`, claim the single-writer role, then integrate Zapret2 in
small verified steps. No firmware build, image test, or router change was made.

## Handoff to Sol — 2026-10-25

The owner explicitly transferred the single-writer role to Sol. Sol must finish
IoT first, then verify the Zapret2 and Modern WebUI work. The root agent stopped
editing after this handoff.

Repository state: branch `codex/wr1200js-service-webui`, local and remote HEAD
`28b0faf3c6b463d02f273f9f627b192406ac7f91`; `origin/main`
`d1dc0ebaf82af316ad8ba65a01952c229c69e919`; PR #2 open and mergeable.
Zapret2 candidate run `40189818250` passed. Firmware build #584, run
`40189820727`, was in progress when this handoff was written.

Completed Zapret2 scope includes the selector, pinned `nfqws2`, Lua/license
assets, fail-open service lifecycle, Classic Services UI with separate observed
states, firewall reapply and localization. Modern preview now follows the
two-column reference dashboard and maps fourteen services to real Classic
routes. Builds #582/#583 compiled successfully but were rejected only by
verifier defects that are corrected in the current HEAD. No final image/TRX has
yet been accepted from a fully green run.

The router was not flashed or rebooted. Read-only SSH timed out, so runtime is
unverified. Preserve the existing 32 modified tracked files and 147 untracked
entries; do not bulk-stage them.

Next order: claim the role; complete IoT open/close/reset ownership, recovery,
PCI remove and callback/registry release; verify build #584 or its replacement
and ROMFS/TRX/SHA256; run Zapret2 device tests only with separate permission and
a recovery path.

Full handoff:
`docs/evidence/WR1200JS-HANDOFF-TO-SOL-2026-10-25.md`.

## Sol IoT continuation: guest-to-IoT receipt (local only)

`virtual-open-claim.h` now has an owned/count/ticket post-open MBSS finish
gate. The local legacy and v40 assemblers now bind guest/IoT readback outside
the transition lock; the v40 assembler retains its claimed raw open and three
ticket-retirement wakeups. Local v40f output passed the strict C11 post-open
and CR_ENABLE fixtures, five-family caller coverage and eight remove-result
pairs. The optional v40 CI path has the host fixture gate. This is not yet
MIPS-compiled, packaged or tested on the router; #600 predates it. Next run
the isolated v40 target compile, then resolve failed open/close recovery
before production integration. Keep the router unchanged.
Local v40h splits failed MBSS abort (`-2`, UNCERTAIN_OPEN) from failed
CR_ENABLE after acquired vendor UP (`-3`, OWNED/count retained, radio FAULT).
The generated-header and raw-function host fixtures passed. A failed ndo_open
will not receive ndo_stop; neither outcome has a bound recovery worker.
Local v40i adds a full registry/vendor-count and MBSS-family check before
MBSS stop-ticket admission; its generated-header C11 fixture passed missing
owner refusal and normal close retry. The v40 CI host gate now tests it.
This does not bind a recovery worker or prove all legacy count writers.
Local v40j source audit found five active virtual-UP callers, all claimed.
The v40 assembler now rejects a new unclaimed caller and removes the
unlocked legacy UP count-write path from its isolated output. Fresh assembly
and MBSS host fixtures passed. Void legacy DOWN still bypasses common count
serialization; continue with owner-aware stop binding and recovery before
target/image claims. No production driver, image or router change.
The v40j source audit identifies four remaining void virtual-DOWN callers:
main, MBSS, AP-client and monitor. WDS already uses checked DOWN. AP-client
and monitor discard family-close results after calls that can mutate state;
do not replay them after uncertain failure. Bind retained owners and checked
result stages before removing the legacy dispatcher branch. See the v40
evidence note for exact call sites and integration order.
Fresh isolated v40k assembly passed an exact four-caller regression inventory
gate. Adjust that gate only when a caller is replaced by checked ownership.
Local v40l fixes a separate MBSS checked-close completion gap: successful
checked DOWN now retires the same ticket and consumes the record under one
lock. A failure keeps the CLOSING record and pin; a repeat after success is
idempotent. Fresh assembly and local/generated-header C11 fixtures passed.
Do not bind to `ndo_stop` until the adapter-pinned recovery worker and PCI
release fence are implemented and verified.
Host-only `mbss-close-recovery-owner.h` now distinguishes acquired failed
open, retained checked close, and uncertain states. Its strict C11 fixture
passed and is gated in optional v40 CI. This is not a bound kernel worker:
next implement actual `dev_hold`/adapter fence, schedule and join the owner,
then connect checked close to `ndo_stop` and PCI remove without replaying
uncertain operations. See the v40 evidence note.
The v40l pre-CI caller gate initially failed because its old MBSS handoff
count missed the new acquired `-3` branch. Updated it to require the distinct
OWNED/fallback path and fourth wakeup while preserving v39 behavior. Pinned
v39 and local v40l both pass. This clears a local source gate only; target
compilation still needs a new isolated CI run.
Selective v40 IoT code/fixture commit `eefbf12` is pushed to PR #2. The
ordinary firmware run `40257333149` and ABI run `40257333066` started on
that HEAD; neither selects optional v40 overlay. Preserve all other dirty
files. When the ordinary run is terminal, check its result, then dispatch
one v40 candidate run if no equivalent run exists for `eefbf12`.
2026-10-26 check: ABI run `40257333066` succeeded; ordinary firmware run
`40257333149` still had `build (wr1200js) / build-wr1200js` in progress.
No optional v40 run has been dispatched from this check. Current production
RC/HTTPD source still has no bound `wr_iot_activation_start` or fixed
`wr_iot_apply` handler; `tools/iot` contains candidate-only logic.
Ordinary firmware #603 (`40257333149`) succeeded on `eefbf12`. A single
manual v40 candidate run `40260205702` was dispatched on the same HEAD with
`boards=wr1200js`, `run_candidate_checks=true`, `iot_candidate_variant=v40`.
Inspect its result and isolated target compile log/artifact before claiming
target compilation. Do not dispatch another equivalent run while it is live.
Run `40260205702` finished successfully: isolated v40 MIPS32r2 driver module
and main-observer probe compiled. Artifact `iot-merged-driver-probe` was
downloaded to `artifacts-603-v40/` for inspection. Its source manifest has
pre-build `target_compiled:false`; use the successful step, build log and ELF
module as compile evidence. No production driver, image or router acceptance.
Next bind retained recovery ownership and all remaining checked DOWN callers
before production inclusion; preserve unrelated dirty files.
Local uncommitted workflow edit adds `target-compile-result.json` after the
isolated IoT module checks, leaving the pre-build source manifest intact.
YAML parsing and an extracted post-build block passed against run
`40260205702`'s downloaded module. New reporting code still needs CI.
The local v40 module's symbol table contains the checked MBSS begin/close
and virtual DOWN functions; the workflow now gates those symbols for v40.
This does not bind `MBSS_VirtualIF_Close`, which still calls legacy DOWN and
returns success. Do not claim checked stop or safe remove from symbol presence.
Local checked-close follow-up captures the original MBSS reference token
across unlocked vendor operations. An injected nonzero replacement token
after DOWN now refuses ticket retirement; strict C11 fixture passed. This
edit is uncommitted and has no target compile or `ndo_stop` binding.
Correction: the focused change was committed/pushed as `b2dce05` on PR #2.
Fresh v40m isolated assembly, generated-header C11 close fixture and caller
coverage passed. Check the ordinary CI run on this HEAD, then dispatch one
optional v40 target build if none exists and no build is active. Other dirty
files were preserved. No production `ndo_stop` binding or device test.
Local uncommitted follow-up checks MBSS post-DOWN vendor count against other
stable OWNED references before retiring the close ticket. An injected extra
count writer is refused; local and fresh v40n generated-header C11 fixtures
passed. Batch this with the next coherent IoT candidate change; it is not in
`b2dce05` or current #605 CI and has no target evidence.
Correction: #605 and its ABI run passed on `b2dce05`; the count follow-up
was committed/pushed as `3041f7f`. Ordinary #606 (`40264642881`) and ABI
`40264642807` started on the new HEAD. Once #606 is terminal, verify it and
dispatch one optional v40 target run on `3041f7f` if none exists. No checked
`ndo_stop`, recovery worker, production IoT image or router acceptance yet.
Build #606 and ABI both succeeded on `3041f7f`; one optional v40 run
`40265901025` was dispatched on the same HEAD. Source recheck found MBSS
remove calls unregister under RTNL and immediately frees the netdev; an
ignored failed `ndo_stop` result cannot protect the retained recovery owner.
Join/reconcile before free and adapter-release gating remain mandatory. See
the PCI-remove evidence note. Do not start an equivalent v40 run while this
one is live.
Manual v40 run `40265901025` subsequently succeeded on `3041f7f`.
`artifacts-607-v40/target-compile-result.json` and the matching module hash
prove isolated target compilation only (`target_compiled: true`,
`production_installed: false`, `runtime_verified: false`). The checked
MBSS/down symbols are present. Continue with retained recovery owner join
before MBSS unregister/free and PCI adapter-release fence; do not infer
production binding or device acceptance from the successful run.
Local follow-up adds an MBSS removal provenance gate: a stale idle token
cannot authorize unregister unless the open was proven unmutated or the
checked close reached stage 4. `prepare-mt7603-checked-off-candidate.py`
now injects that exact gate into a fresh v40p candidate, rather than leaving
the pinned v39 copy unchanged. Local strict C11 reference/registration and
generated-header fixture passed; caller coverage and Python syntax passed.
No MIPS compile of this follow-up, production `ndo_stop` binding, recovery
worker, adapter fence, or router acceptance yet. Preserve other dirty files.
Focused commit `f708bcb` was pushed with the v40 generator, provenance
header, two C11 fixtures and the generated-header CI gate. The broad local
`netdev-registration.inc` diff was deliberately left unstaged; the generator
injects the new guard into pinned v39 for v40. First CI list after push had
not yet shown a run on `f708bcb`. Check for its queued/running ordinary build
before dispatching one optional v40 run; never duplicate a live run.
Follow-up run list showed ordinary firmware `40268551446` queued and ABI
`40268551314` in progress on `f708bcb`. They are not optional v40 runs.
Both ordinary firmware `40268551446` and ABI `40268551314` succeeded.
One optional v40 run `40330460110` was then dispatched on `f708bcb`;
its WR1200JS job was running at first check. Inspect that exact run and its
target compile artifact when terminal. The generated PCI remove path still
ignores `RtmpPhyNetDevExit` failure and frees the adapter, so source/target
success cannot be treated as safe production IoT removal.
Optional v40 run `40330460110` succeeded on `f708bcb`; artifact
`artifacts-609-v40/target-compile-result.json` and matching SHA-256 prove
isolated MIPS compilation of the provenance-gated candidate. The two changed
generated source hashes match the CI manifest. Production installation and
router runtime remain false. Proceed with checked `ndo_stop`, retained owner
join and PCI adapter-release fence as one coherent lifetime change.

## Sol continuation — PCI reset source gate — 2026-10-27

The generic pinned Linux 4.4 reset API was audited after the MT7621 host/PCI-core review. `pci_reset_function()` may fall through to parent-bus reset, which is not presumed isolated; PCIe FLR also proceeds after a pending-transaction timeout and requires full device reinitialization. The live MT7603 endpoint's FLR/AF-FLR/PM capability has not been captured, and host config access lacks checked transaction completion. Do not bind a generic reset fallback or free live DMA/MMIO/adapter state on checked-close failure.

Next single step: obtain the read-only endpoint config/capability snapshot through the existing fixed `wr1200js-readonly.ps1 -Check pci` path, then decide if a device-specific reset is even eligible for further analysis. No code binding, build, flash, router mutation or GitHub write in this step. Preserve all pre-existing dirty/untracked files; Sol remains the single writer.

Correction: the existing `-Check pci` reports `/proc/bus/pci/devices` inventory only, not capabilities. A fixed `pci-config` check has now been added to the allowlist in `tools/wr1200js-readonly.ps1`. It attempts a read-only first-256-byte dump of readable PCI config files under `/sys/bus/pci/devices/*/config`; it accepts no free-form remote command. Next run this exact check in normal Windows PowerShell and return its full output:

`& "C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\router-guide-work\tools\wr1200js-readonly.ps1" -Check pci-config`

No router command has been run by Codex. The output will tell us whether the endpoint advertises FLR and whether the read-only config path is available; it still will not by itself prove reset safety.

## Sol continuation — missing IoT main-readiness producer — 2026-10-27

A source-wide search of isolated v43c established that IoT open preflights the main 2.4-GHz beacon/queue state and requires `WR_RADIO_READY && main_ready` before `MBSS_OPEN`/`VIRTUAL_IF_UP`. But main `ndo_open` calls `wr_iot_radio_finish_unverified()`, leaving `UNVERIFIED/main_ready=0`, and no call site uses the existing VERIFY helpers to publish readiness. Therefore this candidate has no verified route to IoT BSS_UP and currently fails closed. Evidence is recorded in `docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.

Next: design/bind a bounded main-readiness VERIFY producer after main-open, preserving adapter/netdev ownership, reading registers outside the transition spinlock, and rechecking ticket/epoch/registry generation/vendor count before publishing. Failure must preserve recovery ownership. Keep it isolated until close/recovery and PCI-release failure handling are resolved. The live PCI config output requested for the separate reset-capability question remains pending. No firmware build or router change.


## Sol continuation — isolated v44 main-radio VERIFY producer — 2026-10-27

Generated and checked an isolated v44 source candidate for the missing main-radio readiness producer. Focused structural/order checks, the existing strict C11 virtual-open claim fixture, Python syntax, and scoped whitespace checks passed. The candidate performs observer reads outside the transition lock and revalidates the VERIFY ticket/generation/owner before readiness; HNAT/queue admission remains after that gate.

**Do not integrate yet:** failed VERIFY returns `ndo_open` failure after virtual-UP ownership was claimed, while no failed-open recovery owner is bound. The retained owner therefore has no demonstrated drain path; PCI adapter-release safety is also unresolved. The current Windows command environment has no MIPS cross-compiler, so this candidate is not target-compiled. No firmware build/image or router test was performed. Next: resolve failed-open ownership/recovery and PCI release together before integration. See `docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`. The separate live PCI config/capability output remains pending.

CI was checked read-only at 2026-10-27 17:27Z: firmware build #635 (`40538660394`) and ABI run (`40538660378`) succeeded on published SHA `84b2f12d2b653057e6806c824e7123757161a191`; newest monitor run `40543253994` was skipped. Current local HEAD is `4d8373e7b5c24c1ef2d551cff266aa141e26df8d`; the listed CI results predate it and do not validate v44. No workflow was dispatched.


## Sol continuation — live PCI capability evidence — 2026-10-27

The corrected fixed `pci-config` helper successfully read 4096-byte PCI config spaces on the router via SSH. MT7603 `14c3:7603` (`0000:01:00.0`) and MT7662 `14c3:7662` (`0000:02:00.0`) both expose PCIe v2 endpoint capabilities with Device Capabilities `0x00008fc0`; standard FLR bit is clear. Their standard capability lists have no AF capability, so AF-FLR is absent. PMCSR `NO_SOFT_RESET` is clear, making Linux 4.4 PM-reset a source-level candidate subject to device state and quirks, but its return does not verify config transactions, DMA drain or radio reinitialization. No reset/device state change was attempted. See the evidence note for raw offsets and pinned source links. Next: evaluate PM-reset only as part of a complete checked recovery sequence; do not release DMA/MMIO/adapter resources on the API return alone.

## IoT checkpoint — PM-reset is not a recovery receipt — 2026-10-27

Latest continuation reviewed the exact pinned Linux 4.4 source from the local
bare snapshot and correlated it with the live read-only PCI snapshot. MT7603
`14c3:7603` and MT7662 `14c3:7662` expose neither FLR nor AF-FLR. PM capability
is present and NO_SOFT_RESET is clear, but `pci_pm_reset()` only toggles D3hot
and D0 with delays and returns success without config readback or device-ready
verification. The MT7621 PCI config callback itself returns success after PCR
MMIO accesses without reporting a checked transaction timeout. Generic
`pci_reset_function()` requires full endpoint reinitialization and may fall
back to slot/parent-bus reset. Therefore no reset result can authorize freeing
DMA/MMIO/adapter ownership. Keep IoT candidate isolated; no driver was edited,
no reset/build/flash/reboot was run, and router configuration remains unchanged.

Evidence: `docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.
Next single technical step: continue specifying an adapter retirement/recovery
owner that fences all interfaces, joins workers/callbacks, proves device-defined
DMA quiescence, and only then permits release. Do not use PM-reset success as
that proof. Preserve all current dirty/untracked worktree entries; no commit or
push was made. Existing 2026-10-27 CI runs #635/ABI are on the older published
SHA and do not validate current local candidate.

## Queued Sol task — WR1200JS BusyBox applet/version check — 2026-10-27

Read-only device evidence: `busybox hexdump -C -n 4096` worked through the
fixed PCI-config helper; separate `od` is not installed. This confirms only the
running router command path, not the BusyBox packaged in the selected firmware
image. Sol should, at the existing target BusyBox audit stage, identify the
image's BusyBox version/source revision and effective `.config`, hash the ROMFS
binary, inspect applet links/options for `hexdump` and `od`, and compare with
the live output. Record a reproducible conclusion on whether the helper command
works on that exact image. Preserve read-only allowlisting and do not change
router state. This is queued under the existing BusyBox audit and does not
change priority: first continue the open IoT recovery/retirement lifecycle gate.

## Sol continuation — failed main ndo_open recovery semantics — 2026-10-27

Source audit of pinned Linux 4.4 `net/core/dev.c::__dev_open()` confirms that
failed `ndo_open` clears START, never sets IFF_UP, and never calls `ndo_stop`.
The isolated v44 main callback can fail after AP main-open: virtual-UP failure
retains an `UNCERTAIN_OPEN` record; main VERIFY failure leaves an `OWNED` record
with `main_ready=0`. Both preserve the callback's manual module pin. There is no
`dev_close()` retry path for either state.

Next IoT implementation gate: design/bind a deferred main-open recovery owner
that keeps netdev/module/adapter lifetime, starts after the callback leaves
RTNL, validates registration generation/open token/state, admits a checked main
close, and retains everything if checked physical close is not verified. PCI
remove must join it; PM-reset cannot substitute for DMA/quiescence proof. No
recovery owner or production binding has been implemented. Evidence and detailed
sequence: `docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.
No source driver, image, or router was changed.

## 2026-10-27 IoT main-close receipt checkpoint

Sol strengthened `main-stop-owned.h`: main-close completion now requires an
exact checked-DOWN stage-3 receipt, retires the matching ticket and writes
stage 4 only after consuming the record. Strict main-stop and dependent
failed-open-recovery host fixtures pass. Continue with the real stage-3
producer and checked main-close executor in the isolated driver candidate,
then worker/PCI binding. No image or router proof. Evidence:
`docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.
No commit, push, firmware build or router change in this checkpoint.

## 2026-10-27 IoT main-close source checkpoint

Sol rechecked generated v44 `os/linux/rt_main_dev.c`: main `ndo_stop` remains
legacy (`RTMPInfClose` / `VIRTUAL_IF_DOWN` / unconditional module pin drop).
The VERIFY checker passes, but adjacent manifest says recovery and PCI gates
remain unbound. Next source task is a ticketed, staged checked main-close
continuation before any failed-open worker binding. Do not route the retained
owner through legacy `MainVirtualIF_close`. Evidence:
`docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.
No driver/image/router change, commit or push in this checkpoint.

## 2026-10-27 IoT recovery module-pin checkpoint

Sol made worker join an explicit prerequisite to marking the original main
open module pin released. Strict host fixture rejects release before join,
missing release and duplicate release; it passes. This remains a caller-evidence
contract, not a bound workqueue or actual `module_put`. Preserve the pin and
adapter/netdev owner until a real worker is joined and checked close is proven.
See `docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.
No commit, push, firmware build or router change in this checkpoint.

## 2026-10-27 IoT recovery retry/PCI stop checkpoint

Sol added explicit bounded requeue and PCI stop transitions to the isolated
failed-main-open owner. The strict host fixture confirms an unresolved owner
blocks PCI child-teardown completion even after work join. A stopped owner
cannot safely release resources merely because the worker stopped. Continue
with actual workqueue, callback and PCI-remove binding; no driver/image/router
acceptance is implied. Evidence is in
`docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.
No commit, push, firmware build or router change in this checkpoint.

## 2026-10-27 IoT main recovery close-count checkpoint

Sol tightened the isolated `CLOSE_INCOMPLETE` recovery action: it now requires
the recorded vendor count and a registry with exactly one `CLOSING` owner,
rejecting changed or ambiguous references. The strict host fixture passed.
The kernel worker/PCI join are still unbound; do not treat this as driver or
router acceptance. Evidence: `docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.
No commit, push, firmware build or router change in this checkpoint.

## 2026-10-27 IoT bridge ownership checkpoint

Sol confirmed the isolated bridge candidate already rejects foreign `ra2`
membership and rechecks owned `br-iot` before/after BSS up. Do not duplicate
this guard. The pinned RC source attaches only main/guest macros to LAN;
the exact pinned upstream header maps them to `ra0`/`ra1` for WR1200JS.
Check resolved defines again in final build/image inputs before acceptance.
Source evidence is in
`docs/evidence/WR1200JS-IOT-ACTIVATION-GAP-2026-10-21.md`. The primary open
recovery-owner and production activation gaps remain. No firmware/router
change, commit or push in this checkpoint.

## 2026-10-27 lekswrt reference checkpoint

Sol inspected the pinned lekswrt Prometheus donor and documented the useful
build-menu concepts, WSL limitation, external theme ZIP and unsafe-for-our-
offline-build operations in `docs/donor-audits/LEKSWRT-PROMETHEUS-2026-10-27.md`.
The final-stage plan now includes a non-flashing WSL 2 build launcher candidate.
This is documentation only; continue the current IoT work before Mi Mini and
offline build implementation. No build, router action, commit or push here.

## 2026-10-27 IoT main-close stage checkpoint

Sol added host-only stage 1/2/3 gates around the void `RTMPInfClose` and
checked DOWN receipt. Strict main-stop fixture passed, including replay and
physical-close rejection cases. Continue by binding the real checked close
executor to the single adapter lock and deferred recovery owner; do not claim
driver/image/router acceptance from the host fixture. Evidence:
`docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.
No router change, firmware build, commit or push in this checkpoint.
The deferred-owner fixture now exercises the same preclose/checked-DOWN path:
stage 1 blocks retry, stage 2 allows continuation, and stage 3 precedes pin
release. Strict MinGW GCC passed. This remains host-only composition.
Preclose admission now rechecks the exact main owner, all other active
references and vendor count under the intended shared lock. A RESERVED child
or count drift is rejected by the host fixtures. Production binding still
needs an atomic vendor-count sample and all caller families on that lock.
The v44 source review changes the next integration order: failed readiness
returns from main `ndo_open` with its pin retained, and the kernel will not
call `ndo_stop`. First bind and join the deferred recovery worker with adapter
and netdev lifetime; then share one checked close executor with normal stop.
Do not infer physical quiescence from checked virtual DOWN alone.
The v44 PCI remove ignores `RtmpPhyNetDevExit` failure and frees the adapter;
probe unwind also reaches adapter free. Before worker binding, fence all new
queues, join after unregister callbacks can no longer enqueue, and gate both
free paths on actual child/physical quiescence. The hook map is recorded in
the v43 evidence file. No source candidate was installed by this audit.
The host PCI retirement contract now blocks release until a final work join
after main-netdev detach, with no deferred owners. Both affected strict GCC
fixtures passed. The join still needs a real kernel operation and queue fence.
The deferred recovery callback can now record a completed module decrement
before its own work item is joined; only an external joined owner can reset
the record. Strict recovery fixture passed. No actual module decrement or
kernel worker is performed by the host helper.
Recovery queue admission checks `radio.retiring`: ordinary new work is
blocked, while the PCI remove owner may enqueue a pre-existing acquired-main
close for unregister. The host fixture rejects missing remove provenance and
uncertain-open use. Production must prove the removal owner and hold the
shared lock through admission and actual enqueue; this is not yet bound.
Fresh pinned-source queue/ACK assembly completed with this corrected gate;
the output is a partial candidate, not a buildable or installed driver.
Sol added initialized main recovery-owner storage to the isolated adapter
generator and carried its headers through the full queue assembler. Fresh
pinned-source assembly and generated main-open/close host fixtures passed.
Next bind the real work item only with the checked close executor and both
remove/probe-unwind join fences; this candidate still has no workqueue.
Sol tightened the host-only main close recovery action on 2026-10-28:
CLOSE_UNCERTAIN reconciliation requires the exact post-DOWN vendor count
and registry match. Strict GCC fixture and scoped diff check passed.
The kernel worker and PCI lifetime joins remain the next implementation gate;
no driver image or router state was changed by this step.
PCI remove source gate was tightened on 2026-10-28: an unrelated nearby
conditional no longer counts as checking the fallible root detach. Synthetic
checks passed; the partial candidate still reports three open release gates.
Next bind the actual worker and both PCI joins, then rerun the gate and target
compile before considering production driver installation.
Probe-unwind gate added on 2026-10-28: `check-pci-probe-worker-unwind.py`
rejects the current candidate because it has no adapter-owned recovery work
and frees the adapter after attach failure without a synchronous work join.
The gate itself passed Python syntax check and produced those two expected
open findings. Bind/join the worker on both probe failure and PCI remove;
neither path is accepted for production yet.
Normal worker completion also needs an external reap handshake: current
`wr_iot_main_recovery_complete` requires a joined work item, and the callback
cannot join itself. Do not reset the owner while the callback is still
running or allow a new `schedule_work` against that item. Prove this ordering
with a host interleaving fixture before binding kernel callbacks.
The host contract now enforces that join prerequisite in
`wr_iot_main_recovery_requeue(owner, max_attempts, previous_work_joined)`.
Strict main-open and main-close recovery fixtures passed with an unjoined
rejection and a joined retry. The boolean is caller evidence only; actual
Linux worker join, scheduling serialization and PCI lifetime binding remain
unimplemented.
The owner now also records rejected `schedule_work` through
`wr_iot_main_recovery_schedule_result`: it retains the ticket/pin and requires
join before retry. Both strict GCC fixtures passed with that path. The future
Linux binder must use the actual return value under the same admission lock;
host booleans alone are not runtime evidence.
Retry accounting now counts rejected submissions as well as begun callbacks,
requires exactly one recorded schedule result per queue event, and refuses to
begin without accepted submission. Both strict GCC fixtures pass; the
two-failure budget case uses an independent host owner. The Linux binder must
pass the actual schedule_work result and preserve the same adapter-lock order.
Shared main-close continuation is now present in the isolated reviewed
fragment and new 64-file composed partial bundle. Strict GCC extraction
tests forced a failed first DOWN and resumed the exact ticket without a
second RTMPInfClose; all manifest hashes match. The callback still must
queue recovery on failure, and the worker must use this helper with pinned
lifetimes before the PCI probe/remove joins and target compile can pass.
The partial main close is now split into shared admission, fresh-claim
preclose and continuation. Both `ndo_stop` and a future acquired-open worker
can use one implementation; strict host fixtures and v3 composed bundle pass
(64 hashes). Preclose is caller-controlled one-shot, so the worker must never
invoke it for a retained stage-1 uncertain or stage-2/3 ticket. Actual queue
and lifetime binding remain open; do not install this partial driver.
Main `RTMPInfClose` is now guarded by a locked one-shot `close_running` claim
before the void call. Reentry after failure cannot replay preclose; stage 1
remains uncertain if the void call does not return. Strict host fixtures and
the v4 partial composition passed (64/64 hashes). This still needs a Linux
worker with exact-ticket queueing and the PCI lifetime joins before target
compile or production use.
The partial source now has `wr_iot_main_recovery_execute`, shared by the
reviewed close stages. The host fixture proves failed `ndo_stop`, failed
worker DOWN, joined retry and exact-ticket completion without preclose
replay; acquired-open execution also passes. v6 composition has 64 matching
hashes and is explicitly nonproduction. Next bind work_struct and queue
admission with real netdev/adapter pins, then normal reap and both PCI joins;
do not treat host execution as target or router acceptance.
Sol staged v7 from that partial bundle: adapter-owned `work_struct`, callback,
prepublication initialization and `cancel_work_sync` before the probe-failure
free. The probe source preflight passes and all 64 manifest hashes match;
`production_installed=false`. The PCI remove gate still has three open
findings. Next bind queue admission with actual `dev_hold`/`dev_put` and
adapter-release ownership, then external reap and PCI remove joins outside
the lock. Target compilation and fault testing must precede installation.
Sol staged a root-detach guard in isolated v8b: PCI remove checks
`RtmpPhyNetDevExit` directly and retains adapter memory on failure. Its
fallible-detach source finding cleared; two work-join/release findings remain.
Probe-unwind preflight and 64/64 hashes pass. Do not queue recovery yet:
normal completion/reap and PCI remove adapter lifetime are still unbound.
Next implement these ownership transitions, bind queue admission with real
netdev references, and target-compile the composed driver.
Sol staged v9 from v8b: retirement fence plus stop request under the shared
lock, then `cancel_work_sync` outside it before root detach, and another join
after unregister may call `ndo_stop`. Remaining deferred owners block adapter
free. Probe-unwind and 64/64 hashes pass; the PCI release source gate now
reports only the missing ordered release-claim/quiescence path. This does not
reap a retained owner or prove DMA/callback quiescence. Bind those actual
receipts before queue submission or installation; no target compile yet.
The strengthened source preflight distinguishes v8b (missing two joins) from
v9 (joins present, release claim still missing). It is not runtime evidence.
Sol staged v10 with actual PCI bus-master clear/readback and Transaction
Pending config reads behind checked physical-stop milestones. The existing
observer fault fixture passes and all 65 manifest hashes match. The adapter
release claim remains unbound: callback/IRQ/ring quiescence and child/main
ledger completion must come from real producers, then be checked atomically
with final release. Do not treat PCI config-space clear as DMA proof or ship
this isolated candidate; target compilation has not run.

2026-10-29 overlay correction: older manifest marks four required include/*.inc
as fixtures. Initial scratch output omitted them; superseded by overlay2.
Generator now excludes only seven root test fragments and applies all 64
driver files, including those four required include fragments. Verified present.
