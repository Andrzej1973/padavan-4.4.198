# Shared close executor53 — local host evidence

Predecessor: `.iot-local-check/peer-legacy-close52-20261030`.
Prepared candidate: `.iot-local-check/peer-close-executor53-20261030`.
`prepare-peer-close-executor.py` pins the four changed predecessor files by
SHA256, copies to a new directory, adds adapter-owned executor state initialized
only on allocation, and wraps both legacy and checked close bodies.

The executor uses MacTabLock only for short state access. It remains reserved
while the body runs without that lock. A partial checked close retains its
serial and admits only a matching retry. A rejected initial ticket with no body
effects releases the new reservation; an invalid retry cannot release prior
partial work. A partial legacy close is retained. Main-open dispatch checks the
same executor under MacTabLock, blocking both running and retained close.

Actual checks run successfully with Windows host GCC:
`-std=c11 -O2 -Wall -Wextra -Werror`:

- `check-peer-close-executor.c`: competing lanes, duplicate execution,
  wrong-serial completion, matching retry, retained failure and initial rejection.
- `prepare-peer-close-executor-check.py`: extracts both candidate close bodies
  and their wrappers; injected competing calls during teardown are refused;
  management-join failure retains the checked owner; matching retry completes;
  legacy partial failure blocks both paths; completed legacy close is idempotent.
- `prepare-peer-open-dispatch-check.py`: extracted internal ioctl case rejects
  running/retained close and preserves the prior legacy/reopen checks.
- Python AST parsing passed for the three preparer/check scripts used above.

The fixtures model locks, adapter layout, APShutdown, management tasks, hardware
and resource release. They are deterministic interleaving checks, not threaded
kernel tests. No MIPS/OS_ABL target compilation, full preparer replay, firmware
image verification, DMA/callback retirement or router runtime was performed.

Remaining work includes coherent serialization with all radio reset/admission
paths, an adapter-release claim that prevents freeing these locks while any
owner/callback survives, full composed regression and target compilation.
RTMPFreeAdapter currently frees MacTabLock directly; a completed software close
does not establish the prerequisites for freeing the adapter. Stages51–53 are
local candidates and have not been added to the consolidated chain. No router
changes, build dispatch, commit or push in this step. Sol remains sole writer.
