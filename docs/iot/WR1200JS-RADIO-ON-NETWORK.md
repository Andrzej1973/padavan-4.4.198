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
entry. Cold/IoT-OFF and failure/shutdown recovery plus stock entry binding remain to
integrate; private root retirement and follow-up are described below.
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
cold/IoT-OFF handling and stock entry binding remain unfinished.

## Parent release after ACTIVE, before WAN/IAPP

`radio-on-release.c` performs read-only preflight for the exact private ACTIVE
rebind, current profile generation and credentials, Main bridge, Guest state
and isolation, multicast and all submitted service slots. It also checks copied
service policy and process-name auth liveness (not authentication acceptance),
plus a captured, still-current WAN plan.

`radio-on-release-runtime.h` is included only in RC runtime, beside the retained
OFF receipt. It preflights before consuming that exact receipt. Release uses the
original outer signal fence and service guard. Failed mask restore leaves the
profile, receipt, context and guards intact. Same-context retry is local and
checks the retained receipt again. Once mask restoration succeeds, bounded
cleanup wipes credentials and historical receipt, releases the baseline/guard
and clears child ownership pointers before pending SIGTERM is replayed. Status
is RELEASED, not DONE. The captured WAN plan survives and may execute once only
after admission/guard release. No public entry or scheduler is activated here.

Host C11-Werror ASan/UBSan composition passed actual preflight, journal/profile,
RC-owned cleanup and signal fence: auth/WAN/service refusal, no backend progress
from preflight, failed unmask retention, successful retry, credential/receipt
clearing before a real deferred SIGTERM, and one WAN call only after release.
RC wait, OFF-consumer and scheduler regression fixtures passed; prepared separate
translation units passed. Backend, SDK and WAN boundaries are injected. Target
and device acceptance remain distinct. Post-UP failure/shutdown recovery and public OFF/ON entry binding remain
required; private scheduling and follow-up are described below.

## Post-release WAN and terminal IAPP

`radio-on-followup.c` advances RELEASED -> WAN -> IAPP_PENDING -> IAPP -> DONE.
WAN executes the captured plan once only after parent release. A fresh exact
backend resource observation must follow WAN before one LED call or IAPP.
Missing network proof retains WAN without resubmitting it. LED uncertainty is
retained without replay. The default IAPP gate stops at IAPP_PENDING; the paired
installer enables the existing terminal IAPP controller and its one-shot child.
An unknown child result keeps its service guard/fence and drains only that
child. Confirmed failure is retained, while success plus fresh network evidence
permits software DONE. Later DONE reads still require current network proof.

Host C11-Werror ASan/UBSan checks use actual parent release, receipt cleanup,
WAN helper, terminal controller and signal fence with injected SDK/backend/child
boundaries. They cover post-WAN network loss, no WAN/LED/script replay, inert
default gate, paired success, child failure and unknown-result draining. ABI
includes both default and paired-gate MIPS compilation for the new follow-up.
Prepared separate translation units compile; target/image/device acceptance is
still pending. Stock entry binding, cold-OFF handling and post-UP failure/shutdown recovery
remain required before enabling public OFF/ON.

## Stable private RC ON owner and public exclusion

`radio-on-owner.c` keeps admission and all children at stable addresses. Its
private begin validates bounded credentials/subnet and nonzero request nonce
before taking the outer fence. One phase/tick advances restore, exact handoff,
ACTIVE observation, parent release and WAN/IAPP. Input credentials are dropped
after generation captures them. A separate process-only `radio_on_owned` survives
parent release and shutdown_end; public dispatch refuses before mailbox claim,
direct activation refuses before mode/resources, and private OFF admission is
also excluded. Private rebind/terminal continuation remains possible.

RC ppoll prioritizes OFF then ON ownership before deferred dispatch, physical
restart, prior restart scheduler or ordinary continuation. Failed retirement
keeps exclusion. Software DONE retirement requires closed children, no profile
buffers/guards/pointers, cleared desired/input copies, consumed OFF receipt and
fresh owned network/parent proof. Only then is the root wiped and ON exclusion
cleared; one later tick attempts deferred mailbox dispatch.

Explicit reload1 admission permits a nonempty older profile baseline under
fresh physical DOWN and exact file identity. It does not require old bytes to
match newly saved SSID/key before generation. One SDK generation must then
match the desired/saved profile before Main UP. reload0 keeps strict prechecks;
failed post-generation validation restores the captured baseline. Host tests
cover actual old IoT -> newly saved IoT-new profile generation and mismatch
rollback without loosening DOWN/new-Main identity checks.

