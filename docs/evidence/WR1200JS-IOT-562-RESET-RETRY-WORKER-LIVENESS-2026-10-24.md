# IoT reset retry depends on command worker liveness — 2026-10-24

## Scope

Read-only source audit of the reset retry path in the isolated MT7603 candidate.
The candidate remains uninstalled. No driver/image build or router operation was
performed for this audit.

## Source revision and inspected paths

The vendor source is pinned at `c25283e915a2a00a763774dd255b14aff997285e`.
Inspected:

- `common/mlme.c:1704-1712`: `MlmePeriodicExecTimer()` enqueues
  `CMDTHREAD_MLME_PERIOIDC_EXEC`.
- `common/rtmp_init.c:2649-2652`: command handling executes
  `MlmePeriodicExec()` for that queued command.
- `os/linux/rt_rbus_pci_drv.c:152-164`: `RtmpMgmtTaskInit()` creates and
  attaches `RTPCICmdThread` as `RtmpCmdQTask`.
- `os/linux/rt_rbus_pci_drv.c:1839-1852`: the worker waits for commands;
  a failed `RtmpOSTaskWait()` sets `fRTMP_ADAPTER_HALT_IN_PROGRESS` and exits
  its loop.
- `os/linux/rt_rbus_pci_drv.c:1854-1881`: on the non-suspend exit path the
  worker marks the queue stopped and frees queued commands.
- `common/rtmp_init_inf.c:619-625, 875-888`: initialization failure and normal
  halt paths release timers / halt MLME and then call `RtmpMgmtTaskExit()`.
- `tools/iot/prepare-radio-queue-candidate.py:553-560`: the candidate retries
  `wr_iot_radio_reset_drain()` after periodic MLME command handling.
- `tools/iot/reset-admission.inc:6-27`: reset drain uses `rtnl_trylock()` and
  leaves `reset_pending` set when RTNL is busy or no ticket can be admitted.

## Finding

The current candidate's deferred reset retry is coupled to a periodic command
being delivered and processed by `RTPCICmdThread`. If the wait fails, the worker
sets the adapter halt flag and exits before processing more commands; on its
normal exit path it stops and drains the queued commands. Thus the periodic
hook does not establish a guaranteed eventual retry for a retained
`reset_pending` request. During orderly teardown the adapter is also being
halted, but the inspected path does not prove that every pending reset has
already drained before command/timer teardown.

This is a liveness and teardown-order gap in the candidate, not evidence that a
reset was lost on the running router. The state machine conservatively keeps
radio readiness false while reset remains pending. The existing injected reset
fixture covers busy deferral and explicit retry, but does not model worker wait
failure, timer cancellation or adapter teardown.

## Required next work

Define one adapter-lifetime-safe reset owner covering RTNL deferral, worker wait
failure, PM suspend/resume and normal/init-failure teardown. It must guarantee
either reset drain followed by verified bring-up or terminal fail-closed device
retirement before the retry source disappears. Preserve `reset_pending` across
PCI suspend and do not accept `rt28xx_close`'s legacy zero return as radio-off
proof. Add interleaving coverage for worker wait failure, reset pending during
stop, suspend/resume, timer cancellation and teardown ordering before proposing
a production hook.
Do not claim the candidate reset lifecycle complete until those guarantees are
covered and verified in the target build.

## Close-path follow-up

The close-path candidate does not close the liveness gap by itself:

- `tools/iot/prepare-checked-close.py` stages a resumable wrapper around the
  legacy `RTMPDrvClose()` body. Its explicit manifest says legacy callers are
  not replaced and outer resource retention is unproven.
- `tools/iot/physical-close-result.inc` exposes that staged helper, but the
  adapter candidate only includes the helper beside `rt28xx_close()`; the
  existing `rt28xx_close()` caller is not redirected to it. The candidate's
  own comment says legacy `rt28xx_close` is not redirected yet.
- `tools/iot/virtual-down-checked.inc` calls that physical-close helper and
  treats its software success as completion of virtual-down. The helper in
  turn treats `RTMPDrvClose()` success as a software close notification, not
  hardware/RF observation.
- `radio-transition.h` allows a successful `WR_RADIO_CLOSE` finish to clear
  `reset_pending`. That success must therefore not be inferred merely from
  staged software-close completion; hardware quiescence and owner/lifetime
  guarantees remain unproven.

Conclusion: there is no demonstrated normal-close terminal path that safely
supersedes a pending reset. Fail-closed readiness is preserved by the state
model, but eventual drain or safe adapter retirement is not established. Do
not wire this candidate into production or use close success to clear pending
reset until the complete caller chain, hardware quiescence evidence, and outer
adapter/resource lifetime are proven together.

## PM suspend and reset-entry trace

The remaining caller trace was checked against the same pinned revision:

- `common/cmm_cfg.c:1728,1761` enters the public PDMA/PSE recovery routines;
  their additional calls are the known PCI/watchdog paths listed in evidence
  561. No new direct C caller of either public reset function was found in the
  pinned MT7603 subtree.
- `os/linux/pci_main_dev.c:80-123` suspend checks the virtual-interface count,
  detaches/stops the netdevice, issues `RTMP_DRIVER_PCI_SUSPEND`, then calls
  `rt28xx_close` before disabling PCI and entering power state. Thus suspend
  removes the existing periodic retry source before the device is powered down.
- `os/linux/rt_main_dev.c:215-230` calls the `VOID` `RTMPDrvClose` and then
  returns success from `rt28xx_close`; `common/rtmp_init_inf.c:762-921` stops
  watchdog/timer/MLME activity and attempts `RT28xxPciAsicRadioOff`. In the
  legacy close, a failed radio-off is only logged, so the wrapper's zero return
  is not evidence that radio-off succeeded. The staged checked-close changes
  that local branch but remains unbound to this caller and does not prove the
  outer PCI/adapter lifetime contract.

This confirms a suspend hazard for the candidate: a reset left pending while
RTNL is busy can lose its only periodic executor immediately before PCI
power-down. Resume reopens the interface, but must preserve the pending state
and must not publish radio-ready until a real reset/bring-up verification path
succeeds. No source change is justified yet: the terminal teardown contract
and safe post-resume retry owner must be designed together.

## Adapter lifetime and deferred-worker requirements

The pinned removal path closes the other end of that lifecycle:

- `os/linux/pci_main_dev.c:386-429` removes the device by calling
  `RtmpPhyNetDevExit()` and then `RtmpRaDevCtrlExit()` before freeing the root
  netdevice.
- `common/rtmp_init.c:2431-2468` implements `RtmpRaDevCtrlExit()` and calls
  `RTMPFreeAdapter()`.
