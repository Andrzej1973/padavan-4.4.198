# Cold DOWN RC integration boundary

The cold path means ra2 was pre-created but never opened, while Main has a
completed close ticket. It is distinct from an IoT-owned physical RELEASE.
Fresh never-started Main is a separate case and is not covered by this proof.

## Implemented observation

`tools/iot/precreated-down-observe.c` requires active admission, a borrowed
configuration guard, saved initial-OFF policy, absent br-iot, BSS DOWN, no DNS
recovery and Main DOWN. Two typed driver reads must agree on adapter epoch,
ra2 generation and completed Main close serial. `wr_iot_initial_down_current`
repeats this observation and compares all three fields with a captured baseline.
Neither function changes driver state, generates a ticket or grants a future
reopen lease. The caller must retain its exclusion and object lifetime contract.

## Private cold admission implemented

`cold-on-admission.c` now captures a distinct typed DOWN baseline and the actual
read-only radio profile under the existing service guard and signal fence.
Historical RELEASE excludes this path. Repeated current checks surround profile
capture. A claimed refusal retains the fence/context until explicit cancellation;
cancellation frees capture only, preserves foreign file changes and runs before
pending shutdown replay. Failed signal-mask restoration retains ownership.
The component is staged for compilation but is not routed from public RC entry.

## Private cold profile generation implemented

`cold-on-generation.c` exclusively borrows cold admission, retaining its guard,
profile and signal fence. Fresh DOWN provenance precedes generation and restore.
Reload calls the existing generator at most once; actual journal/scanner checks
select VERIFIED or retain/restore the captured baseline. Foreign inode changes
refuse restore. Possible Main UP prohibits every generation/recovery operation.
Pending shutdown currently retains ownership; pending-aware recovery and checked
retirement remain to implement before public binding. Host tests exercise the
actual snapshot, scanner, journal, profile restore and cold admission/fence.

## Required integration, still incomplete

1. `radio-on-admission.c` currently requires `wr_iot_rc_radio_off_receipt` and
   stores a physical RELEASE. Cold admission must retain a distinct typed origin
   and fresh nonce under its own fence; it must refuse if historical ownership
   exists. Profile capture must be bounded by repeated current-DOWN checks.
2. `radio-on-generation.c` validates that same receipt before profile generation,
   rollback and Main UP. Cold provenance needs explicit checks before UP and
   separate rules after UP; a DOWN observer cannot succeed after Main UP.
3. `radio-on-main.c` and `radio-on-prehandoff.c` use
   `wr_iot_rebind_configuration_current`, comparing the new adapter epoch with
   RELEASE epoch. Cold startup needs an independently validated new Main READY
   and exact ra2 generation, without manufacturing CLOSE/RELEASE history.
4. `radio-on-handoff.c`, rebind-start/network/runner, shutdown checks and restore
   retain physical RELEASE identity. They need an explicit cold-origin path
   through success, pre-UP rollback, post-UP refusal and shutdown cleanup.
5. Only after those consumers are covered may `restart-entry.c` route cold ON
   into the new owner. Existing historical RELEASE routing must remain intact.

No generic weakening of RELEASE validation, native fallback after a claimed
cold admission, or use of DOWN snapshots as RF/DMA/IRQ drain evidence is valid.

## Verification

Actual observer and expected-identity revalidation pass host GCC Werror with
ASan/UBSan: changed epoch/generation/Main serial, zero fields, missing guard,
inactive or pending admission, policy/bridge/BSS/DNS/Main failure, first and
second transport-read failure. Prepared RC C11 objects compile. Full SDK target,
final image and physical WR1200JS acceptance remain separate outstanding gates.

## Main READY and recovery package staged

