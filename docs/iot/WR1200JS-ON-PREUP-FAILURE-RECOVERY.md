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
