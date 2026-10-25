# IoT PCI retirement owner contract (2026-10-25)

The isolated MT7603 v39 candidate still has a `void` PCI `remove` callback
that ignores the checked `RtmpPhyNetDevExit` result and calls
`RtmpRaDevCtrlExit` (which frees the adapter). An early return after a child
failure would leave a partly removed PCI device; continuing would risk a
use-after-free. No production driver or router state was changed here.

Added the host-only `tools/iot/pci-retirement-owner.h` sequence:

1. Fence admissions while holding the adapter lifetime.
2. Request stop and join any queued/running close work outside the adapter
   lock; retained tickets still require checked reconciliation.
3. Prove all child families completed and no deferred owner remains.
4. Prove root netdev detach and main callback quiescence.
5. Claim adapter release once, only after the existing release gate proves
   radio DOWN, no pending reset, no live refs/registration, and callback plus
   physical quiescence.

`tools/iot/check-pci-retirement-owner.c` rejects skipped stages and double
release. It compiled with strict C11 `-Wall -Wextra -Werror` and ran with
`PASS PCI retirement owner: release requires ordered quiescence`. The first
fixture run mistakenly assumed the initialized radio was CLOSING and hit an
assertion; the fixture now explicitly sets that phase before checking its
rejection. The corrected run passed. The first Windows test process remained
in the system after assertion (PID 26164). Attempts to stop that exact PID
with `Stop-Process` and `taskkill /F` did not succeed; `taskkill` returned
`Odmowa dostępu` (access denied). It did not block the corrected run, which
used a unique output filename. No other process was touched.

This is an executable ordering contract, **not** a bound work scheduler or
safe PCI-remove implementation. Next production candidate must implement
actual stop/join, checked child/root teardown and callback/DMA proofs before
calling the final release function. No MIPS target compile or device test was
performed.

## Follow-up source check (2026-10-25)

The isolated v39 source still has the unsafe release edge:
`os/linux/pci_main_dev.c:426` discards the `BOOLEAN` result from
`RtmpPhyNetDevExit`; line 430 calls `RtmpRaDevCtrlExit` regardless. That
function frees `pAd` in `common/rtmp_init.c:2488`. In
`os/linux/rt_main_dev.c:881-899`, any failed AP-client, WDS, MBSS or monitor
remove returns before root-netdev detach. The v39 candidate has no bound
`wr_iot_aux_close_recovery` worker or `wr_iot_pci_retirement` owner; those
remain host-only contracts. Existing driver work queues do not establish a
join of a future retained close worker.

The checked child errors do reach that boundary. `RT28xx_ApCli_Remove`,
`RT28xx_WDS_Remove` and `RT28xx_MBSS_Remove` return their ioctl result;
`ap/ap_cfg.c:15048` and `:14965`, plus `common/cmm_cfg.c:1346`, return
`NDIS_STATUS_FAILURE` when the respective family removal fails. Thus the
first discarded result on this path is the call in `rt_pci_remove`, not an
intermediate ioctl wrapper. This trace does not prove that every family
teardown is idempotent or safe to retry.

The root close is a separate unresolved edge. In v39
`os/linux/rt_main_dev.c:112-143`, `MainVirtualIF_close` publishes main-down,
calls `RTMPInfClose` and the unchecked `VIRTUAL_IF_DOWN`, then decrements the
module use count and returns `0`. The `main-stop-owned.h` checked admission
and completion contract exists only as a host model; this `ndo_stop` does not
use it. Root `RtmpOSNetDevDetach` ultimately calls
`unregister_netdevice` (`os/linux/rt_linux.c:1619`) and cannot treat that
callback's return as proof of physical quiescence. Thus checking only the
`RtmpPhyNetDevExit` Boolean would still leave adapter release unproved.

`RTMPInfClose` is declared `VOID` in `include/rt_os_net.h:168`. The
candidate's `wr_iot_rt28xx_close_checked` calls
`wr_iot_drv_close_checked`, but its own comment says its return is
software-close success, not RF or hardware observation
(`include/wr-iot-physical-close-result.inc`). The host
`wr_iot_main_stop_complete` requires a separate `physical_verified` receipt
for the final `WR_RADIO_CLOSE`; no source-bound producer of that receipt is
present in v39. Passing `1` merely because software close returned would
violate this contract. Main-stop binding therefore also needs a real
physical-quiescence observer and retained-ticket recovery.

## MT7603 physical-close incompatibility