`cold-on-main.c` now uses the existing initial-IDLE driver probe to check new
Main READY/configuration and never-opened ra2 registration after one Main UP
attempt. Same ra2 generation and newer adapter epoch are required; repeated
observations must agree and their serial must advance. Possible submission
permanently prohibits old profile rollback, including NOT_SUBMITTED because a
foreign Main UP is possible. This is configuration evidence, not loaded-key/RF
acceptance. `cold-on-recovery.c` provides pending-aware pre-UP restore and checked
retirement; credentials/guard are released before shutdown replay. The earlier
non-pending generation recovery helper remains available, but pending recovery
uses the explicit pre-UP recovery component. No post-UP retirement is implemented.

These units and pending DOWN recovery are now staged for RC/ABI compilation,
with manifest `cold_on_entry_bound=false`. Full registered host suite on43b943dd
passed before adding these new tests; each new test and expanded prepared C11
unit compilation also passed separately. Public cold owner, Main LAN/Guest/
services restoration and initial startup handoff remain incomplete. The existing
initial `start-runner`/`start-admission` path already accepts never-opened READY
ra2; audit its backend handoff for reuse rather than synthesizing a physical
RELEASE or weakening physical-rebind validation.

## Cold Main LAN / Guest / services continuations staged

`cold-on-main.c` now performs at most one existing ra0/br0 attach attempt,
checking current membership and Main READY before/after. `cold-on-guest.c`
preserves the established bridge/isolation/UP order and configured Guest OFF.
Only a submitted Guest UP permits its own one-shot recovery DOWN; uncertain
foreign/no-submission state is retained. `cold-on-services.c` captures policy
and submits each of three existing service slots once; return does not prove
daemon readiness. `cold-on-multicast.c` preserves the existing captured policy,
ordered per-BSS attempts and readback. No global TX/ACK/DTIM mechanism changes.
All are staged for compilation; public cold entry remains disabled. Host tests
use actual cold parent/profile controllers with SDK transport actors, plus
policy/failure tests and prepared C11 object checks. Stable root, initial backend
handoff and post-UP shutdown/retirement remain required before binding.

## Stable cold owner staged through pre-OPEN boundary

`cold-on-owner.c` now owns stable admission/generation/Main/Guest/multicast/service
objects and advances one child phase per invocation. Validated control input is
kept only until generation capture; unused request credentials are wiped on
capture/refusal. Partial generation can recover before Main UP. Every submitted
operation retains its no-replay state and all guards on uncertainty. PREPARED
requires fresh parent/child pointer and readiness checks; it is not ACTIVE/DONE.
The root relies on active admission plus OFF exclusion until a future checked
parent release; it does not set or clear an unrelated ON exclusion. Public RC,
backend initial-start handoff, post-UP shutdown and root retirement are not bound.
Host integration tests use actual cold parent/profile controllers with injected
SDK boundary operations. Prepared RC C11 object compilation passed.

## Experimental RC initial-start binding staged

`rc-cold-start.inc` is inlined into prepared experimental rc-backend.c, keeping
its existing private backend/rebind objects. The helper accepts only exact cold
parent input/desired request and a fresh PREPARED check, then invokes the existing
initial start-runner once. The backend's captured IDLE identity must equal cold
Main identity; mismatch retains UNCERTAIN without progressing to OPEN. Old
INITIAL_OFF identity replay or time reversal refuses. Bound ACTIVE observation
requires the same stable parent, envelope, driver identity and existing full
activation owner observer; APPLIED alone does not suffice. These helpers are
compiled but have no cold-owner/public caller yet. Root lifetime, post-UP
shutdown/retirement and backend continuation handoff remain to connect/test.
Host binding fixture injects parent/start/ACTIVE adapters; prepared RC compilation
is separate evidence. Target and device verification are outstanding.

## Cold handoff and exact backend continuation staged

