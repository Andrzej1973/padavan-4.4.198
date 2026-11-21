# MT76x3 virtual-interface reference audit — 2026-10-25

Source inspected: isolated `virtual-open-claim-v8-20261025` generated from
`virtual-if-identity-v2-20261024`. This is source evidence, not a compiled
driver or device test. Current checkout HEAD at audit: `f0b995d`.

## Shared dispatcher

`common/cmm_cfg.c` handles `CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP/DOWN`.
The claimed IoT MBSS UP branch verifies its ticket and increments
`VirtualIfCnt` under `wr_iot_transition_lock`. The legacy branch checks
only overflow, increments outside that lock, and can call `rt28xx_open`
when the count was zero. DOWN decrements outside the lock and ignores
the return from `rt28xx_close` on the last reference. `VIRTUAL_IF_DOWN`
returns `VOID`, so family wrappers cannot observe failure.

| Family | UP source | DOWN source | First migration requirement |
| --- | --- | --- | --- |
| Main `ra0` | `os/linux/rt_main_dev.c:MainVirtualIF_open` holds a radio ticket, then uses legacy `VIRTUAL_IF_UP` | `MainVirtualIF_close` latches main-down, calls `RTMPInfClose`, then void DOWN | Reserve its registered ref under the ticket; claimed dispatcher UP must handle first physical open and checked rollback. Main close must claim/wait before any teardown. |
| MBSS / IoT | `ap/ap_mbss_inf.c` uses claimed UP and a reserved record | legacy close exists alongside `wr-iot-mbss-close-checked.inc` | Bind the checked close, including the post-UP uncertain case; no duplicate count decrement. |
| AP-client | `ap/ap_apcli_inf.c:ApCli_VirtualIF_Open` uses legacy UP before APC_OPEN | APC_CLOSE, then void DOWN | Reserve/finish its own AUX ticket and ref; propagate APC_CLOSE and DOWN outcomes. |
| WDS | `ap/ap_wds_inf.c:WdsVirtualIF_open` uses legacy UP | stops queue, then void DOWN | Reserve/finish its own AUX ticket and ref; preserve queue and module pin on failed close. |
| Monitor | `os/linux/rt_profile.c:Monitor_VirtualIF_Open` uses legacy UP before SNIFF_OPEN | SNIFF_CLOSE, then void DOWN | Reserve/finish its own AUX ticket and ref; propagate sniffer and DOWN outcomes. |

`wr_iot_netdev_attach_checked` creates registry records for all five
families, but attachment alone leaves them `IDLE`. The new main-stop
registry/count gate therefore correctly refuses present legacy opens.
Wiring the gate directly into `MainVirtualIF_close` now would strand
mandatory teardown. Migrate all five UP/DOWN families through one count
owner first, then bind the bounded ticket wait and checked main close.

Stop and recovery paths must retain netdev/module references until the
dispatcher confirms count and physical close result. A timeout is an
unresolved close, not permission to return success, decrement a module pin,
or release a registry slot. The `IFUP_IN_PROBE` build variant needs its own
explicit handling because main open/close skip the virtual dispatcher there.

## First physical-open failure audit

`os/linux/rt_main_dev.c:rt28xx_open` called `RtmpOSIRQRequest(net_dev)` but
discarded its return. That function returns `request_irq` failure for PCI.
The caller then ran `RTMP_DRIVER_IRQ_INIT` and `rt28xx_init` as though the
interrupt had been obtained. `rt28xx_init` has staged `err0`–`err9`
cleanup; a failure is followed by `RTMP_DRIVER_IRQ_RELEASE` in `rt28xx_open`.
Neither sequence proves RF/DMA quiescence or that an opened virtual reference
can be released. In the isolated v10 candidate, IRQ request failure exits
before IRQ initialization and skips IRQ release for an IRQ not acquired;
both failure exits also end optional `WIFI_DIAG`. Source gate confirms the
branch structure. This is not target-compiled or installed in production.
