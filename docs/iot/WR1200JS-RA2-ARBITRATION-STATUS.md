# WR1200JS ra2 association / GTK arbitration

The complete source composition is enabled in the **isolated peer82 candidate**.
It is not installed on the router and does not enable the production RC image.
MIPS compilation of this new composition, image verification and physical
runtime acceptance are pending.

Implemented composition:

- Association/reassociation and both authentication callbacks own a balanced
  outer reservation before their first native mutation.
- Public ra2 station insertion participates through the complete existing
  table transaction, including the private insertion/tail outside MacTabLock.
- Requested and periodic GTK writers exclude those association actors using
  the same adapter-local owner and existing control-user lifetime admission.
- The periodic writer reserves exact current ra2 peer generations under
  MacTabLock and an existing table transaction; it releases the lock before
  native crypto, timer cancellation, handshake and key-write operations.
- Busy admission preserves native rekey countdown/counters. The natural
  repeating timer owns retry. Refusal does not reset or scan the radio.
- Release validates its ownership. Drift retains foreign reservations and
  poisons future admission instead of silently releasing another actor.

Host tests execute the actual periodic vendor callback and group-request block
with real ownership predicates and explicit SDK boundary actors. Direct/OS_ABL,
feature-disabled/native pass-through, refusal, release faults and mutation
negative controls pass. The source checker validates exact generated wrappers,
helper fragments and insertion include against the final prepared tree.
These tests do not emulate firmware, DMA, IRQ completion or physical clients.

No ACK reuse, stale-ACK protection or radio timing is modified. Main/Guest
mutation paths pass through the native body. Table transactions temporarily
exclude native deletions globally; full device-level noninterference is not
claimed from host tests. Optional direct station mutators and complete WPA
lifetime coverage still need review. Firmware ACK, TxS/DMA ownership, safe
OFF/reopen, isolation/image/release gates and all four final firmware variants
remain part of the original unfinished project objective.
