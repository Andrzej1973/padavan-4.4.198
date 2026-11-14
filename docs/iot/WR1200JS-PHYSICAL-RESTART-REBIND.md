# Physical restart: identity handoff still required

Status: old completion identity capture implemented locally; new-identity
handoff/resume still required. No production or physical runtime acceptance.
This concerns physical restart after a prior IoT OPEN, not ordinary ra2 toggles.

Source findings verified on 2026-11-14:

- `radio-transition.h`, `wr_iot_radio_begin`: START, AUX_START, MAIN_OPEN and
  RESET increment epoch, even if the netdevice address survives.
- `reopen-admission.c`, `wr_iot_reopen_witness_current`: the current CLOSE must
  match the saved epoch, generation, OPEN token and CLOSE serial exactly.
  This witness deliberately cannot authorize OPEN after epoch replacement.
- `precreated-idle-reference.h`, `wr_iot_precreated_idle_reference`: initial
  admission rejects prior `last_token` and CLOSE history. Advancing radio epoch
  does not erase that history or turn a prior OPEN into initial idle.
- `physical-stop-lifetime.h`, `wr_iot_physical_stop_lifetime_end`: ending the
  completed lifetime clears Main identity and ticket validity in that context.
- `physical-stop-terminal-types.h`: terminal cache now includes a pointer-free
  old Main completion origin. `physical-stop-release.inc` captures it from a
  freshly revalidated actual Main release under the transition lock before
  lifetime end. New-identity mapping is still absent; RELEASED is a cleanup
  receipt, not a resume authorization. Snapshot `valid` alone is insufficient:
  terminal ready/RELEASED and exact PID/request are also mandatory.
- `rc-quiesce.h`: desired settings survive normal OFF in a private RC context.
  They are user intent, not a driver identity or loaded-key receipt.

Therefore neither stale CLOSE reuse nor initial-idle fallback can implement
physical restart resume. Do not clear registry history to make initial admission
pass. The restart guard remains held in the staged controller until its verified
consumer is implemented. The existing MCU ACK and shared TX ownership remain
unchanged.

Next implementation sequence:

1. Implemented locally: before physical lifetime end, retain a bounded kernel-derived completion
   identity for the exact old Main ticket/registration and old IoT CLOSE.
   Keep it outside released task/module/netdev ownership. Preserve existing
   disjoint lock ordering and terminal retry behavior; no naked stale pointers.
2. Bind a Linux-only handoff to the actual issuing PID and original nonce /
   physical attempt. CANCELLED cannot serve as a physical completion receipt.
3. After the existing checked Main startup, validate its fresh READY epoch,
   current Main and ra2 registrations, idle executor, completed old recovery and
   closed IoT state. An unchanged address alone is insufficient.
4. Issue a narrowly scoped old-to-new handoff receipt from those actual facts.
   Define single-use OPEN admission, lost-response recovery, generation/epoch
   drift rejection and adapter retirement before installing its transport.
5. Bind the fresh receipt to RC startup/resume while retaining desired settings
   and service/shutdown guards. Release guards only after the captured intent
   and its resume outcome have been handled. STOP/CANCEL recovery stays distinct.

This is a driver/RC Linux API task using available SDK source. It does not
require changing firmware protocol or obtaining proprietary ROM documentation.
A host fixture cannot certify RF/DMA/IRQ or late TxS retirement.

Regression evidence:

- Actual RC backend/owner quiesce fixture rejects a changed driver epoch with
  cleared output while retaining desired settings and resume ownership.
- The initial-reference fixture has26 cases, including radio epoch advancement
  with prior OPEN and prior CLOSE history. Both remain rejected, without state
  mutation. This fixture is already run by the optional merged-candidate job.
- Both passed strict O2 ASan/UBSan locally. Target and device checks remain open.

Local same-registration Main readiness predicate now compares the old origin
with actual last_release and requires READY/Main-ready, newer epoch and retired
radio serial, no active worker release/reset/PM/TX, same published Main device
and generation, and a strictly newer OPEN token. Native tests cover18 rejection
cases in addition to14 old-origin mismatches. This predicate is not yet called
by a new transport/admission path; it is not ra2 or RF readiness. Replacement
registrations are deliberately unsupported by this predicate and need their own
verified mapping rather than address-based acceptance.

Local ra2 historical identity predicate now requires the original RELEASE tuple
and exact published MBSS device/generation/OPEN token/CLOSE serial/old epoch,
IDLE with completed close stage4 and no removal/uncertain/running/unmutated-open
state. Twelve refusal cases pass with the same strict native sanitizer build as
the18 Main readiness and14 old-origin tests. This is historical identity only:
it does not replace current-epoch beacon/key/probe checks, exact terminal issuer
or single-use OPEN admission. Both new predicates remain unbound to transport.

The local paired preflight now requires a ready RELEASED terminal cache, its
valid original RELEASE request, exact old origin, new Main readiness, exact
ra2 history and actual registry/vendor count agreement. Fifty-two negative
native cases pass. The preflight checks that PID storage exists; the predicate now compares the exact retained PID identity and every original
RELEASE field/nonce. The binding must supply actual task_pid(current), never
a PID pointer selected from request data, under the correct serialization. No transport calls this predicate yet. Existing CLOSED probe
requires `close_epoch == radio.epoch`; the old epoch is deliberately preserved,
so that probe must not be reused by rewriting history. A distinct admitted
current-epoch configuration observation is still needed before rebind/OPEN.

