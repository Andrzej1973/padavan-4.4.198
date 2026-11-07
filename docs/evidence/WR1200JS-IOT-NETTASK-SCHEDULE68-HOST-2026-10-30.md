# Network tasklet submission68b — isolated driver binding

`prepare-nettask-schedule.py` pins seven input files from candidate67 and creates
`.iot-local-check/nettask-schedule68b-20261030`. It adds a dedicated adapter
IRQ-safe short lock, scheduling owner, waitqueue and joined marker at fresh
allocation. The lock is freed with the adapter; its final lifetime prerequisite
is not yet integrated into the adapter-release gate.

The transform replaces exactly35 network-cookie tasklet submission sites:
29 in rt_rbus_pci_drv.c,1 BA timeout,2 TBTT and3 UAPSD. MCU cmd_msg_task,
OS scheduling wrapper implementations, main recovery and optional polling work
are deliberately unchanged. Non-PCI preprocessing retains the old macro path.
The final configuration and all callers' lock ordering still need target review.

The helper enters under its dedicated lock, calls the scheduling API outside
the lock, then leaves and wakes drain waiters. Exit blocks new submissions,
refuses atomic/IRQ-disabled waiting, waits up to5000ms outside the lock, then
preserves the original early tasklet kills before management teardown. Timeout
returns failure via candidate67 guards. Joined marker makes repeated exit
idempotent. Init rejects live/unjoined state before tasklet initialization and
opens submissions only after initialization. This relies on existing outer
initialization serialization; this helper does not reserve a second init lane.
OS_ABL tasklet allocation failures remain an existing unverified init concern.

`prepare-nettask-schedule-check.py` extracts the actual helper and network
Init/Exit functions. Base and extended feature variants passed strict host GCC
C11/O2/Wall/Wextra/Werror: submission admitted before a fence, refusal of later
submission, timeout without kills, drain then join, repeated exit, reopen,
duplicate init refusal before mutation and atomic/IRQ-disabled refusal.
Extended flags cover ANDES,MT,ATE,UAPSD,AP,DFS source branches together.

Kernel scheduling, work allocation, locks and waitqueue are modeled. Callback
function/data ABI is not evaluated by the Init macro in the Windows LLP64
fixture; an initial compile diagnosed that pointer-width mismatch and the mock
was scoped accordingly without weakening compiler flags. No actual OS_ABL module
compile, kernel concurrency, callback/DMA or hardware runtime acceptance.

Candidates67/68 remain isolated, not in the consolidated chain. Chain ends64;
draft65 remains excluded. Next bind the final scheduling-owner idle/join proof
into adapter release, verify producer/close lock order and init error unwinds,
adapt existing full fixtures to fallible net-task exit, then replay and target
compile coherently. No firmware build, router changes, dispatch, commit or push.
