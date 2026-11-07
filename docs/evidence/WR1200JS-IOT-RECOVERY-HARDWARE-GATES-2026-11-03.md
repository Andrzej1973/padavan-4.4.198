# Recovery hardware gates: unresolved proof obligations

Source audit after a6f514d3. This records open requirements, not acceptance.

## Firmware ACK freshness

Re-ran `python3 tools/iot/check-mcu-ack-epoch-gap.py
/tmp/wr-checked-ack-current-7hr05rur`. It reproduced acceptance of an old
matching result after 15 sequence slots wrap. Input andes_mt.c SHA256:
`11703f277550f9c5f1644aa3846cf342d41ed236a4365f12596ae93ca9901a37`.
This is a preserved extracted candidate, not a fresh final-image experiment.
The test injects events; it does not show that the router actually delivered
such a duplicate. Its PASS means the ambiguity was reproduced.

Current `mcu-sequence-reservation.h` releases an occupied bit at message
destruction and permits later reuse. Its stated contract is host exclusion,
not ACK freshness. A larger host epoch alone cannot distinguish two firmware
events carrying the same wire sequence and result envelope. Acceptance needs
a verified firmware-visible identity or a transport/firmware boundary that
proves old responses cannot survive reuse. A delay or empty host ledger is
not that boundary. Audit actual RX producer/consumer reset and join ordering
before choosing a remedy; do not silently exhaust IDs or reset live firmware.

The pinned `AndesMTPciFwExit` (mcu/andes_mt.c:3041) clears startup/in-band
flags, calls RT28XXDMADisable and disables interrupts. This function contains
no firmware restart or verified response flush. `AndesCtrlPciInit`
(mcu/andes_core.c:531) resets cmd_seq to zero and initializes host queues.
These operations alone therefore supply no firmware epoch receipt.
The isolated init-failure preparer adds FwExit, RtmpNetTaskExit, DMA-disabled
readback, then MCU_CTRL_EXIT; its documented scope is teardown, not an
ordinary live-BSS command freshness boundary.

Extended the gap fixture to clear the host ledger and reserve seq=1 again:
the old matching ACK remains accepted. This models a host-only reset; it
does not model completed physical RX or firmware reset. Both gap scenarios
reproduced under ASan/UBSan. Next inspect the actual hardware RX ring reset
and firmware event lifetime before proposing an epoch boundary.

Pinned RT28XXDMADisable (common/cmm_mac_pci.c:2626) delegates to
AsicSetWPDMA(FALSE). AndesMTPciFwInit (mcu/andes_mt.c:3027) enables IRQ/DMA
and command flags; it contains no explicit response flush. The RX portion
of RTMPResetTxRxRingMemory unmaps/releases receive buffers and clears host
cells. That function alone neither joins consumers nor establishes what
firmware may emit after resume. These findings do not rule out a stronger
boundary elsewhere; they rule out treating these individual calls as proof.

Strengthened peer82 target symbol checks to require all 14 MBSS close,
submission/retry, worker/join/stop, poll/caller and handoff entry symbols,
alongside the two existing checks. Validated all 16 against the independently
downloaded symbol table in artifact 13257692154 (c363e1e0); none missing.
Shell syntax and whitespace checks passed. This proves compiled presence,
not callback binding or hardware correctness. Archive was consumed in memory.

## Physical RX dispatch is an independent consumer

Pinned common/cmm_data.c:619 (`RMAC_RX_PKT_TYPE_RX_EVENT`) directly invokes
chipOps.rx_event_handler. mcu/mcu.c assigns AndesMTRxEventHandler for this MT
path. In mcu/andes_mt.c:2996 that handler tests MCU_INIT, allocates a message,
copies the packet, calls AndesMTRxProcessEvent synchronously and frees it.
It does not enqueue this event to cmd_msg_task. Clearing MCU_INIT prevents
later entries but cannot join an entry already past the test.

AndesCtrlPciExit (mcu/andes_core.c:626) kills cmd_msg_task and destroys host
queues/locks. That tasklet join alone cannot establish that the direct
physical RX event handler has returned. The pinned close path releases IRQ,
then invokes MCU_CTRL_EXIT, then resets/frees rings (rtmp_init_inf.c:939-966);
this is source order, not proof of all RX tasklet/work joins.
The staged init-failure RtmpNetTaskExit-before-MCU cleanup is therefore
relevant and must remain. Next verify its exact MT RX consumer inventory and
all ordinary-close/reopen paths, separately from firmware event freshness.
No hardware action or new scratch was needed for this source audit.

