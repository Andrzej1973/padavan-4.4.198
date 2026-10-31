# WR1200JS IoT production activation gap — 2026-10-21

## Bridge ownership cross-check, 2026-10-27

The isolated bridge candidate already checks `/sys/class/net/ra2/master`:
`wr_iot_bridge_attach()` rejects a foreign master, and
`wr_iot_bss_set_up()` requires the owned `br-iot`, only `ra2` as a member,
IPv6 disabled and the bridge up, then repeats these checks after raising the
BSS. `check-bridge-kernel.py` covers rejection of a foreign master and member.
Do not add a duplicate guard here. The pinned RC `net_wifi.c` attaches only
`IFNAME_2G_MAIN` and `IFNAME_2G_GUEST` to the LAN bridge; the board profile
names `ra0` as its main interface and uses the `ra` prefix for extensions.
The exact [pinned `netutils.h`](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/user/shared/netutils.h)
maps classic 2.4 GHz main/guest to `ra0`/`ra1` when
`BOARD_2G_AS_WSOC` is true. The pinned `boards.mk` sets both
`BOARD_2G_IN_SOC` and `BOARD_5G_IN_SOC` to 0 by default, making that
expression true; the WR1200JS board overlay does not select either DBDC
alternative (`rax0`/`rax1`). The exact pinned source therefore reserves
`ra2` independently of the existing main and guest bridge attachments.
Confirm the resolved defines and interface list again from the eventual
final build image. This source proof is not an activation or isolation test
on the router.

## Pre-bridge direct-interface quarantine, 2026-10-27

Source audit found that the isolated RC firewall generator emitted no IoT
filter rules while `wr_iot_bridge_is_owned()` was false. It now emits INPUT
and FORWARD drops for reserved third-BSS interface `ra2` in that state, in
both IPv4 and IPv6 filter builders. The installed-helper fixture was updated
to require those drops with either allow-policy setting. The generator ran
successfully against a fresh local copy of the pinned RC source. Python syntax
and whitespace checks passed. The extracted installed-helper fixture could
not compile with the local Windows GCC because its Padavan headers require
`arpa/inet.h`; the existing Linux CI test remains the relevant compile gate
and has not run for this edit. Rules matching `ra2` do not by themselves prove
isolation if a bridge has already enslaved that port and packet filtering sees
the bridge interface instead. Production activation must refuse BSS up until
the owned `br-iot` attachment and quarantine policy are verified. No firmware
image or router state was changed.

## Follow-up 2026-10-22: actual PDMA reset entry paths

At pinned `c25283e`, `MlmePeriodicExecTimer` only enqueues
`CMDTHREAD_MLME_PERIOIDC_EXEC` (`common/mlme.c:1704-1712`). The command
handler calls `MlmePeriodicExec` (`common/rtmp_init.c:2651`), which calls
`PDMAWatchDog` and `PSEWatchDog` when enabled (`common/mlme.c:1797-1815`).
The selected MT7603 AP Makefile defines `DMA_RESET_SUPPORT`, so the
`PDMAWatchDog` stuck branch sets `pse_reset_flag` instead of directly calling
PDMAResetAndRecovery (`common/cmm_mac_pci.c:2145-2154`). An enabled
`PSEWatchDog` can call `PSEResetAndRecovery` (`:2566-2604`) when its
conditions hold, including the gated `bcn_reset_en && pse_reset_flag`
condition, and that recovery calls
PDMAResetAndRecovery (`:2432`). A separate user command reaches
PDMAResetAndRecovery directly through `Set_PDMAWatchDog_Proc` when its
argument is 2 (`common/cmm_cfg.c:1714-1730`); the PSE command has a
similar direct path at `:1761`.

Thus reset can start from the driver's queued periodic command or from a
direct configuration command. None of the inspected call sites supplies an
open/close transaction token or an in-flight-open drain. A future reset
gate cannot simply wait while holding BcnRingLock, and a sleepable wait
cannot be chosen until command-thread dependencies of VIRTUAL_IF_UP and
the direct ioctl context are verified. Next trace those dependencies and
define a nonblocking/deferred reset entry or proven lock order before
implementing rollback. This is source evidence only; no target/device
execution or state change occurred.

## Follow-up 2026-10-22: dequeue-disable writer inventory

The isolated radio candidate generator now pins the ATE source blob and
enumerates every `RTMP_SET_FLAG`/`RTMP_CLEAR_FLAG` writer of
`fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET` in its MT76x3 source tree. The pinned
set is three files: ATE (three SET, two CLEAR), PCI reset (one each), and
MT radio on/off (one each). Any extra or changed writer refuses candidate
generation before output. The manifest records this inventory but keeps
`dequeue_flag_writer_coverage_proven=false`, because the candidate only
serializes the PCI reset writer. The thirteen merged host fixtures passed;
injected extra-writer negative case was refused. This is source-drift control,
not synchronized ownership or device proof. No production/router change.

## Follow-up 2026-10-22: ABI workflow source-path repair

The ABI job's sparse checkout listed the shared `mt76x3` source but omitted
`mt76x3_ap`, while a later assertion read its Makefile. It also read
`source/trunk/configs/boards/WR1200JS/kernel-4.4.x.config`, which was not
included in that sparse checkout. The tracked WR1200JS overlay contains both
required MT7603E selectors, and the pinned `mt76x3_ap/Makefile` contains the
asserted compile flags. The local workflow now checks the overlay config and
includes the small `mt76x3_ap` directory in the sparse checkout. This fixes
the missing-input condition for the existing assertions; CI has not run the
edited workflow. The ABI job still builds extracted fixtures, not the full
candidate driver object. No firmware image or router state changed.

## Follow-up 2026-10-22: virtual-interface rollback and flag ownership

Pinned `mt76x3/common/cmm_cfg.c:1034-1085` shows VIRTUAL_INF_UP increments
the adapter virtual-interface count before first `rt28xx_open`, then undoes
that increment only if startup fails. If the count was already nonzero, it
increments and rebuilds all BSS beacons. VIRTUAL_INF_DOWN decrements the
count and calls `rt28xx_close` when it reaches zero. Therefore, a simple
VIRTUAL_IF_DOWN after a failed CR_ENABLE is not safe without proven
serialization and ownership of that increment: it can close the radio.
`include/rt_os_net.h:178-195` confirms the public wrappers do not add such
transaction ownership.

The dequeue-disable flag also has writers outside PDMA reset: pinned
`hw_ctrl/cmm_asic_mt.c:6095` sets it in `MTPciMlmeRadioOff`, while ATE paths
in `ate/mt_mac/mt_ate.c` set/clear it. These writes are not covered by the
candidate's BcnRingLock sections. The new MBSS_OPEN and CR_ENABLE checks
therefore refuse a broader disabled state, but do not establish a reset
epoch, atomic open or reliable rollback. Next design one transition owner
spanning MBSS_OPEN, VIRTUAL_IF_UP, CR_ENABLE, close and reset, including a
distinct result for first-radio startup, before production integration.
No target compilation or router action occurred in this audit.

## Follow-up 2026-10-22: CR_ENABLE refuses an active reset

The pinned `ap/ap_mbss_inf.c` sequence is MBSS_OPEN, VIRTUAL_IF_UP, then
MBSS_CR_ENABLE. Its original wrapper discards the CR_ENABLE result. In the
isolated `prepare-mbss-cr-check.py` candidate, secondary CR_ENABLE now tests
`fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET` while holding `BcnRingLock` and returns
failure before register reads or writes if reset is already active. The
focused injected-register fixture passed the added reset case and prior
cases. All thirteen assembled host fixtures passed.

This prevents that candidate register block from writing during an already
active reset; it does not make opening atomic across MBSS_OPEN, VIRTUAL_IF_UP
and CR_ENABLE. The wrapper still ignores the returned failure. Blindly
calling VIRTUAL_IF_DOWN there can close the first radio during reset and is
not an established rollback. A complete transition/rollback protocol and
target build are still required. No production or router change was made;
RF behavior is unverified.

## Follow-up 2026-10-22: refuse MBSS open during active reset

The pinned `MBSS_Open` candidate now tests
`fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET` while holding `BcnRingLock`, before
setting any selected BSS beacon intent. It returns failure with the lock
released when reset is active; the existing candidate wrapper propagates
the failed MBSS_OPEN before VIRTUAL_IF_UP. The focused strict MinGW fixture
passed normal, AIRPLAY, BAND_STEERING and combined variants, including the
new reset case. All thirteen merged host fixtures passed with this gate.

This rejects only a reset already active at MBSS_Open. Reset can still begin
after this check and before CR_ENABLE; the wrapper still ignores CR_ENABLE
failure. The flag has other writers. This is host/source evidence only, not
target compilation or RF/device acceptance. The bundle manifest remains
`bss_close_exclusion_proven=false`; production and router were unchanged.

## Follow-up 2026-10-22: paired reset gate and beacon submission

The isolated MT candidate now checks `fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET`
inside the final beacon kickout's `BcnRingLock` and skips submission when
set. `prepare-pdma-reset-gate-check.py` pins `common/cmm_mac_pci.c` and
stages short `RTMP_IRQ_LOCK` sections around the reset path's SET and CLEAR
of that same flag. On the inspected WR1200JS Kbuild variant both lock
macros use the same BH spin lock; this makes the modeled reset-start vs
final-kickout order explicit without holding a lock across DMA waits or
ring cleanup. The recovery candidate also rejects an active reset flag
before and during its final beacon restart. Individual kickout, reset-gate
and recovery fixtures passed, and all thirteen merged host fixtures passed.
The final bundle contains the paired edits; the ABI workflow locally lists
the thirteenth fixture but was not run in CI.

This is not a complete reset/IoT transition protocol. CR enable can still
run during reset, its wrapper currently does not handle a failed CR-enable
return, and other paths also set/clear the global dequeue flag. Target
compile, partial hardware startup cleanup, queue drain and RF silence are
unverified. Keep `bss_close_exclusion_proven=false` and do not install this
candidate into the production image or use it for device acceptance yet.

## Follow-up 2026-10-22: effective lock source and reset gap

Pinned `mt76x3_ap/Makefile` builds the shared MT source directly and does
not include the vendor `os/linux/config.mk` path that conditionally adds
`MULTI_CORE_SUPPORT` for `PLATFORM=BB_SOC`. In the inspected source,
`RTMP_SEM_LOCK` maps to `RtmpOsSpinLockBh`, which maps to `spin_lock_bh`
(`include/os/rt_linux_cmm.h:264`, `os/linux/rt_linux.c:3376`,
`include/os/rt_linux.h:367`). Without MULTI_CORE_SUPPORT,
`RTMP_IRQ_LOCK` also maps to the BH spin lock (`rt_linux_cmm.h:292`).
This is a source/Kbuild inference, not proof of the emitted target compile
flags; a MIPS compile log or object build is still required.

Pinned `PDMAResetAndRecovery` first disables interrupts/PDMA, then takes
`BcnRingLock` to set beacon states IDLE (`common/cmm_mac_pci.c:2069-2094`)
and releases it before the series of `RTMPRingCleanUp` calls and
`AsicEnableBssSync` (`:2098-2107`). `RTMPRingCleanUp(QID_BCN)` does take
the same lock around its descriptor cleanup and index reset (`:1890-1930`).
Thus the beacon ring operation itself is serialized, but the whole reset
sequence is not one atomic close/open transition. Holding the spin lock
across all ring cleanups or the reset polls would be unsafe. The remaining
work is a transition protocol/epoch or equivalent exclusion spanning those
separate critical sections, followed by target compile and device proof.

Local inspection found no MIPS compiler in this worktree; `wsl.exe
--list --quiet` returned usage/help with exit code 1 in this Codex
environment. The ABI workflow downloads a pinned MIPS toolchain and can
cross-compile extracted fixtures; it has not compiled the assembled driver
candidate. No production or router state was changed in this audit.

## Follow-up 2026-10-22: MT BSS-sync ARB writers

`prepare-bss-sync-lock-check.py` pins the MT ASIC source and adds short
`BcnRingLock` sections around the `ARB_BCNQCR0` read/modify/write in both
`AsicEnableBssSync` and `AsicEnableApBssSync`. These writers set the main
hardware queue bits `0x1` and `0x2`; they do not intentionally set the
secondary BSS bit, but unlocked RMW could lose a concurrent CR close/open.
The extracted register-block fixture asserts lock coverage and preserves
preexisting secondary bits. It passed standalone and in the merged bundle;
all twelve radio-bundle host fixtures passed. A pinned-source search found
five direct `ARB_BCNQCR0` writers: CR enable, CR disable, beacon recovery,
and these two BSS-sync functions. The assembled candidate now puts their
RMW sections under the same lock. The workflow locally lists the twelfth
fixture, but CI was not run.

This is only a candidate-level direct-writer inventory. Calls from reset,
scan and periodic AP paths have not been target-compiled or proven safe
under the effective interrupt context. The DMA reset still releases
`BcnRingLock` before ring cleanup and sync restart. Queue drain, device
loss, partial hardware startup and RF silence remain open, so the manifest
keeps `bss_close_exclusion_proven=false`. No production or device change.

## Follow-up 2026-10-22: isolated failed-first-open intent rollback

