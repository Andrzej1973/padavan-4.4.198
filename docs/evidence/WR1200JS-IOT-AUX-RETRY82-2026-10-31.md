# WR1200JS IoT auxiliary retry scheduler 82 — host evidence

Date: 2026-10-31. Scope: source audit, candidate composition and extracted
host control-flow tests. No target compiler, firmware image or device runtime
was established by this evidence.

## Worktree and role checkpoint

DeepSeek accepted the single-writer role in `docs/EXECUTION-ROLE.md` after the
local and remote branch both resolved to `13ce368`. The working tree already
held 71 modified tracked files and 467 untracked entries. Existing work was
preserved; no bulk stage, clean, reset, commit or push was performed.

The audit classified the unfinished tree as:

- 333 untracked `tools/iot` entries: candidate generators, strict fixtures,
  source auditors and experimental headers;
- 133 untracked evidence files plus runtime/donor audit records;
- local-only build, monitor, artifact and scratch directories;
- 71 tracked modifications containing the continuing IoT and WebUI work.

Four untracked source auditors were stale for the current candidate shape and
were corrected: peer reopen/unwind, peer table writers, peer timer arms and TR
insertion readiness. The repaired TR source-order audit reports ready while
retaining its explicit concurrency/lifetime limitation.

## Candidate 81

A fresh composition from `.iot-local-check/full-driver-overlay4-20261029`
completed through the direct APCLI/Monitor exact-ticket retry stage. The full
host suite then passed 85 variants in
`.iot-local-check/full81-host-composition-20261031/result.json`.

This established same-ticket continuation after a proven unmutated auxiliary
DOWN failure, without replaying family close or HNAT effects. It did not yet
provide automatic scheduling or lifetime ownership.

## Candidate 82 scheduler binding

`prepare-aux-family-retry-scheduler.py` adds an isolated scheduler with these
properties:

- APCLI and Monitor close paths queue work only after the owned close returns
  `-EBUSY` and the exact record remains in `WR_FAMILY_DOWN_RETRY`;
- `dev_hold` occurs before queueing, while adapter release is fenced by a
  deferred-owner count;
- the original ndo_open module pin remains held until the exact-ticket retry
  succeeds;
- successful retry marks completion under the same adapter transition lock
  that consumes the ticket, before module-reference release and before slot
  reuse;
- the worker acquires RTNL and calls only the exact-ticket family retry; it
  never calls `dev_close`, repeats `APC_CLOSE`/`SNIFF_CLOSE` or replays HNAT;
- PCI stop/probe paths flush or join the auxiliary work, and adapter release
  additionally requires both an empty deferred-owner count and
  `!work_busy(aux_work)` so the adapter cannot be freed while the callback is
  still returning;
- failed or canceled work remains retained and deliberately blocks adapter
  release; no successful completion is invented from a canceled callback.

The standalone model test
`tools/iot/check-aux-family-retry-scheduler.c` passed strict GCC C11
`-Wall -Wextra -Werror -O2`. It covers stale generation/serial/epoch/token,
double action refusal, rejected scheduling, stop/abandon, joined completion
and the adapter-release fence.

`tools/iot/audit-aux-family-retry-scheduler.py` passed its source-order audit
for the actual candidate bindings. Report:
`.iot-local-check/audit82d-aux-family-retry-scheduler.json`.

## Reproducibility and replay

`prepare-peer-retirement-chain.py` now includes
`aux-family-retry-scheduler` as the final stage. A fresh chain was generated at
`.iot-local-check/peer-retirement-chain82-20261031`.

The fresh final candidate and the incrementally tested scheduler candidate each
contain 585 files; SHA256 comparison found zero file differences. Therefore
the following host results apply to the fresh bytes:

- full composition passed 86 extracted variants in
  `.iot-local-check/full82e-host-composition-20261031/result.json`;
- focused scheduler/adapter/PCI replay passed 6 variants in
  `.iot-local-check/aux-retry82-fresh-replay-20261031/result.json`;
- `python -m compileall -q tools/iot` passed;
- `git diff --check` reported no whitespace errors.

## Remaining limits

- No MIPS target compile, kernel link, ROMFS/image check or CI run was made for
  candidate 82.
- RTNL/workqueue ABI and every feature configuration remain uncompiled.
- Callback, timer, tasklet, IRQ and DMA quiescence remain outside this
  scheduler's proof.
- Canceled or failed work has no automatic reaper and intentionally retains
  all resources.
- Completion-after-DOWN reconciliation, first/last auxiliary physical
  ownership, final child/root/PCI release and router runtime still require
  separate evidence.
- No router state was changed, and no flash, reboot, commit or push occurred.