- `os/linux/rt_profile.c:1697+` frees adapter locks, task resources, timers,
  and ultimately the adapter allocation. The isolated adapter candidate adds
  its transition-lock free here but explicitly requires entry/work quiescence
  from callers and does not prove that precondition.
- The resume side is not a simple netdevice `ndo_open`: `pci_main_dev.c:149-230`
  restores PCI D0/state and enables the device, then (when virtual interfaces
  exist) attaches the netdevice, calls `rt28xx_open`, restores module/HNAT
  registration, calls `RTMP_DRIVER_PCI_RESUME`, and starts/wakes the queue.
  `rt28xx_open` initializes the radio/MBSS and calls `RTMPDrvOpen`; only a
  separate user netdevice open reaches `MainVirtualIF_open`. The current
  transition candidate is not bound to these PCI PM callbacks.

Therefore an independent retry executor cannot just be queued from the public
reset wrapper. Before this can be implemented, its ownership must establish all
of the following: work is initialized before any path that can free the
adapter; marking `retiring` prevents new enqueue; removal synchronously drains
or cancels the work before `RTMPFreeAdapter()` frees its state; worker RTNL
acquisition is nonblocking so cancellation under netdevice teardown cannot
deadlock; and suspend prevents hardware access after PCI power-down while
preserving pending reset until resume has restored power and the driver has
reinitialized. Resume must keep queues and BSS admission fail-closed until
pending recovery is complete and radio state is verified. Since current code
calls `netif_device_attach` before `rt28xx_open`, the integration must establish
whether attach can move later or whether transition gating must keep the device
unusable until verification. `rt28xx_open` alone is driver init, not radio
verification. The safe insertion point and rollback behavior for a failed
resume recovery still need source-level design. This ordering is not represented
by the current transition model or candidate hooks.

This follow-up also read pinned source blobs from the existing sparse checkout;
no new test, target build, CI run, or device command was needed or performed.

No production driver code, firmware image, router state or GitHub state changed.

## Isolated PM transition model — 2026-10-24

Updated the isolated candidate `tools/iot/radio-transition.h` and its host
fixture `tools/iot/check-radio-transition.c`; neither is installed into the
vendor driver. The model now has explicit `SUSPENDING` and `SUSPENDED` phases,
with three caller-driven transitions:

1. `wr_iot_radio_request_suspend()` advances the epoch, clears readiness,
   blocks ordinary admissions, and returns an in-flight reset ticket's kind to
   `reset_pending`. A PM-time reset request is latched for later rather than
   admitted to touch powered-down hardware.
2. `wr_iot_radio_suspend_complete()` refuses to mark the adapter suspended
   until no transition ticket is busy. It is a lifecycle marker, not proof that
   the legacy close callback powered RF off.
3. `wr_iot_radio_resume_unverified()` reopens only into `UNVERIFIED`; pending
   reset must run first, otherwise main-radio open/readback must establish
   verified READY before BSS admission. Late successful START/BSS/RESET
   completions across the suspend fence cannot publish READY.

The fixture now covers suspend during an admitted reset, reset coalescing while
suspended, suspend-time close preserving reset intent, late BSS-open completion,
resume verification, and suspend racing initial START. Local MinGW GCC strict
compile (`-std=c11 -Wall -Wextra -Werror -O2`) and the executable fixture both
passed. The exact CI sanitizer link could not run locally: this MinGW GCC lacks
`libasan` and `libubsan` (`ld: cannot find -lasan/-lubsan`). No local MIPS
cross-compiler was available, and CI was not started.

This is sequential state-machine evidence only. No locking/interleaving stress,
PCI/PM callback binding, queue gating, worker-liveness/teardown proof, target
driver compile, image, device operation, or runtime RF verification was done.
Production integration remains unsafe until those caller/lifetime guarantees
are implemented and checked together.

## PM callback synchronization and queue exposure — 2026-10-24

Inspected the pinned Linux/Padavan source at
`c25283e915a2a00a763774dd255b14aff997285e`:

- `drivers/base/power/main.c:1349-1468` takes `device_lock(dev)` around the
  suspend callback; `device_resume()` at `:735-813` does the same around resume.
  `drivers/pci/pci-driver.c:pci_legacy_suspend()` and
  `pci_legacy_resume()` call this driver's legacy PCI callbacks under that
  device-core path. Driver unbind/remove is also serialized by the device lock
  (`drivers/base/dd.c:634-686`). This gives PM/remove mutual exclusion for the
  device object, but does not itself drain an added adapter work item.
- `net/core/dev.c:1308-1313` and `:1381-1385` assert RTNL around ordinary
  `ndo_open`/`ndo_stop`. PCI PM code calls `rt28xx_close()` and `rt28xx_open()`
  directly (`drivers/net/wireless/mediatek/mt76x3/os/linux/pci_main_dev.c:123,
  209`), outside those net-core wrappers. New PM paths cannot assume RTNL is
  held merely because the netdev is being closed/opened.
- On resume, `pci_main_dev.c:207` calls `netif_device_attach()` before
  `rt28xx_open()` at `:209`. `net/core/dev.c:2420-2425` shows attach wakes all
  TX queues whenever the netdev is logically running. Consequently a queue may
  be woken before the driver's radio reinitialization. The later explicit
  `netif_start_queue()`/carrier/wake at `pci_main_dev.c:228-230` does not remove
  that earlier exposure. The candidate must either keep attach/Tx gated until
  recovery is verified or implement a proven equivalent transmit gate; the
  transition helper currently gates BSS open only, not packet transmit.

Design consequence: the retry worker must never wait on `device_lock`, and PM
must publish its suspend fence under the shared transition lock before draining
the worker. Release the short lock before any synchronous cancel/wait. Worker
RTNL acquisition must remain nonblocking; cancellation and teardown need to be
serialized against all enqueue paths. The `device_lock` observation narrows the
caller context but does not prove the adapter lock order, workqueue lifetime,
Tx gate, PM failure unwind, or resume readiness. No vendor source was edited in
this follow-up; no compile, CI or router operation was performed.

## All-interface transmit path during PCI suspend — 2026-10-24

Further pinned source inspection changes the TX requirement from a main-netdev
queue detail into an adapter-wide gate:

- `os/linux/rt_main_dev.c:374` assigns `rt28xx_send_packets` to the main
  interface. `ap/ap_mbss_inf.c:81` assigns it to MBSS; `ap/ap_apcli_inf.c:81`
  to AP client; `ap/ap_wds_inf.c:51` to WDS; and
  `os/linux/rt_profile.c:1494` to monitor. The pinned source thus shows a
  shared OS transmit hook for these interface families. The main hook has an
  `IKANOS_VX_1X0` override at `rt_main_dev.c:376`; confirm its effective board
  setting before calling the hook inventory exhaustive for the built image.
  MBSS and WDS start queues on virtual open (`ap/ap_mbss_inf.c:155`,
  `ap/ap_wds_inf.c:80`).
