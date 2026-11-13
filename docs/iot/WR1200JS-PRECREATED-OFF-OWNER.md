# Experimental normal-OFF owner

`tools/iot/precreated-stop.c` composes the existing CLOSE controller, owned
disable snapshot, quarantine, DHCP/DNS and bridge operations. It is staged
for compilation, with no runtime entry point bound. Caller must use the
serialized RC worker outside signal context and retain the context.

Begin captures the current network baseline under the service guard. Steps
retain the original successful ON nonce and identity. An uncertain CLOSE is
never resubmitted; progress and release use that same receipt. Subsequent
network phases require fresh matching CLOSED configuration and close serial.
A failed phase retains its state and guard; cancellation is permitted only
before a possibly submitted CLOSE. Network commit releases the guard last.

This implements software sequencing, not RF/FIFO or client acceptance. It
requires the immutable experimental no-host driver. Production ON admission,
shutdown fencing and activation dispatch remain unbound. Main/Guest, firmware
ACK protection and DMA packet release owners are unchanged.

Host checks inject external resource operations. Prepared native compilation,
MIPS compilation, full image validation and physical runtime are separate gates.
See `docs/evidence/WR1200JS-PRECREATED-OFF-OWNER-2026-11-13.json`.

The experimental recovery-only query15/reply16 exposes a CLOSE-admissible
configuration token even when the first beacon wait did not complete. It is
a distinct type from normal ON query11/reply12. The normal acceptance gate
remains strict. CLOSE_BEGIN now uses recovery observation, then CLOSE itself
revalidates the same receipt. Poisoned or stale contexts remain refused; this
does not implement startup baseline rollback or grant RF acceptance.