`prepare-mbss-abort-open-check.py` pins five driver files and stages a new
internal MBSS_ABORT_OPEN ioctl without changing existing command values.
On a failed first `VIRTUAL_IF_UP`, the wrapper invokes the new handler,
which validates the secondary BSS and clears only its beacon-request flag
under `BcnRingLock`, then balances the wrapper's module reference. A
failed MBSS_OPEN ioctl still returns before virtual-up. The new path does
not call MBSS_Close, stop the queue, kick clients or write radio registers.
The staged helper, dispatcher, enum, declaration and wrapper were merged
into the isolated radio bundle; all eleven host fixtures passed. The
rollback fixture passed generic, MT_MAC and MT_MAC+HW NAT MinGW variants.
The ABI workflow locally lists the eleventh fixture; GitHub CI was not run.

This closes the **modeled stale software intent** on that failure path.
It does not prove cleanup of partial hardware startup, beacon DMA/ring
drain, RF silence, target compilation or router behavior. The complete
close/open exclusion protocol and BSS-sync/reset writers remain open.
Nothing was installed into production driver sources or changed on device.

## Follow-up 2026-10-22: bounded secondary-open intent

The pinned `MBSS_Open` candidate now checks null device/adapter, bounds
`BssidNum` **before** `RT28xx_MBSS_IdxGet` loops over that count, rejects
the main BSS 0 and out-of-range/inactive indices, then changes only the
selected beacon-request flag under `BcnRingLock`. Existing AIRPLAY and
Band Steering branches remain in place; the Band Steering notification
stays outside the short lock. Its extracted actual-function fixture passed
four strict MinGW variants: default, AIRPLAY, Band Steering and both.
The candidate was merged with existing MBSS init/close/CR candidates;
all ten merged radio-bundle host fixtures passed. The local ABI workflow
now lists the tenth fixture, but GitHub CI was not run for this edit.

This narrows invalid-open effects and coordinates the successful intent
write with close/recovery. It does **not** clear intent when the subsequent
first `rt28xx_open` fails, prove target lock context, queue drain or RF
silence, or activate IoT in production. Driver/firmware/router unchanged.

## Follow-up 2026-10-22: reject failed MBSS_OPEN ioctl

The isolated `prepare-mbss-open-check.py` wrapper candidate now checks
`CMD_RTPRIV_IOCTL_MBSS_OPEN` before calling `VIRTUAL_IF_UP`. On ioctl
failure it balances its module reference and returns an error. Pinned
`ap_mbss_inf.c` blob `7c736a04eeeddace0bbb0c5c96198d0738f400a2`
was used for generation. The actual-wrapper fixture passed with strict
MinGW warnings in MT_MAC, MT_MAC+HW NAT and generic variants. It checks
that failed MBSS_OPEN never reaches virtual-up, failed virtual-up balances
the module reference, and success/close preserves an existing main
interface reference. These are injected host checks, not a target build.

This correction does not roll back beacon intent when `rt28xx_open` fails
after a successful MBSS_OPEN. `ap/ap.c:1208-1211` rebuilds beacons during
AP startup, and `ap/ap_connect.c:95` consults the secondary request flag.
Thus moving the flag assignment behind VIRTUAL_IF_UP would change the
initial beacon path; no such move was made. Production and router unchanged.

## Follow-up 2026-10-22: exact secondary-open failure path

Pinned source `ap/ap_mbss_inf.c:136-158` invokes MBSS_OPEN before
`VIRTUAL_IF_UP` and CR_ENABLE after it. The wrapper ignores the MBSS_OPEN
ioctl result. `include/rt_os_net.h:178-186` returns a failed VIRTUAL_INF_UP
ioctl as `-1`. In `common/cmm_cfg.c:1034-1071`, that ioctl can fail only on
the first virtual interface (`VIRTUAL_IF_NUM == 0`) when `rt28xx_open`
fails; it then decrements the virtual-interface count. When an interface
is already up, the ioctl increments the count and rebuilds beacons without
an error branch. Thus the currently documented failed-open stale-intent
case is the first-radio-open failure, not every secondary-open call.

The isolated wrapper candidate balances the module reference in that case,
but its failed path still leaves the preceding MBSS_Open beacon-request
flag set. Calling MBSS_CLOSE there is not a proven safe rollback: it stops
the queue, kicks stations and rebuilds beacons while the first radio open
has failed. Moving the flag assignment after VIRTUAL_IF_UP is also
unproven because first radio initialization may consume the flag. The next
driver candidate must provide a narrowly scoped, lock-coordinated intent
rollback on this failure path and prove first-open beacon behavior. No
production or device state was changed in this source audit.

## Follow-up 2026-10-22: secondary CR enable lock

The isolated `mbss_cr_enable` candidate now holds the existing
`BcnRingLock` across the secondary BSS LPON and `ARB_BCNQCR0`
read/modify/write block, matching the disable and recovery candidates.
It does not take this lock or access these registers for the main BSS 0.
The pinned-source MinGW fixture passed. Its injected register operations
assert the lock is held; invalid indices, non-MT mode, BSS 0, selected
queue bit, peer bits and balanced unlock were checked. No driver build or
device test was performed for this candidate.

`MBSS_Open` still sets beacon intent before its virtual-interface-up and
CR-enable sequence. That ordering and the BSS-sync and reset writers need
review before any claim of a complete transition protocol. The changes
remain in an isolated generator, not the production driver or firmware.

## Follow-up 2026-10-22: partial close/recovery critical section

The isolated `mbss_cr_disable` candidate now takes the existing
`BcnRingLock`, clears its selected `bBcnSntReq` intent, evaluates peer intent,
and clears the selected `ARB_BCNQCR0` bit before unlocking. The candidate
recovery handler keeps its two flush polls outside the lock, then takes the
same lock, checks selected intent and secondary netdevice state, performs
the final ARB read/modify/write, and sets `BCN_TX_IDLE` before unlocking.
The preexisting final beacon-kickout candidate rechecks under that lock.

Pinned actual-function host fixtures passed invalid/active CR operations and
lock balance; recovery fixture passed a synthetic close-intent change at lock
acquisition, unchanged success, flush timeouts, device-loss and active reset
branches. All nine merged radio-bundle MinGW fixtures passed after assembly.
The first recovery test attempt failed because the new synthetic-close mode
mistakenly selected the main-BSS test setup; that fixture selection was fixed
before the passing rerun. One generator attempt placed unlock before the
non-MT early return; it was corrected to the actual final return before
passing. These were local test/candidate mistakes, not observed device faults.

This is **partial** exclusion only. `mbss_cr_enable`, `MBSS_Open`, two BSS-sync
writers and the PDMA-reset path do not yet share the complete transition
protocol. MMIO loss still has observation-only guards; the target interrupt
and compile context, selective queue drain and RF silence remain unverified.
The bundle manifest deliberately keeps `bss_close_exclusion_proven=false`.
No production driver or router state was changed.

## Follow-up 2026-10-22: final beacon kickout recheck candidate

`prepare-beacon-kickout-check.py` pins the actual `common/cmm_mac_pci.c` blob
`82db49fa1822a51268d76f23bce94d886f4d50d6` and changes only the
`MT_MAC` version of `RT28xx_UpdateBeaconToAsic`; the separate RTMP/RLT
version remains untouched. It rejects null adapter and invalid/inactive BSS
indices before the existing array lookup. Immediately after taking the
existing `BcnRingLock`, it calls the driver's `BeaconTransmitRequired` again
and unlocks/returns if the selected BSS is no longer eligible. The active
path still submits through the original `HAL_KickOutMgmtTx` and marks
`BCN_TX_WRITE_TO_DMA` under the same lock.

An extracted actual-function MinGW fixture passed null/out-of-range, missing
packet, preclosed BSS, a BSS changed to nonrunning as the lock was taken, and
active submission with balanced lock counts. The candidate is now the sixth
file in the isolated radio-error bundle; all nine assembled host fixtures
passed. ABI workflow loops include the new fixture, but CI was not run here.
Injected packet/lock calls do not prove actual DMA drain or RF silence.

This recheck coordinates with a future close-intent transition only when that
transition uses the same lock. Current `MBSS_Close` still clears the intent
without it, and the ARB register writers remain unsynchronized; hence bundle
metadata continues to mark close exclusion false. No production driver,
firmware image or router state was changed.

## Follow-up 2026-10-22: complete beacon transition writer inventory

Pinned `mt76x3_ap/Makefile` selects the shared `../mt76x3` objects. A scoped
search over that source found all direct `ARB_BCNQCR0` writes: secondary CR
enable/disable in `ap/ap_mbss.c:283-285,327-329`; recovery restart in
`hw_ctrl/cmm_asic_mt.c:1390-1392`; main/AP BSS sync in the same file at
`:1491-1493,1557-1559`. The diagnostic read at `:1085` is not a writer.
The reset path calls `AsicEnableBssSync` only after releasing BcnRingLock and
cleaning rings (`common/cmm_mac_pci.c:2069-2107`). Other located calls are
in AP start/mode/MLME, radar and scan; their wider lock contexts still need
target review before adding a lock to the sync functions.

The last packet submission is a separate race. `RT28xx_UpdateBeaconToAsic`
chooses the beacon packet before locking, then holds `BcnRingLock` around
`HAL_KickOutMgmtTx` and the software state change at
`common/cmm_mac_pci.c:2701-2713`. It does not recheck BSS eligibility under
that lock. A beacon update that passed an earlier eligibility check may
therefore submit after close begins. A correct transition must recheck the
selected BSS inside this existing short critical section. It must also
serialize close/open intent and the selected register read-modify-write with
recovery, without holding a spinlock across flush polls or the entire frame
construction. In-flight DMA/RF drain remains a separate acceptance condition.

The active `mt76x3_ap/Makefile` has no `MULTI_CORE_SUPPORT` flag; the only
located definition in the separate `mt76x3/os/linux/config.mk:1865-1869` is
conditional on `PLATFORM=BB_SOC` and `CONFIG_MIPS_TC3262=y`. Thus the pinned
board/Kbuild source points to the BH branch of `RTMP_IRQ_LOCK`, matching
`RTMP_SEM_LOCK` on BcnRingLock. The exact emitted compile command is not yet
available, so this is a source-level conclusion rather than a compiled-module
claim. No lock was added in this inspection; source and router state unchanged.

## Follow-up 2026-10-22: active MT7603 recovery compile branch

The selected WR1200JS board config at pinned source revision
`c25283e915a2a00a763774dd255b14aff997285e` sets
`CONFIG_MT7603E_RALINK_MT7603E=y`, PCI support and
`CONFIG_MT76X3_AP=m`. `mediatek/Makefile` builds `mt76x3_ap/`; its Makefile
uses objects from `../mt76x3` and line 788 adds `-DDMA_RESET_SUPPORT` and
`-DTXRXCR_DEBUG_SUPPORT` in the selected MT7603 block. The separate
`mt76x3/os/linux/config.mk` default `HAS_DMA_RESET_SUPPORT=n` is not the
deciding Makefile for this Kbuild module. This corrects the earlier fixture
coverage assumption. The exact emitted compiler command and shipped module
still need CI/image confirmation.

The extracted `APCheckBcnQHandler` fixture now compiles both active macros.
New injected cases exercise the main-BSS DMA-reset branch: observed PCI clock
loss during its MMIO read stops before subsequent reset action; unchanged
busy-DMA state follows the vendor force-reset branch; the debug checkpoint
calls its existing diagnostic hook. The earlier secondary recovery cases stay
covered. The focused fixture and all eight assembled radio-bundle MinGW
fixtures passed. The ABI workflow now checks the selected board config and
Kbuild flag line before compiling the fixture; that CI gate was not run here.

This source/host result does not show safe reset concurrency, target compiler
success, actual RF drain or a working third BSS. The shared close/recovery/
reset protocol remains necessary. No production module or router state changed.

## Follow-up 2026-10-22: recovery rechecks beacon eligibility

The isolated `prepare-beacon-recovery-check.py` candidate now calls the
driver's existing `BeaconTransmitRequired(pAd, apidx, pMbss)` after both flush
polls and before the final `ARB_BCNQCR0` restart. Its declaration exists at
`include/ap.h:195`; the merged radio bundle also contains the secondary-BSS
running-device guard in that decision function. A BSS already closed before
this check is refused without marking its beacon state IDLE. The caller still
receives `is_pretbtt_int = FALSE`.

The actual-function injected fixture passed two additional cases: beacon
intent cleared during recovery and secondary netdevice no longer running.
The existing success, timeout and observed device-loss cases also passed.
All eight merged radio-bundle MinGW fixtures passed after assembly from pinned
source. Only the inherited signed comparison warning was suppressed for the
recovery fixture. The bundle manifest now explicitly says BSS-close exclusion
is unproven. `git diff --check` passed.

This is a last-moment eligibility observation, not mutual exclusion. A close
can still start between the decision and MMIO write. The shared transition
protocol, other ARB writers, DMA-reset order, final kickout decision and
target/kernel/device checks remain open. No production source or router state
was changed.

## Follow-up 2026-10-22: observed device-access loss rejects recovery

Recovery candidate checks HALT/NIC flags and, under RTMP_MAC_PCI, bPCIclkOff
before BSS use and before/after each direct MMIO statement in the handler.
Observed unavailable access returns pretbtt=false without restart or IDLE.
Extracted tests passed entry clock-off, synthetic-zero first-poll clock loss,
second-poll NIC loss and clock loss during final restart read, plus timeouts
and success. Eight merged bundle MinGW fixtures rerun passed. Registers/flags
injected; inherited sign-compare warning alone suppressed for recovery.

