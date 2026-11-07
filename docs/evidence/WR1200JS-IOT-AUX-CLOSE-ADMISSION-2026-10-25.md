# IoT auxiliary close admission, isolated host model

The vendor WDS, AP-client and monitor stop wrappers still perform family
CLOSE/queue/HNAT/DOWN work without one shared result owner. In particular,
the old `VIRTUAL_IF_DOWN` has a void result, while the shared vendor count is
also used by main and MBSS. This source/model step does not bind a production
stop handler.

`tools/iot/aux-close-claim.h` now reserves a **non-last** `AUX_CLOSE` ticket
and exact WDS/AP-client/monitor reference under the adapter transition lock.
It requires a published owned record of the requested family and an exact
match between all owned registry records and the vendor reference count.
Unknown/mismatched family, stale count and a last-reference close are refused
before mutation. The last close needs the separate checked physical recovery
owner; routing it through selective AUX_CLOSE would leave the radio running.

`wr_iot_radio_abort_aux_close_unmutated` retires an AUX_CLOSE ticket only
before vendor, queue, HNAT or count mutation. It never clears pending reset
or PM intent. Strict C11 compile (`-Wall -Wextra -Werror`) and
`check-aux-close-claim` execution passed exact owner/count/family, duplicate
admission refusal and unmutated ticket abort. This is sequential host-model
evidence, not a complete `ndo_stop` implementation.

Next: bind checked family CLOSE and `wr_iot_virtual_down_checked` to the same
ticket and reference with retry/uncertain recovery. A failed `ndo_stop` alone
is insufficient because the kernel may consider the netdev administratively
down; a retained worker/release gate is required before image packaging.

## Isolated WDS non-last stop candidate v31

`prepare-wds-close-owner-candidate.py` derived v31 from pinned v30 source.
The WDS `ndo_stop` reserves an exact non-last AUX_CLOSE owner, records the
queue/HNAT stage, invokes checked virtual DOWN, and consumes the reference
and module pin only after a successful DOWN result. On failed DOWN it retains
the CLOSING record, radio reservation and pin; the stack ticket is lost. A
last-reference close is refused before
queue/HNAT mutation.

`prepare-wds-close-wrapper-check.py` extracted that exact wrapper into a
host fixture. GCC C11 `-Wall -Wextra -Werror` compilation and execution
passed success, failed DOWN retention and last-close refusal. The virtual
caller coverage gate passes for v31 and the prior v30. Python syntax and
`git diff --check` passed. This is mocked host execution, not a MIPS compile
or router test. No recovery worker exists yet; failed `ndo_stop` may leave a
kernel-down netdev, so v31 must remain isolated and cannot be packaged.

## Same-ticket retry gate after failed WDS DOWN

Source review found that v31 retains `CLOSING` after a failed checked DOWN,
but its AUX_CLOSE ticket was only a stack local in `ndo_stop`. A later worker
could not safely reserve another ticket: queue/HNAT effects had already
happened. The host model now records the ticket epoch, prior radio
phase/readiness and observed vendor count at admission.
`wr_iot_aux_close_retry_unmutated_down` reconstructs only the same ticket
when the record is at stage 1 and `virtual_down_stage` is zero. It rejects a
different family/count, pending reset, changed epoch, PM and adapter
retirement. It performs no vendor, queue or HNAT operation.

The strict C11 `check-aux-close-claim` fixture exercises successful
same-ticket reconstruction and refusal cases. This remains a host-only
admission gate: no worker schedules retry, a DOWN that succeeded before a
later failure is not reconciled, AP-client/monitor close is not bound, and
the target driver was not compiled. Do not package v31.

## Isolated WDS continuation candidate v32

Review of the staged tree showed that v31 did not carry the new
`interface-reference.h` fields, so the recovery gate was absent from that
candidate. The v32 generator now copies the matching header and adds a
callable `WdsVirtualIF_close_retry` continuation. Its claim changes the
record from stage 1 to stage 3 under the common adapter lock, preventing
two continuations from taking the same ticket. A failed, unmutated DOWN
releases the claim to stage 1. The continuation does not stop the queue or
deregister HNAT again; it consumes the reference and module pin only after
checked DOWN and ticket completion.

Generated `.iot-local-check/wds-close-v32-20261025` from the pinned v30
source. The extracted wrapper compiled with strict host C11 warnings against
the headers copied into v32 and passed initial close, failed DOWN, failed
retry, successful same-ticket retry, no repeated queue/HNAT effects and
last-close refusal. Five-family caller/registration coverage passed for
both v31 and v32; Python syntax and `git diff --check` passed. There is no
retained worker that invokes the continuation after `ndo_stop` returns, nor
reconciliation after a successful DOWN followed by failed finalization.
This is not a MIPS build, installed image, or device test; v32 stays isolated.

## Isolated WDS post-DOWN reconciliation candidate v33

The previous continuation covered only a failed DOWN that left the vendor
count unchanged. A checked DOWN may instead succeed while ticket completion
fails after an epoch change. Reissuing DOWN would decrement the count twice.
The shared host model now finalizes an already completed DOWN only when the
same ticket, CLOSING record, stage and post-DOWN vendor count match. A failed
radio finish records stage 4; one retained owner may claim stage 5 and retry
completion without queue, HNAT or vendor DOWN calls. No pin is released on
failure. The same locked preflight establishes the conditions for consuming
the reference after radio finish succeeds.

Generated `.iot-local-check/wds-close-v33-20261025` from pinned v30. Its
extracted WDS wrappers compiled with strict host C11 warnings using v33's
copied headers. The fixture passed failed finish after one successful DOWN,
refused premature completion, then retired the same ticket with no second
DOWN after reset intent was recorded. The five-family source gate passed for
v31, v32 and v33; Python syntax and `git diff --check` passed. This does
not provide the retained worker or its lifetime/drain semantics. The
candidate remains outside the production driver and image; no target build
or router test was performed.

## Deferred recovery lifetime contract

The pinned PCI removal path still calls `RtmpRaDevCtrlExit` and frees the
adapter after an unchecked `RtmpPhyNetDevExit` result. A worker retaining an
adapter pointer would therefore race free unless every release path obeys a
deferred-owner fence. Added host-only `aux-close-recovery-owner.h`: queueing
requires a pre-acquired netdev hold and an adapter release fence; one queued
owner records the exact device, generation and close serial. Failed work
retains that owner; a bounded explicit requeue is possible. A remove request
stops new retries, but cannot drop the owner merely because work was
cancelled. Completion releases the deferred-owner count only after checked
reference/ticket completion and external work join.

The strict C11 fixture verifies duplicate queue refusal, bounded retry,
retention after failure, stop behavior and the adapter release gate before
and after joined completion. This is a lifecycle contract, not `work_struct`
integration. A boolean supplied by a mock caller does not prove real PCI
remove, unbind and module-unload paths enforce the fence. No worker is safe
to bind until that source-level release path is implemented and target
compiled.

The owner fixture exposed a later-ticket race in its first completion
contract: checking `radio.retired_serial` only after work join could reject
an already finished WDS close when another radio transition retired in the
meantime. Completion is now recorded in the owner under the adapter lock
while the exact close serial, generation, IDLE reference and stage 2 are
still observable. Join releases the deferred owner using that recorded
proof, even if a later ticket updates the global serial. The strict C11
fixture checks wrong-serial refusal, duplicate completion refusal, continued
adapter-release refusal before join, and successful release after a later
ticket. This remains host-only; real worker and PCI paths must enforce the
same lock and lifecycle.
