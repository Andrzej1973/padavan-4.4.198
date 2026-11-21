# First PCI work completion receipt61

Pinned `prepare-pci-first-work-receipt.py` creates
`.iot-local-check/pci-first-work61-20261030` from60b. It checks the stop-request
transition result and records WORK_JOINED only after the actual first
`cancel_delayed_work_sync`, `cancel_work_sync`, recovery join reconciliation,
stop-request fence and zero deferred owners. State is changed under the
transition lock, with synchronous cancellation outside that lock.

`prepare-pci-first-work-receipt-check.py` extracts this exact source block.
The strict GCC C11/O2/Wall/Wextra/Werror host test passed missing-stop refusal,
an owner injected by the joined work, successful receipt after no owners remain,
and refusal to replay an already-consumed receipt. Cancellation and locking
are modeled, not actual kernel scheduling. This is not final adapter release.

The source audit found `wr_iot_children` only initialized, never advanced by
the candidate's actual child removals. Therefore recording children complete
or main callback quiescence just because RtmpPhyNetDevExit returned TRUE would
fabricate evidence. The current first-join fix deliberately does neither.
RtmpOSNetDevDetach calls unregister_netdevice under RTNL protection; the return
alone has not yet been proved sufficient for every retained vendor callback.

Next bind exact published-family teardown and callback ownership, root detach
completion, final recovery join and actual physical observation before the
terminal release receipt. Cold probe/free remains separate. Step61 is added
to the chain/test suite, but not freshly replayed in full. Latest full replay58.
No target/firmware build, router changes, dispatch, commit or push.
