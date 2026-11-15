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
