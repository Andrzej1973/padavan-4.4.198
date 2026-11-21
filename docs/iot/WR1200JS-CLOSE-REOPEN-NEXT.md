# ra2 CLOSE and reopen integration

Historical checkpoints follow. On 2026-11-21 the repository is on local main;
the dated next steps below are not a current implementation queue. Consult
PROJECT_STATUS.md and CODEX_HANDOFF.md for current work and distinguish host,
target, final-image and separately authorized device evidence. Preserve these
notes as provenance; reconcile each proposed operation against current code
before implementing it again.

Current source checkpoint is ebe16bd7. Software queue gating and PS timeout
recovery are composed into the isolated driver candidate. RC CLOSE transport
and controller are staged, with the activation backend still unbound.

The next implementation must carry the retained OPEN nonce, adapter epoch,
registration generation and open token through the existing RC service owner.
`driver-close-controller.c` can submit CLOSE once and reconcile uncertain
submission through operation13. Its completed state tracks reference retirement.

`driver-api-close-finish.h` clears the borrowed task pointer after synchronous
finish and preserves `active`. The designated retirement thread transfers its
module hold only after work/reference readiness. It preserves the active owner.
`driver-api-owner-binding.inc` refuses a subsequent OPEN while that owner is
active. Consequently successful progress alone cannot currently reopen ra2.

To complete the software lifecycle, implement a scoped owner-release operation
using the same RTNL and transition-lock serialization. Revalidate the original
identity, completed reference retirement, returned extra netdev hold, transferred
module ownership, current registration, ready main radio and absence of reset,
removal, control users and recovery work. Preserve the old identity through all
refusals. Couple release to the existing closed beacon/producer and DMA state
observations, while keeping mapped resources under their established owners.

Before exposing that operation, trace data and management enqueue paths after
software OFF, confirm their admission predicates, and establish which retained
beacon TxS callbacks can still mutate BSS state after reopening. Any late event
must be rejected by its existing reservation identity or safely consumed without
mutating a new lifecycle. Retain ACK stale protection and shared ring ownership.
A timeout alone cannot transfer a live skb or free hardware-owned descriptors.

The RC backend must retain network isolation through close/recovery, then bind
the already implemented bridge, DHCP/DNS, firewall and policy stages to the
activation state machine. Validate failure at each actual resource boundary,
repeat OFF/reopen and preserve Main/Guest traffic. Target compilation and
physical runtime acceptance remain distinct requirements.

The current regression generator `prepare-beacon-txs-ledger-check.py` already
executes a duplicate old-PID witness after allocation of a new host generation.
The old report consumes the new reservation. `TXS_CLAIMED` protects the
currently executing callback, while post-callback PID reuse still needs a
scoped policy. Before owner release, trace the actual emitted descriptor and
its handler mutation boundary to select software recovery without relying on
unavailable ROM specifications. No new runtime workaround is installed by
this investigation.

## Sequence correlation ruled out for the existing constructor — 2026-11-12

Fresh exact-source inspection shows write_tmac_info_beacon zeroes the long
TXD and write_tmac_info does not assign txd_3->sn or sn_vld. Thus the TxS SN
currently observed in DBG cannot be treated as a host-assigned generation.
Do not implement an SN equality filter against invented software state.
Evidence: docs/evidence/WR1200JS-BEACON-DMA-TXS-SOURCE-2026-11-12.json.
The next candidate must explicitly define scoped beacon publication and pacing,
including reservation allocation and normal DMA-owner completion, rather than
adding a comparison unsupported by the emitted descriptor. This finding does
not require proprietary ROM documentation and does not change MCU ACK safety.

## Unbound reservation-free status experiment — 2026-11-12

ra2-beacon-no-host-status.py now composes an exact-scoped TYPE1 policy in
write_tmac_info before AddTxSStatus. It does not change TYPE0 or data TXD
constructors, MCU ACK protection or shared queue machines. The actual changed
branch extracted from the hash-checked pinned constructor passes injected
allocator ASan/UBSan checks. It is composed only in the separate optional experimental target pipeline.
The production activation backend remains unbound.
The tracked submission guard still rejects generation0, deliberately.

Before binding, implement one coherent reservation-free periodic/DMA lifetime
mode, including retained beacon buffers, natural-window pacing, CLOSED/OPEN
ownership and handling of earlier tracked reports. Do not merely remove the
tracked guard or advance DMA_DONE to IDLE. Evidence and limits are recorded in
WR1200JS-RA2-NO-HOST-STATUS-EXPERIMENT-2026-11-12.json.

The pinned SDK already rate-limits recovery by TSF Lowpart minus
WriteBcnDoneTime[timer_loop] against BeaconPeriod*1024 (hw_ctrl/cmm_asic_mt.c:
1295). APUpdateBeaconFrame records that timestamp after the submission call,
without checking its result (ap/ap_connect.c:1730). Therefore reuse it only as
a conservative attempted-update pacing marker, never as DMA/RF completion.
Without host TxS, timer_loop no longer advances through BcnTxSHandler; verify
that slot lifetime and TSF wrap/reset before binding. Existing variables may
suffice for pacing without adding a new global timing policy.


## Experimental target verification checkpoint — 2026-11-12

