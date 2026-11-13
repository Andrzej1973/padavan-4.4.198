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
