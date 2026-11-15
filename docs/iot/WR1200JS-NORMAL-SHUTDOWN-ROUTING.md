# Normal router shutdown after IoT ACTIVE

Pinned SDK `trunk/user/rc/init.c:catch_sig_fatal` calls `shutdown_router()`
directly from SIGTERM/SIGQUIT handling. Pinned `rc.c:shutdown_router` stops WAN,
services and then Wi-Fi; failure of a Wi-Fi helper alone does not stop subsequent
LAN teardown. Existing IoT transaction `active/pending` admission delays a normal
signal only while that particular transaction is active. Returning ACTIVE from
a request is therefore not proof that future router shutdown is coordinated.

The cold terminal now rechecks pending signals after child completion, but that
check cannot prove every signal interleaving around the final unmask. General
post-ACTIVE shutdown needs a PID1 process-context route independent of the
current transaction. Signal handlers must not inspect backend structs or invoke
allocation, driver APIs, service locks or backend continuation.

## Inert request slot implemented

`rc-shutdown-admission.h` provides a default-zero normal-route arm and first
requested SIGTERM/SIGQUIT slot, both sig_atomic_t. Existing active transactions
keep their existing pending signal. When explicitly armed, a signal outside
active admission is retained for a future PID1 consumer; a signal replayed by a
completed transaction fence also lands there instead of immediately tearing down
LAN. New ordinary shutdown admission refuses while such a request exists.
SIGPWR and process faults retain their previous immediate path.

The actual signal/fence fixture covers first-request preservation, normal signal
outside admission, signal queued while the outer fence blocks delivery, replay
after its cleanup and another signal after final unmask. The route is not armed
by runtime/boot and no request-acknowledgement shortcut is supplied.

## Required before enabling

1. Retained PID1 controller must claim the routed request without losing a new
   normal signal and must prevent unrelated network/radio notifications.
2. Read the actual independent backend: finish an owned START/STOP, execute one
   owned OFF for ACTIVE, or use a distinct current INITIAL_OFF observation.
3. Transfer exact software CLOSED to the existing physical Main stop lifetime;
   prove AUX/auth drain, ARM/Main completion/RELEASE and PCI/DMA/IRQ joins at their
   actual source/target/runtime levels. Software CLOSE cannot replace this.
4. Release credentials/guards and retire the shutdown controller inside the
   final signal fence. Only then deliberately hand the original signal back to
   the stock shutdown path with routing disabled for that handoff. A fresh signal
   must not resurrect an old completed operation or start a second OFF.
5. Test missing/late/duplicate signal, early and late OFF refusal, stale tuple,
   failed unmask, child uncertainty, Main DOWN failure, device removal and both
   SIGTERM reboot/SIGQUIT halt. Verify user settings and access are retained.

These steps are incomplete. The slot test is not shutdown completion, not
physical RF/DMA retirement and not permission to flash a candidate image.
