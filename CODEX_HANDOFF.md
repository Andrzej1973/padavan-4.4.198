# Current handoff — 2026-10-25

Sol is the single writer. Read `AGENTS.md`, `PROJECT_STATUS.md`,
`docs/AGENT-BOOTSTRAP.md`, `docs/EXECUTION-ROLE.md` and `git status -sb`
before changing files. Preserve every unrelated local modification.

1. Branch HEAD `3d6c602` is pushed. Firmware #594 (`40205825840`), Band
   Steering ABI `40205825793`, and optional isolated IoT build #595
   (`40207139904`) completed successfully. The #595 artifact contains a
   MIPS32r2 `mt76x3_ap.ko`; inspect the evidence document before relying on it.
2. The v39 candidate is **not** the production driver and has not been tested
   on the router. Continue with the PCI remove/adapter lifetime blocker,
   including actual worker join and checked child/root quiescence. Then follow
   the remaining IoT acceptance sequence in `docs/PROJECT-DELIVERY-SCOPE.md`.
3. Do not rerun #595 or claim device acceptance from CI. Do not write, flash or
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
