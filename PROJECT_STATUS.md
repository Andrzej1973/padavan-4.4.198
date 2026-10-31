## 2026-10-31 checkpoints published; Sol receives execution ownership

The owner requested a logical checkpoint, GitHub publication and transfer to
Sol. The code checkpoint is
`61c634b5508ffc29648e522da8444c882cf0abc7`
(`feat(wr1200js): checkpoint IoT ownership and Modern WebUI`): 506 files,
39,105 insertions and 235 deletions. This handoff record is the direct child of
that checkpoint and is published immediately after it; the remote SHA must be
verified again after push rather than inferred from this file.

The checkpoint publishes the full IoT ownership/retry toolchain and its
distilled evidence, including auxiliary scheduler82. The final host replay
passed all 86 extracted variants, but target compilation, ROMFS/image
inspection, callback/DMA quiescence and device runtime remain unproven. Known
open IoT issues include unbound WDS/peer completion identity, retained failed
insertions, incomplete timer/callback joining and no single proven lifetime
owner across all adapter, peer, radio and PCI paths.

The Modern WebUI checkpoint contains the full eleven-page local preview and a
repeatable production-shell installer with authenticated read-only
`/wr_modern.json`. The current local recheck passed Python compilation,
JavaScript syntax, DEMO HTTP verification, production static-shell validation,
host live-JSON generation, production-shell HTTP verification and the IoT
scheduler fixture (release build; this MinGW environment has no ASan runtime
library). The production shell is not yet invoked by the firmware workflow,
MIPS-compiled, present in a verified ROMFS or tested on the router.

Public WAN/ISP addresses and VPN endpoint details were redacted from publishable
evidence. Local-only SSH/PCI evidence remains untracked and ignored. Reproducible
scratch was removed: `.iot-local-check`, extracted CI artifacts, temporary
build directories, local test directories and Python/Node caches. Tracked
candidate content was preserved.

Sol now owns continuation. Required order: accept the role after checking the
remote SHA; complete IoT lifecycle/ownership and its target/feature builds;
verify the production Modern shell and Zapret2; inspect the final TRX, checksum,
ROMFS and gates; only then request separate authorization for device testing.
Band Steering must remain, IoT is mandatory in the release objective and CAKE
stays excluded. No flash, reboot, service restart or router configuration
change is authorized by this handoff.

## 2026-10-31 Modern production shell prepared; host/browser checks PASS

Added `prepare-production.py`, `wr-modern-http.inc` and a live-mode browser
fixture. A disposable pinned source install produced `/modern/index.html`,
private Modern assets and authenticated `/wr_modern.json`. The JSON route emits
selected NVRAM/system fields, memory and uptime without passwords, keys,
certificates or logs. Host GCC emitted valid live JSON; production-shell browser
loaded all assets in `LIVE READ-ONLY` mode with no console error. This is not yet
wired into firmware build, MIPS-compiled, ROMFS-inspected or device-tested.

## 2026-10-31 Modern WebUI full reference-structure preview PASS

Local Modern preview now covers11 informational pages plus Wi-Fi/IoT routes.
Dashboard adds band switcher, DEMO WAN traffic graph, CPU processes, explicit
`Н/Д` temperatures and corrected USB status. All routes rendered without
console errors; desktop and390x844 layouts had no horizontal overflow.
`node --check`,15-route Wi-Fi check, reference-image check and
`verify_preview.py` passed. This is local DEMO only: no production ASP/CGI,
NVRM, service, firewall, DHCP, IoT runtime or firmware integration is claimed.
Verification: `tools/webui-preview/VERIFICATION.md`.

## 2026-10-31 DeepSeek resumed IoT with auxiliary retry scheduler82

DeepSeek accepted the single-writer role after local and remote HEAD matched
`13ce368`. The pre-existing 71 tracked modifications and 467 untracked entries
were preserved. Fresh candidate81 passed85 host variants. The new exact-ticket
APCLI/Monitor scheduler82 binds `dev_hold`, the original module pin, an adapter
release fence, RTNL retry, locked completion and PCI stop/join behavior.
Candidate82 passed86 full host variants; a fresh whole-chain reproduction has
585 files with0 differences from tested bytes and passed6 focused replay
variants. Evidence:
`docs/evidence/WR1200JS-IOT-AUX-RETRY82-2026-10-31.md`.
Target compile, image, callback/DMA quiescence and runtime remain unverified.
No router change, flash, reboot, commit or push occurred.

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

# Current project status — 2026-10-25 (updated)


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

## 2026-10-30 fresh full40 replay and peer-table writer inventory

Previous stage40 was real source/test progress. Fresh preparation now passed
ALL40 stages in peer-retirement-chain40-20261030/legacy-close-result. All560
files match incremental legacy-close-result40b-20261030, which passed42 extracted
host variants. Additional23 composed variants passed against the fresh tree.
This supersedes earlier notes saying last full replay36. No target build or
production installation; full source preparation is not a firmware build.

New audit-peer-table-writers.py records32 lexical sites across8 files, with
comments/strings excluded. Not full alias or effective-feature analysis.
Critical additional admission paths: RTMPInsertRepeaterMacEntry independently
selects/resets/publishes same Content/TR slots under MacTabLock, cancels old
timers and ignores hardware add status. Easy Setup ez_set_entry_apcli_mt7603
mutates a looked-up peer type without local MacTabLock. Fresh init and both
close paths clear entire MacTab. Owner state must live outside cleared memory.

Evidence: docs/evidence/WR1200JS-IOT-PEER-TABLE-WRITERS-2026-10-30.json and
docs/evidence/WR1200JS-IOT-FULL40-AND-WRITER-AUDIT-2026-10-30.json.
Next bind adapter-owned mutation ownership across BOTH insertion paths,
normal/reset/WDS deletion, Easy Setup type mutation and full table clears.
Reset reservation and failed-setup preflight must be one MacTabLock critical
section; release lock before waiting. Failed/retried ownership must not reset
implicitly. This owner is not yet implemented/bound. No false atomicity claim.
No router change, firmware build/dispatch, commit or push in this step.

## 2026-10-30 legacy close result through native/OS_ABL and endpoints (stage40)

Pinned prepare-legacy-close-result.py changes isolated legacy RTMPDrvClose to
INT status, its native declaration and OS_ABL ops return type consistently.
rt28xx_close maps failure to -EIO before diagnostic exit. PCI suspend refuses
before module decrement/power-down tail. Old virtual-down ioctl and wrapper
propagate failure; both remaining callers Monitor/APCLI check before module
decrement. The count already decremented to zero is not restored as a false
active interface. Earlier close/HNAT/radio/PM side effects remain partial.

Latest candidate legacy-close-result40b-20261030. 42 extracted optimized strict
host variants passed, including whole legacy close/rt28xx bridge, actual ops
field/prototype/assignment/macro dispatch with mocked struct, whole Monitor and
APCLI close bodies; native/ABL, WIFI_DIAG and HNAT variants. PCI test covers
the close guard seam, not the whole suspend function. This is NOT binary ABI,
kernel scheduling/lifetime or hardware proof. All affected target modules
must be rebuilt together; no mixed-module compatibility claim. Evidence:
docs/evidence/WR1200JS-IOT-LEGACY-CLOSE-RESULT40-HOST-2026-10-30.json.

Next exclusive reset/insertion and retry ownership: legacy close still has no
shared retained retry owner; PCI/endpoint pre-close effects are not rolled back.
An ndo_stop error does not establish netdev/adapter lifetime. Inspect these
before cleanup binding/release acceptance. Last complete preparation replay36;
full40 replay/target build/runtime not performed. Local edits only, no router
state change, firmware build/dispatch, commit or push in this step.

## 2026-10-30 AP shutdown refusal through checked physical/MBSS close (stage39)

Pinned prepare-ap-shutdown-result.py changes isolated APShutdown/prototype to
BOOLEAN. Legacy RTMPDrvClose stops its local teardown on refusal. Checked
wr_iot_drv_close_checked marks partial shutdown_stage=3 under transition lock
and returns failure before task/Mlme/mgmt/ring teardown; subsequent same-ticket
call cannot replay stage zero. Earlier operations are not rolled back.

37 extracted strict optimized host variants passed. Tests include whole
APShutdown and whole checked-close bodies with injected lower operations,
PCI/non-PCI + WDS/IGMP/WNM variants, failure/retry, virtual-down bridge and
MBSS last-close retaining WR_REF_CLOSING/module reference. The close bridge
does not mark notification complete on refusal. Predecessor38 fixture passed.
Initial host shim lacked RT_DEBUG_TRACE; fixed and whole suite rerun passed.
Evidence: docs/evidence/WR1200JS-IOT-AP-SHUTDOWN-RESULT39-HOST-2026-10-30.json.
Full39 replay, target compile, Linux synchronization and runtime unverified.

Next legacy boundary: RTMPDrvClose remains VOID (including OS_ABL function
pointer), and rt28xx_close in os/linux/rt_main_dev.c still reports success after
its early return. Inspect that ABI/caller path before accepting release.
Higher scan/ATE/SDIO/VOID parents, reset/insertion exclusion and failed-peer
cleanup ownership still open. No production driver installation, router state
change, firmware build/dispatch, commit or push in this local step.

## 2026-10-30 AP stop result and 26 direct caller guards (local stage38)

Pinned prepare-ap-stop-result.py converts APStop/APStopBssOnly and prototypes
to BOOLEAN in isolated candidate ap-stop-result38-20261030. Reset refusal now
returns FALSE; successful tail TRUE. All 26 APStop call sites in this donor
tree check the result. Setters/scans leave with FALSE; ATE returns -1; USB
rescan returns NDIS_STATUS_FAILURE; VOID parents leave before later local
actions. Ioctl authentication/WEP cases set -EBUSY and break the switch. WSC
UFD preserves filename freeing by setting Status instead of early exit.
CMDHandler breaks its command switch and reaches normal queue cleanup.

30 extracted strict optimized host variants passed. New fixture exercises
26 extracted call-site branches plus two reset checkpoints, with mocked stop/
startup and adapted void-return sentinels. Not full enclosing function, lock,
allocator or scheduler execution. UFD free/queue cleanup ordering source
assertions passed. Initial fixture formatting warning fixed without suppression.
Evidence: docs/evidence/WR1200JS-IOT-AP-STOP-RESULT38-HOST-2026-10-30.json.
Full38 replay and target compile not performed. All stage38 work local.

Next: APShutdown still VOID; two callers in common/rtmp_init_inf.c continue
task/thread/resource teardown after it returns early. Propagate refusal there
before accepting release; review outer scan/ATE/SDIO/VOID parents too. Earlier
side effects (including MlmeRadioOff before APStop in APShutdown) remain
partial; reset/insertion exclusion and DMA/TxS lifetime still open. No cleanup
binding, production driver install, build/dispatch, router changes or push.

## 2026-10-30 checked reset results and direct callers (local stage37)

Added pinned prepare-peer-reset-result.py as stage37. MacTableReset and
MacTableResetWdev now return BOOLEAN in the isolated candidate, including
allocation failure, preflight refusal and deletion refusal. Updated prototypes
and all five direct callers: APStop/APStopBssOnly stop their later shutdown
tail; MAP channel branches and disconnect-all return FALSE on reset failure.
Disconnect-all also checks deletion failure in its optional PMF branch.
Correction to prior notes: ap/ap_cfg.c caller is Set_DisConnectAllSta_Proc,
NOT a PMF setter. Earlier side effects are not rolled back.

29 extracted strict optimized host variants passed, including real reset body
return checks, allocation failure, scoped reset, and extracted disconnect-all
with/without PMF. Direct APStop guard ordering is source-asserted only; no
full APStop execution or target compile. Source preparer pins all five changed
files. Full36 replay remains verified; fresh full37 replay not performed.
Evidence: docs/evidence/WR1200JS-IOT-RESET-RESULT37-HOST-2026-10-30.json.

Next: APStop/APStopBssOnly still VOID; audit their callers and prevent restart,
free or false success after refusal. Then establish exclusive reset/insertion
ownership. Current preflight is only an observation; timer/adapter/module,
DMA/TxS and reuse lifetimes remain unaccepted. No cleanup binding, production
driver change, router change, build/dispatch, commit or push in this step.

## 2026-10-30 failed-peer delete/reset refusal, full chain36 replay

Published timer research checkpoint 9af5697; remote branch SHA confirmed. It
contains standalone helpers/tests only, not production driver integration.

Local stage36 now rejects ordinary deletion of an observed failed MT insertion
before timer/vendor cleanup. Both reset loops preflight failed setup metadata
under MacTabLock and stop if MacTableDeleteEntry refuses, preserving terminal
table/BSS counters. This is observation/abort, NOT an atomic reset transaction.
Normal-path EAPOL timer release can precede a later deletion refusal.

Fresh full36 preparation passed. All 560 files match the incremental stage36
candidate. 27 extracted and 23 composed optimized strict host variants passed;
kernel/MMIO/layout operations are mocked. Evidence:
docs/evidence/WR1200JS-IOT-FAILED-PEER-RESET36-HOST-2026-10-30.json.
No target build, driver installation, firmware build or router state changes.
Stage36 and this status update remain local, not part of 9af5697.

Next: checked reset failure propagation and exclusive reset/insertion ownership.
MacTableReset/MacTableResetWdev are still VOID. APStop and APStopBssOnly continue
radio shutdown after reset; PMF setter can report success; MAP channel paths
continue reinitialization. Do not bind failed-peer cleanup until callers honor
refusal and lifetime is owned. Reset preflight can race with a new insertion;
DMA/TxS, old reuse and partial hardware recovery remain open. Goal incomplete.

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


## 2026-10-29 successor verification consolidated

- Unified host suite including bounded checked-close passes; full receipt,
  caller/registration audit, TxS and post-open results saved. Scope and
  remaining target/hardware gates documented in
  docs/evidence/WR1200JS-IOT-V25B-SUCCESSOR-2026-10-29.md.

## 2026-10-29 later successor caller coverage

- v25b generation/readiness successor passed existing five-family virtual
  caller and five checked-registration-path source audit. Independently
  checked all 71 file hashes against its receipt: exactly two declared files
  changed. This proves bounded source coverage/preservation, not runtime
  serialization or complete hardware TxS retirement.

## 2026-10-29 later close reconciliation

- v25b already contains the checked-close poll bound/stage3 retention.
  Accepted both reviewed counter names in source extractor; successor's
  own-header close fixture passed strict GCC. No overwrite of later close
  recovery logic was needed. Legacy caller binding/target tests remain open.

## 2026-10-29 candidate reconciliation inventory

- Hash comparison mapped 26 changed shared files and eight later-only files
  between regenerated base and v25b. Saved later candidate includes recovery,
  steering and producer gates absent from base; no safe wholesale replacement.
  Exact local reconciliation report saved for subsequent stage composition.

## 2026-10-29 admission count-mismatch regression

- Added successful readback with extra vendor reference to final-source
  admission fixture. It verifies owned reference retention plus UNVERIFIED
  phase/main_ready false on count mismatch. Strict optimized GCC run passed
  against regenerated candidate headers; hardware/target acceptance pending.

## 2026-10-29 post-open intended variant checked

- Saved v25b post-open fixture passes with WR_IOT_V40; it also passes with
  current virtual-open-claim.h overlaid temporarily. Verified the header delta
  contains only invalidated READY demotion. Later-chain regeneration and
  target/device checks remain pending.

## 2026-10-29 post-open verification scope corrected

- Standalone post-open fixture expects later steering-ready/intent-race
  stages, absent from fresh base queue bundle. Located their separate v14
  successor preparers and manifest requirements. Do not weaken fixture to
  force a base-bundle pass; later-stage composition remains required for
  steering readiness and compensation acceptance.

## 2026-10-29 early close-regression diagnostic

- Existing final-source close extractor now refuses missing dequeue bound
  before executing its fixture. Positive current-source and negative removed-
  bound checks passed, avoiding the previously observed CI-test hang.

## 2026-10-29 MT_MAC open/close fixture aligned

- Wi-Fi HNAT compile variant also passed strict optimized host GCC/exit0.
  Evidence consolidated in WR1200JS-IOT-MBSS-FIXTURE-ALIGNMENT-2026-10-29.md;
  this does not establish actual offload traffic or target execution.

- Added owned main registry reference matching initial vendor count, current
  MBSS begin-close provenance, and checked ticket retirement instead of
  finishing the already retired ticket again. Final-source fixture passes
  strict optimized GCC across pending/fault DMA and TxS cases; successful
  IoT close retains main ownership/count. IO is injected, not device proof.

## 2026-10-29 invalidated BSS readiness fix

- Full candidate regeneration completed (full-queue-20261029e). Admission
  fixture using its final generated headers passed strict optimized GCC;
  reset/readback correction is now verified through source preparation.
  Target and device acceptance remain outstanding.

- Observed BSS finish now demotes READY after reset/main-down invalidates
  readback. Ownership remains for recovery. Updated admission host fixture
  passes with reset/close injection and failed BSS observation; current local
  headers used, full source regeneration/target compilation pending.

## 2026-10-29 MT_MAC fixture drift identified

- Final MT_MAC open/close host fixture compilation failed on stale injected
  BSS-observer/count/wait interfaces. Base admission fixture needs alignment
  with current contract before claiming MT branch tests. No target failure
  inferred; exact missing interfaces recorded in handoff.

## 2026-10-29 last MBSS close fixture updated

- Updated stale fixture to bind MBSS family, use actual begin-close generation
  capture and model ticket-wait wakeups. Final-source last-close/physical-chain
  fixture now passes strict optimized GCC, including retained reference on
  failed join/radio close, one wake on success and none on failure. Hardware
  and worker actions remain injected; no production acceptance.

## 2026-10-29 live ABI checkpoint

- GitHub reports successful ABI #586/run 40562762027 on fcf45d7. That is
  the committed baseline, excluding current uncommitted IoT fixes. Recent
  successful Agent build failure monitor runs are not firmware/ABI results.
  No new workflow was dispatched by this check.

## 2026-10-29 bounded dequeue close fix

- Final-source close-chain fixture also compiled and exited 0 on the new
  bundle; worker/hardware actions remain injected. Detailed evidence and
  elapsed-time limitations are recorded in
  docs/evidence/WR1200JS-IOT-DEQUEUE-CLOSE-BOUND-2026-10-29.md.

- Confirmed real generated unbounded DeQueueRunning wait. Candidate generator
  now refuses after 1000 delay polls, retains shutdown uncertainty stage 3,
  and does not proceed to join/free. Regenerated full-queue-20261029d; existing
  final-source checked-close fixture compiled with strict optimized GCC and
  exited 0, including timeout/no-free/no-retry checks. Target/runtime pending.

## 2026-10-29 generated close lock-order review

- Current close wrapper releases transition lock before vendor close and
  DMA/TxS snapshots; it does not wait for RX while holding BcnRingLock.
  Zero snapshots still lack a hardware late-report barrier before virtual
  down/reference retirement. Keep production exclusion; lock-order review
  does not prove selective close safety.

## 2026-10-29 PCI RX lock-order constraint

- Source confirms RxRingLock spans the common parser and beacon TxS callback.
  Recorded prohibition on waiting for RX/tasklet drain while holding the
  beacon lock, to avoid blocking the callback needed for progress. A real
  bounded retirement implementation and target tests remain outstanding.

## 2026-10-29 TxS parser caller coverage

- Full source shows parse_rx_packet_type is called from PCI RX extraction,
  SDIO and MT_MAC AndesRxProcessCmdMsg. MCU beacon-TxS reachability remains
  unproved; future drain must account for Andes RX or prove exclusion using
  routing and effective flags. Do not equate rx tasklet completion with all
  parser owners drained. Source evidence only; driver unchanged.

## 2026-10-29 beacon macro semantics

- Pinned MT7603 source has one caller of RTMPHandleBcnDmaDoneInterrupt:
  bcn_dma_done_tasklet (rt_rbus_pci_drv.c:575). The MT_INT_BCN_DLY hard-IRQ
  branch schedules that task at line 1595; it does not call the DMA handler
  directly. This removes the direct-hard-IRQ inference for this path only.
  Other lock callers and effective WORKQUEUE_BH still need review.

- Located actual per-unit Kbuild evidence in artifacts-634-v42/merged-capacity.json:
  all nine beacon-lock units report complete preprocessing, complete site
  activity, and MULTI_CORE_SUPPORT=false. In that saved build both SEM/IRQ
  resolve through the BH helper. This corrects an inference from mixed names;
  it does not verify the current regenerated candidate or hard-IRQ contexts.

- Full pinned headers show SEM uses RtmpOsSpinLockBh; IRQ uses that same
  helper without MULTI_CORE_SUPPORT and spin_lock_irqsave with it. The local
  config.mk definition found is conditional on BB_SOC/CONFIG_MIPS_TC3262,
  not evidence of effective WR1200JS flags. Therefore 12 SEM/9 IRQ text sites
  alone do not prove incompatible locking. Obtain effective preprocessing and
  caller context before normalizing macros or claiming safety.

## 2026-10-29 complete-source lock inventory

- Reviewed the manifest's expanded lifecycle/ownership headers and overlaid
  sources, including rt_os_net.h, and refreshed only overlay/base inventory
  counts to 55/37. Strict audit now passes with all 515 pinned files and
  unchanged 21 sites/9 units/12 SEM/9 IRQ requirements. This validates source
  inventory, not compatibility of mixed lock forms or target execution.

- Pinned archive extraction completed: 515 driver files. Raw inventory
  verified 37 base blobs and all candidate SHA256 records, finding 21 lock
  sites in 9 units (12 SEM, 9 IRQ). Strict coverage gate remains unpassed:
  current overlay/base counts 55/37 differ from reviewed 46/32. Evidence:
  .iot-local-check/full-source-lock-inventory-20261029.json. Receipt moved
  outside source tree so it is not counted as a driver file. Do not equate
  this inventory with lock correctness or target/runtime acceptance.

## 2026-10-29 queue manifest source coverage fix

- Added modified include/rt_os_net.h to generator input/hash ledger; fresh
  full-queue-20261029c preparation succeeded. Full-lock auditor then correctly
  rejected the sparse 38-file base against its 515-file coverage gate. Do not
  lower that gate: a complete pinned driver tree is needed for exhaustive
  lock audit. No target/image/device acceptance follows.

## 2026-10-29 full queue source preparation underway

- Resolved nested inputs with nine additional pinned files. Full queue
  preparation completed in .iot-local-check/full-queue-20261029b and wrote
  its manifest. Both final-source TxS status and extended ledger/parser
  fixtures passed strict optimized GCC, requiring generation exhaustion
  refusal. This is a partial source bundle and host evidence; no target
  module, production backend, image or hardware retirement acceptance.

- Retrieved 29 declared source inputs at the pinned revision through GitHub.
  Full queue preparation reached nested radio-errors and stopped at missing
  ap/ap_mbss.c. Its output is incomplete; nested preparer inputs must be
  collected before retrying into a new directory. No image/device changes.

## 2026-10-29 pinned TxS source regeneration

- ABI workflow now runs the extended extracted ledger/parser with sanitizers
  after full queue-candidate preparation, explicitly requiring generation
  exhaustion refusal and saving its diagnostic output. YAML/order validation
  and targeted diff check passed. CI was not launched; the stale-report
  negative witness remains diagnostic rather than acceptance of retirement.

- Resolved extended-fixture composition: it requires the existing Type-1
  handler-snapshot stage after claimed-slot. Applied that stage to the fresh
  source; extended extracted ledger/parser test then passed strict optimized
  GCC with generation-exhaustion rejection. Stale hardware-report/PID reuse
  remains a negative witness. The interrupted earlier test lacked this stage;
  its remaining owned process was terminated. No device operation.

- Applied callback-ledger and claimed-slot stages to the freshly regenerated
  TxS source. The CI-used allocation/cancel/exhaustion fixture compiled and
  passed strict optimized GCC on these actual generated functions. Extended
  parser fixture did not complete locally and was interrupted; no pass claim.
  Full queue composition includes additional stages and remains required.

- Retrieved all four pinned base files through GitHub connector and verified
  their exact Git blob hashes. Full prepare-txs-status-candidate.py completed
  in .iot-local-check/txs-regenerated-20261029, including generation exhaustion
  guard. This is the TxS stage only: full queue composition, target compile
  and hardware retirement proof remain pending. Source copies stay local.

## 2026-10-29 TxS software generation wrap witness

- Existing CI-used `prepare-txs-status-check.py` now requires refusal at
  generation exhaustion with unchanged outputs/free slot. Its extracted
  allocator fixture passed strict GCC on the temporary guard composition;
  the workflow already invokes this extractor. No new CI run was launched.

- Extractor now has an explicit generation-exhaustion expectation for future
  regenerated candidates. Temporary source composition with the exact new
  guard passed strict optimized GCC; old-candidate witness remains available
  by default. Full regeneration and target compilation remain pending.

- Candidate generator now refuses generation exhaustion under the ledger lock
  before mutating slots or outputs. Extracted guard composed into the current
  host fixture passed strict GCC, preserving outputs and releasing the lock
  at UINT32_MAX. Full source regeneration/target build remains pending; the
  existing v25b artifact still contains the old wrap behavior.

- Extended the extracted ledger fixture to force UINT32 generation wrap:
  allocation returns generation 1 again and accepts a cancellation with that
  repeated identity. Strict optimized GCC C11 execution passed. Before binding
  cancellation, require non-repeating identity or checked exhaustion/drain;
  this is separate from hardware report identity. Driver unchanged.

## 2026-10-29 TxS PID quarantine option reviewed

- Re-extracted current v25b ledger/parser and ran the strict optimized C11
  host fixture. The injected stale-report/PID-reuse negative witness still
  reproduces. Hardware occurrence and the required retirement barrier remain
  unproved; this result keeps the production close gate open.

- Finite UINT8 PID allocation rejects when all slots are occupied; permanent
  quarantine would eventually prevent beacon submission. Quarantining only
  uncertain completions does not address the existing normal-completion stale
  report witness. Retain exact-identity/drain gates; no driver change.

## 2026-10-29 HTTP regression CI coverage

- Negative source check confirmed that removal of the session-reset call is
  detected; repeated preparation refused and preserved HTTPD/WebUI bytes.
  This closes the source-guard check only; Linux execution remains pending.

- Added the standalone strict HTTP form fixture to the existing Linux ABI
  request-boundary step with ASan/UBSan. This carries the disabled-request
  extra-field regression into CI; the existing handler fixture also contains
  the new session-reset/replay case. Workflow YAML and fixture selection
  validation passed locally. The workflow was not run or published; Linux
  execution, MIPS linking and device acceptance remain pending.

## 2026-10-29 IoT CGI candidate preserves existing headers

- `prepare-http.py` now refuses differing or linked IoT header/validation
  destinations before its first write. An isolated conflicting-header fixture
  confirmed refusal with original header, HTTPD and WebUI source bytes
  unchanged; Python compilation and targeted diff check passed. No CGI was
  installed in production and the activation backend remains absent.
- The candidate disabled form now rejects SSID/password or any other extra
  fields, accepting only `enable=0` and CSRF token. Strict C11 form fixture
  and isolated positive HTTP preparation passed. The combined request fixture
  needs POSIX `arpa/inet.h` and was not locally runnable on Windows GCC;
  Linux/target verification remains open.
- HTTPD candidate now clears the process-global IoT CSRF token and pending
  body through stock `reset_login_data()` on logout/timeout/reset. Isolated
  positive source preparation and extracted-source check passed; handler
  fixture includes a reset/replay rejection but still awaits Linux execution.
  No production or device change.

## 2026-10-29 Classic IoT guest band navigation

- Source review found a separate Classic guest 2.4/5 GHz shortcut pair in
  `state.js`. The isolated navigation candidate now adds the IoT destination
  beside both main and guest pairs without changing their original handlers.
  The 14-route in-memory check, JS syntax check and targeted diff check pass.
  This candidate remains outside the production workflow; IoT service and
  authenticated Apply are not established.

- Follow-up source check: Classic constructs `TopBanner` and `tabMenu` in
  `body onload`, but the navigation asset is loaded dynamically. The candidate
  now schedules mounting after load handlers so the controls exist. Node
  coverage includes the pre-load and already-complete cases; rendered Classic
  and image checks remain pending.
- Classic source-preparation guard now requires the four original main/guest
  band-button IDs and all twelve page load hooks. Read-only extracted ROMFS
  check found 1 occurrence per ID and 12/12 hooks; Python compilation, Node
  route fixture and targeted diff check passed. No firmware build or router
  change.

## 2026-10-29 IoT TxS sequence identity source check

- In isolated v25b, beacon `NSeq` has no observed consumer in the descriptor
  writer; `txd_3.sn/sn_vld` are not assigned, and received TxS SN is not
  compared with the PID reservation. The software Sequence assignment found
  in `MlmeHardTransmitTxRing` is a separate transmission path. Source alone
  therefore cannot justify an SN-based retirement gate. Hardware measurement
  or a proven drain remains required; no driver/image/router change.

## 2026-10-29 IoT TxS disable option rejected by source

- Audited isolated v25b beacon state flow: DMA completion reaches
  `BCN_TX_DMA_DONE`, while `BcnTxSHandler` sets `BCN_TX_IDLE`; normal beacon
  update and buffer deinit depend on IDLE. Simply disabling beacon TxS would
  break the demonstrated state machine and is not a safe retirement fix.
  Source evidence added to the TxS options report. No driver, image or
  router change; exact report identity or a real drain barrier remains open.

## 2026-10-29 IoT RC marker to activation host contract

- The activation host fixture now raises SIGTERM after RADIO_PREPARE while
  the RC shutdown marker is active. Its injected backend cancellation callback
  reads the pending marker; the next START step is refused, `BSS_UP` is never
  called, recovery completes, and the pending signal remains for RC delivery.
  Strict C11 GCC test passed. This is a combined host model only; no installed
  backend or bounded driver operation is established. WSL is present as a
  command but has no usable distribution in this environment, so Linux
  SIGQUIT/SIGPWR fixture coverage remains in CI.

## 2026-10-29 IoT cooperative start cancellation candidate

- `activation.h` now requires a backend cancellation callback and checks it
  immediately after LOCK, between each START operation, and after final
  observation. The injected C11
  fixture covers cancellation after radio preparation, cancellation after
  BSS observation, pre-start cancellation, missing callback rejection, and failed recovery retaining
  owner lock/snapshot/isolation until a later checked retry. Strict GCC run
  and `git diff --check` passed. This cannot interrupt a blocked backend
  operation, does not bind the RC signal marker or driver owner, and has no
  target/image/device proof.

## 2026-10-29 IoT RC dispatch signal matrix

- Extended the extracted dispatch fixture to inject SIGTERM, plus SIGQUIT
  and SIGPWR where the host defines them. It checks that normal shutdown is
  delivered after dispatch while SIGPWR takes the immediate handler path.
  The strict Windows C11 run passed; Windows does not establish Linux
  SIGQUIT/SIGPWR coverage. Linux CI remains pending. This is still an
  injected host fixture, not production or router behavior.

## 2026-10-29 IoT power-signal boundary

- Pinned RC source maps `sys_exit()` to SIGTERM and `sys_stop()` to SIGQUIT;
  SIGPWR is a separate fatal-handler input. The isolated RC candidate now
  defers only SIGTERM/SIGQUIT and leaves SIGPWR on the immediate stock path.
  Strict C11 admission and injected-dispatch host tests passed after the
  change. SIGPWR can still interrupt activation; fail-closed recovery and
  bounded normal shutdown remain open gates. No production image or router
  change.

## 2026-10-29 IoT RC shutdown end ordering

- Corrected the isolated signal marker so `end()` clears `active` before
  reading/clearing the deferred signal. This closes a lost-signal window in
  the prior local candidate. `prepare-http.py` and `prepare-control.py`
  passed on a local RC/HTTP source fixture with a minimal HTTP Makefile stub;
  strict C11 admission and injected dispatch checks passed again. The actual
  Makefile selection, Linux CI, MIPS compile, bounded backend, and router
  behavior remain unverified. No production or router change.

## 2026-10-29 IoT normal shutdown admission candidate

- Added an isolated RC signal marker: SIGTERM/SIGQUIT received during
  a claimed IoT transaction are deferred until the mailbox result is written
  and cleanup ends; SIGPWR and process faults retain the original handler. The source
  preparer stages the hook only for WR1200JS. A strict C11 host marker test
  and injected dispatch fixture pass; Linux control-channel/source and MIPS
  checks are wired but have not run. A bounded backend/cancellation protocol
  and driver owner remain required before production inclusion. See RC
  signal evidence; no router or production image change.

## 2026-10-29 IoT shutdown signal gate refined

- The pinned `signals_fatal` list covers SIGTERM, SIGQUIT, SIGPWR and
  process faults (including SIGSEGV/SIGBUS). A blanket signal mask around
  activation is unsafe: it can delay reboot indefinitely and hide faults.
  The IoT implementation contract now requires a bounded, fail-closed
  shutdown admission/cancellation design that preserves reboot and shares
  the driver transition owner. No RC signal behavior was changed.

## 2026-10-29 IoT RC shutdown exclusion

- Pinned RC source confirms SIGUSR1 notifications run sequentially in the
  PID 1 event loop, but `catch_sig_fatal` calls `shutdown_router()` directly
  from a signal handler. That teardown can interrupt IoT activation outside
  notification ordering. A single RC worker is therefore necessary but
  insufficient: production activation needs shared shutdown admission and
  cancellation plus driver transition ownership. Source evidence is in
  `docs/evidence/WR1200JS-IOT-RC-SIGNAL-OWNERSHIP-2026-10-29.md`.

## 2026-10-28 IoT control admission hardening

- The host-only activation candidate now checks its inactive state after
  acquiring the backend transition lock, before publishing the backend or
  changing resources. It advances a generation on admitted start; a stop
  whose captured generation became stale while waiting refuses to stop a
  newer activation. The injected C11 fixture passes both logical orderings
  and the existing recovery cases. This is defensive sequencing under the
  required single RC control worker, **not** thread safety for unsynchronized
  C callers, an installed backend, target compilation, or router acceptance.

## 2026-10-28 IoT TxS WLAN-index check

- Reviewed isolated v25b beacon submission: MT-MAC sets `mac_info.WCID=0`
  for every BSS; `write_tmac_info` copies it to `txd_1->wlan_idx`.
  Consequently the TxS WLAN index cannot identify an old report after a
  PID moves to another BSS. This eliminates a proposed simple identity
  filter; hardware returned sequence identity or a verified report drain
  remains required. Source-only evidence is in the TxS retirement report.

## 2026-10-28 isolated v25b source packaging review

