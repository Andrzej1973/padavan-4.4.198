# Checked multiple-register write response — 2026-11-06

SDK MAC/RF multiple-write callbacks read a LE status at payload offset20 in a
32-byte response and only log errors. The isolated result layer validates the
reviewed command/event enum values, callback layout and builder response size
before installation. It adds a bounded result decoder to both checked receive
branches (generic locked branch and direct allocation-free PCI entry).

Success requires command/extension and event/extension 0xed/0x0e, SET direction,
32 payload bytes, matching actual/wire/header lengths, non-NULL payload and all
four status bytes zero. Payload arithmetic rejects overflow and short packets
before dereference. Query responses cannot masquerade as write acknowledgments.
Sequence matching and duplicate completion remain in the existing dispatcher.
No generic callback or allocator is invoked by the new checked result branch.

Host ASan/UBSan evidence:

- Generated candidate header: status bytes, envelope/direction, length/null and
  overflow cases: PASS.
- Actual direct PCI helper with SDK EVENT_RXD layout: firmware failure status,
  query refusal and duplicate completion: PASS.
- Extracted checked branch: successful/failed write, query refusal and wrong
  sequence: PASS; boot/radio result tests also pass.
- Checked-ID retirement still rejects an old successful ACK across 30 allocations.
  Intentional bypass negative control still reproduces the 15-slot reuse gap.
- Complete generated inventory and protocol anchors: PASS. After adding layout
  anchors, regenerated parser/direct/retirement checks passed again.

The layer changes decoding for already checked messages. It does not mark SDK
configuration commands checked, admit a new sender, invoke the configuration
owner or open data. Those changes still need owner-scoped factory/send routing,
asynchronous/no-response handling and a safe checked-ID budget/epoch policy.
Do not clear retirement/quarantine to permit more than 15 checked allocations.
Target compile and runtime remain unverified. The peer82 CI recipe stages the
layer and fixtures. Temporary candidates (~14MB each) and executables were
automatically removed; no new scratch was retained.