Published source6393edc8e52da1a413f53c4d7114fa9232d7efe2 adds an isolated
full-module build after the four experimental translation units. Optional1062
(run43282006925, sourcef615bf20) already proves four experimental MIPS objects,
with hashes and dependencies recorded in
WR1200JS-RA2-NO-HOST-TARGET1062-2026-11-12.json. It does not prove the module link.
Live GitHub inspection confirms standard1065/run43285398569 for6393edc8 and
optional1064/run43285095413 for2c44a616 are both executing the firmware build
step. Neither result is accepted yet. After standard1065 succeeds, queue the
exact6393edc8 optional once to execute the full experimental module gate.

The composed nine-path experiment now includes original producer-ticket
propagation, bounded packet submission, natural-window pacing and scoped
callback suppression. These compile checks do not establish a cold epoch or
permit owner release. The next lifecycle decision must establish that the
no-host policy applies before the first ra2 beacon reservation in an adapter
lifetime, and preserve Main/Guest PID ownership through OFF/reopen. An empty
ledger snapshot and elapsed beacon interval alone supply insufficient evidence.


## Reuse of the existing CLOSED probe for release integration

The current call chain already exposes a configuration-only CLOSED query.
`driver-api-closed-entry.inc:wr_iot_driver_closed_ioctl` matches the original
OPEN receipt nonce/epoch/generation/token, then invokes
`mt7603-closed-probe-binding.inc:wr_iot_mt7603_closed_probe`. That function
reserves BSS_OBSERVE under transition_lock, drops the lock for the existing
`wr_iot_mt7603_closed_config_observed`, and finishes the same observation ticket.
Its DMA/TxS helpers acquire their own locks. The observer checks producer gate
revocation and generation twice, exact third-netdev DOWN state, beacon request
OFF, Main running and live flags, plus beacon queue/TBTT configuration.

The probe admission excludes an active or poisoned OPEN owner. It does not
exclude the retained CLOSE owner merely for being active. Therefore a new
parallel hardware observer is unnecessary. Reopen integration can consume the
existing probe after reference retirement, with the same original identities,
provided a compiled no-host lifecycle is established. Preserve active CLOSE
through failed observations. A successful probe alone still supplies no owner
release permission. `driver-api-close-progress.inc` returns0 immediately on
validated module transfer and does not execute this configuration probe.
The release operation must explicitly bridge those two existing contracts and
revalidate the same close/device/epoch identity after the unlocked observation.
Retain packet ownership and isolation while this bridge is incomplete.


## Full experimental module evidence

Optional1066 for6393edc8 linked the complete experimental module. Actual
artifact13976324305 contains ELF32 LE MIPS module5,970,476 bytes, SHA256
 d5b31b32221892cf2363d39b5932dc3d7f327d718ce6708680aee5114b590074.
Defined APUpdateBeaconFrame, BcnTxSHandler and RT28xx_UpdateBeaconToAsic
symbols and the nine-path compile-only manifest were checked independently.
See WR1200JS-RA2-NO-HOST-MODULE1066-2026-11-12.json. This closes the full-module
link gate for that revision. Owner release/reopen and production activation
remain open. Later queue publication correction0e8521d1 requires its own
optional result. The new local constructor-preparation gate validates zero
PID and BSS metadata before composing output; it has not yet been published.


## Local experimental release operation14

The no-host source composer now adds operation14 to its isolated common ioctl
only after the existing RTNL, capability and64-byte copy checks. Operation10
CLOSE and13 reference progress retain their semantics. The release binding
uses existing progress retirement, CLOSED probe and original nonce/epoch/
generation/token, then revalidates the revoked producer generation before
clearing only CLOSE active. The retained receipt makes identical retry safe
until a new OPEN replaces it. No packet or network isolation is released.

The local source tree now has13 changed paths. Actual release binding and
strict wire tests pass with injected progress/observer and ASan/UBSan. Full
module compilation for this version, reset/producer synchronization review,
RC operation14 client integration and physical testing remain pending.
Production activation_ready remains false.


## Local RC release transport/controller

The fixed ra2 API client now sends operation14 through its existing exchange
and preserves close/progress outcomes. Controller release is admitted only
from REFERENCE_RETIRED or a retained release attempt. RELEASE_PENDING and
RELEASE_UNCERTAIN preserve the original identity. Success records OWNER_RELEASED;
repeated local observation returns success without another ioctl. A fresh CLOSE
cannot overwrite this completed context. Network teardown and controller reuse
remain the activation owner's responsibility. RC preparation copies the new
wire dependency. Actual transport/controller fixtures pass ASan/UBSan with
injected system calls, including uncertain replies and idempotence. A duplicate
_GNU_SOURCE test-run flag was removed before the successful rerun. Prepared RC
target build and final activation binding remain pending.

## RC release and commit interleavings — 2026-11-13

Published d056ffcb stages operation14 RC client/controller, separating
reference retirement from explicit software-owner release. Activation remains
unbound. Actual release binding now also passes injected reset, suspend,
removal and epoch drift immediately after producer snapshot and before final
transition-lock acquisition. Refusals retain the CLOSE owner. See
docs/evidence/WR1200JS-CLOSE-RELEASE-INTERLEAVING-2026-11-13.json.
These host checks do not establish RF completion or device acceptance.
Next integrate the activation service owner with retained request/network
isolation, after experimental target verification and admission-path review.
