# IoT v42 PCI removal ordering: active MBSS cannot be removed first

Scope: the locally prepared isolated v42 tree
`.iot-local-check/mt7603-beacon-producer-v42-local-20261027`, derived from
pinned Padavan source `c25283e915a2a00a763774dd255b14aff997285e`.
This is source review, not a runtime or target test.

## Observed call order

1. `os/linux/pci_main_dev.c:rt_pci_remove` calls
   `RtmpPhyNetDevExit(pAd, net_dev)` and ignores its Boolean result, then
   calls `RtmpRaDevCtrlExit`, unmaps MMIO and frees the root netdev.
2. `os/linux/rt_main_dev.c:RtmpPhyNetDevExit` marks the radio retiring, then
   calls APCLI, WDS and MBSS removal before detaching the main netdev. It
   returns `FALSE` on a failed child removal.
3. `ap/ap_mbss.c:MBSS_Remove` calls `wr_iot_mbss_begin_remove` before
   beacon deinit and child `RtmpOSNetDevDetach`. A still-owned/closing MBSS
   record fails that precondition. Its child `ndo_stop` cannot be counted on
   to close the BSS before this precondition because detach occurs later.

An active IoT BSS therefore cannot be safely removed by merely adding a
recovery worker and waiting for it at the current call site. The removal
owner must first fence new opens, explicitly request checked close of each
active child, join every deferred completion outside transition locks and
RTNL, and only then begin MBSS buffer/netdev removal. The radio retirement
transition must still allow the already-admitted exact close tickets to
finish; it must reject new opens. Retry must use durable per-record receipts
without repeating beacon deinit or vendor down.

The current transition model permits `WR_RADIO_CLOSE`, `WR_RADIO_BSS_CLOSE`
and `WR_RADIO_AUX_CLOSE` after `wr_iot_radio_retire`, while blocking a new
`WR_RADIO_BSS_OPEN`. `wr_iot_radio_retire` also advances the epoch via
`wr_iot_radio_main_down`; already admitted operations must retire using their
original tickets. This makes close-before-remove feasible in the state
machine, but no source binding currently enumerates and joins each child.

PCI `remove` has a `void` callback. If child close/remove fails, the current
code's unconditional adapter/MMIO free is unsafe; simply returning early
would also leave a detached PCI device with leaked resources. A production
candidate needs a complete, bounded terminal policy for failed/uncertain
close, including callback and DMA/TxS quiescence, rather than a Boolean check
alone. No such policy is bound in v42. The candidate remains outside the
ordinary firmware image.

Next implementation gate: source/host test the order `retire admission →
checked child close → joined owner → beacon/DMA/TxS quiescence → child
unregister → main detach → adapter/MMIO release`, with failure injection at
each transition. Then compile the isolated MIPS module and inspect the final
image separately. Do not use #634 target compilation as release proof.
