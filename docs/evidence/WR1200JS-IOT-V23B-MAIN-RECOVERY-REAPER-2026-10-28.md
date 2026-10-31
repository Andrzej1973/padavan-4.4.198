# IoT main recovery queue and joined reaper — isolated v23b, 2026-10-28

`tools/iot/prepare-main-recovery-reaper-candidate.py` copied the verified v22 67-file composition into `.iot-local-check/mt7603-main-recovery-reaper-v23b-20261028`. It staged changes in `os/linux/rt_main_dev.c`, `include/main-open-recovery-owner.h`, `include/rtmp.h`, `common/rtmp_init.c`, and `os/linux/pci_main_dev.c`. All 67 output file hashes match the new composition manifest. `production_installed=false` and `pci_release_gate_bound=false`.

After a failed main VERIFY, the staged open path first tries synchronous checked close. If that is incomplete, it now holds the root netdev and, under the transition lock, queues the exact acquired-open or recorded partial-close owner, records the `schedule_work` result, and schedules a delayed reaper. A rejected owner admission drops the temporary netdev hold. The callback from v22 uses `rtnl_trylock`, so it never blocks a PCI `cancel_work_sync` join on RTNL.

The separate delayed reaper joins the main work item before retrying or completing the owner. If `cancel_work_sync` cancels a pending item before its callback ran, the new `wr_iot_main_recovery_canceled_before_run` transition moves `QUEUED` to `RETAINED`; without this transition the reaper would indefinitely see a queued owner with no work. A bounded joined retry may then resubmit. On checked completion and released module pin, the reaper clears the owner and drops the one netdev hold. PCI probe unwind/remove now join delayed reaper before main work, and PCI remove can reap a completed owner after the join. A retained incomplete owner still fences adapter release and makes PCI remove return; this is not a complete PCI teardown protocol.

Checks run on Windows:

- Candidate preparer verified all 67 v22 input hashes; v23b output composition verified 67/67 hashes.
- Focused `check-main-readiness-verify-candidate.py` and broad `check-virtual-if-call-coverage.py`: pass on v23b. The focused checker distinguishes the staged queue from a complete PCI gate.
- Strict C11 `check-main-recovery-reaper.c`: pass. It covers accepted and rejected scheduling, join-before-retry, netdev hold/release after completion, retirement admission rejection, exact partial-close ticket submission, and cancellation of a pending item before callback execution. Kernel workqueue scheduling and actual hardware close are mocked.
- Strict C11 `check-main-open-recovery-owner.c`: pass against v23b headers.
- `prepare-main-recovery-open-check.py` extracted the actual isolated
  `MainVirtualIF_open` body into a strict C11 host fixture. GCC compiled it
  with `-Wall -Wextra -Werror`; execution passed three failed-VERIFY cases:
  close-begin rejection queues `OPEN_ACQUIRED`, failed preclose queues
  `CLOSE_UNCERTAIN`, and incomplete close continuation queues
  `CLOSE_INCOMPLETE`. Each retained one module pin and one netdev hold.
  Vendor calls, workqueue operations and hardware remain mocked.
- Python preparer/checker syntax checks passed. No full firmware build was run.

Workqueue review corrected an attempted fault model: a false return from
`schedule_delayed_work` can mean the delayed work is already pending. A mock
that returns false while leaving the work idle does not represent that kernel
contract and was removed. The first submission and self-rearm races still
need checking against the exact vendor workqueue source.