These are fail-closed observations, not mutual exclusion. A transient state
change and revert between checks is not detected; no real MMIO availability
contract or concurrent clock/reset/close exclusion is proven. Effective target
IO wrappers and DMA_RESET_SUPPORT configuration still require verification.
No production installation, firmware build or router state change occurred.

## Follow-up 2026-10-22: close ordering, lock context and MMIO availability

Pinned Linux net/core/dev.c:1394 clears __LINK_STATE_START, 1402 commits it
with smp_mb__after_atomic, and 1417-1418 invokes ndo_stop. Thus normal netdev
close clears netif_running before MBSS stop callback. This does not alone
serialize a recovery that tested the state earlier.

Driver BcnRingLock is allocated at common/rtmp_init.c:136 and used for DMA
completion and beacon ring writers. include/os/rt_linux_cmm.h:264-301 maps
SEM_LOCK to BH spinlock and IRQ_LOCK to irqsave under MULTI_CORE_SUPPORT,
otherwise BH locking. A future short final restart/disable protocol can use
the same initialized ring lock only after all relevant callers/writers and
effective macro selection are checked. Never hold it across the flush polls.
No lifecycle-lock patch is installed by this source audit.

Critical observation: PCI MMIO macro in include/os/rt_linux.h:1008-1016 returns
zero when bPCIclkOff, and write at 1040-1044 silently skips access. A cleared
flush bit can therefore be a synthetic zero, not device progress. The effective
target IO wrappers (including rt_drv.h alternatives) and clock/NIC exclusion
must be established before treating polling or write readback as hardware
receipt. Current injected registers cannot prove that availability contract.
Next scope: shared final restart/disable protocol with truthful device-access
failure handling; do not mark RF quiescence based only on zero register values.

## Follow-up 2026-10-22: beacon recovery no longer treats flush timeout as idle

Pinned APCheckBcnQHandler at cmm_asic_mt.c:1345-1348 and 1368-1371 breaks after
poll timeout but continues through queue restart at 1390-1392 and software IDLE
at 1394. Candidate returns with pretbtt=false on either timeout and adds
null/index/HALT entry checks. It does not free ring packets or declare drain.
Successful recovery retains existing behavior, including its unprotected
restart: a concurrent BSS-close race still requires lock/order work.

Function-only merge retains separate checked DMA poll in radio-error bundle.
Eight host MinGW fixtures passed, including first/second flush stuck and
successful selected-bit restart. Recovery fixture required suppressing inherited
vendor signed/unsigned interval comparison warning; other warnings remain
errors. IO/constants injected; no DMA_RESET_SUPPORT variant, actual concurrency
or RF evidence. CI gates updated but not run; no production/router changes.

## Follow-up 2026-10-22: same-file MBSS candidates merged coherently

prepare-mbss-lifecycle-candidate.py pins original ap_mbss.c, runs existing
init/close/CR preparers, starts from init candidate (retaining its private-free
helper) and replaces only original matching close/CR functions. Conflicting
functions or other close/CR edits are refused. Final functions are re-extracted
into each test fixture; manifest hashes merged source and fixtures.

Radio-error bundle now includes that merged source and additional close/CR
fixtures, preserving existing open/netdev/beacon/DMA candidates. Three merged
tests and seven integrated radio-bundle tests passed strict MinGW. Allocation,
registration, registers and locks are injected. Full-driver compile, selective
queue drain, RF quiescence and BSS allocation strategy remain open. CI gates
added, not run; no production installation or device state changes.

## Follow-up 2026-10-22: per-BSS CR disable is a register request, not drain

Pinned AP ioctl at ap_cfg.c:14951-14954 calls mbss_cr_disable and propagates
nonzero failure. MBSS_VirtualIF_Close discards that result. ap_mbss.c:291-332
scans peer beacon flags, writes selected LPON_SBTOR timing control and clears
selected ARB_BCNQCR0 bit. No queue-empty poll, write readback or synchronization
with a running beacon-update handler occurs in this function. Do not equate
its zero return with no pending RF frames.

Both mbss_cr_enable and disable originally reject only negative index. Pinned
candidate now bounds device/adapter/index, active BssId and BssidNum array count
before registers or peer loop. Strict MinGW actual-function checks passed
invalid/no-IO, non-MT bypass and selected start-bit manipulation preserving
other queue bits; disable retains peer timing register in the modeled case.
Register addresses/bit constants and IO are injected, not hardware proof.
Candidate remains separate from same-file init/close changes: combine by
reviewed function slices, not wholesale overwriting one candidate with another.

## Follow-up 2026-10-22: checked OFF builder is adapter-wide, not IoT control

Pinned andes_mt.c:1751-1786 and andes_mt.h:422-427 establish RadioOnOff payload:
control byte (OFF=2), three reserved zero bytes. Candidate builder allocates a
message, requests synchronous response/no retries/eight-byte result, enables
checked parse and appends the zero-initialized OFF payload. It returns owned
message without calling sender or queue and never sets software radio flags.
Strict MinGW extracted builder passed allocation failure, initialization shape
and exact bytes. MCU preparer and combined bundle track builder hash; sanitizer
and MIPS gates are added, not executed. No live issuer or radio operation bound.

The command has no BSS index: it is not a selective ra2/IoT switch. Do not wire
it to IoT toggle or infer main/guest preservation. Selective BSS quiesce and
approved whole-adapter recovery are different operations. Actual activation
still requires the unresolved BSS creation/address preservation/lifetime path,
target compilation and recoverable on-device evidence.

## Follow-up 2026-10-22: merged candidate source validation

prepare-radio-queue-candidate.py stages queue cleanup/worker, truthful enqueue
and MCU ACK preparers, rejecting overlapping paths and changed input tools or
sources. Final manifest written only after success records source git blobs,
output SHA256 and preparer/helper hashes. Ten driver files and two explicit
fixture assets are included. It is a partial change tree, not a complete driver
or production installer, and retains all target/runtime/lifecycle flags false.

Five strict MinGW extracted/injected tests passed using that merged tree:
ACK receiver, sender, dispatcher/sender, PCI kickout and queue/result with actual
HALT/NIC/cleanup slices. Initial wrong count expectation and missing ACK fixture
asset were corrected before success. Existing output and drifted source were
refused; six original input git blobs reverified. Full kernel build, real
concurrent lifecycle, radio issuer and on-device acceptance remain unproven.

## Follow-up 2026-10-22: actual admission and cleanup slices tested

Composition fixture --cleanup-candidate extracts staged CMDHandler HALT/NIC
eligibility expression, unconditional generic cleanup/free block, and pending
RTPCICmdThread cleanup/free block. Strict MinGW passed base and slice modes
against staged headers. Added cases verify NIC loss after accepted enqueue and
shutdown cleanup under modeled CmdQLock, alongside HALT, timeout and early
completion cases. Queue buffers and shared result refs are released once.
This is not the full CMDHandler switch or thread loop: worker invocation,
OS scheduling, locks and allocations are injected. Real task kill, queue drain
concurrency, target build and RF acceptance remain open. CI gates unexecuted.

## Follow-up 2026-10-22: actual enqueue/result composition passed locally

prepare-queued-composition-check.py composes staged actual cmm_cmd enqueue body
with queued-work producer/worker and shared result/cleanup. Strict MinGW passed
NIC/allocation failures, stopped queue, no-operation failure, queued timeout,
modeled HALT cleanup, running uncertainty, caller-first release and immediate
worker completion before enqueue returns. Queue buffer and shared result frees
are counted separately. This replaces the injected enqueue primitive for this
fixture; OS allocation/locks/wakeup/scheduling remain injected. Actual full
CMDHandler/shutdown and real concurrency are not covered. CI gates added but
not run. No checked MCU operation or production installation is bound.

## Follow-up 2026-10-22: cancellation hooks in staged driver cleanup paths

prepare-queue-cleanup.py stages pinned common/rtmp_init.c blob
a0d9eb2adbbb2ac13e8314806a5ded2f30793623 and os/linux/rt_rbus_pci_drv.c blob
07f1171dc14081af70ba6a1537bf896a9b141be3. It inserts cleanup before existing
generic buffer free in CMDHandler (including HALT/NIC skipped dispatch) and
RTPCICmdThread pending shutdown path. All source bytes checked before output;
originals unchanged. No command producer or radio worker is installed.

Internal candidate tag 0x0D73F001 had no pinned mt76x3 git-grep matches.
queued-cleanup.h checks tag, internal origin and exact envelope size, clears
envelope pointer, cancels pending/running result and drops queue reference once.
It may run under CmdQLock: cancellation takes only result spinlock, completion
is non-sleeping and no inverse queue acquisition is introduced by these helpers.
Future producer/worker must preserve that order and never accept userspace
pointers as envelopes. Origin/size checks are not authentication of a pointer.

Strict MinGW fixture compiled copied staged headers and passed helper bypass,
one-time cleanup and result lifetime/state tests. Structural checks confirmed
both hooks precede generic free. Actual complete driver functions, target build
and concurrent shutdown remain unverified. Candidate manifests keep producer,
radio operation and production installation false. Next bind checked producer
and worker in isolation, then verify actual queue execution/cancellation.

## Follow-up 2026-10-22: shared queued result implemented in isolation

tools/iot/queued-result.h provides caller/queue kref ownership, spinlocked
state and terminal completion. Queue ref must be acquired before enqueue and
released on rejection or after cleanup. A timed-out caller may release its ref
without freeing worker memory. QUEUED cancellation prevents start; RUNNING
cancellation produces UNCERTAIN and ignores later success. It does not stop
hardware. Completion is outside state lock, with invoking owner still holding
a ref. No stack response storage or callback into a released caller.

check-queued-result.c strict MinGW passed deterministic allocation/ref release,
caller-first and worker-first terminal orders, queued cancellation, running
uncertainty, duplicate terminal calls and single release. Kernel primitives are
injected: no actual concurrency/target build proof. No production inclusion.
Next actual queue-envelope cleanup hooks on HALT skip and thread shutdown;
the header alone cannot protect an accepted result whose queue ref is forgotten.

## Follow-up 2026-10-22: enqueue acceptance cannot use legacy success

Pinned common/cmm_cmd.c blob c053649a0c8c12edf459300af022b64ff26d2fca:
RTEnqueueInternalCmd copies payload at 139, tests insertion under CmdQLock at
155-166, frees rejected command/payload at 168-172, then returns success at 177.
Using that return as ownership transfer receipt can strand a checked waiter.
prepare-checked-enqueue.py stages a single shared implementation with legacy
wrapper preserving behavior and checked wrapper returning actual status.
Strict MinGW extracted candidate tests passed NIC, each allocation failure,
stopped queue and successful copied payload, both wrappers. Operations injected;
not kernel concurrency or target evidence. Candidate not installed/bound.
Accepted commands still require shared result lifetime and cancellation on
HALT dispatch skip and command-thread shutdown before releasing their buffers.

## Follow-up 2026-10-22: watchdog worker context narrows lifecycle design

Pinned mt76x3 source proves this route:
`common/mlme.c:1704-1712` timer enqueues CMDTHREAD_MLME_PERIOIDC_EXEC;
`common/rtmp_init.c:2649-2653` dispatch calls MlmePeriodicExec;
`common/mlme.c:1795-1814` calls PDMA/PSE watchdog under feature/runtime guards.
`os/linux/rt_rbus_pci_drv.c:159-160,1822-1852` starts RtmpCmdQTask and runs
CMDHandler in its kernel thread. Do not infer softirq execution from the old
DISPATCH_LEVEL comment above the timer wrapper.

Direct PDMA reset callers found at `common/cmm_cfg.c:1726-1728` (manual proc),
`common/cmm_mac_pci.c:2151` (watchdog without DMA_RESET_SUPPORT), and 2432
(PSEResetAndRecovery, itself reached by PSE watchdog at 2598). Guard presence
does not establish exact shipped configuration or live enabled watchdogs.

Proposed integration direction, not implemented: execute checked operation on
existing command thread to serialize against periodic watchdog; admit via
RTNL ioctl and keep direct reset callers under reviewed exclusion. Thread must
not acquire RTNL while ioctl waits holding it. A synchronous result object must
outlive both worker and caller, including timeout and queued cancellation.

Close source `common/rtmp_init_inf.c:875-888` stops RX tasklets before killing
command thread, so in-flight firmware ACK may become unavailable and cannot
be reported as success. `RtmpMgmtTaskExit` at rt_rbus_pci_drv.c:190-208 sets
STOPED, invokes task kill, but only logs failure and returns void. It is not
an unconditional successful join receipt. CMDHandler at rtmp_init.c:2523
skips dispatch when HALT/NIC flags are set; thread exit at
rt_rbus_pci_drv.c:1854-1878 frees pending buffers. New checked queued work must
receive cancellation completion before buffer release, with caller ownership
explicitly retained. Next implement/review these ownership rules in the actual
queue path; no new sleeping lock in tasklet/timer code and no production binding.

## Follow-up 2026-10-22: existing ioctl serialization and no replay