- `os/linux/rt_main_dev.c:517-539` checks only
  `RTMP_OS_NETDEV_STATE_RUNNING(ndev)` before packet handling. In the target
  Linux configuration, `include/os/rt_linux.h:1120` expands that check to
  `ndev->flags & IFF_UP`; it does not read the candidate PM transition state.
- `pci_main_dev.c:105-123` stops and detaches `net_dev` from PCI driver data,
  the main interface. It does not enumerate each MBSS netdev. The direct
  `rt28xx_close()` path calls `RTMPDrvClose()` but does not invoke each MBSS
  netdev's stop callbacks. `RTMPDrvClose()` calls `APShutdown()` and tears down
  the radio; `APShutdown()` itself does not stop MBSS netdev queues. The MBSS
  queue stops found in `ap/ap_mbss_inf.c:189` and `ap/ap_wds_inf.c:95` belong
  to their separate virtual close callbacks, not this direct PCI close call.

Therefore moving main `netif_device_attach()` later is necessary to remove its
early queue wake, but is insufficient to prove all virtual-interface TX is
fenced. At minimum the shared transmit entry must reject packets while PM is
SUSPENDING/SUSPENDED/UNVERIFIED or reset is pending, with an entry/lifetime
protocol that drains already admitted transmitters before `RTMPDrvClose()` and
PCI power-down. A simple readiness check followed by transmit has a race with
the PM fence. Check every interface family and teardown path before installing
such a guard; use the adapter-scoped lock only for short admission/counter
updates, never across packet transmit. The present candidate does not provide
that active-TX drain, so production PM integration remains blocked.

### Required ordering for a future PCI PM implementation

This is an implementation contract derived from the source paths above, not
an assertion that the current candidate implements it:

1. While the adapter lifetime and registered virtual netdev access are
   serialized by a proved lock/ref protocol that ends before unregister wait,
   publish `SUSPENDING` under the shared transition lock. The common OS TX
   entry must then refuse new packets for every interface family. Account for
   packets that crossed TX admission before this fence and wait for their
   driver entry to finish outside the short lock.
2. Quiesce/stop and detach each eligible netdev queue, not just the main one;
   prevent simultaneous virtual opens and new retry scheduling. Drain or
   synchronously cancel the reset retry owner before `RTMPDrvClose()` stops its
   MLME command worker. Do not hold the transition spinlock while waiting.
3. Use a close result that reports hardware failure. Only after checked close,
   TX drain and worker quiescence may the callback disable PCI and mark
   `SUSPENDED`. On any pre-power-down failure, keep the netdevs detached and
   state fail-closed; return a real error instead of the legacy close's zero.
4. Restore PCI power and initialize the driver while netdev queues remain
   unavailable. Process retained reset, perform radio readback, then publish
   READY and attach/wake the applicable interfaces. A failed open, reset or
   readback must retain `UNVERIFIED`/FAULT and detached queues and return a
   failure to the PCI PM core. Protect remove and adapter free by cancelling
   the owner before `RTMPFreeAdapter()` frees its lock and state.

Before coding this, prove the netdev enumeration/ownership across MBSS,
AP-client, WDS and monitor, the active-TX drain primitive and its lock order,
and the PCI suspend/resume error unwind. The current helper's `main_ready`
flag alone does not synchronize an in-flight call to `RTMPSendPackets`.

### Candidate interface registry coverage audit

The candidate registry is not yet a safe all-interface PM iterator.
`tools/iot/prepare-radio-adapter-candidate.py` allocates
`wr_iot_interface_refs[WDEV_NUM_MAX + 1]`, but
`tools/iot/prepare-radio-queue-candidate.py` binds
`wr_iot_netdev_attach_checked()` only to `ap/ap_mbss.c`. The registry's
`device` field is a raw pointer, and `interface-registry.h` explicitly makes
the caller responsible for pinning device/adapter lifetime and proving queued
callback quiescence before release. Neither file supplies an iteration API
that pins all published references. Thus the current registry cannot justify
stopping, detaching or later reattaching main, AP-client, WDS and monitor
netdevs during PCI PM, nor can it prove an MBSS pointer remains live after
the transition lock is released.

Before an all-interface suspend candidate, map each family to its exact
attach, unregister and free path in the pinned driver; bind registration and
retirement to every eligible interface; and define a snapshot whose lifetime
and lock order are proven against unregister. Do not carry an unbounded
`dev_hold()` across a teardown path that waits for all references. Keep the
snapshot protocol separate from the short IRQ transition lock and active-TX
drain. No production driver change or device test follows from this audit.

### Pinned virtual-netdev lifecycle map

Source revision: `c25283e915a2a00a763774dd255b14aff997285e` under
`trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/`.

| Family | Registration | Detach/free |
| --- | --- | --- |
| PCI main | `os/linux/pci_main_dev.c:334` | `pci_main_dev.c:401-429` via `RtmpPhyNetDevExit`, then root free |
| MBSS | `ap/ap_mbss.c:152` | `ap/ap_mbss.c:201-204` |
| AP-client | `ap/ap_apcli.c:3450` | `ap/ap_apcli.c:3468-3478` |
| WDS | `ap/ap_wds.c:1320` | `ap/ap_wds.c:1344-1352` |
| Monitor | `sniffer/sniffer_radiotap.c:462` | `sniffer/sniffer_radiotap.c:474-482` |

`os/linux/rt_linux.c:1619-1629` implements detach with
`unregister_netdevice()` followed by freeing the netdev-ops allocation;
`RtmpOSNetDevFree()` at `:1505-1510` calls `free_netdev()`. AP-client, WDS and
monitor attach calls do not inspect the attach result. In monitor creation,
failure of `rtmp_wdev_idx_reg()` frees `new_dev_p` at
`sniffer/sniffer_radiotap.c:446-450` while `wdev->if_dev` had already been set
at `:442`; the failure path does not clear that pointer. These are concrete
lifetime/error-path hazards for a PM iterator; a raw registry pointer cannot
be assumed live merely because its slot remains published.

Next integration work must first bind checked registration and removal to
every family, propagate attach failures through their callers, and establish
bounded snapshots that cannot outlive unregister. The main
netdev's PCI probe/remove order requires a separate proof; PCI PM must not
reuse remove semantics. This map is source evidence, not a production fix.

### Isolated monitor failure cleanup candidate

