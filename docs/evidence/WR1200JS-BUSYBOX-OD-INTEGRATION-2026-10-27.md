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

Python syntax and whitespace checks passed locally. GitHub Actions firmware
build #636 (run 40562761997, attempt 1) completed successfully. Its
`target-busybox-audit` artifact reports BusyBox 1.24.2, `od_compact_config`,
`od_applet_and_link`, and the target QEMU `od_octal_bytes` probe all true;
the overall audit result is true. The image BusyBox SHA256 is
`453475ff84d887e008843240467ab9fac8abebfe8fa4b0431a06a41999ca6fb5`
versus `a90dc161a6d434c79b2ddd5253f75e4fdc91577f484fb08786e9502fd0ddfe76`
in build #635. This proves the new image contains a different BusyBox, not
the exact size cost of `od`; other source changes also entered #636. The
currently installed router still lacks `od`; no router runtime test or flash
has been performed for this change.