Pinned target Linux, not a newer API assumption: WEXT dispatch holds RTNL
around wireless_process_ioctl at net/wireless/wext-core.c:988-990; private
SIOCDEVPRIVATE dispatch holds it around dev_ifsioc at net/core/dev_ioctl.c:555-557.
mt76x3/os/linux/rt_main_dev.c:582-607 maps netdev to adapter and AP ioctl.
This provides an existing process-entry serialization candidate; do not acquire
RTNL recursively in its handler. Normal close context and asynchronous recovery
still require tracing before claiming adapter lifetime protection.

Checked sender now rejects need_retransmit before enqueue. Extracted sender
and composed dispatcher/sender strict MinGW checks passed a retry-enabled
request rejected with one private free and no wait/queue. This prevents legacy
implicit replay in the checked path; normal commands unchanged. Injected tests
do not prove kernel concurrency. Candidate remains separate and unbound.

## Follow-up 2026-10-22: cleanup caller ordering and admission contract

Read-only search of pinned c25283e915a2a00a763774dd255b14aff997285e:

- `common/cmm_data_pci.c:1526-1555`: RX coherent recovery returns early for
  MT7603/MT7628 at 1536-1540, before PDMA disable and QID_CTRL cleanup. Do not
  assume this path retires an outstanding control packet on the IoT radio.
- `common/cmm_mac_pci.c:1982-2112`: PDMAResetAndRecovery disables software
  dequeue, interrupts and DMA, but abort polls at 2027-2031 and 2054-2057 only
  log/increment failure and continue to QID_CTRL cleanup and DMA reenable.
  This void recovery routine is not a successful DMA-stop receipt.
- `mcu/andes_core.c:626-650`: PCI exit clears admission flag and MCU_INIT,
  kills command tasklet, cleans ACK and other queues, then destroys locks.
  There is no waiter-drain operation in this function. A spinlock protects
  queue edits, not a waiter using a message between lock acquisitions.
- Exit callers include `mcu/mcu.c:85-94` and full close at
  `common/rtmp_init_inf.c:938-966`. Full close releases IRQ before MCU exit
  and frees/resets ring memory after MCU exit. This ordering does not alone
  establish exclusion with an independently admitted checked caller.

Required integration contract: serialize new checked request admission with
all relevant MCU exit/reset paths; reject new callers once stopping begins;
retain message/adapter until the waiter has left; drain waiters before ACK
cleanup/lock destruction; retire ring packets only after proved DMA exclusion.
Do not wait for a sleeping sender while holding an ACK/ring spinlock. Do not
reuse global recovery or a software flag as proof. These are design obligations,
not implemented lifecycle guarantees. Candidate manifest records both missing
proofs and prerequisites explicitly. No production issuer is bound.

## Follow-up 2026-10-22: control-ring retirement is conditional

Pinned c25283e915a2a00a763774dd255b14aff997285e, mt76x3:
`common/cmm_data_pci.c:2602-2658` (blob
646beb40bc7acb8ee861190b717f8c9a465d0fae) reads hardware DMA index under
CtrlRingLock and releases only completed slots. No index progress means no
packet release. Actual extracted handler passed injected MinGW no-progress,
progress, repeated invocation, empty slot and wrap checks. Vendor unused FREE
counter warning alone suppressed; source unchanged. This is no real DMA proof.

`common/cmm_mac_pci.c:1841-1880` separately releases every QID_CTRL slot under
the ring lock. Call ordering and DMA exclusion must still be traced. Sender
`mcu/andes_core.c:830-836,873-885` unlinks timed-out ACK only with MCU_INIT,
but frees message directly when MCU_INIT is false. Combined with queue cleanup
at 511-526, active waiter/teardown ownership is not proven. Do not bind the
candidate issuer or claim post-failure ring retirement until this is resolved.

## Follow-up 2026-10-22: direct RX context and full-close ordering established

The existing local bare backup `../firmware-source-backup/padavan-4.4.git`
contains the pinned commit and complete searchable driver objects. Read-only
git grep/show was used; no checkout, clone, ref change or fetch occurred.
This is a better local source-search route than relying on incomplete remote
code search. It does not supply a usable Linux compiler/runtime by itself.

One concrete direct-event route is now established:

- os/linux/rt_rbus_pci_drv.c:389, rx_done_tasklet calls rtmp_rx_done_handle;
- tx_rx/wdev_rx.c:2878 obtains a packet through GetPacketFromRxRing;
- common/cmm_data_pci.c:1836 calls parse_rx_packet_type;
- common/cmm_data.c:621-622 calls chipOps.rx_event_handler for RX_EVENT;
- mcu/mcu.c:179 assigns AndesMTRxEventHandler;
- andes_mt.c:3015 directly dispatches the event and matched ACK callback.

Thus this callback can run in the network RX tasklet, distinct from
MCUCtrl.cmd_msg_task. Blob identities: rt_rbus_pci_drv.c
`07f1171dc14081af70ba6a1537bf896a9b141be3`, mcu.c
`454f29c3e57fa17a87df1d1fc12500739e1dc4fd`; other blobs as recorded above.

Full rt28xx close calls RtmpNetTaskExit at rtmp_init_inf.c:875, whose
rt_rbus_pci_drv.c:106 implementation kills network RX tasks, then later
MCU_CTRL_EXIT at 959 kills the command tasklet before queue cleanup. This
provides actual close-path synchronization, superseding the narrower unknown
about that ordering. It does not serialize an ordinary sender timeout against
an already-running callback during otherwise active operation, nor establish
all other MCU reset callers or waiting-process ownership.

Candidate design direction: keep only the new short, non-sleeping checked
response parse/result/completion inside ackq_lock so timeout unlink cannot
overtake it. Do not move all generic response handlers under that lock: they
have unrelated hooks and unreviewed locking/sleeping requirements. Store
result in message-owned state and consume it before queue ownership release;
separately exclude lifecycle teardown while the checked sender is active.
This design is not implemented/validated yet; no generic reference-counting
rewrite or production callback change was made from the partial proof.

## Follow-up 2026-10-22: MCU callback/teardown ownership trace

Pinned andes_core.c (blob 6b430c071742b839a77403bf76d5a4f592abc138):
AndesCtrlPciExit:626 clears in-band/MCU_INIT flags, kills cmd_msg_task, then
cleans queues and frees their locks. AndesCmdMsgBh:447 processes rx_doneq
before tx_doneq; completed/timeout messages in tx_doneq are freed there.
This is real tasklet synchronization and must not be ignored in a lifetime
analysis. It does not by itself establish lifetime for every event entry.

Pinned andes_mt.c:2996 AndesMTRxEventHandler allocates an RX message and calls
AndesMTRxProcessEvent directly at 3015, before freeing the RX message. The
matched ACK message is a different object from that temporary RX message.
AndesMTRxProcessEvent finds it under ackq_lock at 2929-30 and releases that
lock before callback/ack_done access at 2932-69. Sender timeout can unlink it
under the queue lock and later queue it for free (andes_core.c:821-885).

Do not assume command-tasklet serialization merely from the existence of
AndesCmdMsgBh: exact callers/context and shutdown of the direct MT event entry
still need tracing. Nor does killing that tasklet alone prove a waiting
process/caller's lifetime or cancellation handshake. No use-after-free is
claimed reproduced or fully validated here; this is the ownership proof gap
that prevents installing a stack-result callback or declaring an MCU checked
command ready. Next trace direct RX entry/interrupt-task teardown and waiter
ownership, then design result storage within proven message lifetime.

Partial candidate bundle manifest now explicitly keeps MCU lifetime, RF
quiescence and activation binding false, with no selected BSS allocation
strategy. No driver transport edit or device operation occurred.

## Follow-up 2026-10-22: firmware command completion is not RadioOff acceptance

Pinned mcu/andes_mt.c blob cd3b3c371a505f510f1081ba6be0585c351f492e,
mcu/andes_core.c blob 6b430c071742b839a77403bf76d5a4f592abc138,
include/mcu/andes_mt.h blob 2a413a391b854f6c614a74105ba62ffa47546e0f,
and include/mcu/andes_core.h blob ddd27a9cab7f03e22b74116e27bc8e442b573658
were inspected through the connector.

CmdRadioOnOffCtrl (andes_mt.c:1751) requests synchronous eight-byte response
using EventExtCmdResult and returns AndesSendCmdMsg's transport result.
EventExtCmdResult:1642 converts/logs firmware status and calls a hook, but does
not propagate status to the sender or validate the returned extended command
ID against the requested RadioOnOff ID. Header definitions give that ID as
0x05, OFF request value 2 and success status 0; response layout is ID byte,
three reserved bytes and little-endian 32-bit status (andes_mt.h:528).

At andes_mt.c:2948-2972, response length mismatch skips the callback, updates
expected length and still completes a waiting command. AndesSendCmdMsg:818-889
does not convert missing/malformed response or firmware status into failure
after a completed wait. Thus transport zero alone is insufficient acceptance.
This is source evidence, not a reproduced rejected OFF on the running device.

A checked command must require matching extended ID, exact payload length,
explicit success status and completion associated with the current message;
timeouts, missing callbacks and malformed replies must refuse success. Do not
add a callback writing to a caller's stack response without proving timeout/
late-callback lifetime. The command message has no existing result-status
field; received callbacks run after releasing ackq_lock. A transport-result
patch needs ownership/synchronization review before integration, rather than
blindly replacing the shared handler for all firmware commands. Even a valid
firmware reply does not replace DMA/MAC readback or RF acceptance.

## Follow-up 2026-10-22: physical radio-off chain and DMA poll candidate

Pinned sources: common/mlme.c blob bb23e40cf3301df8d0e58d9fb9f25ef6fdba1c41,
common/cmm_mac_pci.c blob 82db49fa1822a51268d76f23bce94d886f4d50d6 and
hw_ctrl/cmm_asic_mt.c blob a8c0c0ec59c7e51c88296111934597064cf36c4a.
Under their PCI/RBUS/MT guards, APShutdown -> MlmeRadioOff:2978 ->
PciMlmeRadioOFF:3091 -> MTPciMlmeRadioOff:6071. Effective board guards still
need target confirmation; this describes the inspected source route.

MTPciPollTxRxEmpty:5990 returns void, logs TX/RX timeout without reporting
failure, and accumulates idle samples without resetting its count on busy
samples. Early NIC disappearance returns with POLL_IDLE still set after the
routine acquired it. MTPciMlmeRadioOff ignores completion status, sets its
RADIO_OFF software flag after PDMA disable, and has a separate iwpriv/one-time
firmware branch that writes AGG_TEMP instead of sending CmdRadioOnOffCtrl.
Thus the software flag is not a successful firmware/DMA/RF completion receipt.

prepare-dma-idle-check.py adds a separate BOOLEAN poll candidate beside the
original function, leaving existing signatures/callers and radio-off behavior
unchanged. It requires consecutive idle windows, returns failure on either
timeout/disappearance, clears its own poll flag on exit and refuses an already
set flag. Caller must serialize writers. Actual extracted polling control flow
passed strict MinGW injected idle/busy/intermittent/disappearance/foreign-flag
cases. Initial fixture pointer-macro/indentation errors were corrected before
success. No register I/O occurred. Register-read error detection, effective
ATE/board variants, target compile and hardware behavior remain unverified.

Added separate helper to partial candidate bundle and sanitizer/MIPS gates;
extended bundle and those gates not executed. This helper alone does not
implement QUIESCE: queue synchronization, firmware acknowledgement, MAC/PDMA
readback and restoring current main/guest state still require integration.

## Follow-up 2026-10-22: beacon recovery is not a quiescence primitive

Pinned hw_ctrl/cmm_asic_mt.c, blob
`a8c0c0ec59c7e51c88296111934597064cf36c4a`, APCheckBcnQHandler:1194 is called
from ap_connect.c:628 after the beacon-decision gate when the buffer is not
idle. The handler writes ARB_BCNQCR1 at 1339 and polls its flush bit. At more
than 1000 waits it logs and breaks, rather than returning failure (1345-47).
The later stuck-beacon flush at 0x21c08 has the same timeout continuation
(1368-71). Regardless of either timeout, the final code ORs the BSS start bit
into ARB_BCNQCR0 at 1390-92 and sets bcn_state = BCN_TX_IDLE at 1394.

Therefore calling this recovery handler is not a safe teardown flush, and
observing software IDLE cannot establish successful hardware drain. These
are exact source paths, not a reproduced stuck queue on the owner's router.
The new secondary beacon-decision candidate prevents new calls for a closed
interface at the initial decision point, but does not synchronize an already
running handler with close or cancel already queued frames.

MBSS_VirtualIF_Close:176 calls MBSS_CR_DISABLE first, then MBSS_CLOSE and
VIRTUAL_IF_DOWN, discarding ioctl results and returning zero. Thus its normal
return and administrative DOWN alone are not RF-quiescence receipts. No
claim is made that there is no other safe hardware stop path; it remains to
trace an actual shutdown/synchronization path and its completion observation.
Activation backend QUIESCE contract now explicitly requires that evidence
before teardown and forbids using these indirect indicators as substitutes.
No production driver patch, hardware-register access or router change occurred.

## Follow-up 2026-10-22: failed netdevice private ops ownership

