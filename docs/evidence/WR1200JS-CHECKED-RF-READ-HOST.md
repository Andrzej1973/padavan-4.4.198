# Checked RF readback and proof retirement — 2026-11-06

The isolated CmdRFRegAccessRead bootstrap route now snapshots the outstanding
RF intent under transition → sender locks. It requires current config task,
full ticket, nonzero unresolved count and the requested stream/address. The
private query tags its generation and expected tuple, sends the SDK 12-byte
QUERY with no callback/stack response pointer, and uses checked-ID allocation.
The ordinary SDK reader path remains unchanged.

Core admission accepts only the tagged reviewed query shape. Private send
checks the serialized query against the snapshot, rechecks the active record,
and validates the full response tuple in both checked receive branches. After
transport consumes the message, only saved locals/adapter state are inspected.
Successful ACK must be followed by message/TX-done drain, a late peer check,
context check and the same record/ticket/generation match. Only then is that
record retired and exactly one unresolved effect decremented. Caller output is
written synchronously after successful return; RX never receives its pointer.

Host ASan/UBSan evidence:

- Actual direct PCI helper with SDK EVENT_RXD: correct full 32-bit tuple, all 12
  individual byte mismatches and duplicate completion: PASS.
- Extracted locked branch: RF tuple mismatch, boot/MAC compatibility and stale
  ACK retirement checks: PASS. Intentional retirement-bypass control still
  reproduces wire ambiguity; no host-generation nonce claim is made.
- Actual RF write/read builders, owner/private transport, SDK initializer and
  extracted core admission gate: write→query→one-proof retirement, duplicate
  query refusal, next generation, wrong value/address, late generation/peer
  drift, timeout/output retention, and preservation of MAC unresolved count:
  PASS. Hardware/ACK transport and waits are injected, with the real byte parser.
- Complete generated SHA inventory: PASS. Temporary candidate (~14MB) and
  executables were automatically removed; older unfinished inputs preserved.

CI peer82 stages this layer and existing expanded fixtures. Target compilation
and runtime acceptance are pending. This connects RF proof only: MAC readback,
other configuration protocols, checked-ID budget/epoch lifecycle, mandatory
owner init/error binding, normal data promotion and repeated opens remain.
The outer bootstrap init gate stays closed; no router operation was performed.
