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

The isolated no-host installer now routes exact WRRB magic from existing
CLOSED_CONFIG after its original privilege checks and bounded initial copy.
The wrapper independently repeats authorization and its own full payload copy.
WPSQ remains routed as before; unknown/reply magic falls through. Source
transformer rejects missing guards/prerequisite or duplicate application.
Metadata explicitly reports the rebind endpoint installed in the experimental
candidate only, with production_installed=false. Native route and installer
checks pass; userspace client and uncertain-result recovery still pending.

Fixed-ra2 userspace client now sends the existing CLOSED_CONFIG ioctl once via
CLOEXEC socket. Invalid syntax/socket acquisition is NOT_SUBMITTED; attempted
ioctl or close failure is UNCERTAIN; zero return is IOCTL_RETURNED only. It
never retries OPEN and wipes its wire buffer on every path, preserving caller
input. Runtime preparer links the client in experimental RC and target link
checks its symbol. The RC scheduler does not call it yet. Exact OPEN identity
receipt/recovery remains required before guard release or resume acceptance.

Experimental RC `physical-rebind-controller.c` retains only nonsecret OPEN
attempt identity and same-PID ownership after one rebind ioctl. Guard failure
refuses before submission. A possible submission cannot be replayed. Current
receipt reads require exact epoch/generation/token; recovery-only reads retain
phase and never certify ON or release admission. The controller is linked into
experimental runtime but is not invoked by the restart scheduler. Network
policy, desired configuration handoff and device verification remain external.

Rebind OPEN reservation now rejects a request ID equal to any retained prior
OPEN receipt, refusal or uncertain request ID before consuming the handoff.
Fresh ID remains mandatory even after radio epoch changes. Native sanitizer
fixture covers all three reuse sources with unspent claim/idle owner, followed
by successful fresh reservation; actual vendor binding fixture also passes.
This does not reset or erase prior evidence to obtain admission.

RC configuration helper now requires identity-before, one WRRB observation and
identity-after under retained shutdown/service guards, using the same future
OPEN nonce. Both reads require newer epoch and same registration; drift or
uncertain ioctl clears output. It does not submit OPEN or grant a lease across
network changes. The future staging/network steps must re-observe before OPEN
and retain recovery/isolation if any observation fails.

Local `rebind-start.c` provides separate new-epoch staging admission. It takes
a normal existing request snapshot between two fresh rebind observations,
retaining snapshot ownership if read-only cleanup fails. Stage revalidates
identity before and after the existing guarded writer, marks possible mutation
before calling it, and never repeats a mutated stage. Failed writes/drift retain
the baseline and service guard for recovery. Normal initial-idle and same-epoch
reopen functions are unchanged. Network steps, rollback/commit and actual RC
scheduler still need binding; this helper is not installed or activated yet.
Native fixture injects observation/snapshot/writer actors; target/runtime pending.

Local `rebind-network.c` preserves the existing seven operations: bridge,
quarantine, attachment, bridge UP, network-enable, DNS preparation and policy.
It uses retained rebind admission and fresh new-epoch observations around each
resource mutation. Failures keep attempted bits/snapshot and enter RECOVERY,
without replay or implicit rollback. Native tests execute actual sequencer and
request matcher/gate writer with resource/readback adapters injected, including
post-operation epoch drift. These sources are not runtime-installed yet;
rollback, commit and actual RC orchestration must be bound before activation.

Local `rebind-rollback.c` handles only pre-OPEN network recovery. It rejects
possible submitted OPEN and even nonempty attempt metadata in IDLE. Existing
bridge/DNS/settings rollback is reused with fresh new-epoch configuration
observation before every phase. Snapshot/guard survive failed restore or foreign
baseline; pending normal shutdown is not released by this function. Actual
snapshot composition tests cover partial retries and all9 baseline changes,
with external resources/readback injected. Post-OPEN CLOSE rollback and commit
are still required before RC/runtime installation.

Local `rebind-commit.c` requires CURRENT rebind OPEN with exact retained ID and
new epoch/generation, plus a fresh current-token query and existing network/
firewall/staged-settings observations. DNS commit is attempted once; uncertainty
retains context and cannot replay commit. Snapshot suspend occurs only after
DNS committed and observations pass. Native test covers recovery-only rejection,
seven existing fault cases, pending shutdown and nonce mismatch, with actors
injected. Runtime/runner integration and post-OPEN CLOSE rollback are pending.

Experimental runtime preparation now links rebind staging/network/rollback/
commit objects and requires their strong symbols during target RC-link checks.
Ten actual prepared translation units compile under strict native C11. Full46
host suite passed; target linking and physical behavior remain pending. Metadata
reports helpers linked while restart_resume_bound remains false. Composition
with the retained restart owner, post-OPEN CLOSE recovery and scheduler is still
required; mere linkage does not enable resume.

