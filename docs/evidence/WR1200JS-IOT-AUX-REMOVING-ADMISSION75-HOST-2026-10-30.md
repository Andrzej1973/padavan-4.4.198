# Exact removing auxiliary owner admission75 — host evidence

Confirmed a composition deadlock: WDS_Remove marks the registry removing
before RtmpOSNetDevClose, but WdsVirtualIF_close reserves AUX_CLOSE through
wr_iot_registry_count_matches, which rejects that same removing OWNED record.
The explicit close gates introduced for APCLI/Monitor expose the same required
admission boundary once their family-specific owner wrappers are bound.

Pinned prepare-aux-removing-close-admission.py changes only the candidate
include/aux-close-claim.h. The new count check allows the exact target record
(still published, generated, OWNED, removal_stage0), and refuses another
removing record, duplicate device identity, wrong count or post-unregister
stage. It leaves the general registry count checker unchanged. No vendor
side effects occur before the ticket is reserved; this is not a callback
retirement or retained recovery implementation.

check-aux-removing-close.c first establishes that the old general count check
rejects the marked owner. It then checks same-target admission for WDS/APCLI/
Monitor, identity preservation and refusal cases. Strict host candidate test
passed; six targeted suite variants passed including existing WDS close/open,
aux removal and family result paths. Existing normal close behavior is covered
by the extracted WDS close fixture. No real kernel concurrency is simulated.

The initial direct test compilation selected tools/iot/aux-close-claim.h via
quoted include precedence and failed at the intended successful admission.
The corrected run copies the fixture to scratch and uses candidate/include
first, as the common suite does. Both outcomes are retained; the old-header
failure is not a candidate failure. No process remains from that failed run.

Main preparer now includes75. Candidate75 is isolated from a fresh full-chain
replay; last full host replay74 passed76 variants, last fresh source composition
is70. Next bind APCLI/Monitor generation/serial family-close owner before
side effects, retain successful family result across DOWN continuation, and
complete callback retirement/child/root PCI release. No target build, image
acceptance, runtime/router changes, commit or push in this step.
