# Counted WDS versus reset/close55

Prepared `peer-wds-executor55-20261030` from the verified full54 tree using
`prepare-peer-wds-executor.py`, with exact hashes for the three input includes.
Normal WDS transaction admission checks executor idleness in the same
MacTabLock section that increments the table transaction count. Both close
wrappers check that count before claiming execution. Raw reset additionally
requires ordinary table admission and a zero transaction count under that lock.
No spinlock is held across the body, raw hardware work or cleanup tails.

Three selected strict host GCC checks passed in
`.iot-local-check/peer-wds-executor55-targeted/result.json`:

- Whole WDS transaction wrapper rejects running reset and retained checked close
  without reaching its body; prior nested/balance/failure checks remain.
- Both extracted close bodies/wrappers reject nonzero transaction count before
  APShutdown and leave the executor idle.
- Actual reset fragment preserves its pending request without raw work while
  the count is nonzero; draining after the count reaches zero executes reset.
  Existing contention and failed-ticket-retirement assertions also passed.

Host locks, layouts, APShutdown and hardware remain mocked. This is not a claim
that every ordinary peer insertion/deletion is counted or that every radio
path obeys the owner. Startup ticket paths still depend on their separate
table reservation. Adapter release and callback/DMA lifetime remain open.
The step is added to the preparer chain, but a fresh full55 replay has not yet
run; latest full replay remains54. No target build, image/runtime acceptance,
router changes, manual dispatch, commit or push in this step.
