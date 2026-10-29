# Peer retirement candidate checkpoint — 2026-10-29

This checkpoint publishes independent candidate preparation/extraction tools
and the OpenRouter participant rules. It does not install a production driver.
The current executor remains Sol. Broader dirty IoT, CI, profile and WebUI
work stays local and must be preserved by the next executor.

## Published candidate tools

- `prepare-uapsd-delete-join.py` and `uapsd-retire-queues.inc`: exact-pinned,
  deletion-only queue join; a failed join retains a disabled entry without
  a recovery owner. Input must already contain the reviewed admission fences.
- `prepare-uapsd-delete-join-check.py`: extracts actual deletion admission.
- `prepare-uapsd-eosp-release.py`: repairs three stale EOSP pointers on
  enqueue-failure early returns; its input is the reviewed deletion candidate.
- `prepare-uapsd-eosp-release-check.py`: extracts those rejection tails.
- `prepare-uapsd-lookup-reuse-check.py`: witness showing address lookup alone
  cannot distinguish an old completion after same-address reassociation.
- `check-uapsd-retire-queues.c`: queue detachment/release contract test.
- `audit-peer-dma-ownership.py`: lexical packet-slot write inventory; includes
  inactive/comment/RX sites, not an active target callgraph.

## Actually observed local evidence

Strict C11 GCC `-Wall -Wextra -Werror -O2`: deletion admission passed with
and without UAPSD; three EOSP failure tails and queue helper passed. Extracted
lookup witness passed. Eight host variants passed on the larger locally
composed candidate (including reset, insertion and dequeue tests), but that
larger chain is not part of this publication and is not a reproducible target
build from this checkpoint alone. Local DMA inventory: 76 lexical writes in
six C files, of which 63 clear slots. No proprietary source copies, firmware,
private logs, generated source or device configuration are included.

## Acceptance still open

Software-generation/completion identity or a proved drain is required before
WCID reuse. MacTabLock -> irq_lock is already present in deletion; acquiring
MacTabLock in the IRQ-locked DMA completion path would invert lock order.
Two packet owners per descriptor, reset cleanup and hardware TxS/FIFO reports
need independent coverage. TRUE capability publication, failure recovery,
auxiliary interface removal, full prepared-source merge, target compilation,
image checks and authorized runtime acceptance remain open.

No firmware build or workflow was manually dispatched, and the router was
not changed. Pushing this checkpoint may trigger the repository's normal CI;
that outcome must be checked separately from these local results.