PCI lifetime review of the isolated source found a stricter blocker. In
`rt_pci_remove`, the adapter is marked retiring and the recovery owner is
marked `stop_requested` before both work items are joined. If the joined owner
is incomplete, `deferred_owners` causes an early return. The PCI remove
callback has no later in-driver retry in this candidate, while the stopped
reaper may no longer retry the close. The same early-return pattern exists
after `RtmpPhyNetDevExit` and after the PCI readiness/transaction gates.
Consequently, holding memory prevents an immediate use-after-free but does
not complete device removal; keeping v23b out of production is required.
The existing state-machine contract permits an acquired-main close to be
queued with `WR_MAIN_QUEUE_RETIREMENT_CLOSE` only while the radio is retiring
and an explicit PCI retirement owner is active. `wr_iot_radio_begin` also
admits CLOSE/BSS_CLOSE during retirement. This means the radio and owner
models already contain a narrow retirement-close admission path. The PCI
binding does not use it: it sets `stop_requested` first, and that state
forbids `wr_iot_main_recovery_begin`, `requeue`, and delayed-reaper retry.
The targeted next step is therefore a retirement-drain phase before the stop
request, with the PCI owner retaining adapter/netdev lifetime and proving
the actual checked close or an explicit unrecoverable result. Only after a
completed close may stop, join, child detach, PCI/DMA observation and free
proceed. A stage-1 void preclose remains ambiguous and cannot be replayed.
The strict C11 owner fixture now exercises the available retirement-close
transition end to end through exact main-close ticket and preclose receipt:
retire, explicitly owned retirement queue, worker begin, close action,
`wr_iot_radio_begin_main_stop`, reference close, and ticket bind all pass.
This proves the model admits the sequence; it does not execute the PCI
callback, vendor preclose, workqueue or hardware.
The next isolated candidate must prove a retirement owner can complete the
exact checked close while adapter/netdev and RTNL lifetimes are protected,
then join work and pass all child-detach, PCI transaction and DMA gates before
freeing resources. A failed close must preserve a live release owner with a
real retry path; returning from the one-shot PCI remove callback alone is not
that path. No hardware or image evidence supports this yet.

The host PCI retirement contract now has explicit `DRAINING` and `DRAINED`
phases between the admission fence and stop request. It refuses to record a
completed drain while recovery work is unjoined or any deferred owner remains,
and it refuses a stop request before the drain completes. Strict C11
`check-pci-retirement-owner.c` and `check-main-open-recovery-owner.c` pass
these transitions. This is a host-only ordering gate; no vendor PCI callback
is bound to it, and no claim of actual adapter release follows from it.
The failed-main-VERIFY fixture also now injects PCI retirement after a joined
retry is queued but before its worker begins. The existing state model still
admits the exact main close under the retirement fence when `stop_requested`
has not been set. Its strict C11 host run passes. This narrows the binding
problem to PCI remove ordering and actual worker/lifetime integration; it
does not prove that a late hardware close is safe after physical device loss.

The upstream [Linux 4.4.198 workqueue implementation](https://raw.githubusercontent.com/gregkh/linux/v4.4.198/kernel/workqueue.c)
defines `flush_delayed_work` as flushing only the last queued instance, and
`cancel_delayed_work_sync` as the delayed-work cancellation/join operation.
The candidate reaper can rearm itself, so one `flush_delayed_work` call is not
a proof of a drained owner. A PCI drain needs an explicit bounded loop that
rechecks the exact owner state after each joined instance, and it still needs
a defined result for an uncertain preclose or exhausted retry. This upstream
source is not a verification of the vendor-patched target kernel.
The host PCI retirement contract now has a bounded per-instance decision:
after a joined reaper instance it returns complete only with no deferred
owner, requests another flush only when another delayed instance is actually
pending within the round limit, and otherwise returns stalled. Strict C11
tests pass completion, self-rearm, no-next-work and exhausted-budget cases.
This decision does not schedule work or resolve a stalled owner; the PCI
callback is still unbound and cannot be considered safely releasable.

The [`cancel_work_sync` API documentation](https://docs.kernel.org/core-api/workqueue.html) describes a true return when work was pending and confirms it is no longer pending or executing on return, absent racing enqueue. The host mock models that contract; it is not evidence of this vendor tree's target build or runtime.

Open gates: source-level review of `schedule_delayed_work` self-rearm and workqueue concurrency on the exact 4.4 vendor tree; fault-injected extracted recovery and PCI callbacks together; MIPS target compilation; a recovery path for owner-admission failure or exhausted retries; completed PCI removal when a partial owner persists; exact callback/DMA quiescence; image and authorized device acceptance. v23b remains isolated and must not be installed in production or flashed.
