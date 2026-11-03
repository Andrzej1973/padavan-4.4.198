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
