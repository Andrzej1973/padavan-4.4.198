# IoT beacon TxS retirement: identity and drain evidence

Scope: isolated WR1200JS MT7603 candidate, not the production driver or a
router runtime test. The successful target compile is GitHub Actions run
`40054121188` on `5da2e60`; its probe is in
`../iot-merged-probe-550-guard/`. Preserve the working copy's unrelated
modified and untracked files.

## Existing close check and its limit

Revalidated 2026-10-29 against the current isolated v25b source: extracted
ledger/parser fixture compiled with GCC C11, `-Wall -Wextra -Werror -O2`
and executed successfully. Its negative witness still demonstrates that an
injected old report on a reused PID consumes the newer BSS reservation.
This confirms the current software ambiguity; it does not demonstrate an
actual delayed report on hardware. Temporary fixture/executable were removed
by the isolated test context, without editing the source candidate.

`include/wr-iot-mbss-close-checked.inc` stops the target BSS beacon request,
calls `MBSS_Close`, then asks `WrBeaconTxSOutstanding` whether the target
BSS has software TxS slots or an active callback. This query only samples
the software ledger. `tools/iot/prepare-beacon-txs-ledger-check.py` already
has a negative witness: after a PID is released and assigned to another BSS,
an injected old report can consume the new slot and make the new BSS appear
idle. The test models a possible ordering; it does not claim that MT7603
actually duplicates reports. Current candidate flags correctly remain
`selective_bss_txs_retirement_proved=false` and
`beacon_ring_admission_atomic=false`.

## Could the reported sequence number identify an old beacon?

The candidate's `TXS_D_4` has a 12-bit `sn` and an 8-bit `pid`
(`include/mac/mac_mt/mt_mac.h:1225-1247`). `TMAC_TXD_3` has a 12-bit `sn`
and `sn_vld` bit (`mt_mac.h:293-318`). However the reviewed beacon builder
sets `NSeq=TRUE` and the candidate's `write_tmac_info` does not assign a
beacon `txd_3.sn` or `txd_3.sn_vld`. No expected SN is retained with the
reservation. Thus the candidate cannot currently compare a report SN with
the submitted beacon's SN.

