# WR1200JS IoT v43: MBSS global preflight candidate — 2026-10-27

Source: local isolated v42 driver prepared from pinned Padavan
`c25283e915a2a00a763774dd255b14aff997285e`.

`tools/iot/prepare-mbss-global-preflight.py` creates a **new isolated**
candidate tree. It injects a check at the start of `MBSS_Remove()`, before the
first beacon or child netdev is freed. Under the shared transition lock, the
check requires radio retirement, no registration in progress, no active TX,
matching non-null child netdev count and published MBSS registry count, every
acquired MBSS at checked DOWN stage 4, and a PCI work-joined receipt. The
receipt is initialized false and has **no producer** yet; the candidate cannot
pass real PCI removal until a reviewed owner binds that receipt.

Verification performed locally:

1. The preparation script succeeded against the isolated v42 tree and wrote a
   manifest with hashes of the five changed/generated driver files. The
   resulting source places declarations before the new preflight call.
2. `check-mbss-global-preflight.c` compiled and executed with host GCC C11,
   `-Wall -Wextra -Werror -pedantic`. It rejects live/closing references,
   incomplete checked DOWN, mismatched counts, unjoined work, in-flight
   registration/TX, non-retiring radio and unknown ownership.
3. `prepare-mbss-global-preflight-check.py` extracted the **generated driver
   source** into an injected host fixture. That fixture compiled and ran with
   the same strict flags. With two BSS, an open or incompletely closed second
   BSS causes `MBSS_Remove()` to fail before *any* remove, beacon deinit,
   detach or free call; both closed BSS pass the injected success path.

Limits: this is not installed in the ordinary image, not MIPS-compiled, and
not exercised on the router. The preflight cannot make an already-started
removal failure atomic, and it does not solve `rt_pci_remove()` ignoring child
exit failure before freeing adapter/MMIO. The PCI owner must set the work
receipt only after all close/recovery owners join outside locks and RTNL,
then handle every terminal failure without unsafe free. It must also fence
the pre-registration construction window before treating the netdev count as
stable. Only after those bindings, target compilation and fault injection can
this become a production release gate.

## Construction-window follow-up

The source review found `MBSS_Init()` stores `wdev.if_dev` before its call to
`wr_iot_netdev_attach_checked()` increments the existing registration counter.
The isolated candidate now acquires a construction lease under
`wr_iot_transition_lock` before that first store, increments the same
registration-inflight count and releases it on every normal/early exit. The
lease refuses retirement/PM overlap and concurrent MBSS construction. The
preflight also rejects an active lease. The generated source contains the
begin call at `MBSS_Init` entry and the end call at its common exit.

The host helper fixture verifies lease acquisition, duplicate refusal,
retirement overlap refusal, count release and wakeup. The generated-source
fixture still verifies only the preflight and `MBSS_Remove()` body; it does
not execute the full vendor `MBSS_Init()`. Both strict host fixtures passed.
No target compile or device test establishes this follow-up yet.

## Adapter removal ordering review

The v43 preflight is intentionally narrower than a complete PCI removal
transaction. In `RtmpPhyNetDevExit()`, APCLI and WDS removal are attempted
before MBSS; a later MBSS failure can therefore follow earlier family
mutation. More critically, `rt_pci_remove()` ignores the Boolean result from
`RtmpPhyNetDevExit()` and unconditionally continues to `RtmpRaDevCtrlExit()`,
CSR unmap/resource release, and root netdev free. The current candidate does
not bind `wr_iot_pci_work_joined`, so it cannot make this path safe.

`RtmpOSNetDevProtect()` only wraps each individual `unregister_netdevice()`
with RTNL. It does not hold a continuous adapter-lifetime boundary across the
whole remove callback. Any deferred owner must acquire and retain adapter and
netdev lifetime before returning from `ndo_stop`, and PCI teardown must join
that owner outside RTNL before any adapter/MMIO release. The required next
design is an adapter-wide two-phase close across APCLI, WDS, MBSS and monitor:
admit/fence and snapshot all children first; drive checked DOWN and join their
owners; then mutate/free family structures only after the complete preflight
passes. The terminal failure policy remains unresolved because PCI `remove`
returns `void`; no candidate is production-ready until that policy preserves
all owners safely without leaving untracked registered devices or freeing a
live adapter.

### Terminal PCI-removal constraint

