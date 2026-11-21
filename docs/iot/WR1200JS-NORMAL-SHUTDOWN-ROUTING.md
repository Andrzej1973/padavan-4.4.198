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

## Process-context normal shutdown controller staged — 2026-11-15

`rc-normal-shutdown.c` retains one private OFF envelope. Existing active/pending,
radio ON/OFF owners defer admission. Missing monotonic time, unavailable entropy
or all-zero request identity defer without submitting an OFF. After generation,
retries preserve the same envelope; once claimed, each call advances at most one
physical step. Preparation refusal first balances the physical fence, then
retains the failed request without replay or an automatic second OFF.

Final physical release accepts an optional infallible owner-retirement callback.
The controller uses it to wipe its envelope and mark itself spent before stock
signal replay. An already spent controller cannot submit again. Actual
controller/session/fence tests cover success and preparation refusal, while
external backend/IO are actors. The existing actual backend routed composition
also passes after the callback addition. Runtime preparation stages the new
unit/header and reports controller_linked=true, dispatch_bound=false and
route_armed=false. Runtime preparer checks pass. No normal-route arm or PID1 wait
invocation has been added: notification ordering and INITIAL_OFF remain required
before that binding can be enabled. Full MIPS/image/device evidence is pending.

## PID1 wait dispatch bound, routing still disabled — 2026-11-15

Runtime wait now schedules the normal-shutdown controller after existing OFF,
cold/ON, physical/restart and backend continuation owners, before bootstrap.
A pending routed shutdown allows wait progress despite notification/alarm flags;
those flags stay set. The prepared pinned init loop remains inside its wait
while normal shutdown is pending and calls wait directly instead of spawning a
shell or entering notification handlers. Other board loop behavior is retained.

Actual runtime fixture verifies notification retention, normal controller
progress and prior backend-owner priority. The generated init loop is compiled
and executed for WR1200JS and another board: only WR drains the routed request,
and both preserve existing notification/alarm flags. Runtime preparation and
controller success/refusal regressions pass. Manifest dispatch_bound is now true,
route_armed remains false. No automatic arm was added.

This loop binding alone does not close the signal-arrival boundary between loop
exit and notification handling. That boundary and never-opened INITIAL_OFF
physical shutdown still require proof/implementation before routing can be armed.
The current local changes have no MIPS/image or device acceptance yet.
Standard1304/029c2228 succeeded; exact optional43733787256 was queued after
checking duplicates. Its source predates these local shutdown changes.

## Notification admission boundary implemented locally — 2026-11-15

Each pinned SIGUSR1/SIGALRM batch now calls
`wr_iot_rc_normal_notification_begin` before clearing its flag and calls the
matching end afterward. With routing unarmed, this keeps the legacy path. With
routing armed, a recorded route or an active transaction's pending normal
signal refuses admission and preserves the flag. An admitted process-context
batch owns the notification slot; normal shutdown stepping refuses until its
end. Signal context only records shutdown, so an already admitted synchronous
batch can finish before any process-context physical shutdown progression.

This admission deliberately does not hold a signal mask across notification
handlers: a handler can start an asynchronous Wi-Fi fence, which must retain its
actual original mask rather than inherit a temporary notification wrapper mask.
The second request check after owner publication conservatively refuses a signal
recorded during admission. Pending normal signals of active IoT transactions
also keep PID1 in the wait loop until their original fence drains and replays.

Actual controller tests cover an admitted batch followed by SIGTERM, unchanged
normal signal mask, refused reentry/late admission and active-transaction pending
signal before route replay. Prepared notification hooks compile and execute for
WR1200JS and another board, including a shutdown recorded during the first batch
which leaves the second flag queued. The original runtime and preparation
regressions pass. Target symbol gates require both admission functions; target
execution is pending. This addresses the earlier missing admission-boundary
implementation; all-interleaving/device acceptance and INITIAL_OFF remain open.
No automatic normal-route arm was added.

## INITIAL_OFF physical source audit — 2026-11-15

The missing path is driver-level Linux admission, not an absent ROM document:

- `precreated-idle-reference.h:wr_iot_precreated_idle_reference` requires ra2's
  last_token/close_serial/close_epoch/stages to remain zero and Main READY.
  A prior attempted OPEN cannot qualify. `initial-off.c` binds fresh repeated
  observations to the same epoch/generation, but does not retire DMA/IRQ.
