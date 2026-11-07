# IoT v41 deferred MBSS recovery and PCI release: source audit

Scope: isolated candidate source after #631. This is a review, not a bound
kernel recovery worker or a device test.

## Observed paths

- `tools/iot/prepare-mbss-checked-stop-candidate.py` replaces
  `MBSS_VirtualIF_Close` with `wr_iot_mbss_begin_close` followed by
  `wr_iot_mbss_close_checked`. It explicitly leaves admission-failure and
  retained-ticket recovery unbound. Linux may discard a failing ndo_stop
  return; the caller cannot rely on a retry of ndo_stop.
- `ap/ap_mbss.c` `MBSS_Remove` calls `wr_iot_mbss_begin_remove` before beacon
  deinit and `RtmpOSNetDevDetach`/`RtmpOSNetDevFree`. The begin-remove helper
  refuses `WR_REF_OWNED`/`WR_REF_CLOSING`; it allows `IDLE` stage-4 after a
  checked close. Thus it does not itself wait for a deferred owner that has
  not yet consumed that completion receipt.
- `os/linux/rt_main_dev.c` `RtmpPhyNetDevExit` returns `FALSE` when
  `RT28xx_MBSS_Remove` fails. But `os/linux/pci_main_dev.c` `rt_pci_remove`
  ignores this return and immediately calls `RtmpRaDevCtrlExit`, unmaps MMIO,
  releases the memory region and frees the root netdev. This is a concrete
  lifetime hole if a close/remove remains retained during PCI teardown.
- `os/linux/rt_linux.c` `RtmpOSNetDevDetach` calls
  `unregister_netdevice`; `RtmpOSNetDevFree` calls `free_netdev`. The recovery
  owner must be joined before the relevant netdev/adapter release. Joining a
  worker that needs RTNL while the caller holds RTNL around netdev detach
  would deadlock.
- `tools/iot/mbss-close-recovery-owner.h` is a host contract only. It models
  deferred ownership and a durable stage-4 receipt, but binds no
  `work_struct`, `dev_hold`/`dev_put`, or PCI release gate. The #631 manifest
  agrees: `recovery_owner_bound=false`, `pci_release_gate_bound=false`.

## Required binding sequence

1. Queue a single per-adapter/per-MBSS recovery owner under the transition
   lock on both admission failure with an acquired vendor count and retained
   checked-close failure. Pin the netdev and fence adapter release before
   making work runnable; reject duplicate ownership for the same generation.
2. Worker rechecks generation/token/ticket under that lock, performs no wait
   or vendor call while holding it, and retries only the exact outstanding
   close or conservatively retains an uncertain state. The close completion
   receipt must remain readable until the worker has consumed it.
3. Before `MBSS_Remove` permits beacon teardown or registry-slot reuse, join
   that owner outside RTNL and the transition lock. `dev_put` and adapter
   fence release occur only after joined successful completion. A failed or
   unjoined owner keeps teardown blocked; no forced success.
4. `rt_pci_remove` must honor a failed `RtmpPhyNetDevExit` and must not call
   `RtmpRaDevCtrlExit`, unmap MMIO or free the root netdev while any deferred
   owner, callback or beacon DMA/TxS operation can still use them. Design a
   complete recoverable removal path for the void PCI remove callback before
   installing this candidate.

The reviewed paths have a partial submission barrier: `MBSS_Close` clears
`bBcnSntReq` under `BcnRingLock`; the final beacon kickout in
`RT28xx_UpdateBeaconToAsic`, TIM kickout in `RT28xx_UpdateTimToAsic`, and
hardware restart check the intent under the same lock. The #631 target config
has `CONFIG_MT7603E_AIRPLAY_SUPPORT` unset. This corrects the earlier broad
description that there is no publication barrier at all.

The barrier does not cover a producer that entered before close and still
holds a raw beacon/TIM packet pointer while preparing a frame.
`APUpdateBeaconFrame` obtains `BeaconPkt` and builds the frame well before
the final `BcnRingLock` kickout; it may reserve a TxS PID after close began,
then cancel it when kickout sees the revoked intent. `RT28xx_UpdateTimToAsic`
similarly obtains `TimPkt` before taking the ring lock. The DMA snapshot
under `BcnRingLock` and TxS status/callback snapshot under `TxSStatusLock`
can both be zero while such a pre-close producer is still preparing its
frame. `MBSS_Remove` may then deinitialize the buffer. A generation-bound
producer pin from before packet-pointer acquisition through final cancellation
or completion, plus a drain before buffer deinit, is required. The exact
hardware/late-report lifetime still needs review; two zero snapshots alone
do not prove safe free.

The isolated MIPS compile does not prove these lifecycle conditions. Until
they are bound and tested, v41 stays out of the firmware image and off the
router.

## Host contract progress

`tools/iot/mbss-close-recovery-owner.h` now has a release-readiness predicate
for a registry record. An active deferred owner blocks release of its netdev
record, even after the record has an `IDLE`/stage-4 completion receipt. A
joined successful owner allows release; inconsistent active owner accounting
fails closed. The strict C11 `check-mbss-close-recovery-owner.c` fixture
compiled and executed with `-Wall -Wextra -Werror -pedantic` and exercises
these cases. This is not yet wired to `MBSS_Remove`, PCI remove or a kernel
worker, so it does not close the production lifetime hole.