`tools/iot/prepare-monitor-lifetime-candidate.py` now stages a monitor-only
source transformation after checking the exact original Git blob
`be4871c082ab8d50c41bf3d1edf8f9f7d29ec340`. On failed wdev-index
registration it clears `wdev->if_dev` and frees both allocations. On failed
`RtmpOSNetDevAttach()` it unregisters the wdev index, frees both allocations,
clears the pointer and leaves `monitor_initiated` false. The second allocation
is `netdev_ops`: `os/linux/rt_linux.c:1548-1551` uses `vmalloc`, and
`RtmpOSNetDevFree()` at `:1505-1510` only calls `free_netdev`; hence the
candidate uses `vfree` on these unpublished failure paths. The successful
detach path already frees ops in `RtmpOSNetDevDetach()`.

The preparation was exercised on bytes extracted directly from the pinned
Git revision; exact-blob and anchor checks passed, and the transformed paths
were inspected. Python syntax compilation passed. This is an isolated source
candidate, not compiled as target C, installed in firmware or tested on a
router. AP-client, WDS and main lifecycle work remains. Do not claim PM
enumeration is safe from this single-path correction.

The monitor stage is now included in `prepare-radio-queue-candidate.py`.
Full bundle preparation passed from a separate exact Git archive made with
`core.autocrlf=false`; its staged manifest records the pinned blob and the
combined output contains `driver/sniffer/sniffer_radiotap.c`. A first attempt
using the Windows CRLF checkout/archive stopped at the pre-existing TxS blob
gate. Git archive inherited `core.autocrlf=true` there, so that failure did
not implicate the monitor transformation. The successful bundle is still a
partial candidate tree with `production_installed=false`; no target compiler,
CI, image or device validation was performed.

### AP-client and WDS registration failure candidate

`tools/iot/prepare-aux-netdev-lifetime-candidate.py` now stages exact-blob
transformations of pinned `ap/ap_apcli.c` (`10336b6b5f22209817035628a907cacb7a54b033`)
and `ap/ap_wds.c` (`e4dedddf254632b528b67f295b06635ec8b5f7b6`). At
index-registration failure, each path frees the separately `vmalloc`'d
`netdev_ops` before `free_netdev`, clears `wdev->if_dev`, then leaves the loop.
At netdev-attach failure, it additionally unregisters the assigned wdev index
before those frees. AP-client's `flg_apcli_init` now reflects whether any
earlier interface was successfully registered (`idx > 0`), allowing removal
of a partially created set while not claiming initialization when the first
interface failed. WDS already uses `index > 0` for that flag.

The stage was added to `prepare-radio-queue-candidate.py`; a complete
candidate preparation against the clean LF Git archive passed and its stage
manifest lists both output files with `production_installed=false`. Generated
failure paths were inspected. Python syntax and whitespace checks passed.
No target C compile, kernel registration fault injection, production-driver
installation, CI, image or router test was performed. Remaining lifetime
work includes the main/MBSS registration paths, a bounded all-interface PM
snapshot, and synchronization with unregister/free and TX drain.

### Refcount and main-open ordering correction

The earlier suggestion to hold `dev_hold()` across all PM work is too broad.
In pinned Linux 4.4.198, `include/linux/netdevice.h:3164-3177` implements
`dev_put`/`dev_hold`; `net/core/dev.c:7094-7146` calls
`netdev_wait_allrefs()` at `:7126` during the unregister todo phase. The
vendor `RtmpOSNetDevProtect()` uses RTNL (`os/linux/rt_linux.c:1633-1639`),
and `RtmpOSNetDevDetach()` calls `unregister_netdevice()` at `:1625`.
Holding a PM reference while waiting for that detach's RTNL unlock/todo
completion can therefore deadlock: unregister waits for the reference that
the PM path has not released. Any snapshot must be bounded, with a proven
release point before unregister waits, or be protected by a demonstrated
serialization order that avoids such a wait cycle.

The source call graph also shows virtual creation occurs inside
`rt28xx_open()` at `os/linux/rt_main_dev.c:309-330`, not in
`RtmpPhyNetDevInit()`. The latter is called from PCI probe at
`pci_main_dev.c:320`, whereas PCI resume directly calls `rt28xx_open()` at
`:209`, without the ordinary netdev `ndo_open` RTNL wrapper. MBSS, WDS,
AP-client and monitor initialization may therefore be reached by the direct
resume path; existing initialized flags can suppress repeat creation, but a
partial or failed earlier initialization needs explicit treatment. Their
remove wrappers are reached from `RtmpPhyNetDevExit()` during PCI remove
(`rt_main_dev.c:729-764`), which the device core serializes with PM under
`device_lock`. This remove serialization does not itself serialize an
ordinary main netdev open against PCI PM.

Next candidate design: publish the adapter PM fence first; serialize any
virtual registration/retirement with it; establish an RTNL/adapter-lock order
for a short all-netdev queue pass; and release any netdev references before
the unregister todo phase. Separately drain active packet transmitters before
hardware close. Do not infer that a `dev_hold` alone is a safe PM protocol.

### Candidate TX admission counter

`tools/iot/radio-transition.h` now has a short-lock `active_tx` lease. TX
entry is refused outside verified READY, during PM/retirement/reset intent,
or while an exclusive radio operation is active. Suspend publishes its PM
fence before waiting; `wr_iot_radio_suspend_complete()` refuses completion
until all admitted TX calls retire. CLOSE, RESET and BSS_CLOSE ticket admission
also refuses while TX is active. A future wrapper must call `tx_enter` and
`tx_leave` under the same adapter lock around *every* `rt28xx_send_packets`
path and wake the PM waiter after the last lease exits. The short lock must
never span `rt28xx_packet_xmit()` or a wait. This counter counts driver entry
calls, not DMA completion or hardware TX retirement.

The sequential host fixture `tools/iot/check-radio-transition.c` now covers
two in-flight TX calls across suspend, refusal of new TX, last-TX completion,
resume remaining UNVERIFIED, close waiting for an admitted TX, and reset
intent waiting for a TX lease. MinGW GCC strict C11
`-Wall -Wextra -Werror -O2` compile and fixture execution passed. This model
still has no kernel wakeup, no all-netdev queue pass, and no proof that
adapter/free waits for the last TX. It is not installed or target-compiled.

The source-pinned adapter stage now wraps the actual common
`rt28xx_send_packets()` in its candidate `os/linux/rt_main_dev.c`. It gets
the adapter from the netdev, takes a TX lease under the shared adapter lock,
rejects an inadmissible packet with the existing release convention, and
returns the lease after `rt28xx_packet_xmit()` returns. The lock is never held
across packet transmit. The extracted generated function was compiled with a
host fixture that checks READY acceptance, PM/UNVERIFIED refusal, packet
release, lease balance and unlocked driver call; strict MinGW GCC C11
`-Wall -Wextra -Werror -O2` execution passed. The complete candidate bundle
also prepared successfully from the exact LF source. This closes the
candidate's common-entry hook gap. The adapter candidate now also allocates
and initializes `wr_iot_tx_drain_wait`; the last TX lease wakes that queue
after releasing the short lock. The extracted TX fixture asserts exactly one
wakeup for an accepted packet and none on a rejected packet; strict host C11
compilation and the full exact-LF bundle preparation passed after this change.
No PCI PM waiter is wired to this queue yet. Its wait predicate, timeout,
unwind and adapter-free synchronization must be reviewed together with PM
binding; target C build and hardware/DMA evidence remain absent.

