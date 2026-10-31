# Zapret2 source base for Padavan

Recorded 2026-10-24. This is a source snapshot and integration inventory, **not** an enabled firmware feature or a router test.

## Pinned upstream

- Author: [bol-van](https://github.com/bol-van); selected project: [zapret2](https://github.com/bol-van/zapret2).
- Pinned upstream commit: [`4a33055448ce5f4e7acc704e1fbe0d8a8a6aa08d`](https://github.com/bol-van/zapret2/tree/4a33055448ce5f4e7acc704e1fbe0d8a8a6aa08d).
- Complete source snapshot: `third_party/bol-van/zapret2/` (253 files). Per-file SHA-256 and the source archive hash are in `third_party/bol-van/zapret2-source-manifest.json`. This makes this specific snapshot available locally without a live upstream checkout.
- Offline integrity check: run `python tools/zapret2/verify-source-base.py` from the repository root. It rejects missing, extra or modified files and unexpected symlinks. The archive SHA-256 records the downloaded upstream archive; the verifier checks the extracted files against their manifest entries.
- Git normalizes seven upstream Windows text files in its index; the vendored `.gitattributes` restores their CRLF bytes on checkout. The manifest verifies checkout bytes, not `git show :path` bytes. Keep those upstream line-ending rules when moving the snapshot between Windows and Linux.
- Upstream's [MIT license](https://github.com/bol-van/zapret2/blob/4a33055448ce5f4e7acc704e1fbe0d8a8a6aa08d/docs/LICENSE.txt) is retained in the snapshot. Some embedded files carry their own notices, notably `nfq2/kavl.h` (MIT), `nfq2/uthash.h` (BSD-style) and `nfq2/crypto/aes.c` (public-domain notice). Review every incorporated component's notice during packaging.

## What is useful for the firmware port

| Snapshot path | Intended use | Porting gate |
| --- | --- | --- |
| `nfq2/` | `nfqws2` packet-processing source and build rules | Cross-compile for the Padavan MIPS target; verify ABI, memory, dependencies and packet path. |
| `lua/` | Lua strategy library, auto/obfuscation modules and tests | Choose a compatible Lua runtime; verify strategy behavior and package only needed modules. |
| `common/`, `init.d/`, `config.default` | Firewall helpers, service lifecycle and starting configuration | Adapt to Padavan's init/firewall conventions; do not install upstream OpenWrt/SysV scripts unchanged. |
| `ip2net/`, `mdig/`, `ipset/` | List conversion, DNS lookup and list management | Determine which tools/lists are needed; bound RAM, flash, update traffic and failure handling. |
| `blockcheck2.sh`, `blockcheck2.d/` | Diagnostic strategy exploration | Optional diagnostic tooling, not an automatic production strategy or background task. |
| `files/fake/` | Example packet payloads used by strategies/tests | Select only reviewed payloads; inspect provenance and avoid unrelated data in the image. |
| `docs/` | Upstream manual, change log, license and build notes | Reference for port and acceptance tests; not proof of Padavan support. |

The full upstream source snapshot also contains other-platform files, small prebuilt Windows objects, installers and CI definitions for provenance. Their presence does not enable or invoke them in Padavan; none is selected for the firmware image by this import.

## Dependency and compatibility gate

The upstream [`nfq2/Makefile`](https://github.com/bol-van/zapret2/blob/4a33055448ce5f4e7acc704e1fbe0d8a8a6aa08d/nfq2/Makefile) uses zlib, libnetfilter_queue, libnfnetlink, libmnl and libm on Linux. It tries LuaJIT first, with a Lua fallback. The [OpenWrt build notes](https://github.com/bol-van/zapret2/blob/4a33055448ce5f4e7acc704e1fbe0d8a8a6aa08d/docs/compile/build_howto_openwrt.txt) are guidance, not a Padavan build recipe. Resolve target headers/libraries and kernel NFQUEUE/conntrack/firewall capabilities against the actual WR1200JS effective config. Check GCC/MIPS compatibility, especially upstream LTO/PIE flags, instead of assuming the desktop build flags work. The old `~0.3MB` config comment is only an estimate; measure the full dependency closure and final compressed TRX before making a size claim.

Stage 2 integration sequence: target dependency audit; minimal source build; Padavan service/firewall hooks with explicit enable/disable and rollback; strategy/list policy; WebUI using existing apply mechanism; image-content and size checks; then read-only and separately authorized runtime acceptance. Verify interactions with HWNAT, VPN, DNS, IPv4/IPv6, reboot and failure paths. No selector was enabled by this source import.

## Other bol-van repositories reviewed

- [`zapret`](https://github.com/bol-van/zapret): prior generation; useful only as a migration/reference comparison. User explicitly chose **Zapret2 only**, so do not restore the old `CONFIG_FIRMWARE_INCLUDE_ZAPRET` selector or ship Zapret 1.
- [`rulist`](https://github.com/bol-van/rulist): dynamic, region-specific block lists; **not bundled**. Decide list sources, update policy and redistribution rights separately. Do not make the firmware depend on a live list service by default.
- [`zapret-win-bundle`](https://github.com/bol-van/zapret-win-bundle), [`bins`](https://github.com/bol-van/bins), [`build`](https://github.com/bol-van/build), [`musl-cross`](https://github.com/bol-van/musl-cross): Windows bundle, prebuilt binaries and build/toolchain aids. They are not substitutes for a target-specific, reproducible source build and are not imported into the firmware base.
- Other repositories on the [author's profile](https://github.com/bol-van?tab=repositories) are unrelated to this Padavan Zapret2 port; do not copy them merely because they share an author.

This source-base task is complete as an inventory and pinned local copy. Stage 2 firmware integration remains open under `docs/PROJECT-DELIVERY-SCOPE.md` after WR1200JS baseline acceptance.

## Final source-base check (2026-10-25)

- `python tools/zapret2/verify-source-base.py` passed: all 253 files and 2,516,830 bytes match the manifest. Git tracks all 253 vendored files.
- GitHub's `bol-van/zapret2` `master` and the pinned commit both resolve to `4a33055448ce5f4e7acc704e1fbe0d8a8a6aa08d` at this check. Future upstream changes require a new reviewed snapshot and manifest, not an unpinned download during a firmware build.
- `configs.build/wr1200js.config` and `configs.build/mi-4.config` still have `CONFIG_FIRMWARE_INCLUDE_ZAPRET2` commented out. The imported base supplies source and documentation only; no target binary, firewall rule, service or WebUI control was enabled.
- The first Stage 2 action remains a target dependency and kernel NFQUEUE audit. Do not infer a working Padavan port from this completed source-base check.
