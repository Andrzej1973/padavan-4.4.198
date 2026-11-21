# Control producer admission — 2026-11-06

The isolated `prepare-mcu-control-admission.py` layer wraps Linux rt28xx_ioctl
and MlmePeriodicExec. On MT7603 PCI, admission increments an adapter counter
under wr_iot_transition_lock only while no radio transition, bootstrap, retained
failure, retirement, reset or suspend is active. Each admitted wrapper releases
after the original body returns, preserving its result. Blocked ioctl returns
-EBUSY; blocked periodic work returns without executing its body. Periodic timer
creation/enqueue is unchanged; queued commands are checked when executed.

Bootstrap reservation checks the same counter and poison bit under the same
lock before setting boot_active. It refuses an undrained producer; it does not
wait under a lock. This orders producer-first and bootstrap-first admission.
Counter overflow/underflow poisons admission permanently for that adapter;
only allocation initializes the fields. The caller still owns adapter lifetime.

Executed host checks:

- Actual transport/reservation plus actual admission helper: two simultaneous
  producers, partial/full drain, transition denial, bootstrap-first denial,
  late release and underflow/overflow retention: PASS (locks injected).
- Generated wrapper bodies: original success/error results, denied-body
  exclusion, balanced release, other-chip bypass and enabled/disabled feature
  guards: PASS with ASan/UBSan (raw SDK bodies/admission injected).
- Existing CI bootstrap fixture sequence through RX bounds: PASS, including
  hardware/IRQ/DMA/loader/scheduler/quota checks. New wrapper fixture initially
  lacked the vendor IN annotation macro; corrected the fixture and reran it.
- Fresh generation and complete manifest inventory: PASS.

Fixture temporary candidates (~14MB each) and executables were automatically
removed. The peer82 CI recipe now stages this layer and fixture; target results
are pending. Other command-worker operations, direct GPIO/EFUSE/chip/ATE paths,
numeric remap aliases and their lifecycle remain outside this coverage. The
counter protects bootstrap from these two admitted actors; it does not serialize
ordinary producers with one another or prove exclusion of all remap users.
Scheduler and normal IoT promotion remain unbound; runtime is unverified.
