# Donor audit: tsl0922/padavan

Inspected 2026-10-08. main: `f9018b198f24681b8d77886bc3b3d679b50b9251` (2023-10-21, SmartDNS Release43 update). Legacy branch 3.4.x: `b46df2842037fc38688a44b1a42e164546267267` (2021-06-14). Repository pushed_at is later than the main commit date; do not equate those dates. Source: https://github.com/tsl0922/padavan

## Useful candidates

- Actual main kernel is **4.4.198**. The donor is oriented toward K2P; its workflow builds K2P/K2P-NANO/K2P-USB with musl. This is not WR1200JS runtime evidence.
- Toolchain Makefile uses crosstool-NG **1.26.0**, with separate local musl/uClibc samples, MIPS32r2 and custom Linux 4.4 headers. Both samples select GCC 13; uClibc sample selects **1.0.43**. README advertises GCC 13.2.0 and musl 1.2.4, but binary compiler/sysroot versions have not been independently verified here.
- Structured OpenWrt-style package recipes, checksummed source archives, ccache and single-package build targets are useful reference implementations for our build/offline infrastructure.
- **ttyd 1.7.4** and **libwebsockets 4.3.2** recipes are older than our optional 1.7.7/4.3.3 candidate. Integration evidence is useful, but no downgrade is needed. ttyd.sh binds to br0, uses login, and configures a writable terminal. It also writes a default port and commits NVRAM when the field is missing; avoid carrying that implicit persistence into our deferred optional integration without review.
- **SmartDNS Release43 / 1.2023.43** uses pinned Git revision `1ba6ee7cb98b5b6448bc2a2be318eb3518d4de79` and a mirror hash. This is a more explicit recipe than the older Release33 donor, useful for our commented optional package. Its age does not establish that it is the latest upstream release.
- **OpenSSL 1.1.1w** is older than our 3.5 selection; retain ours.

## Constraints

A musl toolchain cannot be introduced by replacing the compiler alone: rebuild and verify the complete userspace library/program closure. Keep our current toolchain until isolated kernel, legacy driver, package and runtime checks support a migration. The donor downloads crosstool-NG and prebuilt compiler archives through curl piped to tar without a hash check in the inspected helper; add pinned hashes and local caches before adapting to offline use.

No new WR1200JS roaming implementation, Wi-Fi HNAT kthread fix or newer compatible driver was established by this audit. The legacy 3.4.x branch was identified but not exhaustively audited; no full repository comparison or runtime validation is claimed.

## Preserved board references

20 original Linux 4.4 board files for WR1200JS, MI-4, K2P and K2P-USB are preserved under reference/boards/tsl0922-padavan. provenance.json contains exact Git blob and SHA256 checks and the complete non-truncated 137-file upstream board catalogue. References are unchanged and do not enter the automatic build matrix.

## Recommended follow-up

Use package/download/ccache structure and ttyd lifecycle/UI integration as focused references. Compare SmartDNS packaging with our existing optional integration. Coordinate GCC 13 evaluation with the yummy026 donor rather than introducing separate incompatible compiler migrations. Runtime evidence is still required for the actual WR1200JS firmware.
