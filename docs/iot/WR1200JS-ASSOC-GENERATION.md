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
A separate visible-generation/MAC snapshot also lives outside cleared entries.
All generation and snapshot writes use MacTabLock. The entry is a mirror;
its counter must survive both entry memset and whole-table clears.

`mgmt/mgmt_entrytb.c`:

- MacTableInsertEntry advances the slot after mac_entry_reset (which clears
  the complete entry once or twice). It skips an exhausted slot. Snapshot
  publication happens only after complete entry/hash initialization and before
  the final table unlock.
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
3. Capture reads the published per-WCID generation/MAC snapshot immediately
   before queue locking; it acquires no table lock. A bounded reader uses
   READ_ONCE and read barriers, checks the generation again and compares the
   live entry mirror/validity. A concurrent change refuses the snapshot. If
   reassociation occurs after capture, publication retains the **older** event
   identity and execution rejects it.
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


The initial trylock-only callback version (`dd5c44de`) refused enqueue on
unrelated MacTabLock contention. Source review identified a progress regression:
WPARetryExec ignores MlmeEnqueue's return and its RetryTimer is one-shot.
The revised callback capture and execution checks therefore acquire **no**
table lock. They do not lose a valid retry merely because another station owns
the table. They also cannot form cancel-timer/table-lock deadlock.

Snapshot writers withdraw visibility with zero, issue a write barrier, copy
MAC bytes, issue another barrier and publish the new unique generation. Readers
compare both generation samples and the live mirror. There is no generation
wrap/republication ABA. Withdrawal before station timer cancellation rejects
work for a deleting station; unrelated station deletion leaves this snapshot
readable. Whole-table clears also invalidate entry mirrors, so an old published
snapshot cannot authorize a cleared entry. Full insertion publishes a fresh
counter value only after all initialization.

Only association-success mutation retains a nonblocking table trylock;
contention refuses association to the existing client retry path. The OS_ABL
form unwraps the native pContent lock as RtmpOsSpinLockBh does. No retry timer is
rearmed from a contended callback and no new worker/reset/scan is introduced.

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

## Bound ra2 GROUPKEY REQUEST candidate

`ra2-gtk-request-composition.py` factors the existing AP group-key-request
block and wraps it before its first GenRandom/nonce/key/peer mutation. The
immutable queued receiver BSSID selects ra2; classification does not rely on
a WCID entry that could already have been reused. Main/Guest, other chips and
the feature-disabled build retain the native block.

`ra2-gtk-request-kernel.h` admits the current OPEN receipt under the transition
lock, takes one existing control-user reference and excludes another ra2 key
writer. It then validates the exact queued generation/MAC/WCID/wdev under
MacTabLock, refuses an already-running deletion, enters the existing peer-table
transaction and reserves this association in wr_assoc_event_users. No lock
spans the native crypto, timer cancellation, send or key-install operations.

The existing deletion execution wrapper refuses while the table transaction
is held. The entry deletion body also checks the association reservation before
any timer cancellation. Reassociation checks the same reservation under
MacTabLock. Native timeout/MIC actions are **not** enclosed by this scope and
can still perform their own legitimate deletion.

The complete factored block runs synchronously and then releases the exact
association, table transaction, key-writer flag and control-user reference.
Native early return from the block still returns to the wrapper's release.
Unexpected generation/ownership changes poison control admission rather than
silently freeing another association's reservation. The independent ra2
GREKEY timer uses the same key-writer exclusion and preserves its countdown
when a request owns that exclusion; its natural repeating timer owns retry.

Host fixture `check-ra2-gtk-request.py` executes the actual transformed block
with the real admission helpers and the existing native deletion wrapper. It
attempts reassociation, deletion, reset reservation, CLOSE and a second key
request inside GenRandom. All are refused while the operation is held; the
key install then uses the original current association. Release permits later
reassociation. Stale/closed/contended/already-deleting/MAC-mismatch cases refuse
before any native mutation. Native early-return release, Main/Guest/other-chip
passthrough, feature-disabled and OS_ABL builds also run under ASan/UBSan.

Evidence: `WR1200JS-RA2-GTK-REQUEST-HOST-2026-11-18.json`. These are guarded
software-contract and SDK-actor tests. Target compilation, all optional direct
station mutators, the lifetime of every WPA action, timer-station lifetime and
physical Main/Guest/IoT acceptance remain separate requirements. This is not a
claim that complete safe OFF/reopen or the firmware/DMA boundary is finished.