### RX consumer inventory resolved at source level

Pinned os/linux/rt_rbus_pci_drv.c initializes rx_done_task and rx1_done_task
at lines 61/64. Its RtmpNetTaskExit (106) kills rx_done_task unconditionally
and rx1_done_task under CONFIG_ANDES_SUPPORT, matching initialization guards.
The RX1 callback selects MT_INT_RX_CMD (423 onward). The same exit covers
beacon DMA, MT interrupt, BMC, management and data completion tasklets.

prepare-nettask-schedule.py wraps network submission sites, adds block/drain
before any kill, and sets `wr_iot_nettask_joined` only after the kill inventory.
The release-fence transform
excludes initialization during exit and permanently blocks reopen at adapter
release. This supplies the source-level consumer-join path for direct RX
events; it is not merely the separate MCU command-tasklet join.

Remaining distinctions: kernel tasklet/work semantics and feature builds
need their own verification; IRQ-side adapter lifetime must be retained;
successful host joins do not establish firmware event freshness after resume.
The ACK epoch question therefore remains open, while the missing source
inventory for the physical RX consumers is now identified.

## Wire payload and current ABI result

Pinned andes_mt.h:424 defines RadioOnOff request as ucWiFiRadioCtrl plus
three reserved bytes. Its result at :528 is ucExTenCID, three reserved bytes
and u4Status. CmdRadioOnOffCtrl (andes_mt.c:1751) sends the four-byte request
and requests an eight-byte EventExtCmdResult. No ON/OFF or epoch echo is
defined by these payloads; reserved bytes must not be repurposed without a
verified firmware contract. The existing parser correctly scopes itself to
syntax/status, leaving freshness to transport and physical-state evidence.

ABI run 41695343147 completed successfully on a6f514d3. Read artifact
13262195992 in memory: ABI results record MIPS layouts for both radios
(mt76x2 message size 32/alignment 4; mt76x3 size 80/alignment 8).
Its iot-successor-host report lists caller coverage, ledger, checked close
and post-open host checks. This artifact is not full peer82 module or
firmware/runtime acceptance and does not close ACK freshness.

## Defined-function verification and sequential publication

Tightened symbol gate to require FUNC, a defined section and nonzero size,
instead of accepting any matching symbol name. All 16 peer82 requirements
pass against artifact 13257692154; injected UND and OBJECT records fail,
while a defined nonempty FUNC passes. Shell syntax/whitespace checks pass.
No downloaded archive retained.

Standard 41695343356 and ABI 41695343147 succeeded on a6f514d3.
Optional 41698138284 was queued and its exact a6f514d3 SHA confirmed before
publishing only ef51b36a1d735af974e1a44a3cfa545b35e7c2ba. The newer local
RX configuration commit and uncommitted defined-symbol tightening were not
included in that push. Owner reference archives remain separate and local.

## Actual target refuses checked radio-off

Artifact 13264066070, module SHA256
36c5ab283016b513e8bdf6022845ad2b66c26c30942e81eb6515810d6911a380,
contains radio-off-capability.json reporting known_unconditional_false=true,
symbol size 8 and shutdown_capability=unavailable. Its MIPS disassembly is
`jr ra` followed by `move v0,zero`. This is concrete target evidence that the
checked-off entry cannot succeed in this configuration, not just an absent
runtime test. Ordinary callback integration cannot be accepted on this basis.

Pinned mt76x3_ap Makefile unconditionally adds -DLOAD_FW_ONE_TIME within
the MT7603 branches (795/847). The checked-off source explicitly refuses
that macro. Vendor MTPciMlmeRadioOff instead writes AGG_TEMP high bits under
LOAD_FW_ONE_TIME, omitting CmdRadioOnOffCtrl. Register write/readback alone
does not supply an MCU result or establish RF/report retirement. Do not
remove the refusal merely to obtain a non-stub symbol. A verified one-time
firmware shutdown path or a separately reviewed reload configuration is
required. The task-config checker now records LOAD_FW_ONE_TIME explicitly.

## Upstream comparison is not an epoch receipt

Consulted primary upstream source on 2026-11-03:
https://raw.githubusercontent.com/openwrt/mt76/master/mt7603/mcu.c
and Linux mt7603/main.c. The MCU parser compares response sequence, while
the sender cycles nonzero four-bit sequences. The exit function sends an
MCU restart-download request and purges its response queue. This is a
different transport/lifecycle contract from vendor AGG_TEMP writes; importing
the parser alone would not establish freshness in our driver.

