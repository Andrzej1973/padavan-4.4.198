# IoT v41 MBSS close ticket wake — isolated candidate

After successful target compilation in firmware #627, source review found that `tools/iot/mbss-close-checked.inc` retired a successful MBSS `CLOSE` or `BSS_CLOSE` ticket with `wr_iot_radio_finish` but did not wake `wr_iot_ticket_wait`. `tools/iot/radio-ticket-wait.inc` requires every successful ticket retirement to wake this wait queue. The main-stop path can wait for a busy ticket and then recount references; without a wake it may needlessly wait until timeout even though the MBSS close finished.

The candidate now calls `wake_up_all(&ad->wr_iot_ticket_wait)` after releasing `wr_iot_transition_lock` and before dropping the module pin. It does not wake on incomplete/uncertain close, because those paths retain the ticket for recovery. The virtual caller coverage gate requires exactly this post-unlock wake on the checked MBSS path. The v40 direct-call expectation remains unchanged.

Local verification: freshly regenerated v40 and v41 isolated trees both passed `check-virtual-if-call-coverage.py`; the v41 gate rejected fixtures with the wake removed or moved before unlock. Python syntax and scoped diff checks passed. No target build has compiled these new bytes yet. Recovery owner, adapter lifetime/PCI release and beacon DMA/TxS quiescence remain unbound; this is not an image or router acceptance result.