## Native GTK request execution witness

`tools/iot/check-assoc-gtk-execution-gap.py` executes the generation-only control
WpaEAPOLKeyAction AP group-key-request block before the new scope binding.
A boundary actor forces same-MAC/WCID reassociation inside GenRandom, after the
initial action check. The final generation check correctly prevents
WPAInstallSharedKey. Nevertheless the actual earlier statements already change
DefaultKeyId/GNonce/GTK, GTKState and retry state, and call WPAStart2WayGroupHS
on the new association. This demonstrates why another point check immediately
before hardware write does not prove an execution lease.

The control actor without reassociation still executes the native key request
and install. Crypto, timer and hardware operations are boundary actors; this
is deterministic host evidence, not a reproduced router race. Evidence:
`docs/evidence/WR1200JS-ASSOC-GTK-EXECUTION-GAP-2026-11-18.json`.

The new bounded driver binding admits the exact ra2 association before its first
software mutation and keeps the existing CLOSE control-user fence for the
complete operation. Its source binding and focused host checks are described
above; the control witness remains to distinguish the original gap from the
bound candidate. Complete target/runtime acceptance is still unproven.

Do not wrap all WPA actions in a blanket deletion exclusion: the native
WpaEAPOLTimeout calls MlmeDeAuthAction, and the EAPOL-Key MIC-failure branch
can invoke countermeasures. A generic transaction would refuse their own
necessary deletion. The bounded GTK-request operation now has a source binding and host checks;
trace other actions separately. No lifetime binding for all WPA actions is
claimed by these changes.

## Verification

`tools/iot/check-assoc-generation.py` composes the exact pinned source, checks
all four enqueue branches and requeue/dispatch insertion points, compiles and
executes the **native modified normal/EAP enqueue functions and native entry
reset and one-shot retry callback** with GCC ASan/UBSan, and executes the actual generation helper header.
Cases cover same-MAC/WCID reuse, reassociation, invalid entry/MAC/WCID, malformed
or missing capture payload, stale snapshot publication, original stamp on
requeue, unrelated events, whole table clear, counter exhaustion and wrong
native lookup slot. The native WPARetryExec executes while MacTabLock is
already held and still enqueues the valid event. Readers are interrupted at
all three read-barrier boundaries by an in-place reassociation and refuse the old
snapshot. These deterministic host interleavings are not an LKMM/MIPS memory
model proof or physical scheduling test. Composition rejects a second application.

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

## Target compiler namespace regression — optional1399

Optional1399 failed in the real MIPS module compiler: Linux's `current` macro
expanded the scalar helper parameter named current. The original job shows
both get_current/current definitions and the expansion at assoc-generation.h
line11. The more recent adapter helper also used current as a local name.
Both identifiers are renamed; kernel macros remain defined and unchanged.

The host fixture now includes the exact two macro definitions from that target
log, deliberately rejects a mutated old-name helper and compiles the corrected
helpers and native callback fragments. A function-shaped current macro alone
would not sufficiently reproduce the scalar parameter collision. This is a
host regression check; successful target recompilation is still required.
Evidence: docs/evidence/WR1200JS-OPTIONAL1399-CURRENT-MACRO-2026-11-18.json.

## GTK scope release fault-injection coverage

The focused request fixture now corrupts four independently owned values after
successful admission: association generation, per-WCID reservation, key-writer
owner and peer-table transaction count. Actual leave helpers poison future
control admission; foreign WCID/key reservations remain untouched, transaction
underflow poisons the table, and repeated release of the now-inactive local
scope does not decrement control users twice. An executed negative-control
header with release poisoning removed must fail these assertions.

These deterministic source/host tests exercise an invariant breach; they do
not demonstrate that every external station mutator observes this lease.
Evidence remains WR1200JS-RA2-GTK-REQUEST-HOST-2026-11-18.json. The production
source is unchanged by this test addition; include it with the next coherent
verification package rather than creating a duplicate firmware run now.

## Next lifetime binding: periodic timer versus association prefix

Fresh source audit confirms MlmeHandler sets bRunning under TaskLock and
serializes AP_ASSOC_STATE_MACHINE with WPA_STATE_MACHINE. This serializes their
normal queued actions, not the independent GREKEYPeriodicExec timer callback.
The current timer wrapper owns control_users and the ra2 key-writer flag,
without a peer-table transaction or per-entry reservation during its station
loop. The native association path clears GTKState/PairwiseKey before calling
APBuildAssociation and its later generation/reservation check. Consequently a
late association-success check cannot by itself protect that earlier mutation
from a concurrent timer. Do not equate the GTK-request scope with coverage of
this periodic-timer path.