Pinned target kernel net/core/dev.c, blob
`221c420741a32e6c8fcc177d93a07200e041569f`, was inspected through the connector.
register_netdevice:6804 unwinds failed late notification registration with
rollback_registered, rcu_barrier and NETREG_UNREGISTERED. Earlier failures
remain uninitialized, calling ndo_uninit where applicable. free_netdev:7366
handles uninitialized/unregistered devices and does not free netdev_ops.

Pinned rt_linux.c allocates ops through vmalloc in RtmpOSNetDevOpsAlloc:1548
(function location to confirm against future revisions), assigns them in
RtmpOSNetDevCreate, and vfree's them only after unregister_netdevice in
RtmpOSNetDevDetach:1619. RtmpOSNetDevFree:1505 only calls free_netdev. Therefore
the isolated failed-init candidate's prior device-free-only cleanup leaked
the separately allocated ops; calling Detach would be the wrong substitute.

Candidate now has a dedicated unregistered-device helper that vfree's and
clears ops for kernel >=2.6.31 before device free, used only in failed wdev
registration and failed Linux Attach branches. Normal successful ownership
stays with Detach. Strict MinGW injected tests passed single ops/device release
and preservation of successful lower-BSS allocations. No kernel execution,
target build, production installation or live RF acceptance follows.

Still separate: RtmpOSNetDevCreate's name-allocation failure also calls
device-free-only after ops allocation; candidate does not yet repair that
earlier internal failure. Real register failure callbacks/notifiers, effective
board guards and outer activation/recovery remain to verify.

## Follow-up 2026-10-22: Linux registration failure cleanup candidate

Board template enables CONFIG_MT7603E_MAC_REPEATER_SUPPORT. The registry helper
calls RxTrackingInit even after a failed slot insertion, so that side effect
was traced rather than assumed absent. Pinned common/ba_action.c:2165, blob
`a9d6af04bbfcc39907f95a69928ee36577743cf8`, shows only assignments to embedded
rx_tracking fields (including zeroing the embedded address); no allocation,
timer or hardware operation occurs in that function. Pinned rt_linux.c:1505
shows RtmpOSNetDevFree calls free_netdev, not unregister_netdevice.

Extended isolated prepare-mbss-init-check candidate to inspect Attach status.
On failed Linux registration, remove the acquired wdev slot, clear if_dev,
reduce BssidNum and free the unregistered device. Do not invoke normal detach
or beacon deinit: attachment and beacon initialization did not succeed.
Already-created lower BSS indices are preserved. The slot cleanup relies on
serialized init with the just-acquired registry entry still present; actual
driver registry/concurrency and netdev_ops allocation lifetime need target
review before production use. No general safe reload claim follows.

Strict MinGW actual-MBSS_Init injected tests passed index-registration failure
and Linux-registration failure at BSS 1 and 2, success and one-time guard.
They inject the registry/free/register operations, so do not establish Linux
registration unwind, auxiliary EZ_SETUP behavior or real resource lifetime.
Existing sanitizer/MIPS fixture gates will exercise this extended fixture
when run; neither was run here. Production driver remains unchanged.

## Follow-up 2026-10-22: third-BSS creation failure cannot be treated as success

Re-fetched pinned upstream `ap/ap_mbss.c`, blob
`92d3b01b7be6dd7bcdfe2bc8fbc74b6838ac3b9f`, and `os/linux/rt_linux.c`,
blob `db61215d188d82a50f3468747fff871318fc4b72`, at
`c25283e915a2a00a763774dd255b14aff997285e` through the GitHub connector.

- MBSS_Init assigns `wdev->if_dev = pDevNew` at line 123. On failed
  `rtmp_wdev_idx_reg` (124), it frees pDevNew (127) and breaks without clearing
  that pointer or reducing BssidNum. This differs from allocation failure,
  which reduces BssidNum at 109. The function then sets FlgMbssInit TRUE (162).
- It discards RtmpOSNetDevAttach's result at 152 and continues initialization.
  The actual helper at rt_linux.c:1659 calls register_netdevice/register_netdev
  and converts a nonzero registration result to NDIS_STATUS_FAILURE. It does
  not free the netdevice or erase the caller's wdev pointer on that path.

Therefore neither FlgMbssInit nor the configured BssidNum is a creation
receipt. A live controller must verify the actual registered ra2 identity and
its driver/BSS ownership before attach/open; driver failure recovery must
handle allocation, wdev-registration and Linux-registration separately. A
generic repeat of MBSS_Init is not valid recovery because the one-time flag
can already be set. Do not call detach on an unregistered object blindly.

This is source control-flow evidence, not a reproduced kernel fault or a
claim that current ra0/ra1 hit this branch. Existing wrapper-open tests do not
cover MBSS_Init. Next inspect exact wdev registration ownership and teardown
before preparing a failure cleanup change; retain quarantine on uncertainty.
No production driver patch, target compilation or router operation occurred.

## Follow-up 2026-10-22: legacy module helper returns are not lifecycle proof

Fetched pinned
[user/rc/common_ex.c](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/user/rc/common_ex.c),
blob `56ef8174acc016ccab05f5151b4e48a694234235`.
module_smart_unload returns 1 immediately for refcount>0 WITHOUT issuing an
unload command, and also returns 1 after a successful removal command. In
contrast, module_smart_load returns 0 when already loaded. Neither Boolean
alone proves the desired transition or a fresh adapter generation.

Extracted actual helper functions compiled/executed under strict MinGW with
injected module status/command callbacks. Confirmed busy-unload=1/no command,
missing-unload=0/no command, failed/successful removal command cases, and
already-loaded load=0. No module command was issued on the router.

The same source's get_module_refcount returns -1 for fopen failure, and uses
atoi with an initial zero for empty/malformed input. is_module_loaded returns
false when opendir fails. These are legacy convenience interfaces, not a strict
absent-versus-unreadable observation contract. Do not infer safe unload from
these ambiguous errors or change shared return semantics globally for IoT.

Local stop_wifi_all_rt is void and ignores individual wif_control results;
start_wifi_ap_rt regenerates administrative main/guest behavior from current
mode/schedule, updates mlme state and bridge membership. They are not complete
snapshots/verified restoration callbacks. A selective reload needs strict
module/interface post-observation, preserved 5 GHz identity/state and owned
main/guest/authentication restoration before it can serve RADIO_PREPARE. Path
selection remains open; no generic reload shortcut was added.

## Follow-up 2026-10-22: historical device snapshot matches MAC-transition condition

Read the existing private 2026-10-20 network snapshot referenced by the detailed
device audit. Its SHA256 `03d0e4f1565f2890125bae5ccc481f1ff8c305ebebbf857e5e5c5c2c1fc603ab`
matches the audit JSON manifest; file size is 20789 bytes. No new router access
was performed and raw MAC/WAN/client addresses were not copied into Git output.

Derived only the following booleans from recorded ra0/ra1 addresses:

- Main address byte index3 bit5 was set.
- The Mode4/two-BSS source prediction equals the recorded guest address.
- For that historical main address, the same source's three-BSS prediction
  differs from its two-BSS guest prediction.

This makes the migration concern applicable to the recorded device values,
conditional on the same runtime mode/address mapping. It does not directly
read the chip capability register, prove absence of runtime overrides or
establish current addresses on 2026-10-22. The traced local AP source and fetched
common/init excerpts did not provide a runtime-mode observation. Keep creation
path selection open; do not activate a count/mask change or claim preserved
guest MAC from the generic capacity check. No private snapshot was modified.

## Follow-up 2026-10-22: BSS-count transition can alter guest MAC

Pinned source retrieved through GitHub connector:

- [ap/ap.c](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/ap/ap.c),
  blob `e452c6f55b4dedb2703f4471f9fd2d2c7cb226ac`, matches local git hash-object.
- [chips/mt7603.c](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/chips/mt7603.c),
  blob `ebc08c509250052d90fd92065c1bdcc48ac6e0bc`, defaults MBSSID_MODE4/HIF_MT.
- [include/rtmp_chip.h](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/include/rtmp_chip.h),
  blob `a0aa6d892cf0c39554b4fcc26e7ff68e3e57442c`, defines Mode4 as 4.

The actual set_wdev_if_addr MT_MAC branch uses MacMask=0xef at two BSSes and
0xcf at three/four, independent of the APCLI-count calculation in the older
RLT/RTMP branch. Mode4 selects address byte index 3. For secondary index 1,
the transition clears bit5 previously preserved by the two-BSS mask; main
index0 remains the copied factory address in this function.

Extracted actual function compiled/executed under strict MinGW with register
operations injected. Exhaustive byte0..255 diagnostic confirmed unchanged main
in all cases and changed guest in 128 cases (factory selected byte bit5 set).
This is not a runtime measurement of this router or proof that capability
defaults cannot be overridden elsewhere. It refutes a general address-neutral
BssidNum change. Verify actual mode/addresses, hardware mapping and related
APCLI/WDS before lifecycle selection; no mask patch or reserved-BSS activation
was applied. Record preservation or explicit migration before device acceptance.

## Follow-up 2026-10-22: owned-profile preflight before normal-OFF changes

Normal-OFF begin now validates the captured current profile before closing
gates or regenerating services. Shared profile-scan logic checks the complete
required-key set/uniqueness, exact owned third credentials and list values from
either streams or bounded captured bytes. Buffer preflight uses no file writes.
The current file identity must still match its captured generation.

Failure cancels private read-only settings/profile captures. Added a settings
mutation marker: cancellation is prohibited once any setter was attempted,
even if it returned failure before a completion stage was recorded. No profile
or service mutation is silently discarded as a read-only cancellation.

Six strict MinGW fixture groups passed (list, line, stream, actual radio-state
header, actual context source and actual settings/service adapter). Covered
buffer/stream agreement, embedded NUL, duplicate/foreign credential rejection,
preflight cancellation and existing partial-write/recovery cases. Filesystem,
NVRAM, service and bridge observations remain injected where specified; Windows
declaration/Winsock adapters were used only for settings fixture. New scanner
is staged and header identity checked. Real target/RF/full dispatch acceptance
is still open; no router or firmware changes occurred.

## Follow-up 2026-10-22: composed normal-OFF context

Added disable-controller context composing the real service/settings and
current-profile APIs. It captures the profile before settings; a failed settings
capture cancels only private read-only profile memory, with no external writes.
Service apply runs while bridge remains; profile apply requires committed normal
DNS, absent bridge and DOWN BSS, then removes the exact captured IoT entries.
Final release remembers profile commit if settings cleanup fails, so retry
does not restore or recommit an already released profile baseline.

Actual composition source and radio-state header compiled/executed under strict
MinGW with injected adapters/file operations. Passed capture cancellation,
service/profile failures, phase preconditions, no duplicate operation and partial
final release retry. Initial test indentation warnings were corrected before
successful execution. RC stages both adapter objects/headers; identity checker
and ABI target/sanitizer gates were extended, not run. No RF/driver execution
is implemented here: outer activation must bind quiescence, quarantine, bridge
steps and final live main/guest/service observation. Device untouched.

## Follow-up 2026-10-22: retained normal-OFF profile transaction

Added remove_owned/commit_removed to radio-profile-state using a freshly
captured CURRENT file. Removal journals its intent/result through the existing
bundle and calls the exact owned-third-entry file API. Once removal starts,
the old startup generation/restore path is prohibited. A zero/uncommitted API
result permits retry only when pre-attempt file identity still matches;
uncertain result capture leaves the journal/snapshot retained without replay.
Confirmed removal checks its generated identity on repeat rather than rewriting.
Commit releases that current baseline only after the outer controller has
observed radio/profile/service success. The file receipt itself is not RF proof.

Actual header code compiled/executed under strict MinGW with injected file
journal/removal operations. Checks passed safe retry, no duplicate successful
removal, changed-generation refusal, guard loss, incomplete result capture and
prohibition on restoring old IoT fields. Real filesystem/profile tests remain
pending Linux execution. ABI sanitizer/MIPS and staged RC header probes were
extended, not run. Real radio/controller binding remains open; no device change.

## Follow-up 2026-10-22: profile file removal API

Added public wr_iot_profile_remove through the existing profile replacement
implementation. It uses reverse-stream validation into a private temporary
file, flush/fsync/close and original identity check before rename, preserving
the current first two entries and unrelated fields. Input open now includes
O_NONBLOCK before requiring a regular file, so FIFO input cannot stall the
controller before validation. No global generator, SKU or NVRAM calls added.

Extended Linux file fixture for wrong ownership credentials, temporary creation,
sync, close and rename failures during removal, successful add/remove roundtrip
and FIFO rejection. Those filesystem cases were not executed on Windows.
Strict MinGW line/stream execution passed; profile.c syntax passed with explicit
POSIX function declarations/flag adapters, which do not establish real Linux
file behavior. Existing ABI gates cover file runtime and target compilation when
next run. The candidate manifest records API installation; controller/radio
application and power-loss durability remain unproven. No router state changed.

## Follow-up 2026-10-22: remove owned third BSS without global generator effects

Local base ralink.c generator unlinks/recreates SingleSKU.dat via
symlink_sku_file, may set key_type NVRAM, loads custom AP.dat and closes its
output. The DAT-only radio-profile snapshot does not cover those side effects.
Do not assume calling the whole generator is a profile-only operation.

Added a reverse stream transform sharing the existing known-key table. It
requires BssidNum=3, exact owned third SSID/PSK and known third list values,
then produces BssidNum=2, blank third credentials and the current first two
list values. Unknown/shared fields remain unchanged. Entire profile structure
and required-key uniqueness are checked before output, as for addition.