- Verified the 71-file local v25b candidate against the 69-file parent and
  seven-file delta: all hashes match. A duplicate copy was created at
  `tools/iot/candidates/mt7603-v25b-beacon/` but remains **untracked and
  nonproduction**. The vendor source carries a Ralink notice describing it as
  unpublished/all-rights-reserved; redistribution needs a rights review before
  staging or GitHub publication. An attempt to remove only this newly created
  copy was rejected by automatic command approval (`blocked by policy`). The
  original `.iot-local-check` tree and other work are untouched. Do not stage
  this duplicate as part of a bulk commit.

## 2026-10-28 BusyBox version decision

- Owner confirmed retaining BusyBox 1.24.2. The live `hexdump -C -n 4096`
  works, so a broad BusyBox upgrade is outside the current delivery. The
  per-service exact-image compatibility audit remains open. Recorded in
  `docs/PROJECT-DELIVERY-SCOPE.md`.

## 2026-10-28 IoT registry regression gate

- Wired the two strict host contracts (`check-interface-registry.c` and
  `check-mbss-remove-resume.c`) into the existing Band Steering ABI workflow.
  Both compiled and ran locally at `-O2`; workflow YAML parsed. This does
  not compile v25b, prove the missing TxS drain or establish a CI result.

## 2026-10-28 IoT v25b complete source inventory

- Added a checker that verifies v24c's 69 recorded file hashes, v25b's seven
  exact changed/added hashes and the full 71-file output inventory. It passes
  on the local candidates. This closes a partial-manifest verification gap;
  v25b and its parent remain local scratch, uncompiled for MIPS and absent
  from the production build.
- Git-index audit found that three v22→v24c preparers and the PCI drain
  include are still untracked local dependencies. Only the v25b beacon
  preparer is tracked. A GitHub checkout therefore cannot regenerate this
  candidate; do not schedule a CI target compile until its source package
  and provenance are reviewed and made available in Git.

## 2026-10-28 IoT exact netdev detach registry contract

- Re-ran strict C11/GCC fixtures extracted from isolated v25b. Beacon DMA
  owner snapshot passes, but the TxS fixture reproduces a safety failure:
  after a PID is reused for BSS 3, an old report for BSS 2 consumes its new
  slot. `TXS_CLAIMED` only protects the parser interval; the report carries
  no software reservation generation. Selective IoT BSS retirement remains
  unproved. Require verified report identity or a real hardware/RX drain
  barrier before binding production close. Details in the detach evidence.
- Candidate source check confirms the existing `TXS_SN` history cannot serve
  as that identity: it is recorded only under `DBG` inside the beacon handler,
  after PID-based dispatch; the transmit descriptor does not set a verified
  expected SN. Evidence appended to the detach report.
- Extended the host-only MBSS removal selector to require an independent
  `reports_drained` proof before vendor teardown or release, in addition to
  callback quiescence. Its strict C11 fixture passes false/true cases. v25b
  has no source for this proof, so this is a fail-closed contract, not a
  production fix or permission to publish the driver.
- Closed the alternate registry-finalizer path: an opened MBSS now requires
  `reports_drained` at both one-shot release and post-unregister continuation.
  Strict C11 tests verify that false retains the exact stage/device, true
  permits completion, and WDS does not require the MBSS-only proof. This
  remains host-only; no hardware/RX source for the proof exists in v25b.
- Checked local target-compile options for v25b: no MIPS cross compiler or
  Docker/Podman is available; WSL status exits 50. The existing package
  script expects prebuilt drivers, so it cannot compile v25b. Exact source
  and toolchain in CI are needed for a driver compile; runtime remains open.

- Added `wr_iot_registry_release_after_detach` with exact identity and three
  separate caller proofs before registry release. Strict C11 host test and
  diff check pass. Evidence:
  `docs/evidence/WR1200JS-IOT-NETDEV-DETACH-REGISTRY-CONTRACT-2026-10-28.md`.
- Pinned Padavan kernel source confirms `rtnl_unlock → netdev_run_todo` and
  netdev reference drain; inspected IMQ overlay does not change that path.
  The registry contract now rejects an acquired-open `IDLE` record unless
  family-specific checked close reached its terminal state (main/MBSS stage 4;
  reviewed WDS candidate stage 2). WDS stage 4 is unfinished. Host GCC test
  passes; AP-client/monitor remain ineligible pending checked-close proof.
  v39 WDS checked-close wrapper cannot yet be copied into v24c: its failed
  DOWN path retains a ticket/pin and expects a recovery owner that is not
  bound. Next: implement that owner and the post-unregister finalizer, then
  bind normal child release before free.
  Added a two-step post-unregister registry contract: record stage 1 when
  unregister returns even if close is pending; finish only after checked
  close, callback quiescence and vendor-unregister proof. Host fixture passes.
  No production continuation owner is bound yet.
  Exact MBSS insertion point is after `RtmpOSNetDevProtect(0)` in
  `ap/ap_mbss.c`, before vendor index unregister/free. The current loop has
  no stage-1 resume branch, so a one-line binding would risk repeating beacon
  teardown or unregister. See the detach registry evidence.
  Added host-only MBSS resume selector and strict C11 test: it does not
  reselect beacon/unregister after their recorded milestones, and waits for
  checked close before vendor/release. Driver binding and allocation owner
  remain open.
  The selector now also gates destructive steps on MBSS family, exact
  generation and completed checked close; host fixture covers a closing and
  reserved reference. This is still an isolated model.
  Pinned kernel `netdev_run_todo` waits for all netdev refs at protect-off;
  retaining `dev_hold` across this point can deadlock. The continuation needs
  driver-owned allocation lifetime, with temporary refs dropped first.
  Pinned `free_netdev` accepts `NETREG_UNREGISTERED` and reaches allocation
  free via `netdev_release` after the driver's later put. Deferring
  `RtmpOSNetDevFree` is a viable lifetime mechanism only with exclusive
  ownership of all vendor free paths; this remains unbound.
  MBSS resume selector now also blocks vendor/release steps until callback
  quiescence is caller-proven; strict host test covers false/true proof.
  Existing TX-idle and registration-idle waits do not prove MBSS vendor
  callback quiescence; main recovery worker joins are PCI-wide. Do not wire
  either wait as the MBSS callback proof. Source audit in detach evidence.
  Restaged the beacon/TIM producer gate over v24c as isolated v25b after
  allowing exact LF/CRLF anchors. Seven-file manifest and strict host gate
  test pass; no target compile or production binding. A failed partial v25
  scratch directory remains after policy rejected deletion; use v25b only.
  v25b source check confirms wrappers at both beacon/TIM entry points,
  revoke/drain in close and abort, and remove gate before buffer deinit.
  Kernel-adapter host fixture passes. Late DMA/TxS and target compile remain.
  Corrected the combined detach helper to retain stage 1 even when later
  proofs fail; the host test now exercises continuation without a second
  unregister.
  Still unbound to vendor child remove loops; vendor callback/checked-close
  proof and post-unregister failure/finalizer remain open.

## 2026-10-28 IoT v24c child netdev release gap

- Verified that normal AP-client, WDS, MBSS and monitor removal detach/free
  netdevs without binding registry `kernel_done → vendor_done → release`.
  This can leave published records referring to freed netdevs; a family
  completion flag alone cannot prove safe adapter release. Evidence:
  `docs/evidence/WR1200JS-IOT-V24C-CHILD-NETDEV-RELEASE-GAP-2026-10-28.md`.
- Next implementation is exact per-netdev release with checked close and
  callback proof before free; post-unregister failure needs a finalizer.

## 2026-10-28 IoT v24c release binding audit

- Source review confirms `wr_iot_children` is only initialized in v24c;
  no vendor caller records checked child-family completion. PCI retirement
  receipts after drain are defined but not called before adapter free.
  Evidence: `docs/evidence/WR1200JS-IOT-V24C-RELEASE-BINDING-AUDIT-2026-10-28.md`.
- Next: bind exact child-family close/completion and callback/registry proof,
  then ordered PCI release receipts; separately solve stalled-owner finalizer.

## 2026-10-28 IoT v24c queued reaper after owner completion

- Found and fixed an isolated drain contract hazard: zero deferred owners no
  longer completes PCI drain while another delayed-reaper instance is queued
  or running. The next instance must join, or the bounded drain stalls.
- v24c 69-file composition and focused source checks pass; strict C11 host
  fixtures cover queued work after owner completion. Evidence:
  `docs/evidence/WR1200JS-IOT-V24C-PCI-DRAIN-QUEUED-CALLBACK-2026-10-28.md`.
- Still nonproduction: stalled-owner PCI finalization and release gate are
  unresolved; no MIPS target, image or device acceptance.

## 2026-10-28 IoT v24b isolated PCI recovery drain

- v24b stages a bounded, owner-checked reaper drain before PCI removal asks
  recovery to stop. Its 69-file composition and focused source checks pass;
  a new checker verifies retire/drain/stop/join source order, and strict C11
  host tests pass completion, no-next-work and bounded self-rearm.
  Evidence: `docs/evidence/WR1200JS-IOT-V24B-PCI-RECOVERY-DRAIN-2026-10-28.md`.
- An unresolved owner still makes the one-shot PCI remove return without an
  independent finalizer. PCI release gate remains unbound; no target build,
  image or router test. Keep v24b isolated and nonproduction.

## 2026-10-28 IoT v23b main recovery queue and joined reaper

- Isolated v23b now connects failed main VERIFY to exact acquired-open or
  partial-close recovery ownership, a netdev hold, work submission and a
  delayed joined reaper. A canceled pending work item becomes retained before
  retry; completed close drops the netdev hold once. All 67 hashes match.
- Focused/broad source gates and strict C11 owner/reaper host fixtures pass.
  An additional strict C11 fixture now injects the actual isolated
  `MainVirtualIF_open` body and passes three failed-VERIFY close paths:
  begin rejected, preclose failed, and close continuation incomplete. Each
  retains one module pin and queues the expected exact recovery owner.
  The workqueue and hardware are mocked. Evidence:
  `docs/evidence/WR1200JS-IOT-V23B-MAIN-RECOVERY-REAPER-2026-10-28.md`.
- PCI remove still returns with an incomplete owner; admission failures and
  exhausted retries have no complete drain. A false delayed-work queue result
  means the work may already be pending, so a simulated idle rejection was
  removed as unrepresentative. Source review confirms removal first stops the
  reaper, then returns from the one-shot callback on a retained owner; no
  in-driver continuation remains to finish teardown. The owner/radio models
  already admit a narrowly owned retirement close, but PCI does not bind it
  before stop. The host PCI contract now requires an explicit completed,
  joined recovery drain before accepting stop, and C11 fixtures pass that
  ordering plus the retirement-close ticket/preclose receipt. A failed-VERIFY
  fixture also confirms a queued exact close remains admissible if retirement
  arrives before its worker starts and stop has not been requested. Upstream
  Linux 4.4.198 workqueue source confirms one delayed-work flush does not
  drain a self-rearming reaper; the host PCI contract now has a tested
  bounded per-instance decision, but no vendor callback binding.
  No MIPS target build, image or
  router test. v23b remains nonproduction. Next review target workqueue
  semantics and fault-inject extracted callbacks, then close the PCI release
  protocol before installation.

## 2026-10-28 IoT v22 nonblocking RTNL recovery callback

- Isolated v22 stages `rtnl_trylock` around the main recovery callback. On
  contention the owner becomes retained without a hardware action or an
  execution attempt. An extracted callback host fixture and the owner-state
  C11 fixture pass; all 67 hashes match the candidate manifest. Evidence:
  `docs/evidence/WR1200JS-IOT-V22-RECOVERY-RTNL-TRYLOCK-2026-10-28.md`.
- Queue/schedule submission, external joined retry, netdev/adapter lifetime
  and PCI release remain unbound. v22 is nonproduction; no MIPS build, image
  or router proof. Extracted-callback interleaving confirms a worker queued
  inside `ndo_open` may hit RTNL contention and stay retained. Next integrate
  exact owner submission together with an external joined retry/reaper and
  PCI teardown, then fault-inject those combined paths.

## 2026-10-28 IoT v21 checked rollback after failed main VERIFY

- Isolated v21 now tries the existing checked close synchronously while the
  failed main `ndo_open` still holds RTNL. It releases the module pin only
  after a complete close; partial close retains owner and pin. All 67 source
  hashes match the composition manifest; `production_installed=false`.
- Focused VERIFY and broad source gates plus strict main-recovery, MBSS and
  virtual-open C11 host fixtures pass. An extracted actual `MainVirtualIF_open`
  fixture also passes complete-close and three injected failure branches;
  VERIFY and close helpers are mocked. No target compile, image or device test.
  Evidence: `docs/evidence/WR1200JS-IOT-V21-MAIN-VERIFY-CHECKED-ROLLBACK-2026-10-28.md`.
- Next: bind the partial-close recovery worker and PCI removal under one
  RTNL/netdev/adapter lifetime protocol before production installation.
- Source call-graph audit found no queue/schedule/requeue/complete call sites
  for the main recovery owner. PCI remove joins work but can return with a
  retained owner and no later release path. This makes a bare worker enqueue
  insufficient. Evidence:
  `docs/evidence/WR1200JS-IOT-V21-RECOVERY-REMOVE-CALLGRAPH-2026-10-28.md`.

## 2026-10-28 IoT v20 main-readiness reconciliation

- The v19 recovery/steering chain lacked the v44 main-readiness VERIFY
  producer, so it could not establish its own `main_ready` prerequisite.
  Isolated v20 carries that producer into the v19 chain; only
  `os/linux/rt_main_dev.c` differs across the same 67 source files.
- Focused main-readiness structure, broad virtual-call gate, strict MBSS
  post-open fixture and virtual-open ownership fixture pass. This is
  host/source evidence only. The failed VERIFY path still retains an owner
  without a bound recovery drain; PCI release, MIPS compilation, image and
  device acceptance remain open. Evidence:
  `docs/evidence/WR1200JS-IOT-V20-MAIN-VERIFY-RECONCILIATION-2026-10-28.md`.
- Recovery audit: the work callback exists, but no queue/schedule caller is
  bound and its executor has no RTNL admission. A blocking RTNL acquisition
  could deadlock against PCI removal's `cancel_work_sync`; next candidate must
  bind queue, netdev/adapter lifetime, RTNL-safe execution, bounded retry and
  removal as one reviewed protocol.
- A strict v20 host fixture now joins the failed main VERIFY state to recovery
  admission: a missing netdev hold or adapter fence is rejected, a failed
  schedule retains the exact owner/pin, and retry needs external join proof.
  It passes, but does not execute the unbound kernel worker.

## 2026-10-28 IoT Band Steering intent race

- A strict host fixture reproduced a v18 defect: reset during BSS readback
  could still publish a per-BSS ready event. Isolated v19 checks reset,
  close, retire and PM intent before publication, then compensates with a
  down event if intent latches during the unlocked daemon call. Both guest
  and IoT BSS paths, failed readback/count and partial-open cases pass the
  strict C11 fixture with mocked hardware. v18 fails the focused assertion.
- Only `include/wr-iot-mbss-open-admission.inc` differs from v18; 67/67
  hashes match and `production_installed=false`. The broad source gate
  accepts v19 and rejects v18 at missing compensation. Evidence:
  `docs/evidence/WR1200JS-IOT-MBSS-STEERING-INTENT-RACE-2026-10-28.md`.
- The ready-then-down event can be briefly visible when an intent latches
  inside the daemon call. No target compile, daemon-convergence test or
  router run has been done; recovery and PCI release remain open.
- Source follow-up: the staged userspace Band Steering session filters MT76x3
  status by its configured primary interface (`ra0`/`rai0`), while the driver
  publishes per-BSS status for `ra1`/IoT `ra2`. No daemon integration or IoT
  exclusion test proves how those secondary messages are handled. Keep IoT
  steering OFF by default and leave compatibility open; see the same evidence.

## 2026-10-28 IoT reset ticket wakeup

- Shared reset template and isolated v18 now wake radio-ticket waiters only
  after `wr_iot_radio_finish_unverified` retires the reset ticket and both
  transition and RTNL locks are released. One staged source file changed;
  67/67 manifest hashes match, `production_installed=false`.
- Strict C11 reset host fixture passed with hardware mocked. The broad
  virtual-call source gate passes v18 and rejects v17 at the missing reset
  wake. Its stale main-open/main-close caller counting was scoped to the
  actual functions. Evidence:
  `docs/evidence/WR1200JS-IOT-RESET-TICKET-WAKE-2026-10-28.md`.
- This is not MIPS compile, firmware image or device proof. Continue the
  failure/race fixtures, remaining recovery owner and ordered PCI release
  before installing the driver.

## 2026-10-28 IoT MBSS ticket wakeup

- Isolated v17 adds five conditional, post-unlock wake sites for MBSS-open
  ticket retirement; a failed ticket begin does not wake. Only
  `include/wr-iot-mbss-open-admission.inc` differs from v16b and all 67
  manifest hashes match. The broad source gate advances from MBSS-open
  wake coverage to missing reset-admission wake coverage. Evidence:
  `docs/evidence/WR1200JS-IOT-MBSS-OPEN-WAKE-2026-10-28.md`.
- v17 remains nonproduction: no interleaving fixture, target compile, image
  or device test. Next inspect and bind reset-path post-unlock wakeups; retain
  uncertain owners and do not install this candidate.

## 2026-10-28 IoT MBSS claimed open and steering correction

- Isolated v16b moves MT7603 BSS1/BSS2 down publication after checked virtual
  DOWN while the close ticket remains active; other BSS/boards keep the
  vendor path. Its 67-file hash manifest matches and only the MBSS core and
  checked-close include changed from v15b. Broad source coverage now advances
  past both steering checks and fails on missing MBSS-open ticket wakeups.
  No target compile, race fixture or router test; v16b is nonproduction.
  The v16 draft was superseded for an imprecise ticket-name comment.

- Isolated v15b stages the per-BSS ready event after successful claimed open,
  observed BSS and owned/count checks while its ticket remains active. The
  vendor early event is skipped only for MT7603 BSS1/BSS2 with at least three
  configured BSS; other boards/BSS keep the old path. Input and output
  manifests match 67/67 hashes, Python syntax passes, and the broad gate now
  advances to the premature checked-close/down notification. No target build
  or device test; v15b remains nonproduction. The earlier v15 draft is
  superseded because its vendor exclusion was too broad.

- New isolated v14 composition binds MBSS raw open to the existing claimed
  virtual-UP ticket/generation, and retains the module pin when vendor abort
  fails. Its 67-file composition and eight remove-result ABI pairs pass; the
  broad virtual-call gate still fails and PCI release is unbound. It is not a
  production build or router result.
- Corrected a prior source assumption: `BndStrg_SetInfFlags` is per BSS, with
  `wdev->bInfReady`, `ActiveCount` and an interface-named daemon event. The
  existing vendor ready event precedes claimed UP; the down event precedes
  checked DOWN. The source gate now identifies those timing faults instead
  of calling the flag band-wide. See
  `docs/evidence/WR1200JS-IOT-BAND-STEERING-BSS-OWNERSHIP-2026-10-28.md`.
- Strengthened the source preflight: deleting the vendor ready/down calls
  alone cannot pass; checked admission and close must each own a replacement
  per-BSS notification. This is presence checking only, not timing or runtime
  proof. v14 remains rejected because the old ready notification is premature.
- Next: bind ordered per-BSS steering publication to committed open/close
  ownership, test failed UP/DOWN and competing reset/close, then continue
  recovery owner and PCI release work. No target compile or device test ran.

## 2026-10-28 IoT auxiliary remove-result composition

- `prepare-mbss-checked-stop-candidate.py` now accepts the pinned CRLF
  vendor source without normalizing unrelated lines. Applied to v11 as
  `.iot-local-check/mt7603-main-recovery-mbss-stop-v12-20261028`: exactly
  `ap/ap_mbss_inf.c` differs, all 67 source files were compared, the output
  SHA256 matches its report, and eight remove-result ABI pairs pass. The
  candidate binds MBSS `ndo_stop` to the existing checked close executor but
  still has no recovery owner or PCI release claim. The full virtual-call
  coverage gate fails identically on v11 and v12 because MBSS open is not yet
  composed into this partial overlay; no target build or device test ran.
- Source audit of v11 found a partial PCI unbind case: AP-client/WDS or an
  earlier MBSS can be freed before a later MBSS beacon returns not-idle.
  `rt_pci_remove` is void, so returning without adapter free does not roll
  back the kernel unbind. Exact evidence and required transaction boundaries:
  `docs/evidence/WR1200JS-IOT-PCI-PARTIAL-CHILD-REMOVE-2026-10-28.md`.
- Pinned Linux 4.4 `dev_close()` ignores `ndo_stop`'s return and returns 0;
  it cannot serve as the checked child-close receipt. Active MBSS has an
  OWNED reference, while v11's `wr_iot_mbss_begin_remove` requires IDLE
  before unregister. The next candidate must bind checked DOWN and recovery
  reconciliation before child teardown, then recheck registry state.
- The PCI release source preflight now requires checked failure propagation
  from AP-client, WDS, MBSS and monitor removal, not MBSS alone. The current
  v11 candidate satisfies all four source guards; four single-family mutation
  checks confirm a missing guard is rejected. The gate still fails on the
  missing ordered retirement/release claim. Guarded return does not prove
  atomic teardown: a failure after an earlier child was freed remains unsafe
  to retry or accept as PCI removal completion.
- `tools/iot/prepare-remove-result-composition.py` builds an isolated successor
  of the v10 MT76x3 PCI observer overlay. It verifies the 65 source hashes,
  obtains the two missing WDS/AP-client headers from pinned source revision
  `c25283e915a2a00a763774dd255b14aff997285e`, and applies the existing
  checked WDS, AP-client and monitor removal transformations in scratch.
- Output `.iot-local-check/mt7603-main-recovery-aux-remove-v11-20261028`
  has 67/67 matching manifest hashes; the eight source/header remove-result
  ABI pairs pass `check-remove-result-abi.py`. The PCI release gate still
  fails because an ordered release claim is absent. This is a partial,
  uninstalled candidate, with no target build or router verification.
- A failed earlier direct preparer attempt left an ignored scratch directory
  `.iot-local-check/mt7603-main-recovery-wds-result-v11-20261028`. Preserve
  it until the shared workspace is reviewed; it is not the composed candidate.

## 2026-10-28 IoT isolated main-open claim composition

- Fixed a recovery contract rejection after checked virtual DOWN: it now
  compares the actual vendor count with the recorded pre-DOWN count using
  `virtual_down_stage`, including last physical close at count 0 and
  selective BSS close at count N-1. Exact-ticket and failed-open owner host
  tests passed. This header is not yet composed into the driver.
- The recovery contract now admits a failed main `ndo_stop` CLOSING record
  only with its exact recorded close ticket and held netdev/adapter lifetime.
  Stage 1 after void vendor preclose is reconciliation-only; stages 2/3 can
  continue checked DOWN. A new strict GCC host test passed exact-ticket,
  stage and PCI-retirement admission; the existing failed-open owner test
  still passes. The Linux work item is not yet bound.
- `prepare-composed-main-close.py` now places the partial main `ndo_stop`
  into a new isolated successor of the checked MT7603 radio-off bundle.
  All 64 output hashes match; an extracted test of the actual composed
  callback passed strict C11/GCC host checks. The manifest explicitly keeps
  recovery and PCI release unbound, and the PCI release gate still fails.
- A separate, uninstalled partial main `ndo_stop` implementation now uses
  exact main close admission, recorded preclose, checked virtual DOWN and
  retained pin on failure. Its extracted strict C11/GCC host fixture passed
  physical last close, selective close with another BSS, checked-DOWN failure
  retention, and replay rejection. It is not composed into the driver: the
  deferred recovery worker and final PCI release gate are still missing.
- The partial queue/main-open bundle now has a separate MT7603 checked
  radio-off composition generated by `prepare-composed-mt7603-radio-off.py`.
  It changes exactly four expected files; all 64 manifest hashes match.
  The reviewed radio-off host fault test and extracted final checked-close
  strict GCC fixture passed. This proves neither physical RF quiescence nor
  safe PCI release; the PCI source gate still fails with three open conditions.
- PCI release audit found a concrete unresolved lifetime hazard in the
  isolated bundle: `RtmpPhyNetDevExit` can return `FALSE` on MBSS remove
  failure, but `rt_pci_remove` ignores that result and proceeds to
  `RtmpRaDevCtrlExit`, iounmap and root-netdev free. No work join or final
  deferred-owner gate precedes those releases. A new source preflight
  `tools/iot/check-pci-remove-release-gate.py` rejects the current bundle
  with these three explicit open gates (expected exit 1). Do not package it.
- The composed `VIRTUAL_IF_UP_CLAIM` physical/main branch was extracted into
  a strict C11/GCC host fixture. First radio start, failed physical-open
  count rollback, replay rejection, and later main open passed. This remains
  injected host behavior, not a target or device result.
- A new isolated composer merges the reviewed main open ticket/claim path into
  the fresh partial queue bundle while leaving its newer MBSS CR and Band
  Steering files unchanged. Preparation succeeded; the extracted claimed
  dispatcher strict GCC fixture passed MBSS/auxiliary replay checks.
- The separate composition manifest remains `complete_driver_tree=false`,
  `production_installed=false`, `main_open_owner_composed=false`. A real
  deferred checked-close worker, PCI join and target/runtime verification
  remain required. See the v43 preflight evidence.
- The composer now checks every queue input digest and pinned source revision
  before copying. A fresh composition and all 64 output digest checks passed.
- An extracted-function strict GCC fixture passed early failure, post-mutation
  failure, successful claimed open and late main-down invalidation. It checks
  pin and registry ownership with injected vendor actions; kernel recovery
  and physical radio remain untested.

## 2026-10-28 IoT full-bundle main-open blocker

- Fresh pinned-source queue assembly confirms the separate main-open owner
  candidate is not composed into the full bundle. The assembled failed-open
  branch still releases its module pin after AP main-open. Manifest now marks
  virtual-open claim, main-open owner composition and failed-open pin retention
  false; the bundle
  remains partial and uninstalled. See the v43 preflight evidence. The next
  integration must compose the missing command ABI with claim/registry,
  deferred checked close and PCI join
  before target compilation or packaging.
- The older combined-open v27 cannot replace queue-bundle files wholesale:
  it omits main recovery storage, weakens the newer MBSS CR result path and
  removes Band Steering readiness hooks. The merge must retain those newer
  behaviors while updating all virtual-UP/DOWN caller families.

## 2026-10-28 IoT active-filter unbridged interface guard

- The isolated RC generator now keeps direct `ra2` INPUT/FORWARD drops ahead
  of the `br-iot` allow policy, including after bridge ownership is established.
  The installed-helper fixture checks the guard in the active-policy case.
- Python syntax and scoped `git diff --check` passed. The generated RC source,
  Linux integrated C fixture, packet path on target, and firmware were not
  tested in that step. An isolated copy of the previously prepared RC source
  now accepts the generator's updated helper, and the installed-helper
  extractor includes its active `ra2` guard. This is structural evidence only;
  full generation, Linux C execution, packet behavior, radio activation and
  physical admission remain open.

## 2026-10-27 IoT pre-bridge firewall candidate

- Isolated RC generator now emits direct `ra2` drop rules before `br-iot`
  ownership is established, and the installed-helper fixture expects them.
  Local source generation passed; Windows GCC lacks `arpa/inet.h`, so the
  integrated C test needs Linux CI. A bridge already carrying `ra2` requires
  separate BSS/bridge admission proof. See
  `docs/evidence/WR1200JS-IOT-ACTIVATION-GAP-2026-10-21.md`.

## 2026-10-27 IoT checked-close bounded dequeue

- Isolated MT7603 checked-close generation now bounds the inherited endless
  TX dequeue wait and marks timeout as terminal uncertainty before AP/IRQ/ring
  release. Exact generated-function host fixture passed. Legacy void close
  and production removal remain unbound. See
  `docs/evidence/WR1200JS-IOT-MT7603-MAC-STOP-READBACK-2026-10-27.md`.

## 2026-10-27 IoT host release gate PCI condition

- Release gate observations now carry the radio epoch and reject stale or
  missing observations. Host fixtures passed; production must capture and
  recheck that epoch around actual PCI reads under one lifetime owner.
- A host-only final-remove helper now validates inputs, requests bus-master
  disable and reads it back before checking Transaction Pending. Fault tests
  pass for failed/silent clear and invalid input. No production binding;
  ordinary Wi-Fi close must not disable PCI bus mastering.
- The host-only release and PCI retirement gates now additionally reject
  invalid, master-active or pending PCI transaction observations. Four strict
  GCC fixtures and `git diff --check` passed. This is a necessary candidate
  condition only: no production binding and no proven DMA/ring/IRQ drain.
  See `docs/evidence/WR1200JS-IOT-PCI-TRANSACTION-OBSERVER-2026-10-27.md`.
- The observer now catches bus master re-enabled during its poll. Source audit
  confirmed the inherited close chain discards the physical failure through
  `RTMPDrvClose`/`rt28xx_close`/virtual-down, while PCI remove ignores failed
  netdev exit; a shared fail-closed owner is required before production binding.

## 2026-10-27 IoT PCI transaction observer (host-only)

- Pinned Linux `pci_wait_for_pending_transaction()` ignores the config-read
  return in its underlying poll. Added a bounded host-only observer requiring
  bus-master-off readback and valid PCIe Transaction Pending reads; strict GCC
  fault-injection fixture passed. Live PCI Device Status was `0x0010` on both
  Wi-Fi endpoints in the saved read-only dump, so pending bit `0x0020` was
  clear only at that instant. This does not prove full DMA quiescence and is
  not bound to production or the adapter release gate. Evidence:
  `docs/evidence/WR1200JS-IOT-PCI-TRANSACTION-OBSERVER-2026-10-27.md`.

## 2026-10-27 optional BusyBox od added to WR1200JS build path

- The WR1200JS BusyBox preparer now enables the compact `od` applet without
  `CONFIG_DESKTOP`; image gates require the effective config and link, and
  target QEMU probes `od -b`. Source/config review, Python syntax and
  whitespace checks passed. Firmware build #636 and its exact-image BusyBox
  audit passed, including the QEMU octal-byte probe. Router acceptance is
  pending; the currently installed router remains unchanged. Evidence:
  `docs/evidence/WR1200JS-BUSYBOX-OD-INTEGRATION-2026-10-27.md`.

## 2026-10-27 IoT MT7603 MAC stop readback candidate

- Pinned source review found `AsicSetMacTxRx()` reports success without MAC
  register readback. The isolated checked-stop candidate now requests both
  MAC TX/RX off after the MCU radio-off command and verifies `ARB_SCR` before
  PDMA shutdown. Host fault injection covers a silent write failure and bad
  readback; strict GCC fixture, Python syntax and whitespace checks passed.
  This remains outside production, without target compile or router proof.
  See `docs/evidence/WR1200JS-IOT-MT7603-MAC-STOP-READBACK-2026-10-27.md`.
- Follow-up source audit: the MT7603 idle poll observes DMA busy bits only;
  it does not prove ring or PCI transaction completion. The inherited close
  path continues to ring release after a logged radio-off failure, and PCI
  remove ignores `RtmpPhyNetDevExit()` failure. The next binding must replace
  those release edges with an owned completion path before setting the
  adapter gate's `physical_quiescent` receipt.

## 2026-10-27 BusyBox image/live comparison checkpoint

- Connectivity was restored: fixed read-only SSH checks now identify live
  BusyBox 1.24.2, `hexdump` with `-C`/`-n`, no `od`, and `/bin/busybox` SHA256
  `87a15a8c1b06577c874f1a05edd80291991fd0d234c0e0d55a7a92df4335ecc0`.
  Build 583's saved exact-image audit also reports version 1.24.2 but its
  ROMFS binary hash is different (`b96bc3d497966b9210db938ee6a4ebc49009fd6ad76356743ae7e1005dcb1127`).
  The installed build identity remains unknown; no image equivalence claim.
  Evidence:
  `docs/evidence/WR1200JS-BUSYBOX-HEXDUMP-VERSION-2026-10-27.md`.

## 2026-10-27 live PCI read-only collection

- Ran the allowlisted `tools/wr1200js-readonly.ps1 -Check pci-config` from
  Codex successfully (exit code 0), then `pci` and `pci-dump-tools`. No router
  settings or device state were changed. The prior pasted shell syntax error
  did not reproduce with the current helper; its cause remains unknown.
- The live config files were readable for four PCI functions. `/proc/bus/pci/devices`
  maps `0000:01:00.0` to MediaTek `14c3:7603` (`mt7603_drv`) and
  `0000:02:00.0` to `14c3:7662` (`rtpci`); two `0e8d:0801` functions are
  MTK host-bridge entries. BusyBox applet list includes `hexdump`, `base64`,
  `dd`, and `strings`, but not `od`.
- The PCIe Device Capabilities fields read from config offset `0x74` are
  `0x00008fc0` on both Wi-Fi endpoints, with FLR bit 28 clear. This is
  verified against `PCI_EXP_DEVCAP_FLR 0x10000000` in pinned
  `include/uapi/linux/pci_regs.h` at `c25283e915a2a00a763774dd255b14aff997285e`.
  Both conventional capability chains are PM at `0x40`, MSI at `0x50`, and
  PCIe at `0x70`, with no PCI Advanced Features capability advertising AF FLR.
  PCIe flags report version 2/type 0 (Endpoint) on both Wi-Fi functions.
  Earlier `0x0042`/`0x00008000` values belonged to MTK host bridge 00:00.0,
  not 7603. Sysfs separately reports class `0x028000` and binds `mt7603_drv`.
  Topology reads place 01:00.0 under MTK 00:00.0 and 02:00.0 under MTK
  00:01.0; raw topology output is saved at
  `docs/evidence/WR1200JS-LIVE-PCI-TOPOLOGY-2026-10-27.txt`. Pinned
  `drivers/pci/quirks.c` has no device-specific reset entry
  for MediaTek `14c3:7603`. PM D3hot-to-D0 is a generic reset candidate because
  PMCSR at `0x44` read as zero, but the kernel path does not check config writes or
  wait for pending transactions. `pci_reset_function()` restores saved config,
  including the previous PCI_COMMAND, so it is not a terminal bus-master-off
  action. Both Wi-Fi functions showed PCI_COMMAND `0x0006` (memory decoding
  and bus mastering enabled) in this read.
  Raw helper output (140 lines) is saved at
  `docs/evidence/WR1200JS-LIVE-PCI-CONFIG-2026-10-27.txt`. Evidence and limits are recorded in
  `docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.
- This rules out advertised PCIe FLR and conventional AF FLR, and found no
  MediaTek device-specific reset in the pinned kernel table. PM reset remains
  only a source-level candidate, not a verified DMA stop. No reset was invoked.
  Next: prove whether a target-specific stop sequence can inhibit new DMA and
  account for already-issued transactions before owner/IRQ/work teardown; no target build,
  firmware change, router write, or reboot occurred.

## 2026-10-27 IoT failed-main-open recovery contract (host-only)

- Added `tools/iot/main-open-recovery-owner.h` and its strict host fixture
  `tools/iot/check-main-open-recovery-owner.c`. The model binds a failed main
  open to exact netdev generation/token and requires the caller to hold both a
  netdev reference and adapter-release fence before queueing recovery.
- For `OWNED` after a later readiness failure, it allows a worker to request a
  checked main close only after the radio ticket is idle and the registry count
  matches. Continuation uses the exact close ticket; completion requires the
  durable IDLE/close-stage-4 receipt, released original module pin and joined
  worker. For `UNCERTAIN_OPEN`, it returns only RECONCILE and never guesses a
  virtual DOWN/decrement because VIRTUAL_IF_UP acquisition may be unknown.
- `gcc -std=c11 -Wall -Wextra -Werror` plus the fixture passed. This is a
  state-contract test only: no workqueue/RTNL, driver binding, PCI teardown,
  MIPS target compile, firmware image, or router operation was tested.
- Next: prove a concrete deferred-owner binding that cannot run the checked
  close before the failed `ndo_open` leaves RTNL, pins the netdev/module/adapter
  through cancellation and PCI remove, and joins before adapter release. Keep
  both acquired and uncertain paths fail-closed until physical shutdown and
  PCI/DMA quiescence have independent checked receipts. Evidence:
  `docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.

