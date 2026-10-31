# WR1200JS IoT: PCI remove lifetime boundary (2026-10-25)

This is a source review of the isolated MT7603 candidate
`.iot-local-check/aux-preclose-v38-20261025`, not a production driver change.

## Exact path

1. `os/linux/pci_main_dev.c:408` defines `rt_pci_remove` as `VOID`.
   At line 426 it calls `RtmpPhyNetDevExit(pAd, net_dev)` without checking the
   result; line 430 immediately calls `RtmpRaDevCtrlExit(pAd)`, and line 451
   frees the root netdev.
2. `os/linux/rt_main_dev.c:866` defines `RtmpPhyNetDevExit` as `BOOLEAN`.
   It retires the radio under `wr_iot_transition_lock`, then may return
   `FALSE` on an AP-client, WDS, MBSS or monitor removal failure before
   detaching the root netdev. Thus a child can still exist when PCI remove
   ignores this failure.
3. `common/rtmp_init.c:2451` defines `RtmpRaDevCtrlExit`; line 2488 calls
   `RTMPFreeAdapter(pAd)` unconditionally. Any deferred close owner or worker
   retaining `pAd` can then access freed memory. The host-only
   `tools/iot/aux-close-recovery-owner.h` explicitly requires an adapter
   release fence and joined work; it does not install either in this path.

The source therefore does **not** satisfy the precondition for binding a
deferred WDS close worker. A `VOID` PCI remove callback cannot safely make a
failed `RtmpPhyNetDevExit` harmless merely by returning early: device teardown
must still own the remaining resources and eventually complete. Silently
continuing to adapter free is also unsafe.

## Required next implementation gate

- Before PCI remove can free adapter or netdev, stop new open/registration,
  quiesce callbacks/TX, request recovery stop, then cancel/join any queued or
  running worker outside the adapter lock. Keep the adapter/netdev/module
  references while checked child teardown remains incomplete.
- Reconcile an uncertain child-close result by family, finish the exact
  retained ticket, and verify zero deferred owners plus the conditions in
  `tools/iot/adapter-release-gate.h` under the shared adapter lock. The
  checked completion receipt must be recorded before another ticket changes
  `retired_serial`.
- Only then detach/free the root netdev and call `RtmpRaDevCtrlExit`.
  Define ownership for failures that cannot be completed synchronously in the
  `VOID` remove callback; do not leak or free live resources. Check probe
  failure, unbind, PM and module unload paths against the same ownership rule.
- Compile the bound MT7603 driver with the target MIPS toolchain and test
  remove/failure interleavings before including it in a firmware image.

Status: **source-level release hazard confirmed; production fence and worker
not implemented; no target build or router test performed in this step.**