PCI suspend ordering was rechecked against pinned `os/linux/pci_main_dev.c`:
after stopping and detaching only the main netdev, it calls
`RTMP_DRIVER_PCI_SUSPEND`, then `rt28xx_close`, then proceeds to
`pci_disable_device` and `pci_set_power_state`. The legacy close returns
zero even after calling the void `RTMPDrvClose` (`os/linux/rt_main_dev.c`),
so the callback has no reliable close-failure result. A bounded TX waiter
must be inserted after an atomic PM admission fence and before physical
close/power-down. On timeout or failed close, the callback must avoid PCI
power-down and unwind detached queues/state without reopening admissions
prematurely. Do not wire a waiter alone into this path: that would leave
failure handling and secondary-interface queue ordering unresolved. The
candidate manifest now accurately records the staged last-TX wakeup while
keeping `pm_waiter_bound=false` and `tx_dma_drain_proven=false`.

The transition model now has `wr_iot_radio_abort_suspend()` for a failed
pre-close attempt. It clears the PM marker only when there is no admitted
exclusive operation, leaves the phase UNVERIFIED and readiness false, and
preserves reset intent. An active TX lease may still retire afterward, but
new TX and BSS admission remain closed. The strict C11 host fixture passed
TX-timeout-like and reset-pending abort cases. Full exact-LF candidate bundle
preparation passed. This does not bind the PCI callback: when an exclusive
operation remains busy, abort is refused and its completion must be joined
first; queue restoration and physical-close failure handling are still open.

A follow-up admission review found that after a pre-close PM abort, a TX lease
could still be active while the phase was UNVERIFIED. The old model rejected
new TX but allowed `VERIFY` or `MAIN_OPEN` to begin, so an observed readback
could race the prior TX call. `wr_iot_radio_begin()` now refuses every new
radio operation while `active_tx` is nonzero. The strict C11 fixture checks
both refusals, then permits VERIFY only after the last lease retires. This is
still a sequential host model; it does not prove DMA retirement, kernel
memory ordering, netdev lifetime or PCI PM callback integration.

The exact-source adapter stage now includes `wr_iot_wait_tx_idle()` as an
unbound process-context helper. Its predicate reads `active_tx` under the
same adapter spinlock as the OS TX lease; `wait_event_timeout` runs only after
that lock is released. It returns success for an idle adapter, failure for a
zero timeout with active TX or for an expired wait, and success after the
last lease leaves and wakes the queue. Generated host fixture passed strict
MinGW C11 `-Wall -Wextra -Werror -O2`; full exact-LF bundle preparation and
Python syntax passed. The manifest distinguishes `pm_wait_helper_staged=true`
from `pm_waiter_bound=false`. This is a driver-entry drain, not DMA or RF
quiescence. Caller lifetime, PM admission fence, exclusive-ticket joining,
secondary netdev queue ordering, timeout unwind and physical-close result
remain prerequisites before a PCI callback can call this helper.

Pinned `include/rt_os_net.h` maps `RTMP_DRIVER_PCI_SUSPEND` to an ioctl;
`common/cmm_cfg.c` sets `fRTMP_ADAPTER_HALT_IN_PROGRESS` and
`fRTMP_ADAPTER_RADIO_OFF`, while its RESUME counterpart clears both. The
current `rt_pci_suspend` sets those flags before legacy void-result close.
Consequently, a pre-close TX timeout unwind must reconcile vendor flags as
well as the transition model and all affected queues; calling only
`wr_iot_radio_abort_suspend()` would leave a mismatched adapter. The staged
`wr_iot_rt28xx_close_checked()` instead requires a live CLOSE ticket and
propagates checked-close failure, but PCI PM has no such bound ticket yet.
Its host fixture now uses an actual admitted CLOSE ticket and rejects a
stale serial, then checks failure and one-time notification. Strict C11
compile/execution passed. This remains injected behavior, not target-driver
or hardware proof.

The transition model now distinguishes an unmutated pre-close PM timeout
from a partially executed suspend. `wr_iot_radio_abort_suspend_unmutated()`
may restore the prior READY state even while an old TX lease is completing,
but only if the caller proves no queue, vendor flag or hardware mutation has
occurred and no reset, close or exclusive radio operation intervened. It
refuses a prior UNVERIFIED phase or new reset intent. Once any such mutation
has occurred, only the fail-closed UNVERIFIED abort path is eligible. The
strict host C11 fixture covers the READY rollback with active TX, reset
refusal and UNVERIFIED refusal; full exact-LF candidate assembly passed.
This is a model contract, not a PCI callback binding or MIPS build.

The PCI/AP attach map has been staged consistently: main PCI probe, MBSS,
AP-client, WDS and monitor now call the same `wr_iot_netdev_attach_checked()`
candidate. The pinned source has exactly these five PCI/AP call sites;
`sdio_main_dev.c` is a separate SDIO path and is outside the WR1200JS PCI
candidate. The wrapper records an interface before kernel publication and
releases its record on attach failure. Its host registration fixture passed
strict C11, and the complete exact-LF candidate assembly produced all five
wrapped sites. This does **not** turn the registry into a safe PM iterator:
successful unregister/detach is not yet bound to registry retirement, and
raw device pointers cannot be dereferenced after their netdev lifetime ends.
`VirtualIfCnt` is only an aggregate count (`common/cmm_cfg.c` ioctl case),
not an enumeration of queue owners. PM queue traversal and referenced
snapshot lifetime therefore remain open.

Dynamic removal is broader than PCI teardown: pinned ioctl dispatch can call
`MBSS_Remove` and `ApCli_Remove` from `ap/ap_cfg.c`, and `Monitor_Remove` and
`WDS_Remove` from `common/cmm_cfg.c`. Each removal unregisters its netdev
under RTNL and then frees it. Thus PCI `device_lock` serialization against
PCI remove alone cannot protect a PM snapshot. The candidate attach bridge
now rejects new registration during PM/retirement and counts an attach from
record allocation through publication or rollback. Its final completion
wakes an adapter-owned registration waitqueue after dropping the spinlock.
An unbound bounded wait helper reads that counter under the same lock. Host
fixtures passed for in-flight visibility, PM fence during attach, rejection
of a subsequent attach, immediate idle and timeout; full exact-LF bundle
preparation passed. The PM callback still does not wait on the counter, and
dynamic removal has no matching registry retirement or short referenced
snapshot. Do not dereference registry entries in PCI PM yet.