Linux `pci_driver.remove` is a `void` callback. In this candidate source,
`rt_pci_remove()` calls `RtmpPhyNetDevExit()` without checking its Boolean result,
then proceeds to `RtmpRaDevCtrlExit()`, CSR unmap/resource release and root
netdev free. Returning early on a child-close error cannot veto removal. Upstream Linux v4.4
`pci_device_remove()` invokes the PCI driver callback and then continues PCI
cleanup and clears the driver binding; the callback return is not a retry or
rollback mechanism. See [the v4.4 PCI core source](https://github.com/torvalds/linux/blob/v4.4/drivers/pci/pci-driver.c#L2895-L2919).

The normal `RTMPDrvClose()` sequence synchronously disables RX/TX and interrupts,
requests PCI radio-off, releases IRQ via `synchronize_irq()`/`free_irq()`, then
frees or resets DMA rings. It is `void` and provides no checked, adapter-wide
completion receipt. The isolated `wr_iot_drv_close_checked()` may fail after
prior shutdown stages changed state. Ring release also reads MMIO indices, so it
must occur while MMIO is mapped and after DMA/interrupt producers are quiesced.

Required design before production binding: fence opens, creates, PM and TX;
preflight/snapshot all child families before any detach; drive every child and
root close; join deferred owners outside RTNL; and prove IRQ, tasklet/work,
DMA/beacon/TX-status and callback quiescence before releasing MMIO, rings or the
adapter. The terminal path needs a reviewed, bounded hardware/DMA stop and owner
drain if a checked stage fails. If no such fallback is proven for this MT76x3
PCI device, do not free live state or claim safe removal; keep the feature
isolated pending hardware/API evidence. No source binding, target build or
router change was made here.

### Legacy MT radio-off limitation

The inspected v43 tree's legacy `RT28xxPciAsicRadioOff()` returns `FALSE`
immediately for `HIF_MT` (`TODO: ... Not support for HIF_MT yet`). Its PCI probe
sets bus mastering with `pci_set_master()`. The reviewed `rt_pci_remove()` path
does not clear bus mastering or check `RtmpPhyNetDevExit()` before releasing
adapter/MMIO. The isolated MT-specific checked helper attempts RX/TX and PDMA
shutdown, but several hardware/firmware checks can fail; on MCU command failure
it records terminal stage 5, and future retries reject a stage greater than 4.
That is not a demonstrated recovery path. No local kernel PCI implementation
was found in this candidate tree to prove that `pci_disable_device()` or any
other bus-level operation guarantees DMA quiescence for this board. Do not infer
that releasing BAR/MMIO or `synchronize_irq()` alone stops bus mastering.

The next source investigation must establish the exact MT7621 PCI core behavior
and a verified stop sequence for MT7603 before choosing fallback mechanics.
Until then, do not bind the checked close into PCI removal or free adapter state
on a failed stage.

## CI checkpoint — 2026-10-27

Firmware run `40538660394` (build #635) completed successfully on pushed commit
`84b2f12d2b653057e6806c824e7123757161a191`. The `build (wr1200js)` job
completed successfully at 16:40:19Z; `firmware-zip (wr1200js)` and `downloads`
completed successfully at 16:40:36Z. GitHub lists the WR1200JS firmware artifact
`WR1200JS_4.4.198.9-635_ab2d3a0d_TEST` and associated verification artifacts.
ABI run `40538660378` also succeeded on the same earlier head. Neither run
contains local v43 commits `47abc0a` or `4d8373e`. This establishes CI success for
the published SHA only; it does not establish runtime acceptance on the router.
### Pinned Linux and MT7621 PCI source audit — 2026-10-27

The current WR1200JS build workflow pins Padavan source commit
[`c25283e915a2a00a763774dd255b14aff997285e`](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/). The exact source, fetched read-only through the connected GitHub source tool, was inspected at:

- [`drivers/pci/pci.c`](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/drivers/pci/pci.c): `pci_clear_master()` calls `__pci_set_master(dev, false)`. That helper reads `PCI_COMMAND`, clears `PCI_COMMAND_MASTER`, writes the word if changed, and updates the software `is_busmaster` flag. It does not check the config read/write return values or verify the hardware bit afterward.
- [`arch/mips/pci/pci-mt7621.c`](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/arch/mips/pci/pci-mt7621.c): `config_access()` serializes config cycles with `asic_pcr_lock`, accesses the MT7621 PCR address/data registers, and returns `PCIBIOS_SUCCESSFUL` unconditionally. This callback contains no checked transaction completion/error path. Its root-port resets are used during PCI host probe; there is no per-endpoint recovery API in this file.
- [`drivers/pci/pci-driver.c`](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/drivers/pci/pci-driver.c): `pci_device_remove()` invokes the driver's void `remove()` callback, then proceeds to `pcibios_free_irq()` and clears `pci_dev->driver`. A driver return cannot veto unbind.
- The exact vendor driver's relevant `MTPciMlmeRadioOff()` and v43 `wr_iot_mt_radio_off_checked()` bodies were inspected in the locally materialized isolated source based on that pinned source. The legacy radio-off function calls the void `MTPciPollTxRxEmpty()`, whose TX/RX timeout branches only log and continue; `CmdRadioOnOffCtrl()` status is ignored there. `AsicSetWPDMA()` writes `MT_WPDMA_GLO_CFG` and returns `TRUE` without readback. The v43 checked helper improves these checks, but it does not prove the PCI bus-master bit was cleared or drain transactions already issued.
- `wr_iot_pdma_reset_raw()` is unsuitable as terminal fallback: after reset/polling it cleans rings, re-enables BSS sync, calls `RT28XXDMAEnable()`, re-enables interrupts and dequeue. It is a watchdog recovery path, not a removal stop path.

**Conclusion:** `pci_clear_master()` is a candidate inhibit against later bus-master requests, not by itself a hardware DMA-idle receipt or proof that transactions already issued have drained. The exact pinned config path does not report or verify the write. The currently reviewed sources do not establish a safe terminal policy when the checked MT7603 shutdown fails. The v43 candidate therefore remains isolated; do not free DMA rings, MMIO or adapter state on that unresolved path.

**Next gate:** establish a bounded, target-specific sequence covering stable device TX/RX idle, the actual PCI command-bit update/readback and ordering semantics, any in-flight PCIe transactions, and all deferred owner/IRQ/work/beacon/TX-status drains. Only then can removal free resources. The exact source does not expose a safe per-device root reset; using the probe-time shared reset sequence as fallback is not justified.

This was source inspection only. No code binding, build, firmware image or router state was changed or tested for this step.

### PCI reset API follow-up — 2026-10-27

A further read-only inspection of the exact pinned Linux `pci.c` and `pci.h` found generic `pci_reset_function()` / `pci_try_reset_function()` APIs. This does not close the MT7603 terminal-stop gate:

- The kernel reset selector tries device-specific reset, PCIe FLR, AF FLR, PM D3hot/D0, hotplug-slot reset, and finally a parent-bus reset. The last option can affect other devices on the bus and is not acceptable as an assumed per-adapter fallback.
- The PCIe FLR path checks the endpoint FLR capability, waits for pending transactions, but if that wait times out it logs and still issues FLR, then returns success without endpoint-specific post-reset readiness validation. The API documentation also presumes the function is unused and requires the caller to reinitialize PCI configuration, BAR decoding, interrupts and bus mastering.
- The MT7603 vendor PCI probe identifies the device and enables bus mastering but does not establish that this specific function advertises FLR/AF FLR or a safe PM reset. No current router PCI capability dump is present in the evidence reviewed here.
- MT7621 config access still reports success without checked transaction status, so a software success result alone cannot prove the command-bit write or endpoint reset took effect.

**Decision at the time of this source-only review:** do not add a blind call to `pci_reset_function()` to checked close or PCI remove. Live PCI capability data was collected later and is recorded below. Until one complete bounded stop sequence is demonstrated, keep v43 isolated and do not release DMA/MMIO/adapter resources after failed shutdown.

This follow-up was source-only: no driver binding, firmware build, device command, router change or image validation was performed. Source references: [pinned PCI reset implementation](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/drivers/pci/pci.c), [pinned PCI API declarations](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/include/linux/pci.h), [pinned MT7621 PCI host](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/arch/mips/pci/pci-mt7621.c).

**Read-only evidence collection detail:** `/proc/bus/pci/devices` is not a PCI capability dump. The fixed SSH helper's allowlisted `pci-config` check reads readable sysfs PCI config files using `busybox hexdump -C -n 4096`; no arbitrary remote command can be supplied. On 2026-10-27 the check completed successfully from the Codex execution environment (exit code 0), followed by the fixed `pci` and `pci-dump-tools` checks. It read four PCI config files. `/proc/bus/pci/devices` identifies `0000:01:00.0` as `14c3:7603` (`mt7603_drv`) and `0000:02:00.0` as `14c3:7662` (`rtpci`); the other two entries are MTK host-bridge functions `0e8d:0801`. BusyBox exposes `hexdump`, `base64`, `dd`, and `strings`; the list does not contain `od`. The exact 140-line helper output is saved as `docs/evidence/WR1200JS-LIVE-PCI-CONFIG-2026-10-27.txt`. This confirms that the earlier pasted `unexpected ( expecting fi` error did not reproduce with the checked-in helper as currently present. It does not establish why that earlier invocation differed.

The observed standard PCI Express capability at offset `0x70` has Device Capabilities bytes `c0 8f 00 00` for both Wi-Fi functions. The pinned kernel's `include/uapi/linux/pci_regs.h` defines `PCI_EXP_DEVCAP_FLR` as `0x10000000`; bit 28 is clear in both values. The conventional capability chains in the raw capture contain PM at `0x40`, MSI at `0x50`, and PCIe at `0x70`, with no PCI Advanced Features capability to advertise AF FLR. At the time of the read, PCI_COMMAND at offset `0x04` was `0x0006` on both Wi-Fi functions, so memory decoding and bus mastering were enabled. The PCIe flags at `0x72` are `0x0002` for both 7603 and 7662 (version 2, type 0 / Endpoint). The earlier `0x0042`/`0x00008000` values came from the MTK `0000:00:00.0` host bridge, not 7603. No write/configuration command was issued. This rules out advertised FLR interfaces as known reset candidates, but does not exclude vendor-specific reset and does not prove that bus-master disable or DMA draining is safe.

The FLR interpretation was checked against the exact pinned Linux `pci_regs.h`: `PCI_EXP_DEVCAP` is offset 4 in the PCIe capability and `PCI_EXP_DEVCAP_FLR` is bit 28 (`0x10000000`). The pinned `drivers/pci/quirks.c::pci_dev_reset_methods[]` contains Intel and Chelsio reset entries, but none for MediaTek `14c3:7603`. Both devices have a PM capability at `0x40`; the captured PMCSR at `0x44` is zero (D0 and `NO_SOFT_RESET` clear), so generic `pci_pm_reset()` appears to be a possible method if the kernel's in-memory state and config access are valid. However, that path writes D3hot then D0 without checking the writes or waiting for pending PCI transactions. The generic `pci_reset_function()` path first writes `PCI_COMMAND_INTX_DISABLE` (which disables memory/I/O decode and bus mastering), then restores saved config including the prior PCI_COMMAND value; it is therefore not a terminal remove fallback that leaves bus mastering inhibited. The MT7621 host config accessor's unchecked completion status/readback remains a hard limit. Do not invoke any reset on the live device as part of this read-only evidence step.

Pinned source references: [PCI register definitions](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/include/uapi/linux/pci_regs.h), [PCI reset selection and PM reset](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/drivers/pci/pci.c), and [device-specific reset table](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/drivers/pci/quirks.c).

### PCI identity and topology cross-check — 2026-10-27

The fixed read-only `pci-topology` helper read `vendor`, `device`, `class`,
and the sysfs device/driver/subsystem symlinks for each PCI function. Its
28-line raw output is saved at
`docs/evidence/WR1200JS-LIVE-PCI-TOPOLOGY-2026-10-27.txt`. The two host
functions `0000:00:00.0` and `0000:00:01.0` identify as MTK `0e8d:0801`, class
`0x060400`; the corresponding sysfs paths place Wi-Fi functions
`0000:01:00.0` and `0000:02:00.0` beneath those separate branches. The
`14c3:7603` function reports class `0x028000` and binds `mt7603_drv`; the
`14c3:7662` function reports class `0x028000` and binds `rtpci`.

The raw config capture identifies both 7603 and 7662 with PCIe capability
type field `0x0002` (Endpoint), consistent with their network-controller class
and driver bindings. The earlier `0x0042` interpretation belongs to the MTK
host bridge and must not be used to infer the 7603 reset scope. No reset or
other write was attempted. The local allowlisted helper gained this read-only
check; it does not accept an arbitrary remote command.

### Main-radio readiness producer gap in isolated v43 — 2026-10-27

A source-wide call-site audit of `.iot-local-check/mt7603-mbss-global-preflight-v43c-local-20261027` found that the main-radio precondition is present in the IoT open wrapper but its successful producer is missing:

- `include/wr-iot-mbss-open-admission.inc` admits MBSS open only when phase is `WR_RADIO_READY`, `main_ready` is true, and reset/retire/inhibit flags are clear. Before `MBSS_OPEN` / `VIRTUAL_IF_UP`, the MT7603 observer reads the main BSS beacon request state and `ARB_BCNQCR0`, requiring main beacon queue bit 0 active and IoT queue bit 17 inactive.
- `os/linux/rt_main_dev.c::MainVirtualIF_open()` successfully records main-interface ownership, but completes its open with `wr_iot_radio_finish_unverified()`. This deliberately leaves phase `WR_RADIO_UNVERIFIED` and `main_ready=0` until hardware/configuration readback.
- `include/virtual-open-claim.h` contains `wr_iot_main_radio_verify_owned()` and the transition model has `WR_RADIO_VERIFY`, but a call-site search across the isolated candidate finds no caller that acquires VERIFY, runs `wr_iot_mt7603_main_config_observed()`, and publishes verified main readiness. Thus the later IoT open cannot satisfy its own prerequisite in this candidate; it fails closed before BSS_UP.

This is a concrete candidate integration blocker, separate from the PCI terminal-removal blocker. The next source step is to design/bind a bounded main-readiness verification producer after main-open, keeping adapter/netdev ownership pinned, performing the register read outside `wr_iot_transition_lock`, then revalidating epoch, ticket, registry generation and `VirtualIfCnt` under the shared lock. A failed or invalidated observation must preserve recovery ownership and must not permit IoT BSS_UP. First add a focused candidate-level call-site/transition fixture; do not install this into the production driver until the close/recovery and PCI lifetime owners are resolved.

Source-only audit at that point; no source candidate was edited, built or installed. The pending capability question was answered by the live snapshot recorded below.


### Isolated v44 main-readiness VERIFY producer candidate — 2026-10-27

Following the v43 call-site gap above, I generated isolated candidate
`.iot-local-check/mt7603-main-readiness-verify-v44-local-20261027` using
`tools/iot/prepare-main-readiness-verify-candidate.py`. The candidate adds a
bounded main-readiness VERIFY call in `MainVirtualIF_open()` after main open
records its unverified ownership and before HNAT/queue/carrier admission. It
acquires a VERIFY ticket with the current epoch, performs the main beacon and
queue observation outside the transition spinlock, then reacquires the common
lock and revalidates the ticket, generation, family and ownership before
publishing READY. A failed observation retires only the matching VERIFY ticket;
the virtual-interface owner is deliberately retained.

The focused checker `python tools/iot/check-main-readiness-verify-candidate.py
.iot-local-check/mt7603-main-readiness-verify-v44-local-20261027` passed:
source structure, lock/readback/revalidation order, and queue/HNAT ordering
were confirmed. Its manifest keeps `production_installed`,
`recovery_owner_bound`, and `pci_release_gate_bound` false. The existing strict
host fixture `check-virtual-open-claim.c` also passed; Python syntax checks and
`git diff --check` passed for the two new scripts.

**Safety boundary:** this is still an isolated source candidate, not a working
IoT activation path. The verify-failure branch returns an ndo_open error after
the virtual-UP owner was claimed; because the recovery owner is not bound, the
retained owner has no demonstrated drain path. Do not integrate this candidate
or claim main/IoT radio readiness is solved until a reviewed recovery owner can
join failed opens and the PCI adapter-release fence is proven. No MIPS
cross-compiler is installed in the current Windows command environment, and no
MIPS compile, full firmware build, image inspection, router command or device
runtime test was performed.

New local source files: `tools/iot/prepare-main-readiness-verify-candidate.py`
and `tools/iot/check-main-readiness-verify-candidate.py`. The generated v44
candidate and its manifest remain under the existing ignored local
`.iot-local-check/` directory. Next: design an explicit failed-open recovery
owner/join that is compatible with Linux ndo_open failure semantics, then
re-run the source and host fixtures before arranging isolated target compile.
The live PCI config/capability snapshot is still pending separately.


### CI snapshot — 2026-10-27 17:27Z

GitHub Actions read-only query shows firmware build #635, run `40538660394`, and Band Steering ABI run `40538660378` completed successfully on published SHA `84b2f12d2b653057e6806c824e7123757161a191`. The newest Agent build failure monitor run `40543253994` was `skipped`, not a firmware build. These runs predate the current local HEAD `4d8373e7b5c24c1ef2d551cff266aa141e26df8d` and the uncommitted v44 candidate, so they do not validate this candidate. No workflow was triggered.


### Live WR1200JS PCI configuration snapshot — 2026-10-27

The owner supplied a failed fixed-helper attempt with a remote shell syntax error. I reran the currently checked-in allowlisted helper successfully over SSH; the cause of the earlier error was not established. The helper reads up to 4096 bytes from each readable PCI config file with `busybox hexdump -C -n 4096`. BusyBox's applet list contains `hexdump` and omits `od`. This is read-only; no router state was changed.

The 4-KiB sysfs config files were readable for all four PCI functions. `/proc/bus/pci/devices` and the bound driver identify these Wi-Fi functions:

- `0000:01:00.0`: vendor/device `14c3:7603` (MT7603).
- `0000:02:00.0`: vendor/device `14c3:7662` (MT7662).

Both Wi-Fi functions expose standard capabilities at `0x40` (PM), `0x50` (MSI), and `0x70` (PCI Express). Both `14c3:7603` and `14c3:7662` report PCIe version 2/type 0 (Endpoint), with Device Capabilities `0x00008fc0`. The prior Root Port reading was from MTK host bridge `0000:00:00.0`, not 7603; there is no Wi-Fi type/class mismatch in this capture. `PCI_EXP_DEVCAP_FLR` (`0x10000000`) is clear on both Wi-Fi endpoints. The standard capability chain contains no Advanced Features capability (`PCI_CAP_ID_AF`, `0x13`), so there is no advertised AF-FLR capability. PM capability word is `0xc9c3` on both Wi-Fi endpoints; PMCSR at `0x44` is zero on both, with `PCI_PM_CTRL_NO_SOFT_RESET` clear. Under pinned Linux 4.4 `pci_pm_reset()` preconditions, this makes PM-reset a source-level candidate if each function is in D0 and has no `PCI_DEV_FLAGS_NO_PM_RESET` quirk. It is not proof that invoking reset is safe or that driver reinitialization restores these radios.

Correction to the preceding progress note: AF-FLR is in the conventional PCI capability list (the pinned kernel checks `pci_find_capability(..., PCI_CAP_ID_AF)`), not in the PCIe extended-capability list. The conventional list was decoded from this dump and does not contain it. Linux's PM-reset implementation only writes D3hot then D0, sleeps, and returns success without checking config transaction completion or device readiness. The MT7621 host config callback is already documented above as reporting success without checked transaction status. Reset remains unsuitable as an unqualified terminal fallback; do not release DMA/MMIO/adapter state based on the PM-reset return alone.

Pinned source references: [PCI capability definitions](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/include/uapi/linux/pci_regs.h), [PCI reset selection and PM reset](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/drivers/pci/pci.c), and [MT7621 PCI host config access](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/arch/mips/pci/pci-mt7621.c). The PM-reset quirk search in pinned `drivers/pci/quirks.c` only found the generic VGA-class quirk; this does not replace a full target-build quirk/config review. No reset, build, flash, reboot, or router configuration change was attempted.

## PM-reset source decision — 2026-10-27

The pinned source was re-read from the preserved bare Git snapshot at
`../firmware-source-backup/padavan-4.4.git`, revision
`c25283e915a2a00a763774dd255b14aff997285e`; the pin resolves exactly. The
snapshot is outside this repository working tree and was not modified.

`pci_pm_reset()` accepts the live endpoints at the capability/precondition
level only when they are D0 and no `PCI_DEV_FLAGS_NO_PM_RESET` quirk applies.
It clears the PM state bits, writes D3hot, sleeps, writes D0, sleeps, and
returns 0. The reset implementation does not read back PMCSR or prove the
endpoint has recovered. `pci_reset_function()` documents that a caller must
reinitialize the device, including MSI, BARs, bus mastering, and memory/I/O
decoding after reset. Its fallback chain can also select slot-function or
parent-bus reset, so this generic API is not endpoint-isolated merely because
the PM capability is present.

The MT7621 `config_access()` uses the host PCR MMIO address/data registers and
returns `PCIBIOS_SUCCESSFUL` after its access sequence; the callback has no
separate transaction timeout/error result. Thus a kernel PM-reset success code
cannot be treated as verified config completion, DMA stop, or radio readiness
on this board. The live PCI snapshot also showed both adapters have FLR clear
and no AF capability, so neither has an advertised function-level reset path.

**Decision:** PM-reset is not an acceptable recovery completion receipt or
terminal fallback for IoT close/remove. Keep reset support out of the candidate's
release predicate. Before any future reset experiment, the owner must first
fence every netdev TX/open/close and registration path, synchronize/drain all
callbacks and DMA using a device-defined completion proof, preserve adapter
lifetime through all recovery work, and have a complete PCI reinitialization
path plus fault-injection evidence. If those cannot be proven, fail closed and
retain the adapter rather than freeing DMA/MMIO state. No driver source was
changed, no PCI reset was issued, and no target build/image/device acceptance
was run.

Source files inspected in the pinned snapshot: `drivers/pci/pci.c`
(`pci_pm_reset`, `pci_dev_reset`, `pci_reset_function`),
`arch/mips/pci/pci-mt7621.c` (`config_access` and PCI ops), and
`drivers/pci/quirks.c` (NO_PM_RESET quirk search). The prior live-config
observations and exact source links remain above.

## Failed main ndo_open recovery boundary — 2026-10-27

Read the pinned Linux 4.4 `net/core/dev.c` from the same exact local bare Git
snapshot (`c25283e915a2a00a763774dd255b14aff997285e`). In `__dev_open()`,
Linux sets `__LINK_STATE_START` before calling `ndo_open()`. If the callback
returns an error, it clears START and returns the error; the success-only branch
that sets `IFF_UP`, activates the device, and notifies `NETDEV_UP` is skipped.
There is no `ndo_stop()` call on this failure path. The source also states this
contract in the main vendor callback comment. Thus a later `dev_close()` is not
a retry path for cleanup after failed main `ndo_open`.

Correlated with isolated v44 `MainVirtualIF_open()`:

- Failure before `RTMP_DRIVER_AP_MAIN_OPEN` may be classified as unmutated and
  release its local module pin only when no vendor/device mutation occurred.
- Once AP main-open is attempted, a failed `VIRTUAL_IF_UP_CLAIM` is recorded as
  `WR_REF_UNCERTAIN_OPEN`; the operation ticket is retired, but the registration
  and manual `RT_MOD_INC_USE_COUNT()` pin are retained.
- If virtual UP succeeds but main-radio VERIFY fails, the registry is `OWNED`,
  `main_ready` remains false, and `ndo_open` returns an error before HNAT/queue
  enable. Linux still does not call `ndo_stop`; the manual module pin and main
  reference remain for an external owner.

Required recovery shape, not yet implemented: publish a deferred main-open
recovery owner while the callback still holds its existing device/module pins;
serialize the worker after the failed callback leaves RTNL; validate the exact
netdev registration generation, open token, and uncertain/owned state; admit a
checked main-close ticket under the common adapter lock; then perform the checked
main physical/virtual-down sequence and any required beacon cleanup outside the
spinlock. Keep the owner, netdev reference, module pin, and adapter-release fence
when any step is unverified. Release them only after the matching ticket and
registry owner are retired, callback/work/TX/DMA quiescence is independently
proven, and PCI remove joins the owner. A worker must not retry `dev_close()`
and must not free resources based only on PM-reset or software return status.

This establishes the Linux callback semantics and v44 failure states only. It
does not implement or bind recovery, prove close safety, or authorize target
compilation/packaging. No production source, device, image, or router state was
changed.

## Main failed-open recovery owner contract — 2026-10-27

Added the isolated host contract `tools/iot/main-open-recovery-owner.h` and
fixture `tools/iot/check-main-open-recovery-owner.c`. It binds owner state to
the exact registered main netdev, generation and open token, and refuses to
queue without both a held netdev reference and an adapter-release fence.
An acquired main reference can proceed only when the radio ticket is idle and
all registry entries match the vendor count; the caller must then bind and
continue the exact checked-close ticket. Final owner completion requires the
record's IDLE/close-stage-4 receipt, release of the original module pin, and a
joined worker. An `UNCERTAIN_OPEN` state yields only RECONCILE: because failed
virtual-UP admission may have occurred before the vendor count changed, the
model deliberately does not attempt a speculative DOWN/decrement.

Verification: the exact host fixture compiled and passed with GCC
`-std=c11 -Wall -Wextra -Werror`. This does not exercise a kernel workqueue,
RTNL ordering, device/module reference operations, production callbacks, PCI
removal or hardware DMA. Recovery binding and physical-resource release remain
unproven; do not install the contract or free driver resources from it.

### Close-count revalidation, 2026-10-27

The retained `CLOSE_INCOMPLETE` action now requires the current vendor count
to equal the count recorded with its exact close ticket. A dedicated registry
walk counts that one `CLOSING` record plus only unambiguous `OWNED` records;
it rejects a changed count, missing closing record or another transitional
entry. The generic registry-count helper is intentionally unsuitable here
because it rejects all `CLOSING` records. The host fixture exercised both
vendor-count and registry drift and passed with MinGW GCC
`-std=c11 -Wall -Wextra -Werror -O2`. The first attempted output executable
was locked by Windows after an earlier failed assertion; the successful run
used a new filename. This is an isolated host contract, not a bound kernel
worker or proof of physical close.

### Retained retry and PCI stop contract, 2026-10-27

The isolated main-open recovery owner now has explicit bounded `RETAINED` to
`QUEUED` requeue and PCI stop-request transitions. Requeue requires a caller
decision, a remaining attempt budget and an acquired/retained close source;
`UNCERTAIN_OPEN` cannot be retried as a guessed DOWN. A stop request prevents
new attempts while preserving the deferred owner, netdev/module pin and
adapter-release fence until checked completion. The host fixture exercises
the attempt limit, queued and retained stop, and the PCI retirement gate:
even after a reported work join, children cannot be marked done while this
owner remains. It passed strict MinGW GCC
`-std=c11 -Wall -Wextra -Werror -O2`. No real workqueue, `cancel_work_sync`,
PCI remove hook or driver callback is bound. A stopped unresolved owner blocks
adapter release; a production caller must resolve it before final removal.

### Module-pin release ordering, 2026-10-27

The isolated recovery owner no longer accepts release of the original
`RT_MOD_INC_USE_COUNT` pin merely after the close receipt. Its release marker
requires an independently joined worker and a reported actual pin release;
`complete` still requires both this marker and join before dropping deferred
ownership. The host fixture rejects release before join, rejects absent
release and duplicate release, then passes the completed sequence with strict
MinGW GCC `-std=c11 -Wall -Wextra -Werror -O2`. This is necessary because a
worker running module code must not allow the module to unload before its
callback returns. The booleans remain caller-provided evidence; no Linux
workqueue, module ref operation or PCI remove path was executed here.

### v44 close prerequisite for worker binding, 2026-10-27

Rechecked the generated isolated v44 source, not just the host owner model.
`MainVirtualIF_open()` retains its module pin and owner after an unverified
open, while `MainVirtualIF_close()` at `os/linux/rt_main_dev.c:113-145` still
uses legacy `RTMPInfClose`, `VIRTUAL_IF_DOWN`, then unconditional
`RT_MOD_DEC_USE_COUNT`. The callback is registered as the main netdev stop at
`:475`. Linux does not invoke it after a failed open, and invoking it manually
would bypass the exact checked ticket and could release the pin on uncertain
hardware state. The v44 structure checker passed again; its output explicitly
reports recovery and PCI release gates unbound. The adjacent
`mt7603-main-readiness-verify-v44-local-20261027.manifest.json` independently
records `production_installed`, `recovery_owner_bound`, and
`pci_release_gate_bound` as false.

Required source order before worker binding: (1) implement a checked main
close continuation that records the same ticket/generation, stages every
vendor mutation and preserves the pin on incomplete close; (2) have the
deferred failed-open owner invoke only that continuation after leaving RTNL;
(3) join the worker and verify close/physical quiescence before PCI adapter
release. Host contracts alone do not provide these operations. No generated
driver source or router was changed in this audit.

### Main-close receipt gate, 2026-10-27

Tightened `tools/iot/main-stop-owned.h` so a successful main-close completion
requires the exact record's stage-3 checked-DOWN receipt, matching close
serial/epoch/prior state and the original vendor count for CLOSE or BSS_CLOSE.
Only after ticket retirement and record consumption does it write stage 4 and
authorize release of the original open pin. The strict host fixture rejects
an absent or stale receipt, wrong CLOSE cardinality and wrong ticket epoch;
it passes both physical-last-close and secondary-
reference close cases. `check-main-stop-owned.c` and the dependent
`check-main-open-recovery-owner.c` both passed with MinGW GCC
`-std=c11 -Wall -Wextra -Werror -O2`; whitespace check passed. This closes a
host-contract bypass, but the v44 source still has its legacy main ndo_stop:
the stage-3 receipt producer, checked executor and worker are not yet bound.

### Main-close preclose stages, 2026-10-27

The pinned v44 source `common/rtmp_init_inf.c` shows that `RTMPInfClose`
returns `void` while changing main-BSS beacon, client and Band Steering
state. The legacy `MainVirtualIF_close` calls it before `VIRTUAL_IF_DOWN`.
The isolated `tools/iot/main-stop-owned.h` contract now records stage 1 before
that call, stage 2 only after its return, and stage 3 only after a checked
DOWN result (including physical verification for the final CLOSE). A stage-1
interruption is ambiguous and cannot be replayed as a fresh call. The host
fixture covers duplicate claims/finishes, premature DOWN receipts and the
physical-close requirement; strict MinGW GCC with `-Wall -Wextra -Werror`
passes. No production executor calls these helpers, and a caller-supplied
checked result is not evidence of radio quiescence or on-device behavior.

The deferred-owner host fixture now uses the same staged close contract
instead of fabricating a stage-3 receipt. It binds the exact close ticket at
stage 1, rejects continuation while the void preclose is in progress, permits
continuation after stage 2, and requires the physical checked-DOWN receipt
before consuming the main reference and releasing its module pin. Strict
MinGW GCC passed. This establishes composition of the two host contracts;
neither is yet called by the production kernel worker or main ndo_stop.

Before a stage-1 claim, the isolated close contract now rechecks the entire
registry: the exact published main record must be `CLOSING`, every other
active record must be owned, and their count must match the ticket's vendor
count. The deferred recovery owner uses the same predicate. The fixture
rejects count drift and an intervening `RESERVED` child. Both strict host
fixtures passed. Production still needs the actual vendor count sampled
under the common adapter lock immediately before the void call; these helpers
alone cannot serialize an uninstrumented writer.

### v44 source binding order, 2026-10-27

In the exact generated v44 `os/linux/rt_main_dev.c`, a failed
`wr_iot_main_readiness_verify` returns `-1` after the main open has acquired
its reference and retains the module pin. The kernel does not call `ndo_stop`
after a failed `ndo_open`. The current `MainVirtualIF_close` still calls void
`RTMPInfClose`, then void `VIRTUAL_IF_DOWN`, and unconditionally decrements
the module use count. The candidate's `wr_iot_virtual_down_checked` returns a
software close result, not physical DMA or PCI quiescence. Replacing normal
close alone would leave the failed-open path without an executor and could
release the pin on an unverified physical close. Bind the adapter-pinned
deferred recovery owner and its stop/join lifetime first; then route normal
stop and failed-open recovery through one checked close executor. Physical
completion and PCI release need independent quiescence receipts. This is
source inspection of an isolated candidate, not a production driver test.

### Worker lifetime hooks in v44 source, 2026-10-27

`rt_pci_probe` allocates the adapter with `RTMPAllocAdapterBlock`, publishes
the main netdev, and has a later error path through `RTMPFreeAdapter`.
`rt_pci_remove` calls `RtmpPhyNetDevExit`, ignores its Boolean result, then
calls `RtmpRaDevCtrlExit`, which reaches `RTMPFreeAdapter`; it also unmaps the
PCI BAR and frees the main netdev. The generated v44 adapter contains a
transition lock and wait queues but no bound main recovery work item. An
actual work item therefore needs initialization before netdev publication,
a stop request plus synchronous join before every adapter free (including
probe unwind), and a release fence that covers netdev callbacks and the
retained module pin. Joining only before `RtmpPhyNetDevExit` is insufficient
because unregister can invoke `ndo_stop` and create a new deferred close.
The remove path cannot treat a failed child teardown as success or free the
adapter after a failed join. This is a source hook map, not an implementation
or proof that PCI remove is currently safe.

The host PCI retirement contract previously accepted a worker join before
main netdev detach as its only join. That ordering misses work that
unregister/`ndo_stop` might queue. It now requires a second, final joined
receipt after main detach and zero deferred owners before release can be
claimed. The strict PCI retirement and failed-main-open recovery fixtures
passed. A Boolean supplied by a caller is still only a contract input: the
production `cancel_work_sync`/queue fence and callback quiescence remain
unbound and unverified.

### Deferred pin-release ordering correction, 2026-10-28

The isolated recovery contract had required `work_joined` before marking the
module pin released, which a running work callback cannot satisfy for itself.
It now permits the active owner to record an already performed module
decrement only after checked close completion; resetting the owner still
requires an external work join. The strict recovery fixture verifies that
pin-release recording can precede join while owner completion cannot. The
helper neither decrements the module reference nor proves callback identity;
real worker, queue fence and PCI remove binding remain necessary.

### Deferred queue retirement admission, 2026-10-28

The isolated main recovery queue gate now receives the radio transition
state and refuses ordinary recovery after `retiring` is set. Source review
showed that `wr_iot_radio_begin` still permits CLOSE/BSS_CLOSE during remove:
unregister may invoke main `ndo_stop` after retirement has begun. The gate
therefore admits only a specifically identified PCI removal owner to queue
an already acquired main close during retirement; it rejects an uncertain
open and a caller without removal ownership. Its strict host fixture covers
both origins and wrong-origin attempts. This gate assumes the caller holds
the one adapter lock across the retirement check, owner state update and
actual kernel enqueue; caller-supplied removal ownership is not proof of
that binding. Production queue, stop and join remain unbound.
The revised strict recovery host fixture passed. Fresh full queue/ACK
assembly from the exact pinned MT76x3 source also completed with the revised
owner header; this does not compile or exercise the kernel workqueue.

### Adapter recovery-owner storage candidate, 2026-10-28

`prepare-radio-adapter-candidate.py` now embeds and initializes the shared
main recovery-owner record in `RTMP_ADAPTER` before adapter publication;
the queue assembler carries both owner headers into its driver bundle. A
fresh isolated adapter stage passed both generated main-open/close host
fixtures. A fresh full queue/ACK assembly from the exact pinned MT76x3 source
completed; its manifest includes the headers, adapter field and init.
`python -m py_compile` and `git diff --check` passed. This is storage only:
there is no `work_struct`, `INIT_WORK`, queue callback, checked main-close
executor, target MIPS compilation or production/image/device installation.

### Full bundle main-open composition audit, 2026-10-28

The exact pinned-source queue assembler still takes `MainVirtualIF_open`
from the adapter storage stage. Its failed `VIRTUAL_IF_UP(pAd)` branch runs
after `RTMP_DRIVER_AP_MAIN_OPEN` but decrements the module pin and returns an
error. The separately prepared main-open owner candidate is not composed
into this bundle. Linux does not call `ndo_stop` after failed `ndo_open`, so
the storage field alone cannot recover or justify pin release. The assembler
now recognizes this exact interim branch and writes explicit false manifest
flags for main-open owner composition and failed-open pin retention. A fresh
assembly from pinned revision `c25283e` completed; both flags are false and
the bundle still declares itself partial and not installed. Next compose the
reviewed main-open claim/registry path with a real checked deferred owner,
then remove this interim-branch assertion and prove pin release, join and
PCI teardown on the assembled source. No target build or router action occurred.

Directly applying `prepare-virtual-open-claim-candidate.py` to that assembled
bundle failed before creating an output tree: `include/rtmp_cmd.h` has no
`if_dev` member in `RT_CMD_INF_UP_DOWN` (expected one anchor, found zero).
That claim stage expects an earlier virtual-open candidate, not the queue
bundle. The assembler now also records `virtual_open_claim_composed=false`
and checks this exact legacy command ABI. Composition must merge the command
ABI, claimed dispatcher and main owner as one reviewed dependency chain;
copying only the main wrapper would leave vendor UP unclaimed.

Compared the already prepared `combined-open-v27-20261025` with the fresh
queue bundle on all command ABI and open/close caller files. The required
composition spans `include/rtmp_cmd.h`, `include/rt_os_net.h`,
`common/cmm_cfg.c`, `os/linux/rt_main_dev.c`, `include/rtmp.h`,
`common/rtmp_init.c`, `ap/ap_mbss_inf.c`, `ap/ap_apcli_inf.c`,
`ap/ap_wds_inf.c`, and `os/linux/rt_profile.c`. The v27 adapter lacks the
new main recovery-owner storage, so wholesale replacement would discard it.
More importantly, v27 `ap/ap_mbss_inf.c` discards the newer checked
`MBSS_CR_ENABLE` result, and v27 `ap/ap_mbss.c` removes Band Steering
readiness hooks present in the queue bundle. Therefore copying the older
files wholesale would regress existing candidate checks. Merge only the
reviewed ABI, ticket and call-site deltas, preserve newer CR/Band Steering
behavior, then compile/check every caller family before claiming composition.

### Isolated main-open claim composition, 2026-10-28

Added `tools/iot/prepare-queue-main-open-compose.py`. It takes the fresh
partial queue bundle and hash-pinned reviewed open candidate, extends only
the virtual-UP command record and claimed dispatcher, adds the main ticket
wait queue, and replaces the main open callback with the reviewed reservation
and retained-pin path. Legacy auxiliary callers keep their original ABI;
their full claim binding remains open. The script preserves queue-bundle
`ap/ap_mbss.c` and `ap/ap_mbss_inf.c` byte-for-byte, so it does not discard
the newer MBSS CR or Band Steering behavior. It writes a separate partial
composition manifest and does not install driver sources into firmware.

Preparation succeeded against the 2026-10-28 fresh queue bundle. The
extracted claimed dispatcher host fixture compiled under strict C11/GCC and
passed MBSS/auxiliary claim and replay checks. The composed main callback
contains a claimed virtual UP and retains its pin on post-mutation failure;
the two MBSS files matched their queue-bundle hashes. This does not prove
main callback runtime behavior, all-family count ownership, checked close,
deferred work/PCI joins, target MIPS build, image inclusion or router operation.
The next step is to bind the real deferred recovery worker and close owner,
then verify the composed main callback and full ABI across every caller.

The composer now verifies the pinned source revision and every input file
digest against the queue manifest before copying any source. A fresh isolated
composition passed that preflight; all 64 output file digests matched its
composition manifest. This protects the reviewed merge against a changed
scratch bundle, but it does not test the kernel callback or replace the
missing deferred worker. The recovery contract requires an exact recorded
close ticket, checked DOWN receipt, module-pin release by the active owner,
and an external synchronous work join before adapter release; these actions
are not yet bound to Linux workqueue or PCI remove.

### Extracted composed main-open host execution, 2026-10-28

Added a fixture generator that extracts the actual `MainVirtualIF_open`
function from the composed bundle and links it to the current registry/radio
headers. Strict host C11/GCC execution passed four paths: missing adapter
and missing registration release the early pin; failed claimed virtual UP
after `AP_MAIN_OPEN` retains the pin and `UNCERTAIN_OPEN` record; successful
claimed UP owns the record and remains radio `UNVERIFIED`; a late main-down
intent after virtual UP returns failure and retains the pin/uncertain record.
Vendor actions, lock, queue and wakeup are injected in this fixture. It does
not exercise a kernel workqueue, checked close, PCI remove or physical radio.

### Extracted physical/main dispatcher branch, 2026-10-28

`tools/iot/prepare-main-open-dispatch-check.py` extracted the actual composed
`VIRTUAL_IF_UP_CLAIM` physical/main branch into a C11 host fixture. Compilation
with `-Wall -Wextra -Werror` and execution passed: first `WR_RADIO_START`
increments the virtual count and calls physical open once; failed physical
open rolls the count back and marks stage 2; the same ticket cannot be
replayed; `WR_RADIO_MAIN_OPEN` increments an existing count and updates
beacons without restarting physical radio. This test injects the physical
open operation and transition lock. It does not prove Linux concurrency,
deferred checked close, target build, or router behavior.

### PCI remove release ordering audit, 2026-10-28

The current isolated composition exposes a specific release hazard. In
`os/linux/rt_main_dev.c`, `RtmpPhyNetDevExit` returns `FALSE` when
`RT28xx_MBSS_Remove` fails, before detaching the root netdev. In
`os/linux/pci_main_dev.c`, `rt_pci_remove` calls `RtmpPhyNetDevExit` without
checking its result, then calls `RtmpRaDevCtrlExit`, unmaps CSR and frees the
root netdev. `RtmpRaDevCtrlExit` can reach `RTMPFreeAdapter`, whose transition
lock is freed. The candidate contains a host-only PCI retirement contract,
but neither a bound recovery work item nor synchronous joins around root
unregister are present in this call path. A failed child close or a newly
queued `ndo_stop` recovery can therefore leave callbacks or owners referring
to released state. A production candidate must fence admissions, request
stop, join existing work, complete child teardown and root detach, join work
again after `ndo_stop`, then prove zero deferred owners and callback/DMA
quiescence before claiming release. The existing `FALSE` return must be
propagated into that decision; simply returning early from a `void` PCI remove
callback is not a complete hardware cleanup strategy. This is source-level
evidence only; no device operation or target build occurred.

Added `tools/iot/check-pci-remove-release-gate.py` as a source-order preflight
for this release path. Running it on the composed bundle exited 1 as expected,
reporting three open gates: the fallible root-detach return is discarded; the
first work join, root detach, final work join and release claim are not ordered
before adapter free; and no synchronous work join appears in PCI remove. It
does not emulate kernel lifetime or prove a future candidate safe merely by
finding the required source tokens.

### MT7603 checked radio-off composition, 2026-10-28

The prior queue/main-open composition contained checked software close but
did not contain `wr_iot_mt_radio_off_checked` or its transition stage. Its
return therefore could not establish the register/PDMA milestones required
before considering a physical main close. Added
`tools/iot/prepare-composed-mt7603-radio-off.py` to compose only the reviewed
MT7603 radio-off slice into a new isolated tree. It also bounds the checked
dequeue wait and retains an uncertain failure rather than proceeding to IRQ
and ring cleanup. The generated v2 tree changes exactly four source files;
all 64 manifest hashes matched. `check-mt7603-checked-off.py` passed its
fault-injection host cases. The actual composed `wr_iot_drv_close_checked`
was extracted, compiled with C11/GCC `-Wall -Wextra -Werror`, and executed
successfully with injected AP/PCI primitives. The PCI release source gate
still reports three open conditions. This is not a target build or RF/device
observation, and it does not bind main `ndo_stop`, recovery work or PCI join.

### Partial main ndo_stop host validation, 2026-10-28

Added uninstalled `tools/iot/main-close-checked.inc` with exact main-stop
admission and recorded preclose; it calls checked virtual DOWN only with its
owned close ticket and releases the main module pin only after a checked
completion receipt. `tools/iot/prepare-main-close-check.py` extracted this
actual fragment into a C11/GCC host fixture. `-Wall -Wextra -Werror` compile
and execution passed physical last close, selective close with an owned peer,
failed DOWN retaining the original ticket/pin, and refusal to replay a close
that was already attempted. The host fixture injects netdev, driver close,
hardware stage and locking behavior. Linux `ndo_stop` ignores its return;
therefore this fragment cannot be installed without an adapter-pinned
recovery worker, a safe handoff for WAIT_TICKET and failure, and PCI two-phase
join/release gates. No target build or router test occurred.

### Partial main close composition, 2026-10-28

The checked virtual DOWN and physical close result bridge were already
present in the queue/radio-off bundle as included source fragments. Added
`tools/iot/prepare-composed-main-close.py` to place the reviewed partial main
`ndo_stop` into a separate successor, after verifying every input manifest
hash. Only `os/linux/rt_main_dev.c` changes; all 64 output hashes match.
An extracted strict GCC host test of the composed callback passed the same
physical/non-last/failure/replay scenarios. The PCI release gate still exits
1 with the discarded detach result and missing joins/release claim. The
manifest retains false recovery, complete-tree, production and runtime
claims. No target compilation or physical device operation was performed.

### Failed main ndo_stop recovery admission, 2026-10-28

The prior recovery owner could identify a CLOSING record at stage 2/3, but
could not accept that owner from a failed `ndo_stop` because its queue
function admitted only OWNED or UNCERTAIN_OPEN records. Added
`wr_iot_main_recovery_queue_close` to the host contract. It accepts the
exact recorded close ticket, stable registry count and pinned lifetime;
the PCI retirement origin requires an active retirement owner. Stage 1,
after an attempted void `RTMPInfClose`, is marked CLOSE_UNCERTAIN and permits
reconciliation only. Stages 2/3 are CLOSE_INCOMPLETE and may continue the
same checked DOWN ticket. A strict C11/GCC `-Wall -Wextra -Werror` test passed
wrong ticket/lifetime rejection, stage 1 no-retry, stage 2 continuation and
retirement admission. The earlier failed-open recovery-owner test still
passes. No Linux `work_struct` is scheduled by this header, and no PCI work
join or target/runtime proof has been added.

The checked virtual DOWN path decrements `VirtualIfCnt` before invoking
physical close. A failed physical close can therefore leave the exact CLOSE
ticket and retained reference at vendor count zero, while the record stores
the pre-DOWN count one. The initial recovery admission and action wrongly
required equality with that prior count. Added a stage-aware count check:
stage 0 requires the prior count, stage 1 is valid only for last CLOSE at
zero, and stage 2 requires prior minus one (including selective BSS close).
The registry cardinality still checks the original owned reference count.
Targeted strict GCC host tests now cover post-decrement last close and
selective close, and the existing failed-open owner test still passes. A
terminal or ambiguous physical failure still needs its own retryability
decision in the eventual Linux worker; this count fix alone does not permit
releasing the adapter.