`cold-on-handoff.c` now retains a stable parent pointer and immutable envelope/
Main identity before its one backend begin attempt. Refusal cannot replay begin.
Continuation uses only the exact RC-bound START owner; APPLIED never substitutes
for the full ACTIVE observer. Fresh retained profile, Main LAN, Guest policy/
isolation/admin state, service policy/auth liveness, multicast and auxiliary DOWN
checks gate progress and ACTIVE observation without relying on post-OPEN IDLE.
The profile and outer admission/fence remain retained. Three private RC symbols
now have explicit optional link gates as well as prepared object compilation.
Host integration runs actual cold parent/profile and RC binding, injecting initial
start-runner and full ACTIVE observation; this is not device OPEN acceptance.
Public cold entry, post-UP shutdown/retirement, disabled-IoT release and final
WAN/IAPP completion remain incomplete before activation can be enabled.

## Cold release preparation staged

`cold-on-release.c` captures the current generated profile identity without file
bytes/credentials and captures the existing WAN followup plan. It revalidates the
full handoff ACTIVE before and after capture. Failed WAN policy or observation
retains the same context/profile/guard; retry does not recapture a completed WAN
intent. No WAN submission, parent binding removal, guard release or signal fence
cleanup occurs here. The current function may complete missing capture; it is
not a purely read-only observer. Actual cold-parent/handoff/profile fixture and
prepared C11 object compilation pass. RC binding release, signal-fenced cleanup,
post-UP shutdown and final WAN/IAPP followup remain required before public entry.

## Nonsecret post-release policy retained

`cold-on-policy.c/h` retains Guest enable/isolation, service enterprise/RSSI and
multicast policy by value. Release captures it before parent cleanup and validates
current policy before completion. The post-release full ACTIVE/profile observer
also verifies this policy under its fresh guard. No parent pointers, SSIDs or keys
are stored. Actual cleanup/followup tests refuse Guest/auth/multicast/RSSI drift;
all WAN plans still avoid replay after uncertain post-call observation. The new
unit is staged for RC/ABI/link compilation. Standalone detach/cleanup/signal/
followup/WAN tests are now registered in the full host suite. Runtime cleanup/
followup fragments remain uncomposed until LED/IAPP owner, retirement and post-UP
shutdown handling are complete. Target/image/device verification stays separate.

## Cold LED/IAPP terminal and retirement candidate

`rc-cold-terminal.inc` owns WAN, one LED attempt and one existing IAPP terminal
transaction at stable addresses. Unknown child completion drains that same
context; confirmed failure remains retained and never replays the command.
The default IAPP policy gate is inert; only paired prepared policy permits the
terminal begin. DONE requires a successful closed child, balanced terminal
fence/guard and a fresh full post-release ACTIVE/profile/policy observation.
Final retirement repeats this proof before wiping nonsecret release/terminal
contexts and clearing ON exclusion, preserving the independent ACTIVE backend.
The host test runs actual cold parent cleanup, WAN and IAPP terminal/fence with
SDK and child-result actors, both policy gates and final retirement. These
private fragments remain uncomposed; public entry, post-UP shutdown and disabled
IoT completion are still outstanding. Software checks do not certify RF/runtime.

## Private completion API composed into experimental RC

Prepared rc-backend now contains detach, parent cleanup, post-release policy/
ACTIVE/WAN observer and LED/IAPP terminal code. `rc-cold-completion.h` supplies
stable caller-owned context types; private exported wrappers expose release,
terminal begin/step/retire. Exact-source validation mirrors all named fragments.
The host preparation fixture now compiles the actual prepared backend in GNU11
and checks its four completion symbols with nm, using the real activation owner
header. Earlier fixture compilation covered individual RC units but omitted the
backend; that older evidence must not be read as backend compilation. Other
prepared units retain C11 Werror checks. Terminal integration uses the exported
wrappers with both policy gates; pending SIGTERM composition still passes.
No public cold entry or scheduler caller is enabled. Post-UP shutdown, disabled
completion and root integration remain before runtime activation.

## Disabled completion composed into experimental RC