Strict MinGW list/line/stream compile/execution passed exact add/remove
roundtrip, main SSID changed after addition preserved on removal, credential
ownership rejection, malformed/extra list values and small-buffer rejection.
No SKU/NVRAM generator calls occur in this stream transformation. It is not yet
an installed atomic file/removal API or driver action. Current effective DAT
must still be reconciled with current NVRAM by the real backend; changing the
driver's parsed BSS count/MAC allocation and RF behavior need target/device
evidence. No production source activation or router mutation occurred.

## Follow-up 2026-10-22: verify assembled candidate RC source

Ran complete prepare-rc.py against an isolated fresh copy of local base RC
sources and board l1profile. Preparation succeeded. Verified actual installed
adapter content/header mapping and manifest candidate flags. Compiled the
installed disable-services object under strict MinGW C11. Actual GNU Make
selected its object only for WR1200JS, excluding other/no-board modes.

Extended prepare-activation-header-check.py to compare installed adapter/header
identity, object count and manifest scope before producing the combined RC
probe. Probe generation passed. A deliberate mutation in the temporary installed
adapter was refused before replacing an existing probe; source was restored.
Added target compile of the installed object to ABI; not run here. These are
source/host checks, not full RC link, target/device execution or real radio
binding. Original base/worktree inputs were preserved; temporary fixture removed.

## Follow-up 2026-10-22: composed service/settings normal-OFF adapter

Added disable-services API composing existing settings and DNS mechanisms.
Begin captures current owned temporary settings; apply closes gates while
bridge remains, prepares normal DNS/DHCP and commits it. Failed preparation or
commit retains settings and guard for retry. Once commit returns success its
synchronous receipt prevents another generation/commit on repeated apply.
That receipt is not a live status verdict; final controller OBSERVE is required.
Finish is refused before service commit or bridge removal, clears remaining
temporary credentials/ranges and releases its settings snapshot. The caller
must still hold its separate outer guard through final observation.

Strict MinGW execution linked actual request-stage, request-snapshot and new
adapter. DNS, NVRAM and bridge callbacks were injected. Tests passed preparation
failure, commit failure, retry, no duplicate committed operation, premature
finish refusal and final clearing, alongside previous ownership/failure cases.
Candidate RC stages the header/source/object and records controller_bound=false;
ABI host link and MIPS compile commands include it, not executed here. Real
radio/profile preservation, full activation binding and device acceptance are
still open. No router commands or firmware builds occurred.

## Follow-up 2026-10-22: normal-OFF owned temporary settings adapter

Extended the existing request-snapshot adapter rather than adding a second
configuration save mechanism. Normal-OFF take captures current bounded nine
temporary values and an owned existing bridge index under the service guard.
Gate closure requires that same owned bridge and administrative BSS DOWN.
Only fixed three gates are closed before DNS disable. Credentials/ranges are
forgotten only after bridge removal; ordinary restore and suspend are refused
in this mode so no historical IoT gate can be reopened by rollback.

Each clear validates all current values against its expected owned state.
After a setter error it accepts only the intended result or the previously
expected value, never arbitrary replacement values. Partial failures retain
snapshot/guard for retry. Finish requires complete clearing, no bridge, DOWN
BSS and matching expected values, then clears retained memory. Real radio
quiescence/quarantine remains the outer controller's responsibility.

Strict MinGW actual request-stage/request-snapshot fixture execution passed
all three gate-setter failures, all six credential/range failures, independent
foreign changes to all nine fields, changed bridge index, foreign bridge and
UP-BSS refusal plus prior startup snapshot cases. NVRAM/bridge callbacks were
injected and POSIX declarations/Winsock adapter supplied; no Linux/target/device
acceptance follows. Source preparation maps the bridge header and records this
candidate API. Real activation callback binding remains open.

## Follow-up 2026-10-22: preserve bridge for DNS disable recovery

Corrected the previous normal-OFF ordering: a current DNS configuration can
refer to br-iot, so removing that interface before preparing replacement
services can make service rollback fail. New DISABLE_SERVICES runs after
quiescence/quarantine and before bridge-down/detach/removal. It must commit
current normal services with the three gates closed before bridge teardown.
DISABLE_APPLY afterward handles remaining owned profile/settings teardown.

DNS-disable readiness now accepts an absent or owned bridge and requires
administratively DOWN/absent BSS. Added a read-only bss_is_down observer which
rejects foreign masters and unowned br-iot attachment. This does not establish
RF quiescence or clear driver beacon intent; the real QUIESCE callback retains
that responsibility. Preparation maps the bridge API header into RC includes.

Strict MinGW activation/DNS-flow fixtures passed revised ordering, failure
retaining the bridge, foreign bridge and UP-BSS refusal. Linux bridge observer
cases were added but not executed. Real callbacks still must implement owned
gate clearing while bridge exists; the older startup staging helper refuses
an existing bridge and must not be reused blindly for this step. Production
remains excluded; no router state changed.

## Follow-up 2026-10-22: prepared normal-OFF DNS retry is read-only

Factored final activation readiness from commit. Repeated disable_prepare on
its own prepared transaction now invokes that observer instead of returning
permanent EBUSY or replacing snapshots. It checks current guard, exact gates,
marker absence, writer-journal status, lock identity, generated-file identity,
effective service settings and protocol readiness. Normal OFF cannot adopt a
prepared startup transaction. Commit remains the step releasing saved state.

prepare-dns-disable-check.py extracts actual readiness, commit and disable
functions. Strict MinGW execution passed repeated preparation without another
generation, seven independent failed observations, retained prepared state,
retry after observations recover, transaction failure and startup refusal.
An initial helper-name collision in the fixture was corrected before the
successful run. Service/filesystem reads are injected, so this is control-flow
evidence. Linux service tests were extended and ABI sanitizer/MIPS core checks
added; neither executed here. Real callback/radio integration is still pending.

## Follow-up 2026-10-22: fresh DNS disable service transaction

Added normal-OFF DNS prepare/commit entrypoints to the candidate RC controller.
Prepare requires the outer guard, exact zero profile/network/firewall gates and
absent br-iot, then uses the existing retained service transaction to capture
CURRENT files/leases and regenerate normal DNS/DHCP. It does not replay startup
files or change radio/bridge state. Commit checks those preconditions again,
normal daemon readiness and absence of owned br-iot/wr-iot markers throughout
the bounded effective include graph. Invalid/missing/unreadable includes or
conf-script prevent an absence claim. Detection is conservative: unrelated
literal marker text can also block it; arbitrary custom networking rules and
daemon runtime absence are not proven by this marker test alone.

Failed post-generation validation leaves prepared service state for explicit
retry/abort, keeping the outer controller responsible for quarantine and BSS
closure. Abort recovers this NEW current baseline; it must never reopen IoT.
Normal disable still needs real radio/controller callback binding and service
acceptance. Manifest records API installation without changing production-ready
or rollback-complete flags.

Strict MinGW compile/execution passed extracted actual preflight and quote/
comment/marker helpers, including nonzero/empty/malformed gate refusal and
existing-bridge refusal. Linux include-graph tests and actual injected-daemon
transaction fixture were extended for normal disable and failed commit retry,
but were not run here. No firmware build or router mutation occurred.

## Follow-up 2026-10-22: distinct normal-OFF state machine implemented

Activation sequencing now distinguishes startup rollback from post-ACTIVE
disable. Normal stop locks and requests a fresh read-only DISABLE_SNAPSHOT;
failure leaves ACTIVE unchanged. After quiescence and quarantine it tears down
the owned bridge, invokes DISABLE_APPLY against current desired configuration,
DISABLE_OBSERVE, removes quarantine and DISABLE_COMMIT. Normal OFF never invokes
the old startup RESTORE operation. Partial stop retains a disabling marker,
snapshot/lock and next step; retry rechecks quiescence and resumes teardown.
Callbacks must be idempotent and must not reopen IoT during failed OFF.

Strict MinGW C11 compile/execution passed each normal-stop stage with failure
before and after modeled mutation, lock/snapshot refusal, retained recovery,
preservation of a main configuration changed after activation, and previous
startup rollback tests. No actual DNS/radio callbacks are implemented by this
model. Linux sanitizer/MIPS gates already compile the model when next run;
they were not run here. This closes the sequencing conflation, not the real
post-commit service transaction implementation or device acceptance.

## Follow-up 2026-10-22: normal OFF is a separate service transaction

Traced restart-controller.inc activation_commit -> restart_finish ->
service_state_finish -> service_transaction_finish. Successful commit releases
saved service files, lease backup, transaction lock and nested service guard,
and clears restart_active/prepared. The existing abort requires restart_active;
it therefore cannot serve normal OFF after commit. This is valid startup
transaction behavior, not a reason to keep that guard held forever.

The unbound radio backend must implement normal post-commit disable with a new
guarded transaction over current service/main/guest settings. Startup failure
may roll back its retained baseline; normal OFF must remove owned IoT state
without replaying an obsolete global DNS/lease/configuration snapshot over
legitimate later changes. It must have its own failure/recovery proof. The
activation model's generic RESTORE callback is not evidence that this path
exists. Clarified API/contract; no runtime behavior changed or test executed
for this source-only audit. No device operations occurred.

## Follow-up 2026-10-22: snapshot resume checks retained expected values

The temporary NVRAM snapshot previously reacquired its guard after ACTIVE
without checking whether another writer had replaced the staged values. Added
bounded expected-value capture during suspend and comparison of all nine
fields after reacquisition. A mismatch refuses resume without writes or losing
the baseline. A failed bounded capture does not release the held guard.

Strict MinGW compile/execution of actual request-stage/request-snapshot and
their fixture passed all nine independent foreign-change cases, overlong
capture, and existing restoration/readback/guard failures. Host adapters only
supplied net/if declarations and Winsock inet includes/linkage. Temporary test
files were removed. Linux locks, target execution and production integration
remain unverified. Equality is current-value evidence, not a generation counter;
an intervening change-and-revert remains undetected and requires full writer
coordination. No device configuration was changed.

## Follow-up 2026-10-22: carry transaction identity into activation

The old strong activation interface received settings only, so it could not
bind its retained expected-state/recovery snapshot to the request ID later
used by status. The interface and dispatch now pass the complete claimed
wr_iot_control_request envelope (ID, creation time, settings). The backend
must copy needed private state before return and must not retain credentials
merely to answer status queries. No real backend was substituted.

prepare-dispatch-check.py extracts the actual dispatch function. Strict MinGW
C11 compile/execution passed envelope propagation, backend invocation without
the mailbox lock, recovery for nonterminal backend outcomes, first/second open
failure, missing clock, no replay of running or terminal outcomes, and terminal
cleanup. IPC and activation were injected; Linux real mailbox tests remain
pending. ABI sanitizer and MIPS fixture compilation were added, not executed.
This repairs the interface needed for a real observer; it does not implement
activation, persistent snapshot ownership or radio restoration.

## Follow-up: close wrapper and main-reference preservation checked

Extended the isolated candidate fixture to extract the original
MBSS_VirtualIF_Close as well as the repaired open wrapper. Strict MinGW
compile/execution passed base/MT/HNAT cases. Paired open/close balances wrapper
and virtual references, calls secondary-close controls and retains an existing
main-interface reference without invoking modeled hardware close. The ABI
workflow now also compiles these extracted fixtures with its target MIPS
compiler; that compilation has not run here. This checks actual wrapper flow
with injected driver operations, not full driver headers, hardware resource
lifetime, beacon reset or runtime RF isolation. Production remains unchanged.

## Follow-up: isolated module-reference correction executed

`prepare-mbss-open-check.py` creates a separate source candidate that balances
the wrapper's module reference when VIRTUAL_IF_UP fails. It deliberately does
not decrement the virtual count again, invoke unsafe beacon cleanup or change
the successful ordering. Input source and existing output files are preserved.
It is not invoked by production preparation and does not resolve beacon intent.

Actual extracted repaired wrapper compiled with strict MinGW C11 warnings and
ran successfully in base, MT_MAC and MT_MAC+HNAT variants. Injected operations
confirmed failure leaves module/virtual references balanced and no queue/CR/
HNAT registration, while success retains both references and normal controls.
ABI now includes Linux sanitizer versions of the same fixture; not executed
here. These are wrapper-control-flow checks, not real driver/module lifetime,
target compilation or on-device behavior. Production source remains unchanged.

## Follow-up: failed secondary-open path must be covered by radio recovery

The pinned secondary wrapper `MBSS_VirtualIF_Open` in `ap/ap_mbss_inf.c`
increments the module use count, invokes MBSS_OPEN (which can set beacon
intent), and only then invokes VIRTUAL_IF_UP. If VIRTUAL_IF_UP fails, the
wrapper immediately returns -1 without the normal MBSS_CLOSE or module-count
decrement. Therefore an ioctl failure and a DOWN netdevice alone cannot prove
that the preceding driver-side actions were undone.

