# IoT MBSS opening: readiness revalidation gap

Scope: isolated MT7603 candidate only. The optional MIPS module build in
run `40077253251` passed, but it did not prove a live IoT BSS opening.

`tools/iot/mbss-open-admission.inc` takes `wr_iot_transition_lock`, checks a
published idle interface record, obtains a `WR_RADIO_BSS_OPEN` transition
ticket, reserves the interface reference, releases the lock, then directly
calls `wr_iot_mbss_open_raw(pDev)`. It never calls
`wr_iot_mt7603_main_config_observed()`. Thus its `main_ready` bit can reflect
an earlier VERIFY observation rather than the actual main 2.4 GHz netdevice,
beacon request and ARB_BCNQCR0 state immediately before the raw open.

The observer in `tools/iot/mt7603-main-observe.h` already checks the MT7603
chip, adapter startup/interrupt and halt/reset/radio flags, main `netif_running`,
main beacon request, candidate IoT interface down, and the relevant queue
control bits while holding `BcnRingLock`. It is a configuration observation,
not an RF/client or TxS retirement proof. Calling it inside the transition
spinlock would introduce an unreviewed nested lock acquisition. Calling it
before taking the transition ticket would leave the same time-of-check race.

Required candidate change before production binding:

1. Reserve the transition ticket and interface reference under the shared
   short transition lock, as now. While that ticket excludes every participating
   close/reset/open mutator and adapter/netdevice lifetime is pinned, call the
   observer outside the transition lock.
2. Reacquire the transition lock, compare the ticket serial/epoch and current
   close/reset/retire intent, and refuse raw open if either the observation or
   ownership is stale. Abort the reserved interface reference without claiming
   a vendor UP reference. Keep an uncertain state if any mutation occurred.
3. Only then call the raw open while retaining the exclusive ticket; complete
   it using actual hardware/readback evidence. A successful software return
   alone is still `UNVERIFIED`.
4. Bind **all** relevant physical and virtual open/close, reset, watchdog,
   manual radio and teardown paths to the same owner. Otherwise a path outside
   the protocol may race after the second check, so the wrapper alone cannot
   establish atomic readiness. Review lock order with `BcnRingLock` and IRQ
   context before target compilation.

The existing sequential `check-radio-transition.c` host fixture passed with
`gcc -std=c11 -Wall -Wextra -Werror`; it verifies ticket bookkeeping, not
driver integration or the above interleavings. No driver source, firmware,
router state or runtime setting was changed in this audit.