The never-opened disabled branch now stages initial-OFF observation, release
preparation, inert INITIAL_OFF backend publication, post-release policy/profile
proof, all WAN plans and LED/IAPP terminal/retirement. Stable context types and
private wrappers live in `rc-cold-disabled-completion.h/inc`. Prepared backend
GNU11 Werror compilation, exact source verification and nm T symbols pass; the
disabled standalone units pass C11 compilation. Exported-wrapper integration
covers both IAPP gates, all WAN plans, LED/child failure and retirement; real
SIGTERM cleanup passes separately. Tests are registered in the host suite.
Current public/scheduler cold entry remains false; post-UP shutdown and root
integration still require implementation and target/image/device verification.
The completed host suite on c40e389a covered the prior enabled package and is
recorded independently from these newer disabled checks.

## Pending shutdown before initial backend handoff

`cold-on-prehandoff.c` verifies a retained cold owner after possible Main UP,
with pending SIGTERM/SIGQUIT, owned profile and exact parent chain. Guest must
already be administratively DOWN through its existing own-UP recovery. Two
initial-IDLE probes verify a newer READY adapter epoch, same never-opened ra2
registration and increasing serial; a captured Main identity must agree.
`rc-cold-prehandoff.inc` refuses any claimed initial backend/start/stop/rebind.
Both enabled and disabled intent fixtures pass with actual cold parents/profile/
Guest and backend predicate; driver/SDK transport remains injected. No Main UP,
profile rollback or cleanup occurs in this predicate. It is staged for compilation;
signal-fenced shutdown cleanup and post-handoff shutdown are still outstanding.

## Prehandoff shutdown cleanup staged

`cold-on-shutdown.c` checks stable parent/Main/generation/admission ownership and
an idle RC backend before allowing one existing own-Guest recovery step. The
pending prehandoff proof then gates outer signal-fence cleanup. Cleanup wipes
private profile bytes, desired credentials and child pointers; it releases the
guard and OFF exclusion while preserving the live fence token until fence_end.
The current generated profile file remains unchanged; Main is neither reopened
nor rolled back. Real queued SIGTERM runs after successful cleanup; failed unmask
retains the root/profile/guard for exact-context retry. Both intent fixtures and
prepared compilation pass. This private function is staged but no public root
shutdown caller is bound. Shutdown after initial backend handoff still requires
its own exact CLOSED or completed pre-OPEN rejection path.

## Post-handoff shutdown exact CLOSE observer staged

`rc-cold-shutdown.inc` observes only the same bound cold initial backend and
completed owned OFF under pending normal shutdown. It matches original ON and
fresh OFF envelope, adapter/ra2 identity, open token and close serial against the
existing backend's full CLOSE observer and retained stop controller. OFF resume
flags or desired credentials, ACTIVE/rebind/foreign owners and stale tuples
refuse with zero output. The prior startup profile is not compared/restored after
normal OFF's owned profile change. Focused predicate fixture uses an existing
CLOSED-observer actor; prepared backend compilation and nm symbol checks pass.
No shutdown controller, pre-OPEN rejection alternative or cleanup is bound yet.

## Distinct pre-OPEN rejection observer staged

`wr_iot_rc_cold_shutdown_rejected` requires the same bound cold ON identity and
completed initial backend REJECTED state under pending shutdown. If settings
mutation started, rollback must be DONE with no active snapshot/token. OPEN must
be IDLE or NOT_SUBMITTED with no identity/request nonce left, and no CLOSE/stop
owner exists. Two fresh READY initial-IDLE responses, absent IoT bridge, temporary
OFF gates and no DNS recovery confirm the never-opened state. This returns only
a rejection proof; it never fabricates an OPEN token or CLOSE serial. Host
predicate tests and prepared backend/symbol checks pass. Actual shutdown
controller/cleanup composition and driver-level runtime evidence remain required.

## Post-handoff shutdown controller staged

