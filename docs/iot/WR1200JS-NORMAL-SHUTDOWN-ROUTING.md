# Normal router shutdown after IoT ACTIVE

Pinned SDK `trunk/user/rc/init.c:catch_sig_fatal` calls `shutdown_router()`
directly from SIGTERM/SIGQUIT handling. Pinned `rc.c:shutdown_router` stops WAN,
services and then Wi-Fi; failure of a Wi-Fi helper alone does not stop subsequent
LAN teardown. Existing IoT transaction `active/pending` admission delays a normal
signal only while that particular transaction is active. Returning ACTIVE from
a request is therefore not proof that future router shutdown is coordinated.

The cold terminal now rechecks pending signals after child completion, but that
check cannot prove every signal interleaving around the final unmask. General
post-ACTIVE shutdown needs a PID1 process-context route independent of the
current transaction. Signal handlers must not inspect backend structs or invoke
allocation, driver APIs, service locks or backend continuation.

## Inert request slot implemented

`rc-shutdown-admission.h` provides a default-zero normal-route arm and first
requested SIGTERM/SIGQUIT slot, both sig_atomic_t. Existing active transactions
keep their existing pending signal. When explicitly armed, a signal outside
active admission is retained for a future PID1 consumer; a signal replayed by a
completed transaction fence also lands there instead of immediately tearing down
LAN. New ordinary shutdown admission refuses while such a request exists.
SIGPWR and process faults retain their previous immediate path.

The actual signal/fence fixture covers first-request preservation, normal signal
outside admission, signal queued while the outer fence blocks delivery, replay
after its cleanup and another signal after final unmask. The route is not armed
by runtime/boot and no request-acknowledgement shortcut is supplied.

## Required before enabling

1. Retained PID1 controller must claim the routed request without losing a new
   normal signal and must prevent unrelated network/radio notifications.
2. Read the actual independent backend: finish an owned START/STOP, execute one
   owned OFF for ACTIVE, or use a distinct current INITIAL_OFF observation.
3. Transfer exact software CLOSED to the existing physical Main stop lifetime;
   prove AUX/auth drain, ARM/Main completion/RELEASE and PCI/DMA/IRQ joins at their
   actual source/target/runtime levels. Software CLOSE cannot replace this.
4. Release credentials/guards and retire the shutdown controller inside the
   final signal fence. Only then deliberately hand the original signal back to
   the stock shutdown path with routing disabled for that handoff. A fresh signal
   must not resurrect an old completed operation or start a second OFF.
5. Test missing/late/duplicate signal, early and late OFF refusal, stale tuple,
   failed unmask, child uncertainty, Main DOWN failure, device removal and both
   SIGTERM reboot/SIGQUIT halt. Verify user settings and access are retained.

These steps are incomplete. The slot test is not shutdown completion, not
physical RF/DMA retirement and not permission to flash a candidate image.

## Consumer integration audit — 2026-11-15

Current `rc-physical-stop.c:physical_begin` rejects active/pending admission and
uses the ordinary `wr_iot_radio_stop_fence_begin`. That fence invokes ordinary
`wr_iot_rc_shutdown_begin`, which rejects a retained normal-route request.
Consequently a routed request cannot yet enter the physical controller.
Clearing the request just to pass admission would lose its ownership witness.

A second independent constraint exists in `wr_iot_rc_physical_step`: a pending
normal signal while the session is still IDLE selects `prearm_cancel` once
quiescence completes. That cancellation deliberately does not submit ARM or
Main DOWN. Reusing that path as a successful routed physical stop would be an
incorrect completion claim. A routed shutdown must have an explicit controller
mode distinguishing its original intent from cancellation of an ordinary
restart. It must retain the request until verified physical RELEASE.

The backend already provides `wr_iot_rc_quiesce_shutdown_begin`, which requires
normal pending admission and suppresses restart resume. Simply calling the
ordinary quiesce entry would not establish these semantics. INITIAL_OFF still
requires a separate verified path; no synthetic CLOSED token is permitted.

The actual signal/fence regression was rerun successfully. Runtime arming remains
absent. Standard1302 and its ABI succeeded; exact4a79c103 optional peer82 was
queued as run43732157782 after checking for a duplicate. Optional1298 succeeded;
optional1300 was observed in progress. These CI results do not cover this
unimplemented routed physical consumer or physical device acceptance.

## Explicit routed fence claim implemented locally — 2026-11-15