Next implementation must reserve affected ra2 peers and exclude association
mutation before its first key clear, with balanced release and no table lock
across native timer/send work. A point check added only at SST_ASSOC is
insufficient. Source hashes and required concurrency checks are recorded in
WR1200JS-REKEY-PEER-LIFETIME-SOURCE-2026-11-18.json. This source audit is not a
physical race reproduction or a completed periodic-peer lifetime fix.

## Executed periodic peer-loop coverage

The existing rekey host fixture previously exercised countdown/key installation
with zero stations; this did not cover its per-peer WPAStart2WayGroupHS branch.
The fixture now runs the actual native callback with a secured ra2 station and
an expired rekey interval. A control case handshakes with generation1. A second
case replaces the station in the GenRandom boundary actor after admission and
before the native loop; that loop mutates and handshakes with generation2.
Both feature-enabled and feature-disabled builds execute this branch.

This is an intentionally passing witness of a remaining gap, not a passing
lifetime acceptance test. The replacement is a host actor, not a native
concurrent deletion or on-device reproduction. Do not report the periodic-peer
path verified from the fixture's existing host_contract_verified flag; its new
periodic_peer_lifetime_verified field is explicitly false. Evidence:
WR1200JS-RA2-PERIODIC-PEER-GAP-HOST-2026-11-18.json.

## Periodic snapshot requires insertion exclusion too

The actual peer-table owner permits multiple concurrent transactions, and
peer-table-insertion-gate checks table_allows(0), which does not reject a
nonzero transaction count. peer-normal-insert itself enters another transaction.
An executed ASan/UBSan header check confirms both transactions are admitted
while exclusive reset is refused. Therefore taking the existing transaction
and reserving only current ra2 WCIDs cannot keep a periodic snapshot complete:
a new ra2 peer can be published afterward and enter the native timer loop.

A correct timer binding needs ra2 insertion and early association-mutation
exclusion for its entire operation, in addition to exact peer reservations and
existing CLOSE admission. Rejecting all global insertions would unnecessarily
change Main/Guest semantics. The snapshot alone must not be marked a fix.
Evidence: WR1200JS-REKEY-INSERTION-TRANSACTION-GAP-2026-11-18.json. No insertion
body, concurrent target execution or hardware was run by this header witness.

## Unbound ra2 association/key arbiter

ra2-association-owner.h implements the local arbitration needed before binding
periodic peer retention: association actors exclude a key writer, and the key
writer excludes association actors. Access requires one caller-owned lock;
tickets are private, noncopied stack objects. The helper performs no wait,
allocation, reset or firmware command. Serial/count exhaustion refuses admission
and changed writer ownership retains the writer and poisons future admission.
The host fixture checks both operation orders and independent adapter progress.

This helper is deliberately not included by prepare-driver-api.py yet and does
not alter the running candidate. Completion requires balanced native wrappers
before first key mutation, ra2 insertion/authentication reset coverage, periodic
and requested GTK coverage, peer-generation retention and existing CLOSE
lifetime admission. Main/Guest must bypass only after validated BSS selection.
Host evidence: WR1200JS-RA2-ASSOCIATION-OWNER-HOST-2026-11-18.json. Native binding,
MIPS and runtime verification are false; the periodic peer gap remains open.

## Outer mutation-wrapper preparation (not installed)

ra2-mutation-wrappers.py prepares outer wrappers for the common assoc/reassoc
handler and both authentication handlers. Native function bodies remain
byte-for-byte intact; reversible composition is checked against the pinned
sources. The outer wrapper handles pass-through, refusal and admitted execution,
so a return in the native body still reaches admission release. Feature-disabled
code retains the direct native call.

check-ra2-mutation-wrappers.py executes the exact generated wrappers with boundary
actors for the untouched native bodies, for both compile-time feature modes.
It does not execute the full authentication/association state machines. The
required Linux wr_ra2_mutation_enter/leave functions are not yet implemented;
this producer is not called by prepare-driver-api.py and its output must not be
installed as a buildable driver. Next work is adapter initialization, consistent
lock/lifetime admission and ra2 insertion/key-writer binding. The header and
wrappers alone do not close the periodic peer gap.