### Post-OPEN recovery helpers — 2026-11-14

`rebind-close.c` retains the new-epoch OPEN attempt and uses the existing CLOSE
controller for submission/progress/owner release. Exact retained physical
RELEASE, newer epoch, matching generation/OPEN ID, PID, snapshot and service
guards are required. Fresh CLOSED serial is pinned and revalidated; an uncertain
reply cannot authorize network teardown or a new OPEN.

`rebind-closed-rollback.c` applies existing bridge/DNS/settings cleanup only
after this CLOSE owner release. It rechecks the same serial and ra2 DOWN before
every phase; failure retains the snapshot and phase. Caller must serialize DNS
commit: startup rollback is for the pre-commit path. After DNS commit has been
attempted, the future runner must retain uncertainty or complete normal OFF
before entering settings cleanup. These helpers do not implement that runner.

Both helpers are linked into experimental runtime preparation with strong
symbol gates. Full48 host suite passed before the linkage edit; the changed
runtime preparer separately passed12 native translation units afterward.
Transport/resources are injected; no MIPS or physical-runtime claim. Restart
entrypoint orchestration remains false. Scratch test trees auto-removed.

### Retained resume runner — 2026-11-14

`rebind-runner.c` composes new-epoch admission/staging/network preparation,
exact one-use OPEN, fresh CURRENT, commit, pre-OPEN rollback and post-OPEN CLOSE
rollback. It validates and copies the ON request and retains ID/created and
contexts across bounded step calls; foreign continuations and busy callers do
not progress it. OPEN includes existing bridge/address/services/firewall and
staged-settings checks, with fresh physical rebind observation. The transient
credential envelope is wiped after submission. A successful ioctl alone does
not authorize COMMIT. No old CLOSE epoch is rewritten.

DNS commit uncertainty retains recovery ownership without replay. Failure
before commit uses explicit CLOSE then startup rollback; confirmed commit
failure uses existing normal OFF before restoring the startup baseline. The
caller must retain the outer physical restart guards throughout. Native
failure-injected tests cover success/13 faults and actual runner -> CLOSE
controller -> closed rollback composition. Normal OFF component behavior is
separately checked by its existing tests; this runner test injects that adapter.
Experimental runtime linkage and13 prepared native TUs pass. Full target and
physical verification remain required; RC scheduler/physical restart entrypoints
are still unbound. Next integrate ACTIVE quiesce/desired retention, exact
physical RELEASE transfer, checked Main startup and the retained resume owner.

### Physical owner now retains ACTIVE quiesce — 2026-11-14

Private `wr_iot_rc_physical_begin_quiesce` takes an explicit fresh OFF envelope,
then acquires the physical fence/service guard and delegates to existing RC
quiesce. Entropy failure precedes OFF admission. Each physical step performs
at most one OFF continuation; no AUX shutdown, ARM or Main DOWN occurs until
quiesce yields the exact released CLOSE. Desired ON settings remain in the
retained private context after normal OFF wipes the previous ON runner.

`wr_iot_rc_physical_resume_read` returns a private pointer-free copy of desired
settings and the acknowledged physical RELEASE tuple while retaining all
guards/intent. The session retains QUERY as its base identity even at COMPLETE;
only the terminal action is reconstructed as RELEASE. Epoch/generation/token/
CLOSE serial/attempt/nonce remain unchanged. Output is cleared on refusal;
credentials must never be sent to telemetry and must be wiped after use.

Actual backend -> normal OFF -> physical session/fence composition passes with
external driver/resources injected. Existing STOP/restart fence regression and
prepared runtime compilation also pass. Stock restart routing, checked Main
startup and rebind-runner ownership/continuation remain unbound. No target or
physical acceptance follows from these host tests.

### Rebind ACTIVE normal OFF and observation helpers — 2026-11-14

`rebind-active-stop.c` owns the original rebind runner by pointer. It resumes
that runner's suspended snapshot, executes existing precreated normal OFF,
retains snapshots/guards on failure, then discards the baseline and wipes copied
ON credentials only after full OFF. No live runner is copied into a legacy
startup context and no old epoch is substituted.

`rebind-observe.c` checks fresh ACTIVE settings/network/services/firewall and
exact new-epoch OPEN/current token, including commit/open nonces. OFF observation
requires the original stop pointer, released CLOSE identity, completed service
cleanup and cleared temporary settings. CLOSE extraction holds the service guard
across full OFF observation and a second driver read; drift clears output.
These are software/configuration receipts, not physical RF acceptance.

