# Owned firmware completion receipt — 2026-11-06

Isolated Method1 now commits a software receipt only after CmdFwStartReq returns
success and the RUN poll observes a valid, non-all-ones value. The private
builder uses the checked sender and FW_START response handling; this receipt
adds ticket/epoch provenance rather than replacing ACK validation.

The receipt checks peer/context, completed hardware actors, FW_RUN_TIME,
retired-boundary epoch, drained sender/messages, ledger, device flags and
unfrozen constructors. Under transition → sender locks it records radio serial
and epoch, freezes private constructors, then publishes receipt state2. No
further private restart/scatter can invalidate the stamp after publication.
Allocation alone initializes the fields. Duplicate or stale commits refuse.

Scheduler claim/owned/finish now require receipt state2 for the current radio
serial/epoch. Claim accepts the freeze handed over by the receipt. Receipt
failure follows existing Method1 loader-abort before generic SCH cleanup.
Later failed context invalidates use of a retained receipt; it is not reset to
manufacture fresh readiness.

Host evidence:

- Actual receipt body:20 success/failure cases, stale ticket/epoch, duplicate,
  hardware/constructor/ledger/device gates: ASan/UBSan PASS; context/locks mocked.
- Actual Method1: cold/warm start, start failure, RUN timeout/all-ones and
  receipt failure; receipt failure aborts without generic SCH writes: PASS.
- Scheduler owner: missing/stale receipt, ownership/finish and failure gates:
  PASS; leaf hardware checker mocked.
- Complete CI fixture sequence and generated-tree inventory: PASS before final
  constructor handover tightening. Fresh regeneration and receipt/owner/Method1
  plus inventory reran PASS after that change.

The peer82 CI recipe includes the layer and receipt fixture. MIPS compilation
of this change is pending. MCUSysInit scheduler invocation, normal command
policy and sender/data promotion remain unimplemented; existing bootstrap-init
refusal stays. This is neither production inclusion nor runtime acceptance.
Temporary candidates (~14MB each) and binaries were automatically removed;
unfinished prior inputs remain retained.
