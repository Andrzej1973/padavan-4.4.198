# WR1200JS BusyBox `od` integration — 2026-10-27

The pinned firmware source `c25283e915a2a00a763774dd255b14aff997285e`
contains BusyBox 1.24.2 `coreutils/od.c`. `coreutils/Config.src` defines
`CONFIG_OD` without a separate dependency, and `include/applets.src.h`
registers it at `/usr/bin/od`. The upstream `trunk/configure` copies
`trunk/configs/boards/busybox.config` into the effective BusyBox `.config`.
The pinned board config has `# CONFIG_OD is not set` and
`# CONFIG_DESKTOP is not set`.

The existing WR1200JS preparation script now enables `CONFIG_OD=y` together
with its previously reviewed readlink options. It leaves `CONFIG_DESKTOP`
disabled, selecting BusyBox's smaller legacy `od` implementation; this does
not provide GNU-style `-A/-t/-N` options. The WR1200JS image gate requires
the effective selector and `/usr/bin/od` symlink. The exact-image BusyBox
audit also checks the applet list/link and probes `od -b` on four known bytes
under target QEMU.

Python syntax and whitespace checks passed locally. No target BusyBox build,
final ROMFS/image gate or router runtime test has yet been run for this
change. Flash size delta is unknown until comparison of actual image
artifacts. The currently installed router still lacks `od`; the change only
affects a future built image and does not alter the live device.