The host fixture uses real snapshot/stage/suspend/resume, normal OFF, CLOSE
controller and observers. It checks nine foreign configuration fields in ACTIVE
and OFF, identity/token/nonce drift, second-read CLOSE serial drift and retained
three guards during isolation failure. Driver/netdev/resource actors are
injected.15 prepared native TUs compile. Both helpers are experimentally linked
with strong target symbols; backend routing/owner adoption and physical resume
remain unbound. Checked Main startup and scheduler integration remain necessary.

### RC backend rebind routing — 2026-11-14

`rebind-owner.c` embeds the new runner and pointer-based normal OFF at a stable
address. `wr_iot_rc_rebind_begin` in RC backend requires the exact prior retained
OFF tuple, completed/unowned legacy OFF, a fresh request identity and current
mode. Old OFF is provenance only: fresh physical RELEASE/new-Main admission
still occurs inside the runner before staging. Live contexts are not copied.

Once retained, public execute/continue/status and fresh CLOSED extraction route
to the rebind owner; old ON receipts cannot report ACTIVE. Private quiesce also
uses this owner, preserves desired settings and continues the same normal OFF.
Legacy-only composition fixtures resolve new owner adapters with assertions
that must remain unreachable, preserving their original verification scope.

The new RC composition executes real owner/runner/admission/staging/commit/
normal OFF and observers; it injects old OFF provenance, network and driver
actors. It covers wrong old tuple, foreign continuation, ACTIVE token drift,
retained isolation failure, desired preservation and new-epoch CLOSED.
16 prepared native TUs compile. This is not physical restart scheduler binding.
Ordinary ON after rebind OFF and repeated physical-resume cycles still require
explicit implementation; they currently refuse without initial-idle fallback.
Checked Main startup, scheduler, target build and physical acceptance remain.

### Ordinary ON after rebind OFF — 2026-11-14

RC `rebind_reopen` accepts a fresh ON only after a fully observed rebind OFF.
It obtains an exact pointer-free CLOSED witness in the new epoch and verifies
it again through the existing reopen predicate. Dormant legacy state must be
completed/unowned or empty. No live runner, stop or snapshot is copied: the
ordinary runner begins directly at its final backend address. Rebind routing
is retired only after this new runner has claimed its context. Pre-claim failure
keeps the source OFF owner; private quiesce still works after dormant legacy
state has been discarded.

The ordinary path thereafter uses the existing CLOSED-reopen/normal OFF
architecture. It never reuses initial-idle admission or the physical one-use
rebind claim. The native RC composition checks invalid mode, CLOSED serial
drift, stable handoff, ACTIVE status and a subsequent public OFF with new OPEN
token/CLOSED serial while the epoch stays unchanged. Physical rebind probe and
initial-idle counters remain unchanged. Network and driver actors are injected;
this does not prove device association or RF behavior. Direct repeated physical
resume without this ordinary handoff remains separate unfinished work, along
with checked Main startup, scheduler, target and physical verification.

### Direct repeated physical resume admission — 2026-11-14

`wr_iot_rebind_owner_restart` validates the current completed rebind OFF tuple
for a subsequent physical RELEASE. Snapshots, service guards, profile captures
and unused startup recovery owners must be inactive before replacing the owner.
Only this completed/unowned context may be retained as rollback metadata; no
live runner/snapshot is copied. On read-only refusal the exact completion is
restored and its internal stop pointer repaired. A new partial snapshot/guard
keeps the new owner and cannot be overwritten with the previous completion.
RC private begin routes subsequent admission to this owner while keeping the
old/new epoch receipts distinct.

The native RC composition covers epoch2 OFF -> epoch3 ACTIVE/OFF, stale tuple,
invalid mode, read-only probe refusal and epoch4 partial-snapshot cancellation
failure. Driver, network and physical completion actors are injected. This is
admission evidence, not a claim of repeated hardware restarts. Checked Main
startup (including desired profile/key loading before init), full scheduler and
outer guard completion remain required. The pinned SDK restart_wifi_rt mixes
stop/profile generation/AP/WDS/APCLI startup, so the whole stock helper cannot
be replayed after the already-owned physical RELEASE.

### Saved key/profile correspondence before Main startup — 2026-11-14

The cold generator already reads saved `wr_iot_ssid`/`wr_iot_psk` independently
of temporary activation gates. Valid saved credentials are reserved at BSSID3
while OFF; a factory random key is only for wholly empty unprovisioned OFF.
A private NVRAM credential override is therefore unnecessary. Runtime enable
policy remains owned by the retained RC transaction, not this cold parser.

