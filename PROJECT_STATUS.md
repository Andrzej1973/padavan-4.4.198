# Current project status — 2026-10-25 (updated)

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
- The local workflow now copies and configures its own isolated kernel tree for
  `iot` scope and emits a specific error if the tree is absent. `all` retains
  the preexisting full Band Steering tree. YAML parsing and scoped diff check
  passed locally; repeat target compilation is still required. No production
  driver or router state changed.
- Agent monitor run `40383532268` identified the failed job and step, but its
  first-16-MiB excerpt missed the late failure. The local monitor now streams a
  bounded last-16-MiB suffix and has a >16-MiB offline regression fixture.
  Nim compilation and the monitor fixture passed; this parser change is not
  yet part of the default-branch monitor workflow.

This section is the current handoff. Older time-specific notes below are
historical; their pending-run and local-only statements are superseded here.

- Current writer: Sol, branch `codex/wr1200js-service-webui`; published code
  baseline `a71e8ab`; follow-up IoT candidate commits are published.
  Preserve all unrelated modified and untracked files.
- Documentation evidence commit `c2b1d48` is the current GitHub HEAD. It does
  not change driver sources. Its push started ordinary firmware run #601
  (`40218879277`) and service ABI run `40218879240`; both were in progress at
  the last check and do not select the optional IoT candidate.
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
  injected DMA/MCU/PDMA/readback failures; strict C11 passed. This does not
  establish target compilation or radio silence. Fixture and optional CI hook
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
  No v40 target run has started. Push the prepared commits, then dispatch the
  WR1200JS candidate build with optional checks enabled and variant `v40`;
  inspect its target compilation and artifact evidence.
  Vendor `MainVirtualIF_close` and PCI removal are still unbound.
  Then verify network isolation and Classic WebUI. Shared HTOP/MTR integration
  is now explicit item 4 in `docs/PROJECT-DELIVERY-SCOPE.md`, pending after
  service WebUI and before WAN/final image/device acceptance. Do not start
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

## HTOP/MTR shared integration queued — 2026-10-25

User requested reusable, profile-gated HTOP and MTR support for compatible
Padavan 4.4.198 boards. The task is recorded in
`docs/PROJECT-DELIVERY-SCOPE.md` after IoT and service WebUI. No build recipe,
profile, firmware image or router was changed for this task. WR1200JS is the
only admitted image-build profile; Mi Mini and Mi 4 require separate board
and resource evidence before package inclusion. Next when this stage opens:
check pinned recipes/dependencies, then integrate and measure each eligible
profile against an identical image baseline.

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
