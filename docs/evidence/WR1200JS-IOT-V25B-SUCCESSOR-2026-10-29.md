# Isolated v25b successor

The saved later candidate contains recovery, steering publication and beacon
producer stages missing from the freshly regenerated base queue bundle.
The base must not overwrite it. SHA256 reconciliation found 26 shared files
different and eight additional later files.

`tools/iot/prepare-v25b-generation-bound.py` prepares a separate successor.
It verifies exact reviewed TxS/readiness-header input hashes, applies the
generation-exhaustion refusal and invalidated-READY demotion, and records
every input/output hash. All other source bytes remain unchanged. The legacy
v25b checked-close bound was already present and was retained.

`tools/iot/check-v25b-successor.py` verifies the full receipt, checks five
virtual caller families/five registration paths, extracts and runs the TxS
ledger and checked close, and runs the intended WR_IOT_V40 post-open fixture.
Compiles use strict optimized GCC C11; each command has a 30-second timeout.
Run on `.iot-local-check/v25b-generation-readiness-20261029` passed; detailed
logs and candidate hashes are in
`.iot-local-check/v25b-successor-fullchecks-20261029/result.json`.

The 71-file inventory has exactly two declared changed files. Passing host
checks does not establish a complete MIPS module, production backend, firmware
image or device operation. The ledger still deliberately demonstrates stale
PID report ambiguity. Exact report identity/drain remains required before
selective BSS retirement can be accepted. Vendor source copies remain local;
this report does not authorize publishing them.

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

2026-10-29 overlay correction: older manifest marks four required include/*.inc
as fixtures. Initial scratch output omitted them; superseded by overlay2.
Generator now excludes only seven root test fragments and applies all 64
driver files, including those four required include fragments. Verified present.

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