`os/linux/rt_rbus_pci_drv.c:2055` assigns `HIF_MT` to the MT7603 adapter.
The checked shutdown path in `common/rtmp_init_inf.c:1195` calls
`RT28xxPciAsicRadioOff(pAd, RTMP_HALT, 0)` and treats `FALSE` as failure.
But `common/cmm_mac_pci.c:2955-2967` explicitly says HIF_MT is unsupported
and returns `FALSE` before doing radio-off work. Therefore the v39 MT7603
checked close reaches `shutdown_stage=3` on this path and cannot supply the
required physical-close receipt even without an injected failure.

There is an MT-specific `MTPciMlmeRadioOff` in
`hw_ctrl/cmm_asic_mt.c:6335`, used by the separate `PciMlmeRadioOFF`
dispatcher. It returns `VOID`: it discards the `MTPciPollTxRxEmpty` outcome,
the possible `CmdRadioOnOffCtrl` result and PDMA/readback status. Merely
substituting that call would hide failure rather than prove quiescence.
Next source candidate must add an MT7603-specific checked stop with bounded
DMA drain, radio-command result where supported, PDMA disable/readback and
explicit failure retention. Only then can main-stop completion and PCI
adapter-release ownership be connected. The original v39 source remains
unchanged and outside the production image.

Child removal also has family-specific partial states: WDS and AP-client call
`RtmpOSNetDevClose` (a `void` wrapper around `dev_close`) and refuse free
when the registered close phase is not idle. MBSS deinitializes beacon state
before detaching its netdev. A generic retry of the whole family remove
cannot be assumed safe after one child already completed or an MBSS beacon
step partially advanced. The next source binding must retain per-device
progress and settle the main close ticket as well as child tickets.

The host-only owner now has an explicit `STOP_REQUESTED` phase between the
admission fence and work join. The fixture rejects a join before stop request,
an unconfirmed stop request and a repeated stop receipt. Recompiled and ran
`check-pci-retirement-owner.c` with MinGW GCC, C11, `-Wall -Wextra -Werror`:
`PASS PCI retirement owner: release requires ordered quiescence`. This proves
the model's phase checks only; no stop request or join is yet bound to the
vendor driver.

Implementation order for the **same** PCI remove owner:

1. Under the adapter transition lock, fence new open/registration and mark
   retirement. Keep the adapter and root/child netdev references live.
2. Outside that lock, request stop and join every close continuation. A
   stopped worker is not a successful close: reconcile its retained ticket
   and family-specific partial side effects before child removal can pass.
3. Check each child removal result and callback quiescence; only then detach
   the root netdev and prove its callbacks quiescent. Recheck the radio,
   registration and reference gate under the shared lock before adapter free.
4. Cover a persistent child-close failure explicitly. The `void` PCI callback
   cannot propagate it to the PCI core, and returning early after partial
   removal leaks ownership. This case requires a proven synchronous recovery
   or a separately pinned, unload-safe owner; neither exists in v39.

Until all four steps and fault-injection interleavings pass, do not connect a
deferred worker to v39, install it in the firmware image or infer runtime IoT
support from the successful isolated MIPS compilation in build #595.

## Isolated MT7603 radio-off source candidate (v40, local only)

`tools/iot/prepare-mt7603-checked-off-candidate.py` now derives a separate
source overlay from the reviewed v39 files. It adds a checked HIF_MT path to
`wr_iot_drv_close_checked`: RX disable/readback, bounded TX/RX DMA idle poll,
MCU radio-off command result, then PDMA disable/readback. The close records a
retryable stage after software shutdown so an early poll/readback failure does
not replay `APShutdown` or `MlmeHalt`; a command with uncertain completion is
terminal for that ticket and is not replayed. The legacy non-MT path remains.

The generated directory is under `.iot-local-check/` and deliberately has **no
assembly manifest**: the copied v39 manifest would have stale hashes. The
optional `v40` CI variant now generates the overlay, pins a fresh manifest
against the reviewed driver revision, and passes it to the existing isolated
module build. Python syntax, source generation, YAML parsing and `git diff
--check` passed locally on 2026-10-25; **the v40 CI variant has not run**.
Target C compilation, fault injection, final-ROMFS packaging and hardware
observation remain unverified. An MCU command result plus PDMA register
readback cannot establish RF silence or callback quiescence. Before any
production merge, audit the stage-4 resumption path, PCI callback lifetime
and failure-retention rules.