The upstream Linux MT7603 implementation defines the same descriptor fields
in [mac.h](https://github.com/torvalds/linux/blob/master/drivers/net/wireless/mediatek/mt76/mt7603/mac.h).
Its [descriptor writer](https://github.com/torvalds/linux/blob/master/drivers/net/wireless/mediatek/mt76/mt7603/mac.c)
clears `MT_TXD3_SN_VALID` for non-QoS data and non-BAR frames, which includes
ordinary beacons. This is evidence about that implementation's chosen TXD
format, not a hardware guarantee for our vendor driver. It supports
investigating hardware-assigned beacon SN; it does not prove that a software
chosen SN would be accepted or echoed unchanged by WR1200JS hardware.

Follow-up on the exact isolated v25b source: `ap/ap_connect.c:127` sets
`mac_info.NSeq = TRUE` for the beacon, but a search of the candidate shows no
consumer of `NSeq` in `mac/mt_mac.c::write_tmac_info`. That writer also does
not set `txd_3->sn` or `sn_vld`. The `TXS_D_4.sn` value is printed in the
TxS dump and saved only in a `DBG` time record by `BcnTxSHandler`;
`tx_rx/txs.c::RemoveTxSStatus` claims by PID and does not compare SN.
`common/cmm_data_pci.c:2255` assigns a software Sequence in the separate
`MlmeHardTransmitTxRing` path; it is not evidence of a beacon reservation
identity. Thus the existing source does not implement an SN match. A target
experiment would have to establish an actual submission-to-report SN mapping
before any close gate could rely on it. This does not prove the hardware
cannot provide one.

## Could a fixed timeout prove that the report queue is drained?

Upstream mt76 uses a [status timeout](https://github.com/torvalds/linux/blob/master/drivers/net/wireless/mediatek/mt76/mt76.h)
of `HZ/4` after DMA completion and then [stops waiting for TxS](https://github.com/torvalds/linux/blob/master/drivers/net/wireless/mediatek/mt76/tx.c).
That is a recovery policy, not a source-backed upper bound on when this
vendor driver's old report can arrive. Copying the timeout would make a
software slot reusable without proving that a delayed report cannot later
match its new owner. A timer alone must not flip the retirement flag true.

## Does TxS WLAN index distinguish a stale beacon from another BSS?

No in the reviewed MT-MAC submission path. In isolated v25b,
`ap/ap_connect.c::write_tmac_info_beacon` sets `mac_info.WCID = 0` for the
MT-MAC beacon and passes `apidx` separately as `TxSPriv` and `bss_idx`.
`mac/mt_mac.c::write_tmac_info` copies `info->WCID` into
`txd_1->wlan_idx`. The received `TXS_D_3::wlan_idx` therefore cannot be
treated as a unique BSS identity: two beacons for different BSSs submit
the same WLAN index. The other legacy descriptor branch uses the common
`RESERVED_WCID` value and does not rescue this path. This is a source-backed
rejection of the simple WLAN-index filter, not an on-device measurement of
what the chip returns. Keep the PID-reuse negative witness and the
`reports_drained` requirement; do not use `wlan_idx` alone as its proof.

## Available driver cleanup paths are adapter-wide

### Why simply disabling beacon TxS is not a selective-close fix

The isolated v25b driver registers `BcnTxSHandler` and enables host status
for management beacons in `tx_rx/txs.c:340-342`. The normal beacon DMA
completion in `common/cmm_data_pci.c:2743-2744` advances
`BCN_TX_WRITE_TO_DMA` only to `BCN_TX_DMA_DONE`; the TxS handler in
`tx_rx/txs.c:77-124` advances the BSS to `BCN_TX_IDLE`. The ordinary beacon
update path checks for `BCN_TX_IDLE` in `ap/ap_connect.c:638`, and
`wdev_bcn_buf_deinit` refuses a non-IDLE beacon buffer in
`tx_rx/wdev.c:142-150`. Other IDLE assignments occur during initialization
or broader reset paths, not as a demonstrated replacement for each normal
beacon completion. Thus deleting the beacon TxS subscription would change
the steady-state beacon state machine; it is not a proven way to remove the
late-report hazard. A replacement would need an independently observed
completion path and selective lifetime proof before any candidate change.

The pinned receive path also shows why an empty software ledger is not a
report-queue barrier. `common/cmm_data.c:578-617` handles
`RMAC_RX_PKT_TYPE_RX_TXS`: one received packet may contain `txs_cnt` reports,
each 20 bytes; the loop passes only `txs_d4->pid`, `txs_d0->txsfm` and the
report body to `ParseTxSPacket`. The current candidate parser claims the
software slot by PID before invoking the beacon handler. A report may
therefore already be present in a received batch while the close path sees
the slot as idle. The reviewed source has no per-BSS receive-batch flush or
generation field in this parser call. The candidate's reservation generation
is software-only and cannot identify a delayed report after PID reuse.


In the assembled candidate, `RtmpNetTaskExit` kills both `rx_done_task`
and `bcn_dma_done_task` (`os/linux/rt_rbus_pci_drv.c:107-117`). Its callers
are adapter initialization/teardown paths in `common/rtmp_init_inf.c`, not
the checked close for one virtual BSS. `RTMPRingCleanUp(QID_BCN)` loops over
every cell in the shared beacon ring and resets the ring indices
(`common/cmm_mac_pci.c:1889-1933`). `RTMPRingCleanUp(QID_RX)` likewise acts
on the shared receive ring. Calling either global cleanup from one IoT BSS
close could discard work belonging to the main or guest BSS; the current
candidate does not do that. `RTMPHandleBcnDmaDoneInterrupt` retires entries
in the same shared beacon ring and reads each packet's `own_mac` to update
its BSS state (`common/cmm_data_pci.c:2668-2760`); it is a possible place
to account for per-BSS DMA retirement, but its current state update is not
a hardware TxS drain. A safe selective barrier must preserve the other BSSs
and separately account for reports already in the shared RX path.

## DMA owner accounting must cover every ring exit

Source inspection after the per-descriptor owner-reset change found the
submission point in `common/cmm_data_pci.c:750-865`:
`RtmpPCIMgmtKickOut` publishes a packet to `BcnRing.Cell[TxCpuIdx]` and
advances the shared hardware index for `Q_IDX_BCN`. The candidate call path
at `common/cmm_mac_pci.c:2726-2752` holds `BcnRingLock` over this publish.
The normal beacon DMA callback at `common/cmm_data_pci.c:2668-2766`
reclaims cells under the same lock and can decode each descriptor's
`own_mac`. A per-BSS DMA ledger could therefore record ownership at
publication and retire it at normal completion without clearing another
BSS's entry.

But the callback is not the only ring exit. Adapter-wide
`RTMPResetTxRxRingMemory` (`common/cmm_mac_pci.c:64-220`),
`RTMPFreeTxRxRingMemory` (`cmm_mac_pci.c:1329-1550`), and
`RTMPRingCleanUp(QID_BCN)` (`cmm_mac_pci.c:1889-1933`) also reclaim or
clear beacon cells. A future ledger must handle these paths and missing
packet cells as well as normal completion; otherwise an outstanding count
could remain nonzero forever or falsely reach zero. These global paths
cannot be invoked to close just IoT while main and guest BSS stay active.
This is a source map, not a completed DMA barrier or TxS drain.

## Next implementation gate

Current generated close review: `wr_iot_mbss_close_checked` releases the
transition lock before MBSS_Close and before WrBeaconDmaOutstanding /
WrBeaconTxSOutstanding. These are immediate snapshots; the wrapper does not
hold BcnRingLock across an RX wait. Thus the reviewed wrapper does not itself
introduce the proposed RX-wait/beacon-lock inversion. However zero snapshots
still allow it to proceed to virtual-down/reference retirement without a
hardware report barrier. Its production exclusion remains mandatory until
that gap is resolved; absence of this lock inversion is not close safety.

PCI lock-order constraint, 2026-10-29: pinned cmm_data_pci.c acquires
`RxRingLock[RxRingNo]` at 1712, calls `parse_rx_packet_type` at 1836,
and releases that ring lock at 1993. A beacon TxS callback can therefore
reach BcnRingLock while the RX ring is owned. Any close/drain implementation
must not hold BcnRingLock while waiting for that RX owner or synchronizing
its tasklet: doing so can prevent the callback required for progress.
Publish the BSS stop/admission state under the beacon lock, release it,
then perform bounded synchronization and revalidate under the appropriate
transition owner. This is a design constraint, not an installed drain.

MT dispatch resolved in pinned source: MT7603 sets `HIF_MT`
(`chips/mt7603.c:1038,1097`); the MT branch in `mcu/mcu.c:179` selects
`AndesMTRxEventHandler`. The common RX parser sends only RX_EVENT packets
to that callback; RX_TXS uses its separate direct ParseTxSPacket branch.
AndesMTRxEventHandler calls AndesMTRxProcessEvent without re-entering the
common parser. The direct generic Andes caller PciRxCmdMsgComplete is
guarded by RLT_MAC and originates from its HIF_RLT path. Thus the ordinary
MT event route does not add a second beacon-TxS queue owner in this reviewed
source. Preserve target-preprocessing/runtime limits and focus the remaining
retirement proof on PCI RX backlog, hardware status and callbacks.

Andes follow-up: `AndesCmdMsgBh` consumes `rx_doneq`, but no producer
referencing that queue was found in the full pinned C/header inventory.
Another direct caller is in `mcu/andes_rlt.c:647`; MT event processing has
its separate `AndesMTRxEventHandler`/`AndesMTRxProcessEvent` path. Therefore
the generic Andes parser call alone is weak evidence of reachable MT7603
beacon TxS. Follow effective dispatch/type guards before adding a queue drain
or treating this as an active owner; source search alone does not prove its
runtime exclusion.

Full-tree caller review, 2026-10-29: `parse_rx_packet_type` also has an
MT_MAC caller in `mcu/andes_core.c::AndesRxProcessCmdMsg` (line 433), in
addition to PCI RX extraction and SDIO paths. This does not prove MCU RX
delivers beacon TxS on WR1200JS, but a barrier cannot assume the PCI RX
tasklet is the only possible parser owner without checking routing/type
constraints and effective flags. Account for the Andes receive queue or
prove beacon TxS cannot enter it before claiming report drain.

2026-10-29 PID quarantine review: permanent non-reuse is not a steady-state
solution. The inspected allocator casts its index to `UINT8`, scans a finite
`TXS_STATUS_NUM` pool, and fails allocation when no UNUSED slot remains.
Quarantining every completed beacon PID would therefore eventually stop
submission. Quarantining only uncertain completions also does not resolve
the existing negative witness for an old report after an apparently normal
completion. This may be a bounded failure-containment policy, but cannot
replace report identity or a proved drain for continued operation. No driver
change was made based on this option.

Before binding selective IoT close to production, choose and verify one of:

1. An exact report identity: establish on target hardware that a per-beacon
   SN (or another report field) can be assigned at submission, retained with
   the PID, and returned unchanged; handle wrap, PID reuse and duplicate
   reports in host tests and the device test.
2. A real drain barrier: after stopping all producers for the target BSS,
   prove that its beacon DMA descriptors, hardware TxS queue, software RX
   backlog and callbacks have retired before releasing its PID or reopening
   that BSS. A timeout must fail closed and retain ownership unless hardware
   reset/flush semantics prove no old report can arrive.

The successful MIPS module build and current software ledger satisfy neither
gate. No router settings, modules, firmware or services were changed during
this audit.
