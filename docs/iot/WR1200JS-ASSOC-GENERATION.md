# Queued WPA association generation — WR1200JS MT7603E

Implemented in the isolated `peer82` candidate; host checks pass. MIPS module,
final image and router runtime verification of this change remain pending.
Producer: `tools/iot/assoc-generation-composition.py`, applied by
`prepare-driver-api.py` after predecessor layers and before manifest writes.
Review diff: `WR1200JS-ASSOC-GENERATION.patch` (against pinned vendor source,
not a second patch to apply over the composed candidate).

Pinned SDK: vipshmily/padavan-4.4 at
`c25283e915a2a00a763774dd255b14aff997285e`, `trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3`.
Only this SDK was used. No MCU protocol, ACK reuse, shared TX state machines,
radio timing, new reset or scan is changed.

## Identity and reset handling

`include/rtmp.h`: MAC_TABLE_ENTRY gains `unsigned int assoc_gen`.
An unsigned per-WCID backing counter in RTMP_ADAPTER lives **outside MacTab**.
All generation updates use MacTabLock. The entry is a published mirror;
its counter must survive both entry memset and whole-table clears.

`mgmt/mgmt_entrytb.c`:

- MacTableInsertEntry advances the slot after mac_entry_reset (which clears
  the complete entry once or twice). It skips an exhausted slot.
- MacTableDeleteEntry's existing locked, MAC-matching body advances/invalidate
  the generation before native teardown. The composed deletion wrapper and
  reset-ownership gates remain intact.
- MacTableReset/ResetWdev retain the backing counters outside their clear area.

`ap/ap_repeater.c`: native repeater allocation advances after both possible
entry clears, before entry publication. Counter exhaustion refuses allocation.

`ap/ap_assoc.c`: both normal association update and WSC success advance under
MacTabLock, including association in place with the same WCID and MAC.
Exhaustion refuses association. The EAPOL pairwise-key renewal assignment to
SST_ASSOC is not a new association and does not advance the generation.
APCLI insertion uses the allocation path. RRM/FT synthetic station insertion
also gets allocation generation; this does not claim a separate audit of every
optional FT reassociation interface.

Fresh adapter allocation is zeroed by os/linux/rt_linux.c,
AdapterBlockAllocateMemory, called from common/rtmp_init.c,
RTMPAllocAdapterBlock. No live table reset reinitializes the backing array.
Zero never matches. A slot reaching UINT_MAX stays exhausted on subsequent
advance attempts; it never wraps to an old valid generation. No reset/restart
is automatically requested to recover exhaustion.

## Enqueue and execution

`include/mlme.h`: MLME_QUEUE_ELEM carries assoc_gen, assoc_wcid, assoc_addr.
Msg remains the first field, preserving the native alignment placement.

`common/mlme.c`:

1. MlmeEnqueue and EAPMlmeEnqueue stamp internal six-byte-MAC events.
2. MlmeEnqueueForRecv stamps the actual receive WCID/MAC for either queue.
3. Capture uses MacTabLock immediately before queue locking; it does not nest
   table locking under queue locking. If reassociation occurs between capture
   and publication, the event retains its **older** identity and is rejected.
4. Requeue copies the original stamp verbatim; it never refreshes an old event
   against a new station. Non-WPA producers explicitly publish a zero stamp.
5. A stale WPA event is discarded before the disconnected-key requeue branch
   and checked again immediately before WPA dispatch. Normal element cleanup
   remains with the existing handler. No log flood, deauth or reset is added.

`common/cmm_wpa.c`: Start, Timeout and Key handlers validate the native lookup
against the stamped slot/MAC/generation before action state mutation. The
AP EAPOL-Key group-key request validates again immediately before its
WPAInstallSharedKey call. On PCI MT7603 the shared-key macro directly calls
CmdProcAddRemoveKey (`include/mac/mac_mt/mt_mac_pci.h`), rather than a separate
USB command-thread payload. This patch does not stamp unrelated USB queues.
The independent GREKEYPeriodicExec timer retains its existing ra2 admission;
it is not a queued station EAPOL event.


New callback-side lock acquisitions use `spin_trylock_bh`, matching this SDK's
BH lock semantics. The OS_ABL form unwraps the existing `pContent` lock exactly
as `RtmpOsSpinLockBh` does. Contention refuses the enqueue/action/association
without waiting, spinning or modifying counters. This is necessary because
native deletion/entry reset cancels station timers while holding MacTabLock;
adding a blocking acquisition in their callbacks could deadlock. Protocol
retries retain their native ownership. The fixture exercises both direct and
OS_ABL layouts, busy-lock refusal and a missing OS_ABL lock.

In this PCI AP target, the queued GTK-related work is EAPOL-Key processing in
the same MLME payload. Its AP group-key-request write receives an additional
identity check immediately before WPAInstallSharedKey. Independent periodic
GREKEY callback admission remains the previous, separate counted control-user
mechanism. USB key command queues and deep APCLI GTK writer lifetime are not
claimed covered by this ra2 AP change.

## What this does and does not prove

It rejects events already stale at capture/dispatch/key-write checks, including
same-MAC reuse and in-place reassociation. It does **not** pin a station for the
entire WPA action: a concurrent deletion/reassociation after the last check is
still an execution-lifetime issue. Holding MacTabLock over arbitrary WPA actions
would be unsafe because native timeout actions can invoke station deletion.
No such lock or global state-machine change is introduced. A pre-enqueue stale
timer callback and firmware events without an original association tag also
need their own provenance; restamping cannot retrospectively identify them.
Thus this change is not proof of complete safe OFF/reopen or original TxS
packet ownership, and does not change those acceptance statuses to FIXED.

## Verification

`tools/iot/check-assoc-generation.py` composes the exact pinned source, checks
all four enqueue branches and requeue/dispatch insertion points, compiles and
executes the **native modified normal/EAP enqueue functions and native entry
reset** with GCC ASan/UBSan, and executes the actual generation helper header.
Cases cover same-MAC/WCID reuse, reassociation, invalid entry/MAC/WCID, malformed
or missing capture payload, stale snapshot publication, original stamp on
requeue, unrelated events, whole table clear, counter exhaustion and wrong
native lookup slot. Composition rejects a second application.

The prepared-source CI check compares all three exact native enqueue bodies,
the WPA source, helper headers and association hook counts against the final
candidate. Manifest hashes still cover every candidate file. Focused snapshots
now include generation helpers, entry structure, association and repeater code.
ABI runs the host fixture; optional compiles the isolated MIPS driver afterward.
The host fixture does not compile a Linux kernel or prove BH scheduling behavior.
Local evidence: `docs/evidence/WR1200JS-ASSOC-GENERATION-HOST-2026-11-18.json`.

Runtime acceptance, separately authorized: Main/Guest/IoT handshake and GTK
rotation; disconnect/reconnect with the same MAC and repeated WCID reuse;
queue EAPOL-Key/Start/Timeout before reuse and confirm none modifies the new
peer; confirm newly stamped events still authenticate; ra2 OFF/reopen while
Main/Guest associations remain stable. Race injection after the final check
must remain a separate execution-lifetime test, not be reported as solved by
a generation equality test. No router configuration was changed here.