`restart-profile.c` compares saved credentials with the immutable desired ON
request, validates the existing third-BSS profile through the no-write scanner,
then independently rereads the fixed profile bytes/inode and saved credentials
under the retained service guard. It refuses missing/nonregular/symlink/oversize
files and byte drift, including same-size modification. Owned buffers and
credential snapshots are wiped on every release. It neither generates nor
writes a profile, changes NVRAM or opens a BSS. Match is current file evidence,
not a future lease, loaded-key verification, association or RF acceptance.

Native tests execute the actual cold parser/profile scanner/capture and inject
borrowed NVRAM, guard failure and an external file change.17 prepared native TUs
compile; target symbol gate includes the observer. It remains unbound to Main
startup. The pinned AP helper calls mlme_state_rt and ignores Main/Guest ioctl/
bridge results, so its void return cannot certify readiness. Owned generation/
recovery, checked one-shot Main startup, scheduler and physical tests remain.

### Owned pre-start profile generation — 2026-11-14

`restart-generation.c` captures the fixed radio profile through the existing
journal only with the exact retained RELEASE/intent/desired context and Main
administratively DOWN. It attempts the isolated SDK generator once, marking
UNCERTAIN before mutation. No-reload skips generation. Successful readback of
saved credentials/third BSS reaches VERIFIED while retaining the baseline;
this does not open Main or release any physical guard. A later Main/resume
owner still needs explicit baseline finalization.

Partial errors use existing identity-checked journal restoration. Foreign inode
or an unrecorded/pending write keeps recovery ownership and cannot trigger
another generator call or blind restore. Each step performs one phase;
normal pending shutdown permits cleanup but prevents generation. A read-only
post-capture refusal cancels its capture; completed rollback clears copied
request credentials. Native tests use actual capture/journal/restore/observer,
with physical/Main state and SDK actors injected, including pending-write and
foreign-file refusal. Fixed ra0 state reads use only SIOCGIFFLAGS and never
substitute administrative DOWN for the separate physical RELEASE receipt.

Pinned SDK inspection confirmed gen_ralink_config_2g delegates to the SoC2g
generator and the existing path matches RT2860AP.dat. Its original tail ignored
stream/final-close errors. The preparer now checks ferror/fflush/fclose only for
WR1200JS SoC2g and returns-1 on failure, allowing owned rollback. Other boards
and bands retain the baseline branch. Extracted-fragment tests inject each
stdio failure and verify one close. Both new objects and the SDK wrapper have
strong target-symbol gates.19 prepared native TUs compile; no Main startup,
target-image or physical acceptance is claimed.

### Retained Main UP controller (experimental)

`restart-main-up.c` uses fixed ra0 GETFLAGS followed by one SETFLAGS preserving
other flags. Socket/GET/already-UP refusal is NOT_SUBMITTED; SET or final-close
errors are UNCERTAIN. No internal retry or readiness inference occurs.
`restart-main-controller.c` retains the generation owner by pointer and marks
`main_may_have_started` before any transport call. This monotonic fence disables
pre-start profile restore even if Main later appears DOWN. NOT_SUBMITTED stays
retained for explicit recovery because a foreign UP cannot authorize restore.

WAIT/READY steps verify retained physical origin, journal-owned profile identity,
profile credentials and a fresh exact physical rebind observation with a newer
Main epoch. Once pinned, that epoch cannot change silently. UP success alone
never sets READY; pending shutdown, foreign owner or zero future OPEN nonce
refuse. READY is a software driver/configuration predicate only, not Main bridge,
Guest, DHCP/client/RF acceptance. Actual journal/controller composition tests
cover uncertain UP once, profile replacement with identical content, changed
RELEASE, no pre-start restore after UP and epoch drift. Physical/UP/probe actors
are injected. Runtime prep links both objects; scheduler remains unbound.

### Checked Main LAN attachment

The pinned SDK defines ra0/br0 in netutils.h; its bridge helper does not perform
post-ioctl membership readback. `restart-main-bridge.c` restricts operations to
these names, checks service ownership, actual bridge type, stable indexes, Main
UP and master link. It refuses foreign masters. An already attached interface
is observed without another add; mutation/close errors remain uncertain.
`wr_iot_restart_main_lan_step` records its one attempt before calling the adapter,
then uses readback only. Both before and after bridge observation it requires
fresh Main driver/profile/origin readiness. Lost membership cannot replay add.

Actual controller/bridge-transport composition passes error-after-add, readback
reconciliation, foreign/detached membership and epoch refusal, with syscall and
driver actors injected. Full66 host suite passed;22 prepared native TUs compile.
The adapter/controller are experimentally linked with target symbol gates.
Guest/services, post-UP recovery, baseline finalization and scheduler remain
unfinished. No target image or physical runtime acceptance is implied.
