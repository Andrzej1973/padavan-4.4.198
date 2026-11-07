# IoT tasklet submission owner: publication boundary

Published scope: `tools/iot/tasklet-schedule-owner.h` and its standalone
`check-tasklet-schedule-owner.c` host test. This is an experimental model,
not production driver integration. All accesses require one external shared
IRQ-safe lock. The counter covers calls to the scheduling API, not callback
execution; real callback joining and adapter lifetime remain caller duties.

Verified on Windows on 2026-10-30 with MinGW GCC:

```text
gcc -std=c11 -O2 -Wall -Wextra -Werror tools/iot/check-tasklet-schedule-owner.c -o <local-output.exe>
<local-output.exe>
```

Compilation and assertions passed. Cases include blocked admission, submission
drain, reopen prerequisites, nested submissions and counter overflow/underflow.
This sequential host model does not prove kernel concurrency, target ABI,
firmware image contents or device operation. No router changes were made.

The existing published parent is `9cb154a37a08d44331022f88312930838ecf841e`.
Other accumulated changes, generated vendor trees, binaries and firmware
artifacts remain outside this publication. In particular, isolated driver
candidates 67–69 still require composition, lifecycle review and target
verification before production acceptance. IoT is not release-ready.

Sol remains the single writer. Continue from the local PROJECT_STATUS.md and
CODEX_HANDOFF.md without discarding their uncommitted history. This report is
the portable scope record for this small publication; it does not claim that
the remaining local work is present on GitHub.
