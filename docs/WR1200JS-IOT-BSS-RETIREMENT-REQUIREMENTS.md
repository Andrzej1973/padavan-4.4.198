# IoT BSS retirement: remaining acceptance requirements

The final API candidate remains experimental. Successful standard or peer82
compilation is not permission to bind its configuration-only CLOSED result to
production network cleanup. These requirements supplement the existing IoT
implementation contract; they do not replace Main/Guest/network acceptance.

| Required property | Existing evidence | Missing proof |
|---|---|---|
| Stop new BSS2 beacon builders | producer gate revoke/drain and exclusive builder fixtures | real callback/task execution and MMIO ordering on WR1200JS |
| No host beacon DMA mapping still in use | WrBeaconDmaOutstanding snapshot and DMA-cell ownership checks | hardware completion semantics and ordering, including racing IRQ completion |
| No queued BSS2 beacon can transmit after accepted closure | ARB BCN enable/TBTT config checks; vendor ARB/FQCR0 polling; encoding agrees with upstream fields | authoritative BSS-specific FIFO/filter completion semantics, timeout and read-error behavior |
| Late TxS cannot affect a future lifetime unsafely | callback in-flight ledger; STOP immutability; builder rejects busy/unknown DMA despite stale IDLE | report retirement boundary or validated receive correlation; PID reuse negative witness remains |
| Main and Guest stay available | scoped candidate paths and host fixtures | simultaneous client/traffic/device evidence across repeated IoT toggles |
| RC may release its owned state | nonce/epoch/generation reference checks and configuration-only CLOSED | complete closure receipt plus owned service/network recovery and final observation |

## Exact source boundaries

- tools/iot/mbss-close-checked.inc: stage2 checks software DMA/TxS snapshots;
  stage3 performs virtual down; stage4 consumes the reference and retires the
  transition ticket. This is bookkeeping completion, not an RF receipt.
- tools/iot/mt7603-closed-observe.h: reads queue/TBTT configuration, checks stopped
  BSS and snapshots counters under a generation fence. Its contract explicitly
  excludes RF/FIFO/late-callback retirement.
- tools/iot/driver-api-closed-entry.inc: configuration response is tied to original
  OPEN provenance. Do not reinterpret its flags or operation numbers as stronger
  acceptance. A new receipt needs a distinct documented contract and tests.
- tools/iot/prepare-beacon-txs-ledger-check.py: actual parser/allocator extraction
  reproduces conditional stale PID matching. Local reservation generation is
  cancellation identity, not a generation supplied by firmware in receive data.
- tools/iot/check-txs-builder-composition.py: stale IDLE cannot admit a builder
  while its injected DMA snapshot is busy/unknown. This narrows one software
  hazard; it does not establish an empty RF queue or safe isolation release.

## Evidence needed to choose a safe implementation

Obtain a verified MT7603 E1/E2 description or a reproducible hardware/source
experiment for BSS-specific ARB/FQCR0 completion: which ownership layers have
retired, whether TX status remains queued, and what happens on reset/timeout.
Any report-correlation proposal must show the transmitted field, firmware echo,
receive extraction, wrap behavior and all beacon construction call sites.
Host-only counters, a larger PID pool and an arbitrary quarantine duration are
insufficient substitutes. No firmware command should be invented from register
names or borrowed from another chipset.

If the mechanism is established, implement the smallest scoped close operation
with exact owner identity, lifecycle/filter serialization, terminal uncertainty,
readback/error handling and a typed receipt. Preserve Main/Guest and retain
isolation on every uncertain result. Then compile, inspect the exact image, and
run the existing owner-authorized physical acceptance procedure. Router access
or mutation is not authorized by this document.

Until then: retain the original MCU ROM ACK issue separately, leave ACK safety
unchanged, keep the activation controller unbound, and record IoT as incomplete.
The CONFIG_PM callback binding gap is inactive in the independently inspected
8f5c5c7 WR1200JS configuration; it must not distract from this active BSS gate.
