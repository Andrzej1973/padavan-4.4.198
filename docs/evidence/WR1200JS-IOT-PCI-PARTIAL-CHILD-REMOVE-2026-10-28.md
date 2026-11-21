# IoT PCI removal: partial child teardown in the isolated MT76x3 candidate

Date: 2026-10-28. Scope: read-only inspection of the nonproduction
`.iot-local-check/mt7603-main-recovery-aux-remove-v11-20261028` overlay.
This is not a target build or a router result.

## Exact source path

`os/linux/rt_main_dev.c::RtmpPhyNetDevExit` removes AP-client, then WDS,
then MBSS, then monitor. The v11 candidate checks each return and returns
`FALSE` on failure. `os/linux/pci_main_dev.c::rt_pci_remove` checks this result
and returns without freeing the adapter on failure. Its callback has a `void`
return type; a return cannot cancel the PCI core's unbind operation.

`ap/ap_apcli.c::ApCli_Remove` and `ap/ap_wds.c::WDS_Remove` free each netdev
inside a loop. A later `wr_iot_netdev_mark_removing` rejection can therefore
occur after an earlier child has already been detached and freed. Similarly,
`ap/ap_mbss.c::MBSS_Remove` loops through secondary BSS and may return failure
when `wdev_bcn_buf_deinit` refuses a non-idle beacon. The latter function in
`tx_rx/wdev.c` checks `bcn_state != BCN_TX_IDLE` under `BcnRingLock` and returns
`FALSE` without freeing that beacon packet. Earlier family or BSS removals
may already have occurred by this point.

Example source-reachable sequence (not observed on hardware):

1. AP-client removal succeeds and frees its netdev.
2. WDS removal succeeds.
3. One MBSS beacon is not idle; `MBSS_Remove` returns failure.
4. `RtmpPhyNetDevExit` returns `FALSE`; `rt_pci_remove` returns while the
   adapter, CSR mapping and remaining netdevs are retained.

This prevents immediate adapter use-after-free, but it does not establish a
complete PCI removal or a recoverable partial unbind. Re-entering the same
remove path is not a proven rollback. The current `wr_child_teardown` and
`wr_iot_pci_retirement` headers are host-only contracts; v11 does not record
their actual family completion or callback/DMA quiescence. The PCI release
gate correctly remains open.

## Why `dev_close()` cannot be the checked preclose

The pinned Linux 4.4.198 source at revision
`c25283e915a2a00a763774dd255b14aff997285e`,
`trunk/linux-4.4.x/net/core/dev.c`, shows `__dev_close_many` calling
`ops->ndo_stop(dev)` without inspecting its return value and then clearing
`IFF_UP`. `dev_close` returns 0 after `dev_close_many`. The vendor wrapper
`os/linux/rt_linux.c::RtmpOSNetDevClose` also discards the return value.
Thus a successful `dev_close` call proves neither checked virtual DOWN nor
release of a retained recovery owner. It can leave a device administratively
down while the registry record remains `WR_REF_CLOSING`.

In v11, `include/wr-iot-netdev-registration.inc::wr_iot_mbss_begin_remove`
requires the matching published registry record to be `WR_REF_IDLE` before
destructive MBSS removal. `include/interface-reference.h` places a successful
vendor UP in `WR_REF_OWNED`; a checked close must take it through CLOSING to
IDLE. `ap/ap_mbss.c::MBSS_Remove` calls `wr_iot_mbss_begin_remove` before
unregistering the netdev. Consequently, merely relying on unregister's
implicit `ndo_stop` cannot make an active MBSS removal admissible. This is a
source-derived path condition, not an observed device failure.

## Required next implementation evidence

1. Before destructive child removal, close every live child through a driver
   transaction that records the actual checked virtual DOWN result and joins
   its deferred recovery owner. Recheck each registry record under the shared
   lock; `dev_close()` return zero is not evidence of this. Prove
   beacon/producer drain for all MBSS instances, including a non-idle refusal.
2. Bind a shared retirement transaction to the actual PCI path and each
   child family. Record exact per-device completion after unregister, vendor
   teardown and callback retirement; do not infer completion from one family
   call returning success.
3. Establish a defined path for a failure after the first destructive child
   mutation. A `void` PCI remove callback cannot ask the core to retry.
   Only after this path, work joins, physical stop, DMA/callback quiescence,
   PCI observation and registry drain are proven may the adapter release
   claim precede `RtmpRaDevCtrlExit`.

No production source, firmware image, or device state was changed for this
audit. Do not promote v11 based on the eight-pair ABI check or the presence
of checked `return FALSE` statements alone.