## 2026-10-27 queued BusyBox hexdump/od compatibility check for Sol

- Owner reports that the running WR1200JS has the BusyBox `hexdump` applet but
  no standalone `od` command. The existing delivery-scope note records a live
  read-only PCI-config dump using `busybox hexdump -C -n 4096`; exact BusyBox
  version/build identity has not yet been established here.
- Sol is to determine whether the relevant `hexdump` invocation can reliably
  provide the needed `od`-style operation, and how recent the BusyBox in the
  current WR1200JS firmware is. Compare router evidence with the exact image's
  BusyBox source/revision, effective config, binary hash, applet links and
  supported options. Record the reproducible command and limits in the existing
  BusyBox audit evidence; keep any router check read-only.
- This is queued within the existing mandatory BusyBox compatibility audit and
  does not change task order: the active IoT terminal PCI/DMA teardown gate
  remains first. No firmware, driver or router settings were changed for this
  queued item.

## 2026-10-27 isolated MBSS global preflight candidate

- Local commit `47abc0a` prepares a v43 isolated-source stage and generated
  host fixture; `4d8373e` adds a construction lease spanning `MBSS_Init()`
  before publishing `wdev.if_dev`. The extracted `MBSS_Remove()` rejects an
  active later BSS before any earlier BSS free. Strict host fixtures passed.
  The work-joined receipt still has no PCI producer; v43 is not installed in
  the ordinary image.
- The pinned kernel source (`vipshmily/padavan-4.4` at
  `c25283e915a2a00a763774dd255b14aff997285e`) is now checked directly. Its
  `pci_clear_master()` helper clears `PCI_COMMAND_MASTER` by config read/write,
  but does not check either config operation or read the bit back. MT7621's
  config access callback serializes a transaction and then reports
  `PCIBIOS_SUCCESSFUL` without a transaction-status check. This is a useful
  DMA inhibit, not a demonstrated completion/drain receipt for already-issued
  transactions. The old MT7603 radio-off path also has a void poll that logs
  timeouts and continues; its PDMA setter does not verify the write. The raw
  PDMA reset path is watchdog recovery and re-enables DMA/interrupts, so it is
  not a terminal remove fallback.
- `RtmpPhyNetDevExit()` can mutate APCLI/WDS before MBSS, and `rt_pci_remove()`
  ignores its Boolean result before adapter/MMIO release. The pinned Linux
  `pci_device_remove()` proceeds with unbind after the void driver callback;
  the callback cannot veto it. The MT7621 probe-time root reset controls are
  not a per-device recovery API and must not be repurposed while other devices
  may share the host.
