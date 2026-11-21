# WR1200JS BusyBox hexdump / od checkpoint — 2026-10-27

## Exact saved image evidence

`artifacts-583/target-busybox-audit/target-busybox-audit.json` records build
number 583 against pinned firmware source revision
`c25283e915a2a00a763774dd255b14aff997285e`. Its QEMU probe identified
BusyBox `1.24.2`; the source Makefile at
`trunk/user/busybox/busybox-1.24.x/Makefile` has version 1.24.2.
The recorded ROMFS BusyBox SHA256 is
`b96bc3d497966b9210db938ee6a4ebc49009fd6ad76356743ae7e1005dcb1127`.
The exact effective config records `CONFIG_HEXDUMP=y` and
`# CONFIG_OD is not set`; the applet inventory contains `hexdump` and omits
`od`. `usr/bin/hexdump` links to `../../bin/busybox`. The image audit's
`usbip_hexdump_exact_options` probe passed for `-v -n -e` under target QEMU.
That probe does not exercise the PCI helper's `-C -n 4096` options.

## Running router evidence — connection restored

Earlier read-only router inspection successfully used `busybox hexdump -C -n
4096` on PCI config files and observed `hexdump` but no `od` in its applet
list. After the owner restored connectivity, the new allowlisted
`busybox-version` and `busybox-image` checks both exited 0 over SSH.
The live BusyBox banner is `v1.24.2 (2026-10-18 14:22:26 UTC)`;
`/bin/busybox` is 709260 bytes and has SHA256
`87a15a8c1b06577c874f1a05edd80291991fd0d234c0e0d55a7a92df4335ecc0`.
The applet list includes `hexdump`, `base64`, `dd`, and `strings`, but not
`od`. `/usr/bin/hexdump -> ../../bin/busybox` exists; `/usr/bin/od` does not.
`busybox hexdump --help` advertises both `-C` and `-n LENGTH`, matching the
successful live PCI dump command. No files or settings were changed.

The live hash **differs** from build 583's saved ROMFS hash
`b96bc3d497966b9210db938ee6a4ebc49009fd6ad76356743ae7e1005dcb1127`.
Therefore the shared version and applet names do not identify build 583 as
the installed image. No other saved image hash matched in the bounded local
reports checked here; the installed build number remains unconfirmed.
Two earlier attempts returned SSH connection timeout before connectivity was
restored; they did not run remote commands.

Keep `hexdump` in the PCI helper; no `od` fallback is required for the
already-observed live command. Before claiming exact-image equivalence,
identify the installed build and compare its ROMFS BusyBox hash to the live
hash. The observed version is the 1.24.2 source lineage; this evidence alone
does not establish whether the device has later patches or applet changes
beyond those listed.