Linux mt7603_stop cancels MAC work and calls mt7603_mac_stop. The preserved
upstream MAC source sets TX/RX disable bits, stops TX start queues and clears
RX_START. MAC admission stop, firmware restart and physical RX/DMA retirement
are separate operations. None of these individual snippets establishes RF
power-off or vendor one-time-firmware shutdown completion on WR1200JS.
Inference: neither upstream sequence matching nor AGG_TEMP readback is a
substitute for the missing end-to-end retirement evidence. No upstream code
was installed and no router action was taken. Master URLs are comparison
sources, not pinned target inputs or a release claim.

## Timeout-specific mitigation regression

The local extended extracted-dispatcher fixture quarantines a timed-out ID
and delivers its late ACK against 30 successive new reservations. None is
completed by that ACK. ASan/UBSan passed. The same fixture still reproduces
arbitrary duplicate replies after a successful release and host-only reset;
it does not claim a full firmware epoch solution. The preserved extracted
input remains the previously identified andes_mt.c hash. Temporary fixture
and binary were removed. CI now invokes this distinction on its actual
generated sequence-reserved candidate; live CI execution remains pending.

## MBSS close and beacon retirement

`prepare-mbss-cr-readback-check.py` checks control-bit readback and explicitly
excludes RF silence, pending RX TxS and kernel locking. The vendor
`MBSS_Close` changes queue/beacon request state and updates beacons; that
function's return alone is not a DMA/IRQ/report-drain receipt.
`mbss-close-checked.inc` likewise describes outstanding DMA/TxS reads as
snapshots, not proof that a late report cannot arrive.

The required order must exclude new beacon production, finish already
admitted submitters and DMA ownership, join relevant IRQ/tasklet/work/RX
consumers, and establish report identity/drain before releasing a reused BSS
or registration. Preserve other BSS operation; do not equate a global device
shutdown with verified independent BSS teardown.

## Uncertain recovery

a6f514d3 preserves stage-5 origin in an already admitted recovery owner.
The worker still retains RECONCILE without executing hardware recovery.
CR, vendor close, invalid BSS identity, DMA and TxS failures need distinct
validated recovery paths. Do not restore a prior stage or repeat a vendor
mutation based solely on the saved stage, a zero snapshot or elapsed time.
Ordinary callback binding and runtime acceptance remain open.

The reproduction created only a temporary host fixture/binary, removed by
TemporaryDirectory. Preserved input was left intact for unfinished work.

## Reload firmware restart is not yet an epoch receipt (2026-11-04)

Further source review of pinned mcu/andes_mt.c (SHA256 680db15bb22ad5bf48283fd3e415a0ada0e4f1f054a401f32b9d2a3c9c60baee):
CmdRestartDLReq at 929 waits for CmdReStartDLRsp, but that callback at 385
only logs firmware statuses; it does not propagate a validated status into
the caller result. Method1 checks TOP_MISC2 for ROM ready after restart
(2330) and runtime after download (2361). These are distinct observations
from transport command completion. In the ROM-not-ready timeout branch
(2338), it jumps to done without assigning failure to ret; a successful
restart transport return can therefore survive this failure branch.
This is source evidence of a missing fail-closed error result, not a
verified runtime failure or permission to change production firmware mode.

Before considering reload as an epoch boundary: validate actual board
DownLoadType, propagate ROM/start/download failures, join old RX/DMA/IRQ
consumers and retire old descriptors/events, then bind a reset receipt to
that complete transition. No sequence quarantine is cleared by this audit.
The existing one-time-mode refusal remains necessary. Full reload module
compilation and firmware/device verification remain separate pending gates.

## 2026-11-04 Sol: ROM-ready timeout candidate fix verified locally

Prepared final peer82 manifest-preserving layer prepare-fw-rom-ready.py:
Method1 ROM-not-ready timeout sets NDIS_STATUS_FAILURE and FW_NO_INIT before
existing done cleanup. Does not clear sequence quarantine or claim an epoch.
Source inventory checked before mutation; updated source hashes recorded.
check-fw-rom-ready.py compiles/executes the actual extracted branch. Old
source fails; patched source passes timeout with prior success/failure,
non-timeout preservation, cleanup path and stage invalidation. Duplicate
transformation rejected; exact inverse diff and manifest digest verified.
No heavy local build. Scratch fixtures removed; target compilation pending.
Standard 41771312863 (#735) / ABI 41771312880 still running on efbf784b.
This separate ready package may publish while that standard runs; optional
for efbf784b remains required after its standard succeeds, using explicit SHA.