- `physical-stop-wire.h:wr_iot_physical_stop_request_valid` requires nonzero
  OPEN/CLOSE identifiers. `physical-stop-arm-admission.inc` then calls
  `wr_iot_physical_stop_prior_close`, which validates actual retained released
  OPEN/CLOSE owners. Substituting nonzero INITIAL_OFF identifiers would be false.
- `physical-stop-lifetime.h:wr_iot_physical_stop_lifetime_begin_main` captures the
  actual Main device/generation/OPEN and transition serial under the existing
  lock; this part does not inherently need a prior ra2 OPEN. Its capture/released
  checks and actual callback/dev_put joins provide a reusable Main foundation.
- `physical-stop-query.inc` still requires ra2 CLOSE identity, and
  `physical-stop-main-completion.inc` requires a closed peer-table owner. A
  never-opened table must be proven empty/idle via its own registration witness,
  not relabelled as a completed CLOSE.

Implementation direction, NOT implemented: add a distinctly typed Linux-only
initial-idle physical admission, carrying its fresh idle observation identity;
keep existing CLOSE-origin requests and their validation unchanged. The binding
must latch the same ra2 registration plus real Main lifetime before ARM, then
verify never-opened history and the exact Main release on QUERY/RELEASE. The
live initial-idle predicate cannot simply be called after Main DOWN because it
requires Main READY/nonzero vendor count. Completion must use the latched
identity under the retained physical fence and actual checked Main completion.
No firmware field, ACK reuse, WCID DMA flush, global queue or radio timing change
is needed or authorized by this direction. No initial RF/DMA completion exists
merely because ra2 has never opened.

## INITIAL_OFF completion composition constraints — 2026-11-15

Read-only follow-up while the full host suite runs: peer-table-owner initialization
sets serial/active/retained/poisoned/transactions/closed to zero. This is an empty
software owner, not a CLOSE seal. `physical-stop-record.h:finish_core` and
`physical-stop-main-completion.inc` explicitly require table.closed. A future
initial-idle path must therefore capture and validate an independently empty
never-opened table under MacTabLock and its existing exclusion; it must not set
closed=1 merely to satisfy those existing functions.

The normal idle reply records the exact BSS_OBSERVE ticket epoch/generation/
serial after closed-configuration readback. ARM must consume or latch that
accepted observation before Main lifetime changes and reject later observation,
OPEN, reset or registration changes. Retain Main device/generation/open token,
transition serial, adapter/task/module pins and query identity across completion.
Use a separate origin discriminant for initial-idle versus released-CLOSE;
old wire validity, CLOSE matching and completed-table predicates stay strict.
A new origin needs explicit response/retry/terminal semantics and negative tests
before common endpoint routing. This is the concrete implementation boundary,
not an assumption that never-opened means hardware idle.

## Final stock replay interleaving still needs a dedicated guard — 2026-11-15

Read-only audit during frozen full-suite execution found an uncovered boundary
in `wr_iot_rc_physical_shutdown_release_cleanup`: normal_route_requested is
cleared, routing is disarmed, then raise(original) is called. A second normal
signal delivered after disarm but before that raise reaches the stock handler
with its own signal, potentially selecting halt instead of the first reboot
request (or vice versa). Private physical/controller retirement is already done,
so this is a first-signal semantics/interleaving gap, not evidence of an early
DMA free. Existing duplicate-at-mask-restore tests do not cover this later point.

Do not declare all-interleaving final replay accepted. After the current frozen
suite ends, add a dedicated final replay owner/handler admission that preserves
the original signal through the stock handoff, with injected signal at each
clear/disarm/raise boundary, failed replay and duplicate handling. Avoid holding
a temporary mask that silently changes an asynchronous caller's saved mask.
The production route remains unarmed while this and INITIAL_OFF are incomplete.

## First-signal replay guard implemented locally — 2026-11-15