`cold-on-postshutdown.c` owns a stable cold parent/handoff and fresh OFF envelope.
It drains only the existing own-Guest UP, advances the bound initial startup via
RC helper, then accepts completed pre-OPEN rejection or starts existing normal
OFF at most once. A refusal after that attempt retains context; no repeated
begin is permitted. DRAIN uses existing quiesce continuation plus exact CLOSE
observer; terminal states require fresh proof on every call. No Main reset,
old-profile rollback or cleanup occurs. RC helpers independently validate the
pending parent/ON/radio binding before startup continuation or OFF admission.
Controller tests use backend/quiesce/Guest actors; RC predicate/wrapper tests are
separate. Prepared backend and component compilation/symbol checks pass. Exact
shutdown cleanup and root/public wiring are still required.

## Post-handoff shutdown cleanup composed

`rc-cold-shutdown-release.inc` requires terminal cold shutdown state, retained
parent/generation/profile ownership and Guest DOWN, then repeats the exact
backend CLOSE or distinct pre-OPEN rejection proof. Successful outer-fence
cleanup detaches the borrowed backend parent, wipes cold profile bytes/desired
credentials/handoff/stop context and releases guard/OFF exclusion before pending
signal replay. Live parent fence token is preserved until fence_end completes.
Backend completed OFF/REJECTED state remains intact. No old profile comparison
or restore occurs after normal OFF's owned profile mutation. Host composition
uses actual cold parent/profile/handoff/predicates and real SIGTERM/fence with a
full-CLOSE observer actor; failed unmask retains all resources and current OFF
profile identity remains unchanged. Prepared backend and symbol checks pass.
Public root shutdown scheduling remains unbound and target/device gates remain.

## Stable cold root normal completion candidate

`cold-on-root.[ch]` now retains the cold owner, initial backend handoff,
nonsecret release and terminal continuation at stable addresses for both saved
IoT ON and OFF intent. Each step invokes one existing child continuation.
Admission or backend refusal remains owned; it never selects native fallback.
An OFF observer claimed by a failed fresh begin observation is polled through
`current`, never begun twice. Release wrappers repeat their own full proof;
terminal DONE is re-observed and retirement repeats its current proof before
wiping the root. The independent ACTIVE/INITIAL_OFF backend remains owned by RC.

The controller fixture checks both intents with injected child actors, including
capture/release refusal, pending signal drain in the existing terminal child,
and failed retirement retaining the exact root. This is host controller evidence,
not composed driver, MIPS image or physical evidence. Scheduler/public entry,
pre-UP recovery and root shutdown routing are still unbound. In particular,
pending shutdown before terminal continuation retains the root until its exact
pre/post-handoff cleanup can be composed; do not install this normal-only root
as a replacement for the running startup path.

## Cold root post-UP shutdown routing staged

`cold-on-root-shutdown.c` routes pending normal shutdown before parent release:
never-opened ON/OFF intent uses the existing exact prehandoff cleanup; a bound
ON backend uses one fresh OFF envelope, then the same retained stop controller
and exact CLOSED/rejected release. A changed OFF argument after stop ownership
cannot replace the original stop. Failed cleanup retains the root unchanged;
root metadata is wiped only after child cleanup has released credentials and
guard inside the existing signal fence. No Main reset or old-profile rollback.

Both root units/headers and tests are now registered in runtime preparation,
source equality checks, host compile checks, target ABI compilation and target
symbol verification. The root shutdown routing fixture uses child actors;
existing child fixtures exercise actual cleanup/signal fences separately.
Pre-UP recovery, fresh OFF generation and scheduler/public root routing remain
unbound, including post-parent-release root shutdown routing. Compile staging
is not installation or target/runtime acceptance.

The prior full-suite run stopped at the 60-second external budget for
`check-physical-terminal-down.py`. The unchanged test then passed standalone
in 52.78 seconds. It executes nested RELEASE fixtures like handler, so the
suite now grants this check the same bounded 120-second budget as handler.
This changes the host test budget only; the stopped suite is not marked PASS.
