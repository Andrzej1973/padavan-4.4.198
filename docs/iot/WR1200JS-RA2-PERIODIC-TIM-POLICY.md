# WR1200JS reserved ra2 periodic beacon / TIM policy

Scope: isolated three-BSS MT7603 candidate, not the production image or device
acceptance. Source base c25283e915a2a00a763774dd255b14aff997285e.

The periodic APUpdateBeaconFrame wrapper retains the existing exclusive producer
pin and DMA admission. For MT7603 BSS2 it now also requires zero observed beacon
TxS reservations/callbacks, BCN_TX_IDLE and the same admitted producer generation.
The BSS count is rechecked under BcnRingLock after the TxS observation. Busy,
unknown, non-IDLE or changed layout skips the inner periodic builder and releases
the pin exactly once. It cannot enter APCheckBcnQHandler to force shared queue
recovery as a side effect of this periodic update. Initial APMakeBssBeacon is
not routed through the new periodic guard.

While waiting, the existing mapped beacon (including its TIM IE) is untouched.
New buffered-traffic bits remain in the live software bitmap and are consumed by
the next admitted update. No OR of an old TIM into a later peer generation is
introduced: actual empty-queue cleanup, disassociation and AID reuse remain
owned by their existing station lifecycle. In pinned rtmp.h the ordinary
WLAN_MR_TIM_BIT_CLEAR macro is already empty; CLEAR1 in common/mlme.c clears
when the enumerated software queues are empty and its idle countdown expires.
Keeping obsolete bits after those queues are gone would announce nonexistent
buffered traffic. This patch changes neither queue expiration nor packet drops.

No BKOFF_SLOT_CFG, SIFS, beacon period, DTIM counter/offset or radio frequency
is changed. APUpdateAllBeaconFrame still owns the normal shared DTIM tick.
A zero host TxS observation is not proof that no late firmware report exists;
the original ACK/RF/late-TxS/reopen blockers and close fences remain in force.

## Existing WebUI path

This source has no user/www/wireless.asp. Its existing Classic page is
user/www/n56u_ribbon_fixed/Advanced_WAdvanced2g_Content.asp. It exposes rt_dtim
(1..255, default1) and rt_bcn (20..1000, default100). HTTP variables.c maps both
to EVM_RESTART_WIFI2. RC ralink.c emits DtimPeriod and BeaconPeriod, validating
the same bounds. These are shared radio settings and apply by radio restart,
not independent hot ra2 controls. No duplicate NVRAM key or unsupported Modern
Apply control is added. A user-driven change to these settings remains distinct
from ordinary IoT enable/disable and must not be described as restart-free.

## Opt-in diagnostics

prepare-psm-diagnostics.py remains compile-time opt-in WR_IOT_PSM_DIAG, OFF in
the normal image. BSS-attributed events are now scoped to slot2. Event meanings:

| event | x | y | meaning |
|---|---|---|---|
|0|old PsMode|new PsMode|PSM transition observed; not ESP-specific identification|
|1|PsQIdleCount|enqCount|queue-flush site reached; not a hardware packet-drop total|
|2|NoDataIdleCount|StaIdleTimeout|station age-out decision|
|3|DtimCount|DtimPeriod|TIM construction observation|
|4|ME/RE/LE/BE bit mask|raw MPDU count|delivered Format0 TxS; BSS explicitly unknown|
|5|BCN_TX_IDLE|0|beacon callback changed host state to IDLE; not RF retirement|

Kernel log prefix is wr_ps. hits counts instrumented events per translation unit,
including suppressed logs. Existing rate limit is8 lines per5 seconds per
translation unit. No peer pointer is retained, allocation added, extra TxS
requested, ACK protection removed or new hardware operation issued. Event4 is
not attributed to ra2 by guessing a BSS from WCID. Obtain the station WCID from
an independently authorized station observation to correlate an ESP client.

## Verification and remaining work

Host GCC warnings-as-errors and ASan/UBSan cover exclusive pin ownership,
DMA busy/unknown, TxS busy/unknown, non-IDLE state, close/generation changes,
layout change during observation and unchanged Guest admission. Diagnostic
ON/OFF checks cover rate limiting, suppressed-event counts, non-IoT filtering,
unknown-BSS TxS, invalid events and zero argument evaluation when compiled OFF.
The diagnostic patch applies cleanly to pinned source. First-beacon composition
and reserved-UP refresh regression checks pass.

Target candidate/module compilation is pending for this revision. The normal
firmware still lacks an accepted IoT driver/controller binding; do not install
this isolated driver into a release merely to make these controls available.
Runtime tests must cover Main/Guest associations, TIM captures for an actual
sleeping client during delayed TxS, queue drain, wake/disassociation/AID reuse,
restart, reboot and physical PCI/DMA/IRQ teardown. No router was contacted.