`wr_iot_radio_stop_fence_begin_routed_shutdown` blocks normal signals before
checking an armed valid first request and publishing active/pending ownership.
It preserves normal_route_requested, rejects nested routed claims and leaves
ordinary admission blocked. The original signal remains pending as the shutdown
intent. Ending this fence replays into the still-armed retained route; it does
not authorize stock teardown or acknowledge physical completion.

Actual signal tests exercise original SIGTERM plus queued duplicate SIGQUIT,
refused competing owners, and absent/invalid/unarmed request rejection. Injected
mask-restore failure retains the exact token, active/pending and request; retry
releases admission without clearing the route. ASan/UBSan checks for normal
routing, normal/nested fence, failed restore and actual physical controller
composition pass. These are host tests, not MIPS/image/device evidence.

The physical controller has NOT been switched to this API: its explicit routed
mode, shutdown-specific quiesce, INITIAL_OFF handling, PID1 dispatch and final
physical-release-based acknowledgement still need implementation. No production
route arm or router operation was added. Local changes remain grouped for that
consumer rather than publishing an incomplete activation.

## Routed physical controller mode implemented locally — 2026-11-15

`wr_iot_rc_physical_begin_routed_shutdown` accepts a private OFF envelope and
zero restart intent. It uses the explicit routed fence and existing
`wr_iot_rc_quiesce_shutdown_begin`; that backend entry wipes desired resume
credentials and disables resume. A retained routed-mode flag suppresses both
automatic and directly requested pre-ARM cancellation, so the original normal
shutdown intent can progress through AUX/auth drain, ARM, Main completion and
RELEASE rather than being mistaken for restart cancellation.

The actual controller/session/fence fixture verifies absent-route and competing
owner refusal, shutdown quiesce without desired settings, no physical work
before quiesce, CLOSE alone refusing off_read, one Main DOWN, six AUX slots,
exact RELEASE receipt and one terminal take. The route remains retained after
fence replay, and ordinary admission still refuses. Driver IO and backend
observations in that fixture are actors, not physical evidence. Existing actual
backend/OFF/controller composition and pre-ARM cancellation, mask failure and
exact OFF consumption regressions also pass with ASan/UBSan.

This replaces the earlier statement that no physical caller uses the routed
fence. It does NOT supply PID1 dispatch, safe INITIAL_OFF physical handling,
final acknowledgement/stock signal handoff or runtime arming. Those remain
required before enabling the feature. Full prepared target and image evidence
for these local changes is still missing.

## Exact RELEASE final handoff implemented locally — 2026-11-15

`wr_iot_rc_physical_shutdown_release(id, created)` requires the routed owner,
armed original normal signal and exact completed off_read RELEASE receipt.
Generic physical take/take_off now refuse routed owners so they cannot discard
the receipt before dedicated handoff. The final helper blocks normal signals,
retains the original mask in the physical owner across a failed restore, and
restores it while routing remains armed. An originally blocked normal mask is
refused rather than claiming synchronous stock replay. Only after successful
restore does it retire private physical state, clear/disarm the route and raise
the original signal. No physical operation is repeated on retry.

The routed fixture now covers foreign envelope refusal, generic take refusal,
failed final mask restore with exact retry, and a stock-signal actor checking
private retirement and disarmed routing before replay. ASan/UBSan routed,
ordinary physical, ordinary mask-failure and exact OFF-take checks pass.
This supersedes the earlier missing-final-helper note, but is still host-only.
PID1 dispatch and INITIAL_OFF handling remain absent; full signal interleaving,
target build, image verification and physical acceptance are not implied.

## Actual backend and signal interleaving regression — 2026-11-15

`check-rc-routed-shutdown.py` composes actual activation/backend/OFF code with
actual physical controller/session/fence and final handoff. The external driver
and network-resource operations remain injected. It verifies delayed isolation
prevents AUX/ARM/Main, one CLOSE/Main DOWN/RELEASE, wiped resume secrets, generic
take refusal and private retirement before stock signal handling.

The focused routed fixture now runs both original SIGTERM and SIGQUIT. An
opposite normal signal queued at final mask restore is routed without replacing
the first intent. Originally blocked masks refuse; failed restore retries with
the saved original mask. These are additional host evidence, not proof of all
possible signal interleavings. Both fixtures are in the physical suite.
See evidence/WR1200JS-ROUTED-SHUTDOWN-HOST-2026-11-15.json for exact source hashes.
Standard1303 succeeded; exact e08c8810 peer82 optional43732936560 was queued after
a duplicate check. This published CI source predates the local routed changes.
