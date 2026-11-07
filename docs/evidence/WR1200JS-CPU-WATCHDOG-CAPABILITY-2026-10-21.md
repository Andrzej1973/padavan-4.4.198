# WR1200JS CPU timer watchdog capability — 2026-10-21

## Finding

The `watchdog_cpu` switch is not the built-in MT7621 hardware watchdog. At the
pinned Padavan revision `c25283e915a2a00a763774dd255b14aff997285e`,
`start_watchdog_cpu()` and `restart_watchdog_cpu()` only request load/unload of
the optional `rt_timer_wdg` module. The WR1200JS effective kernel configuration
enables `CONFIG_MT7621_WDT=y` and leaves `CONFIG_RALINK_WDT` unset; these are
separate driver paths. The repository contains no `rt_timer_wdg` implementation
or package recipe.

The read-only router sample from 2026-10-21 16:18 UTC had
`watchdog_cpu=1`, no `rt_timer_wdg` in `/proc/modules`, no
`/sys/module/rt_timer_wdg`, and no matching file under `/lib/modules`.
`/sbin/watchdog`, `/dev/watchdog`, and `watchdog0` were present, but no
read-only signal proved that the built-in timer was active or being serviced.
This supports marking the optional CPU timer watchdog control unsupported on
WR1200JS; it does not mark the built-in MT7621 watchdog unsupported.

Pinned source anchors were rechecked through the repository's GitHub source
connector at the exact revision: the two lifecycle functions are adjacent and
match the strict transform; `defaults.c` has one `watchdog_cpu=1` default; the
Services page has one toggle initializer and one complete control row; and
`board.mk` defines `BOARD_WR1200JS`. The pinned `rc/Makefile` installs the rc
binary as `/sbin/rc`.

## WR1200JS-only implementation

- Remove the `watchdog_cpu` enable row and initializer from the Services page.
- Keep the separate read-only status observation so the legacy setting and
  module absence remain diagnosable.
- Compile the WR1200JS lifecycle functions as no-ops so an old saved value of
  `1` cannot request the missing module. Other boards retain the pinned source
  behavior.
- Set the WR1200JS factory default to `0`; retain the generic `1` default for
  other boards.
- Exclude the unsupported control from the WR1200JS service navigation.
- Add a final ROMFS gate that requires the control/link and module to be absent
  and checks `/sbin/rc` for the module name.

The scoped in-memory source fixture and service-navigation verifier both pass.
GitHub's exact pinned source was also inspected and each transform anchor matched
once. Firmware #513 predates this change; final source integration, ROMFS image
gate, physical UI and runtime behavior require a later build and device check.
The router has not been changed, rebooted, or flashed.
