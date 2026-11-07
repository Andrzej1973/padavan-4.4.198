# IoT RC dispatch and signal ownership — source audit, 2026-10-29

Scope: pinned Padavan RC source in the local prepared candidate
`.iot-local-check/rc-quarantine-20261027/trunk/user/rc/`; no firmware or
router operation was performed.

`init.c::catch_sig_event` handles SIGUSR1 by setting the `sig_usr1_received`
flag. The PID 1 main loop later clears the flag and calls
`handle_notifications()` synchronously (`init.c`, around lines 120–137 and
493–505). `rc.c::handle_notifications` walks notification markers and invokes
handlers in that call (`rc.c`, around lines 859–889). The candidate
`prepare-control.py` inserts `wr_iot_rc_dispatch()` into this branch.
This supports one sequential notification consumer within PID 1; the
mailbox's RUNNING record separately prevents a second claim of the same
request. It does not prove that all radio/network writers use the IoT lock.

`init.c::catch_sig_fatal` instead calls `shutdown_router()` directly from
the fatal-signal handler (around lines 83–111). `signals_fatal` includes
normal shutdown SIGTERM/SIGQUIT, SIGPWR, and process faults such as SIGSEGV
and SIGBUS (`init.c`, around lines 50–62). That path is not queued
through `handle_notifications()` and can interrupt an in-progress IoT
activation or recovery. The shutdown path stops Wi-Fi and other services.
Consequently the single RC event loop is insufficient evidence for safe
activation or adapter lifetime. A production design must arrange a common
teardown admission/cancellation protocol, including this signal path, and
prove its behavior before shipping the IoT backend. A blanket signal mask
would suppress process faults and a long-lived mask could prevent reboot
when a backend blocks; neither is a reviewed solution. Deferring normal
shutdown would also need to preserve reliable reboot. No such change was
made in this audit.

The host-only activation candidate's post-lock generation check is defense
against stale logical requests under a serialized caller. It is not a
concurrent C memory-safety mechanism or a substitute for signal/driver
transition ownership. The RC transport remains a candidate and the strong
`wr_iot_activation_execute` backend remains absent.

## Isolated normal-shutdown admission candidate

`tools/iot/rc-shutdown-admission.h` now supplies a PID 1 `sig_atomic_t`
transaction marker and first-pending-signal slot. `prepare-control.py` stages
an early `catch_sig_fatal` hook for WR1200JS only. When the control server is
inside `wr_iot_rc_dispatch`, SIGTERM/SIGQUIT are recorded; after mailbox
result publication and cleanup, the server clears
its marker and re-raises the saved signal to the original handler. Signals
outside the transaction, SIGPWR, and process faults retain the stock path.
The hook performs only `sig_atomic_t` accesses in signal context.

The standalone host admission test passed with strict C11 GCC on Windows.
The extracted dispatch fixture passed with injected mailbox/backend and an
actual host SIGTERM delivered inside the backend: it remained pending until
the dispatch returned, then reached the test handler. The Linux CI
control-channel test also injects SIGTERM from
the backend and checks that delivery occurs after dispatch; that edited CI
has **not** run. The preparer and source checker now cover the generated
`init.c` hook and server/header identity; their full generated-source check
also awaits Linux CI. No production image contains this candidate.

Follow-up local check: `prepare-http.py` and `prepare-control.py` both passed
on a disposable fixture assembled from the pinned RC source and local HTTP
source. The HTTP Makefile in this fixture was a minimal anchor stub, so this
does **not** validate the real Makefile object selection or target compile.
The shutdown marker's `end()` was corrected to clear `active` before reading
the pending slot: a signal arriving at the end now either gets recorded
before that transition or takes the stock handler after it, instead of being
cleared unseen. Strict C11 host admission and injected dispatch tests passed
again after this correction. Linux signal timing and device behavior remain
unverified.

The source identifies `sys_exit()` as SIGTERM and `sys_stop()` as SIGQUIT.
SIGPWR is installed in the fatal-handler set but has no equivalent normal
RC command entry. The candidate excludes SIGPWR from deferral: a power event
must not wait for an activation backend. This preserves its stock immediate
behavior, which can interrupt activation; fail-closed recovery after that
interruption remains a production gate. The host check asserts SIGPWR is not
admitted when the platform defines it.

The extracted dispatch fixture now has separate SIGTERM, SIGQUIT and SIGPWR
injection cases, guarded by each host's available signal constants. On
Windows the strict C11 fixture passed the SIGTERM case; the Linux-only
SIGQUIT/SIGPWR branches require the existing CI job. The SIGPWR test handler
is an observation stub and does not emulate `shutdown_router()` teardown.

This deferral does not guarantee timely reboot if the future activation
backend blocks. Before production binding, prove bounded operations and a
cooperative cancellation path for pending shutdown, then target-compile the
generated RC and exercise SIGTERM/SIGQUIT/SIGPWR against an activation in
progress. A process fault still invokes stock fatal teardown and must be
recovered fail-closed on the next boot. Driver transition and TxS retirement
proofs remain independent gates.