Pinned
[common/cmm_cfg.c](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/common/cmm_cfg.c),
blob `cb3e9607326e473436862132b18de9679cc6c154`, was fetched via the connector.
Its VIRTUAL_INF_UP branch increments the virtual-interface count before the
first hardware open and rolls that count back on open failure. VIRTUAL_INF_DOWN
decrements it unconditionally. Do not blindly call VIRTUAL_IF_DOWN as failure
cleanup: that can double-decrement the already-restored counter. Normal
MBSS_CLOSE also calls beacon/station routines whose resource validity after a
failed hardware open must be established before reusing them as cleanup.

Normal APShutdown calls MlmeRadioOff and, under RTMP_MAC_PCI, APStop. APStop
calls MacTableReset and disables synchronization; this does not establish that
every failed-open path reaches those operations or clears beacon intent.
The real radio backend must handle this partial-open case explicitly and
retain quarantine/recovery when driver state cannot be confirmed. A driver
repair needs target/source failure-injection evidence for both counters,
beacon state and resource lifetime before integration. No speculative cleanup
or module reload was added to the production driver.

## Follow-up: beacon initialization does not reset transmission intent

Fetched pinned upstream
[tx_rx/wdev.c](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/tx_rx/wdev.c),
blob `c3967f59f470bdaf3afdab8f3eec8fefba12aea7`, via GitHub connector.
`wdev_bcn_buf_init()` at line 108 has its `bBcnSntReq = FALSE` assignment
commented out. It initializes the buffer index, capability offset and MT beacon
state, but does not clear the beacon transmission-request flag. Do not treat
this routine as a reset of prior BSS transmission intent. Fresh zeroed adapter
allocation and reusing an existing adapter are different lifecycle cases.

The local `ap_assoc.c` common association handler looks up an existing station
entry and selects its stored BSS; its initial checks do not reproduce the
explicit netdevice-RUNNING checks seen in initial authentication/probe handling.
`ApAllowToSendPacket` also permits group traffic without that explicit check.
These local function observations are not proof of an exploitable receive path:
earlier dispatch, station deletion, Linux interface state and hardware filters
must be traced. They do show why probe/auth checks alone cannot establish full
isolation or safe reserved-BSS reuse.

Next prove complete close/open state reset and packet dispatch for the exact
board before choosing reserved BSS or fresh-adapter lifecycle. Any reserved
startup implementation must explicitly guarantee silent/down/unattached ra2
before exposing its generated credentials and must preserve main/guest state.
No driver edit, module operation or device command occurred. Source lookup
404s for guessed common beacon filenames were not interpreted as absent
functionality; the verified implementation was located through the driver's
`os/linux/Makefile.6` object list (`tx_rx/wdev.o`).

## Follow-up: inactive preallocated third BSS source investigation

Local driver-reference inspection provides a concrete alternative to live
module replacement, but not enough evidence to select it for production:

- `mt76x3/ap/ap_mbss.c:67` creates secondary netdevices up to parsed BssidNum
  during the one-time MBSS initialization. `MBSS_Open` sets that BSS's beacon
  request flag; `MBSS_Close` clears it and kicks associated stations.
- `mt76x3/ap/ap_connect.c:42`, `BeaconTransmitRequired`, requires the beacon
  request flag for a secondary BSS. Main-BSS WDS exceptions are separate.
- `mt76x3/ap/ap_sync.c:91` skips probe replies when the BSS netdevice is absent
  or not RUNNING. `mt76x3/ap/ap_auth.c:652` rejects initial authentication under
  the same condition; the later authentication path also checks DOWN at 1119.
- Board kernel template enables MT7603E MBSS and disables AIRPLAY. APStartUp's
  AIRPLAY-only flag writes therefore do not by themselves demonstrate a board
  startup opening the third beacon. Effective target preprocessing still needs
  checking; a template is not the final build configuration.

This makes creating a reserved DOWN ra2 on initial driver startup worth further
investigation. It is not permission to change BssidNum globally or expose an
unconfigured/open third SSID. Missing evidence includes beacon-buffer initial
state, all beacon/receive/data paths across repeated main-radio opens, parser
defaults for the reserved third security entry, MAC-address allocation effects
on main/guest/APCLI/WDS, exact target guards and RF/device acceptance. Association
and data-path behavior cannot be inferred solely from probe/auth checks.
The currently running router has no ra2 in the supplied interface snapshot;
this path also does not solve activation on that already initialized adapter
without a separately approved lifecycle transition. No driver/profile changes
or device operations were made during this investigation.

## Follow-up: actual status-core host check executed

`prepare-status-check.py` extracts the actual status function from control-client
and supplies injected mailbox/observer reads. Compiled using MinGW GCC with
`-std=c11 -Wall -Wextra -Werror -O2` and executed successfully on Windows.
Covered exact-success gating, error/noncanonical observation values, changes
to ID/state/created/observed during observation, first/second open/read failures,
all non-applied states, invalid inputs and observer invocation without queue
lock. ABI now includes this fixture with Linux sanitizers; that run is pending.
This evidence covers the actual status function, not real filesystem locks,
live resource observations or firmware/device behavior.

## Follow-up: transaction replacement during observation

The status observer intentionally runs without the mailbox lock. The client
now reacquires that lock and rereads the result after successful observation;
ID, state and both timestamps must still match. A new queued transaction or
an updated result therefore invalidates the old response. The channel fixture
submits a replacement request inside the fake observer and asserts old-result
refusal and new queued-ID visibility without replay. Linux fixture execution
is pending; whitespace checks passed. This only addresses mailbox replacement;
the real observer must still serialize with live writers and queries describe
a point in time, not a promise that future radio state cannot change.

## Follow-up: prevent historical APPLIED from standing in for live observation

The candidate control client now calls the strong
`wr_iot_activation_result_observed(result)` interface before returning APPLIED.
Only exact 1 is accepted; missing/error/changed state must produce unknown at
the HTTP layer. Queue/running/recovery/rejected records retain their existing
meaning. The mailbox lock is released before observation to preserve lock
ordering with the service controller. This does not mutate or replay a request.

The observer must bind the transaction ID to a retained expected-state snapshot
and generation, serialize against radio/network writers and verify enabled or
disabled outcomes as appropriate. It is not implemented yet. A production link
must fail rather than silently substitute a success default. This closes the
transport's unconditional historical-success path, not the missing full runtime
observer/legacy-writer integration. The Linux channel fixture now covers
observer failure, negative/noncanonical return values, no backend replay and
mailbox lock availability during observation. It was not executed on this
Windows host. Whitespace checks passed; no build or device mutation occurred.

## Follow-up: legacy restart and watchdog are separate radio writers

Read-only inspection of the local base reference found the following concrete
call sequence in `trunk/user/rc/net_wifi.c:764`, `restart_wifi_rt()`:
stop 802.1X, stop all 2.4 GHz interfaces, optionally regenerate the profile and
set temporary `reload_svc_rt=1`, start AP/WDS/AP-client, start 802.1X, rebuild
guest isolation, check AP-client WAN, update radio controls, and restart iappd.
No module unload/load occurs in this function. The DBDC conditional can also
affect the other band and must be evaluated for the exact board configuration.
This is a base-source observation, not proof of the running image's exact code.

In `trunk/user/rc/watchdog.c:341`, `reload_svc_rt` resets cached RADIO2/GUEST2
schedule state. Watchdog then queues `control_wifi_radio_rt_on/off` and
`control_wifi_guest_rt_on/off` according to its current schedule evaluation.
Therefore the flag means schedule resynchronization, not module replacement.
Single-threaded RC dispatch alone cannot prevent a separate watchdog process
from queuing events while the candidate activation callback is running.

The current `tools/iot/prepare-rc.py` guards stop/restart with owned IoT
quiescence, but does not bind those legacy events to the candidate activation
state/snapshot. A later legacy restart can close IoT temporary gates without
updating an earlier ACTIVE result. Do not expose a durable active verdict until
legacy writers either enter the same controller/recovery protocol or invalidate
and re-observe the result before it is reported. Do not silently discard user
or scheduled radio-off events to maintain an IoT ACTIVE label.

Required integration evidence: schedule/manual restart while ACTIVE, queued
events during STARTING and RECOVERY, radio-off with IoT enabled, main/guest
restoration and stable 5 GHz, and a status query after each transition. These
cases are acceptance requirements, not executed tests. The real activation
backend remains absent; production exclusion remains in force.

## Follow-up: explicit radio creation stage and one-time driver MBSS init

The candidate activation state machine now has an explicit
`WR_IOT_RADIO_PREPARE` operation after bridge preparation and quarantine, before
attachment/DHCP. PROFILE must not reopen the radio; RADIO_PREPARE may create/
reload the candidate BSS only with quarantine already installed and returns
success only after observing ra2 DOWN. The backend must preserve and restore
the previous main/guest radio state. Recovery QUIESCE targets IoT and must not
re-stop an already restored main/guest radio on a later recovery retry.

The strict MinGW sequencing fixture compiled and ran successfully. It now
requires explicit handling of every operation, tests refusal before each
startup mutation, tests partial failure after each mutation, and models ra2
opening during a failed radio reload. Quarantine and the rollback snapshot/
lock remain retained when restoration fails; an explicit retry completes
modeled recovery. These are injected-backend checks, not radio execution.

The 2.4 GHz build selects MT7603E/mt76x3. The GitHub connector verified that
the local driver-reference files match pinned upstream blobs:

- [ap_mbss.c](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/ap/ap_mbss.c),
  blob `92d3b01b7be6dd7bcdfe2bc8fbc74b6838ac3b9f`.
- [ap_mbss_inf.c](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/ap/ap_mbss_inf.c),
  blob `7c736a04eeeddace0bbb0c5c96198d0738f400a2`.

`MBSS_Init()` returns immediately when `FlgMbssInit` is already true, derives
its creation loop from the parsed BssidNum, and sets the flag after creation.
`MBSS_Remove()` detaches/frees secondary interfaces but does not reset that
flag in this source. The interface wrapper also documents that changing the
profile count with a down/up is insufficient for this creation path. Therefore
ordinary `restart_wifi_rt()` must not be assumed to grow an already initialized
two-BSS adapter into three BSSes. This is a source constraint, not an observed
test of the running router or every possible driver lifecycle path.

Next trace fresh-adapter/module lifecycle and ownership or prove a safely
reserved inactive third BSS before choosing the production creation method.
Do not add an unverified down/up fallback, unload a live module, or claim that
profile generation created ra2. Actual radio/authenticator rollback, NAT and
offload observation, persistence, target link/image and device acceptance are
still open. The strong activation backend remains unimplemented and IoT stays
excluded from production. No router state was changed.

## Follow-up: final active-filter observation

Source tracing found that the existing `wr_iot_active_filter_ready()` calls
`wr_iot_policy_rules_ready()`, whose `eligible(0)` rejects an UP ra2. It is a
pre-mutation readiness check, so using it for final OBSERVE after BSS_UP would
reject a successful administrative startup. Its strict mutation conditions
remain unchanged.

Added a separate read-only path:

- `wr_iot_bss_is_active()` requires an owned UP br-iot, UP ra2 attached to it,
  and exactly ra2 as its sole member. Directory read/close errors refuse the
  observation. The existing BSS-UP mutation now shares the stricter membership
  reader, including error handling.
- `wr_iot_policy_rules_observed()` requires the held service guard and an active
  administrative BSS both before and after reading both installed filter
  families. Failed/missing observations return false.
- `wr_iot_active_filter_observed_current()` rebuilds the expected current policy,
  requires exact enabled gates and service readiness, and refuses WAN selection
  changes across observation. It does not rebuild firewall rules or change
  service gates.

The extracted actual core observer compiled strictly with MinGW and executed
successfully with injected reads. Cases cover missing guard, failed duplicate
close, inactive BSS, each failed filter family, activity loss during readback and
missing expected rules. Python syntax and whitespace checks passed.

Existing Linux bridge/netfilter namespace fixtures now include active-BSS
observation, foreign-member/down-BSS refusal, retained mutation refusal and
changed installed-policy refusal. The installed firewall-source fixture also
covers this new read-only path, service failure and WAN changes. Linux/kernel,
MIPS and target/device execution of these changes remain pending; local tests
do not establish actual radio activity, RF/client connectivity, NAT readback or
hardware offload isolation. The production activation backend is still absent.

The new project skill was read. Existing owner-approved scope and repository
rules remain authoritative where its suggested defaults differ. This step
changes no radio feature defaults and performs no device operation.

## Scope of this inspection

Read-only source inspection of `tools/iot/activation.h`,
`tools/iot/request-stage.c`, `tools/iot/quarantine-apply.inc`,
`tools/iot/prepare-rc.py`, and the WR1200JS production workflow. No source,
router setting, firmware image, or running service was changed. No test or
firmware build was run in this checkpoint.

## Confirmed state

- `activation.h` defines an ordered state machine, but explicitly says no
  production backend is installed. A search of the IoT candidate code and CI
  workflow call sites found
  `wr_iot_activation_start()` / `stop()` only in the injected-backend fixture
  `tools/iot/check-activation.c`; there is no production caller.
- `wr_iot_request_stage()` validates and stages NVRAM values, but its call
  sites are limited to the function itself and host fixtures. No authenticated
  WebUI/CGI Apply handler invokes it.
- The prepared radio profile hook checks the temporary
  `wr_iot_profile_t` gate; the request stage can set that gate, but no
  production activation path currently owns the full sequence that creates,
  observes, and recovers the third BSS.
