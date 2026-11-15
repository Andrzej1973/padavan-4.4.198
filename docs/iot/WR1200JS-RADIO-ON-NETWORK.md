# OFF-to-ON Main LAN, Guest and services

`radio-on-main.c:wr_iot_on_main_lan_step` observes Main configuration before
attempting the existing fixed ra0-to-br0 bridge adapter once. Subsequent calls
only read membership. Missing/foreign membership or epoch loss never triggers
another add; a successful bridge readback is followed by Main identity checks.

`radio-on-guest.c` retains its real ON Main parent, with no fabricated restart
origin. It follows the established vendor Guest sequence using the existing
SDK policy/transport helpers: DOWN bridge attachment, L2 isolation, then UP.
Guest policy OFF performs no UP. Bridge/UP mutations are attempted once; a
post-UP policy or isolation loss performs one administrative DOWN and retains
the parent. No submitted UP means no ownership to tear down a foreign Guest.
Administrative DOWN does not certify RF/DMA retirement.

`radio-on-services.c` requires the Guest controller's current policy/state and
Main/LAN proof before every phase. It copies the existing SDK enterprise/RSSI
policy, then attempts each of the three established service slots once. Policy
drift, pending shutdown, invalid Main or Guest blocks further submissions.
Uncertain/not-submitted calls remain retained, with no automatic replay.
Returned commands do not prove daemon readiness or applied RSSI values.

Focused C11/ASan/UBSan parent composition passes actual admission, generation,
journal, profile scanner, Main, Guest and service controllers with injected SDK
and bridge/identity/UP boundaries. Cases cover one-shot Main add, lost bridge,
Guest OFF, failed Guest bridge, post-UP policy/isolation drift, no-submission,
three ordered service slots and pending shutdown. Separate service fault tests
cover uncertain/not-submitted outcomes and policy drift. Prepared separate
translation units compile with C11-Werror. Tests clean their temporary trees.

The preparer, ABI unit list, source/Make verifier and target-link symbol gates
include these modules. They remain unbound to the public RC physical OFF/ON
entry. WAN/IAPP, IoT rebind, post-UP rollback, OFF receipt
consumption and final transaction retirement remain to integrate and verify.
No new target or device acceptance is claimed. Existing ordinary ra2 toggle,
MCU ACK protection and global driver queues/timing are unchanged.

## Ordered restore and mode0 AUX policy

`radio-on-restore.c` owns children at stable addresses and advances one phase
per tick: generation, one RAM-state attempt before any Main UP, Main/LAN, Guest,
multicast, then services. PREPARED remains an observation with all baselines and
outer guards retained. RAM failure prevents UP and is not retried. Multicast
uses existing fixed BSS0/BSS1 adapters, records attempt before writing, omits
Guest when disabled, and refuses policy/readback drift. Uncertain writes are
not replayed. Pending shutdown may drain Guest's owned DOWN; complete parent
shutdown recovery remains to integrate.

The actual pinned SDK net_wifi.c activates WDS only in mode1/2 and APCLI only
in mode3/4 with saved SSID. Our mode0 scope requires the inactive alternatives:
`radio-on-aux.c` observes wds3,wds2,wds1,wds0,apcli0 absent or administrative
DOWN with no master. Missing interface is accepted only ENODEV/ENXIO; interface
index, mode and guard are rechecked. No foreign AUX interface is stopped or
detached. Source hash/function lines are recorded in
WR1200JS-ON-MODE0-AUX-POLICY-2026-11-15.json.

Host C11-Werror ASan/UBSan composition passed the whole new restore chain,
reload0/Guest OFF, one RAM write, RAM failure before UP, uncertain multicast
blocking services, current multicast/AUX loss and pending Guest recovery.
Separate multicast and AUX fixtures cover policy/identity/syscall refusals.
Prepared separate translation units are checked; new MIPS/target results remain
pending. No private/public RC entry binding, WAN/IAPP, ra2 rebind or final
receipt/guard retirement is implied by PREPARED.

## Exact private rebind handoff

`radio-on-handoff.c` requires PREPARED, the stable child pointer chain, matching
OPEN nonce/request ID, creation time and all six immutable desired fields.
Fresh restore observations precede the only backend begin. HANDOFF and creation
time are recorded before calling the backend; even a refusal may retain partial
admission and cannot cause another begin. The existing RC rebind backend retains
its normal old OFF provenance and fresh new-Main validation; no restart-origin
object is fabricated and no old receipt is rewritten to the new epoch.

Continuation reconstructs the exact private envelope, advances the retained
backend by ID/time and requires its exact ACTIVE proof for original physical
RELEASE and new Main identity. APPLIED alone is insufficient. Origin/AUX and
multicast observations are repeated; the temporary credential-bearing envelope
is volatile-wiped. A separate read-only `wr_iot_on_rebind_current` never calls
activation_continue and is available for final preflight.

C11-Werror ASan/UBSan composition passed mismatched nonce, each desired field,
zero time, one begin for success/refusal, APPLIED-without-ACTIVE refusal, exact
ACTIVE, epoch/receipt/AUX/multicast drift and no progress from read-only checks.
It uses actual admission/profile/journal/Main/Guest/multicast/services/restore
controllers with a backend actor. Prepared separate translation units also
compile. This does not replace real target rebind, image or device evidence.
The API remains private and unbound to RC OFF/ON entry; failure/shutdown recovery,
receipt consumption, final retirement and WAN/IAPP remain unfinished.
