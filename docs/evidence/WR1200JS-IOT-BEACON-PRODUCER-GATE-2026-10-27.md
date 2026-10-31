# IoT beacon/TIM producer lifetime — host contract, 2026-10-27

The isolated candidate is not ready for the firmware image. In its
`ap/ap_connect.c`, `APUpdateBeaconFrame` takes `BeaconPkt` near the start of
the function and performs a long frame build before its final hardware
kickout. In `ap/ap_nps.c`, `RT28xx_UpdateTimToAsic` takes `TimPkt` before
`BcnRingLock`. `MBSS_Close` revokes beacon intent under that lock, but it does
not wait for a producer already using either pointer. A simultaneous zero DMA
and TxS snapshot therefore does not prove that buffer deinit is safe.

`tools/iot/beacon-producer-gate.h` now models the required per-BSS contract:
admit a generation before packet-pointer access, revoke admission under the
same lock used for final submission, wait outside that lock for active
producers to finish or cancel, and reject reopen until the old generation
drains. `tools/iot/check-beacon-producer-gate.c` covers a close racing with
preparation, blocked late submit, blocked early reuse and generation checks.
Each invocation has its own ticket, so a duplicate finish from one producer
cannot decrement the count held by a second producer of the same generation.
Revocation is idempotent for that generation: a retained close may retry its
drain without reopening admission.

The binding must cover `APUpdateBeaconFrame` and `APMakeBssTimFrame` from
their entry through all early returns. Pinning only
`RT28xx_UpdateTimToAsic` is too late: `APMakeBssTimFrame` already writes to
`TimPkt` before calling it. Final submit must check the same generation while
holding the submission lock. A wait for producer drain must not hold that
lock, or producer completion could deadlock.

The producer entry is not limited to a process context:
`common/cmm_data_pci.c:1520-1526` calls `APMakeAllTimFrame` from
`RTMPHandlePreTTTTInterrupt`, which reaches `APMakeBssTimFrame`. The
`APUpdateAllBeaconFrame` path is reached from `RTMPHandlePreTBTTInterrupt` in the same
file. Thus begin/end and the final submission check must use IRQ-safe,
non-sleeping synchronization; only the close owner may sleep while waiting
after revocation. The existing candidate uses both `RTMP_SEM_LOCK` and
`RTMP_IRQ_LOCK` forms on `BcnRingLock` in beacon paths. Their definitions
must be checked for each target configuration. The host contract does not
solve the void `rt_pci_remove` teardown hole.

Pinned-source check for the #631 target: in `include/os/rt_linux_cmm.h` at
`c25283e`, `RTMP_SEM_LOCK` uses `RtmpOsSpinLockBh`; with
`MULTI_CORE_SUPPORT` disabled, `RTMP_IRQ_LOCK` uses the same BH wrapper.
The downloaded `merged-capacity.json` for #631 reports this option false in
all nine inspected units, and the CI gate rejects a mixed-form build if it
becomes true. `mt_mac_int_3_tasklet` in `os/linux/rt_rbus_pci_drv.c` invokes
`RTMPHandlePreTBTTInterrupt` for the MT MAC path. This supports using the
existing lock for short producer admission/revocation on this target; it
does not justify sleeping under that lock or assuming the same result on
other configurations.

## Isolated v42 binding, source preparation only

`tools/iot/prepare-beacon-producer-candidate.py` layers a new isolated
candidate on the v41 checked-stop tree. It adds per-BSS gate storage and a
wait queue to the adapter, initializes them before publication, wraps
`APUpdateBeaconFrame` and `APMakeBssTimFrame` from entry through every
return, revokes and drains on MBSS close/abort, and refuses beacon buffer
deinit while the gate is open or producers remain. The preparer verifies
that only five reviewed source files and two new headers change. The optional
workflow accepts `v42` and retains target-source manifest and MIPS module
checks. Ordinary production builds do not select it.

Local verification: current v39 → v40 → v41 → v42 source preparation
succeeded; both host fixtures passed under GCC strict C11; Python scripts
compiled; workflow YAML parsed; `git diff --check` passed. The v42 manifest
explicitly reports `target_compiled=false`, `production_installed=false`,
`runtime_verified=false`, `recovery_owner_bound=false` and
`pci_release_gate_bound=false`. A target compile is still required, followed
by recovery/PCI lifetime and late DMA/TxS report proof. No router setting
was changed.

A source-call scan of the prepared v42 tree found one call to
`RT28xx_UpdateBeaconToAsic`, from the wrapped `APUpdateBeaconFrame` inner
function, and one call to `RT28xx_UpdateTimToAsic`, from the wrapped
`APMakeBssTimFrame` inner function. Other beacon callers, including WSC and
configuration handlers, call the public wrapped `APUpdateBeaconFrame`.
`APMakeBssBeacon` checks `BeaconPkt` but returns before dereferencing it
for this HIF_MT path. The other `RT28xx_UpdateBeaconToAsic` definition is
under `RTMP_MAC || RLT_MAC`, outside the reviewed MT target. This is source
coverage for the pinned candidate, not proof that all runtime callbacks or
late hardware reports are quiescent.

## Target compile follow-up

Run #634 (`40527671413`) completed successfully. Its downloaded artifact
confirms the isolated v42 MIPS32r2/O32 module and matching SHA256. The ordinary
image still excludes this candidate. See
`WR1200JS-IOT-V42-CI-634-TARGET-COMPILE-2026-10-27.md` for the bounded
evidence. Recovery ownership, PCI release and late DMA/TxS safety remain open.