Exact issuer/request correlation now rejects foreign PID identity, changed
attempt, epoch, generation, OPEN token, CLOSE serial, nonce and CANCEL action.
There are60 negative cases across origin/Main/ra2/terminal/request tests. This
remains a preflight without transport or current configuration observation; the
new caller must pin adapter/netdevices and provide actual kernel PID identity.

Local `physical-rebind-probe.h` adds begin/finish around existing BSS_OBSERVE
admission. Begin requires exact paired identity and snapshots the new Main
generation/token. Finish retires only its own ticket, then requires unchanged
epoch, successful configuration observation and a fresh paired identity/count
check. Epoch/Main token/ra2 identity drift and failed readback reject without
rewriting old CLOSE history. Failed ticket retirement retains the active probe.
Native sanitizer tests use injected readback and exercise real radio ticket
functions. This API-only header is not installed into the vendor candidate yet;
it must be bound to the existing BcnRing-protected actual configuration observer
with pinned lifetime before any transport or OPEN permission is exposed.

Probe identity is now retained across unlocked readback: actual issuer pointer,
Main/IoT devices and original RELEASE tuple/nonce are copied at begin and
required at finish. Even a newly valid replacement terminal cache with another
nonce/attempt cannot complete the previous probe. Caller-held lifetime pins
remain mandatory; these copied pointers do not acquire references. Seven
observation outcomes, including terminal replacement, pass strict sanitizer
checks. Next persistent storage/teardown fencing and actual observer binding
remain required before installing this header into the candidate driver.

Probe storage is now staged in the isolated candidate adapter and zeroed only
at fresh allocation, before publication. Both recovery retirement gates and
raw-free fencing reject an active rebind probe. Raw-free test verifies no
terminal PID return while the probe is active. The types-only header is copied
and hashed by both physical-stop installers. The observation functions and
actual configuration readback are still not bound into a callable endpoint.
No live probe may be discarded to bypass a failed ticket retirement.

The accepted probe now supports a one-use host handoff claim for a nonzero future
OPEN request ID. Claim revalidates exact issuer/devices/original RELEASE and
paired identities, plus the exact current observation epoch/serial/retired serial
and Main generation/token. It copies the ID, clears accepted and marks spent.
Duplicate claim and reprobe of the same physical transaction refuse. A later
valid different terminal transaction can start a fresh observation. This helper
does not invoke OPEN or prove loaded keys. Final OPEN admission must claim under
the same transition lock and retain the claimed ID for uncertain OPEN recovery;
it must not reset spent merely because a call failed. That binding is pending.

`physical-rebind-open.h` locally composes claim and the existing actual
`wr_iot_driver_owner_reserve` under one caller-held transition lock. OPEN query
identity, new epoch/generation and control state are checked before claim.
Existing owner logic still reserves its own BSS_OPEN/registry token; credentials
and mutation policy are unchanged. Native sanitizer tests execute real owner
reserve/leave: conflict refuses without spending; accepted reserve produces one
ticket; duplicate refuses; pre-mutation leave clears owner but never refunds the
handoff. The helper is not installed/routed yet. Recovery after spent admission
and actual RC/API routing remain required before activation.

The internal `wr_iot_physical_rebind_request_enter` now supplies actual
`current`/`task_pid(current)` and performs claim plus existing owner reserve
under one transition critical section. It rejects active CLOSE/physical
lifetime, boot/control poison, foreign BSS and missing RTNL. The isolated
installer stages the open helper. Actual binding tests exercise reserve,
control conflict, duplicate and existing pre-mutation owner_leave. No external
ioctl route calls it yet; capability-checked transport, dev_open/first-beacon/
leave orchestration, uncertain recovery and RC resume remain pending.

Internal `physical-rebind-open-entry.inc` now composes rebind request_enter,
existing dev_open, existing first-beacon wait and mandatory request_leave.
Admission failure never calls dev_open/leave; any accepted admission leaves
after dev_open error or beacon timeout; failed leave overrides with EUCLEAN.
A private credential copy is wiped and caller input remains untouched. The
outer transport must still capability-check/decode both requests and retain
RTNL/module/adapter/netdevice lifetime. No external route is installed. Native
execution test injects lifecycle actors and covers these error paths; actual
owner reservation and observer are tested separately. Target/runtime pending.

Local Linux-only envelope `physical-rebind-wire.h`: WRRB/version1, operation
byte5 (1 observe,2 OPEN), reserved bytes6–7 zero. Original64-byte RELEASE starts
at8; optional144-byte existing OPEN starts at72. Exact total lengths72/216.
OPEN syntax additionally requires newer epoch and same registration generation.
No native pointers/padding or firmware changes. This is syntax only, no copied
identity is trusted without actual kernel admission. Native sanitizer/target
declaration-warning test covers truncation/header/stale tuple and wipe. No
wrapper/dispatch installed yet. The future wrapper must check capability before
reading either request and independently validate its own bounded copy.

`physical-rebind-ioctl.inc` now independently checks RTNL, namespace capability,
MT7603 and exact ra2 before userspace reads. It copies8-byte header, selects
constant72/216 length, copies whole request and compares the header before strict
decode. Copies/credential-bearing request are wiped on return. Handler executes
once without automatic retry; original errors remain visible. Native wrapper
fixture covers both copy faults, header race, foreign BSS and exact dispatch.
Installer stages it after execution helpers, but no ioctl discriminator routes
WRRB yet. Userspace transport/uncertain recovery and RC resume are pending.
