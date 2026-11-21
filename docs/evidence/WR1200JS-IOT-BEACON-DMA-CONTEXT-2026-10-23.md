# IoT MT7603 candidate: beacon DMA callback context

Source: exact pinned `vipshmily/padavan-4.4@c25283e915a2a00a763774dd255b14aff997285e`
with 45 candidate driver files overlaid in a separate scratch tree. The full
source-text lock inventory is
`WR1200JS-IOT-FULL-CANDIDATE-BEACON-LOCK-INVENTORY-2026-10-23.json`.

- `os/linux/rt_rbus_pci_drv.c:1642-1652`: the interrupt handler detects
  `MT_INT_BCN_DLY`, disables that interrupt source and schedules
  `bcn_dma_done_task` with `RTMP_OS_TASKLET_SCHE`. It does not call
  `RTMPHandleBcnDmaDoneInterrupt` inline.
- `os/linux/rt_rbus_pci_drv.c:597-640`: `bcn_dma_done_tasklet` calls
  `RTMPHandleBcnDmaDoneInterrupt` at line 629. The only call found in the
  assembled candidate source tree is this deferred callback.
- `include/os/rt_linux_cmm.h:335-350`: `RTMP_OS_TASKLET_SCHE` maps to
  `schedule_work` if `WORKQUEUE_BH` is defined and to `tasklet_hi_schedule`
  otherwise. Both variants defer execution from the hard interrupt handler.
- `common/cmm_data_pci.c:2686`: the deferred DMA callback acquires
  `BcnRingLock` with `RTMP_SEM_LOCK`. The pinned wrapper uses the BH spin-lock
  for SEM; build #540 established `MULTI_CORE_SUPPORT=false` only for the
  baseline translation unit, not the overlaid candidate.

This establishes a source-level caller path for one lock owner. It does not
prove the target candidate's effective `WORKQUEUE_BH`, conditional call
reachability, the context of other owners, absence of nested acquisition,
lock lifetime, or target compilation. It is not runtime acceptance. Next:
capture exact target Kbuild commands for all nine candidate lock units and
audit each surviving call path before choosing one lock discipline.

## Beacon TxS receive path and lock order

- `tx_rx/txs.c:340` registers `BcnTxSHandler` for management beacon TxS
  reports by packet type. `ParseTxSPacket` calls a Type 1 handler only after
  releasing `TxSTypePerPktTypeLock` (`tx_rx/txs.c:830-834`). The candidate
  `BcnTxSHandler` takes `BcnRingLock` in IRQ form at `tx_rx/txs.c:98`.
- The PCI receive path runs from `os/linux/rt_rbus_pci_drv.c:391-443`
  (`rx_done_tasklet`) through `rtmp_rx_done_handle`, then
  `GetPacketFromRxRing` and `parse_rx_packet_type`.
  `common/cmm_data.c:611` calls `ParseTxSPacket` for an RX TxS report.
- `common/cmm_data_pci.c:1717` acquires `RxRingLock[RxRingNo]` at the start of
  `GetPacketFromRxRing`; `parse_rx_packet_type` is called at line 1841; the
  ring lock is released at line 1998. Thus a beacon TxS report can acquire
  `BcnRingLock` while the RX ring lock is held. This is a concrete nested
  lock order, not proof of deadlock: the reverse order and target-enabled
  branches have not yet been audited.
- The PCI hard interrupt queues `rx_done_task` rather than calling the RX
  handler inline (`os/linux/rt_rbus_pci_drv.c:1730`). The MCU command path
  also reaches `parse_rx_packet_type` from `AndesRxProcessCmdMsg`; its
  `AndesCmdMsgBh` consumer is scheduled with `RTMP_OS_TASKLET_SCHE` or
  `tasklet_hi_schedule` (`mcu/andes_core.c:450-510`). Target-specific macro
  survival and other caller contexts remain unverified.

Before production integration, check for any `BcnRingLock` -> `RxRingLock`
acquisition path, and capture exact target Kbuild flags for these units.

## Scoped reverse-order check: PCI ring cleanup and PDMA reset

In the assembled full candidate, the only C-code users of `RxRingLock` are
`GetPacketFromRxRing` (`common/cmm_data_pci.c:1716-1998`) and the `QID_RX`
case of `RTMPRingCleanUp` (`common/cmm_mac_pci.c:1800-1838`); the other
references initialize or free the lock. The latter releases `RxRingLock`
before returning from its case. The separate `QID_BCN` case acquires and
releases `BcnRingLock` at `common/cmm_mac_pci.c:1889-1932`; the two cases do
not nest these locks.

The candidate PDMA reset takes `BcnRingLock` while setting the dequeue-disable
flag (`common/cmm_mac_pci.c:1992-1994`), and again while marking beacons idle
(`2072-2098`). It releases that lock before calling `RTMPRingCleanUp` for
`QID_BCN` and `QID_RX` (`2106-2108`), then reacquires it after the cleanup
(`2118-2120`). Thus these inspected direct paths do not establish a
`BcnRingLock` -> `RxRingLock` inversion against the TxS receive path.

This is a source-text scope check, not a complete transitive call-graph or
target-preprocessed lock proof. Other callbacks under beacon-lock regions,
effective target macros, and the nine lock units' compiler commands remain
to be checked before selecting a lock discipline or integrating a driver.

## ABI run 40020039665 scope correction