## Linux mutation admission helper prepared locally

ra2-mutation-admission-kernel.h implements the wrapper admission/leave functions
using the actual current OPEN-receipt predicate and transition lock. Exact
queued receiver BSSID selects ra2. A validated ra2 mutation takes one existing
control-user reference and one association arbiter ticket in the same locked
admission span. Failure to allocate that ticket rolls back only the just-added
control reference. Key-writer activity, closed receipts, malformed frames and
exhaustion refuse before any native action. Main/Guest and other-chip paths
return native pass-through. A foreign or inactive leave ticket poisons control
admission and cannot decrement either adapter's unrelated reference.

The host check uses the actual receipt/arbiter helpers and boundary adapter
setup, in direct and OS_ABL modes. It does not execute full native mutation
bodies. This helper remains uninstalled: adapter state initialization, native
wrapper/header insertion, all ra2 insertion actors and both key-writer bindings
must be composed and tested together before enabling it. Source/host evidence:
WR1200JS-RA2-MUTATION-ADMISSION-HOST-2026-11-18.json. Target and runtime false.

## Unified native mutation admission composition

ra2-mutation-binding.py now composes the adapter owner field, exact native
association/authentication outer wrappers and actual Linux admission headers
as one pending source change set. Duplicate installation/source drift refuses.
The native bodies remain untouched. This producer is still not called by
prepare-driver-api.py: ra2 insertion and both key-writer actors must participate
before the arbitration is enabled in a target candidate.

check-ra2-mutation-admission.py now executes each exact generated wrapper with
the actual receipt/control/arbiter admission, with early-return native boundary
actors. Accepted execution releases both references; active rekey refuses
before the native actor. Direct/OS_ABL checks pass. This verifies the combined
wrapper/admission seam, not complete SDK body behavior or target compilation.

## Final insertion-stage composition correction

The final peer pipeline renames the native insertion body to
wr_iot_mac_insert_entry and replaces public MacTableInsertEntry with the
wr-iot-peer-normal-insert.inc outer wrapper. Snapshot publication must use the
private body containing mac_entry_reset and hash initialization. The composition
now selects that body explicitly when present and validates its native anchors;
pristine-only composition still uses the original native function. A host
fixture composes a renamed native body plus the include-based public entry and
checks exactly one publication in the private body. Target verification of this
correction is pending; this source-stage error is independent of current-macro
compilation. No CI failure result is inferred from this local source witness.

## Public ra2 insertion admission prepared

The pending Linux admission now has an exact embedded-wdev entry, sharing the
same receipt/control/association reservation as queued mutation. No fabricated
MLME event or interface-name inference is used. compose_insertion wraps the
whole peer-normal-insert.inc public function, including its unlocked private
insertion/tail call and original table transaction release. Result/NULL return
passes through after releasing the outer ra2 reservation. Main/Guest use the
native body without that reservation; active rekey refuses only ra2.

The combined host test executes the exact existing public transaction body,
new outer wrapper and real admission helpers. Its private insertion call is a
boundary actor checking that no table lock spans the call and that control,
association and table reservations remain held. Success and NULL both balance;
active key ownership refuses ra2 and permits Guest. Direct/OS_ABL checks pass.
This is not full private insertion execution, and the new producer is still
uninstalled until requested/periodic key-writer arbitration is composed too.

## Combined arbitration preview for both GTK actors

ra2-key-arbitration-composition.py adds linear key tickets to the requested
GTK scope and the existing periodic wrapper. Both take a key ticket under the
same transition lock as mutation actors, before entering their native bodies.
Active associations refuse a writer; a writer refuses mutation tickets.
Failed ticket admission rolls back only the new control reference; release
checks the exact ticket, and owner corruption poisons future control admission.

check-ra2-key-arbitration.py executes both transformed native GTK paths with
actual arbiter/receipt helpers and SDK boundary actors, in feature-on/off host
ASan/UBSan builds. Requested-key execution refuses a nested mutation, and an
existing association refuses periodic rekey before nonce/counter mutation.

ra2-mutation-binding.compose_all builds one source preview containing the
adapter owner, native association/auth wrappers, public insertion outer scope,
requested-key scope and periodic-key scope. It requires the real prepared
public insertion fragment and checks exact predecessor anchors. It is not
called by prepare-driver-api.py yet. The outstanding periodic table transaction
and exact peer-generation retention must be bound before publication into the
candidate. Arbitration alone does not protect a peer from deletion.

