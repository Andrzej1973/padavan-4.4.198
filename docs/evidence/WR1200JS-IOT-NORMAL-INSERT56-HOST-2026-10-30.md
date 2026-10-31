# Whole public insertion56 — local candidate

Source inspection of candidate55 `mgmt/mgmt_entrytb.c` confirms insertion's
last MacTabLock release precedes `rtmp_tx_burst_set(pAd)` and the final return.
Deletion also releases MacTabLock before TX-burst/protection/capability tails.
Consequently the entry-lock critical section alone cannot cover these tails.

`prepare-peer-normal-insert.py` pins the actual management source SHA256 and
replaces only the public MacTableInsertEntry wrapper with
`wr-iot-peer-normal-insert.inc`. It checks executor idleness and enters the
existing synchronous table transaction count atomically under MacTabLock,
calls the unchanged private vendor insertion body, then leaves the count after
that body returns, including its unlocked tail. The explicit startup-WDS API
remains under its own startup ticket/lease. No lock spans the vendor body.

Candidate `.iot-local-check/peer-normal-insert56-20261030` was generated from55.
Strict GCC C11/O2/Wall/Wextra/Werror checks passed:

- New public-wrapper fixture: nested count balance, failed insertion balance,
  reset/table-owner refusal before body, invalid input, count still active in
  simulated unlocked finishing tail. Its private insertion body is mocked.
- Existing extracted private peer-ready publication ordering check.
- Existing explicit startup insertion admission/lease check.

Results: `.iot-local-check/peer-normal-insert56-targeted/result.json` (3 passed).
This does not prove actual vendor tail/hardware execution, kernel concurrency,
target ABI, adapter lifetime or slot-reuse safety. Ordinary deletion is still
open. Its existing gate refuses normal deletion while the transaction count
is nonzero; blindly wrapping deletion with that same count would self-reject.
Reset-owned deletion must preserve its exact table serial instead.

Step56 is added to the preparer chain, but no fresh full55/56 replay has run.
Latest full replay remains54. No target/firmware build, router changes, manual
dispatch, commit or push in this step. Adapter release remains open.
