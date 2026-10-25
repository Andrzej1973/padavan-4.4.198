# Zapret2 for WR1200JS — integration plan (Stage 2)

Recorded 2026-10-25 after the pinned source base was accepted. This is a plan
and an audit of the current image; nothing is enabled yet and the router is
untouched.

## Verified target capabilities (image #535 / board config)

| Item | State | Evidence |
| --- | --- | --- |
| `CONFIG_NETFILTER_NETLINK_QUEUE` | `y` | `overlay/padavan-4.4/trunk/configs/boards/WR1200JS/kernel-4.4.x.config` |
| `CONFIG_NETFILTER_XT_TARGET_NFQUEUE` | `y` | same |
| `CONFIG_NETFILTER_XTABLES` | `y` | same |
| `CONFIG_IP_NF_MANGLE` / `CONFIG_IP6_NF_MANGLE` | `m` | same; `iptable_mangle.ko`, `ip6table_mangle.ko` present in ROMFS |
| `CONFIG_NETFILTER_NETLINK_GLUE_CT` | **not set** | NFQUEUE conntrack metadata unavailable; Zapret2 keeps its own userspace conntrack pool (`nfq2/conntrack.h`) |
| `CONFIG_NF_TABLES` | not set | iptables-legacy path only |
| `nf_conntrack_netlink.ko`, `xt_CT.ko` | present | ROMFS listing |
| Lua 5.1 runtime | present | `liblua.so.5.1.5` (288 888 B), `CONFIG_FIRMWARE_INCLUDE_LUA=y` |
| zlib | present | `libz.so.1.3.1` (101 272 B) |
| `libmnl`, `libnfnetlink`, `libnetfilter_queue` | **absent** | ROMFS listing |
| `nfqws2` | absent | ROMFS listing |
| `CONFIG_FIRMWARE_INCLUDE_ZAPRET2` | commented out | `configs.build/wr1200js.config`; no build consumer found in the pinned upstream fork |

## Consequences

- Kernel-side NFQUEUE is ready; no kernel rebuild is strictly required for a
  first build. `GLUE_CT` would only matter if we later need kernel conntrack
  metadata inside the queue.
- The missing userspace libraries are the real dependency gap. Preferred
  approach: build them **statically** into `nfqws2` so the image gains one
  binary instead of three extra shared objects.
- Lua is already shipped for Shadowsocks, so strategies can use the existing
  `liblua.so.5.1.5` (`LUA_JIT=0`, `LUA_VER=5.1`). A LuaJIT build would add a
  second runtime and is not justified yet.
- Upstream `nfq2/Makefile` defaults to LTO/PIE. These must be tested with the
  Padavan MIPS/uClibc toolchain and disabled if unsupported.

## Ordered work items

1. Vendor pinned `libmnl`, `libnfnetlink`, `libnetfilter_queue` sources with
   per-file manifests (same model as the Zapret2 snapshot).
2. Add an overlay package Makefile that cross-builds the three libraries as
   static archives and links `nfqws2` with `-lz -lm` plus the target Lua.
3. Stage `/usr/sbin/nfqws2` and the required Lua strategy files; nothing else
   from the upstream tree is shipped by default.
4. Add service and firewall integration with explicit enable/disable and full
   rollback; no automatic start on boot until verified.
5. Image gates: MIPS ELF, dependency closure (only libraries present in the
   image), strategy presence, and measured TRX size delta against build #535
   (`12 842 033` bytes).
6. Runtime acceptance only with separate owner approval: queue counters,
   traffic through the queue, VPN/DNS/IPv6 and HWNAT interactions, rollback.

## Size policy

The old `~0.3MB` config comment is only an estimate. Record:

- uncompressed `nfqws2` size,
- added Lua strategy size,
- compressed TRX delta,
- runtime RSS after start.

Do not claim a size until the build artifact is measured.
