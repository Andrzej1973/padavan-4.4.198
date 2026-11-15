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
entry. Multicast/WDS/APCLI, WAN/IAPP, IoT rebind, post-UP rollback, OFF receipt
consumption and final transaction retirement remain to integrate and verify.
No new target or device acceptance is claimed. Existing ordinary ra2 toggle,
MCU ACK protection and global driver queues/timing are unchanged.
