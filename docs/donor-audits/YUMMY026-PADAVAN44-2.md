# Donor audit: yummy026/padavan4.4-2

Inspected 2026-10-08 at main `b9ddc11fe1c6f5da3c9dbd98963ba03fea14c28c` (2025-07-28, Update XY-C1.config). Only main was returned. Source: https://github.com/yummy026/padavan4.4-2

## Findings

- **Kernel:** actual Makefile confirms 4.4.198. This donor is closer to our target than the previous Linux 3.4 donors; it does not prove WR1200JS runtime stability.
- **Toolchain candidate:** both mipsel-linux-musl and mipsel-linux-uclibc samples select GCC 13 and custom local Linux 4.4 headers. The package tree includes GCC 13.3.0, and also newer version recipes such as 14.2.0/15.1.0. Recipe availability is not evidence that these versions were selected, built or tested for this firmware.
- **Libc discrepancy:** README advertises musl 1.2.5 / uClibc-ng 1.0.52, but the actual uClibc sample explicitly selects CT_UCLIBC_NG_V_1_0_51=y. The musl package tree contains 1.2.5; an actual compiler/sysroot must still be built or inspected to establish the installed version.
- **Build integration:** top-level Makefile defaults to mipsel-linux-musl and downloads from TurBoTse/padavan toolchain releases. It auto-discovers template targets and appends compiler/ccache settings. Workflow builds XY-C1 with musl, so it is not WR1200JS build evidence. Useful candidates: ccache integration and standardized OpenWrt-style package recipes.
- **Offline limitations:** top-level Makefile downloads sys/queue.h from the moving glibc master URL and streams the compiler archive into tar without checksum verification. These paths must be pinned and cached before adapting to our offline requirement. The fallback toolchain Makefile checks command -v libtool-bin (a package name rather than the normal libtool executable), which needs review before reuse.
- **ABI:** musl-built objects and shared libraries must not be mixed with our uClibc firmware. A compiler/libc migration requires rebuilding the complete userspace dependency closure, checking target ABI/loader/thread/TLS/atomic behavior and legacy kernel/driver compilation. Evaluate GCC 13 with uClibc separately before deciding whether to change libc.
- **Wireless:** donor MT76x3 os/linux/config.mk is byte-identical to our pinned vipshmily base c25283e915a2a00a763774dd255b14aff997285e. It defaults HAS_DOT11R_FT_SUPPORT, HAS_DOT11K_RRM_SUPPORT and HAS_DOT11V_WNM_SUPPORT to n. This file offers no new roaming implementation. The MT76x2 directory exists, but its config.mk was not found at the same expected path; a full source/build path comparison remains pending. No kthread/HNAT fix was verified.
- **WR1200JS:** kernel config selects MT7603 plus MT7612 and enables Wi-Fi HNAT. Do not overwrite our deliberately controlled LAN-only factory HNAT policy with donor defaults.
- **Packages:** ttyd 1.7.7 matches our optional candidate. OpenSSL recipe is 3.0.16, older than our 3.5 selection. Its SHA256-based package recipes are useful examples for source preservation; do not downgrade our package solely to match this donor.

## Preserved references

20 original files for WR1200JS, MI-4, G-AX1800, G-AX1800-B and ZTT-RX6000 are retained under reference/boards/yummy026-padavan4.4-2, with Git blob verification and SHA256 provenance. The complete non-truncated boards catalogue contains 220 files. The two G-AX1800 variants have separate profiles; do not assume identical port mappings. These references do not enter the automatic build matrix or establish hardware validation.

## Recommended follow-up

Prioritize an isolated GCC 13/uClibc evaluation and comparison of package/download/ccache infrastructure. Record exact compiler and sysroot versions from built artifacts, compile our real kernel/drivers and selected package closure, then test runtime before production adoption. Preserve donor licenses and all recursive dependencies offline. No toolchain, driver or service was switched in production by this audit.
