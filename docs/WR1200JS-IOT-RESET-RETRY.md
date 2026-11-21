# Deferred reset retry: evidence and limits

Beacon recovery holds the lifecycle active_tx lease until its wrapper returns.
The generated wrapper fixture injects reset intent inside the vendor-body call:
reset admission fails while the lease is held, remains pending, and can be
explicitly admitted after release. This does not itself schedule reset.

The periodic command tail in common/rtmp_init.c attempts reset drain after
control admission is released, including when the periodic command body was
denied. The timer callback enqueues CMDTHREAD_MLME_PERIOIDC_EXEC; enqueue wakes
the command worker only after successful insertion. Allocation failure or a
closed queue can lose an individual tick. Actual callback/enqueue tests verify
that a later successful tick still queues and wakes. They also compile the
actual terminal-owner predicate: after terminal close, later ticks cannot
resurrect the queue even when its insertion-state bit appears open.

Host fixtures inject allocator, queue, locks and wake primitives. They do not
prove timer delivery, worker liveness, bounded RTNL availability, firmware ACK
behavior or hardware reset completion. The command drain uses rtnl_trylock;
contention preserves intent but no bounded success is claimed. Raw VOID reset
return never establishes radio readiness.

Evidence: evidence/WR1200JS-IOT-RESET-RETRY-2026-11-08.json and
WR1200JS-IOT-RESET-DELIVERY-2026-11-08.json. Current tests run against the final
generated API candidate; source inspection records identify the retained
predecessor where applicable. The new periodic checker runs in peer82 CI.

A PM completion/resume binding gap is recorded separately in
WR1200JS-IOT-PM-BINDING-GAP-2026-11-08.json. The successful 8f5c5c7 target build
has CONFIG_PM and CONFIG_SUSPEND disabled, confirmed from its archived effective
kernel config. That inactive path is not evidence of the current IoT blocker.
Do not enable PM or clear lifecycle fences as an attempted workaround.

The actual beacon callback negative test still demonstrates that an uncorrelated
report can mutate a reopened BSS state. This is a conditional software witness,
not evidence that hardware delivered a duplicate. RF/FIFO/late-TxS retirement,
safe reopening and the owning RC controller remain required before acceptance.
