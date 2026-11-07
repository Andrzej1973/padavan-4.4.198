# Tasklet scheduling fence66 — model and expanded inventory

On resume, confirmed full64 preparation finished: 61 preparers, 580 files
byte-identical to incremental64; its full extracted suite passed68 variants.
These were host results, not target or device acceptance.

The draft65 moves tasklet destruction after IRQ release but removes the early
RX drain before MlmeHalt/management teardown. It remains excluded from the
preparer chain. Passing its narrow order fixture did not prove this ordering
safe for the intervening vendor teardown. Preserve early tasklet join and
first fence every producer instead of accepting draft65.

Expanded `audit-tasklet-producers.py` beyond the scheduling macro. Result
`.iot-local-check/tasklet-producers66-expanded.json` has44 lexical call sites
in8 files:36 RTMP_OS_TASKLET_SCHE,2 direct tasklet_hi_schedule,4 schedule_work,
2 schedule_delayed_work. These include generic OS wrapper implementations,
MCU scheduling, recovery work and optional polling work; they are not44
independent active tasklet producers for this board. Effective preprocessing
and object/lifecycle classification remain necessary. The old36-site inventory
was incomplete as an inventory of all scheduling APIs.

`tasklet-schedule-owner.h` models one short shared IRQ-safe-lock owner. A
producer enters before calling the scheduling API and leaves after it returns.
Close blocks admission, waits outside that lock until inflight scheduling calls
drain, then performs the actual early callback join. Reopen requires separately
proven tasklet initialization and prior join. Overflow/underflow poisons
admission. This count tracks scheduling submissions, not running callbacks;
it cannot replace tasklet_kill/cancel_work_sync or adapter lifetime pins.

`check-tasklet-schedule-owner.c` passed strict GCC C11/O2/Wall/Wextra/Werror:
admission-before-block interleaving, nested submissions, refusal to join or
reopen while submissions remain, permanent closed admission until explicit
reopen, and counter corruption. No driver binding is present yet.

Next bind the classified tasklet producer calls and early join to the same
owner without lock-order inversion or waiting under IRQ locks. Keep MCU and
recovery work lifecycles distinct. Then verify all feature/OS_ABL branches
and full candidate composition. No target/firmware build, router change,
dispatch, commit or push. Current chain ends64;65 remains excluded.