Evidence: WR1200JS-RA2-COMBINED-ARBITRATION-HOST-2026-11-18.json. Full native
station lifecycle, MIPS and runtime acceptance remain unverified.

## Periodic per-peer scope prepared

ra2-rekey-peer-scope.h reserves the exact generations of existing ra2 client
entries under MacTabLock, plus one existing peer-table transaction. It refuses
an active deletion, pending older insertion transaction, conflicting per-entry
reservation, invalid WCID/generation/wdev or table reservation before changing
any peer. Main/Guest entries receive no reservation. No table lock spans native
timer cancellation/send work. Leave validates generations and identity before
clearing each reservation; mismatches retain foreign ownership and poison the
table. Caller must already own the ra2 key arbiter and adapter/control lifetime.

Host fixture executes the real scope and existing deletion wrapper with SDK
actors: deletion/reset/reassociation refusal, balanced release, wrong-entry
and contention preflight remain test requirements at their exact coverage.
The current executed cases cover two ra2 entries, reassociation/deletion/reset
refusal through the table transaction, balanced release and feature-independent
Linux lock layouts. This does not prove full periodic callback composition.

The pending compose_all now places this scope around the arbitrated native
periodic body. Admission refusal leaves native rekey counters untouched and
releases key/control admission for the natural next timer tick. A failed leave
poisons control admission. These composed callback paths require combined
execution tests and target compilation before enabling the producer. No
production candidate is changed by preparing this source composition.

## Full periodic callback host composition

check-ra2-periodic-peer-path.py now executes the actual transformed native
GREKEYPeriodicExec with both key arbitration and retained-peer scope. At the
GenRandom SDK boundary it attempts real guarded reassociation, the existing
native deletion wrapper, exclusive table reset and a competing key request.
All refuse while the scope is held. Native handshake statements update the
original generation and all reservations release after return. The independent
countdown-only key-install path and admission-refusal counter preservation are
covered in the composed callback. Direct/OS_ABL ASan/UBSan checks pass.

The helper uses exact ra2 wdev identity; a separate WDS/APCLI entry whose
numeric function index is 2 does not become an ra2 client. Inconsistent ra2
client identity refuses conservatively. This completes the focused host callback
composition check, not full optional-feature native mutator coverage, MIPS,
image or device acceptance. Evidence:
WR1200JS-RA2-PERIODIC-PEER-PATH-HOST-2026-11-18.json.

## Isolated peer82 activation of complete arbitration package

The source preparation above is now connected as one compose_all layer in
prepare-driver-api.py after generation and GTK-request preparation and before
manifest hashing/writes. Earlier unbound notes describe preparation history.
This activates only the isolated peer82 driver source; it does not install a
new router firmware or establish physical acceptance.

ABI runs native-wrapper/admission, requested/periodic key arbitration, retained
peer scope and full native periodic-callback host checks. Optional checks the
exact final prepared fragments with check-ra2-arbitration-source.py, runs those
same SDK boundary fixtures, preserves all predecessor checks, snapshots the new
helpers and then invokes the existing MIPS module build. Predecessor execution
fixtures remain explicit control-path checks; exact source validation covers
the fully composed successor and separate fixtures execute its changed helpers.

The adapter owner is zeroed by the verified fresh-adapter allocator and lives
outside MacTab. No live reset reinitializes it. Source/host checks pass; new
optional MIPS/image verification and separately authorized runtime remain
required. Other direct optional-feature station mutations and the lifetime of
all WPA/TxS/DMA/IRQ paths are not declared complete by this bounded package.
Current delivery boundary: WR1200JS-RA2-ARBITRATION-STATUS.md.

## Successor report hash correction

The predecessor timer fixture's prepared-source assertion already accepted the
exact new arbitration/peer-scope source, but its candidate_ap_wpa_sha256 still
reported the predecessor composition. The report now hashes the actual checked
successor expectation and separately names host_control_ap_wpa_sha256. It also
states that this fixture executes the control callback while the separate
periodic-peer fixture executes the successor. A composed-tree test checks the
successor hash against actual file bytes and confirms that the two hashes differ.
The combined source checker additionally records hashes read from the prepared
files, separately from pristine-derived expected hashes. No driver behavior is
changed by these reporting corrections. Evidence:
WR1200JS-RA2-SUCCESSOR-REPORT-HASH-2026-11-18.json.
