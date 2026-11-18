# Scoped ra2 GTK timer and pre-admission CLOSE deferral

## Observed gap

Pinned vendor `ap/ap_wpa.c:1044` defines `GREKEYPeriodicExec`. A remaining
`RekeyCountDown` reaches `WPAInstallSharedKey` even with `StaCount == 0` and
without checking whether that BSS is still active. This timer is independent
of the already counted MLME/ioctl paths. Host execution of the actual native
callback reproduces that key-install call with an IDLE ra2 registry entry.
It is a source/host finding, not an observed router failure.

## Counted timer admission

The isolated API producer now wraps only the MT7603/MT_MAC/PCI third-BSS timer.
Main/Guest timers, other chips and disabled feature guards run the native body.
Under the existing transition lock it requires the current active third-BSS
registry/OPEN receipt, first host publication, Main ownership, vendor count,
and no CLOSE/probe/bootstrap/reset/PM/retirement conflict. It increments the
existing `wr_iot_control_users` before unlocking, runs the native callback
outside the lock, then releases the counter through `wr_iot_control_leave`.
No borrowed netdev pointer is dereferenced and no new long-lived reference is
stored. The counter is a participating-transition fence, not an adapter pin or
RF/PCI/DMA/IRQ retirement proof. Existing timer/adapter teardown obligations
remain in force.

CLOSE reservation checks the same counter under the same transition lock.
If the timer is admitted first, CLOSE cannot reserve until it returns. If
CLOSE reserves first, the timer cannot enter its native body. Other counted
actors need not finish before a timer tick; this avoids creating an exclusive
global periodic-worker lock. Counter overflow poisons rather than wraps.

A refused tick leaves the native countdown/key/counter state untouched. The
SDK creates REKEY timers as periodic at `ap/ap.c:264`. Both timer mechanisms
rearm outside the callback: the non-task macro in `include/rtmp_timer.h` tests
Repeat after callback return; the task worker at `common/rtmp_timer.c:175`
tests Repeat/State after calling the handler. The wrapper neither cancels nor
reschedules timers. AP shutdown still performs its existing timer cancellation.
This does not claim to repair or replace all worker/adapter teardown paths.

## Why the CLOSE change accompanies the timer fence

Previously any request ioctl error became UNCERTAIN. A transient pre-admission
EBUSY could therefore put RC into progress-only recovery even though no CLOSE
owner existed. A new counted timer would make that normal race more likely.

The paired kernel/client contract now reserves request EBUSY for refusal before
admission. The kernel reply converts every error after `dev_close` to EUCLEAN,
even if a future netdev implementation returned EBUSY. The RC client recognizes
only an initial CLOSE request's exact `ioctl == -1, errno == EBUSY`, with a
successful fd close, as NOT_SUBMITTED. The existing controller then stays IDLE
and the existing OFF owner can attempt admission on a later bounded step.

OPEN, progress/release EBUSY, EAGAIN, failed fd close, positive unexpected reply
and all post-admission failures remain conservative. Admitted/uncertain CLOSE
is never replayed. Existing guards, successful OPEN identity and network
isolation remain owned while OFF waits. Driver/RC pairing now requires typed
metadata for the new busy contract and timer fence, refusing an old/mismatched
module contract. This is for coherent paired candidates, not independently
installed mixed driver/userspace versions.

## Verification

- 44 admission cases: epoch/nonce/registry/receipt/family/count/PM/teardown
  refusal, concurrent actors, saturation and CLOSE exclusion.
- Actual native timer plus generated wrapper, both feature modes: the original
  closed-countdown witness, refused ticks with unchanged state, accepted work
  outside locks, early-return release, Main/Guest/other-chip pass-through and
  later tick progress. Native key/handshake/MMIO boundaries are actors.
- Actual kernel CLOSE reply, RC client and controller together: busy before
  admission followed by one close; post-admission EBUSY normalizes to EUCLEAN;
  fd-close failure, refused finish and unexpected positive reply never replay.
- Actual OFF owner: two NOT_SUBMITTED ticks retain both guards, then one
  mutation completes existing ordered teardown. Existing uncertain-close and
  network failure fixtures remain covered.
- Pairing/staging strict metadata negative cases, actual common CLOSE dispatcher,
  retained RC backend/edit composition and complete edit/view host suite passed.
  Runtime source preparation passed. Python/YAML/shell/whitespace checks are
  separate from target compilation.

New host checks run in ABI and optional preparation. Optional additionally
compares the actual prepared full `ap_wpa.c` and copied admission header with
the composer output before compiling the module. No new ioctl, firmware
protocol, ACK reuse, DMA release, global TX state machine or radio timing is
introduced. The original stale-ACK issue and new-profile provisioning remain
separate unfinished requirements. Target, final-image and physical acceptance
for this package are still pending; router unchanged.