- `quarantine-apply.inc` contains guarded apply/readback functions, but the
  activation controller is still pending. `prepare-rc.py` reports
  `activation_integrated: false` and `dnsmasq_service_rollback_complete: false`.
- The production firmware workflow currently asserts that
  `trunk/user/rc/wr-iot-profile.c` and `trunk/user/rc/wr-iot/` are absent.
  Thus its successful firmware build intentionally cannot include this IoT
  candidate.

## Consequence

The existing MIPS object and injected-backend fixture results are preparation
evidence only. They do not establish a usable IoT page, authenticated Apply,
third-BSS lifecycle, safe recovery, firmware inclusion, or router acceptance.
The interim Classic IoT destination must remain unavailable and must not show
a working/enabled state.

## Next implementation dependency

Before enabling or shipping IoT, implement and test one production-owned path
that binds authenticated request validation to the serialized activation
controller and its retained snapshots; it must coordinate radio-profile
restore, owned bridge/BSS operations, DHCP/DNS readiness, firewall quarantine
and final policy, then expose observed status. Complete rollback of the shared
dnsmasq and other writers is still required. Only after that source-level path
is complete should the main image exclusion be replaced by board-scoped build,
ROMFS, and runtime gates. Keep the feature OFF and excluded until those gates
pass.
# Host activation recovery fixture follow-up — 2026-10-21

The candidate `tools/iot/check-activation.c` fixture now injects failures
*after* each startup operation's modeled mutation, including profile,
bridge, isolation, DHCP, policy and BSS-up. Each case requires the recovery
state machine to finish inactive, release its lock and snapshot, and clear
all modeled owned resources. MinGW GCC compiled the fixture with
`-std=gnu11 -Wall -Wextra -Werror -O2`; the executable returned exit 0 with
`PASS IoT activation sequencing and retained recovery`. The local executable
was removed after the run. This is a backend simulation only: it does not
bind production RC callbacks or prove actual file, daemon, driver or router
rollback. Production IoT remains excluded.

# Beacon restart/close lock audit — 2026-10-22

Read-only inspection of pinned driver revision
`c25283e915a2a00a763774dd255b14aff997285e` narrowed the remaining
race. `ap/ap_mbss_inf.c:185-191` invokes CR disable before `MBSS_Close` and
discards both ioctl results. `ap/ap_mbss.c:327-329` clears the selected
`ARB_BCNQCR0` bit; only later, at `:432`, does `MBSS_Close` clear
`bBcnSntReq`. The recovery handler in `hw_ctrl/cmm_asic_mt.c:1390-1394`
reads, sets, and writes that same bit, then marks the BSS IDLE. Neither path
holds `BcnRingLock` around these operations. A preexisting beacon update can
therefore reach recovery while close is in progress.

The ring lock is real but covers more than the two register operations:
`common/cmm_data_pci.c:2681-2760` holds it in DMA completion;
`common/cmm_mac_pci.c:2710-2713` holds it while kicking out a beacon and
changing its software state; `:2069-2095` holds it for PDMA-reset state
updates, then releases it before ring cleanup. The pre-TBTT interrupt calls
`APUpdateAllBeaconFrame` (`cmm_data_pci.c:1484-1492`), whose path reaches
recovery (`ap/ap_connect.c:1885-1888, 622-631`) and can later reach beacon
kickout. Holding `BcnRingLock` across recovery or the whole close path would
nest with the existing kickout lock and would also cover two bounded flush
polls. That is not a sound lock placement.

Further `ARB_BCNQCR0` writers exist in
`hw_ctrl/cmm_asic_mt.c:1490-1493,1556-1559` for BSS synchronization and
`ap/ap_mbss.c:282-285` for secondary enable. A pairwise lock only around
recovery and disable would not serialize those writers. `MBSS_Open` sets
`bBcnSntReq` before CR enable (`ap_mbss.c:369-375`,
`ap_mbss_inf.c:143-149`), so the opening transition needs the same state
protocol. In the effective multi-core variant, `RTMP_IRQ_LOCK` uses irqsave
but existing ring completion/kickout use `RTMP_SEM_LOCK` (BH spin lock);
mixing these without proving interrupt context and nesting is not yet safe.

Next source change must establish one adapter/BSS transition protocol for
open, close, successful recovery and reset, then cover every writer above and
the final beacon kickout decision. It should keep long flush polls outside
the critical section and require a fresh active-BSS/access check at the
restart point. The current candidate only rejects observed timeouts/device
loss; it does **not** prove close exclusion, selective drain, or radio silence.
No candidate, production image, or device state was changed in this audit.


## Main-radio readiness gate — 2026-10-22

Pinned-source review found that `rt28xx_open` initializes the adapter and
initializes MBSS, while `MBSS_VirtualIF_Open` requests `MBSS_OPEN` before
`VIRTUAL_IF_UP`. The first `VIRTUAL_IF_UP` may therefore enter the physical
radio-open path; the additional-interface path does not provide the same proof
that the primary radio has just become ready. This justifies an explicit
readiness stage before opening the candidate IoT BSS.

The unbound activation candidate now calls `WR_IOT_MAIN_RADIO_READY` directly
before `WR_IOT_BSS_UP`. The production callback contract is to verify the primary
2.4 GHz interface is operational on the expected adapter and the IoT BSS remains
DOWN after radio preparation. The strict MinGW fixture passed with injected
callbacks, including the negative case: missing main-radio readiness prevents
`BSS_UP`, then startup rollback returns the fixture to inactive and removes its
modeled resources.

This check alone is not atomic with the next operation. Until one adapter/BSS
transition owner serializes first/additional open, close and reset, production
`BSS_UP` must revalidate primary-radio readiness while holding that ownership
protocol. The fixture does not bind vendor callbacks or prove that runtime
observation, MBSS open, driver compilation, final image inclusion, or RF/client
operation works. No production handler, image or router state changed.

## Close/command-thread dependency audit — Sol, 2026-10-22

Read pinned source `c25283e915a2a00a763774dd255b14aff997285e`, under
`trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/`:

- `os/linux/rt_rbus_pci_drv.c:152-173` creates `cmdQTask` running
  `RTPCICmdThread`. Its `RtmpMgmtTaskExit` at lines 190-207 marks the queue
  stopped and calls `RtmpOSTaskKill` on that task.
- `common/rtmp_init_inf.c:888` invokes `RtmpMgmtTaskExit` during radio close,
  after net-tasklet shutdown and MLME halt. It also invokes that helper in
  initialization failure cleanup at line 625.
- `os/linux/rt_linux.c:921-945` implements task termination with
  `kthread_stop` or a signal followed by `wait_for_completion`, depending on
  the compiled task implementation. Both require the worker to terminate.

Combined with the previously traced watchdog/reset command-thread path,
these dependencies rule out blindly holding a transition mutex across close
while reset blocks on the same mutex: close could wait for the very worker
waiting for its lock. This is a source-level possible deadlock, not an
observed router failure. The actual target task variant still needs checking.

Design requirement for the next implementation: publish a closing/stopping
state under a short adapter-scoped gate before teardown; incoming command-thread
reset/open work must refuse or defer without waiting on a lock held by the
thread joining it. Release the short gate before task joins, flush polls or
firmware waits. Keep adapter lifetime pinned until accepted users retire, and
revalidate main-radio/BSS generation at the final open decision. Merely adding
an RC mutex or holding BcnRingLock over close cannot satisfy these conditions.
The init-failure path needs the same ordering review as normal close.

No driver candidate or production handler changed in this audit. No test,
firmware build or router command was run; evidence is direct pinned-source
inspection. Next trace RTPCICmdThread shutdown/queue draining and choose the
nonblocking transition admission and lifetime protocol before patching it.

## Command-worker exit and accepted queue lifetime — Sol, 2026-10-22

Pinned revision remains `c25283e915a2a00a763774dd255b14aff997285e`.
Paths below are relative to the MT7603 `mt76x3` driver root.

`os/linux/rt_rbus_pci_drv.c:1833-1851` publishes RUNNING under CmdQLock,
waits, checks STOPED and then calls CMDHandler when not suspended. In
`common/rtmp_init.c:2509-2525`, CMDHandler loops on queue size, dequeues under
CmdQLock and releases it before checking HALT/NIC flags. It does not recheck
CmdQState there. Its periodic-command case at line 2651 calls MlmePeriodicExec,
which is the previously inspected watchdog/reset entry. Consequently a STOPED
queue state alone does not stop a handler already draining accepted commands.
The HALT/NIC checks are separate observations, not atomic transition admission.

`rt_rbus_pci_drv.c:1854-1881` conditionally frees remaining CmdQ elements and
payloads only when PM_FlgSuspend is false. This generic cleanup has no explicit
IoT result publication. It must not be treated as a cancellation receipt or
proof that future IoT result references are retired. The suspended case needs
separate ownership analysis before any adapter-free safety claim.

`common/cmm_cmd.c:154-180` rejects insertion under CmdQLock after STOPED and
frees rejected allocation, but legacy RTEnqueueInternalCmd returns SUCCESS
at the end even on that rejection. The existing isolated checked-enqueue
candidate already fixes the opt-in status; it does not solve cancellation of
previously accepted commands. No duplicate enqueue implementation was added.

Added the resulting production gates to IOT-WIFI-IMPLEMENTATION-CONTRACT.md:
nonblocking generation admission before hardware access, explicit queued IoT
cancellation outcomes, suspended-exit ownership and new-generation rejection of
stale work. Next bind these requirements to the existing queued-result and
radio-lifecycle candidates; inspect their cancellation/refcount integration
before introducing a driver-wide gate. No production source or router changes,
firmware build or executable tests in this read-only source review.

## Pending cancellation notification candidate — Sol, 2026-10-22

Added `wr_iot_queue_cancel_pending` to queued-cleanup.h. Unlike cleanup it
publishes cancellation without clearing the envelope or releasing the queue
reference. prepare-queue-cleanup.py now stages a worker-exit walk under CmdQLock,
marks STOPED and notifies pending IoT work before the suspend-dependent free
branch. This closes the missing notification path while retaining existing
buffer/reference ownership for subsequent retirement. It does not prove the
suspended retained queue is eventually freed or permit adapter destruction.

The strict MinGW queued-result fixture passed, including cancellation preserving
two references/envelope, one terminal notification, refusal of later start and
subsequent cleanup dropping exactly one reference. Generator Python AST and
`git diff --check` passed. The modified full generated source was not compiled
or executed; target compilation, shutdown concurrency, adapter lifetime and
production installation remain unverified. Next validate the actual generated
worker-exit slice for suspended and ordinary shutdown, then establish its
retirement/lifetime protocol. No router operation or firmware build.

## Readiness-to-open boundary — owner-directed checkpoint, 2026-10-22

Rechecked the owner's quoted checkpoint against activation.h, MBSS lifecycle
preparer and radio-error bundle: production backend remains absent; bundle
still declares production_installed=false and bss_close_exclusion_proven=false.
The recent queue cancellation candidate is support work, not a replacement
for the required adapter-wide open/close/reset transition protocol.

Made the BSS_UP backend contract explicit in activation.h: revalidate adapter
generation, main-radio readiness and absence of close/reset under the same
driver transition owner as the opening mutation. An outer RC lock and an
earlier MAIN_RADIO_READY result do not establish that exclusion.

The existing activation fixture now injects loss of readiness after the ready
stage succeeds but before BSS_UP. Its simulated backend rejects before any BSS
opening mutation, and recovery finishes inactive with isolation/resources
retired. Strict MinGW -std=gnu11 -Wall -Wextra -Werror -O2 fixture passed;
whitespace check passed. This validates the required failure behavior in an
injected backend only; it does not implement or prove a real shared driver gate.

Resume from adapter-scoped admission/lifetime integration in MBSS wrappers,
virtual-interface first/additional open, close and reset. Keep task-join waits
outside locks needed by the command worker; retain explicit cancellation and
recovery on ambiguous hardware mutation. Do not install the partial bundle as
a complete backend. No driver build, image or router state changed.

## Generated pending-notification coverage — Sol, 2026-10-22

Extended prepare-queued-composition-check.py to extract and execute the actual
notification walk inserted by prepare-queue-cleanup.py before the worker's
PM_FlgSuspend-dependent free branch. The fixture now supplies linked queue
nodes and checks two accepted IoT results plus an unrelated tail. It runs the
walk twice, requires STOPED, no buffer frees, retained envelopes/two references,
one cancellation notification per result, refused subsequent start, then one
queue-reference release at later cleanup. Existing dispatch/free slices remain
covered. This checks the unconditional pre-suspend fragment, not the entire
suspended thread lifecycle or adapter retirement.

Prepared pinned originals c25283e915a2a00a763774dd255b14aff997285e from the
local bare archive; the existing preparers verified exact blob hashes. Generated
composition compiled with host GCC -std=c11 -Wall -Wextra -Werror -O2 and ran
successfully. Evidence directory:
C:/Users/ANDRZEJ/AppData/Local/Temp/iot-queue-notify-mbgqx3al.
The initial sandbox attempt failed at nested-directory creation with WinError 5;
the successful attempt used the approved escalated local command. The failed
empty workspace directory iot-queue-notify-3w6_c0t1 was retained, not removed.
No network/router, MIPS driver compilation or firmware build was involved.
The remaining primary dependency is shared adapter transition/lifetime admission
for BSS open, close and reset, including eventual suspended-queue retirement.