After parent release a metadata-only profile receipt (including nanosecond
mtime/ctime) survives without profile bytes/keys. Post-WAN/IAPP observations hold
a service guard and recheck that receipt, live Main/LAN and AUX, Guest policy/
bridge/isolation, multicast policy/readbacks and service policy/auth liveness
alongside the exact IoT backend. Lost Guest isolation or profile drift cannot be
hidden by a still-ACTIVE IoT backend. These are software observations, not RF or
daemon authentication acceptance.

C11-Werror ASan/UBSan actual root/mode/profile/release/WAN/terminal composition
passes success and retained failure, no request/UP/WAN/script replay, validation,
ON exclusion through parent release, fresh retirement and consumed-receipt reuse
refusal. Actual RC ppoll with a root boundary actor proves priority, cadence,
failed retirement and later redispatch. Actual mailbox/backend composition
proves both ON guards and preservation across shutdown_end. Existing OFF,
scheduler/autostart and prepared separate-unit checks pass. Child failure and
pre-UP failure retain ownership; complete pre/post-UP failure/shutdown cleanup,
cold/IoT-OFF admission and stock/UI entry binding remain unfinished. Only private
root progress is bound; no public OFF/ON activation or device acceptance.

## Pending-shutdown pre-UP profile recovery

The dedicated recovery DOWN observer accepts active admission with a pending
normal shutdown, while preserving exact RELEASE/QUERY matching, Main DOWN,
stable ifindex and service ownership. Normal OFF/resume observers still reject
pending shutdown. `wr_iot_on_generation_recover` independently forbids any
possible Main UP, never generates a profile, and restores only the owned
journalled baseline. Foreign or uncertain file ownership remains retained.
The restore controller invokes this path on pending shutdown before Main UP.
Baseline and guards remain retained afterward: RAM rollback and final cancelled
retirement are still required. This is not post-UP teardown permission.

Focused host observer, actual journal/profile generation, full ON owner,
restore composition and prepared-unit checks cover this addition. Tests verify
pending recovery, UP/stale refusal, no generator replay, no recovery after
main_may_have_started, and retained ownership. No target/device claim.

## Pre-UP RAM OFF rollback

After pending-shutdown profile recovery returns restored, the restore controller
records one rollback-state attempt and calls the fixed SDK RAM adapter. It
requires guard, router mode0 and exact recovery DOWN before and after
`mlme_state_rt(0)` plus readback of `mlme_radio_rt`. It does not alter saved
radio_x, rewind the consumable reload event, commit flash or issue radio UP.
Failed write/readback or post-call drift retains uncertainty without replay.
The profile baseline and fences still remain held: cancelled final retirement
has not yet been implemented. No post-UP recovery is authorized by this path.

Host C11-Werror ASan/UBSan constructed SDK helper check, actual restore pending
composition, full ON-owner/release regression and prepared separate-unit checks
passed. Pending pre-UP recovery calls rollback once, never Main UP, and keeps
baseline/ownership. SDK and DOWN boundaries are injected; target/device status
remains unverified. TemporaryDirectory scratch removed after checks.

## Verified cancelled pre-UP retirement

The ON root now handles pending shutdown after generation admission and before
any possible Main UP: profile recovery, one RAM OFF rollback, then read-only
RAM/DOWN/receipt/file checks. The cancellation finish requires no Main/Guest/
service/multicast/WAN/IAPP child ownership. Failed mask restoration retains the
whole root. Successful outer fence cleanup volatile-wipes profile buffers and
root credentials, clears process exclusions and releases the guard before
pending shutdown replay. It preserves the historical OFF receipt. Step returns
-1 only after that cancelled root has been released; this is not ON success.

Actual root C11-Werror ASan/UBSan fixture passes cancellation both before and
after generation, baseline byte restoration, one RAM call, failed unmask retry,
zero Main UP and real SIGTERM delivery after cleanup. SDK read-only rollback
fixture separately verifies no setter on current-state checks. Normal root and
prepared separate-unit checks pass. Public OFF/ON remains unbound; cancellation
before generation admission, RAM failure uncertainty, post-UP shutdown/failure,
cold/IoT-OFF paths and physical runtime acceptance remain to complete.
