# Padavan NG donor references

Checked on 2026-10-09. Both snapshots use Linux 3.4.113. These are reference files, not validated Linux 4.4 board ports. They are not selected by `boards.json` and do not trigger automatic firmware builds.

- [nilabsent/padavan-ng](https://github.com/nilabsent/padavan-ng), revision `14e4fac1ca24ab15278378d3e994db82fc9bcdda`: 39 board directories, original MIPS toolchain sample/build instructions and selected package recipes.
- [hadzhioglu/padavan-ng](https://gitlab.com/hadzhioglu/padavan-ng), revision `503a6f0064bc5999bf92e47a902a732693a1a4f5`: 39 board directories and original MIPS toolchain sample/build instructions.

Each directory contains `SOURCE.json` with original paths and SHA256 checksums. Files are copied without adaptation; upstream license files and notices are retained. This is a local/reference snapshot, not a complete offline build kit.

## Candidates for later WR1200JS work

Both MIPS samples select GCC 7, hard float and Linux 3.4 headers. Hadzhioglu selects uClibc-ng 1.0.52; nilabsent takes uClibc-ng from its firmware recipe, currently 1.0.58. Do not substitute these samples for the current 4.4 toolchain without rebuilding and checking the complete ABI, kernel modules and userspace.

Nilabsent's inspected recipes select dnsmasq 2.93, Dropbear 2026.91 and OpenSSH 9.6p1. Preserve them as update candidates; adapt their patches and service integration before adoption. Its ZeroTier recipe selects 1.16.0, which is older than our pinned 1.16.2 and is not an upgrade. The inspected `trunk/user/ttyd/Makefile` does not exist at this revision.

Continue selective review of WebUI/service integration and hardware descriptions when needed. Copying a board description does not establish flash layout, calibration or driver compatibility. Finish and verify WR1200JS before expanding active build targets.
