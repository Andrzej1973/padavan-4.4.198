# Timer research checkpoint published for shared review

Date: 2026-10-30. Executor: Sol. Base: 81122cd.

This checkpoint contains only authored experimental timer helpers and their
standalone host tests in tools/iot:

- timer-task-owner.h and check-timer-task-owner.c;
- timer-os-join.inc and check-timer-os-join.c;
- timer-checked-join.inc and check-timer-checked-join.c.

These files are NOT bound into the production driver or firmware. They require
the caller to own the timer, queue, adapter and module lifetime. The fence,
adapter fields, initialization and worker integration are separate unpublished
candidate work. Do not include these fragments in production independently.

## Verification performed for this publication

Seven host variants passed with GCC, C11, -O2 -Wall -Wextra -Werror:
owner; OS native/ABL crossed with legacy/KTHREAD; checked join direct/task.
Kernel timers, execution context, queue operations and waits are mocked.
The test includes use the wr-iot- prefix: copy the two .inc files to an isolated
test include directory under those names, and include tools/iot as well.
No production or target build, Linux scheduler/deadlock test, firmware image
acceptance, CI result or router runtime success is established by these tests.

Only the task wait is capped at 5000 ms. del_timer_sync has no timeout; the
whole operation must not be described as bounded.

## Next work and retained local changes

Prove exclusive failed-peer ownership and reset/delete serialization before
binding cleanup to the join API. The newest reset preflight work is still local
and not accepted as an atomic reset transaction. DMA/TxS, old timer reuse and
partial hardware recovery remain open. IoT is not release-ready.

The broad dirty working tree, candidate preparers, vendor-source scratch trees,
generated executables, private diagnostics and unrelated edits are preserved
locally and intentionally excluded. PROJECT_STATUS.md and CODEX_HANDOFF.md have
additional local details; their newest sections are not all published by this
checkpoint. Existing published history is preserved; no force push is used.