The uploaded `band-steering-mips-abi` artifact contains
`iot-full-beacon-locks.json`, but it reports only 10 candidate overlay files,
6 verified source blobs, 7 lock sites in 4 units (5 SEM, 2 IRQ). The locally
assembled candidate used for the 20-site inventory has 45 overlay files and
31 source blobs. The workflow's committed `prepare-radio-queue-candidate.py`
therefore generated a narrower candidate than the local working copy. The
green ABI run proves the audit executed against that narrower CI candidate;
it does not verify the local 45-file candidate or all nine lock units. Do not
use run 40020039665 as full-candidate lock-coverage evidence.

At the time of ABI run 40020039665, the local generator differed from its
published HEAD by 691 added and 9 removed lines. Its manifest recorded 75
preparer input files: 29 were untracked, and four tracked inputs were dirty.
The generator itself was also dirty
but was missing from that input hash set. A one-line local change now adds
its own SHA-256 to `preparer_inputs`.

With this change, a fresh local preparation into
`../iot-full-dependency-closure-20261023/` completed. Its manifest records
the generator hash `40def6858a66bdcf8fddcfa1f2ad30d625ea2081b876dd4e31b4e0c25e9f184c`;
the independent audit verified 31 source blobs and again found 20 lock sites
in 9 units. The manifest has 51 file records. The audit overlays 45 paths
under driver source directories: 41 records marked `driver` and four helper
`include` fragments marked `fixture`; six other fixtures sit outside those
directories. This local repeat establishes reproducibility of the working
copy, not target compilation. Commits `b44ab21` and `569bccb` contain the
coherent dependency closure and an exact-shape CI gate; both remain local
until the active #541 run finishes and they are pushed together.

## Isolated dependency closure reproduction

An independent scratch checkout at `../iot-closure-check-20261023b/` was
assembled from `git archive HEAD tools/iot`, then overlaid with exactly the
34 local manifest inputs absent or changed in HEAD: 29 untracked inputs,
four modified tracked inputs, and the modified generator itself. No other
working-tree files were copied. Running that isolated generator against the
pinned MT7603 source succeeded. Its `manifest.json` is byte-identical to
the manifest produced in the ordinary working copy; all 51 generated driver
and fixture files match byte-for-byte. The independent lock audit again
verified 31 pinned source blobs and found 20 sites in 9 units.

This proves the selected local file set closes the generator's host-side
dependencies under this pinned source. It does not prove target compilation,
correct lock semantics, or availability on GitHub until the selected files
are pushed and the ABI workflow runs against that commit.

The audit now checks every one of the 51 candidate file SHA-256 values against
the manifest, in addition to pinned source Git blobs. The intact isolated
candidate passed. A copy with a deliberate change to `include/rtmp.h` was
rejected before writing JSON. This is a local audit-integrity check, not a
target compile or runtime result.

## Exact-image baseline #541 target preprocessing

Firmware run `40020039819` completed successfully. Its
`wr1200js-iot-radio-capacity/mt76x3.json` artifact was downloaded to
`../iot-capacity-541/`. For the baseline source installed in that image,
the `beacon_lock_units_probe` found recorded Kbuild commands and completed
directive preprocessing for four lock units: `ap/ap_cfg.c`, `ap/ap_nps.c`,
`common/cmm_data_pci.c`, and `common/cmm_mac_pci.c`. Each reports
`effective_multi_core_support=false`. All listed sites except the
`RTMPFreeTxRxRingMemory` SEM site in `cmm_mac_pci.c` survived directives.
The `txs_receive_units_probe` also completed for `cmm_data.c`,
`cmm_data_pci.c`, `wdev_rx.c`, and `andes_core.c`; all four report effective
`MT_MAC`, PCI and Andes support.

These are baseline image facts, not target Kbuild results for the nine-unit
experimental candidate. The candidate is not installed in #541, so the
remaining candidate lock owners and their effective flags remain unknown.

## Full experimental candidate ABI run 40021678711

The ABI run for `ab19045` completed successfully. Its
`band-steering-mips-abi` artifact was downloaded to
`../iot-abi-542-artifact/`. The uploaded `iot-full-beacon-locks.json` reports
515 pinned source files, 45 source-directory overlay paths, 31 verified
original Git blobs, and 20 lock sites in 9 units (11 SEM, 9 IRQ). The
candidate manifest marks 41 files as `driver` and 10 as `fixture`, sets
`production_installed=false`, and sets `target_compiled=false`.

Running the hash-checking audit again on the downloaded candidate files and
the pinned local source produced semantically identical JSON; the raw files
differ only in newline encoding after Windows artifact extraction. The CI
gate therefore covers the full source-text candidate and verifies its
candidate file hashes. It does not show which of the nine candidate units
survive target preprocessing, that the entire candidate compiles, or that
any IoT behavior works on the router. Baseline #541 Kbuild evidence cannot
be promoted to candidate Kbuild evidence.

Firmware run `40021678720` (#542, head `ab19045`) also completed with
`board-build-status-wr1200js` reporting `success`. Its downloaded
`wr1200js-iot-radio-capacity/mt76x3.json` is semantically identical to #541's
report: the same four baseline lock units have complete target Kbuild
directive probes and `MULTI_CORE_SUPPORT=false`. The experimental candidate
source is present in the repository as tooling, but the firmware workflow
does not overlay it into the production MT7603 module. Thus #542 repeats
baseline image evidence rather than candidate target-compile evidence.