An isolated `wr_iot_registry_snapshot()` model now selects only published,
non-removing records while the caller holds the common adapter lock. Its
callback is intended for a nonblocking `dev_hold` at kernel binding; the
caller must perform queue actions and `dev_put` every pin promptly, before
any RTNL wait, unregister wait or physical close. The strict C11 fixture
checks unpublished exclusion, remove exclusion, capacity refusal and balanced
pins; full exact-LF candidate preparation includes the helper. This does not
yet bind dynamic remove intent before `unregister_netdevice`, nor prove that
all producers and callbacks are quiescent. There is no PM use of these raw
records, no actual `dev_hold/dev_put` binding and no target compile.

Dynamic virtual removal now has an isolated admission marker. The staged
MBSS, AP-client, WDS and monitor remove paths call
`wr_iot_netdev_mark_removing()` under the adapter lock before acquiring RTNL
and invoking `RtmpOSNetDevDetach`; if no published, unmarked record exists,
they refuse to free that netdev. A marked record is excluded from the short
snapshot. The host registration fixture verifies first mark, repeat refusal
and snapshot exclusion; exact-LF full candidate assembly passed. This is
still incomplete for production: after unregister the record remains a
non-reusable tombstone because vendor callback quiescence and registry release
are not proved. Repeated dynamic reconfiguration could exhaust slots, so do
not install this stage until a complete release protocol is verified. Main
PCI removal is separately fenced by adapter retirement, but its registry
release also remains unbound. No MIPS compile or device test occurred.

The adapter candidate now binds the short snapshot to kernel `dev_hold` and
`dev_put` for a dedicated `wr_iot_stop_registered_queues()` helper. It
requires a published PM fence and zero in-flight registrations, takes pins
under the adapter lock, stops each selected queue outside the lock, and drops
all pins before returning. It does not acquire RTNL or wait while pins are
held. The generated host fixture checks admission refusal without PM,
refusal while registration is active, one published queue stop and balanced
pins; strict C11 compile/execution and full exact-LF candidate preparation
passed. This is still an unbound helper: PCI suspend does not call it, queue
restoration on failed suspend is absent, and dynamic removal's vendor
quiescence/slot release remains unresolved. Kernel target compilation and
runtime ordering are not established by the host fixture.

### Main PCI attach failure path

Pinned `os/linux/pci_main_dev.c:327` stores the newly allocated main netdev
in PCI driver data before calling `RtmpOSNetDevAttach()` at `:334`. On an
attach failure the original `err_out_free_netdev` at `:362-363` calls only
`RtmpOSNetDevFree()`. Since `netdev_ops` was separately allocated with
`vmalloc`, that path leaks ops and leaves PCI driver data pointing to freed
storage. `tools/iot/prepare-pci-probe-lifetime-candidate.py` stages a
source-pinned correction (original blob
`eb1118e720e49741261314226a5cc9f9f6ede150`) that clears driver data and
frees ops before freeing the unregistered netdev. The candidate is included
in the full IoT bundle; exact LF-source preparation passed and the stage
manifest records `production_installed=false`.

The existing MBSS initialization candidate already checks attach failure,
unregisters its acquired wdev index, clears `if_dev`, reduces `BssidNum`, and
frees unregistered netdev plus ops. Its host fixture injects a failed attach,
but kernel/netdev reference lifetime remains unproved. The new PCI stage was
not compiled as target C or fault-injected in a running kernel. Main and
virtual cleanup candidates reduce known failure leaks; they do not yet supply
safe all-interface PM enumeration, a TX drain, or a production backend.

### PCI suspend HALT ownership in the isolated checked close

Pinned `include/rt_os_net.h` dispatches PCI suspend to the vendor ioctl, which
sets `fRTMP_ADAPTER_HALT_IN_PROGRESS` and `fRTMP_ADAPTER_RADIO_OFF`. Pinned
`common/rtmp_init_inf.c:969` then clears HALT unconditionally at the end of
legacy `RTMPDrvClose`, including the suspend path. The isolated checked-close
stage now reads `pm_suspending` under the transition lock and preserves HALT
while PCI suspend owns it. Ordinary checked close still clears HALT. Radio-off
failure returns before the clear and retains the uncertain stage. This does
not change the production legacy close or bind the PCI PM callback.

The full exact-LF candidate assembly passed. Extracted checked-close and
complete virtual-down-chain fixtures both compiled with MinGW `-std=c11
-Wall -Wextra -Werror` and ran successfully. The checked-close fixture now
asserts ordinary HALT clearing and PCI-suspend HALT retention. These are
injected host primitives, not a MIPS build or router test. Next, stage and
review the PCI callback's bounded registration/TX drain and failure unwind;
do not power down PCI on any unverified close result.

### Failure after requesting physical close

The transition model exposed another suspend gap: a failed CLOSE finishes in
`WR_RADIO_CLOSING` with no busy ticket. Previously `suspend_complete()` could
accept that state and `abort_suspend()` refused it, leaving no safe callback
result. `suspend_complete()` now rejects CLOSING; once the CLOSE ticket has
retired, `abort_suspend()` accepts either CLOSING or DOWN and lands in
UNVERIFIED without reopening TX/BSS admission. DOWN covers a successful close
followed by a later PCI suspend failure. Active ticket refusal remains in
place. The strict MinGW C11 transition test covers both failure points and
passed; full exact-LF candidate assembly also passed. These tests exercise a
sequential model and staged source only. A PCI callback still has to restore
PCI availability, vendor flags and netdev queues, or retain a detached
fail-closed state, before returning a real suspend error.

### MBSS removal fence before beacon storage teardown

The staged `MBSS_Remove` had `wdev_bcn_buf_deinit()` before
`wr_iot_netdev_mark_removing()`. A concurrent PM snapshot could therefore
still select a published netdev while its beacon storage was being destroyed.
The candidate assembler now marks a present MBSS netdev as removing before
beacon deinitialization, then performs RTNL unregister and vendor wdev cleanup.
The no-netdev path still deinitializes the beacon buffer. Exact-LF full bundle
assembly passed; generated-source order was checked as `mark < deinit <
unregister`. This is ordering evidence, not a concurrent kernel test.

The registry record still cannot be released after unregister: the candidate
has no proof that all vendor callbacks/queued references have retired. Reusing
the slot on the strength of `unregister_netdevice()` alone would be unsafe.
Repeated dynamic removal/recreation remains a production blocker; do not
install this registry until the post-unregister quiescence and slot-release
path is completed and target-verified.

### Dynamic removal review: beacon deinit result is not consumed

