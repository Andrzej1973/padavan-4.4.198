# ON failure recovery before Main UP

`radio-on-owner.c:wr_iot_radio_on_step` now handles non-shutdown generation
failure and pre-UP retained state through
`radio-on-restore.c:wr_iot_on_restore_preup_recover`.
The existing generation recovery verifies the retained OFF receipt, current
profile ownership and fresh physical DOWN before restoring journalled bytes.
RAM OFF is attempted once and independently read back before root cleanup.
Cleanup preserves the original OFF receipt, wipes captured credentials and
releases the existing signal fence. Return -1 means cancelled, never ON success.

Possible Main UP, owned children, handoff, foreign inode or stale DOWN evidence
prevent this recovery. No post-UP rollback, MCU ACK change, reset or retry loop
is introduced. Foreign profile replacement remains owned and retained for
explicit recovery rather than being overwritten.

The registered actual-root fixture covers partial output, invalid output and
foreign inode. Existing owner fixture covers RAM-state failure; cancellation
and post-handoff shutdown regressions pass. Separate prepared C11 units pass.
These use injected SDK/backend boundaries. Target build, final image and device
acceptance remain unverified. Public physical OFF/ON binding remains disabled;
cold/desired-IoT-OFF lifecycle and post-UP failure handling remain open.

## Generation result contract

The restore controller formerly treated any nonzero generation result as
readiness. Generation returns -1 when rollback restored the baseline; this
incorrectly advanced to MAIN_START and could invoke RAM ON despite cancellation.
Both parent transitions and Main admission now require exactly 1. The new
`check-radio-on-restored-result.py` failed before the change and passes after:
six direct parent ticks after partial generation leave the profile RESTORED,
RAM ON calls zero, Main UP zero and no Main owner. This tests the parent directly,
independent of root interception. The full-suite process and temporary log were
lost across an environment transition; no full-suite pass is claimed for it.

## Capture-only refusal

If generation begin refuses after admission, the parent may own a RETAINED
restore with no generation owner. The root now permits capture-only cleanup
in this exact state. It requires no Main/Guest/service/multicast/WAN/terminal/
child owner, no radio write attempt, no generation admission or handoff, and
reuses unchanged-profile/original-OFF-receipt/fresh-RAM-OFF/DOWN validation.
No generator or RAM write is retried. A failed unmask retains ownership.
The new registered capture-refusal fixture checks stale proof, changed file,
RAM not OFF, unmask retry and real deferred SIGTERM after root cleanup.

The full registered suite passed on a1502a1a before this patch was applied.
Focused capture/cancel/owner and separate prepared C11 checks pass afterward;
this distinction is preserved in the evidence.
