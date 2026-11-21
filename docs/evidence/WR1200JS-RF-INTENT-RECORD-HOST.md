# Owned RF write intent record — 2026-11-06

The isolated layer records one unresolved RF write before hardware submission.
The actual CmdRFRegAccessWrite builder tags expected stream/address/value; the
private sender compares those tags against all three serialized LE payload
words and requires exactly 12 bytes before recording. The record stores the
full five-field bootstrap ticket and a monotonically increasing generation.
Mismatch refuses before TX. An active record cannot be overwritten by another
RF write, and generation overflow poisons recording rather than wrapping.
Generation is host provenance, not a firmware-echoed nonce; checked-ID
retirement and the firmware/RX epoch boundary remain separate requirements.

TX success or timeout never clears the record or the unconfirmed-effects
counter. This makes the next readback integration able to compare a snapshot
of the original request, rather than trusting values supplied by a later query.
MAC no-response writes remain separately counted; RF evidence must not resolve
their effects. There is no RF query admission or record/counter clearing here.
Config finish also refuses an active/poisoned record even if the aggregate
counter is incorrectly zero, preventing that inconsistency from granting
software completion.

Fresh ASan/UBSan checks pass:

- Pure record: every ticket/tuple/generation field, duplicate retention, poison,
  generation overflow, valid zero register/value and stale-generation refusal.
- Actual owner/transport/SDK initializer/RF builder: serialized payload tags,
  pre-TX recording, duplicate RF refusal, timeout and late consumer completion
  retaining the record, mismatched metadata refusing before hardware.
- RF parser and earlier synchronous/no-response configuration paths: PASS.
- Full generated-tree inventory: PASS. Temporary candidate (~14MB) and binaries
  auto-removed; unfinished older input remains preserved.

The peer82 recipe stages the layer/test. This is host/source evidence; target
compile and runtime are pending. The config phase is still not bound to init,
the outer gate remains closed, and readback proof retirement, MAC query
protocol, checked-ID budget/epochs, normal promotion and repeated lifecycle
remain required. No journal reset or manufactured ACK was added.