The staged AP-client, WDS and monitor removal paths mark `removing` before
their first unregister/teardown operation. The MBSS mark was moved before
beacon deinit in the previous step. Further pinned-source review changes the
next gate: `tx_rx/wdev.c::wdev_bcn_buf_deinit()` returns `FALSE` without
freeing `BeaconPkt` when `bcn_state != BCN_TX_IDLE`. `ap/ap_mbss.c::MBSS_Remove()`
ignores that result and continues to `RtmpOSNetDevDetach()`, wdev index
unregister and netdev free. `MBSS_VirtualIF_Close()` and `MBSS_Close()` stop
the queue/disable BSS beacon request but contain no unconditional transition
of `bcn_state` to IDLE. The separate AP stop path has IDLE writers; it cannot
be assumed to run or finish for every dynamic MBSS removal.

Therefore a successful unregister alone is neither proof of beacon-packet
retirement nor permission to release the registry record. Before binding
dynamic release, make the MBSS close/deinit result mandatory, prove DMA/TxS
and vendor callback quiescence, and provide a retry/fail-closed path when
deinit refuses. This is source evidence only; no driver, image or router was
modified by this review.

### Conditional removal cancellation and error propagation boundary

The isolated registry now has `wr_iot_registry_cancel_remove_unmutated()`.
Under the shared adapter lock it refuses a wrong generation, PM/retirement,
an unpublished or already advanced removal, and clears `removing` only when
the caller proves no unregister, beacon free or vendor mutation occurred.
The strict MinGW C11 registry fixture covers these refusals and a permitted
retry; full exact-LF candidate preparation passed. No driver removal call
uses this primitive yet, so it is not a completed retry path.

The actual failure chain is broader than `MBSS_Remove()`: `ap/ap_cfg.c`
dispatches it without checking a result; `RT28xx_MBSS_Remove()` is `VOID` and
ignores the ioctl status; `RtmpPhyNetDevExit()` returns `BOOLEAN` but does not
inspect the MBSS wrapper; PCI `rt_pci_remove()` ignores that BOOLEAN before
adapter/netdev teardown. A local deinit check without propagation through
these boundaries could still free the adapter around a retained MBSS. The
next binding must make removal outcome mandatory across the PCI path and
provide an explicit fail-closed lifetime plan; merely canceling a registry
mark or skipping one netdev free is insufficient.

### Adapter-locked cancellation bridge

The staged `wr_iot_netdev_cancel_removing_unmutated()` now looks up the
registered netdev and checks the radio PM/retiring flags under the same
adapter transition lock before calling the registry cancellation primitive.
Its caller must still prove the attempted removal made no vendor/kernel
mutation. The strict MinGW C11 registration fixture passed cancellation
refusal during suspend, permitted cancellation after an unmutated abort, and
refusal after the kernel-removal stage advanced. Full exact-LF candidate
assembly passed. MBSS removal does not yet invoke this helper; callback
quiescence, end-to-end error propagation and target compilation remain open.

### Checked MBSS leaf, 2026-10-24

The isolated candidate changes `MBSS_Remove` to return a status, checks
`wdev_bcn_buf_deinit()` before unregistering the netdev, and cancels only an
unmutated removal mark on refusal. The ap_cfg ioctl path checks that result.
The extracted strict C11 MinGW fixture and full exact-LF candidate assembly
passed. The VOID `RT28xx_MBSS_Remove` wrapper and later PCI teardown still
discard failure. This is not production-safe removal, a target build, or
on-device evidence.

### Exact pinned-source teardown boundary

Reviewed the pinned MT76x3 source at
`iot-pinned-mt76x3-c25283e/mt76x3` on 2026-10-24. Its
`ap/ap_mbss_inf.c` declares `RT28xx_MBSS_Remove` as `VOID`, and
`include/rt_os_net.h` exposes the same signature. In
`os/linux/rt_main_dev.c`, `RtmpPhyNetDevExit` calls the wrapper without a
result, then detaches the main netdev and returns `TRUE`. In
`os/linux/pci_main_dev.c`, `rt_pci_remove` ignores that return and proceeds
to `RtmpRaDevCtrlExit`, CSR unmap, resource release and root netdev free.
The staged checked leaf therefore cannot prevent adapter destruction.
Before binding, the removal contract must cover every child interface and
PCI teardown outcome: either prove retirement cannot fail after the point
of no return, or retain the adapter and resources on failure with a defined
retry and device-removal lifetime. Merely returning `FALSE` from the leaf
would leave a registered child referencing freed adapter state. No source
change to these production callers was made in this review.

### Isolated wrapper and physical-exit propagation

The candidate assembler now stages `RT28xx_MBSS_Remove` as `INT`, returns
the AP ioctl result, updates its OS header declaration, and makes
`RtmpPhyNetDevExit` return `FALSE` before main-netdev detach when MBSS
removal fails. `python -m py_compile` and full exact-LF candidate assembly
passed; generated signatures/call sites were inspected. This is partial
propagation only: PCI `rt_pci_remove` still ignores the BOOLEAN result and
frees the adapter. Other child-interface remove functions remain unchecked.
The generated bundle is isolated; no production driver, image or router was
changed. Next, design and verify a PCI-safe teardown ownership rule across
all child interfaces before binding or claiming failure recovery.

### Two-BSS partial-removal retry reproduction

Extended the extracted strict C11 host fixture to create two virtual BSS.
When beacon deinit refuses the second BSS, the current candidate has already
detached and freed the first. A retry calls beacon deinit for the first BSS
again, even though its netdev pointer is NULL. The fixture checks both the
partial state and the repeated call; it passed with MinGW GCC
`-std=c11 -Wall -Wextra -Werror`. This is evidence of an unsafe retry shape,
not a successful recovery test. Before any production binding, a common
transition owner must prevent new open/reset activity and establish a
per-BSS retirement state that cannot repeat destructive steps. All-child
preflight and the irreversible teardown boundary must be reviewed together.

### Other child removal signatures

The same pinned source uses `VOID` removal wrappers for AP-client
(`ap/ap_apcli_inf.c`), WDS (`ap/ap_wds_inf.c`) and monitor
(`os/linux/rt_profile.c`). Their source removal paths detach and free child
netdevs. `RtmpPhyNetDevExit` calls AP-client and WDS before MBSS, monitor
after it. Consequently a failed MBSS teardown may follow earlier child
destruction, and a `FALSE` return before monitor removal leaves a mixed
adapter state. Per-BSS retry handling alone cannot make PCI removal safe.
The candidate must eventually model a single all-child removal transaction
with explicit ownership and irreversible milestones; this source review did
not install or exercise that transaction.

### All-child teardown state model