Admission now contains sig_atomic_t replay_signal/ready/delivered. After exact
RELEASE, restored mask and private retirement, final handoff publishes the
original signal with ready0 before clearing route fields, then sets ready1.
Normal signals before ready or of the opposite type are swallowed; exactly the
first matching ready signal reaches stock. delivered remains latched afterward,
including when stock SIGQUIT returns. Fault signals keep their existing path.
Ordinary admission/route arming and notification batches refuse after replay.

Process-context replay_step preserves an undelivered signal after raise failure.
PID1 pending/step handles that retry even after the private controller is spent;
no second OFF or physical operation is submitted. A focused real-signal fixture
runs both TERM and QUIT with signals at publication/clear/disarm/ready, injected
failed raise then retry, opposite signal just before replay and later duplicates.
The first fixture draft used an ordinary int signal counter; corrected it to
volatile sig_atomic_t before accepting its result. Focused replay, normal-route,
fence-fault, physical routed, normal controller and actual backend routed tests
PASS with ASan/UBSan. This supersedes the specific uncovered disarm-to-raise gap;
full all-interleaving and physical acceptance are not implied.

The earlier full suite PASS covers the pre-guard source hashes only. The new
regression is registered; broad target/prepared verification for this revision
is still required. INITIAL_OFF physical origin remains unimplemented and the
production route remains unarmed.

## Initial-idle physical provenance implemented locally — 2026-11-15

`physical-initial-origin.h` captures a distinct never-opened origin from the
actual accepted current precreated-idle probe plus an already acquired exact
Main lifetime. Main registry generation/token must still equal that lifetime;
observation serial must be current/retired and no active TX is allowed. Capture
is one-shot. It does not call or fabricate CLOSE, seal the peer table or change
old physical request validity.

A read-only history predicate checks the same published ra2 registration with
zero OPEN/CLOSE history even after Main is DOWN, when the live READY-only idle
predicate cannot be used. A separate Main binding checks the retained lifetime
identity. Neither function proves Main completion: the actual release checker
and checked shutdown stages remain required, along with peer-table exclusion.
No ARM endpoint or completion certificate is installed by this header.

The fixture uses actual idle probe begin/finish and Main lifetime acquisition.
It covers absent observation/lifetime, changed Main token before capture,
duplicate capture,12 ra2 history/registration faults, post-DOWN origin and foreign
Main lifetime refusal. ASan/UBSan PASS after initializing fixture device sentinels
to satisfy GCC maybe-uninitialized analysis. Suite-registered; no MIPS/driver
binding/runtime proof yet. Next integrate distinct Linux initial-idle ARM origin,
query/release and real peer-table exclusion without weakening CLOSE-origin flow.

## Initial origin composed with actual Main release — 2026-11-15

Added transition-lock-only `wr_iot_physical_initial_main_released`: same initial
origin/Main lifetime, unchanged never-opened ra2 history, advanced radio epoch,
and existing exact Main lifetime release predicate. Fixture now executes actual
Main stop ticket, preclose, recovery queue/begin, checked DOWN, native completion,
module-pin release and netdev release state transitions. It refuses before
netdev-reference return and with nonzero final vendor count, accepting only after
the exact release. These state transitions use software receipt actors and are
not physical hardware proof.

Source audit corrected the earlier idea of holding a new peer-table reservation:
`peer-close-table.inc:wr_iot_peer_close_hold` itself needs the existing table
owner available, checks actual MacTab/tr entries empty, then starts its own serial.
`wr_iot_peer_close_finish` produces a real closed seal after native close. Holding
a new active owner across Main stop would block that established path. Do not
introduce such a reservation or assign closed1 merely to satisfy initial-idle
completion. Instead eventual distinct initial ARM must retain the existing Main
lifetime and validate actual peer close/executor/stage outcomes with disjoint
locks. No global table state machine changes were made.

The initial origin still is not bound to a typed ARM/QUERY/RELEASE endpoint.
Those bindings, table/executor completion and target/device acceptance remain
required. Production route remains unarmed.

## Distinct initial-origin Linux wire implemented locally — 2026-11-15

`physical-initial-wire.h` defines64-byte WPIQ/WPIR requests/replies with full
64-bit adapter epoch, ra2 generation, accepted IDLE observation serial, driver
attempt and nonce. It reuses only existing action/status meanings. There are no
OPEN token or CLOSE serial fields. Existing WPSQ/WPSR CLOSE-origin syntax and
validation are unchanged. ARM requests have attempt0, ARM replies require the
assigned nonzero attempt; later actions match it exactly. Reserved bytes must be
zero, errors clear decoded output, and reply matching compares every identity.

