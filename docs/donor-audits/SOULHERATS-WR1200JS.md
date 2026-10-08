# Donor audit: soulherats/wr1200js_router

Inspected 2026-10-08. Repository: https://github.com/soulherats/wr1200js_router
Pinned master: `83a7672e469dee6220193f6596bc1b14cb5bf7a8` (2026-09-24, Update CI). The branch listing returned only master. No code or compiler from this donor has been enabled in production.

## Findings and decisions

- **Kernel:** trunk/linux-3.4.x/Makefile specifies 3.4.113. This is a donor for selected implementations and board references, not a replacement for our pinned Linux 4.4.198 base.
- **Toolchain:** build_toolchain selects samples/mipsel-linux-uclibc/crosstool.config. That sample selects GCC 7, little-endian MIPS32r2, uClibc-ng 1.0.32 and local Linux 3.4 headers. dl_toolchain.sh instead downloads hanwckf/padavan-toolchain v1.1 into toolchain-3.4.x without a checksum check. The downloaded compiler has not been executed or version-verified in this audit. No newer, proven-compatible compiler was established; retain our checksum-pinned toolchain.
- **WR1200JS memory:** its default board kernel config specifies 512 MB. CI also creates a 128 MB variant. Our supplied device log proves 128 MB physical RAM; do not transfer the 512 MB configuration into production.
- **Wireless candidate:** WR1200JS kernel config enables MT7603 DOT11K_RRM, WNM, WPA3 and OWE, but leaves DOT11R_FT disabled. The inspected mt76x3 os/linux/config.mk separately defaults HAS_DOT11K_RRM_SUPPORT and HAS_DOT11V_WNM_SUPPORT to n. These distinct configuration paths require tracing the actual kernel build and feature sources; flags alone do not prove working k/v or WPA3. Candidate follow-up: trace Kconfig/Makefile definitions, source implementations, userspace/profile integration, then assess a focused 4.4 port and compile/runtime tests.
- **Board wiring:** board.h records FN1 GPIO18, reset3, WPS12, WAN LED6, USB LED8 and router LED7, 2x2 radios and gigabit Ethernet. board.mk specifies one USB port. Preserve as comparison evidence; GPIO changes still require physical-device validation.
- **ttyd:** recipe 1.6.2, older than our optional 1.7.7 candidate; no replacement planned.
- **SmartDNS:** recipe Release33 with a local source archive; available as historical integration evidence, not evidence of a newer package.
- **Other donor ideas:** README describes AriaNg and optional regional authentication/diagnostic tools. These are outside our current WR1200JS priorities; do not enable packages solely because a donor lists them.

## Preserved references

`reference/boards/soulherats-wr1200js-router/` holds 11 original board files for WR1200JS, MI-MINI and MI-4, with exact Git blob and SHA256 checks in provenance.json. They retain their original kernel-3.4 names and contents. They are not adapted Linux 4.4 profiles and are not in the enabled build catalogue. Editor swap files were excluded. The manifest also records the other 323 non-swap file paths in the complete upstream board catalogue for later selection.

The initial whole-repository recursive API tree was truncated. Board catalogue evidence was therefore obtained through an independent recursive boards subtree, which was not truncated. This audit does not claim an exhaustive code comparison of the full donor repository.

## Next evidence to collect

Trace the real MT7603 k/v/WPA3 configuration path and compare implementation files with our pinned 4.4 drivers. Inspect any donor-specific commits affecting WR1200JS stability before selecting changes. Keep a separate pinned audit for each further repository supplied by the user.