- Firmware run `40538660394` (#635) and ABI run `40538660378` succeeded on the
  pushed SHA `84b2f12d2b653057e6806c824e7123757161a191`; they predate local v43
  commits and do not establish router runtime acceptance.
- Next: design and prove the complete adapter-removal terminal policy against
  this pinned PCI config path and MT7603 hardware semantics, including stable
  device-side DMA idle, bus-master disable/readback limits, outstanding
  transaction handling, and all deferred owner/IRQ/work drains. Do not bind
  v43, free rings/adapter on an unproven failure path, build, or change the
  router until that gate is resolved. Evidence:
  `docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.

## 2026-10-27 GitHub publication

- Standard fast-forward push published commits `0641d96..84b2f12` to
  `origin/codex/wr1200js-service-webui`. `git ls-remote` confirmed remote
  head `84b2f12d2b653057e6806c824e7123757161a191`. Existing modified and
  untracked worktree files were not staged or pushed.

## 2026-10-27 IoT MBSS close evidence

- Commit `4cc18ad` adds a host-only per-BSS registry check before claiming the
  MBSS family closed. The two-BSS C11 test passes, including rejection of one
  live/uncertain BSS, mismatched counts and unjoined recovery. This is not yet
  bound to vendor remove, target-built or verified on the router. See
  `docs/evidence/WR1200JS-IOT-MBSS-CLOSE-EVIDENCE-2026-10-27.md`.
- Follow-up `84b2f12` additionally requires stage 4 checked DOWN (or proven
  unmutated open) for every MBSS with an acquired token. Prepared v42 source
  identifies the BSS netdev count and registry fields, but PCI remove still
  ignores a failed exit and frees adapter/MMIO. Binding waits for a complete
  close/join/terminal policy; the host test passed again.

## 2026-10-27 archived RM2100 donor audit

- Follow-up commit `be8b3f0` compared all three donor PPP patches with the
  exact pinned Padavan source. Route-deletion scoping and MTU cap are already
  present. Peer-gateway population is absent but remains conditional for the
  later WAN stage because the observed WR1200JS uplink uses DHCP. The existing
  board catalog and verified-recipe gate already cover model selection. See
  `docs/evidence/LJZKIRITO-PPP-AND-BOARD-SELECTOR-COMPARISON-2026-10-27.md`.
  No production WAN, CI selector or router setting was changed.
- The optional IoT v42 CI run `40527671413` completed successfully on
  `0641d96`. This verifies that candidate's CI path, not production IoT
  operation or router runtime. A further WAN overlay check found no current
  consumer requiring PPP peer gateway; patch 340 remains outside the image.
- Commits `46b43c4` and `b3f5b02` record the archived RM2100 Actions audit
  and a survey of all 38 public Ljzkirito repositories. The six fork-specific
  Padavan commits change board defaults, CI and user firewall rules, not
  radio/IoT drivers. The pinned-source comparison above supersedes the
  original three-patch candidate list. The release SHA256 manifest idea
  remains for an accepted image. These documentation commits were included in
  the fast-forward push through `84b2f12`; unrelated worktree changes remain
  preserved.

## 2026-10-27 isolated IoT v42 producer gate preparation

- Commit `91a4537` records the host-only child/PCI teardown contracts and
  enforces checked-close proof before family removal. Three strict C11 GCC
  fixtures passed. This is still not bound to the vendor driver or ordinary
  image. See `docs/evidence/WR1200JS-IOT-V42-PCI-REMOVE-ORDER-2026-10-27.md`.
- Source follow-up found a second PCI removal ordering requirement: an active
  MBSS is refused by begin-remove before child unregister can call ndo_stop.
  The release owner must explicitly checked-close and join child ownership
  before MBSS removal; the current void PCI callback still ignores a failed
  `RtmpPhyNetDevExit`. See
  `docs/evidence/WR1200JS-IOT-V42-PCI-REMOVE-ORDER-2026-10-27.md`.
- Final #634 evidence: optional run `40527671413` passed on `0641d96`.
  Downloaded isolated `mt76x3_ap.ko` is 5,225,808 bytes, SHA256
  `46ef52aea556529ca4f711f267c5308f11978b223197dd2c2e85ce595d3cab3c`,
  matching the manifest; ELF32 MIPS32r2/O32. It is absent from the ordinary
  image. See `docs/evidence/WR1200JS-IOT-V42-CI-634-TARGET-COMPILE-2026-10-27.md`.
  Recovery worker, PCI release fence and late DMA/TxS lifetime proof remain
  open; no router runtime claim follows from this compile.
- Commit `0641d96` and its three preceding producer-gate commits were pushed
  together to `codex/wr1200js-service-webui`. ABI #584 (`40524113079`)
  and ordinary firmware #633 (`40524113504`) passed on this exact SHA;
  neither selected isolated v42. The optional v42 target run
  `40527671413` passed on the same SHA. Firmware
  #632 passed on the earlier `5ebf69d`.
- v42 has an isolated source binder for beacon/TIM producer tokens and a
  close/abort drain. Fresh local v39 → v40 → v41 → v42 preparation,
  strict C11 host fixtures, call-coverage and remove-ABI checks passed.
  MIPS v42 compilation passed in #634. Recovery owner, PCI release and late
  DMA/TxS lifetime proof remain open. See
  `docs/evidence/WR1200JS-IOT-BEACON-PRODUCER-GATE-2026-10-27.md`.

## 2026-10-27 beacon producer lifetime gate (host-only)

- Source inspection found that beacon/TIM frame preparation can retain packet
  pointers after `MBSS_Close` revokes submissions and before DMA/TxS counters
  become nonzero. Added a per-BSS, generation-bound producer gate contract and
  strict C11 passing test; evidence:
  `docs/evidence/WR1200JS-IOT-BEACON-PRODUCER-GATE-2026-10-27.md`.
- The host contract is now bound in the optional v42 source candidate, but
  not the ordinary firmware image. Deferred MBSS recovery, PCI release and
  late hardware reports remain unproven. #632 and ABI #583 passed on
  `5ebf69d`; they did not compile v42.

## 2026-10-27 optional IoT #629 host fixture failure

- Source audit after #631 found a concrete PCI-release hole in the isolated
  candidate baseline: `RtmpPhyNetDevExit` can return `FALSE` for retained
  MBSS removal, while `rt_pci_remove` ignores the return and proceeds to
  free the adapter/MMIO. See
  `docs/evidence/WR1200JS-IOT-V41-MBSS-RECOVERY-RELEASE-AUDIT-2026-10-27.md`.
  A host release-readiness guard now blocks registry reuse until its deferred
  owner is joined; strict C11 fixture passed. Kernel/PCI binding remains open.
  Source review found an existing `BcnRingLock` submission barrier, but
  pre-close beacon/TIM producers can hold packet pointers during preparation
  outside it. DMA/TxS zero snapshots do not prove those producers drained.
  Candidate remains excluded until a joined recovery owner and effective
  release gate are implemented and verified.
- Optional IoT-only v41 #631 (`40511894915`) passed on `3868270`. The
  downloaded `iot-merged-driver-probe` reports target compilation of
  `mt76x3_ap.ko`; its local SHA256 and byte count match the manifest.
  Evidence: `docs/evidence/WR1200JS-IOT-V41-CI-631-TARGET-COMPILE-2026-10-27.md`.
  This is an isolated module, absent from the ordinary image; kernel recovery,
  lifetime and physical acceptance remain open.
- Firmware #630 (`40449849750`) and Band Steering ABI #582
  (`40449849683`) both passed on `3868270`. One optional IoT-only v41
  run #631 (`40511894915`) was then dispatched on that exact SHA.
- Optional IoT-only v41 #629 (`40447432208`) failed in the standalone
  `check-mbss-close.c` host compile. The candidate include now calls
  `wake_up_all(&ad->wr_iot_ticket_wait)`, but the host mock lacked both the
  wait field and function. This is a fixture failure, not proof of a target
  driver compile failure. The fixture now models the wake, checks no wake on
  failed close and exactly one wake after successful retirement. Strict C11
  builds/runs passed locally in base, MT_MAC and MT_MAC+PCI variants.
  Evidence: `docs/evidence/WR1200JS-IOT-V41-CI-629-HOST-FIXTURE-2026-10-27.md`.
- #629 produced no MIPS candidate module. A new optional target run is needed
  after the fix is published and ordinary gates pass. Production and runtime
  acceptance remain open.

## 2026-10-27 MBSS recovery receipt host correction

- Host-only recovery completion no longer depends on the radio's mutable
  `busy`/`retired_serial` after checked close writes its exact per-record
  `IDLE`/stage-4 receipt under the adapter lock. The strict C11 fixture
  passed with a newer radio ticket and rejected an incomplete stage-3 record.
  Evidence: `docs/evidence/WR1200JS-IOT-MBSS-RECOVERY-RECEIPT-2026-10-27.md`.
  Kernel worker/lifetime binding and target tests remain open.
- Optional IoT-only v41 run #629 (`40447432208`) was dispatched after ordinary
  firmware #628 and ABI #581 passed on `48ffaef`; its result is pending.

## 2026-10-27 isolated v41 close ticket wake

- Post-#627 source review found the checked MBSS close retired its radio
  ticket without waking `wr_iot_ticket_wait`, contrary to the candidate wait
  helper's contract. The isolated close source now wakes after lock release
  only on successful retirement; the caller gate checks this ordering.
- Freshly generated v40/v41 trees passed caller coverage. Two negative wake
  mutations were rejected. Evidence:
  `docs/evidence/WR1200JS-IOT-V41-TICKET-WAKE-2026-10-27.md`.
  These bytes need a new target compile. Recovery owner, PCI release and
  beacon quiescence still block production installation.

## 2026-10-27 CI on published v41 gate repair

- Firmware #626 (`40431336149`) and Band Steering ABI #580
  (`40431336135`) both passed on `e73f9dc`. The ordinary firmware build did
  not select v41. These results do not prove IoT candidate target compilation.
- After both completed and the branch had no active run, dispatched exactly
  one optional IoT-only v41 run #627 (`40443241354`) on the same SHA. It
  passed; the downloaded MIPS module's size and SHA-256 match its manifest.
  Evidence: `docs/evidence/WR1200JS-IOT-V41-CI-627-TARGET-COMPILE-2026-10-27.md`.
  Recovery owner and PCI release gate remain unbound. No production image or
  router state was changed.

## 2026-10-27 optional IoT v41 CI #625

- Optional #625 (`40429949035`, SHA `2216583`) failed in the virtual-interface
  caller-coverage gate before MIPS target compilation. Original job
  `121944962949` shows that v41 moves MBSS DOWN through a checked executor;
  the gate still required the v40 direct callback call. The monitor's early
  log excerpt did not contain the causal late error.
- The gate now distinguishes v40 and bound v41 and checks the single v41
  callback/executor/DOWN chain. Both full local candidate checks and two
  negative mutations passed. Evidence:
  `docs/evidence/WR1200JS-IOT-V41-CI-625-COVERAGE-GATE-2026-10-27.md`.
  Candidate remains isolated; no v41 target module, production installation,
  or router proof exists. Publish the coherent fix, let ordinary CI finish,
  then run one optional v41 target compile on the exact published SHA.

## 2026-10-26 IoT v41 isolated stop binding

- Firmware #623 (`40391518751`) completed successfully on `f1960a8`; the
  Band Steering ABI run `40391518761` also passed. #623 is an ordinary image
  build and did not compile the new v41 candidate.
- Local commits `a3f57e4`, `b7b0f65` and `99b670b` record the v40 release
  barrier, stage a checked MBSS `ndo_stop` binding in an isolated copy, and
  add `v41` to optional IoT CI. A fresh v40 source tree generated from tracked
  v39 produced a v41 copy with 58 files verified byte-for-byte except for the
  one callback edit. Python syntax and workflow YAML parsing passed.
- The v41 manifest explicitly leaves recovery owner, PCI release gate,
  target compilation, production installation and runtime verification false.
  It must not enter the firmware image. After these commits are published and
  the resulting ordinary build completes, run one optional IoT-only v41 target
  compile on the exact published SHA. Then continue retained-close recovery
  and PCI adapter-lifetime binding.

## 2026-10-26 CI after IoT-only workflow repair

- Optional #622 (`40387415111`) succeeded on published `b2ec889`, including
  isolated v40 MIPS module compilation. The downloaded module and SHA-256 were
  independently checked; full limits and the nonfatal `modpost` warning are in
  `docs/evidence/WR1200JS-IOT-V40-CI-622-TARGET-COMPILE-2026-10-26.md`.
  Candidate remains outside the production image and unverified on hardware.
- Firmware #621 (`40385894396`) and Band Steering ABI `40385894121` succeeded
  on published `b2ec889`. #621 uploaded the WR1200JS image and download ZIP;
  it did not select the optional IoT v40 candidate. Its config and radio
  capacity artifacts are summarized in
  `docs/evidence/WR1200JS-BUILD621-IOT-BASELINE-2026-10-26.md`.
- After confirming no queued/running run on that branch and exact remote SHA,
  dispatched one optional WR1200JS run #622 (`40387415111`) with
  `run_candidate_checks=true`, `candidate_scope=iot`, variant `v40` on
  `b2ec889`; it completed successfully. No driver was installed in production
  or on the router.

## 2026-10-26 optional IoT CI #620 failure and repair

- Optional firmware run #620 (`40381625442`, SHA `676b020`, IoT v40 scope)
  completed with failure in `Compile isolated merged IoT MT7603 candidate`.
  The ordinary firmware image had built and uploaded before this optional step;
  the `iot-merged-driver-results` artifact was absent. The original job log
  reports exit code 1 immediately after the step starts, with no compiler
  output. Workflow source shows its first `test -d "$driver"` requires the
  isolated kernel tree made only by the Band Steering step gated to `all`.
  Thus the `iot` scope skipped that prerequisite; this is a CI orchestration
  failure, not evidence that v40 did or did not compile.
- The published workflow now copies and configures its own isolated kernel tree for
  `iot` scope and emits a specific error if the tree is absent. `all` retains
  the preexisting full Band Steering tree. YAML parsing and scoped diff check
  passed locally; #622 confirmed the repaired target compilation. No production
  driver or router state changed.
- Agent monitor run `40383532268` identified the failed job and step, but its
  first-16-MiB excerpt missed the late failure. The feature-branch monitor now streams a
  bounded last-16-MiB suffix and has a >16-MiB offline regression fixture.
  Nim compilation and the monitor fixture passed; this parser change is not
  yet part of the default-branch monitor workflow.

## 2026-10-26 IoT v40 target check

- With local (unpublished) fixture changes, a fresh v40 candidate was staged
  from the pinned v39 candidate and its checked-close function extracted.
  Strict C11 host builds/execution passed in plain and MT_MAC modes. The
  synthetic fixture now mocks the checked radio-off call and MT_MAC fields,
  and tests HALT clearing in normal close versus retention on PM suspend.
  This temporary preparation emitted no assembly manifest and is not a target
  driver compile or production installation. The optional CI run below tests
  published `676b020`, not these local bytes.

- Ordinary firmware #619 (`40377110297`) and Band Steering ABI
  `40377110309` both passed on published `676b020`. A single optional
  WR1200JS `run_candidate_checks=true`, `candidate_scope=iot`,
  `iot_candidate_variant=v40` run was dispatched as `40381625442` on the
  same exact SHA. It was in progress at the latest check. This is an isolated
  candidate probe; no production driver installation or device acceptance.
- Local docs/cache commits `1c400bd` and `c469f5a` remain unpublished while
  that run is active. Do not launch a duplicate build or push them into its
  branch until this run reaches a terminal result.

## 2026-10-26 Actions storage and Mi Mini preservation

- Mi Mini diagnostic radio runs `38130857982` and `37136824063` succeeded
  for isolated compile/link only. Their artifact API lists no remaining
  bundles. Exact commits, job results and limits are recorded in
  `docs/evidence/MI-MINI-RADIO-PROBE-CI-2026-10-26.md`, committed locally as
  `1c400bd`; publication waits for active WR1200JS firmware `40377110297`.
- Deleted 30 oldest WR1200JS compiler caches by ID, releasing 7,117,485,674
  bytes according to their pre-delete sizes. The cache-list API verified 35
  entries and 3,448,974,011 bytes afterward; workflow history and artifacts
  were retained. A local workflow edit now selects one UTC-day cache key with
  old-key restore fallback; this is statically checked but not CI-tested.
  See `docs/evidence/ACTIONS-STORAGE-AUDIT-2026-10-26.md`.

## 2026-10-26 CI recompilation audit

- While CI on `676b020` runs, the existing v39 checked-close synthetic host
  fixture was extracted. Its missing MT_MAC mock watchdog/chipCap/TxS fields
  were added locally, then both plain and MT_MAC variants passed strict C11
  compilation and execution. The fixture has PCI support hard-coded; this
  does not independently test PCI-off behavior or prove target compilation.
  No router or firmware state was changed.

- Firmware `40374656513` and ABI `40374656233` completed successfully on
  `721fe60`. After confirming remote branch still pointed to that commit,
  published local IoT commits `472c2ca`, `1ac816a`, `690206d` together with
  scoped workflow commit `676b020` by one normal fast-forward SSH push.
  New SHA `676b020` has not yet passed CI or an optional v40 target compile.
  Ordinary firmware `40377110297` and ABI `40377110309` started on this SHA;
  both were in progress at the latest check. Do not dispatch duplicates.

- Ordinary WR1200JS PR builds do not run isolated candidate compilations unless
  `run_candidate_checks` is selected. Disabled EoIP and StrongSwan have final
  ROMFS exclusion checks, not separate service builds. The optional successful
  run `40368551644` restored ccache and reported 10,378 hits / 42 misses
  among cacheable calls (99.60% hit rate); final image checks still need the
  current source and effective config.
- Published workflow commit `676b020` adds `candidate_scope`: manual candidate checks default
  to IoT only; `all` explicitly retains the full isolated candidate suite.
  YAML parsing, all 21 optional-step scope checks and `git diff --check`
  passed locally. No manual firmware build was started for this edit; the
  branch push may trigger ordinary CI automatically.

## 2026-10-26 IoT continuation

- Published `1ac816a` adds a per-record checked-close executor claim under the
  adapter lock. A reentrant same-ticket call during vendor close is rejected;
  success, deferred DMA/TxS, and error paths release the claim only for the
  same registration generation. Published `690206d` carries that field into the
  v40 generator, which otherwise copied an older v39 header. Fresh generated
  v40 source passed three strict host close variants (plain, MT_MAC and
  MT_MAC/PCI), plus interface-reference and recovery-owner fixtures; Python
  syntax and scoped diff checks passed. Ordinary firmware `40374656513` on
  parent `721fe60` passed. Target MIPS compilation
  of these new bytes and production binding remain pending.

- Published `472c2ca` makes the optional checked-close host fixture valid for
  MT_MAC without PCI as well as MT_MAC/PCI, and adds that CI variant. Three
  strict C11 host variants passed; workflow YAML parsed and scoped diff check
  passed. Ordinary firmware `40374656513` and ABI `40374656233` on parent
  `721fe60` passed; no duplicate build was dispatched.

- Published commit `721fe60` adds an optional v40 CI host fixture for the
  MT_MAC/PCI close path. It supplies bounded vendor stubs and tests that
  pending beacon DMA or TxS retains close stage 2 and the module reference.
  Both plain and MT_MAC/PCI strict C11 fixtures, workflow YAML parsing and
  scoped `git diff --check` passed. Optional run `40368551644` on parent
  `bd9f49a` passed, including isolated MT7603 target compilation. Ordinary
  firmware `40374656513` and ABI `40374656233` are in progress on `721fe60`;
  they do not select v40. This is host coverage,
  not a production `ndo_stop` or router result.

- Optional v40 run `40360064346` completed successfully on `59db347`,
  including isolated MT7603 candidate compilation. Follow-up commit
  `bd9f49a` was pushed: checked MBSS close and its recovery-owner model now
  reject a ticket whose operation disagrees with the admitted vendor count or
  whose reset kind is nonzero. Focused strict C11 host tests and scoped
  `git diff --check` passed. The host close fixture was run without `MT_MAC`;
  its MT_MAC variant lacks vendor stubs and is not target-compile evidence.
  Production binding, final image inclusion and router operation remain open.

- On `59db347`, ordinary firmware run `40357156009` and Band Steering ABI
  `40357155947` completed successfully. Neither selects the optional v40
  driver. The later ticket-provenance gate is now in `bd9f49a`; ordinary
  firmware `40363573850` and ABI `40363573442` were in progress at the latest
  check. Neither substitutes for optional v40 target compilation on this SHA.

- The generated v40 checked MBSS close now records the admitted ticket's
  epoch, prior radio phase/readiness and vendor count in its interface record
  before unlocked vendor work. It rejects altered ticket provenance before
  any close mutation and rechecks that provenance at each close milestone.
  The existing recovery-owner model accepts only that recorded ticket and
  copies it for continuation; main-down epoch drift retains the original
  admitted ticket. Fresh v40 generation, both focused strict C11 fixtures,
  the checked-stop source gate and `git diff --check` passed locally. This
  remains isolated candidate source; target compilation of these new bytes,
  real worker binding, production image integration and device operation are
  still pending. The coherent code/test change was published as `59db347`;
  this status update remains local alongside pre-existing document edits.

- The existing host-only MBSS recovery owner now retains the complete radio
  close ticket (serial, epoch, operation and prior state) for an incomplete or
  uncertain close. Its copy helper returns that same ticket only while the
  matching record and radio transition still authorize continuation. The
  focused C11 fixture rejects absent and altered-epoch tickets in the normal
  phase and keeps the original ticket when main-down advances the epoch during
  an admitted close. It passes after the change. This closes a model-level
  gap; no worker, kernel reference
  pin or production `ndo_stop` binding has been added.

- Optional v40 workflow `40350468431` completed successfully on `cde9846`:
  the `Compile isolated merged IoT MT7603 candidate` step passed after the
  ordinary WR1200JS image build. This proves target compilation of the
  generated candidate, not inclusion in that image or operation on the router.
  The generated v39-derived `MBSS_Remove` still begins beacon teardown before
  any explicit `dev_close`, while the compiled checked MBSS close remains
  unbound and legacy `ndo_stop` discards close errors. The next lifecycle
  change must bind an owned, retryable close and prove its result before beacon
  deinit, detach or adapter release; adding a bare preclose call would not
  establish this because `RtmpOSNetDevClose` returns void and PCI remove
  currently ignores `RtmpPhyNetDevExit` failure.

- Published commit `cde9846` closes a final RX DMA read race in
  isolated v40: `NIC_NOT_EXIST` is checked again before the helper reports
  idle. Fresh generation and strict host C11 fault tests passed against the
  generated helper, including disappearance on the final read. Firmware #611
  (`40341400065`) on parent `54061d3` completed successfully before this
  push. Ordinary firmware #612 (`40344805795`) and ABI `40344805641`
  completed successfully on `cde9846`; neither selects the optional v40
  compile. The separate optional run `40350468431` then passed that step.

- Owner removed HTOP/MTR from the required firmware on 2026-10-26. The
  WR1200JS profile now has both selectors commented; an operator can enable
  either for a separate diagnostic build, subject to target/image checks.
  This supersedes older notes that call package integration mandatory item 4.

- Published `6bae503` on `codex/wr1200js-service-webui`: the optional v40
  candidate CI step now compiles and runs the exact generated checked DMA-poll
  helper with TX/RX disappearance fault cases. Local strict C11 execution,
  workflow YAML parsing and `git diff --check` passed. At the last check,
  ordinary firmware run `40335749228` was queued and Band Steering ABI run
  `40335749283` was in progress on this SHA. Neither is optional v40 target
  compilation; do not dispatch a duplicate build while one is active.
- Source reachability remains open: generated v40 `MBSS_VirtualIF_Close` is
  still the legacy `ndo_stop`, discarding close and DOWN results. The compiled
  `wr_iot_mbss_close_checked` symbol is not yet bound to an owner that can
  retain netdev/module references across failed `dev_close` or PCI removal.
  A direct callback substitution would not safely solve the lifetime problem.
  No production driver, image installation or router state changed.

This section is the current handoff. Older time-specific notes below are
historical; their pending-run and local-only statements are superseded here.

- Current writer: Sol, branch `codex/wr1200js-service-webui`; published code
  baseline `a71e8ab`; follow-up IoT candidate commits are published.
  Preserve all unrelated modified and untracked files.
- Local and GitHub branch HEAD match at documentation commit `ba118ea`.
  Firmware #601 (`40218879277`) and service ABI `40218879240` on its parent
  `c2b1d48` completed successfully. Service ABI `40219026319` on `ba118ea`
  also completed successfully; ordinary firmware #602 (`40219026350`) was
  still in progress at the 2026-10-25 check. These documentation-triggered
  runs do not select the optional IoT candidate.
- Candidate build #600 (`40216625327`) completed successfully on `a71e8ab`.
  Its ordinary WR1200JS firmware build and optional `Compile isolated merged
  IoT MT7603 candidate` step both passed. The separate probe artifact contains
  `mt76x3_ap.ko`, ELF32 MIPS32r2/O32, 5,202,152 bytes, SHA-256
  `f01a3272ac60769dd08a312fbe67622284fa590a533285335a749a300b75a4e5`.
  This is candidate target-compilation evidence only: the candidate was built
  after the firmware image and is not installed in that image. The log has one
  non-fatal `modpost` section-mismatch warning. Full details:
  `docs/evidence/WR1200JS-IOT-V40-CI-600-TARGET-COMPILE-2026-10-25.md`.
- Firmware #594 (`40205825840`) and Band Steering ABI `40205825793` passed on
  `3d6c602`. Optional IoT candidate build #595 (`40207139904`) also passed:
  its isolated MT7603 driver compiled to MIPS32r2 `mt76x3_ap.ko`. See
  `docs/evidence/WR1200JS-IOT-V39-CI-595-TARGET-COMPILE-2026-10-25.md`.
- Firmware #597 (`40212920316`) completed successfully on `971a899` and
  published the WR1200JS image/ZIP artifacts. It builds the unchanged
  production driver; this does not validate or package the IoT v39 candidate.
- The ordinary firmware image still uses the production driver. Isolated
  compilation does not establish packaging, lifecycle safety, IoT isolation,
  on-device operation or release acceptance. No router write or reboot occurred.
- Source reachability review of generated v40 found that main close still uses
  legacy `VIRTUAL_IF_DOWN`/`rt28xx_close` and releases the module pin without
  checked physical completion. The separate main-open owner candidate ends in
  `UNVERIFIED` with `main_ready=0`, so it cannot admit IoT BSS open until a
  reviewed radio-ready observation is bound. Legacy family count writers also
  bypass the owner. See the follow-up in the #600 evidence report.
- A local main-readiness completion gate now pairs a VERIFY ticket with the
  owned MAIN record and exact vendor count under one adapter lock. Its strict
  C11 host fixture passed seven valid/failure cases. This helper is not bound
  to the vendor source; source integration, MIPS compilation and hardware
  observation remain open. See the #600 evidence report.
- Local source review corrected the MT7603 main observer's IoT beacon-queue
  mask from bit 2 to the driver's BSS-2 bit 17. The focused host fixture
  failed before the correction and passes afterward; generated candidates,
  target compilation and firmware image have not yet incorporated this edit.
  A second host fixture failure showed that the observer's old
  `!netif_running(iot)` condition rejects IoT during its own `ndo_open`:
  pinned Linux sets START first. That condition is removed; ticket/registry,
  beacon request and queue bit 17 now provide the separate checks. No new
  target or device evidence is claimed.
  The optional candidate CI step now checks the staged observer header and
  requests its MIPS compile probe. Workflow YAML parsing, whitespace check
  and focused host fixture passed locally; a new target run remains pending.
- The staged MBSS wrapper still leaves every successful guest/IoT open in
  `UNVERIFIED`; guest-first therefore blocks IoT admission. Raw CR_ENABLE
  return is ignored. A local unbound post-open BSS configuration observer now
  checks guest/IoT request and register queue bits; strict host cases passed.
  It needs checked CR_ENABLE, partial-failure ownership and same-ticket
  revalidation before it can publish READY. See the #600 follow-up report.
- The local IoT assembler now checks the raw MBSS `CR_ENABLE` result and
  routes failure after claimed virtual UP to the existing uncertain-open
  ownership path before HNAT/queue publication. Python syntax and exact
  source-anchor checks passed locally. This is not regenerated/MIPS compiled;
  the retained-resource recovery owner and post-open READY path are still open.
  A focused host fixture now compiles the actual transformed raw wrapper and
  passes five injected paths, including CR_ENABLE failure retaining module
  pin/vendor count without publishing the queue. This remains host evidence.
  The optional IoT candidate CI step now runs this fixture on the assembled
  driver before target compilation. Workflow YAML parsed locally; no new
  candidate CI run has executed this gate yet.
- Next IoT gate: bind and fault-test PCI removal, deferred-close join, checked
  child/root teardown and adapter-release ownership before production install.
  Follow-up source check confirmed that v39 still discards the checked teardown
  result and has no bound recovery worker; the persistent-failure path of the
  `void` PCI callback remains unresolved. See
  `docs/evidence/WR1200JS-IOT-PCI-RETIREMENT-OWNER-2026-10-25.md`.
  The host-only owner now checks stop-request-before-join ordering; its strict
  C11 fixture passed. Actual stop/join and persistent-failure ownership remain
  unbound. Root `MainVirtualIF_close` also discards physical-close status and
  releases its module pin; main stop needs checked ownership and an actual
  RF/DMA-quiescence receipt before PCI free. The checked driver close reports
  software shutdown only. More specifically, its radio-off call always
  returns `FALSE` for MT7603's `HIF_MT`; the MT-specific alternative is void
  and does not report DMA/radio/PDMA results. A checked MT close is now
  target-compiled in isolated v40; main-stop and PCI ownership binding remain.
  The v40 source generator creates a separate checked MT radio-off candidate.
  Python syntax, generation, strict host fault tests and source-shape checks
  passed; target C compile is now verified by #600, while production-image
  inclusion and runtime proof remain open. See the PCI-retirement evidence.
  Firmware #598 (`40215206293`) and Band Steering ABI
  (`40215206230`) both completed successfully on `9916538`; neither is a v40
  compile. Commits `83289bd`, `b1953b2` and `8fe91c0` add v40 dispatch,
  failure tests and caller-coverage checks. The generated v40 source passed
  `check-remove-result-abi.py` locally (8 source/header pairs).
  A host GCC fixture now executes the generated checked-off C body with
  injected DMA/MCU/PDMA/readback failures; strict C11 passed. The fixture by
  itself does not establish target compilation or radio silence; #600 supplies
  separate target-compilation evidence. Fixture and optional CI hook
  are in `b1953b2`.
  The local five-family virtual-interface coverage checker initially failed
  because it assumed WDS remove still returns `VOID`; the reviewed candidate
  uses `INT`. Its signature boundary now accepts those two known forms and
  both v39 and v40 overlays pass the same caller/registration inventory.
  A main-stop host-model bug is fixed locally: an unverified physical close
  now retains its CLOSE ticket, which v40 needs for the same-ticket retry.
  Its strict C11 fixture passed including rejection of a competing writer.
  The dependent model files stay local with their modified shared headers;
  caller-coverage checker and CI gate are in `8fe91c0`.
  The prepared commits were pushed and optional v40 run #600 completed; its
  target compilation and artifact evidence are recorded above.
  Vendor `MainVirtualIF_close` and PCI removal are still unbound.
  Then verify network isolation and Classic WebUI. Optional HTOP/MTR selectors
  are excluded from the required image by the 2026-10-26 owner decision. Do not start
  Modern UI until the required earlier stages are complete.
- The `padavan-ci` one-minute Codex heartbeat stays paused. GitHub monitor runs
  on failures; its `main` checkout may still use the older excerpt heuristic.
  Confirm any failure in the original job log and diagnostic artifact.

## Historical session notes (superseded by current status above)

## Sol resumed execution — 2026-10-25

Sol accepted the user's direct role transfer after DeepSeek handoff `6f459de`.
The shared branch matched GitHub; 177 modified/untracked working-tree entries
remain intact. Priority: complete IoT, then verify Zapret2 and Modern WebUI.
Firmware run `40190118803` was in progress at acceptance, with no final image
or on-device verification inferred.

## IoT PCI remove lifetime gate — 2026-10-25

Reviewed the latest isolated MT7603 candidate: `rt_pci_remove` ignores the
`BOOLEAN` child-teardown result and calls `RTMPFreeAdapter` through
`RtmpRaDevCtrlExit` immediately. A deferred close worker cannot safely be
bound until the remove path enforces quiescence, work join, checked child
completion and adapter release ownership. Exact source path and next gate:
`docs/evidence/WR1200JS-IOT-PCI-REMOVE-LIFETIME-2026-10-25.md`. No production
driver, image or router change was made.

The isolated v38 PCI probe-failure control flow was separately traced. It
does not publish child netdevs before the ordinary error unwind, so the
successful-probe remove hazard must be solved in its own retirement owner.
Partial-allocation and callback quiescence still need fault injection; see
`docs/evidence/WR1200JS-IOT-PCI-PROBE-UNWIND-2026-10-25.md`.

## IoT close/removal admission guard — 2026-10-25

The isolated registry model now refuses a new netdev removal while a prior
checked close remains `CLOSING`. The strict C11 fixture passed. A deterministic
v39 candidate contains exactly that one source-file change from v38; see
`docs/evidence/WR1200JS-IOT-CLOSING-REMOVE-ADMISSION-2026-10-25.md`.
Deferred completion and PCI adapter release remain open, so v39 is not ready
for the firmware image.

## IoT PCI retirement owner order — 2026-10-25

Added a host-only single-owner sequence for PCI `remove` that refuses adapter
release until admissions are fenced, work joined, child and main teardown
proven, and the existing physical/callback release gate passes. Strict C11
fixture passed after correcting its initial phase assumption. Evidence:
`docs/evidence/WR1200JS-IOT-PCI-RETIREMENT-OWNER-2026-10-25.md`. No vendor
binding or production image change; actual work join and quiescence proofs
remain to implement.

## IoT v39 prepared-source merge — 2026-10-25

The v39 candidate was merged into the saved prepared MT7603 source in a
separate output tree. Its 55 source paths include 36 pinned originals and
five prepared-source overlaps; the known single adapter-init conflict was
resolved by the existing strict rule. All output hashes and conflict-marker
checks passed. This is source integration only: no local MIPS toolchain/WSL
distribution or v39 CI input was available, so target compile remains open.
Evidence: `docs/evidence/WR1200JS-IOT-V39-PREPARED-SOURCE-2026-10-25.md`.

## IoT v39 optional CI input — 2026-10-25

Versioned v39 source overlay, pinned manifest and an explicit optional CI
selector are now local. Default candidate selection remains legacy and the
production firmware driver is unchanged. Local manifest, merge, overlap,
workflow YAML and diff checks passed; no commit/push/CI execution yet. See
`docs/evidence/WR1200JS-IOT-V39-CI-INPUT-2026-10-25.md`.

Follow-up: the isolated v39 input and selector were committed as `6d67414`
and pushed to `codex/wr1200js-service-webui`. Automatic firmware run #587
(`40195057638`) and Band Steering ABI run #555 (`40195057593`) were both
in progress when checked on 2026-10-25. They use the default path and do not
compile v39. Dispatch one optional run with `run_candidate_checks=true` and
`iot_candidate_variant=v39` only after the active firmware run is complete
and the queue is clear. A successful candidate compile would not establish
safe PCI removal, a production activation backend, or device acceptance.
ABI #555 subsequently completed successfully; firmware #587 was still in its
`Build WR1200JS firmware` step at the next check. The ABI result is evidence
for that workflow only and does not compile the optional v39 candidate.
Firmware #587 later completed successfully on `6d67414`. With that run
terminal and no queued/running duplicate on the ref, one optional v39 run
was dispatched: #588 (`40195811064`), inputs `boards=wr1200js`,
`run_candidate_checks=true`, `iot_candidate_variant=v39`. Its result is
pending; no target-compile claim is made from dispatch alone.

Follow-up: #588 failed in the isolated candidate compile. The target compiler
saw `ApCli_Remove` as `void` at the checked call in `ap_cfg.c`, because the
candidate changed the definition to `INT` without its `ap_apcli.h` declaration.
The focused declaration/manifest correction is local and passed source merge
and syntax checks; target recompilation is pending. See
`docs/evidence/WR1200JS-IOT-V39-CI-588-APCLI-ABI-2026-10-25.md`.
Follow-up: the focused correction was committed as `3ee7220` and pushed.
Automatic firmware #589 (`40197704591`) and ABI #556 (`40197704453`) were
in progress on that commit at the first check. Neither is the optional v39
compile; wait until the firmware run is terminal before dispatching one new
candidate run. The other dirty working-tree entries remain untouched.

## Zapret2 build #586 image verified — 2026-10-25

Run `40190599321` succeeded at `5953fc4`. Its downloaded target audit
passed all 51 checks, including Zapret2 entrypoints, pinned Lua/license,
service markers, compiled Classic WebUI/dictionaries and MIPS ELF dependency
closure. TRX: 13,064,690 bytes, SHA256
`d306846066729f2761125ad33e1f1f2e72ce3e61348e56aa42408cbd40c9799e`.
Source-to-image integration is confirmed; browser/device behavior and
NFQUEUE traffic effect remain unverified. Evidence:
`docs/evidence/WR1200JS-BUILD586-ZAPRET2-2026-10-25.md`.

## Historical HTOP/MTR integration request — 2026-10-25; superseded

User requested reusable, profile-gated HTOP and MTR support for compatible
Padavan 4.4.198 boards. The task is recorded in
`docs/PROJECT-DELIVERY-SCOPE.md` after IoT and service WebUI. No build recipe,
profile, firmware image or router was changed for this task. WR1200JS is the
only admitted image-build profile; Mi Mini and Mi 4 require separate board
and resource evidence before package inclusion. Next when this stage opens:
check pinned recipes/dependencies, then integrate and measure each eligible
profile against an identical image baseline.

Superseded by the 2026-10-26 owner decision at the top of this file: these
tools are optional, default-off diagnostics and are not a release gate.

## IoT deferred close completion receipt — 2026-10-25

Fixed a host-model race: completion is recorded under the adapter lock before
a later radio ticket may replace `retired_serial`; joined work then releases
the owner from its own receipt. Strict C11 negative/interleaving fixture
passed. Still no production worker or PCI release binding. Evidence:
`docs/evidence/WR1200JS-IOT-AUX-CLOSE-ADMISSION-2026-10-25.md`.

## IoT deferred close lifetime contract — 2026-10-25

Added host-only recovery-owner state and a strict C11 fixture. It retains
the deferred adapter owner across failed/queued WDS close work and refuses
release until checked completion plus work join. Production PCI remove and
worker binding remain open; this does not prove target or device behavior.
Evidence: `docs/evidence/WR1200JS-IOT-AUX-CLOSE-ADMISSION-2026-10-25.md`.

## IoT WDS partial-DOWN reconciliation candidate v33 — 2026-10-25

The isolated WDS stop candidate can now reconcile a successful checked DOWN
whose ticket finish failed: it claims the recorded stage and never decrements
the vendor count again. Host C11 extracted-wrapper and five-family source
checks passed. A retained worker and target-driver build remain open; no
image or router change. Evidence:
`docs/evidence/WR1200JS-IOT-AUX-CLOSE-ADMISSION-2026-10-25.md`.

## IoT WDS retained retry candidate v32 — 2026-10-25

The v32 isolated WDS close tree now carries the matching reference header
and a same-ticket continuation guarded against concurrent retry. Extracted
host C11 wrapper and five-family source gate passed. No worker invokes it,
successful-DOWN partial completion is not reconciled, and no target build or
device test was run. Keep out of the image. Evidence:
`docs/evidence/WR1200JS-IOT-AUX-CLOSE-ADMISSION-2026-10-25.md`.

## IoT AUX_CLOSE retry gate — 2026-10-25

The host model now retains the original AUX_CLOSE ticket identity after a
failed non-last WDS DOWN and permits only a same-ticket, unchanged-count,
unmutated-DOWN retry. Strict C11 fixture passed. No recovery worker, target
build or device test; v31 stays isolated. Evidence:
`docs/evidence/WR1200JS-IOT-AUX-CLOSE-ADMISSION-2026-10-25.md`.

## IoT overlay conflict gate — 2026-10-24

Added `tools/iot/check-overlay-conflicts.py` and documented the local #542
artifact check in `docs/evidence/WR1200JS-IOT-OVERLAY-CONFLICTS-2026-10-24.md`.
The 31 pinned originals pass; the partial RSSI-prepared fixture conflicts on
four changed paths. Replayed 20 precompiler Band Steering stages and five RSSI
stages on a scratch copy of the verified full upstream archive. That complete
driver has five conflicts: `ap/ap.c`, `ap/ap_cfg.c`, `common/rtmp_init.c`,
`hw_ctrl/cmm_asic_mt.c`, `include/rtmp.h`. The remaining Band Steering ABI
probe/package stages were not run without a target compiler; source inspection
shows no additional MT7603 writes. Next: merge those five files deliberately,
then isolate and target-compile the resulting IoT candidate.
An LF-normalized three-way probe found four text-clean merges and one real
same-anchor conflict in `common/rtmp_init.c`, where RSSI and IoT both initialize
state before adapter publication. Review all merged files; retain both init
sequences in the one conflict. See the evidence note for exact provenance.
An isolated full merged MT7603 candidate is now staged by
`tools/iot/assemble-prepared-candidate.py` in sibling scratch. It verifies
input hashes and the five-file overlap, retains both initialization sequences,
and records 45 output hashes. Local hash/marker checks passed. It is not
target-compiled or installed; next is source review plus exact WR1200JS
target compile and lifecycle gates before production inclusion.
Current local generator output normalized to LF exactly matches all 45 staged
hashes from the #542 candidate. Optional isolated target compilation was added
to the firmware workflow and pushed as `5a09fc7`; normal image remains
unchanged. Await the baseline PR checks for that commit, then dispatch one
`run_candidate_checks=true` run if no equivalent run exists. Do not call this
compiled or device-accepted before CI evidence arrives.
At the latest read, baseline build #543 (`40045468630`) and ABI run
`40045468649` for `5a09fc7` are both in progress. The local merged-source
manifest has 45 paths, no conflict markers, and all compile/install/runtime
claims false. Do not dispatch the optional candidate run while these PR checks
occupy the branch queue.
Build #543 and ABI run `40045468649` both completed successfully. After
confirming no queued/running duplicate on this ref, dispatched exactly one
optional `run_candidate_checks=true` WR1200JS run: `40046513315`, head
`5a09fc7`. It was in progress at last read. This is the first attempt at
isolated target compilation of the merged IoT candidate; its result is not yet
known. Even a successful compile would leave issuer binding, lifecycle
exclusion, beacon/TxS retirement and device runtime gates open.
No production driver, image, or router change from this check.

## Beacon DMA-map failure gap confirmed — 2026-10-23

Pinned ring has 20 slots. PCI map helper returns zero on dma_mapping_error;
RtmpPCIMgmtKickOut does not check it and still writes descriptor/CPU index.
Candidate manifest now explicitly denies atomic ring admission and PID submit
accounting. Next implementation needs checked ring admission, DMA error
propagation and PID settlement before IoT TxS completion can be trusted.
No production/device change. See IoT contract.

## Beacon ring/TxS reservation gap confirmed — 2026-10-23

Source trace: ap_connect checks free beacon ring space without BcnRingLock,
then creates TxS PID; later kickout locks ring but does not recheck capacity
or roll back PID after failure/guard return. PCI kickout always returns zero
in reviewed body and cannot prove hardware completion. Next candidate must
atomically admit ring slot and account for reserved PID or quarantine missing
completion before IoT BSSID retirement. Exact lines in IoT contract.

## TxS occupied-PID overwrite prevented in partial candidate — 2026-10-23

Updated exact-blob TxS stage across txs.c, mt_mac.h and all four mt_mac.c
callers. Under metadata lock it scans for free PID; full table disables host
TxS for that frame without overwriting a live record. Strict extracted-function
host checks passed skip/full/wrap/duplicate cases. Unified partial bundle:
../iot-unified-txs-no-overwrite-v2-20261023. Late PID reuse, missing reports,
target compile and router runtime remain open; no production installation.

## TxS PID metadata lock staged in partial candidate — 2026-10-23

Exact-blob gated txs.c + mt_mac.h candidate now gives Add/Remove a dedicated
IRQ-safe short metadata lock, with init/free hooks. Reassembled partial driver
in ../iot-unified-txs-lock-v2-20261023; extracted actual functions passed
strict local GCC cases for PID return/wrap, completed rate, duplicate/unused
rejection and modeled lock release. This does not solve occupied PID overwrite,
shutdown callback quiescence or target/runtime acceptance. No router change.

## Generated TxS removal fixture passed locally — 2026-10-23

Extracted actual staged RemoveTxSStatus into host fixture. MinGW GCC strict
build/run passed first, duplicate and unused PID cases plus correct rate slot.
ABI workflow now stages the same generated fixture with Linux sanitizers after
partial assembly; workflow has not run for this edit. Parser/concurrency,
collision and target runtime remain unproved. See IoT contract.

## Pinned TxS parser correction staged — 2026-10-23

Added exact-blob gated TxS parser candidate and included it in the separate
partial driver assembler. Generated diff rejects unused/out-of-range PID and
fixes TxRate indexing; standalone and unified assembly succeeded. Evidence:
../iot-txs-candidate-20261023 and ../iot-unified-txs-20261023 manifests.
No synchronization, collision or callback retirement proof; target not built,
candidate not installed and router unchanged. See IoT contract.

## Global TxS allocator scope confirmed — 2026-10-23

Four management/data submissions share the eight-bit PID table; one parser
consumes completion. Removal accepts even an unused slot and parser ignores
its result. A beacon-only patch would leave collision/late-result behavior
unresolved. Next code change must cover all producers and common parser with
real target evidence before using TxS as an IoT unregister fence. See contract.

## Beacon TxS PID reuse is an IoT retirement gate — 2026-10-23

Pinned beacon producer writes BSSID index into TxSPriv. The 256-slot TxS PID
table overwrites an occupied slot and only increments TxSFailCount, so a late
completion cannot be safely attributed by a generation tag alone. A checked
PID allocation/overflow policy and missing-report drain proof are required
before selective IoT BSSID reuse. Source evidence in IoT contract. Candidate
not installed; no target build or router change.

## Beacon DMA and TxS paths traced — 2026-10-23

Pinned driver source has a beacon DMA completion path under BcnRingLock and a
separate TxS callback indexed by BSSID only. Recovery flush re-enables beacon;
global TxS table exit is adapter-wide. None proves selective old-generation
TxS retirement before IoT slot reuse. Keep registry vendor_done blocked until
a per-BSS drain protocol or verified adapter-wide lifetime boundary exists.
Source locations and exact limitation recorded in IoT contract. No driver,
image or router changed. Post-firmware self-contained-source stage remains
queued after firmware acceptance in PROJECT-DELIVERY-SCOPE.md.

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
Pinned mt76x3 `ap/ap.c` audit: `APStop` writes beacon IDLE after setting HALT;
PCI `APShutdown` calls it, and reconfiguration paths also call it. `APStartUp`
writes IDLE on startup. `APStopBssOnly` has another unlocked write but no
caller in the pinned driver tree; it is not evidence of an active IoT close.
New isolated `iot-unified-ap-state-lock-20261023` stages PCI `BcnRingLock`
around the `APStartUp` and `APStop` IDLE writes. Assembler completed; generated
source and manifest inspected. This does not prove callback drain, PID reuse,
reset/deinit safety or target compatibility. No production install, target
build or router change. Next establish producer quiescence and retirement.
Follow-up direct-writer audit found `APCheckBcnQHandler` beacon recovery.
The existing radio-error stage already locks final HW re-enable and IDLE;
new isolated `iot-unified-beacon-recovery-stop-20261023` adds a STOP rejection
inside that lock. Assembler completed; generated-vs-stage diff has one added
condition and one manifest record. Earlier recovery-lock/merge attempts are
superseded. Full reader/lifetime and target build/device proof remain open.
The AP debug `BcnStateCtrl` ioctl is compiled under pinned AP `-DDBG`; its
original handler lacked a BSS bound and narrowed the parsed state before
validation. `iot-unified-beacon-debug-guard-v2-20261023` stages bounds,
full-width validation and a locked state decision, preserving the radio-error
stage. Generated code and manifest inspected; target/production remain false.
Local toolchain archive contains an ELF GCC; WSL list exited 1 without a
distro, so no local target compile was available in this Windows session.
The latest isolated bundle `iot-unified-beacon-lock-forms-20261023` rejects
debug state changes from STOP/HALT/NIC-missing and inventories both SEM and
IRQ lock forms for `BcnRingLock`. Pinned macros differ under
MULTI_CORE_SUPPORT; actual WR1200JS translation-unit flags are unverified.
Manifest explicitly marks lock semantics unproved and target/production false.
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

## IoT beacon PID submit boundary — 2026-10-23

Pinned MT_MAC source shows beacon TMAC construction reserves TxS PID before
enqueue, but `RT28xx_UpdateBeaconToAsic` carries neither a typed reservation
nor a checked submit result. Big-endian conversion changes packet descriptor
bytes before kickout. Documented the required token and pre-publication
rollback boundary in `docs/IOT-WIFI-IMPLEMENTATION-CONTRACT.md`. No driver,
firmware, or router change; atomic ring admission and PID accounting remain
unimplemented and must not be counted as runtime acceptance.

The isolated TxS candidate now provides generation-tagged cancellation for a
proved unsubmitted reservation. The new output is
`..\iot-txs-generation-20261023`; its extracted host fixture compiled under
strict GCC and passed stale/success/duplicate cancellation cases. No caller
connects it to beacon yet; no target build or device acceptance is claimed.
The unified partial bundle was reassembled at
`..\iot-unified-txs-generation-20261023`; its manifest keeps production and
target compilation false.

Next IoT candidate step: the generated `MAC_TX_INFO` now carries the allocated
TxS reservation generation, initialized to zero for no reservation. The
unified partial bundle `..\iot-unified-txs-token-output-20261023` assembled
with pinned `include/mac/mac.h`; its beacon caller remains unbound.

The beacon builder in the corrected isolated bundle
`..\iot-unified-beacon-generation-v2-20261023` now returns that generation;
its legacy RTMP/RLT branch retains the full power-adjustment block before
returning zero. The earlier non-v2 generated folder has an early return and
must not be used. No caller or production firmware was changed.

The corrected isolated bundle `..\iot-unified-beacon-token-v3-20261023` now
passes a typed PID/generation reservation through the beacon submit ABI.
The submit implementations deliberately do not consume it until locked ring
admission, DMA failure propagation and pre-publication cancellation exist.
Two earlier token-output folders failed assembly and lack completed manifests.
No target compile, production installation or router verification occurred.

The isolated candidate `..\iot-unified-beacon-admission-v2-20261023` now
checks beacon ring space under `BcnRingLock`, returns from PCI DMA-map failure
before publishing the descriptor, and attempts generation-matched TxS
cancel on known pre-publication failures. It was assembled only, not target
compiled or installed. Submit remains `VOID`; cancellation failure is logged
but not quarantined, so beacon retirement/runtime acceptance stays open.

The current isolated candidate is
`..\iot-unified-beacon-submit-offload-guard-20261023`: beacon submit now
returns explicit accepted/rejected/cancel-failed status to the caller. The
candidate refuses compilation when PCI and MCU beacon offload are both
enabled, because an MCU publication may precede PCI rejection. The pinned
driver config defaults that offload flag to `n`; effective target flags are
not yet verified. No target compile or device test. Quarantine and late-TxS
handling remain open; earlier bundles are historical checkpoints.

The existing IoT capacity inspector now records effective
`BCN_OFFLOAD_SUPPORT` and `RTMP_PCI_SUPPORT` from its MT7603 `rtmp_chip.o`
Kbuild preprocessing in the archived CI report. The pinned source and current
workflow contain no explicit `HAS_BCN_EVENT_UPDATE_SUPPORT=y`. This does not
yet prove the flags for `cmm_mac_pci.o`; no new CI build or router check ran.

The inspector additionally probes the actual `cmm_mac_pci.o` Kbuild command
and records its separate macro result or a specific unavailable reason. The
local self-test did not reach assertions: Windows denied fixture-directory
creation in both default and workspace-local `%TEMP%`. In-memory Python syntax
parse and `git diff --check` passed. No new target build/device check ran.

The targeted `check-capacity-selftest.py` then passed under approved elevated
local execution (exit 0). Its printed compiler-timeout `UNAVAILABLE` is an
intentional injected case. This is host/synthetic evidence only; the real
MT7603 Kbuild beacon-submit probe awaits a firmware build artifact.
The follow-up case with both `BCN_OFFLOAD_SUPPORT` and `RTMP_PCI_SUPPORT`
also passed in the same targeted self-test; it verifies report detection,
not safe MCU/PCI coexistence.

Source audit: the pinned `BcnTxSHandler` uses `Priv` as an unchecked BSS index
and sets its beacon state idle. The isolated bundle
`..\iot-unified-beacon-txs-bound-v2-20261023` now rejects indices outside
current `BssidNum` or `MAX_MBSSID_NUM` before array access. Manifest and
generated source were inspected; `git diff --check` passed. Late report/PID
reuse, BSS lifetime, callback quiescence and failed-cancel quarantine remain
unproved. No target compile, production install or router action.

The newer isolated bundle `..\iot-unified-beacon-dma-bound-20261023` also
bounds the DMA completion BSS index decoded from `own_mac`; unknown values
no longer default to BSS 0, and the ring cell is still reclaimed. Generated
source and manifest were inspected, `git diff --check` passed. Source audit
shows three unsynchronized beacon-state writers: DMA under `BcnRingLock`,
Type 1 TxS callback after releasing its type lock, and `wdev_bcn_buf_deinit`
without that same lock. Report PID has no driver generation. A shared
state/lifetime owner and completion/reuse rule are needed before binding.
This candidate is not compiled or installed; router untouched.

Further source audit: `RTMPFreeAdapter` frees `BcnRingLock` before main
`wdev_bcn_buf_deinit`; secondary deinit occurs through `MBSS_Remove`.
Therefore simply taking `BcnRingLock` in deinit would use a freed lock on
main teardown. Establish producer/IRQ quiescence and reorder lock lifetime
before implementing a shared beacon-state lock. See IoT contract. No driver
or router mutation in this audit step.

The isolated candidate `..\iot-unified-beacon-lock-order-20261023` now
places main PCI beacon deinit before `BcnRingLock` free and preserves the
original non-PCI cleanup path. Generated source and manifest were inspected;
the manifest explicitly keeps lock lifetime unproved. Producer quiescence,
partial-init behavior, failed deinit, callback synchronization and stale PID
handling remain open. No target compile, production install or router change.
Normal PCI removal reaches netdev exit before adapter free, and
`RTMPDrvClose` disables Tx/Rx and releases IRQ before `ExitTxSTypeTable`;
that source ordering alone does not prove callback return or IoT-only close.

The new isolated bundle `..\iot-unified-beacon-state-lock-v2-20261023`
stages PCI `BcnRingLock` around beacon TxS callback state/index access and
the deinit `IDLE -> STOP` check, in addition to the existing DMA lock. The
callback rejects `STOP`. Generated code and manifest were inspected; both
state-lock flags true, lifetime/quiescence/target/production flags false.
Successful adapter allocation initializes the lock before publication;
allocation failure frees the adapter directly, while later PCI probe errors
can call `RTMPFreeAdapter`. IoT-only close, stale PID, failed deinit and
callback drain remain open. No target build or router change.

## Latest IoT checkpoint — 2026-10-23

Latest isolated bundle: `..\iot-unified-beacon-lock-forms-20261023`.
It includes the DBG STOP/HALT guard and records mixed SEM/IRQ forms for
`BcnRingLock`; lock semantics are not yet proved. The existing CI capacity
inspector now records effective `MULTI_CORE_SUPPORT` from the actual
`cmm_mac_pci.o` command, with explicit one-unit scope. Targeted capacity
self-test passed (its injected timeout is expected). No compiled target
driver, production installation, image or router runtime proof. Next obtain
effective flags for all relevant lock users and resolve callback/PID/BSS
lifetime before production binding.

## Deferred source consolidation — 2026-10-23

The owner confirmed a separate post-firmware stage to organize the repository
and keep the exact build sources, dependencies and toolchain material locally
instead of requiring external source downloads. The delivery order remains:
WR1200JS acceptance, Mi Mini, then source consolidation/offline build.
Requirements and acceptance criteria are in `docs/PROJECT-DELIVERY-SCOPE.md`.
No sources were moved, fetched or removed in this planning update.

Type 1 TxS registration audit, 2026-10-23: the pinned parser dereferences a
registration entry after unlocking, while removal/exit can free that entry.
Staged a handler-pointer snapshot under the lock in the isolated candidate
`..\iot-unified-txs-handler-snapshot-v2-20261023`. A strict GCC host fixture
poisoned registration at unlock and passed; all 51 generated files and 75
preparer hashes matched the manifest. The late-report/reused-PID negative
witness still fires. Callback quiescence, target build, production binding and
device acceptance remain open. See `docs/IOT-WIFI-IMPLEMENTATION-CONTRACT.md`.

Follow-up source audit: `ExitTxSTypeTable` sets a plain `TxSValid` flag then
frees registration/status locks, while `ParseTxSPacket` checks the flag before
taking those locks. A parser already admitted can race with teardown; the
handler snapshot does not solve callback quiescence. Whole-radio close order
does not prove that RX tasklet and MCU queue callbacks have completed, and
the RX-drain call is commented out. Keep production/target/runtime gates
closed pending an explicit admission-stop and completion rule.

Correction from pinned source: normal whole-radio close calls
`RtmpNetTaskExit`, which kills PCI RX tasklets, and its Andes MCU exit kills
the MCU message tasklet before TxS table exit. This narrows the full-shutdown
question but does not supply an IoT-only barrier: the tasklets are shared
with main and guest BSS. Effective board flags and all producers still need
confirmation. See the corrected contract anchors.

Beacon TxS source audit: the callback resets the addressed BSS beacon state
to idle; normal update and buffer deinit reject a non-idle state. Disabling
IoT beacon TxS is not a safe shortcut. The BSS-indexed recovery flush in
`APCheckBcnQHandler` re-enables beacon start and does not prove RX/MCU TxS
report drain, including on register-poll timeout. Keep selective retirement
closed; exact anchors are in the IoT contract. No driver/firmware/router
change was made in this audit.

TxS identity audit: the hardware report format has PID and 12-bit SN but no
descriptor `own_mac`/BSS field. Beacon submit assigns WCID 0 across BSSs;
its BSS index is saved only in the current software PID slot. Thus report
`wlan_idx` cannot distinguish a late old beacon report from a new BSS after
PID reuse. No expected SN is stored by the inspected submit path, and the
software reservation generation is absent from the report. Keep the late-PID
gate open pending proven SN matching or a real report drain. Source anchors
are in the IoT contract; no router or firmware change.

Selective producer audit: candidate close clears the target beacon request
and disables/readbacks TBTT/queue controls before `MBSS_Close`; candidate
submit rechecks the request under `BcnRingLock` just before kickout. This
stages exclusion of new software submissions after close intent. It does
not drain already-submitted TxS reports. The candidate mixes SEM/BH and IRQ
lock forms on `BcnRingLock`; with `MULTI_CORE_SUPPORT` their interrupt
masking differs. Effective target flags and the complete lock map remain
unproved, so atomicity and production gates stay false. See IoT contract.

## IoT beacon lock compile flags — 2026-10-23

Extended `tools/iot/check-capacity.py` to inventory MT7603 C units with
`BcnRingLock` acquisition and preprocess each against its own recorded Kbuild
`.o.cmd`. The report records effective `MULTI_CORE_SUPPORT` per unit; missing
or ambiguous commands remain `unavailable` with a null value, never false.
The existing `cmm_mac_pci.o` beacon-submit result is retained. The targeted
synthetic capacity self-test passed, including a missing-command case; its
printed timeout is intentionally injected. Python syntax and `git diff --check`
passed. No actual target Kbuild commands were available locally, so lock
semantics, target compilation and runtime remain unverified. Next obtain
real per-unit CI artifacts, then resolve callback/PID/BSS lifetime before
binding this partial driver candidate.

## IoT TxS PID retirement finding — 2026-10-23

Pinned mt76x3 source shows an 8-bit report PID with 256 status slots.
`AddTxSStatus` overwrites an occupied slot after counting a collision;
`RemoveTxSStatus` clears a slot without checking state/identity. The Type 1
report path removes the slot before the beacon callback. This rules out
treating a software-only reservation generation as proof against a late
report after PID reuse. See the exact source locations and acceptance gate
in `docs/IOT-WIFI-IMPLEMENTATION-CONTRACT.md`. No driver, image or router
change occurred; source evidence only. Next establish a real report drain
or identity rule before candidate production integration.

The isolated candidate already stages occupied-PID overwrite prevention and
slot validation; its manifest still marks PID reuse safety false. This
source audit does not invalidate those staged guards, but they cannot
distinguish a late report after a freed slot is reused.

Further source trace: TxS reports enter through the RX packet path in
`common/cmm_data.c`, while whole-radio `RTMPDrvClose` has the explicit
RX-drain call commented out before TxS table exit. Beacon TX-ring drain
alone would not retire old PIDs, and whole-radio teardown is not a selective
IoT BSS close. Evidence and the pending selective RX-report/callback barrier
are recorded in the IoT contract. No runtime drain claim was made.

The hardware TxS report also exposes a 12-bit sequence number, currently
recorded only under `DBG`; the beacon descriptor path does not currently
retain an expected SN for identity matching. Its wrap and hardware behavior
remain unverified. This is a possible investigation path, not acceptance.

The MT7603 beacon TMAC path was traced further: descriptor memory is zeroed,
and the inspected submit path does not set `txd_3->sn`/`sn_vld` or save an
expected SN with the PID. `TxSPriv` carries the BSS index only. Therefore the
current source cannot match the report's SN to a reservation. See the IoT
contract for exact anchors; hardware SN assignment still needs target proof.

Selective close trace: pinned `MBSS_Close` clears only that BSS beacon
request and rebuilds all beacons; it has no pending TxS retirement.
`APStopBssOnly` has no pinned caller and disables shared interrupts/TBTT,
so it cannot safely substitute for an IoT-only close. IoT needs a BSS-scoped
barrier on the actual MBSS path while preserving main/guest operation.

Assembled a fresh isolated candidate at
`..\iot-unified-beacon-selective-gates-20261023` from pinned revision
`c25283e915a2a00a763774dd255b14aff997285e`. Its manifest explicitly
keeps SN matching, selective BSS TxS retirement, PID-reuse safety, target
compilation and production installation false. Independently checked hashes
of all 51 generated candidate files; `git diff --check` passed. This bundle
supersedes the earlier lock-forms bundle as the latest candidate but does
not add a functioning selective-close backend or justify device flashing.

The next isolated bundle is `..\iot-unified-beacon-cr-readback-20261023`.
It stages post-write verification of the target secondary BSS TBTT and
beacon-queue control bits in `mbss_cr_disable`, returning a failure if
either remains enabled. Compared with the prior 51-file bundle, only
generated `ap/ap_mbss.c` changed; all 51 manifest hashes matched. The
checked-close candidate can retain the uncertain ticket on this failure,
but it is not bound to production `ndo_stop`. No target compile or router
runtime proof, and pending TxS reports still lack a retirement barrier.

The current rebuilt bundle is `..\iot-unified-beacon-cr-readback-v2-20261023`.
Its CR generator now casts `BssidNum` before comparing it with the array
capacity; the prior expression failed a strict host compile for signedness.
`tools/iot/prepare-mbss-cr-readback-check.py` extracted the actual generated
`mbss_cr_disable` into an injected-register fixture. It compiled with
`gcc -std=c11 -Wall -Wextra -Werror` and passed success, sticky TBTT,
sticky queue, neighbor-preservation and invalid-index cases. All 51 bundle
file hashes match the manifest; `git diff --check` passed. This is a host
fixture only: target compile, RF silence, selective TxS retirement, mandatory
close binding and router runtime remain unproved.

Checked the pinned firmware flush primitive before choosing a TxS-retirement
approach. `CmdFlushFrameByWlanIdx` sends `EXT_CMD_FLUSH_FRAME_WCID` without
waiting for a response; its sole in-tree caller uses a removed station WCID,
not an IoT beacon BSS. It provides no source-backed evidence that pending RX
TxS reports or callbacks have finished. Do not use it as the IoT close
barrier. The next implementation step remains a BSS-scoped pending-report
ledger and callback quiescence design, with PID reuse and bounded failure
handling proved before production binding. No device action occurred.

Staged a per-BSS beacon TxS callback ledger in a new isolated candidate:
`..\iot-unified-beacon-txs-ledger-v5-20261023`. It increments in-flight
ownership before a PID slot is released, decrements after Type 1 handler
completion or rejection, and keeps an accounting mismatch as a fail-closed
fault. A query scans both occupied beacon slots and in-flight callbacks.
The extracted source/host parser fixture passed under GCC strict warnings;
51 manifest hashes matched, with only TxS C/header files changed from the
prior bundle. This does not prove delayed-report safety after PID reuse,
bind a close wait, compile the MIPS target, or validate router runtime.
See the IoT contract for the exact boundary. No router state changed.

Next isolated bundle: `..\iot-unified-beacon-txs-close-gate-v2-20261023`.
The candidate checked BSS close now queries pending beacon TxS slots and
in-flight callbacks after CR-disable and `MBSS_Close`. A pending result
retains stage 2 for retry; a query error marks the close uncertain before
HNAT deregistration or virtual reference consumption. The extracted MBSS
host fixture passed pending/retry and accounting-fault cases, and the TxS
parser fixture passed; GCC used `-std=c11 -Wall -Wextra -Werror`. All 51
manifest hashes match. This is only a snapshot gate, not a proved report
drain: PID reuse, producer exclusion, bounded wait, target compilation,
production binding and router runtime remain open. No device changes.

Latest isolated candidate: `..\iot-unified-txs-claimed-slot-v2-20261023`.
The TxS parser now keeps each accepted PID `TXS_CLAIMED` until its handler
path exits; allocation only accepts `TXS_UNUSED`. This closes the specific
reuse window during a running callback while preserving the per-BSS
outstanding snapshot. Extracted strict-GCC host fixtures passed beacon and
Type 0 exits, missing/mismatched handlers, same-PID allocation during
callback, slot exhaustion and BSS-close pending/retry. All 51 candidate
hashes and preparer hashes matched. Late or duplicate hardware reports
after a later PID reuse remain unresolved; no MIPS target build, production
installation or router change occurred.

Late-report negative witness, 2026-10-23: the extracted host fixture now
reuses a completed PID for BSS 3 and injects an old duplicate report before
the new one. It observed the old report invoke BSS 3's handler and consume
its outstanding slot; the new report is then unmatched. Strict GCC compile
and run passed as an expected unsafe-order witness, not a safety proof.
`tools/iot/prepare-beacon-txs-ledger-check.py` changed; the old bundle's
preparer-input hashes refer to its earlier tool snapshot. Next prove a real
hardware identity/drain rule or keep selective IoT retirement closed. Source
and limitation are in the IoT contract; no device/production change.

TxS receive-path audit, 2026-10-23: pinned PCI ring-0 receive calls the TxS
parser, and the source also calls that parser from an Andes MCU message queue.
Effective WR1200JS compilation/routing of the MCU path is not yet proved.
Normal RX has reset/radio/startup exits and a batch limit; HIF_MT `StopDmaRx`
returns without draining. Therefore a ring-idle sample or that helper cannot
justify IoT BSS/PID retirement. Exact source lines and next gate are in the
IoT contract. No production build or router change.

Added `txs_receive_units_probe` to the existing capacity inspector for four
exact RX/MCU source units. It reads each recorded target Kbuild command and
reports MT_MAC, PCI and Andes macros; absent commands stay unavailable/null.
Synthetic self-test passed including missing Andes command (the injected
compiler timeout line is expected). #535 config plus pinned config.mk suggest
Andes support, but #535 downloaded artifacts lack the needed `.o.cmd` files,
so effective per-unit flags and actual MCU TxS routing remain unverified.
Future CI evidence is required; no full build, production or router change.

TIM queue-producer audit, 2026-10-23: pinned AP driver builds `ap_nps.o`;
its `RT28xx_UpdateTimToAsic` can submit `Q_IDX_BCN` using a separate
`tim_buf.bTimSntReq` flag. The staged IoT CR-disable clears only the normal
beacon request, so its producer-exclusion claim is limited to that path.
The only source call to `APMakeAllTimFrame` is inside
`RTMPHandlePreTTTTInterrupt`, for which full-tree search found no caller;
`TimEnable` is a registered development-only private command. Runtime TIM
dispatch is unproved. The pinned PCI `WF_MAC_INT_4` branch only reads and
masks `HWISR4`/`HWIER4`; it never calls/schedules the PRETTTT handler.
Therefore no live software call chain was found in this source snapshot.
Next establish effective target dispatch and, if
active, BSS-scoped admission/DMA accounting before close. No production or
device changes; see IoT contract.

Beacon-lock inventory, 2026-10-23: pinned full tree has seven active
`BcnRingLock` sites across `ap_nps`, `ap_cfg`, `cmm_mac_pci` and
`cmm_data_pci`: five SEM/BH and two IRQ-form owners. The original driver
already mixes forms; candidate-only edits cannot establish atomicity.
Allocation/free and commented aliases were also checked. Exact anchors and
the required all-owner lock/context gate are in the IoT contract. No driver
installation, target build or router action.

Next concrete IoT step: extend `tools/iot/check-capacity.py` so its report
enumerates each live BcnRingLock owner with function/context and actual
per-object Kbuild macro status, including files omitted from candidate
bundles. Add an in-memory self-test for the seven pinned owners and absent
`.o.cmd` entries. Then use full exact build artifacts when available to
decide whether one IRQ-save wrapper is required across all compiled owners;
do not alter locking based on guessed target macros or incomplete context.

## Звіт за шістьма етапами IoT — 2026-10-23

Після завершення кожного етапу оновлювати цей список доказом і окремо
повідомляти власнику: «Етап N виконано: ...». Часткову роботу позначати
частковою; CI не замінює перевірки на пристрої.

1. **Блокування beacon-черги — в роботі.** Інвентар семи місць готовий;
   фактичні прапорці компіляції та контексти виклику ще треба підтвердити.
2. **Безпечне закриття IoT BSS — не завершено.** Потрібні узгоджене
   блокування, зупинка подавання кадрів і доказ завершення DMA/TxS без
   помилкового повторного використання PID.
3. **Життєвий цикл адаптера й BSS — не завершено.** Узгодити відкриття,
   закриття, скидання, помилки й відкат.
4. **Мережевий шлях IoT — не завершено.** Міст, підмережа, DHCP/DNS,
   firewall, ізоляція й інтернет.
5. **WebUI та образ — не завершено.** Налаштування, збереження, компіляція
   драйвера й перевірка готового образу.
6. **Приймання на роутері — не розпочато.** Одночасна робота мереж,
   адресація, ізоляція та відновлення; зміни пристрою потребують окремого
   дозволу власника.

Проміжний результат етапу 1: інспектор `check-capacity.py` тепер додає до
кожного знайденого власника `BcnRingLock` рядок і форму SEM/IRQ навіть тоді,
коли його `.o.cmd` відсутній; макроси в такому разі лишаються невідомими.
Перевірено синтаксис Python і `git diff --check`. Функції/контексти виклику,
повнота інвентарю та прапорці цільової збірки ще не перевірені.

Наступний проміжний крок пункту 1: інспектор також записує назву найближчої
попередньої розпізнаної функції або `null`, якщо її не вдалося встановити.
Перевірка в пам’яті підтвердила, що власник із відсутнім `.o.cmd` лишається
у звіті з рядком, формою й функцією, а макрос лишається невідомим. Перша
спроба файлового fixture натрапила на заборону запису в Windows Temp;
жодного файла fixture не створено. Контекст переривання та повнота для
семи реальних власників ще потребують окремої перевірки.

Перевірка семи реальних місць пункту 1: інспектор запущено лише на читання
проти збереженого дерева драйвера `source-exact`. Він повернув `ap_cfg.c:14608`
(`Set_BcnStateCtrl_Proc`, SEM), `ap_nps.c:77` (`RT28xx_UpdateTimToAsic`, SEM),
`cmm_data_pci.c:2681` (`RTMPHandleBcnDmaDoneInterrupt`, SEM), а також
`cmm_mac_pci.c:1490` (`RTMPFreeTxRxRingMemory`, SEM), `:1890`
(`RTMPRingCleanUp`, IRQ), `:2069` (`PDMAResetAndRecovery`, IRQ), `:2710`
(`RT28xx_UpdateBeaconToAsic`, SEM). Це збігається з ручним інвентарем.
Фактичні `.o.cmd` для WR1200JS у цій перевірці не надані; її результат
не доводить ефективні макроси чи контексти виконання.

Виклики власників замка, 2026-10-23: завершення beacon DMA викликається з
`bcn_dma_done_task` (`os/linux/rt_rbus_pci_drv.c:575`), тобто з відкладеного
обробника; подання маяка йде через `APUpdateBeaconFrame`
(`ap/ap_connect.c:1724`). `PDMAResetAndRecovery` має щонайменше шлях через
debug-процедуру (`common/cmm_cfg.c:1728`) і watchdog
(`common/cmm_mac_pci.c:2151`), після чого викликає `RTMPRingCleanUp`.
Це конкретні вихідні шляхи, але вони ще не доводять усі можливі контексти
кожної функції або ефективну конфігурацію WR1200JS. Пункт 1 відкритий.

Перевірка інвентарю, 2026-10-23: `check-capacity-selftest.py` доповнено
окремим fixture у пам'яті для семи відомих власників `BcnRingLock` у чотирьох
файлах. Він перевіряє функцію, форму SEM/IRQ і ненульовий номер рядка кожного
місця, а також те, що за відсутності `.o.cmd` усі власники залишаються у
звіті з невідомим `MULTI_CORE_SUPPORT`. Цільова перевірка пройшла; `py_compile`
і `git diff --check` пройшли. Повний файловий self-test у цьому Codex executor
не стартував через Windows `PermissionError` під час створення тимчасової
теки навіть у робочій копії; це не збій перевірюваної логіки і не доказ
успіху всього набору. Фактичні `.o.cmd` та повні контексти WR1200JS лишаються
відкритими, тому етап 1 ще не завершено.

Уточнення фактичного обсягу, 2026-10-23: сім позицій — це входження у
вихідному тексті, а не сім доведено скомпільованих шляхів. Таблиця приватних
команд `ap/ap_cfg.c:1295` реєструє `Set_BcnStateCtrl_Proc` тільки під `DBG`.
`RTMPFreeTxRxRingMemory` у `common/rtmp_init_inf.c:966` викликається лише
без `RESOURCE_PRE_ALLOC`; інші виклики є в `common/rtmp_init.c:415,2465`.
`RT28xx_UpdateTimToAsic` викликається з `ap_nps.c:243` через
`APMakeAllTimFrame`; знайдений виклик останньої —
`common/cmm_data_pci.c:1521` у `RTMPHandlePreTTTTInterrupt`, але фактичне
підключення цього переривання для WR1200JS ще не підтверджене. Інспектор
тепер явно позначає, що його позиції походять із вихідного тексту, а
прапорці `.o.cmd` самі по собі не доводять активність кожної позиції.

Продовження етапу 1: інспектор з фактичної команди Kbuild кожного файла
додатково викликає GCC `-E -fdirectives-only`. Маркери GCC визначають цільовий
файл, а унікальна пара назви функції та форми замка визначає
`active_after_directives` для кожного знайденого виклику `BcnRingLock`.
За відсутності `.o.cmd`, помилки препроцесора або маркера цільового файла
статус лишається `null`/`unavailable`, а не хибним `false`. Перевірки в пам'яті
підтвердили всі сім входжень, відповідність активних власників вихідному файлу
та відмову за відсутності його маркера. `py_compile` і `git diff --check`
пройшли. Це готує доказ для майбутньої точної збірки, але #535 не містить
нового звіту; активні місця на цільовій прошивці поки невідомі.

Після дозволеного запуску поза обмеженням тимчасових тек повний
`python tools/iot/check-capacity-selftest.py` пройшов. Синтетична команда
Kbuild перевірила обидві гілки `DBG`: за `-DDBG` місце `ap_cfg.c`
залишається активним, без нього — неактивним; окреме місце без `.o.cmd`
лишається у звіті зі статусом `null`. Перевірка використовувала host GCC,
не цільовий MIPS-компілятор, і не доводить стан #535 або роутера. Раніша
помилка Windows Temp стосувалася запуску в sandbox; тут вона не повторилась.

Цільовий тест `RESOURCE_PRE_ALLOC` знайшов похибку попереднього алгоритму:
GCC може додати порожні рядки після `#endif`, тому підрахунок рядків його
виводу дав зсув. Інспектор змінено на зіставлення унікальних пар
«функція + SEM/IRQ» всередині маркера цільового файла. За дубліката пари
він відмовляється робити висновок. Повний self-test пройшов із host GCC:
він перевірив активний/неактивний `DBG`, активний/неактивний
`RESOURCE_PRE_ALLOC` і відсутній `.o.cmd`. Це не підтверджує ефективну
конфігурацію #535, але усуває помилкове `false` у майбутньому звіті.

Збережені артефакти #535 містять `kernel-effective.config`, де
`CONFIG_MT7603E_WIFI_WORK_QUEUE` вимкнено (`:1665`), але не містять жодного
MT7603 `.o.cmd`, модуля `.ko` чи нового `beacon_lock_units_probe`. У
збереженому `config.mk:340` `RESOURCE_PRE_ALLOC` додається до `WFLAGS`, а
`MULTI_CORE_SUPPORT` додається лише в окремій платформній гілці
(`:1865-1869`). Ці дані підказують можливі гілки, проте не замінюють
команду фактичної компіляції кожного файла. Етап 1 залишається відкритим.

Додатковий source-context аудит етапу 1: `RT28xx_UpdateBeaconToAsic` має
щонайменше два класи викликів. `RTMPHandlePreTBTTInterrupt` викликає
`APUpdateAllBeaconFrame` (`common/cmm_data_pci.c:1484-1491`), який веде до
`APUpdateBeaconFrame` і замка; для MT MAC він викликається з
`mt_mac_int_3_tasklet` (`os/linux/rt_rbus_pci_drv.c:1050,1081`). Та сама
`APUpdateBeaconFrame` викликається з численних налаштувальних обробників
`ap/ap_cfg.c`, тож один замок обслуговує і відкладений обробник, і шлях
налаштувань. `RTMPHandleBcnDmaDoneInterrupt` викликається з
`bcn_dma_done_tasklet` (`rt_rbus_pci_drv.c:575`). Ці функції мають
`WORKQUEUE_BH` альтернативу, ефективний вибір для WR1200JS ще не доведений.
`RTMPHandleRxCoherentInterrupt` містить виклики `RTMPRingCleanUp`, але для
MT7603 має ранній `return` перед ними (`common/cmm_data_pci.c:1535-1551`),
тож цей шлях не є доказом очищення кільця WR1200JS. Залишаються шляхи
відновлення. Не вибирати остаточну форму замка, спираючись лише на назву
однієї функції.

Уточнення recovery-шляхів: `PDMAWatchDog` (`cmm_mac_pci.c:2119-2151`)
викликає `PDMAResetAndRecovery` лише без `DMA_RESET_SUPPORT`; з цим прапорцем
ставить `pse_reset_flag`. Натомість `PSEResetAndRecovery`
(`cmm_mac_pci.c:2222-2432`) також викликає `PDMAResetAndRecovery`.
`PciMlmeRadioOn` містить `RTMPRingCleanUp`, але для `HIF_MT` повертається
через `MTPciMlmeRadioOn` перед цими викликами (`cmm_mac_pci.c:3021-3057`).
Отже source-карта вже виключає два хибні докази активного ring cleanup для
MT7603; ефективні `DMA_RESET_SUPPORT`/`HIF_MT` треба звірити в цільовому
звіті й готовому модулі.

Передача інспектора до CI, 2026-10-23: GitHub PR #2 вказує на
`675be3ebc90d34b6b32c23cc8f4471b5cdfac782`; успішний firmware run
#537 (`39838016889`) для цього HEAD має IoT radio-capacity артефакт, але він
ще старого формату і не містить `beacon_lock_units_probe`. Артефакт
завантажено локально до `artifacts-537/wr1200js-iot-radio-capacity/`.
Перевірений інспектор і self-test закомічено окремо як `0852a2e`
(`build(iot): report effective beacon lock owners from Kbuild`). Інші
незакомічені файли не стаджилися. Коміт **не відправлено**: `ssh -T` у
Codex executor повертає блокувальне `off\r\nexit /b 1\r\n`; за
правилами проєкту обхід SSH або заміна remote не виконувалися. Наступна
цільова збірка має взяти `0852a2e` після дозволеного відправлення гілки;
до того фактичні цільові власники замка залишаються непідтвердженими.

Карта часткового кандидата, 2026-10-23: перевірено саме
`..\iot-unified-txs-handler-snapshot-v2-20261023/driver`, а не всі проміжні
`stages/`. Знайдено 19 вихідних місць `BcnRingLock` у восьми файлах:
10 SEM і 9 IRQ; незмінений `ap_nps.c` у цьому частковому дереві відсутній.
Маніфест кандидата підтверджує `complete_driver_tree=false`,
`target_compiled=false`, `production_installed=false`. Повний машинний список
з SHA256 маніфесту —
`docs/evidence/WR1200JS-IOT-CANDIDATE-BEACON-LOCK-INVENTORY-2026-10-23.json`.
Початковий інспектор помилково підписав `INT32` власників у `txs.c:98` і
`cmm_mac_pci.c:2726`; розпізнавання `INT32` виправлено. Два SEM-місця у
`mbss_cr_disable` мають однакову пару функція/форма: коли директиви зберігають
лише одне, інспектор тепер ставить обом `null`, а не вгадує рядок. Повний
self-test host GCC, `py_compile` і `git diff --check` пройшли. Кандидат усе
ще не є повним драйвером або готовим образом; етап 1 відкритий.
Інспектор та машинний список кандидата зафіксовані окремим локальним
комітом `0f567ed`; разом із `0852a2e` вони ще не відправлені до PR #2.

Оновлення CI етапу 1, 2026-10-23: системний OpenSSH у поточному Codex
executor автентифікувався на GitHub. `0852a2e` і `0f567ed` відправлено
звичайним fast-forward push; віддалений ref підтверджено на `0f567ed`.
ABI run `40010694921` впав у self-test: кандидатний заголовок
`tools/iot/mt7603-main-observe.h` був невідстежуваним локально і відсутнім
у CI checkout (`Observer header absent`). Локальний повний self-test пройшов.
Окремий коміт `9727933` додав лише цей заголовок і відправлений fast-forward.
Для нього стартували ABI run `40010959283` та прошивкова збірка #539
(`40010959461`); їхні кінцеві результати й цільовий артефакт ще не перевірено.
Заголовок є лише кандидатом проби: виробничий драйвер, образ і роутер цим
виправленням не змінено. Етап 1 відкритий до підтвердження фактичних
прапорців/контекстів та узгодження блокування.

Межа доказу #539: у відправленому workflow є наявна перевірка
`beacon_lock_units_probe` за фактичними Kbuild-командами. Додавання
`--check-main-observer` та окремого `check-task-config.py` для TU
`rt_linux` залишаються незакоміченими, тому #539 не підтвердить їх.
Новий ABI `40010959283` уже пройшов попередній проблемний self-test і на
останній перевірці виконував host-kernel isolation; #539 ще очікував запуску.

ABI `40010959283` завершився **успішно** для `9727933`. Це усуває попередній
збій fixture через відсутній кандидатний заголовок у Git checkout, але не
доводить цільові макроси MT7603 чи поведінку фізичного роутера. На останній
перевірці #538 ще компілювала старіший `0f567ed`, а #539 очікувала запуску.
Повторний workflow не запускати; наступний доказ — артефакт саме #539.

Уточнення черги та доказу: #538 (`0f567ed`) вже містить інспектор
`beacon_lock_units_probe` і не вмикає ще локальний прапорець
`--check-main-observer`; тому її готовий артефакт може дати цільові
Kbuild-прапорці раніше за #539. Перевіряти перший готовий придатний
артефакт #538 або #539, не створюючи повторних запусків. #538 виконує
крок компіляції прошивки на GitHub-hosted runner; #539 чекає в групі
`firmware-${{ github.ref }}` через `cancel-in-progress: false`.

Збірка #539 (`40010959461`, `9727933`) завершилася успішно. Її
`wr1200js-iot-radio-capacity/mt76x3.json` підтвердив джерельний ліміт
16 BSS, але всі чотири цільові одиниці `BcnRingLock` лишилися
`unavailable`: вивід GCC `-fdirectives-only` містив байт `0xa1`, який
суворе UTF-8 декодування Python відхилило. Отже фактичні
`MULTI_CORE_SUPPORT` і `active_after_directives` ще невідомі. Доказ і
SHA256 артефакту: `docs/evidence/WR1200JS-BUILD539-IOT-LOCK-PROBE.md`.
Виправлено лише декодування directive output через UTF-8
`surrogateescape`; додано вузький випадок із реальним subprocess та
невалідним байтом. Повний capacity self-test, перевірка синтаксису і
`git diff --check` пройшли. Коміт `160a1bc` відправлено fast-forward;
наступний цільовий артефакт має підтвердити per-unit прапорці. Етап 1
залишається відкритим; виробничий драйвер і роутер не змінювалися.

Артефакт збірки #540 вже доступний: `beacon_lock_units_probe` для чотирьох
базових одиниць завершився з `all_unit_flags_available=true` і
`all_site_activity_available=true`. Ефективний `MULTI_CORE_SUPPORT=false`
у кожній; шість із семи вихідних місць `BcnRingLock` збереглися після
директив, `RTMPFreeTxRxRingMemory` — ні. Перелік і SHA256 наведено в
`docs/evidence/WR1200JS-BUILD540-IOT-BEACON-LOCK-UNITS.md`. Це знімає
невідомість для базового дерева, але не підтверджує всі 19 місць часткового
IoT-кандидата, контексти IRQ або безпечну виробничу активацію. Загальний
workflow #540 ще виконував наступні перевірки на момент читання артефакту.

ABI `40016197273` для `160a1bc` завершився успішно, включно з
регресійним self-test. Прошивкова #540 (`40016197462`) на останній перевірці
ще встановлювала залежності; артефакту з виправленими per-unit прапорцями
поки немає. Це успіх CI перевірки скрипта, не доказ безпеки замка на MT7603.

Фінальний стан #540 (`40016197462`) перевірено повторно: jobs `select`,
`build (wr1200js) / build-wr1200js`, `downloads` і
`firmware-zip (wr1200js)` завершилися успішно. Маніфест часткового
кандидата `../iot-unified-txs-handler-snapshot-v2-20261023/manifest.json`
досі зазначає `complete_driver_tree=false`, `target_compiled=false` і
`beacon_lock_forms_complete_tree=false`; він не включає базовий
`ap/ap_nps.c`. Наступна робота етапу 1: скласти повне закріплене дерево з
накладеними кандидатними файлами, перевірити всі скомпільовані власники
`BcnRingLock` за цільовими Kbuild-прапорцями й контексти виклику.
Базовий образ #540 не є IoT-кандидатом. Роутер не змінено.

Повне джерельне дерево для наступної перевірки складено окремо від
репозиторію: архів точної ревізії `vipshmily/padavan-4.4@c25283e` дає
515 файлів MT7603; усі 31 оригінальний Git blob з маніфесту IoT-кандидата
збіглися. Поверх копії накладено 45 драйверних файлів кандидата, разом
529 файлів. Повна карта `BcnRingLock` тепер містить 20 місць у 9 файлах
(11 SEM, 9 IRQ), зокрема незмінений `ap/ap_nps.c`, якого не було в
частковому дереві. Машинний звіт із SHA256 архіву й маніфесту:
`docs/evidence/WR1200JS-IOT-FULL-CANDIDATE-BEACON-LOCK-INVENTORY-2026-10-23.json`.
Це лише джерельний облік: цільові Kbuild-команди, активність директив,
контексти IRQ, компіляція кандидата й runtime поки не перевірені.

Перша перевірка контексту одного власника замка: у повному кандидатному
дереві апаратний обробник `MT_INT_BCN_DLY` лише ставить у чергу
`bcn_dma_done_task`; виклик `RTMPHandleBcnDmaDoneInterrupt` із SEM-формою
`BcnRingLock` відбувається у відкладеному tasklet/work callback, не прямо
в hard IRQ. Доказ і точні місця коду —
`docs/evidence/WR1200JS-IOT-BEACON-DMA-CONTEXT-2026-10-23.md`. Це
джерельна звірка одного шляху; інші власники, цільові макроси кандидата,
вкладені захоплення й час життя замка ще потребують перевірки.

Повний джерельний облік став відтворюваним: додано
`tools/iot/audit-full-beacon-locks.py`, який віртуально накладає частковий
кандидат на закріплене дерево, перевіряє всі вихідні Git blob з маніфесту
і записує перелік місць замка. Локальний повтор отримав 31/31 blob,
20 місць у 9 файлах (11 SEM, 9 IRQ), як і попередній звіт; зіпсований
оригінальний blob відхиляється. У незакоміченому ABI workflow додано виклик
після генерації кандидата; його JSON потрапить до `abi-results/`.
Локально пройшли перевірка синтаксису Python і `git diff --check`.
Цільової компіляції кандидата ще не виконано; CI для нового кроку не запущено.

Оновлення доставки: вузький коміт `51c0776` містить тільки
`tools/iot/audit-full-beacon-locks.py` і п'ять рядків виклику в ABI workflow;
його відправлено звичайним fast-forward push до
`codex/wr1200js-service-webui`. Інші незбережені зміни лишилися в робочій
копії. Для цього HEAD стартували ABI run `40020039665` і прошивкова
збірка #541 (`40020039819`); на першому читанні обидва були `queued`.
Нове підтвердження CI треба взяти з ABI артефакту
`abi-results/iot-full-beacon-locks.json`. Базовий firmware workflow не
встановлює IoT-кандидат у виробничий образ; жодного runtime-висновку немає.

Незалежна перевірка TxS шляху кандидата виявила конкретний вкладений порядок:
`GetPacketFromRxRing` бере `RxRingLock`, а всередині викликає
`parse_rx_packet_type` → `ParseTxSPacket` → `BcnTxSHandler`, який бере
`BcnRingLock`. `ParseTxSPacket` перед Type 1 handler відпускає власний
TxS registry lock, але RX ring lock залишається утриманим. Деталі та межі
доказу доповнено в
`docs/evidence/WR1200JS-IOT-BEACON-DMA-CONTEXT-2026-10-23.md`.

Наступний обов'язковий крок: перевірити, чи існує зворотний порядок
`BcnRingLock` → `RxRingLock`, і які гілки переживають цільову препроцесорну
збірку. Факту deadlock або безпеки всього драйвера поки не встановлено.

ABI run `40020039665` завершився успішно, але завантажений артефакт
`iot-full-beacon-locks.json` охоплює лише 10 overlay-файлів, 6 перевірених
blob і 7 місць замка в 4 файлах (5 SEM, 2 IRQ). Локальний повний кандидат
має 45 overlay-файлів, 31 blob і 20 місць у 9 файлах. Зелений CI
підтверджує виконання аудиту лише для вужчого зафіксованого генератора;
повний локальний кандидат CI ще не перевірив. Артефакт збережено поза
репозиторієм у `../iot-abi-541-artifact/`.

Перевірка зворотного порядку у двох конкретних шляхах показала, що
`RTMPRingCleanUp` обробляє QID_RX і QID_BCN окремо, а кандидат PDMA reset
відпускає `BcnRingLock` перед очищенням QID_RX. Це не повний доказ
відсутності інверсії через інші виклики. Деталі в
`docs/evidence/WR1200JS-IOT-BEACON-DMA-CONTEXT-2026-10-23.md`.

Наступний крок — довести повний 45-файловий кандидат до відтворюваного CI
та отримати цільові Kbuild-команди всіх дев'яти одиниць замка.

Підтверджено різницю CI та локального кандидата: поточний генератор
`tools/iot/prepare-radio-queue-candidate.py` має 691 доданий і 9 видалених
рядків відносно HEAD, а з 75 вхідних файлів маніфесту 29 ще не відстежуються
Git і чотири відстежувані змінені локально. Генератору додано самоперевірку
власного SHA-256 у `preparer_inputs`. Нова локальна збірка кандидата у
`../iot-full-dependency-closure-20261023/` завершилася; повторний аудит
підтвердив 31 blob, 45 driver-overlay файлів і 20 місць замка у 9 файлах.
Це ще не CI/цільова компіляція. Наступний коміт для повного CI повинен
охопити весь узгоджений набір залежностей, а не лише audit script.

Ізольований closure-доказ: `git archive HEAD tools/iot` плюс рівно 34
залежні локальні файли відтворив кандидат із байтово тотожним маніфестом
і всіма 51 вихідними файлами. Незалежний аудит знову знайшов 20 місць у 9
одиницях. Ці 34 файли зафіксовано локальним комітом `b44ab21`
(`build(iot): publish full experimental radio candidate inputs`). Коміт ще
не відправлений на GitHub, поки #541 виконується. Інші незбережені зміни
збережено. Кандидат експериментальний, не встановлений у прошивку.

Додано fail-closed gate для ABI-аудиту: локальний коміт `569bccb`
вимагає точну перевірену форму повного кандидата (515 вихідних файлів,
45 driver-overlay файлів, 31 blob, 9 lock units, 20 lock sites,
11 SEM і 9 IRQ). Перевірено позитивний випадок на ізольованому повному
кандидаті й негативний — на завантаженому вужчому артефакті #541:
вужчий випадок завершується кодом 2 і не створює доказовий JSON.
Коміти `b44ab21` і `569bccb` локальні, без push, поки #541 виконується.

Уточнення обліку кандидата: 45 overlay-шляхів у дереві драйвера — це
41 запис маніфесту з `purpose=driver` і 4 допоміжні `include`-фрагменти з
`purpose=fixture`; ще 6 fixtures лежать поза цими каталогами. Локальний
коміт `ab19045` додає SHA-256 звірку всіх 51 файлів кандидата до аудиту.
Незмінений ізольований кандидат пройшов; копія зі зміненим `include/rtmp.h`
відхилена без створення JSON. Коміт локальний, не відправлений.

Оновлення CI та публікації: #541 (`40020039819`) завершилася `success` на
попередньому SHA `51c0776`; це перевірка образу без встановленого IoT
кандидата. Після завершення #541 одним штатним fast-forward push відправлено
локальні коміти `b44ab21`, `569bccb`, `ab19045` до PR #2; віддалений HEAD
тепер `ab19045`. Для нього стартували ABI run `40021678711` і прошивкова
збірка #542 (`40021678720`). Наступний доказ — завантажити новий ABI JSON і
перевірити 45 overlay-шляхів, 31 source blobs, 20 lock sites, а також усі
подальші кроки ABI. Зелений CI не означатиме роботу IoT на роутері.

З артефакту успішної #541 завантажено `wr1200js-iot-radio-capacity/mt76x3.json`
до `../iot-capacity-541/`. Базовий образ має записані Kbuild-команди для
чотирьох beacon-lock одиниць; директивна препроцесорна перевірка завершилася,
`MULTI_CORE_SUPPORT=false` в усіх чотирьох. Обидва приймальні шляхи TxS,
включно з `cmm_data_pci.c` та `andes_core.c`, мають ефективні MT_MAC/PCI/Andes
ознаки у чотирьох перевірених одиницях. Це лише базовий образ #541, без
IoT-кандидата; дев'ять одиниць кандидата цим не доведено. Деталі в
`docs/evidence/WR1200JS-IOT-BEACON-DMA-CONTEXT-2026-10-23.md`.

ABI run `40021678711` для HEAD `ab19045` завершився `success`. Завантажений
`band-steering-mips-abi` артефакт у `../iot-abi-542-artifact/` містить
`iot-full-beacon-locks.json`: 515 файлів закріпленого джерела, 45 шляхів
накладення, 31 перевірений Git blob, 20 місць у 9 одиницях (11 SEM, 9 IRQ).
Локальний повтор аудиту завантаженого кандидата дав семантично ідентичний
JSON. Маніфест усе ще `target_compiled=false` і
`production_installed=false`. Отже, повне джерельне охоплення CI доведено,
але цільова компіляція дев'яти одиниць і робота на роутері — ні.

Прошивкова #542 (`40021678720`, HEAD `ab19045`) завершилася `success`;
`board-build-status-wr1200js` підтверджує статус. Завантажений
`wr1200js-iot-radio-capacity/mt76x3.json` семантично ідентичний #541:
ті самі чотири штатні lock-одиниці мають Kbuild-проби й
`MULTI_CORE_SUPPORT=false`. Це очікувано: експериментальний IoT-кандидат є
в репозиторії як інструмент, але firmware workflow не накладає його у
виробничий модуль. #542 не доводить компіляцію кандидата. Деталі в
`docs/evidence/WR1200JS-IOT-BEACON-DMA-CONTEXT-2026-10-23.md`.

## IoT ізольована компіляція #544 і повторний запуск — 2026-10-24

Ручний run `40046513315` (#544, `5a09fc7`) з `run_candidate_checks=true`
завершився помилкою на кроці `Compile isolated merged IoT MT7603 candidate`.
Артефакт `iot-merged-driver-probe` збережено в сусідній теці
`../iot-merged-probe-544/`. Перший збій: `ap/ap_cfg.c:14639-14642`,
`-Werror=misleading-indentation` у згенерованому debug setter. Звичайний
образ був зібраний раніше; цей збій стосується лише ізольованого кандидата.

Генератор виправлено: `return TRUE` вирівняно після `if (changed)`. Локально
перегенеровано кандидата і підготовлене злиття; змінився лише `ap/ap_cfg.c`
серед 45 вихідних файлів. Коміт `236dedb` також додав збір ефективних
Kbuild/lock даних дев'яти одиниць після цільової компіляції й був відправлений
до PR #2. Базова прошивкова #545 (`40047701330`) та ABI (`40047701287`)
завершилися успішно. Після перевірки порожньої черги запущено рівно один
ручний run кандидата `40048878570`; він був `queued` при останньому читанні.
Локальний full-lock аудит виправленого кандидата підтвердив 31 Git blob і
20 lock sites у 9 одиницях. Результат цільової компіляції ще очікується.
Production IoT та пристрій не змінювалися.

Ручний run `40048878570` завершився помилкою ізольованої компіляції після
проходження попереднього місця `ap_cfg.c`. Новий перший збій:
`common/cmm_mac_pci.c:2740`, макрос `GET_BCNRING_FREENO` має кінцеву `;`
і не є коректним виразом умови. Журнал завантажено до
`../iot-merged-probe-546/build.log`. Генератор кандидата локально змінено на
еквівалентну перевірку індексів кільця; усі 400 допустимих пар індексів при
`BCN_RING_SIZE=20` збігаються з умовою нульового вільного місця макроса.
Нове злиття змінило тільки `common/cmm_mac_pci.c` серед 45 файлів.
Цільову компіляцію цієї правки ще не підтверджено.

ABI run `40049984130` для `22df59a` завершився успішно. Артефакт
`band-steering-mips-abi` збережено в `../iot-abi-548-artifact/`.
Його `iot-full-beacon-locks.json` підтверджує 45 overlay-шляхів, 31 pinned
blob, 20 місць блокування у 9 файлах (11 SEM, 9 IRQ). Незалежний локальний
повтор аудиту з файлів артефакту дав семантично ідентичний JSON. Маніфест
залишає `target_compiled=false`, `production_installed=false`; це джерельна
звірка, не перевірка роботи IoT. Автоматична прошивкова збірка
`40049984099` ще виконувалася під час останньої перевірки.

Базова прошивкова збірка `40049984099` завершилася `success` для `22df59a`.
Черга GitHub Actions була порожня, після чого запущено один ручний run
`40051068385` з `run_candidate_checks=true` для того самого SHA. Він був
`in_progress` при останньому читанні. Звичайний образ не містить IoT-кандидат;
результат його окремої цільової компіляції ще невідомий.

Цільовий run `40051068385` завершився `success`. Його артефакт
`iot-merged-driver-probe` завантажено до `../iot-merged-probe-550/`:
ізольована MIPS-компіляція створила ELF32 MIPS `mt76x3_ap.ko` розміром
5 106 508 байтів. Усі 45 SHA-256 злитих файлів збігаються з локальним
кандидатом; конфігурація ядра не змінилася за перевіркою workflow.
`merged-capacity.json` має повну Kbuild/директивну звірку 9 файлів та
20 місць замка: активні 10 SEM і 9 IRQ, одне SEM місце неактивне;
`MULTI_CORE_SUPPORT=false` в усіх одиницях. У цій конфігурації обидві форми
використовують BH-обгортку. Це доказ цільової компіляції експериментального
кандидата, але не безпечного IoT BSS teardown, не встановлення у виробничий
образ і не роботи на роутері. Деталі та відкритий `modpost` warning — у
`docs/evidence/WR1200JS-IOT-OVERLAY-CONFLICTS-2026-10-24.md`.

Наступна джерельна звірка простежила два асинхронні виклики: beacon DMA
tasklet → `RTMPHandleBcnDmaDoneInterrupt` і RX tasklet → TxS parser →
`BcnTxSHandler`. У чинному target build обидві форми замка переходять до
`spin_lock_bh`, але решта callback-контекстів та порядок вкладених замків
ще не доведені. У коміті `5da2e60` додано fail-closed gate для 19 активних
місць (10 SEM, 9 IRQ) і відсутності `MULTI_CORE_SUPPORT` у всіх дев'яти
Kbuild-одиницях. Локально пройшли `bash -n`, перевірка gate проти
артефакту #550 та `git diff --check`. Коміт відправлено до PR #2;
автоматичні firmware `40053080982` і ABI `40053080975` стартували.
Нова перевірка guard ще не запускалася з `run_candidate_checks=true`.

ABI `40053080975` для `5da2e60` завершився успішно. Базовий firmware
`40053080982` ще виконував крок збірки образу при останній перевірці;
ручний candidate run для нового guard не дублювали. Додаткова джерельна
звірка знайшла, що `RTMPHandleRxCoherentInterrupt` на MT7603 виходить до
очищення кілець; це конкретна виключена гілка, а не доказ відсутності
інших шляхів інверсії `BcnRingLock` ↔ `RxRingLock`.

Ручний optional run `40054121188` для `5da2e60` запущено після звільнення
черги; при останньому читанні виконував `Build WR1200JS firmware`. Це один
запуск для перевірки нового fail-closed guard, результат ще не термінальний.
Окремо перевірено TIM producer на повному кандидатові та в модулі з успішного
run `40051068385`: `RTMPHandlePreTTTTInterrupt` напряму викликає
`APMakeAllTimFrame` (MIPS relocation `0x0000b318`), що веде до подання кадру
у спільне beacon ring. Попередній пошук по вужчому pinned reference tree
пропустив цей виклик. Прямого виклику самого interrupt handler у
зібраному C-кандидаті/модулі не знайдено. Єдиний релокейт до handler лежить
у діагностичній `.rel.pdr`, а `WF_MAC_INT_4` лише читає/маскує регістри, не
викликаючи handler. Це виключає прямий dispatch цією гілкою в ізольованому
модулі, але не є доказом для майбутнього production build або невідомого
непрямого шляху. `beacon_ring_admission_atomic=false` залишається правильним
через інші активні producer/teardown gaps. Деталі в
`docs/evidence/WR1200JS-IOT-OVERLAY-CONFLICTS-2026-10-24.md`.

Ручний run `40054121188` для `5da2e60` завершився `success` з
`run_candidate_checks=true`. Артефакт `iot-merged-driver-probe` завантажено
до `../iot-merged-probe-550-guard/`; новий fail-closed guard виконався після
ізольованої MIPS-компіляції. Звіт: 9 повних одиниць Kbuild, 20 джерельних
місць замка, 19 активних (10 SEM, 9 IRQ), `MULTI_CORE_SUPPORT=false` всюди.
Зібрано ELF32 MIPS `mt76x3_ap.ko`, 5 106 508 байтів. Це підтверджує
саме guard/compile, а не production IoT чи безпечне зняття одного BSS.
Модуль і роутер не встановлювали/не змінювали. Наступне — життєвий цикл
окремого BSS, TxS/DMA завершення та відкриті шляхи producer.

Окремий аудит TxS retirement записано у
`docs/evidence/WR1200JS-IOT-TXS-RETIREMENT-OPTIONS-2026-10-24.md`.
У чинному кандидатові TxS містить 12-бітний SN, але beacon TXD не задає
очікуваний SN у дескрипторі й не зберігає його з PID. Основний драйвер Linux
MT7603 також не позначає SN_VALID для звичайного beacon; це зовнішня
порівняльна реалізація, не доказ поведінки vendor-драйвера. Його timeout
`HZ/4` після DMA — політика відмови, а не гарантований drain. Наступна
реалізація має довести або точну ідентичність звіту, або повний бар'єр
producer/DMA/TxS/RX до повторного використання PID і BSS. Прапорці
приймання залишено false; роутер не змінювали.

Додаткова джерельна звірка бар'єра завершення: `RtmpNetTaskExit` прибирає
спільні RX і beacon-DMA tasklet лише при adapter teardown;
`RTMPRingCleanUp(QID_BCN/QID_RX)` очищає цілі кільця, які належать усім BSS.
Тому виклик цих наявних примітивів при закритті одного IoT BSS порушив би
основну/гостьову мережу. `RTMPHandleBcnDmaDoneInterrupt` розпізнає BSS за
`own_mac`, тож можливий окремий облік DMA, але це ще не TxS drain. Деталі
додано в аудит TxS retirement; production-код не змінювався.

2026-10-24 — наступний крок IoT: у генераторі ізольованого MT7603-кандидата
виправлено повторне використання `bss_idx` між beacon DMA-дескрипторами.
Індекс тепер скидається до недійсного значення перед декодуванням `own_mac`
кожної комірки. Кандидат з pinned `c25283e` зібрано локально; Python syntax,
згенерований код і `git diff --check` перевірено. MIPS-компіляцію саме цієї
правки та runtime не виконано. Доказ: `docs/evidence/WR1200JS-IOT-BEACON-DMA-OWNER-2026-10-24.md`.
Бар'єр вибіркового TxS retirement, production binding та приймання IoT лишаються відкритими.

Публікація цього кроку: коміт `5c17e5a` відправлено до гілки
`codex/wr1200js-service-webui` і PR #2. GitHub запустив firmware #551
(`40056688499`) і ABI `40056688426`; на момент запису вони ще не завершились.
Решта локальних змін не включена до коміту.

Наступна перевірка IoT DMA: окремий лічильник на BSS мусить охопити
публікацію в beacon ring, звичайне DMA-завершення, reset/free/cleanup усього
кільця та порожні комірки. Джерельні точки додано до
`docs/evidence/WR1200JS-IOT-TXS-RETIREMENT-OPTIONS-2026-10-24.md`.
Це не завершений бар'єр і не доказ TxS drain. #551 є PR-збіркою з
`run_candidate_checks=false`; її успіх не підтвердить цільову MIPS-компіляцію
цього ізольованого кандидата. На момент перевірки #551 та ABI ще виконувалися.

2026-10-24 — кандидат вибіркового DMA-знімка: замість лічильника, який
довелося б узгоджувати з усіма шляхами очищення кільця, додано сканування
живих beacon-комірок під `BcnRingLock` для конкретного BSS. Невідомий
власник або неузгоджений стан кільця дає помилку. Перевірку прив'язано до
stage-2 MBSS close; host fixture з виконанням згенерованої C-функції та
close fixture пройшли. Доказ:
`docs/evidence/WR1200JS-IOT-BEACON-DMA-SNAPSHOT-2026-10-24.md`.
Це лише програмний знімок; TxS drain, атомарність усіх виробників,
MIPS-компіляція цієї версії й production/runtime лишаються відкритими.

CI для попереднього коміту `5c17e5a`: firmware #551 (`40056688499`) та
Band Steering ABI (`40056688426`) завершилися `success`. Ці запуски не
містили нового DMA-знімка й не виконували його ізольовану MIPS-компіляцію.

DMA-знімок і host fixture опубліковано окремим комітом `7df3e9c` до PR #2.
GitHub створив firmware #552 (`40066799333`) та ABI `40066799319`; обидва
були в черзі на момент запису. Вони не замінюють цільової збірки кандидата
з `run_candidate_checks=true`. Інші незбережені файли не включено до коміту.

2026-10-24 — firmware #552 завершилася успішно, але ABI `40066799319`
зупинився на застарілій кількості beacon-lock місць у source-inventory gate:
очікувалося 20 SEM/IRQ місць, фактично 21 через новий DMA-знімок.
Після перевірки згенерованого місця оновлено gate до 21 (12 SEM, 9 IRQ).
Локальний повторний аудит pinned source і кандидата пройшов; `git diff
--check` пройшов. Доказ:
`docs/evidence/WR1200JS-IOT-ABI-552-BEACON-LOCK-GATE-2026-10-24.md`.
Це не підтверджує MIPS-компіляцію IoT-кандидата чи безпечний TxS drain.
Виправлення gate і цей доказ опубліковано комітом `06b2620` у PR #2;
статус нового CI ще потрібно перевірити.
Для `06b2620` стартували firmware #553 (`40067873712`) та ABI
`40067873711`; обидва виконувалися під час останньої перевірки.

Додатковий source-аудит pinned MT7603: `common/cmm_data.c:578-617`
обробляє TxS пакет як серію 20-байтних звітів і передає в parser PID без
software generation. Порожній DMA/TxS-знімок не доводить, що старий звіт
уже вийшов з RX batch. Записано у
`docs/evidence/WR1200JS-IOT-TXS-RETIREMENT-OPTIONS-2026-10-24.md`;
вибірковий TxS retirement лишається відкритим.

ABI `40067873711` для `06b2620` завершився `success`, зокрема раніше
невдалий крок `Check private IoT request mailbox`. Firmware #553 ще
виконувалася під час перевірки. Цільова MIPS-компіляція IoT-кандидата
залишається окремим відкритим кроком.

2026-10-24 — під час аудиту усіх виробників `Q_IDX_BCN` знайдено TIM-подання
з `ap/ap_nps.c`, яке обходило намір закриття BSS. В ізольованому кандидатові
додано перевірку `bBcnSntReq` під `BcnRingLock` для вторинного BSS і межі
індексу перед доступом. Host fixture з гонкою закриття та аудит повного
дерева пройшли. Доказ:
`docs/evidence/WR1200JS-IOT-TIM-ADMISSION-2026-10-24.md`. Повної
атомарності кільця, MIPS-компіляції цієї версії та runtime ще немає.
Кандидат і доказ зафіксовано локальним комітом `1ae2408`; push відкладено,
бо firmware #553 ще виконує збірку попереднього коміту.
Після завершення #553 (`success`) і ABI `40067873711` (`success`) коміт
`1ae2408` відправлено до PR #2. Нові CI-запуски треба звірити окремо.
Для `1ae2408` стартували firmware #554 (`40068837518`) та ABI
`40068837433`; обидва виконувалися під час перевірки.

2026-10-24 — firmware #554 (`40068837518`) і ABI `40068837433` для
`1ae2408` завершилися `success`. Звичайний PR build не компілює ізольованого
IoT-кандидата. Після перевірки, що активних збірок цього ref немає, запущено
один ручний workflow з `boards=wr1200js` і `run_candidate_checks=true`:
`40071175138` (той самий SHA). Результат цільової MIPS-компіляції ще не
отримано; перевірити job `build-wr1200js`, крок `Compile isolated merged IoT
MT7603 candidate` та діагностичний артефакт. Новий запуск не дублювати.

Run `40071175138` завершився `failure` до MIPS-компіляції IoT-кандидата:
окремий assembler gate ще очікував 45 overlays/31 originals після додавання
`ap/ap_nps.c` (фактично 46/32). Перевірено склад маніфесту, оновлено точні
лічильники у `tools/iot/assemble-prepared-candidate.py`; локальне складання
повного кандидата завершилося з 46 шляхами і п'ятьма merge. Доказ:
`docs/evidence/WR1200JS-IOT-555-ASSEMBLY-GATE-2026-10-24.md`. Це ще не
підтверджує MIPS-компіляцію; після публікації точкової правки потрібен один
новий `run_candidate_checks=true` запуск для нового SHA.

Вузьку правку assembler gate і доказ опубліковано комітом `1a15f6e` у PR #2.
Нові PR-запуски: firmware `40073309681`, ABI `40073309606`; обидва були
`queued` під час першої перевірки. Після їх завершення, за відсутності
активної збірки на цьому ref, запустити рівно один optional candidate compile
для `1a15f6e`. Існуючі незбережені файли не включено до коміту.

Firmware `40073309681` та ABI `40073309606` для `1a15f6e` завершилися
`success`. Запущено один optional candidate build `40074321999` з
`boards=wr1200js`, `run_candidate_checks=true` на тому самому SHA. До
результату його кроку `Compile isolated merged IoT MT7603 candidate` MIPS-
компіляція цієї ревізії лишається непідтвердженою. Дублікат не запускати.

За запитом власника записано окремий майбутній план Linux 4.4.198 →
4.4.302 у `docs/KERNEL-4.4.302-MIGRATION-PLAN.md`, локальний коміт
`5d41827`. У `docs/PROJECT-DELIVERY-SCOPE.md` додано посилання без зміни
порядку етапів. Міграцію ядра та збірку 4.4.302 не запускали; коміт не
відправляли, поки активна optional IoT збірка `40074321999`.

Optional run `40074321999` завершився `failure` після успішного MIPS
`LD [M] .../mt76x3_ap.ko`. Причина — окремий workflow gate ще очікував
20/19/10/9 beacon-lock sites, тоді як артефакт підтвердив 21/20/11/9
після TIM overlay. Накладено точкове оновлення очікування; predicate
перевірено на завантаженому CI JSON. Доказ:
`docs/evidence/WR1200JS-IOT-556-MIPS-LOCK-GATE-2026-10-24.md`.
MIPS module link підтверджено, але ELF/copy/hash gates і runtime ще ні.

Вузьку правку gate і доказ зафіксовано комітом `6eec863` та опубліковано
разом із попереднім документним комітом `5d41827` одним push до PR #2.
Нові PR-запуски на `6eec863`: firmware `40075915187`, ABI `40075915089`;
обидва виконувалися при першій перевірці. Optional build для цього SHA
не запускати до їх завершення і перевірки відсутності дубля.

Обидва PR-запуски на `6eec863` завершилися успішно: firmware
`40075915187` та ABI `40075915089`. Після перевірки відсутності активного
дубля запущено один optional IoT run `40077253251` з
`run_candidate_checks=true`. На момент запису його WR1200JS job виконується;
перевірити фінальний результат, насамперед merged lock, ELF/copy/hash gates.

За останнім уточненням власника можливий перехід Linux 4.4.198 → 4.4.302
закріплено як останній етап проєкту: одразу після завершення Mi Mini та
решти погоджених робіт. За умови окремого схвалення міграція охопить кожен
роутер, доданий до проєкту на той час, з окремим аналізом і прийманням для
кожної плати. До цього етапу ядро залишається на 4.4.198. Початковий аналіз
WR1200JS не є планом міграції для інших плат. Ці уточнення документації
локальні, не опубліковані.

Optional run `40077253251` завершився `success`. Ізольований MT7603
кандидат зібрано й скомпоновано як MIPS `.ko`; пройшли merged lock,
джерельний SHA256/copy, MIPS ELF та незмінність `.config`. Завантажений
артефакт перевірено локально; точні хеші й межі висновку записано у
`docs/evidence/WR1200JS-IOT-557-OPTIONAL-MIPS-CANDIDATE-2026-10-24.md`.
Виробничого backend і перевірки на роутері це не встановлює.

Далі в коді кандидата виявлено конкретну прогалину перед IoT BSS open:
`mbss-open-admission.inc` не перевіряє фактичний стан основного радіо після
отримання ticket і до `wr_iot_mbss_open_raw()`. Послідовний host-тест
`check-radio-transition.c` пройшов із `-Werror`, але гонку не покриває.
Безпечний порядок виправлення та межі доказу записані в
`docs/evidence/WR1200JS-IOT-558-MBSS-OPEN-REVALIDATION-GAP-2026-10-24.md`.

У кандидатному `radio-transition.h` додано
`wr_iot_radio_abort_bss_open_unmutated()` для відмови до vendor/hardware
мутації; `mbss-open-admission.inc` більше не скидає `busy` прямим присвоєнням
при невдалому резервуванні посилання. Існуючий локальний
`check-radio-transition.c` доповнено випадками stale ticket, reset,
main-down і close під час такого скасування. Host GCC з `-Werror` пройшов.
Це кандидат і послідовна модель, не доведення інтеграції драйвера; повторна
апаратна перевірка перед raw open і спільний власник усіх mutator ще відкриті.

У кандидатному `mbss-open-admission.inc` тепер після ticket/ref reservation
IoT BSS перевіряє основний MT7603 інтерфейс через наявний observer поза
transition lock, а перед raw open під цим lock повторно звіряє serial/epoch,
READY/main_ready та close/reset/retire intent. Невдале спостереження
скасовує лише квиток до vendor UP. Guest BSS зберігає свій шлях.
Новий injected-IO host-тест `check-mbss-open-revalidation.c` пройшов з
`-Wall -Wextra -Werror`; Python fixture генератор доповнено цими випадками,
`py_compile` і `git diff --check` пройшли. MIPS збірка цієї нової ревізії,
повна участь усіх mutator і робота на роутері ще не перевірені.

Кандидатну правку та host fixture зафіксовано `3095603` і разом із
документними `a332f11`, `7152d25` відправлено одним push у PR #2.
Автоматичні запуски на `3095603`: firmware `40079234854`, ABI
`40079234798`; обидва виконуються на момент запису. Не запускати optional
дублікат до завершення цих job. Повна MIPS кандидатна компіляція цієї
ревізії все ще потребує окремого optional прогону.

Додатковий host-випадок відмови `wr_iot_ref_reserve` після ticket пройшов
із `-Werror`; зафіксовано локальним комітом `010fc2c`, ще не відправлено.
На останній перевірці ABI `40079234798` виконував host-kernel IoT isolation,
а firmware `40079234854` збирав WR1200JS; жоден не був terminal.

Обидва запуски на `3095603` завершилися `success`: ABI `40079234798`
та firmware `40079234854`. Після перевірки відсутності активного дубля
запущено рівно один optional IoT run `40080616642` на віддаленому SHA
`3095603` з `run_candidate_checks=true`. Дочекатися точного результату
кандидатної MIPS-компіляції та артефакту; локальний test-only `010fc2c`
не входить у цей запуск. Виробничий backend і пристрій не змінено.

Optional run `40080616642` завершився `success`. Завантажений артефакт
підтвердив MIPS32r2 `.ko`, source-copy/hash, 21/20/11/9 lock gate та
незмінність `.config` на `3095603`. Точні байти/хеші й межі висновку:
`docs/evidence/WR1200JS-IOT-559-MBSS-REVALIDATION-MIPS-2026-10-24.md`.
Це не підтверджує виробниче встановлення або роботу на пристрої.

Наступний source-аудит виявив конкретну all-mutator прогалину: кандидатний
`MainVirtualIF_close` виставляє `main_down` перед мутацією, але не резервує
ексклюзивний transition ticket і не чекає завершення вже прийнятого IoT
BSS-open ticket. Тому close після другої перевірки може перетнути raw open.
Доказ і потрібні interleaving-перевірки:
`docs/evidence/WR1200JS-IOT-560-MAIN-CLOSE-OWNER-GAP-2026-10-24.md`.

Уточнення до цього аудиту: pinned `ap_mbss_inf.c` та `rt_linux.c` показали,
що штатні MBSS open/close і main open/close є `ndo_open`/`ndo_stop`, які
серіалізує RTNL. Тому попередня фраза про гонку саме цих штатних callback
була надто широкою; документ 560 виправлено. Залишається перевірити прямі,
PM/watchdog/error і reset шляхи поза RTNL, перш ніж змінювати main close.

Точну pinned MT7603 ревізію перевірено у тимчасовому sparse checkout поза
робочою текою. Прямих C-викликів main/MBSS open/close, окрім реєстрації
ndo-hook, не знайдено; reset має debug/PCI/watchdog входи поза RTNL.
Кандидатний reset wrapper ставить pending і пробує RTNL, із періодичним
retry, але це не доказ гарантованого завершення. Інвентар і наступний
цільовий аудит: `docs/evidence/WR1200JS-IOT-561-RTNL-RESET-ENTRY-INVENTORY-2026-10-24.md`.


### IoT MBSS-open intent interleaving — 2026-10-24

Розширено локальний injected-IO host fixture для двох випадків: reset або
close надходить усередині raw `BSS_UP`. Кандидат завершує успішний raw open зі
збереженим `WR_REF_OWNED`, не публікує `main_ready`, а reset лишається pending
або close лишає фазу CLOSING. Перевірено як standalone fixture і як fixture,
згенерований з кандидата, зібраного з точних pinned Git blobs
`c25283e915a2a00a763774dd255b14aff997285e`; обидва запуски пройшли з GCC
`-std=c11 -Wall -Wextra -Werror`. Python AST parse і `git diff --check` також
пройшли. Це модель з injected driver IO, не повна конкурентна перевірка ядра.
Правки тесту локальні, не закомічені й не опубліковані. Наступне: довести
гарантований drain/reset retry після звільнення BSS-open ticket, зокрема
життєвий цикл періодичного worker; production backend і runtime ще відкриті.


### IoT deferred reset retry liveness — 2026-10-24

Pinned source audit `c25283e915a2a00a763774dd255b14aff997285e` confirms the
candidate retry hook runs only after periodic MLME command processing.
`RTPCICmdThread` exits after wait failure and drains queued commands on exit;
init-failure and normal halt paths stop timers/MLME and call `RtmpMgmtTaskExit`.
Therefore pending reset has no proven eventual executor after worker/timer shutdown.
Radio readiness remains fail-closed, but that does not guarantee reset completion.
Evidence: `docs/evidence/WR1200JS-IOT-562-RESET-RETRY-WORKER-LIVENESS-2026-10-24.md`.
Next: design one lifetime-safe reset owner for RTNL deferral, worker exit,
PM suspend/resume and normal/init-failure teardown; preserve pending reset over
suspend and distinguish verified bring-up from radio-off/close software returns.
Then cover its interleavings. Candidate only; no firmware or router changes.

Close-path follow-up: `prepare-checked-close.py` stages a helper but explicitly
leaves legacy callers unreplaced and outer resource retention unproven. The
adapter candidate includes the physical-close bridge beside `rt28xx_close()`
without redirecting the legacy caller. Its success means software close
completion, not hardware/RF quiescence, while successful `WR_RADIO_CLOSE`
finish clears `reset_pending`. Do not equate these signals. No safe terminal
reset recovery is established; next prove the complete close/PM/error chain,
hardware quiescence and adapter lifetime. Source inspection only; no test,
build, CI or device action. See the added close-path section in evidence 562.

Pinned PM trace is now recorded in evidence 562: suspend invokes
`RTMP_DRIVER_PCI_SUSPEND`, then `rt28xx_close`, then disables PCI. The legacy
`rt28xx_close` calls void `RTMPDrvClose` and returns zero even when its radio-off
attempt failed (failure is only logged). This tears down the candidate's
periodic retry source before power-down, so pending reset must survive suspend
and block readiness until verified resume recovery. No suitable terminal
teardown contract has been proved; next design the owner across suspend/resume
and adapter lifetime before source integration. No test/build/CI/device action.

Further pinned teardown trace: `rt_pci_remove` calls `RtmpPhyNetDevExit`, then
`RtmpRaDevCtrlExit`, which calls `RTMPFreeAdapter` and frees adapter locks and
storage. The current candidate requires quiescence before freeing its
transition lock but has no delayed-work owner/cancel path. Any independent retry
executor must be initialized before cleanup can occur, block new scheduling
after retirement, and be synchronously drained before adapter memory is freed;
RTNL acquisition in its worker must stay nonblocking. Exact evidence and
remaining PM/resume invariants are in section “Adapter lifetime and
deferred-worker requirements” of evidence 562. No code or tests changed.

Resume trace in evidence 562 is now exact as well: PCI D0/state restore and
enable precede `netif_device_attach`, `rt28xx_open`, PCI-resume notification and
queue wake. The transition candidate is not bound to this callback; `rt28xx_open`
reinitializes the driver but does not itself prove radio readiness. Next design
how to keep queues/BSS admission fail-closed through resume recovery and readback,
including whether attach must move or remain gated. No code/test/build/CI/device
action this step.

### Kernel migration order clarification — 2026-10-24

The owner reconfirmed that Linux 4.4.198 → 4.4.302 belongs at the very end of
the project, after Xiaomi Mi Mini, all other agreed work, and repository source
consolidation. It remains a conditional future stage: decide then whether to
proceed. If approved, cover every router in the project at that time, with
board-specific compatibility review, builds and device acceptance. Keep all
routers on 4.4.198 until that stage. See the final-stage section in
`docs/PROJECT-DELIVERY-SCOPE.md` and `docs/KERNEL-4.4.302-MIGRATION-PLAN.md`.
Planning clarification only; no migration or build started.

## IoT isolated PCI suspend/resume state model — 2026-10-24

Added candidate-only `SUSPENDING`/`SUSPENDED` transitions to
`tools/iot/radio-transition.h`. Suspend invalidates readiness and prevents new
radio tickets, preserves an admitted or newly requested reset for resume, and
cannot complete while a ticket remains active. Resume returns to `UNVERIFIED`;
pending reset or main-radio readback must succeed before BSS can reopen. Added
sequential fixture cases in `tools/iot/check-radio-transition.c` for reset,
initial START and BSS-open races across suspend, suspend close, and PM-time
reset coalescing.

Validation: MinGW GCC strict C11 compile with `-Wall -Wextra -Werror -O2` and
both `check-radio-transition.c` and `check-reset-admission.c` fixtures passed.
CI-equivalent ASan/UBSan linking was unavailable locally (`-lasan`/`-lubsan` not
installed); no MIPS compiler, CI run, target driver build, image build or router
operation was used. This model is not wired to vendor PCI callbacks and does
not prove worker cancellation/liveness, queue gating or radio-off. Keep IoT
unaccepted and do not integrate it into the driver yet.

Further pinned-source finding: PM suspend/resume and driver remove callbacks
are serialized under the device lock, but ordinary netdev `ndo_open`/`ndo_stop`
RTNL context does not apply to PCI PM's direct `rt28xx_close/open` calls. More
critically, resume calls `netif_device_attach` before `rt28xx_open`; kernel
`netif_device_attach` wakes TX queues for a running netdev. This candidate gates
BSS-open only, not packet TX, so queue/attach exposure is a concrete remaining
integration gate. Evidence, exact source paths and next requirements:
`docs/evidence/WR1200JS-IOT-562-RESET-RETRY-WORKER-LIVENESS-2026-10-24.md`.

Additional pinned-source finding: main, MBSS, AP-client, WDS and monitor
netdevs assign `rt28xx_send_packets`; its only netdev readiness check is
`IFF_UP`. PCI suspend stops/detaches the main netdev and calls physical close
directly, without invoking each virtual netdev stop callback. Consequently
deferring main attach alone does not establish an all-interface transmit fence.
A shared admission barrier and in-flight TX drain before radio close/PCI
power-down are required; the current model has neither. The exact hooks and a
candidate PM ordering contract are recorded in evidence 562.

Next: prove interface enumeration/ownership and a sleep-safe active-TX drain
primitive across all virtual netdevs, then implement the PM failure unwind,
worker cancellation and queue gate in a separate candidate before driver
integration or target compilation.

Registry coverage audit: `prepare-radio-queue-candidate.py` currently binds
checked registration only to MBSS. The allocated registry stores raw netdev
pointers and has no pinned all-interface snapshot; its own release contract
requires externally proven callback quiescence. It cannot yet enumerate and
hold main, AP-client, WDS and monitor devices for PCI PM. Evidence 562 records
the exact gap and next integration requirements. No production change made.

Pinned-source lifecycle map now locates attach and detach/free for main,
MBSS, AP-client, WDS and monitor. AP-client, WDS and monitor ignore attach
return; monitor index-registration failure also leaves `wdev->if_dev` pointing
to freed storage. Fixing those error/lifetime paths and pinning registry
snapshots precedes any PCI PM iteration. Details in evidence 562.

An isolated, source-pinned monitor cleanup candidate now handles failed index
registration and failed netdev attach, including the separately `vmalloc`'d
`netdev_ops`. Exact original blob/anchors and Python syntax passed; no target
C build or firmware integration. Continue with AP-client/WDS error paths and
all-interface reference ownership before PCI PM work. Evidence 562 updated.

Monitor cleanup is now a stage of the combined IoT candidate assembler. The
full assembler passed against an exact LF Git archive and emitted the monitor
file and manifest; the default Windows CRLF archive had stopped at an older
TxS exact-blob gate. This validates candidate composition only, not a driver
build, image or runtime. No production source or router was changed.

AP-client and WDS index/attach failure cleanup is now a source-pinned stage
in that same combined candidate. It frees separately allocated netdev ops,
clears stale `if_dev`, retires the wdev index on attach failure, and avoids an
AP-client initialized flag if the first registration fails. Full candidate
preparation passed on the LF source archive; generated paths were inspected.
Target C compile and runtime failure injection remain open. Evidence 562.

Main PCI probe failure also needs cleanup: original attach failure leaves
`pci_set_drvdata` pointing at freed netdev and leaks its separately allocated
ops. A source-pinned PCI cleanup stage now clears driver data and frees ops;
full candidate preparation passed on exact LF source. Existing MBSS candidate
already handles index/attach failure in a host fixture. Neither establishes
PM traversal safety or target runtime acceptance. Evidence 562 updated.

Pinned Linux refcount and call-graph correction: `netdev_run_todo()` waits for
all `dev_hold` references during unregister, so a long PM-held reference can
deadlock removal. Virtual interfaces are initialized inside `rt28xx_open`,
which PCI resume invokes directly outside netdev `ndo_open` RTNL context.
Plan a bounded, serialized queue snapshot and release references before
unregister waits; keep active-TX drain separate. Evidence 562 revised.

Added a candidate TX admission counter to `radio-transition.h`: PM fence
rejects new packets and suspend completion waits for all admitted driver TX
entries to leave; close/reset admission also checks the count. Sequential
fixture includes two-TX suspend, close and reset races and passed strict
MinGW C11 compilation. The common `rt28xx_send_packets` hook is now staged in
the exact-source adapter candidate; its extracted host fixture passed strict
C11 compilation and verified refusal, packet release and lease balance. No
PCI PM binding, DMA drain, target compile or production install yet. The
adapter candidate now initializes a TX drain waitqueue and signals it after
the last lease exits outside the spinlock. Host fixture confirms accepted-TX
wakeup and rejected-TX silence; complete LF-source bundle preparation passed.
No PM waiter/timeout or teardown synchronization is installed. Evidence 562.
## IoT PCI PM TX drain checkpoint — 2026-10-24

Pinned PCI suspend source confirms main-netdev detach, direct legacy
`rt28xx_close()`, then PCI disable/power-down. The legacy close returns zero
without a physical close failure result. A TX wait timeout must therefore
abort power-down and restore a safe detached state; a waiter alone is not a
valid PM binding. Corrected the isolated adapter candidate manifest to mark
the existing last-TX wakeup as staged and the PM waiter as unbound. Python
syntax, exact-source candidate preparation and `git diff --check` passed.
No production driver, image, CI or router state changed. See evidence 562.

The isolated transition model now aborts a failed pre-close PCI suspend into
UNVERIFIED without reopening TX/BSS admission or erasing reset intent. Strict
MinGW C11 host fixture and full exact-LF candidate bundle preparation passed.
PCI callback, queue unwind, physical-close result and DMA drain remain open.
Admission review then closed a model race: after abort, active TX now blocks
VERIFY/MAIN_OPEN and all other new radio operations until the lease exits.
Strict C11 fixture passed. This has not been target-compiled or installed.
The exact-source adapter candidate now stages a lock-protected TX-idle wait
helper with bounded `wait_event_timeout`; host fixture covers immediate idle,
expired wait and last-TX wakeup. Full IoT candidate assembly passed. The helper
is not bound to PCI PM and does not establish DMA or adapter lifetime safety.
Pinned PCI ioctl tracing found suspend sets HALT/RADIO_OFF flags before legacy
close and resume clears them later. Timeout unwind must reconcile those flags,
queues and transition state. Strengthened checked-close host fixture to use a
real CLOSE ticket and reject a stale serial; strict C11 build/run passed.
Added a separate unmutated PCI-suspend timeout rollback to the isolated
transition model. It restores prior READY only before any queue/vendor/hardware
change and when no reset, close or exclusive operation intervened; otherwise
the earlier UNVERIFIED abort remains. Strict host C11 fixture and exact-LF
candidate assembly passed. No PCI binding or target compile.
The isolated PCI/AP candidate now registers main, MBSS, AP-client, WDS and
monitor netdevs through one checked attach bridge. Exact-LF bundle preparation
and strict host registration fixture passed. SDIO is outside this board path.
Unregister retirement, pinned enumeration and PM queue traversal remain open;
the registry still contains raw pointers and cannot yet serve as a PM list.
Pinned ioctl source confirms MBSS, AP-client, WDS and monitor can be removed
outside PCI remove. Candidate attach now counts registration in progress,
blocks new attach after PM fence, and wakes a bounded registration-idle helper
after completion. Strict host fixtures and full exact-LF bundle passed. PM
waiting, dynamic removal retirement and referenced snapshots remain unbound.
Added a short registry snapshot model that selects published/non-removing
records under the adapter lock and requires caller-supplied lifetime pinning.
Strict host fixture and full exact-source candidate assembly passed. Kernel
`dev_hold/dev_put`, dynamic remove intent and PCI PM use are not bound.
The partial IoT candidate now marks MBSS/AP-client/WDS/monitor removal before
RTNL unregister, so a short snapshot excludes those entries. Host fixture
and exact-LF assembly passed. Registry slot release after vendor quiescence is
unbound; the stage would retain tombstones on repeated dynamic removal and is
not fit for production installation yet.
An unbound adapter helper now pins each published netdev with `dev_hold` under
the shared lock, stops its queue, and drops all refs before returning. It
requires PM fence and registration drain. Generated strict C11 fixture and
full exact-LF candidate preparation passed. No PCI call, queue unwind or
target MIPS compile; dynamic removal retirement remains incomplete.

The pinned PCI suspend ioctl sets HALT/RADIO_OFF, but legacy `RTMPDrvClose`
clears HALT even during suspend. The isolated checked-close candidate now
retains HALT while `pm_suspending` is set; ordinary close still clears it.
Full exact-LF assembly and two strict MinGW C11 extracted host fixtures
passed. Production PCI/driver, image and router remain unchanged. Evidence:
`docs/evidence/WR1200JS-IOT-562-RESET-RETRY-WORKER-LIVENESS-2026-10-24.md`.

The transition candidate also now rejects `suspend_complete()` after a failed
physical CLOSE left CLOSING. With no busy ticket, a failed CLOSE or a later
PCI failure after successful CLOSE aborts to UNVERIFIED rather than restoring
readiness. Strict C11 transition test and exact-LF candidate assembly passed.
PCI error unwind, queue/vendor-flag reconciliation and target build remain open.

MBSS removal candidate now marks the published netdev as removing before
beacon-buffer deinitialization. Full exact-LF assembly and generated-source
order check (`mark < deinit < unregister`) passed. This closes a PM snapshot
ordering gap but does not prove concurrent callback quiescence or safe registry
slot reuse. No production driver/image/router change. Evidence: 562 report.

Removal review found a separate MBSS gate: `wdev_bcn_buf_deinit()` returns
FALSE for non-IDLE beacon state, but `MBSS_Remove()` ignores the result and
continues unregister/free. MBSS close has no unconditional IDLE transition.
Registry release must wait for checked beacon retirement and vendor callback
quiescence; source review recorded in evidence 562. No target/runtime proof.

The isolated registry now supports canceling a removal mark only before any
teardown mutation and only without PM/retirement; strict host C11 fixture and
full exact-LF assembly passed. It is not bound. Tracing found that MBSS remove
failure would also need propagation through ap_cfg ioctl, the VOID wrapper,
`RtmpPhyNetDevExit()` and PCI remove before adapter free. Evidence 562.

Staged an adapter-locked cancellation bridge for an unmutated failed remove.
Host registration fixture checks PM refusal, retry after PM abort, and refusal
after unregister-stage advancement. Strict C11 and full exact-LF assembly
passed. The bridge is not called by MBSS remove; no production/runtime proof.

2026-10-24: The owner made IoT a mandatory release capability for every
project router, including WR1200JS, Mi Mini and future boards; build profiles
must not omit it. This rule is recorded in AGENTS.md, the delivery scope and
the IoT contract. Runtime enable/disable remains distinct. Current firmware
images excluding IoT are development checkpoints, not release-ready.

The isolated candidate now checks MBSS beacon deinit and propagates failure
through the leaf ioctl path; strict C11 extracted fixture and exact-LF
candidate assembly passed. The VOID wrapper, RtmpPhyNetDevExit and PCI remove
still do not propagate failure. Production binding, target build and router
runtime remain open; see evidence 562.

The isolated assembler now carries the checked MBSS removal result through
`RT28xx_MBSS_Remove` and `RtmpPhyNetDevExit`. Python syntax check, exact-LF
assembly and generated call-site inspection passed. PCI remove still ignores
the result and frees the adapter; other child removals are unchecked. This is
not production-safe teardown. Evidence 562 records the precise boundary.

The two-virtual-BSS host fixture reproduced partial MBSS removal: second-BSS
beacon refusal leaves the first freed, and retry invokes its beacon deinit
again. Strict C11 MinGW test passed as a diagnostic. The candidate needs
per-BSS retirement state and a shared transition owner before retry or PCI
teardown can be safe. No production/runtime acceptance is implied.

Pinned-source audit also found `VOID` AP-client, WDS and monitor remove
wrappers around detach/free paths. Physical exit removes AP-client/WDS
before MBSS and monitor after it, so the current early-return candidate can
leave a mixed partially removed adapter. The next implementation must cover
all child interfaces and PCI lifetime in one transition contract. Evidence 562.

An isolated all-child teardown state model and strict C11 fixture now cover
AP-client/WDS/MBSS/monitor completion, unmutated abort, partial-failure
poisoning and release gating. Fixture passed. It is not bound to driver or
PCI removal and does not prove actual quiescence; per-BSS milestones remain
open. Evidence 562.

An isolated generation-keyed per-BSS retirement model now records beacon,
kernel and vendor milestones. Combined host fixture gates MBSS-family
completion on every BSS; strict C11 and full candidate assembly passed.
No vendor binding, target build or runtime proof yet. Evidence 562.

The isolated adapter candidate now allocates and initializes the all-child
and per-BSS retirement storage before adapter publication. Full exact-LF
assembly, syntax and generated-source checks passed. These fields are not
yet updated by real removal callbacks; target build/runtime remain open.

The isolated shared netdev-attach bridge now gives MBSS a generation-keyed
state before netdev publication and rolls it back on attach failure. Strict
C11 registration fixture and full exact-LF assembly passed. Prior MBSS
attach failure cleanup was already present in the radio-error stage. Removal
milestones, PM interleaving, target build and runtime remain open. Evidence 562.

Strict MBSS attach fixture now injects PM suspend mid-registration and checks
generation and in-flight drain. It passed. Pinned PCI suspend does not call
the staged registration wait, so the real PM/attach race remains unresolved;
bind the fence and bounded wait before queue stop/radio close. Evidence 562.

The isolated PCI suspend candidate now fences admission under the common
lock and waits up to two seconds for in-flight registrations before its
first queue/carrier mutation. Syntax, exact-LF assembly and generated-source
ordering passed. TX/DMA drain, checked close, PM completion, resume and
power-failure unwind remain open; this is not a working PM binding. Evidence 562.

The PCI PM fence was extracted from the assembled candidate and compiled in
a strict C11 host fixture. Success, registration timeout before mutation and
reset-during-wait fail-closed cases passed. No local MIPS compiler was found;
WSL did not expose a usable distribution. Target/CI and runtime are still
unverified. Evidence 562.

The isolated MBSS remove path now binds generation-checked removal intent
and the beacon-success milestone under the adapter lock. Strict registration
and extracted MBSS C11 tests plus full assembly passed. Kernel/vendor-done
events and safe retry after partial teardown are not bound; target/runtime
remain open. Evidence 562.

The isolated MBSS loop now skips a BSS with no netdev on retry. The extracted
two-BSS strict C11 test confirms that a second-BSS refusal no longer repeats
the first beacon deinit; full assembly passed. Kernel/vendor retirement and
PCI failure ownership are still unproved. Evidence 562.

Generation-matched MBSS remove admission now rejects a non-IDLE interface
reference and active OS TX under the common adapter lock. Strict C11 cases
and full candidate assembly passed. Checked `ndo_stop` is not bound, so this
is a fail-closed gate rather than operational teardown. Evidence 562.

\r\n
## IoT MBSS stop ownership audit — 2026-10-24

Pinned MT76x3 `MBSS_VirtualIF_Close` is the netdev stop hook, but
`VIRTUAL_IF_DOWN` discards its ioctl result. In `common/cmm_cfg.c`, DOWN
decrements shared `VirtualIfCnt` before last-interface `rt28xx_close` and
discards that result; UP changes the same count without a common transition
lock. The isolated checked MBSS close therefore cannot yet be bound safely.
Required next: serialize all virtual-interface UP/DOWN writers with radio
transitions, retain ownership on close failure and
test main/MBSS/reset interleavings. Exact evidence in the IoT contract.
The isolated candidate already has arithmetic zero/overflow guards, but no
serialization. Source inventory confirms main, MBSS, AP-client, WDS and
optional sniffer all use the shared dispatcher.
Further source check: `wr_iot_virtual_down_checked` already owns staged
last-close decrement and retry state under a ticket; it is not wired to the
five legacy `VIRTUAL_IF_DOWN` callers. No second counter reservation helper
was added. See the IoT contract for the exact integration boundary.
Recompiled and ran `check-virtual-down.c` with local MinGW GCC
(`-std=c11 -Wall -Wextra -Werror`): exit 0. This is a host model check, not
MIPS compilation or device evidence. The resulting temporary executable is
`C:\Users\ANDRZEJ\AppData\Local\Temp\iot-virtual-down-check.exe`;
the command tool rejected its cleanup operation.
Pinned-source continuation: legacy `rt28xx_close` always returns 0, including
when adapter lookup fails, and calls a `VOID RTMPDrvClose`. Returning its value
from the ioctl would not propagate checked teardown failure. MBSS admission
already has a BSS_OPEN ticket, but its raw UP still uses the shared legacy
dispatcher. Next integrate common UP/DOWN ownership with the existing checked
close chain; do not treat a legacy zero return as teardown proof.
Source audit only; no target build, production driver or router change.


## IoT reserved-open removal gate — 2026-10-24

`wr_iot_registry_begin_remove` in the isolated candidate now refuses
`WR_REF_RESERVED`, preventing generic removal from marking a device while
its admitted MBSS open is between observation and raw UP. Retry after ticket
retirement remains possible; OWNED/CLOSING removal intent is preserved.
The CLOSING portion describes this historical candidate and is superseded by
the 2026-10-25 v39 guard above: an unfinished close refuses new removal until
its checked continuation returns the record to IDLE.
Host registry and netdev-registration tests compiled with strict C11 `-Werror`
and ran with exit 0. No production/MIPS/router change. See IoT contract.
Follow-up: the assembled MBSS removal checks begin_remove before beacon
deinit and returns on refusal. The expanded fixture proves RESERVED is refused
by both generic and MBSS-specific admission while BSS remains LIVE; strict
C11 compile and run returned 0. Generic other-family removal is unbound.
Full isolated candidate preparation from pinned MT76x3 exited 0 at
`.iot-local-check/reserved-removal-20261024`; generated header and MBSS
removal source contain the guard and pre-deinit refusal respectively. No
MIPS compile/image or device proof.
## IoT atomic MBSS close admission — 2026-10-24

Added `wr_iot_registry_find_owned` and isolated
`wr_iot_mbss_begin_close`: under one adapter lock it checks the published
OWNED record, reads `VirtualIfCnt`, starts CLOSE/BSS_CLOSE and returns the
registration generation with the ticket. Direct strict C11 fixture now covers
unpublished record, zero count and competing ticket; it and both composed
open/close/down and last-close-chain fixtures passed `-Werror` compile/run.
This is not wired to production `ndo_stop` or other families. Shared count
owner, lifetime/TxS quiescence, MIPS build, image and device proof remain open.

## IoT MBSS close post-call revalidation — 2026-10-24

Extended the isolated MBSS close with generation/ticket revalidation after
each unlocked vendor step and before every close-stage write/reference consume.
The uncertainty path also refuses to write into a replaced registration.
Injected same-address slot reuse during `MBSS_Close`; strict C11 fixture
proved the old operation fails without mutating the new slot or releasing its
module reference. Combined open/close/down and last-close physical-chain
fixtures also passed `-Werror` compile/run. This remains fail-closed candidate
behavior, not permission for live slot reuse: shared owner, callback drain,
target compile and device proof remain open. Production/router unchanged.

## IoT MBSS close generation check — 2026-10-24

`wr_iot_mbss_close_checked` now accepts an expected registration generation
and rejects zero/stale values via the existing registry before any close
mutation. Direct strict C11 test, composed MBSS open/close/down fixture and
last-close physical-chain fixture compiled with `-Werror` and ran successfully.
The combined fixture had stale UP/type assumptions; corrected them to the
current extracted raw wrapper, then reran to completion. Python fixture
scripts compile. This is isolated candidate code only. Caller generation
pinning across unlocked vendor work, all-family owner, target build and
runtime remain open; no production driver or router change.

## IoT shared openable registry lookup — 2026-10-24

The isolated registry now has one openable-record lookup requiring published,
non-removing IDLE state and nonzero generation under the adapter lock. MBSS
admission uses it. Strict C11 `check-interface-registry.c` and a freshly
composed MBSS admission fixture both compiled with `-Werror` and ran with
exit 0. This reduces a duplicated lookup and supplies the existing generation
for a future private UP request. The common dispatcher and other families
are not bound; no target build, production driver or router change.

## IoT all-family caller gate — 2026-10-24

Added `tools/iot/check-virtual-if-call-coverage.py` as a fail-closed source
gate for the upcoming all-family ioctl ABI migration. It found exactly one
UP and DOWN call in each of main, MBSS, AP-client, WDS and sniffer in the
staged `reserved-removal-20261024/driver` tree, and displayed the current
two-callback request fields. Python compile and the gate passed. It does not
test driver operation; no production or router change.

## IoT common ioctl identity gap — 2026-10-24

The source check of the common `VIRTUAL_IF_UP/DOWN` request found an ABI gap:
`RT_CMD_INF_UP_DOWN` carries only open/close callbacks, no netdev/family or
registration generation, and DOWN returns `VOID`. The common dispatcher
cannot validate per-interface ownership at its count mutation boundary.
Recorded the all-family request/result migration requirement in the IoT
contract. This is source evidence only; no production-driver or device change.

## IoT shared dispatcher coverage inventory — 2026-10-24

Current isolated candidate tickets main and MBSS open, but AP-client, WDS
and sniffer still enter raw VIRTUAL_IF_UP; all five DOWN callers remain
legacy. AP-client also ignores APC_OPEN status after virtual UP. The shared
dispatcher cannot be promoted from the MBSS helper alone. Exact family
coverage and next integration boundary recorded in the IoT contract.
Source inventory only; no production/target/device change.
Pinned `ApCli_Open` can fail on a missing device after virtual UP and possible
packet-forward probe; a bare propagated error would leak count/ref ownership.
Pre-UP generation validation and checked post-UP rollback are required.
## Zapret2 pinned source base — 2026-10-24

### IoT caller identity continuation

Correction: upstream `BndStrg_SetInfFlags` updates a band-wide ready flag.
Clearing it for an aborted IoT BSS could disable steering readiness of the
active main 2.4-GHz BSS. Removed that unsafe `FALSE` rollback from the
isolated candidate generator. Abort still clears IoT beacon intent, but
band-level ownership and daemon convergence remain unresolved. The previous
abort fixture result is superseded. Generated isolated v5 from the v2 identity
tree; five-family source gate passed. Extracted v5 abort passed strict C11
host check: IoT beacon cleared while main beacon stays requested. No MIPS
build or router operation was performed.

Next isolated v6 additionally removes the band-wide `BndStrg_SetInfFlags`
updates from secondary `MBSS_Open` and `MBSS_Close`; main AP lifecycle retains
its updates. The five-family source gate passed and confirms no secondary
open/abort/close update remains. This prevents IoT close from marking the
active main 2.4-GHz band unready in this candidate. Radio lifecycle
serialization, target compile and device acceptance remain open.

Reviewed isolated `MainVirtualIF_close`: it latches main-down but then calls
`RTMPInfClose` and `VIRTUAL_IF_DOWN` without claiming or waiting for the
shared radio ticket. An admitted IoT open can still mutate in parallel.
Added host-only `wr_iot_radio_begin_main_stop` and strict C11 cases for busy
IoT open, retained inhibition after retry, zero count, and final physical
close classification. The sequential model passed. Driver binding requires
a bounded ticket-drain wait/wakeup, stabilized count and actual close-result
propagation; no firmware or router change was made.
Corrected repeated main-stop admission: retries while the IoT ticket remains
busy no longer increment the epoch repeatedly. Strict C11 transition test
passed with an explicit stable-epoch assertion.
Added ticket-specific `retired_serial` to the host transition model so a
future bounded wait can distinguish the admitted IoT operation from a later
one. Successful finish and unmutated abort publish retirement; stale abort
does not. Radio and auxiliary C11 fixtures passed. Kernel wait queue/wakeup
and main-close binding are still absent, so this is not runtime proof.
Isolated v8 now has `wr_iot_ticket_wait` storage/init, a bounded
ticket-retirement wait helper, and post-unlock wakeups at the currently
admitted MBSS/main-open/reset completion paths. Five-family source gate and
strict C11 wait fixture passed. Production main-close still does not call the
wait helper; all-family count ownership, target compile and router evidence
remain open. The failed v7 scratch generation was superseded by v8; neither
was packaged or sent to the router.
Added a host-only registry/count gate for main stop. It requires the closing
device to be the owned main netdev and every vendor reference to have an
unambiguous published owner; mismatches or in-flight/uncertain records refuse
teardown before changing the radio epoch. Strict C11 registry and main-stop
tests passed. Legacy main/AP-client/WDS/monitor UP/DOWN paths still bypass
this ownership model, so no production driver binding was made.
Audited all five actual `VIRTUAL_IF_UP/DOWN` caller families and the shared
dispatcher in isolated v8. The legacy dispatcher increments/decrements
`VirtualIfCnt` outside the common owner lock; void DOWN discards physical
close failure. Registry attachment alone leaves those legacy opens IDLE.
Documented per-family migration order and failure semantics in
`docs/evidence/WR1200JS-IOT-VIRTUAL-REF-CALLERS-2026-10-25.md`. Do not bind
main-stop gate until every family shares the count/ref owner.
Prepared the first host-only main `ra0` open claim: exact adapter netdev,
published reserved registry record, current ticket/generation/epoch, and
zero count for START versus positive count for MAIN_OPEN. Added a strictly
pre-mutation main-ticket abort. Radio-transition and claim C11 tests pass.
Actual main wrapper/dispatcher remain legacy because first physical open can
fail after partial mutation and needs checked rollback or uncertain ownership
before its module/ref pin can be released safely.
Audited the physical first-open failure path. `RtmpOSIRQRequest` returned
status but `rt28xx_open` ignored it, then initialized the driver as though
IRQ was acquired. Isolated v10 now exits before `RTMP_DRIVER_IRQ_INIT` on
request failure, skips release of an unacquired IRQ, and closes optional
`WIFI_DIAG` on both error paths. Python parse, five-family source gate and
source structure check passed. No target compile or on-device test; partial
`rt28xx_init` cleanup still does not prove hardware quiescence. See the
2026-10-25 virtual-ref audit evidence.

Closed an isolated MBSS abort-failure reuse gap. `MBSS_ABORT_OPEN` can return
failure in vendor dispatch; v4 now maps that post-mutation failure to
`WR_REF_UNCERTAIN_OPEN`, keeps its module pin, and blocks reopen/unregister.
Reference/registry strict C11 checks and the five-family source gate passed.
No recovery worker, target compile or production integration yet; an
uncertain record remains intentionally unavailable pending observed cleanup.

Closed isolated claimed-UP replay: `virtual_up_stage` is reset with each
radio ticket and set atomically with the claimed count increment. A host
fixture extracted from v4 `cmm_cfg.c` passed strict C11 for one increment,
replay, wrong device and partial claim. Auxiliary/radio/registry/DOWN fixtures
and the five-family source gate also passed. No target MIPS compile or
production DOWN/wrapper binding yet.

Prepared isolated MBSS claim-through-ABI candidate
`.iot-local-check/virtual-open-claim-v4-20261025`. Its outer MBSS ticket and
registration generation reach `cmm_cfg.c`; the claimed branch validates and
increments the count under the common lock before beacon refresh. Reproducer
`tools/iot/prepare-virtual-open-claim-candidate.py` passed, as did the host
claim fixture and five-family source gate on the identity and v3 candidates.
The v4 preparer overlays current transition/registry/checked-close/DOWN
fragments; v3 carried older copies and is superseded. No MIPS compile,
production binding or router test. Earlier v1/v2 scratch copies are
incomplete; the executor rejected their removal.

Added isolated `virtual-open-claim.h` and strict C11 fixture. The common
dispatcher can accept one wrapper-owned open ticket only when device,
generation, operation, serial, epoch and reserved record match; stale/reused
identity and reset/main-down intent fail. This closes a model-level admission
gap without double reservation. Test passed on 2026-10-25. No vendor request
ABI/dispatcher binding, count mutation or target build is claimed.

Source-backed integration conflict: isolated MBSS already reserves the radio
ticket and registry record before `MBSS_OPEN` then `VIRTUAL_IF_UP`. Giving the
common dispatcher a second independent open ticket would self-conflict after
family-specific mutation. The contract now requires one ticket shared from
wrapper preflight through dispatcher count/physical open and checked finish,
with device plus registration generation validation. No production edit.

Consumer source audit on the isolated five-family identity candidate:
`common/cmm_cfg.c` still ignores `RT_CMD_INF_UP_DOWN.if_dev`, changes the
global `VirtualIfCnt`, opens/closes via `pAd->net_dev`, and drops the final
close result. AP-client/monitor ignore their post-UP specific-open return;
AP-client, WDS and monitor release wrapper resources before void DOWN.
Recorded the owner-generation and rollback requirements in the IoT contract.
No production integration or target/device verification is claimed.

Checked main-interface DOWN racing with isolated `AUX_START`. Late success
remains `UNVERIFIED` with `main_inhibited`; another auxiliary open is refused.
`check-aux-radio.c` passed under strict C11 on 2026-10-25. Production caller
ownership and vendor serialization remain open.

Fixed an isolated AUX reset race: a late successful `AUX_START`/`AUX_OPEN`
completion after reset intent now enters `UNVERIFIED`, preserving
`reset_pending`, rather than republishing `READY`. Strict C11 auxiliary and
radio-transition fixtures passed. No target integration or router action.

Corrected auxiliary first-open policy after deeper source review: MBSS, WDS,
AP-client and monitor initializers each guard against redundant creation.
Removed the overbroad zero-count ban. The isolated owner now chooses
`AUX_START` at zero count, allowing physical radio readiness while keeping
main-interface readiness false; later `MAIN_OPEN` promotes main readiness.
Strict C11 auxiliary and existing radio fixtures passed. Production wrappers
remain unbound and full teardown/reinit idempotence needs target proof.

Added distinct host-model AUX_OPEN/AUX_CLOSE tickets for AP-client, WDS and
monitor. They use the existing exclusive radio owner/reset fence, preserve
selective-close phase and classify the final reference as physical CLOSE.
Strict C11 auxiliary, existing transition and virtual-DOWN fixtures passed.
The vendor wrappers are not yet bound; first-open policy and target evidence
remain open.

Audited DOWN failure semantics across the five family wrappers and common
dispatcher. All legacy close wrappers return success after `VOID`
`VIRTUAL_IF_DOWN`; the dispatcher decrements `VirtualIfCnt` before the
last physical close and ignores its return. A return-type-only change would
not preserve resources because earlier teardown has already run. Contract
records the per-family order and required shared owner/uncertain retry.

Follow-up source gate now checks all five checked-netdev registration paths
in addition to ten virtual UP/DOWN calls. It passed against both the staged
source and isolated identity candidate. Source audit proves only MBSS has
reference reserve/finish/close/consume transitions; main, AP-client, WDS and
monitor need owner binding before common DOWN accounting can be safe.

IoT continuation after source-base check: isolated candidate
`.iot-local-check/virtual-if-identity-v2-20261024` now carries caller `netdev`
through the private virtual UP/DOWN request for all five caller families.
`tools/iot/prepare-virtual-if-identity-candidate.py` reproduces the transform;
the five-family source gate and strict C11 main open/close fixtures passed.
The request consumer still ignores this field. Shared ownership, generation,
failure propagation, target build and device tests remain open; production
driver and router were not changed.

Follow-up verification: added `tools/zapret2/verify-source-base.py` so every
agent can check the pinned snapshot offline. It passed for all 253 files
(2,516,830 bytes) on 2026-10-24. The pinned upstream commit exists on GitHub
and includes the `nfqws2: fix UAF` change. This is source integrity evidence,
not a target build or runtime acceptance.

Reviewed bol-van's GitHub repositories for the Zapret2 port. Imported the
complete `bol-van/zapret2` source tree at upstream commit
`4a33055448ce5f4e7acc704e1fbe0d8a8a6aa08d` into
`third_party/bol-van/zapret2/` (253 files, 2,516,830 source bytes). Recorded
archive SHA-256 and per-file SHA-256 in
`third_party/bol-van/zapret2-source-manifest.json`; archive, manifest and
working files matched byte-for-byte. Component selection, dependencies,
licensing and excluded companion repositories are in
`docs/ZAPRET2-SOURCE-BASE.md`. Stage 2 integration is still open: target
libraries/kernel NFQUEUE, service/firewall lifecycle, WebUI, image size and
device behavior remain unverified. No firmware build, selector enablement,
router change, commit or GitHub publication in this source-base step.

## Zapret scope corrected — 2026-10-24

Owner decision: only Zapret2 remains in Stage 2. Removed the old
`CONFIG_FIRMWARE_INCLUDE_ZAPRET` selector (the user's Zapret 1) from WR1200JS
and Mi Mini board configs and the WebUI config inventory. The exact spelling
`CONFIG_FIRMWARE_INCLUDE_ZAPRET1` was not present. Updated delivery scope;
earlier notes planning both variants are superseded. Zapret2 stays deferred
and unchanged; no build or router operation in this step.

## Zapret2 source base committed — 2026-10-25

Pinned `bol-van/zapret2` commit `4a33055448ce5f4e7acc704e1fbe0d8a8a6aa08d`
is now Git-tracked locally in commit `9e56bc6`, together with the SHA-256
manifest, offline verifier, and source inventory. `python
tools/zapret2/verify-source-base.py` passed for all 253 files (2,516,830
bytes) after the commit. Only these 256 base files were committed; existing
unrelated working-tree changes remain untouched. GitHub publication and
Stage 2 firmware integration remain open. No router or build change.

## IoT main-open failure ownership — 2026-10-25

Source review located mutation before the main virtual-UP call:
`RTMP_DRIVER_AP_MAIN_OPEN` precedes `rt28xx_open`, which can fail at IRQ or
within `rt28xx_init` after partial adapter changes. Added the host-only
three-way main-open outcome to `tools/iot/interface-reference.h`: success
owns the reference, pre-mutation refusal releases it, and any post-mutation
failure retains `UNCERTAIN_OPEN` plus the module pin. Strict C11 fixture and
`git diff --check` passed. The isolated vendor wrapper is still unbound and
still needs checked recovery; no firmware build or router change.
Follow-up: added `wr_iot_main_open_reserve` for one-lock ticket plus published
`ra0` record reservation. Strict C11 check passed. Rebuilt isolated candidate
`.iot-local-check/virtual-open-claim-v11-20261025`; the five-family source
gate and C11 check against its overlaid header passed. The vendor main wrapper
and common dispatcher still do not use this helper, so the production gap
remains. No MIPS build or device action.
Next isolated source step: `tools/iot/prepare-main-open-owner-candidate.py`
generated `.iot-local-check/main-open-owner-v12-20261025` with a main
reservation before `AP_MAIN_OPEN` and a claimed START/MAIN_OPEN dispatcher.
The five-family source gate passed on v11 and v12; Python syntax check and
`git diff --check` passed. Do not package v12: main close and the other
three legacy auxiliary count writers remain unsynchronized, and no checked
recovery exists for post-mutation open failure. No target compilation or
router action occurred.

IoT main-stop correction: the host gate previously checked registry-count
equality before latching main-down. A RESERVED secondary record could make
the gate fail while an already admitted open proceeded. It now latches
main-down once after confirming the owned main record, then checks count and
claims the stop ticket. Repeated mismatch/busy tests and strict C11 radio
transition checks passed. This is not wired to the vendor close wrapper;
no target build or device change.

Linux v4.4 source audit closed the main-stop return-value question:
`__dev_close_many` holds RTNL, ignores `ndo_stop` return and clears `IFF_UP`.
Added `wr_iot_main_stop_complete` host model: failed/unverified close keeps
the main record CLOSING and module pin; successful last close requires
checked DOWN plus physical verification before release. Strict C11 fixture
passed. Evidence: `docs/evidence/WR1200JS-IOT-NDO-STOP-RTNL-2026-10-25.md`.
No vendor binding, MIPS build or router action.

Follow-up source trace of the isolated v12 ticket producers: main and MBSS
open hooks run as `ndo_open` under RTNL; admitted reset holds RTNL through
retirement. Evidence and exact paths are in
`docs/evidence/WR1200JS-IOT-TICKET-RTNL-CONTEXT-2026-10-25.md`. Main
`ndo_stop` must not gain a direct ticket wait without proof of an
RTNL-independent completion path. A deferred owner that survives worker
failure/suspend/removal is still missing. No code binding or device change.
Added host `wr_iot_main_stop_request` to classify invalid ownership, busy
ticket with serial, unmatched state needing recovery, or admitted stop. The
strict C11 fixture passed. This removes ambiguity from the future ndo_stop
handoff but does not schedule work or prove adapter lifetime; production
driver remains unchanged.

PCI remove audit found a concrete adapter use-after-free risk for any future
deferred IoT owner: `rt_pci_remove` ignores `RtmpPhyNetDevExit` failure and
then frees the adapter through `RtmpRaDevCtrlExit`. Added a host-only
adapter-release predicate requiring terminal child/radio/reference and
deferred-worker quiescence; strict C11 test passed. See
`docs/evidence/WR1200JS-IOT-PCI-REMOVE-DEFERRED-OWNER-2026-10-25.md`.
No PCI binding, MIPS build or device operation.

AP-client source trace (2026-10-25): `ApCli_VirtualIF_Open` ignores the
`APC_OPEN` ioctl result, although `ApCli_Open` can return failure after
`VIRTUAL_IF_UP`; its close path also ignores `APC_CLOSE` and virtual-DOWN.
See `docs/evidence/WR1200JS-IOT-APCLI-OPEN-RESULT-2026-10-25.md`.
AP-client must join the same checked radio/reference owner before production
IoT binding. No driver, image or router change in this trace.
Added the host-only `wr_iot_aux_open_reserve` atomic ticket/record admission
for AP-client/WDS/monitor. Strict C11 `check-virtual-open-claim` passed;
actual family wrappers, checked APC_OPEN/CLOSE and vendor count dispatcher
remain open.
Host-only auxiliary result policy now distinguishes unmutated refusal,
acquired required-call success and uncertain partial/failed OPEN. Strict C11
`check-interface-reference` passed. `ApCli_Open` can invoke packet-forwarding
probe before device matching, so a failed APC_OPEN is not presumed clean.
WDS has no family OPEN; the host result policy now accepts checked virtual-UP
as its acquisition. Monitor ignores SNIFF_OPEN status, and Monitor_Open returns
TRUE even on a mismatched netdev. Source evidence is in the APCLI open report.
Prepared a source-pinned isolated `Monitor_Open` identity correction and
executed its extracted C function for matching and mismatched netdevs.
Both cases passed; diff changes only the two return lines. The wrapper still
ignores SNIFF_OPEN status, and no production driver/image/router was changed.
Host registry/attach model now tags MAIN, MBSS, APCLI, WDS and MONITOR at
registration and rejects unknown hook flags. AUX ticket reservation refuses
a mismatched family. Strict C11 registration, registry and open-claim fixtures
passed. The copied driver dispatcher must still recheck family before its
count mutation; this host work is not a production binding.
Host AUX dispatcher predicate now rechecks family, exact ticket and the
zero/nonzero vendor-count split before count mutation; strict C11 claimed-open
fixture passed. Source trace of `rt28xx_open` shows first-open side effects
before a possible error, so AUX_START physical failure still needs a retained
recovery owner. Do not bind a decrement-only rollback into the copied driver.

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

## IoT WDS close candidate v31 — 2026-10-25

Isolated non-last WDS `ndo_stop` now binds AUX_CLOSE admission to checked
DOWN and releases its reference/pin only on success. Extracted-wrapper host
tests pass success, failed DOWN retention and last-close refusal; caller
coverage passes v30 and v31. No recovery worker, target compile, image or
device verification. Keep v31 out of production until those gaps close.
Evidence: `docs/evidence/WR1200JS-IOT-AUX-CLOSE-ADMISSION-2026-10-25.md`.

## IoT PCI remove path audit — 2026-10-25

The pinned v33 driver still discards AP-client, WDS and monitor removal
results. Their `VOID` remove functions can skip a failed `mark_removing`, while
`rt_pci_remove` ignores even the checked MBSS failure and continues to
`RTMPFreeAdapter`. Source inspection established that all four child-family
outcomes and main-netdev/callback quiescence must be owned before adapter
release. The separate probe-error `RTMPFreeAdapter` path also needs a partial
initialization audit. No production driver, image or router change was made.
Evidence and binding order: `docs/evidence/WR1200JS-IOT-PCI-REMOVE-DEFERRED-OWNER-2026-10-25.md`.

An isolated v35 WDS candidate now propagates a skipped removal as failure
through the ioctl wrapper to `RtmpPhyNetDevExit`; Python syntax and source
chain assertions passed. It is not packaged or target-compiled. PCI remove
still ignores the parent result, so adapter release remains unsafe.
Isolated v36 extends checked-result propagation to AP-client and monitor;
source-chain and byte-diff checks passed. All three still lack joined
close/recovery and callback/registry release proof. Keep v36 out of image.
Source audit confirmed `mark_removing` is admission only. Isolated v37 adds
a post-detach/pre-free `WR_REF_IDLE` gate for all three families, retaining
their netdev pointer after incomplete close. Source-order and changed-file
checks passed, but later OS-helper inspection invalidated that ordering:
detach already frees `netdev_ops`. Isolated v38 moves explicit close and the
phase gate before unregister under RTNL, leaving a failed-close netdev
registered. Source order and changed-file checks passed. Worker join,
lock-order proof, registry/callback quiescence and PCI release are still open.
Keep v37/v38 out of image.
Pinned Padavan 4.4.198 source semantics add a further v38 blocker: `dev_close`
clears `IFF_UP` after one `ndo_stop` call regardless of driver result, so
calling it again cannot retry failed AUX_CLOSE. The retained WDS continuation
must be scheduled by an adapter-fenced worker; AP-client/monitor need their
own continuations. The checked-in IMQ modifications do not touch this close
path; final generated build-tree comparison is still pending.
Host deferred-owner model now routes exact WDS close stages to direct
same-ticket retry or post-DOWN completion, never through `dev_close`; strict
C11 fixture passed, including wrong-family refusal. No kernel worker, target
driver or release fence is bound.
AP-client and monitor close wrappers execute family-specific APC_CLOSE or
SNIFF_CLOSE before virtual DOWN and discard their results. The WDS recovery
owner now refuses both families at admission; strict C11 checks passed.
Their own checked family-close/partial-side-effect continuations remain open.
Host-only AP-client/monitor close-stage model now distinguishes uncertain
family ioctl, confirmed family close, retryable unmutated DOWN failure and
verified DOWN. Strict C11 fixture passed. Vendor wrapper and recovery owner
are not yet bound; uncertain ioctl side effects still need reconciliation.

## Zapret2 source published; integration handed to DeepSeek — 2026-10-25

GitHub branch `codex/wr1200js-service-webui` now points to `df2605a`.
Pinned Zapret2 source and documentation are in `9e56bc6` and `df2605a`.
`tools/zapret2/verify-source-base.py` passed: 253 files, 2,516,830 bytes,
upstream `4a33055448ce5f4e7acc704e1fbe0d8a8a6aa08d`. Five preceding
IoT commits were in the same branch push. Existing uncommitted work remains
local. No Zapret2 production integration, firmware build, image validation,
or router test has been performed. User assigned DeepSeek the next integration
work; observe the single-writer handoff in `docs/EXECUTION-ROLE.md`.

## Handoff to Sol; IoT first, then Zapret2/WebUI verification — 2026-10-25

The owner explicitly transferred the single-writer role to Sol. The root agent
stopped editing after recording this handoff. Sol must first finish IoT and only
then verify the Zapret2 and Modern WebUI work.

Current branch and remote HEAD are `28b0faf3c6b463d02f273f9f627b192406ac7f91`.
`origin/main` remains `d1dc0ebaf82af316ad8ba65a01952c229c69e919`; PR #2 is open
and mergeable. Zapret2 candidate run `40189818250` passed on this HEAD.
Firmware build #584, run `40189820727`, was still in progress at the handoff.

Zapret2 now includes the enabled build selector, `nfqws2`, the explicit
fail-open service, three Lua files and MIT notice, Classic Services control,
separate process/rule/strategy observations, firewall reapply and EN/UK/RU
labels. Modern preview now follows the supplied two-column dashboard reference,
preserves six hashed design PNGs, and maps fourteen service tiles to real
Classic routes.

Builds #582 and #583 compiled the firmware but failed only on verifier defects:
wrong dictionary path and a stripped-symbol expectation. Both were corrected.
No completed final image or TRX containing the complete Zapret2 service/WebUI
has yet been independently accepted. The router was not flashed or rebooted;
the read-only SSH identity check timed out, so runtime remains unverified.

Sol's required order is: claim the role, preserve the existing 32 tracked and
147 untracked working-tree entries, finish the IoT open/close/reset/recovery/
PCI-remove lifecycle and target acceptance, then verify build #584 or its
replacement, ROMFS/TRX/SHA256, and only afterward a separately authorized
runtime test.

Detailed handoff:
`docs/evidence/WR1200JS-HANDOFF-TO-SOL-2026-10-25.md`.

## IoT guest-to-IoT open receipt — local host check, 2026-10-25

Added `wr_iot_bss_open_finish_observed` to the isolated open-claim contract.
It can publish READY after a successful guest/IoT BSS open only when the
post-open readback, published MBSS owner, complete vendor reference count and
current BSS_OPEN ticket agree under the common lock. Failed evidence leaves
the reference owned and readiness UNVERIFIED for checked close/recovery.
The strict MinGW C11 fixture passed success, count mismatch, wrong family,
failed readback and intervening reset; `git diff --check` passed. This helper
does not prove RF beacon emission. The local legacy candidate assembler now
copies the helper and its MBSS wrapper observes guest/IoT BSS configuration
outside the transition lock, then checks the owned count and retires the same
ticket under that lock. A separate strict C11 wrapper fixture passed guest
then IoT, failed readback, count mismatch and reset-during-receipt. This
binding was then ported to the v40 **assembler**, preserving its claimed raw
open and all three ticket-retirement wakeups. The assembler also checks the
`CR_ENABLE` result and copies the corrected observer and open-claim headers.
It produced the separate local v40f tree. The generated v40f MBSS wrapper
passed the strict C11 guest-to-IoT fixture; checked CR_ENABLE, five-family
caller coverage and eight remove-result pairs passed. Only the expected eight
candidate paths differ from reviewed v39, and PyYAML parsed the CI workflow.
The optional v40 CI path now requires that host fixture before target compile.
This local v40f output is not a MIPS build or packaged image; CI #600 predates
the edit. Next: target-compile the newly generated v40 candidate, then resolve
close/recovery ownership before production integration.
The v40 host fixture now selects generated candidate headers before local
headers; it passed again with that exact include order. The first workflow
form would have allowed local header shadowing, so only the corrected run is
counted as candidate-header evidence.
The v40 assembler now pins the reviewed v39 MBSS fragment before replacing
it, so later upstream changes fail closed instead of being silently lost.
Fresh local v40g assembly and its candidate-header guest-to-IoT fixture passed.
Source review then separated two previously conflated MBSS partial opens:
failed abort before confirmed virtual-UP retains UNCERTAIN_OPEN (`-2`), whereas
failed CR_ENABLE after successful claimed virtual-UP retains an OWNED vendor
reference and module pin (`-3`) with radio FAULT. Fresh local v40h assembly,
candidate-header host fixture and generated raw CR_ENABLE fixture passed.
Neither failed ndo_open gets ndo_stop; an adapter-pinned recovery owner is
still mandatory before target image integration.
The isolated MBSS checked-close admission now requires a matching MBSS
record and complete registry/vendor count under the common lock before it
chooses a stop ticket. Local v40i assembly and candidate-header close fixture
passed refusal for a missing main owner plus the existing retry cases. The
optional v40 CI path has that fixture gate. Legacy count-writer bypasses,
unbound close/recovery and PCI lifetime still block production integration.

The isolated v40j assembler now closes the unclaimed virtual-UP count-writer
bypass after proving all five active open callers use `VIRTUAL_IF_UP_CLAIM`.
Fresh v40j assembly and focused host fixtures passed. Legacy virtual-DOWN
still decrements outside the common lock; checked close/recovery, PCI fence,
target compile/image and router acceptance remain open. Evidence:
`docs/evidence/WR1200JS-IOT-V40-CI-600-TARGET-COMPILE-2026-10-25.md`.

The v40j DOWN audit found four legacy void stop callers (main, MBSS,
AP-client, monitor); WDS already uses checked DOWN. APC_CLOSE and
SNIFF_CLOSE return results that their callers discard, after potentially
mutating family state. A lock around the legacy decrement is insufficient:
bind retained close owners and result stages first, then retire the old
callers and reject unclaimed DOWN. Source locations and order are in the v40
evidence note. No production driver or router change was made.
The v40 assembler now gates this exact four-caller inventory; fresh isolated
v40k assembly passed. The gate must be updated deliberately as callers move
to checked owner-aware DOWN.
The MBSS checked-close helper now retires its exact radio ticket and consumes
the registry reference atomically after checked DOWN; before this correction
it left the radio busy after releasing the module pin. Fresh local v40l
assembly and strict C11 local/generated-header fixtures passed, including
ticket-retirement failure. `ndo_stop`, retained recovery and target/runtime
binding are still absent. See the v40 evidence note.
Added a separate host-only MBSS recovery owner for acquired failed-open,
retained checked-close and uncertain outcomes. Its strict C11 fixture passed
and the optional v40 CI path now runs it. It cannot release its netdev/adapter
fence before checked completion and worker join; uncertain outcomes do not
automatically replay DOWN. Kernel workqueue, lifetime pins, PCI release
binding and target/runtime verification remain open. Evidence: v40 note.
Pre-CI source coverage initially rejected v40l because the older checker
expected one uncertain MBSS handoff and three wakeups. It now distinguishes
the acquired post-UP `-3` branch from uncertain `-2`, requires both owner
paths and four wakeups for v40, and keeps v39 compatibility. Both pinned v39
and generated v40l passed. Target compilation of these local changes remains
open. See the v40 evidence note.
Selected v40 IoT source/tests/workflow changes were committed as `eefbf12`
and pushed to PR #2; other dirty files remain untouched. Ordinary firmware
run `40257333149` queued and ABI run `40257333066` started on this HEAD.
Neither selects the optional v40 overlay. A duplicate candidate dispatch was
deferred under CI queue discipline. See the v40 evidence note.
ABI run `40257333066` completed successfully on `eefbf12` (GitHub Actions
status/conclusion checked 2026-10-26). Ordinary firmware run `40257333149`
was still in progress with its board build job running. Neither result is a
v40 target compile or IoT runtime acceptance; dispatch one optional v40
candidate run only after the ordinary run is terminal and no equivalent run
exists for this HEAD.
Ordinary firmware #603 (`40257333149`) completed successfully on `eefbf12`,
including the WR1200JS build and ZIP jobs. After confirming no equivalent
v40 dispatch existed, started exactly one manual run `40260205702` for
`wr1200js`, `run_candidate_checks=true`, `iot_candidate_variant=v40` on the
same HEAD. It was in progress at first check; its target compile result and
any image/runtime claims remain pending.
Manual v40 run `40260205702` then completed successfully. Its isolated
candidate step produced a MIPS32r2 `mt76x3_ap.ko` and compiled main-observer
probe. The source manifest is pre-build and still says `target_compiled:false`;
the job result, build log and module prove isolated target compilation only.
Production integration, image inclusion and router runtime remain open. See
the v40 evidence note for artifact hash and limits.
The IoT workflow was locally updated to emit a post-build target result JSON
after ELF/config checks; an extracted block passed against the downloaded
v40 module, and YAML parsed. This new reporting step has not run in CI yet.
The same local module contains the v40 checked MBSS begin/close and virtual
DOWN symbols. A new CI symbol gate guards their presence; local readelf and
YAML checks passed. The actual `MBSS_VirtualIF_Close` remains legacy and
does not yet call that checked path, so this is compilation evidence only.
Local MBSS checked-close follow-up now pins the original reference token
across unlocked vendor calls and preflights reference consumption before
radio-ticket retirement. A C11 fixture with a changed nonzero token after
DOWN passed, retaining ticket and module pin. This edit needs target compile
and still is not bound to production `ndo_stop`.
The focused workflow/MBSS close/fixture changes were committed as `b2dce05`
and pushed to PR #2. Fresh isolated v40m assembly, generated-header C11
fixture and virtual-interface caller coverage passed locally. Unrelated
modified/untracked files remain in the shared checkout. Verify the new
ordinary CI run before one optional v40 target run on `b2dce05`.
Further local MBSS close review found missing post-DOWN vendor-count
revalidation. The helper now requires the count to equal other stable OWNED
registry records before ticket retirement; an injected extra count writer
retains the ticket/pin. Local and fresh v40n generated-header C11 fixtures
passed. This follow-up is uncommitted and awaits target compilation.
Build #605 (`40262929363`) and ABI run `40262929407` succeeded on
`b2dce05`. The post-DOWN count follow-up was then committed and pushed as
`3041f7f`, without staging unrelated dirty files. GitHub started ordinary
build #606 (`40264642881`) and ABI run `40264642807`; they were queued/
running at first check. Because #605 did not include this count fix, defer
the optional v40 target dispatch until #606 is terminal and confirm no
equivalent run already exists on `3041f7f`.
Build #606 and ABI completed successfully on `3041f7f`. A single manual
v40 candidate run `40265901025` was started on that exact HEAD. The MBSS
unregister/free source path was rechecked: it frees the netdev immediately
after unregister, while Linux ignores `ndo_stop` failure. The retained owner
must therefore be joined/reconciled before free and PCI adapter release;
this binding is not implemented. See the PCI-remove evidence note.
Manual v40 run `40265901025` completed successfully on `3041f7f`.
Downloaded `iot-merged-driver-probe` to `artifacts-607-v40/` and verified
`target-compile-result.json`: isolated MIPS module 5,207,716 bytes, SHA-256
`13ac9ac57450324e3763e24e8fe75fc3a479889db33aacd8f42f4705e774383f`,
matching the file hash. Required checked-close/down symbols are present.
The report explicitly says production-installed and runtime-verified are
false. Next implement retained owner join before MBSS netdev free and PCI
adapter release, then bind checked close; no router change was made.
Local MBSS removal provenance gate: `interface-reference.h` now records a
caller-proven unmutated open failure separately from an acquired reference.
`wr_iot_mbss_begin_remove` refuses an idle record with a previous token
unless it has that unmutated proof or checked-close stage 4. The v40
generator applies these changes to its pinned v39 copy explicitly. Strict
C11 local and freshly generated v40p registration/reference fixtures passed;
Python syntax, source caller coverage, MT7603 stop check and diff check
passed. This is not target-compiled, bound recovery, or router evidence.
The focused v40 generator/provenance-header/two host-fixture/workflow change
was committed and pushed as `f708bcb`. The large pre-existing local changes
in `tools/iot/netdev-registration.inc` and other dirty files were not staged.
The workflow will run the reference and registration C11 fixtures against
the generated v40 headers before its isolated MIPS compile. At first run-list
check after push, no new run for this HEAD was listed; check CI before any
manual candidate dispatch and do not claim target compilation yet.
Subsequent GitHub check found ordinary firmware run `40268551446` queued and
ABI run `40268551314` in progress on `f708bcb`. Reuse those runs; wait for
the ordinary run to become terminal before one optional v40 dispatch.
Ordinary firmware `40268551446` and ABI `40268551314` subsequently
succeeded on `f708bcb`. After confirming no equivalent candidate run existed,
dispatched exactly one optional v40 run `40330460110` on the same HEAD; its
WR1200JS build job was in progress at first check. Do not duplicate it.
Source recheck of the generated candidate confirms PCI remove still ignores
`RtmpPhyNetDevExit` failure and frees the adapter; the new MBSS provenance
gate does not solve that release hazard or bind checked `ndo_stop`.
Optional v40 run `40330460110` succeeded on `f708bcb`. The downloaded
isolated MIPS module is 5,207,896 bytes, SHA-256
`4088c6f3d2e5eeacddba2708eaee5c81159530558dba61518ca20ec0b13ece52`;
its hash matches `target-compile-result.json`. Candidate manifest hashes for
the updated interface reference and netdev registration files match fresh
v40p generation. The report explicitly keeps production-installed and
runtime-verified false. Next: bind checked close with a retained recovery
owner and adapter-release fence before any production inclusion.

## IoT PCI reset fallback audit — 2026-10-27

Continued the pinned Linux 4.4 source audit. Generic function reset APIs exist, but their fallback chain can reach parent-bus reset; the PCIe FLR path proceeds even after pending-transaction timeout and requires full PCI device reinitialization. No evidence yet confirms FLR/AF-FLR/PM-reset capability on this live MT7603 endpoint, and MT7621 config access does not provide checked completion/readback. Therefore no reset API is safe to bind as a generic terminal fallback. v43 remains isolated; failed radio shutdown must not proceed to DMA/MMIO/adapter free.

Next: collect the router's read-only PCI config/capability snapshot using the fixed `wr1200js-readonly.ps1 -Check pci` check, then verify whether the endpoint advertises an isolated reset and what device/board reinitialization would require. If the fixed check lacks capability detail, extend the read-only evidence path only after reviewing its allowlisted command; no arbitrary SSH command. No router state, driver, image or build was changed here.

Correction to the prior next-step wording: the existing `-Check pci` only reads `/proc/bus/pci/devices`, which identifies devices but does not expose PCI capability structures. I added a separate fixed allowlisted `pci-config` check to `tools/wr1200js-readonly.ps1`; it reads the first 256 bytes from each readable `/sys/bus/pci/devices/*/config` file using `od` and cannot accept arbitrary remote commands. Use `-Check pci-config` to collect capability bytes. This has not been run on the router; the router's support for that sysfs path and BusyBox `od` remains to be observed.

### IoT v43 main-readiness integration gap — 2026-10-27

New source audit of isolated v43c: MBSS/IoT open correctly requires `WR_RADIO_READY && main_ready` and performs a main-BSS beacon/queue-register observation before BSS open. However `MainVirtualIF_open()` ends with `wr_iot_radio_finish_unverified()`, which leaves readiness false, and no candidate call site invokes the existing `WR_RADIO_VERIFY`/`wr_iot_main_radio_verify_owned()` helper. Therefore the candidate has no demonstrated path to authorize IoT BSS_UP; it will fail closed. This is not production integration and no build/device test was performed.

Next engineering step: add a bounded main-readiness verification producer after main open, with pinned adapter/netdev lifetime, observer outside transition spinlock, and ticket/epoch/generation/vendor-count revalidation under the common lock. Verify invalidation/failure retains recovery ownership. Keep it isolated until the family-close/recovery and PCI adapter-release gates are solved. The separate live PCI capability snapshot is still awaiting user output.


### IoT v44 candidate — main-readiness VERIFY producer — 2026-10-27

Added untracked candidate tooling `tools/iot/prepare-main-readiness-verify-candidate.py` and `tools/iot/check-main-readiness-verify-candidate.py`; generated source and manifest remain isolated at `.iot-local-check/mt7603-main-readiness-verify-v44-local-20261027`. Focused candidate structure/order checker, existing strict C11 virtual-open claim fixture, Python syntax, and scoped `git diff --check` passed.

The candidate observes main beacon/queue state outside the transition lock, then revalidates VERIFY ticket/generation/ownership before setting readiness, with HNAT and queue enable after verification. It remains **unsafe to integrate**: failed verification returns `ndo_open` error after virtual-UP ownership was claimed, and no recovery owner is bound to drain it. PCI adapter release remains unproven. No MIPS compiler was found in the current Windows environment; no target compile, firmware build, image check, router command, or runtime validation occurred. Next: design and test explicit failed-open owner recovery/join semantics; retain isolation until recovery and PCI release gates pass. The separate live PCI config output is still pending.

CI snapshot at 2026-10-27 17:27Z: firmware #635 (`40538660394`) and ABI (`40538660378`) succeeded on published SHA `84b2f12d2b653057e6806c824e7123757161a191`; monitor run `40543253994` was skipped. These are older than current local HEAD `4d8373e7b5c24c1ef2d551cff266aa141e26df8d` and do not cover local v44 changes. No CI run was started.


## 2026-10-27 read-only PCI reset capability check

Fixed the router helper's `pci-config` allowlisted command: BusyBox lacks `od` but has `hexdump`; the check now reads up to 4096 bytes per PCI config file. SSH read-only collection succeeded. WR1200JS reports MT7603 `14c3:7603` at `0000:01:00.0` and MT7662 `14c3:7662` at `0000:02:00.0`. Both PCIe v2 endpoints have Device Capabilities `0x00008fc0` with FLR clear; neither conventional capability list contains AF-FLR. PMCSR `NO_SOFT_RESET` is clear, so Linux 4.4 PM reset appears eligible for source-level consideration, but is not evidence of safe DMA stop or successful driver recovery. No reset or other state-changing command was run. Exact parse and source limits are in `docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`. Next: assess PM-reset in a complete recovery sequence; keep candidate isolated until transaction/DMA quiescence, recovery-owner join and PCI release are independently proven.

### IoT PM-reset decision — 2026-10-27

Re-read pinned Linux 4.4 source from the exact local bare snapshot
`../firmware-source-backup/padavan-4.4.git` at
`c25283e915a2a00a763774dd255b14aff997285e`. `pci_pm_reset()` only toggles
D3hot→D0 with delays and returns 0 without readback/readiness evidence;
`pci_reset_function()` requires full device reinitialization and can fall back
to slot or parent-bus reset. MT7621 `config_access()` accesses PCR MMIO and
returns `PCIBIOS_SUCCESSFUL` without a separately checked transaction status.
Combined with the live MT7603/MT7662 snapshot (FLR absent, AF capability absent),
PM-reset is not a safe close/remove completion receipt and must not authorize
DMA/MMIO/adapter release. Keep reset out of the release predicate; fail closed
until a device-defined DMA/callback quiescence proof and full reinitialization
owner are established. Evidence: `docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.
No source driver, build, image, router state, or PCI reset was changed/run.
Next: continue the lifecycle owner/recovery design without using PM-reset as a
release signal; leave the candidate isolated until target compile and fault
injection can prove the complete sequence.

## Queued task for Sol — verify target BusyBox hexdump and version — 2026-10-27

The router's BusyBox `hexdump -C -n 4096` successfully produced the PCI config
snapshot through the fixed read-only helper; standalone `od` is unavailable.
This is live-device command evidence only and does not establish the firmware
image's BusyBox version, source revision, effective `.config`, or applet flags.

Queued for Sol within the existing target BusyBox audit, without changing task
order: inspect the exact WR1200JS build's BusyBox version/revision, config,
ROMFS binary SHA256, applet links and `hexdump` options; determine why `od` is
absent; compare against the currently running device; and document whether the
allowlisted PCI dump invocation is valid for that exact image. No router state
change is authorized. The current IoT lifecycle/recovery gate remains ahead of
this audit follow-up.

### IoT failed-main-open recovery source gate — 2026-10-27

Inspected pinned Linux 4.4 `net/core/dev.c` from the exact source snapshot.
`__dev_open()` sets START before `ndo_open`; on error it clears START and skips
the success branch that sets IFF_UP. It does not invoke `ndo_stop`. Therefore
`dev_close()` cannot replay cleanup for a failed `MainVirtualIF_open()`. In
isolated v44, failure after AP main-open either leaves an `UNCERTAIN_OPEN`
record (virtual-UP uncertain) or an `OWNED` record with `main_ready=0` (VERIFY
failure); the manual module pin is intentionally retained, and Linux supplies
no stop callback.

Next implementation gate: introduce a deferred main-open recovery owner that
retains netdev/module/adapter lifetime, runs only after the failed callback
leaves RTNL, validates the exact generation/token and record phase, obtains a
checked main-close ticket, and preserves all ownership on any failed/unverified
physical close. It must join before PCI removal and cannot rely on `dev_close()`
retry or PM-reset success. No recovery owner is yet bound; no driver, build, image
or router was changed. Detailed source correlation is in
`docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.

## 2026-10-27 IoT main-close receipt gate

Main-stop host completion now requires an exact stage-3 checked-DOWN receipt
with matching ticket provenance before it retires the ticket, consumes the
record and marks stage 4. Missing/stale receipt tests plus dependent recovery
fixture pass strict MinGW GCC. The real v44 main close executor and PCI worker
remain unbound. Evidence:
`docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.

## 2026-10-27 IoT v44 main-close prerequisite

Source recheck found the isolated v44 main `ndo_stop` still uses legacy
`VIRTUAL_IF_DOWN` and unconditional module-pin release. The v44 checker passes
only its VERIFY structure; manifest confirms recovery and PCI release are
unbound. Implement a ticketed, staged checked main-close continuation before
binding the failed-open worker. See
`docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.

## 2026-10-27 IoT recovery module-pin ordering

The isolated failed-main-open owner now refuses to release its module pin
before the worker join is confirmed. Host fixture covers early, missing and
duplicate release and passes strict MinGW GCC. Real workqueue, module ref and
PCI remove binding remain open. See
`docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.

## 2026-10-27 IoT recovery retry and PCI stop gate

The isolated failed-main-open owner now has bounded explicit requeue and a
PCI stop request. The host composition test shows an unresolved stopped owner
still blocks child teardown after work join. Strict MinGW GCC fixture passed.
No production workqueue/remove binding or physical close proof exists. See
`docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.

## 2026-10-27 IoT main recovery close-count gate

The isolated failed-main-open recovery owner now rechecks the vendor count
and registry with exactly one `CLOSING` record before continuing a retained
close ticket. Host fixture rejects count/registry drift and passes strict
MinGW GCC. This does not bind a kernel worker or prove physical close. See
`docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.

## 2026-10-27 IoT bridge ownership cross-check

The isolated bridge candidate already rejects a foreign `ra2` master and
rechecks ownership before/after BSS up; its kernel fixture covers this case.
Pinned RC source only attaches main/guest interface macros to LAN, while the
WR1200JS profile reserves `ra0` as main and the `ra` extension prefix. The
exact pinned upstream `netutils.h` maps classic 2.4 GHz main/guest to
`ra0`/`ra1` under this board's `BOARD_2G_AS_WSOC` selection. Source mapping
is confirmed; resolved definitions in the final image remain to be checked.
See `docs/evidence/WR1200JS-IOT-ACTIVATION-GAP-2026-10-21.md`. No production
activation, image or device test was performed.

## 2026-10-27 lekswrt Prometheus donor review

Inspected lekswrt repository at `afaa72a1ac83b2dd0bf6a4f51fe1bf1f5d061295`.
Recorded its interactive build workflow and historical theme references in
`docs/donor-audits/LEKSWRT-PROMETHEUS-2026-10-27.md`; added a bounded WSL 2
candidate to the final offline-build stage of `docs/PROJECT-DELIVERY-SCOPE.md`.
The donor README reports WSL Ubuntu 20.04 build failure, and its scripts have
network downloads and router-write operations. No code was imported, no build
was run, and the WR1200JS -> Mi Mini -> offline stage order is unchanged.

## 2026-10-27 IoT main-close preclose stages

The isolated main-stop contract now records `RTMPInfClose` start and return
before accepting a checked DOWN receipt. This prevents a stage-1 interrupted
void call from being treated as safe to replay. The strict host fixture passed;
the v44 production driver still has its legacy main close path. Next: bind a
checked executor under the shared adapter transition lock, then the deferred
owner and PCI removal gate. Evidence is in
`docs/evidence/WR1200JS-IOT-V43-MBSS-GLOBAL-PREFLIGHT-2026-10-27.md`.
The stage-1 claim now shares a full registry/count predicate with recovery;
both host fixtures reject count or child-phase drift and pass strict GCC.
Source review corrected the binding order: failed main readiness returns from
`ndo_open` with its acquired owner, so kernel `ndo_stop` will not run. Bind
the adapter-pinned deferred recovery worker and join fence before routing
normal close through the shared checked executor. Checked virtual DOWN is
software evidence, not physical quiescence.
The v44 PCI source also ignores `RtmpPhyNetDevExit` failure and proceeds to
`RtmpRaDevCtrlExit`/adapter free. Worker binding must initialize before
netdev publication and join after unregister can no longer queue work, before
all adapter free paths. See the same evidence file; no driver binding yet.
The host PCI retirement gate now requires a second worker join after main
netdev detach and zero deferred owners. PCI retirement and recovery fixtures
passed strict GCC; no actual kernel workqueue is bound.
The deferred-owner pin-release order is corrected: its active callback may
record an actual decrement after checked close, then the external remove
owner must join work before clearing the record. Strict host fixture passed;
the kernel worker is still unbound.
The isolated recovery queue rejects ordinary admission after retirement;
it now permits only the PCI remove owner to queue a pre-existing acquired
main close needed by unregister/`ndo_stop`. Uncertain open is rejected in
this path. Strict host fixture passed. Actual queueing and owner proof must
be atomic with the retirement flag in the production binder.
Fresh pinned-source queue/ACK assembly with that origin gate completed; it
still has no work item or target driver compilation.
The isolated adapter generator now carries initialized main recovery-owner
storage and both owner headers into the full queue/ACK bundle. Fresh pinned
source assembly and generated main-open/close host fixtures passed. No kernel
work item, checked executor, production driver or target compilation yet.
The deferred-owner fixture now composes these same stages with its retained
close ticket and pin-release gate; strict MinGW GCC passed. The executor and
worker remain unbound to the production driver.
2026-10-28 Sol: The retained CLOSE_UNCERTAIN recovery action now checks the
actual vendor reference count and registry cardinality against the exact
recorded close stage before allowing reconciliation. The strict host fixture
rejects mismatched counts before and after virtual DOWN; scoped diff check
passed. This is a host-only gate, not a bound worker or device acceptance.
2026-10-28 Sol: PCI removal source gate now rejects an unrelated nearby `if`
around `RtmpPhyNetDevExit`; it requires the FALSE result itself to guard
adapter release. Synthetic negative/positive checks passed. The current
partial driver still fails this gate and the two work-join/release gates;
therefore no production installation is justified yet.
2026-10-28 Sol: Probe-failure lifetime was checked separately. In the current
PCI source, failed `wr_iot_netdev_attach_checked` reaches `err_out_free_radev`
and calls `RTMPFreeAdapter` directly. Added a source preflight that requires
adapter-owned recovery work and `cancel_work_sync` before that free, while
preserving the existing `pci_set_drvdata(NULL)` cleanup. The present partial
candidate correctly fails both new worker gates. This expands the required
worker binding to probe unwind as well as ordinary PCI remove.
2026-10-28 Sol: Worker binding review found a normal-completion ownership
gap. `wr_iot_main_recovery_complete` requires `work_joined`, but a running
work callback cannot join itself. A callback that merely records success
would leave the owner occupied; resetting it inside the callback could admit
a new schedule before the prior work returns. Before binding the Linux work
item, define and test an external completion/reap handshake that serializes
new queue admission with work completion, and use the PCI remove joins for
retirement. No callback was installed on this evidence alone.
2026-10-28 Sol: Host recovery owner now requires a caller-supplied proof that
the previous work callback was joined before RETAINED may become QUEUED.
Both strict GCC fixtures reject an unjoined retry and pass a joined retry;
the result is still only an ownership contract. The Linux binder must supply
real `flush_work`/`cancel_work_sync` evidence outside the adapter lock and
serialize that receipt with new queue admission. No kernel work item is yet
installed.
2026-10-28 Sol: Added explicit `schedule_work` result handling to the host
main recovery owner. A rejected enqueue moves QUEUED to RETAINED without
dropping the exact ticket or deferred pin; another attempt requires a joined
prior callback. Strict GCC tests for failed-open and failed-close recovery
passed, including rejected submission and subsequent joined retry. The
kernel binder must call this immediately after actual schedule_work under
the same adapter lock. This does not install or execute a Linux work item.
2026-10-28 Sol: Bounded retry accounting now includes rejected work
submissions, rather than counting only callbacks that began. Duplicate
schedule-result recording is rejected and `wr_iot_main_recovery_begin`
requires a recorded accepted submission. The host fixture proves two
rejected submissions exhaust a two-attempt budget on an independent owner;
both strict GCC recovery fixtures pass. Kernel callback binding remains
unimplemented; this is not target or device evidence.
2026-10-28 Sol: Extracted a shared checked main-close continuation into the
partial MT7603 candidate. `MainVirtualIF_close` records the void
`RTMPInfClose` preclose once, then calls that helper; a future deferred worker
can resume stage 2/3 with the exact retained ticket without replaying
preclose. The generated host fixture forced virtual DOWN failure, confirmed
the second `ndo_stop` call does not replay preclose, then resumed the same
ticket and completed the close with one module-pin decrement. Strict GCC
passed on the source fragment and the composed tree. New isolated output
`.iot-local-check/mt7603-main-close-shared-composed-v2-20261028` has 64/64
manifest hashes matching and `production_installed=false`. Recovery queue,
PCI joins, target compile and runtime remain open.
2026-10-28 Sol: Refactored the same partial main-close implementation into
shared ticket admission, fresh-claim preclose, and exact-ticket continuation.
`ndo_stop` uses all three; a deferred acquired-open owner can use these
stages without duplicating close logic. Host extraction checked ordinary
physical/selective close, failed DOWN followed by exact-ticket continuation,
and a separate acquired-open path through all three stages. Strict GCC passed
for source and new composed output
`.iot-local-check/mt7603-main-close-shared-composed-v3-20261028` (64/64
manifest hashes; `production_installed=false`). The one-shot preclose rule
still relies on caller ownership; no Linux worker, automatic queueing,
PCI joins, target compile or runtime proof exists.
2026-10-28 Sol: Main close now records `close_running=1` under the shared
adapter lock immediately before the void `RTMPInfClose`; the returned
milestone clears it and advances stage 1 to stage 2. A second claim of the
void preclose is rejected, including after failed checked DOWN. The shared
`close_running` field already existed in the interface record, so no extra
layout field was added. Three strict GCC host fixtures passed. The new
isolated `mt7603-main-close-oneshot-composed-v4-20261028` bundle copies the
reviewed close-owner header, passes its extracted close fixture and matches
64/64 file hashes. `production_installed=false`; worker, PCI release and
target/runtime gates remain open.
2026-10-28 Sol: Added a checked deferred main recovery executor to the
partial MT7603 source. It consumes an accepted owner, validates the current
record and radio count under the shared lock, either begins a fresh close or
continues the exact retained ticket, and records completion before releasing
the module pin. Stage-1 uncertain preclose is kept for reconciliation, never
replayed. Host extraction covered a failed `ndo_stop` followed by a failed
worker attempt, joined retry and successful exact-ticket close, plus a
separate acquired-open worker path. Strict GCC passed. The v6 isolated bundle
matches 64/64 hashes and remains `production_installed=false`: no actual
Linux work item, queue submission, external reap or PCI joins are bound.
2026-10-28 Sol: Staged the adapter-owned Linux `work_struct`, initialized it
before adapter publication, connected its callback to the checked deferred
executor, and joined it on the PCI probe attach-failure path before netdev and
adapter free. New isolated v7 bundle passes the probe-unwind source preflight,
Python syntax and 64/64 manifest hashes; `production_installed=false`.
This is partial: no actual failure-path queue submission, netdev lifetime pin,
normal external reap, or PCI remove join/release proof is bound. The PCI
remove source gate still reports three open findings. No target compile,
firmware image or router test was performed for v7.
2026-10-28 Sol: Isolated v8b PCI candidate checks the actual
`RtmpPhyNetDevExit` result before adapter free. Failed detach now returns
without releasing live adapter/CSR memory. The source release gate cleared
its fallible-detach finding; two findings remain: ordered first/final work
joins and release claim, plus a synchronous join in PCI remove. A v8 draft
with a diagnostic between the check and `return` was not accepted by the
conservative gate; v8b uses a direct guarded return. Probe-unwind preflight,
Python syntax and 64/64 manifest hashes passed. No target compile, firmware
image or router test was run; a partial detach may retain resources.
2026-10-28 Sol: Isolated v9 PCI candidate fences ordinary admissions under
the shared radio lock, requests main recovery stop, then joins the work item
outside the lock before root detach. Because unregister may invoke `ndo_stop`,
it joins again after successful root detach. Both joins reject adapter free
while a deferred owner remains. Probe-unwind preflight, Python syntax and
64/64 manifest hashes passed. The PCI remove source gate now has one open
finding: child/main detach, final join, release claim and physical/callback
quiescence are not yet proven as a complete ordered release path. A retained
owner currently keeps resources rather than providing recovery/reap. This is
still a nonproduction partial candidate; no target compile or router test.
The PCI remove source preflight now requires two exact main-work joins, one
on each side of root detach. It reports the missing joins in v8b and only
the remaining ordered release claim in v9; Python syntax and scoped diff
checks passed. This is a source-order check, not execution proof.
2026-10-28 Sol: Isolated v10 MT7603 candidate binds the existing bounded PCI
transaction observer to actual `pci_clear_master`, config-word reads and
`msleep`. It runs only after the staged checked physical-stop milestones,
rejects missing PCIe capability, failed reads, active bus master or pending
transactions, and rechecks the radio epoch before adapter release. The
observer's strict GCC fault fixture passed; probe-unwind source preflight and
65/65 manifest hashes passed. PCI remove source preflight still has the
ordered release-claim finding. The config observation is a necessary check,
not proof of DMA/ring/IRQ or callback quiescence; no target compile, firmware
image or router run was performed and `production_installed=false`.

2026-10-29 overlay correction: older manifest marks four required include/*.inc
as fixtures. Initial scratch output omitted them; superseded by overlay2.
Generator now excludes only seven root test fragments and applies all 64
driver files, including those four required include fragments. Verified present.