Host sanitizer fixture covers both protocol discriminators rejecting each other,
request/reply separation, header/reserved corruption, all4 action/status paths,
stale epoch/generation/idle/nonce/status rejection and cleared failures. Initial
origin/Main-release regression also passes. This defines syntax only; no kernel
endpoint, ARM publication, QUERY completion, RELEASE pins or RC initial dispatch
is installed. No firmware protocol/ACK or shared queue change was made.

## Initial-origin attempt bound to wire and Main ticket locally — 2026-11-15

`physical-initial-record.h` joins the accepted initial origin/lifetime to a
serialised exact task/nonce/epoch/generation/idle-serial attempt. ARM is one-shot;
a lost reply can read the same ARMED attempt without acquiring another record.
RUNNING requires the exact captured Main CLOSE ticket after the idle serial.
QUERY only reads the current record; wrong task/attempt and premature RELEASE
refuse with cleared output. The composed fixture runs actual Main close/recovery
and reference-return transitions while reading initial wire replies.

Main reference return alone deliberately leaves this record RUNNING. COMPLETE
publication still needs real peer-table close/executor idle and checked shutdown
stage binding, not an endpoint caller boolean. Reference pins, terminal cleanup
and installed ARM/QUERY/RELEASE routing remain unimplemented. This metadata is
not production adapter state yet. Both origin/record composition and wire
sanitizer regressions PASS; no target/image/device claim.

## Initial-origin checked adapter completion implemented locally — 2026-11-15

`physical-initial-main-completion.inc` samples the exact initial record and
module/task/Main-netdev pins under MacTabLock, validates immutable origin and
actual Main lifetime/netdev-reference return under transition lock, and requires
shutdown2/radio-off4/virtual-down2. It then rechecks exact attempt/task/pins plus
native peer-table closed/no active/retained/poisoned/transactions and idle close
executor under MacTabLock before publishing COMPLETE with the observed epoch.
Locks never nest; RTNL and caller lifetime remain mandatory. Duplicate completion
is read-only and requires the same epoch. No DOWN, allocations, puts or firmware
operations occur in this function.

The fixture compiles and executes this exact adapter fragment with actual idle
and Main close/recovery/reference lifecycle helpers. Vendor struct/lock/pin
boundaries are injected;8 stage/pin/table/executor/history/count/lifetime failures,
missing table seal, missing RTNL and changed epoch refuse. Actual table begin/
close_seal helpers produce the fixture seal, not a boolean argument. ASan/UBSan
PASS after correcting fixture prepared transition-header selection and insertion
position. Origin/record and wire tests also PASS.

This fragment is not installed in adapter or dispatched yet. Initial-origin
pins acquisition/publication, cancel/release reference returns and terminal
retries still need binding. No physical RF/DMA/IRQ/device acceptance is claimed.

## INITIAL_OFF ARM pin publication implemented locally — 2026-11-15

`physical-initial-arm-publication.inc` validates the actual accepted idle probe,
Main lifetime and ra2 registration under transition lock, then checks the free
native pin slot, exact caller-acquired pending bundle, old CLOSE record idle,
peer-table availability/no transactions and idle executor under MacTabLock.
Only a successful initial record ARM transfers the bundle; all refusals leave
its task/device/module fields with the caller. It never calls acquire/drop or
puts under a lock. RTNL and retained Main lifetime protect publication across
disjoint lock snapshots; exact vendor adapter/control/boot conditions are gates.

The composed fixture executes this exact fragment plus origin and Main completion
helpers:7 refusal gates preserve local refs, success transfers once, duplicate
cannot allocate another record, and old CLOSE owner blocks initial publication.
ASan/UBSan PASS. Kernel acquire/drop are not executed in this test: those existing
native helpers require a full terminal caller composition still to be built.
No adapter-field preparation, endpoint dispatch or device installation yet.

## Native reference acquisition/unpublished unwind composed — 2026-11-15

