# Remap admission findings — 2026-11-06

Inspected isolated candidate `/tmp/wr-scheduler-run-jpoYun` (the prior quota
layer, not the newly published preflight). Adjacent manifest validates its
complete inventory; the JSON companion records source hashes and reference
lines. These are source findings, not evidence of actual concurrent execution.

## Paths requiring exclusion

- `common/mlme.c:MlmePeriodicExec` calls `PSEWatchDog` when START_UP is set
  and PSEWatchDogEn is true. `PSEWatchDog` calls `MonitorRxPse` before its reset
  condition. `MonitorRxPse` temporarily changes MCU_PCIE_REMAP_2. No explicit
  bootstrap check appears in these call sites. Bootstrap IRQ-unmask itself
  sets START_UP, so that flag alone cannot prove exclusion. Existing close-time
  timer joins must be traced through the following open to prove whether this
  callback can actually run.
  The reopen path is now traced further: `common/rtmp_init_inf.c` calls
  RtmpMgmtTaskInit, then MlmeInit, then MCUSysInit. MlmeInit initializes and
  arms PeriodicTimer. MlmePeriodicExecTimer enqueues CMDTHREAD_MLME_PERIOIDC_EXEC;
  the command worker in `common/rtmp_init.c` executes MlmePeriodicExec.
  RTMPSetTimer refuses retiring timers and HALT/NIC_NOT_EXIST, but does not
  test bootstrap admission. Therefore an earlier close-time join alone is
  insufficient: this open creates a new periodic producer before MCU startup.
  Both timer admission and already queued command execution need accounting.
- `os/linux/ap_ioctl.c:rt28xx_ap_ioctl` invokes PREPARE for most commands;
  `os/linux/rt_profile.c:RTMP_AP_IoctlPrepare` checks INTERRUPT_IN_USE, with a
  NULL-command-data success exception. It does not check the bootstrap ticket.
  `ap/ap_cfg.c:OID_GET_CPU_TEMPERATURE`, `common/cmm_info.c:show_temp_proc`, and
  debug `common/cmm_cfg.c:Set_themal_sensor` call MtAsicGetThemalSensor, which
  saves, changes and restores this same remap register. The upstream Linux
  ioctl/lifetime path must also be traced before concluding it is reachable.
  `os/linux/rt_main_dev.c:rt28xx_ioctl` itself checks only non-NULL adapter and
  AP mode before rt28xx_ap_ioctl; no bootstrap gate was found at that entry.
- GPIO, EFUSE, reset, chip init and ATE/QA use the register too. Build guards,
  initial startup ordering, runtime admission and any nested calls must be
  audited separately. A scheduler-only lock would not serialize these users.

## Integration requirement

Do not bind scheduler_run or remove the normal-init refusal on the strength of
the frozen sender constructor lease. It excludes MCU constructors, not all
register users. Admission must both prevent new incompatible users and drain
already admitted users before remap ownership transfers. A plain flag test at
a diagnostic entry point leaves a check/use race. Long reset/diagnostic loops
must not be enclosed in an IRQ-disabled scheduler spinlock merely to share a
lock. Unknown or failed drain must retain the closed state and resources.

The next implementation must identify the complete applicable producer set,
establish lock order with the existing transition lock, and test both actor
orders (producer first and bootstrap first), retained failure and late release.
