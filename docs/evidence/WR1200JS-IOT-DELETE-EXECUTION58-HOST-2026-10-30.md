# Replacement deletion execution58 — host evidence

Candidate57 was rejected because retaining a new table owner prevented the
existing WDS checkpoint resume API from reaching its recovery body. Candidate58
is built directly from56, not from rejected57.

`prepare-peer-delete-execution.py` pins all twelve changed input files. It adds
an adapter-owned synchronous deletion execution flag initialized only on fresh
allocation. Normal deletion claims it under MacTabLock, calls the unchanged
private deletion body with its original table serial zero, and releases it
only after the complete body returns, on success or failure. Existing per-entry
WDS state continues retaining the incomplete hardware deletion; it is not
cleared by dropping this execution flag. Parent-reset deletion validates its
existing serial and leaves its ownership with the parent.

Under the same MacTabLock, insertion/WDS admission, table reset, main open,
both close wrappers, raw reset, repeater insertion and the previously audited
EZ type mutation gate now refuse an executing normal deletion. Close also
rejects unrelated active table ownership while permitting its own close retry.
No short lock spans the complete vendor deletion body.

Verified on `.iot-local-check/peer-delete-execution58-20261030` using strict
GCC C11/O2/Wall/Wextra/Werror:

- The contract that failed57 now passes: a modeled NOT_WRITTEN failure followed
  by explicit WDS resume reaches the body twice. Lease-enabled variant also
  checks nested deletion refusal, active flag during the body and preservation
  of a parent-reset serial after successful deletion.
- Five selected checks passed in `peer-delete-execution58-targeted/result.json`:
  insertion, whole WDS transaction, actual close bodies/wrappers, actual reset
  wrapper and internal main-open dispatcher.
- Seven selected variants passed in `peer-delete-execution58-resume-d/result.json`:
  extracted WDS checkpoint flow, two whole reset-loop variants, reset owner,
  startup insertion, and two resume-contract variants. Earlier fixture runs
  exposed stale private-name detection and synthetic adapter-field anchors;
  these were corrected without removing the assertions.

The default suite now detects the renamed private deletion body and includes
the two contract variants for58 instead of the rejected57 model test.

Private vendor deletion, MMIO, layouts, RTNL and kernel locks remain partly or
wholly mocked by these checks. This is not full vendor-body execution or real
kernel concurrency/callback/DMA proof. Fresh full58 replay and default suite
have not run; latest completed full replay remains54. The chain includes58
and excludes57. Adapter release and remaining writer/callback lifetime remain
open. No target/firmware build, device change, dispatch, commit or push.
