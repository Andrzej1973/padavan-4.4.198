# WR1200JS checked MAC readback — host evidence

Source package follows 341726aebd805cb99ba8da76b4182a2c86259f01.
Candidate generated from retained close-ack-order input through every layer in
ci-compile-merged-candidate.sh, ending mcu-config-mac-read. All inventory hashes
match manifest; production_installed and target_compiled remain false. Outer
bootstrap startup refusal remains closed.

Passed under GCC ASan/UBSan:
- check-mcu-config-result.py: exact LE MAC record and envelope.
- check-mcu-config-transport.py: actual SDK MAC read/write builders, SDK message
  initializer, extracted raw admission gate and owned transport; exact MAC
  retirement, retained RF effect, wrong type/address/value/generation/peer,
  timeout/output retention, duplicate refusal, next generation, invalid Num/null.
- check-mcu-rx-direct.py: actual direct RX branch, all12 record byte mutations,
  wrong direction and duplicate completion.
- check-mcu-checked-sequence-retirement.py: actual locked RX branch, record byte
  mutations, wrong direction, no successful old ACK across30 allocations,
  checked-pool exhaustion without reuse.
- check-mcu-ack-epoch-gap.py: expected negative controls still demonstrate why
  host-only reset or15-slot reuse cannot establish firmware ACK epochs.
- check-mcu-boot-result.py: existing checked bootstrap handling remains valid.

New wrong-direction test initially failed: SET write status could accept a
MAC-query-tagged response. Both RX write-decoder predicates now reject that
query tag; repeated tests pass. Transport/locks/ACK delivery are injected in
host fixtures; this does not establish real PCI/DMA concurrency or device proof.

Cleanup: temporary generated candidate trees (~14MB each) and sanitizer binaries
removed by TemporaryDirectory. Retained input for unfinished IoT remains needed.
No router commands, target build, image acceptance or runtime acceptance claimed.