The publication fixture now executes actual `physical-stop-pins.inc` acquire and
drop helpers rather than assigning a successful bundle. Injected kernel ref
primitives count module/task/device references and assert no adapter lock held.
Module-get refusal acquires nothing; a real publication refusal retains local
references, native drop balances all3 once, and a duplicate drop refuses. A
second acquire followed by successful publication retains all3 refs in the
adapter slot, with empty local drop refusing. The eventual terminal detach/drop
is intentionally still missing; this test does not free the published bundle or
claim completed native lifetime. ASan/UBSan PASS. This supersedes the earlier
statement that the publication fixture does not execute acquire/drop helpers.

## Initial pin detach primitive and native CANCEL return locally verified

`physical-initial-pins.inc` separates MacTab-locked exact bundle detachment from
native reference drops. It requires same current task/attempt/nonce and a free
local destination. CANCEL requires ARMED without completion epoch; RELEASE
requires COMPLETE with an advanced completion epoch. It clears slot and record
task before returning the detached local bundle. It does not end Main lifetime
or publish a terminal response. Caller must first validate exact Main cancellation
or release under the transition lock and maintain RTNL/outer lifetime.

The publication fixture now detaches its actually acquired/published bundle for
CANCEL, verifies no reference decrement inside the lock, drops module/task/netdev
outside locks once, and refuses wrong RELEASE/stale attempt/duplicate detach.
Native ref counters return to baseline. ASan/UBSan PASS. This is the low-level
CANCEL pin-return path only: safe Main cancellation admission, COMPLETE RELEASE
composition, persistent terminal retries and endpoint routing remain required.

## Initial CANCEL Main preflight composed locally

`wr_iot_physical_initial_cancel_current` validates exact origin/lifetime, no
captured Main ticket, idle Main recovery without deferred/netdev owner, zero
active TX and the same current accepted idle probe/epoch/serial. It rechecks the
live Main registration generation/open token. Tests show CANCEL stops being
eligible immediately after Main stop ticket admission, even before the initial
record moves to RUNNING. Active TX/deferred recovery refuse too.

The native pin publication fixture now executes this preflight under its
transition-lock actor, then separately detaches under its MacTab actor while
retaining outer lifetime/RTNL. Actual native drop balances references outside
locks. Publication and actual completion fixtures PASS ASan/UBSan. A production
terminal wrapper and durable PID-reference reply cache are still required to
make the whole preflight/detach/drop/lifetime-end sequence an installed API.

## Initial terminal PID-reference cache composed for CANCEL locally

`physical-initial-terminal.inc` prepares a separate PID-reference cache using
get_pid(task_pid(current)). It cannot reply until commit inspects exact record,
request identity, returned pin slots and ended matching Main lifetime. No caller
completion booleans substitute for those structures. CANCEL requires detached
ARMED/no completion epoch; RELEASE requires detached COMPLETE/advanced epoch.
Exact repeated reply is read-only and checks current PID-reference identity;
cache clear drops the PID reference outside locks once.

Composed CANCEL fixture executes actual native acquire, ARM publication, cancel
preflight, exact pin detach, native3ref drop, actual lifetime end then terminal
commit. Commit/reply refuse before references return and again before lifetime
end. Repeated exact response performs no extra puts; foreign PID/nonce refuses,
commit/clear occur once. Kernel ref primitives remain injected. ASan/UBSan PASS.
RELEASE cleanup composition and an installed serialized terminal wrapper still
need verification; this cache is not an endpoint or physical acceptance.

## Checked COMPLETE to native RELEASE and PID replay composed locally

`check-physical-initial-release.py` extends actual Main lifecycle/completion and
terminal composition. Native pins_acquire obtains the test RELEASE bundle via
injected kernel reference primitives. It refuses detach while RUNNING, then
uses actual initial pin detach after checked COMPLETE, returns all3 references
outside locks and ends the same actual Main lifetime. Terminal commit refuses
both before native drop and before lifetime end. Three RELEASED replies leave
reference counts unchanged; clearing the PID cache returns its single reference.
ASan/UBSan PASS. This verifies helper ordering in a composed host fixture, not an
installed serialized driver terminal wrapper, physical RF retirement or runtime.
The next implementation must place this sequence in that wrapper, preserve
partial cleanup state across refusal and route only after adapter preparation.
