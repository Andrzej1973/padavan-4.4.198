# Saved IoT startup — paired WR1200JS candidate

The pinned SDK `trunk/user/rc/rc.c:init_router()` generates radio profiles,
loads wireless modules, starts LAN, DHCP/DNS, firewall/WAN and services before
returning to `init.c`. Previously `control-server.c` accepted IoT only through
the `wr_iot_apply` notification/mailbox; runtime initialization created the
status endpoint but did not submit the saved ON request. Profile pre-reservation
alone therefore did not establish saved-ON startup activation.

The paired runtime source now arms `rc-boot` immediately after `init_router()`
returns, under BOARD_WR1200JS and the existing prepared IAPP policy gate. Arm
only records intent; the existing RC wait cycle runs readiness work later.
Default runtime preparation keeps that policy gate zero. Other boards and the
unpaired source do not arm it.

The path is:

```
init_router returns -> boot_arm -> RC wait -> boot_step
  -> initial-only mailbox publication -> later dispatch
  -> canonical control-server -> activation backend/continuation
```

`rc-boot.c` polls at most once per monotonic second without retaining credentials
between attempts. Saved radio OFF/unsupported mode and saved IoT OFF do not
publish a request. A saved-ON radio which is not live yet remains pending.
Saved ON waits for temporary-OFF network/BSS/DNS policy, a free backend, initialized
nonblocking entropy, two matching fresh IDLE observations, and a repeated saved
request/mode snapshot. It never generates a profile or requests Main restart.
Actual OPEN/network activation remains exclusively with the normal backend.

The service guard is released before taking the mailbox lock. Initial publication
requires `request`, `result`, `request.new` and `result.new` all absent under that
lock. Existing user transactions, terminal history, malformed files, symlinks and
interrupted publications are preserved. Once publication is attempted, bootstrap
never retries it, even if publication is uncertain. No separate replay or recovery
owner is created. Successful publication schedules normal dispatch on a later RC
tick; canonical continuation owns RECOVERY, terminal publication and credential
file cleanup. Already-retained RC work takes priority over bootstrap.

Host checks:

- Actual mailbox fixture: empty initial publication succeeds; existing normal,
  terminal, malformed/staging and symlink records refuse without replacement.
- `check-rc-boot.py`: real mailbox plus canonical dispatch/continuation; factory
  OFF, saved/live radio distinction, delayed IDLE/entropy/guard readiness,
  one publication/execute, user QUEUED/terminal preservation and RECOVERY.
- `check-rc-boot-scheduling.py`: actual RC wait priority and deferred one-time
  dispatch after boot publication.
- Runtime preparation compiles the backend/root/boot units with Werror and
  executes the generated init-arm snippet for both board and policy-gate values.

Mode, driver readiness and activation results in the boot fixture are injected.
These checks do not prove target image inclusion, RF readiness, DHCP leases,
isolation, first-boot acceptance or saved-settings operation on physical WR1200JS.
Those gates remain open; no router changes were performed.
