# RC radio-stop integration requirements

Status: initial-never-opened backend and balanced signal fence implemented;
post-OPEN physical radio integration remains incomplete. No runtime acceptance.

`prepare-rc.py:47-83` adds calls from `stop_wifi_all_rt()` and
`restart_wifi_rt()` to the strong `wr_iot_activation_prepare_radio_stop()`
contract. `rc-backend.c` now supplies the strong provider for initial-never-opened state.
It deliberately refuses all previously opened states pending full integration.
A full executable link must remain a separate gate from TU compilation.

The contract also requires shutdown admission. The original inserted call sites did not
establish that fence; the current prepared bodies now do so with LIFO tokens. The new backend must not assume that normal
radio notifications already hold the IoT transaction fence: `rc-shutdown-
admission.h` changes only through explicit begin/end, and IoT mailbox dispatch
is not the only caller of these stock radio functions. Establish and balance
the fence over the entire physical stop/restart call, including nested
stop-all calls and all early returns; restore the original signal mask and
deliver deferred normal shutdown exactly once. Preserve fatal signal behavior.

Implementation order:

1. Trace actual stock stop/restart bodies and their callers from pinned SDK.
   Establish one outer fence with balanced cleanup across returns; nested
   stop-all must not acquire a conflicting controller transaction.
2. Supply the strong callback from the retained backend. Pending START/STOP
   must retain and advance their own transaction, never create another owner.
   Initial-never-opened observation and previously opened CLOSE are distinct.
3. After ACTIVE, initiate an owned normal OFF with a fresh envelope and progress
   asynchronously. A callback that returns refusal must prevent both stop and
   subsequent profile reload/open. No busy wait and no recursive radio stop.
4. Require the actual driver evidence appropriate to physical teardown.
   Current CLOSED is configuration/reference state, explicitly not an RF/DMA
   drain certificate. Do not promote it through a naming change or a stub.
5. Test INITIAL_OFF/ACTIVE/START/STOP/rejected/uncertain, pending termination,
   duplicate callbacks, nested calls and all early returns. Then execute full
   RC/HTTP link and dependency checks on GitHub.

IoT toggling itself continues to use the reserved ra2 lifecycle, without
physical restart. This does not resolve ordinary physical radio restart.

Pinned versus composed teardown: pinned `common/rtmp_init_inf.c:762` defines
RTMPDrvClose; lines815-822 wait on DeQueueRunning before task shutdown. This
raw loop is unbounded. It is **not** evidence of an unfixed candidate bug:
existing `prepare-peer-legacy-close.py` already adds a1000-poll limit, propagates
radio-off refusal and guards replay; `peer-close-executor.inc` serializes legacy
and checked bodies. Verify the actual composed candidate before changing this
path. Do not duplicate or remove its existing ownership checks.

RC result gap: existing prepare-legacy-close-result.py propagates checked
status through RTMPDrvClose, OS_ABL dispatch, VIRTUAL_IF_DOWN and immediate
driver consumers. This alone does not provide an RC completion receipt:
prepared stop/restart remain void calls to wif_control. Before permitting a
post-OPEN physical restart, prove how RC observes the result of that exact
physical teardown and prevents reload/open on a retained failure. Do not
translate syscall return or software CLOSED into a new hardware certificate.

Initial-only callback now uses a fresh double initial-idle observation for
every invocation, including retained INITIAL_OFF after adapter replacement.
The original public OFF result keeps its own epoch and is not rewritten.

Confirmed pinned Linux boundary: `net/core/dev.c:1417-1425` calls
`ops->ndo_stop(dev)` without testing the returned value, clears `IFF_UP` and
returns zero. A vendor negative close result therefore cannot be assumed to
reach RC through SIOCSIFFLAGS. Keep generic netdev behavior unchanged; design
and validate a separate exact completion observation before post-OPEN restart.

Pending task-binding choice must be resolved before driver hooks: `wif_control`
spawns shell/ifconfig, so a record armed by a synchronous PID1 ioctl cannot
require the same task in subsequent ndo_stop. Passing a numeric PID or accepting
any close task is insufficient. Either a retained child must arm and execute
its own close with references held until parent observation, or one explicit
serialized Linux driver operation must perform arm/close/report in the same
pinned task. Audit reentrancy, RTNL and ioctl-entry lifetime before choosing.
Current metadata helpers cannot resolve this binding by themselves.

Confirmed composed execution path: `prepare-main-physical-close-delegation.py`
changes MainVirtualIF_close so WR_RADIO_CLOSE submits the existing main recovery
owner/work outside ndo_stop RTNL. Therefore same-task SIOCSIFFLAGS does not
imply same-task RTMPDrvClose/checked body execution. The physical executor
transform currently hooks the synchronous legacy lane only and cannot serve
this production candidate path. Installer now refuses the detected delegated
checked-close shape before output creation. Keep the source-only legacy tests
as limited fixtures, not physical path acceptance. Next binding must consume
the exact retained main recovery ticket/owner at worker entry and after its
module-reference receipt; do not weaken task matching to accept any worker.

Local exact Main recovery software receipt now survives joined netdev release.
`wr_iot_main_recovery_release_for_ticket` requires the retained Main physical
close ticket plus Main generation/OPEN token and revalidates current registry
and radio state. The previous ra2 CLOSE tuple cannot substitute for this Main
identity. The physical-stop handler must bind that Main ticket when submitted;
calling only the current-state observer is insufficient. This handler binding
is still absent. Neither accessor certifies hardware retirement.

Capture admission now also requires expected Main generation and OPEN token
from the ARM-time kernel snapshot, rather than accepting whichever newer
recovery owner exists at QUERY time. A larger radio serial alone is insufficient
request correlation. The future handler must hold the existing lifetime fence
across ARM/submission/capture and compare these saved Main values; userspace's
ra2 generation/token cannot substitute for Main's separate registry identity.
The source helper enforces equality, but the handler/caller snapshot remains
unimplemented and must not be claimed integrated.