Added an isolated, unbound state model in `tools/iot/all-child-teardown.h`
for AP-client, WDS, MBSS and monitor. It requires a common admissions fence,
records completed child families once, permits abort only when the caller
proves no mutation, and poisons a partially completed failed transaction.
Adapter release additionally requires caller-proven quiescence; the model
cannot itself prove DMA, callbacks or vendor worker retirement. The strict
MinGW C11 fixture in `tools/iot/check-all-child-teardown.c` passed success,
partial failure, retry refusal, unmutated abort, duplicate completion and
empty-child cases. The candidate assembler hashes these model inputs for
provenance but does not bind the model into driver or PCI remove. Per-BSS
milestones and all actual child-wrapper results remain pending.

### Per-BSS retirement milestones

Added an isolated `tools/iot/mbss-retirement.h` model keyed by a caller-
provided generation. Each BSS must progress through removal intent, proven
beacon deinit, kernel netdev retirement and vendor callback quiescence.
Retries can identify a BSS whose beacon step is already complete and must
not repeat it. The all-child fixture now requires both modeled BSS to reach
vendor-done before accepting MBSS-family completion. Strict MinGW C11 tests
for both models passed, as did Python syntax and exact-LF candidate assembly.
The assembler only hashes these model inputs; it does not bind them into the
vendor driver. Real callback retirement, generation assignment, multi-BSS
failure unwind and PCI lifetime still require implementation and target
verification. The two-BSS extracted vendor fixture continues to document
the existing repeated-deinit defect.

### Adapter-owned model storage in isolated candidate

The adapter candidate now includes the all-child and per-BSS model headers,
owns `wr_iot_children` and `wr_iot_mbss[WDEV_NUM_MAX]`, and initializes them
before publishing the adapter. The full exact-LF assembler and Python syntax
check passed; the generated `rtmp.h`, `rtmp_init.c` and copied headers were
inspected. This is storage only. No MBSS/AP-client/WDS/monitor event updates
these fields yet; no callback quiescence, target compilation or PCI lifetime
proof follows from their presence.

### MBSS generation bound before netdev publication

Source review found that the earlier radio-error stage already checks MBSS
attach failure and clears the failed wdev; no duplicate cleanup was added.
The shared candidate attach bridge now recognizes `INT_MBSSID`, checks its
BSS index, and publishes the per-BSS generation under the adapter lock
before calling `RtmpOSNetDevAttach`. On attach failure, it releases the
unpublished registry record and resets only the matching LIVE BSS state.
The strict C11 registration fixture passed failed attach, successful attach,
generation match and duplicate-slot refusal. Full exact-LF candidate assembly
passed and the generated MBSS call and bridge include were inspected. This
does not yet advance removal milestones or prove PM/attach interleaving safe.

### PM fence during MBSS registration

The strict registration fixture now injects a PM suspend request while the
MBSS OS attach is in progress. The bridge completes with matching generation,
LIVE BSS state and zero in-flight registrations; subsequent attach is refused.
MinGW C11 with `-Wall -Wextra -Werror` passed. This confirms only the bridge
side of the race. Pinned `rt_pci_suspend()` still stops/detaches the main
netdev and closes the radio without calling the staged registration wait.
Therefore the real PM callback must publish its fence, wait for in-flight
registrations and then snapshot/stop all published interfaces before closing
hardware. The wait must occur outside the adapter spinlock with a bounded
failure unwind. No PCI PM binding or target/runtime test was made here.

### Isolated PCI suspend registration barrier

The isolated assembler now stages a common-lock PM admission fence in
`rt_pci_suspend`, followed by a bounded two-second registration wait outside
the lock. Timeout attempts unmutated abort and returns `-EBUSY` before
carrier, queue, vendor or hardware mutation; an unsuccessful abort leaves
admission closed. Python syntax and full exact-LF assembly passed. Inspection
of generated PCI source places the fence/wait before `netif_carrier_off`,
`netif_stop_queue` and `rt28xx_close`. This is only the initial PM barrier:
active TX, all-interface queue stop, radio close result, suspend-complete,
resume verification and PCI power failure unwind remain unbound/unproved.
No target compile, firmware install or router operation was performed.

### Extracted PCI PM barrier host test

The generated PCI suspend fence was extracted into a host fixture from the
actual assembled candidate, not retyped in the test. Strict MinGW GCC C11
with `-Wall -Wextra -Werror` passed the success path, registration timeout
before any modeled mutation, and reset arriving during the wait (abort must
not reopen admission). Python syntax and full exact-LF assembly also passed.
No local MIPS toolchain was found; the available `wsl.exe` did not list a
usable distribution in this session. This test covers the pre-mutation
control flow only and cannot establish kernel compilation, TX/DMA drain,
radio close, PCI power unwind or router behavior.

### MBSS removal intent and beacon milestone binding

The isolated MBSS removal path now enters through a generation-matched
`wr_iot_mbss_begin_remove` under the common adapter lock. It rejects PM
suspend and requires either physical retirement or an admitted BSS-close
transition. A failed beacon deinit attempts an unmutated rollback under that
same lock; successful deinit records the beacon milestone before netdev
detach. The strict registration fixture tested begin, duplicate begin,
unmutated cancel and refusal to cancel after beacon completion. The exact
MBSS function was extracted from the assembled candidate and passed strict
MinGW C11 refusal/success tests. Python syntax and full assembly passed.
The path still does not record kernel/vendor completion, and a failed later
step can leave partial removal; the two-BSS diagnostic still demonstrates
repeat-deinit on retry. No production or target runtime claim follows.

### Two-BSS repeat-deinit avoided in isolated candidate

Pinned MBSS init creates beacon storage only after successful netdev attach.
The staged removal loop now skips a BSS whose `if_dev` is already NULL, so a
second-BSS refusal followed by retry does not deinitialize the first BSS
again. The exact generated MBSS function was extracted; the strict C11
two-BSS fixture now asserts only one deinit on retry and passed. Full exact-LF
assembly and Python syntax passed. This fixes that single reproduced repeat
operation in the candidate; it does not make all-child teardown atomic.
Kernel/vendor-done milestones were deliberately not marked: the registry
requires IDLE and independently proven callback quiescence, neither of which
is established by `RtmpOSNetDevDetach` alone. PCI remove still ignores
physical-exit failure; target compilation and router runtime remain open.

### MBSS remove admission requires an idle reference

The staged checked MBSS close helper can consume a reference only after its
DOWN operation succeeds, but it is not yet the driver's `ndo_stop` binding.
`RtmpOSNetDevDetach` is therefore not evidence that an owned/open reference
has retired. The generation-matched remove-begin helper now refuses a
non-IDLE interface reference or an active OS TX entry under the common lock.
Strict C11 fixture cases for OWNED and active-TX refusal passed, as did full
exact-LF candidate assembly. This gate deliberately prevents unsafe removal;
it does not by itself make open BSS removable. Checked close binding, DMA/
callback quiescence, kernel/vendor milestones and PCI ownership remain open.
