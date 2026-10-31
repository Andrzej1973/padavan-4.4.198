# Net-task exit result67 — prerequisite for submission fencing

Pinned `prepare-nettask-exit-result.py` creates
`.iot-local-check/nettask-exit-result67-20261030` directly from64. Draft65 remains
excluded. The transform changes RtmpNetTaskExit declaration and both PCI/RBUS
and SDIO definitions to INT, preserving existing body work and returning success.
It checks all three direct calls: initialization unwind, legacy close and checked
close. Refusal stops further teardown; checked close records terminal partial
stage3, while the legacy executor retains its existing failed-close latch.

`prepare-nettask-exit-result-check.py` extracts both candidate close bodies and
shared wrappers. Strict GCC C11/O2/Wall/Wextra/Werror passed injected net-task
failure before MlmeHalt, management join, UserCfgExit and ring free; retry does
not repeat partial stage zero; successful exit permits the old completion path.
The init-unwind guard and both bus signatures are source-checked only, not whole
init/SDIO execution. Net-task exit is mocked during the close fixture; no actual
tasklet cancellation is executed. No producer fence/drain is installed yet.

Classification found scheduling sites can already hold LockInterrupt or other
vendor locks. Submission ownership therefore needs a dedicated short IRQ-safe
lock and no wait while any producer lock is held. MCU cmd_msg_task is a separate
lifecycle from the network-cookie tasklets, as are main-recovery and optional
polling work; do not fence them indiscriminately using one network-task flag.

Current consolidated chain still ends64. Stage67 remains isolated until the
fence/drain binding and existing full fixtures are adapted coherently to the new
status. Latest full64:61 preparers,580 matching files,68 host variants. No target
or OS_ABL module compilation, firmware build, kernel concurrency/runtime proof,
router changes, dispatch, commit or push. Next bind network submission producer
leases, block/drain before early tasklet kill and explicit initialization/reopen.
