# Ljzkirito public repositories: Padavan relevance audit — 2026-10-27

The GitHub user API listed 38 public repositories on 2026-10-27. This is a
review of the public inventory, not a claim about private repositories or
working firmware. The earlier focused audit of the archived RM2100 Actions
repository is `LJZKIRITO-RM2100-DONOR-AUDIT-2026-10-27.md`.

## Padavan and board candidates

| Repository, reviewed HEAD | Observed contents | Disposition |
| --- | --- | --- |
| [`MeIsReallyBa-padavan-4.4`](https://github.com/Ljzkirito/MeIsReallyBa-padavan-4.4), `2e7659369bfd8818b99abbe9b6f8f3735c9f2331` | Archived fork of `MeIsReallyBa/padavan-4.4`; GitHub compare reports six commits ahead and six behind parent `main`. Its six fork commits change RM2100 config, CI, default `192.168.5.x` addresses, CN help text, user-specific IPv6 port ACCEPT rules and a hosts entry. No fork-specific kernel or Wi-Fi driver changes were in that comparison. | Do not replace our pinned 4.4.198 base. Keep commit and compare as provenance; the firewall ports and hosts entry are private-network choices, not reusable fixes. |
| [`Actions-Padavan_Xiaomi-Mini`](https://github.com/Ljzkirito/Actions-Padavan_Xiaomi-Mini), `aded2cafa1037c3f8a1b31c4efad46c6be47825f` | Archived 2021 MI-MINI Actions wrapper around moving `hanwckf/rt-n56u`, with a toggle list, optional toolchain rebuild, release SHA256 and automatic run deletion. No firmware source or standalone Mi Mini profile is stored here. | Keep as historical Mi Mini feature-budget reference for the later Mi Mini stage. The old source/kernel, moving dependencies, blind `sed` config toggles and release deletion cannot be transplanted into the planned 4.4.198 board port. |
| [`Padavan-Build`](https://github.com/Ljzkirito/Padavan-Build), `910079d16d4ed9d284682412516a3079e16e250e` | Fork of `TurBoTse/Padavan-Build`; workflow offers WR1200JS, MI-4 and many other boards plus toolchain choices, but this fork stores only RM2100, JDCloud and ZTE config files. It clones moving `TurBoTse/padavan` main and uses moving action refs. | Candidate UI pattern for an explicit per-board build selector. Our board catalog and pinned uClibc source/toolchain already address this more strictly. No WR1200JS config is supplied by this fork. Do not enable its default release/run deletion or musl cross-build without ABI and image proof. |
| [`Actions-JDCloud-RE-SP-01B`](https://github.com/Ljzkirito/Actions-JDCloud-RE-SP-01B), `79b8637e70341f00098e587b3af42cdfb387b9b0` | Despite its name, current default branch builds `padavanonly/immortalwrt` on Linux 5.10/OpenWrt, using feeds and UCI. Its README warns that changing Turbo ACC can break HWNAT on that different device. | Keep only as a general reminder to test hardware acceleration after configuration changes; not source or scripts for Padavan 4.4.198. |

## Network package candidates

| Repository, reviewed HEAD | Candidate | Required comparison before adoption |
| --- | --- | --- |
| [`openwrt-packages`](https://github.com/Ljzkirito/openwrt-packages), `e4f4d68e32130c6a5d9c318ca09ed8ed39bd9c06` | Its OpenWrt `ppp/patches/330-retain_foreign_default_routes.patch` scopes deletion to the PPP device; `340-populate_default_gateway.patch` sets peer gateway; `207-lcp_mtu_max.patch` caps negotiated MTU. These are concrete WAN/PPPoE review candidates. | At the scheduled WAN stage compare exact `pppd` version and `sys-linux.c`/`lcp.c` in pinned Padavan source, verify whether the changes are already present, then test route ownership, reconnect and MTU on a recoverable device path. Do not apply OpenWrt patches blindly. The same repo has old SmartDNS, miniupnpd and AdGuardHome recipes tied to OpenWrt/UCI dependencies. |
| [`smartdns-openwrt`](https://github.com/Ljzkirito/smartdns-openwrt), `e5d1f4183a40eab4bd0c9e645b1baf1e19c2f3b1` | The current `PikuZheng` branch packages SmartDNS 48.4.2 prebuilt with dashboard; its Makefile permits aarch64, arm and x86_64 and has no MIPS package branch. | No binary for MT7621/WR1200JS. Keep upstream version/features as a future DNS service reference only; any Padavan port needs source build, libc/dependency, flash-size and runtime checks. |
| [`adguardhome-openwrt`](https://github.com/Ljzkirito/adguardhome-openwrt), `eb689187d1f3b7bafae1b02870e38409af2e7e54` | Very small OpenWrt init/config packaging. | UCI/OpenWrt lifecycle is incompatible with Padavan's service framework; no direct import. |

The remaining public repositories are other SoC/OpenWrt build wrappers,
bootloaders, LuCI themes, VPN/application forks, IPTV lists or unrelated
desktop/personal projects. They do not supply a reviewed WR1200JS Padavan
4.4.198 driver, IoT isolation implementation or matching WebUI backend.
Their names and metadata were inventoried; no deep code/runtime claim is made
for them. The `bl-mt798x-dhcpd` and Airoha/MT798x repositories target other
SoCs; the LuCI themes target OpenWrt rather than Classic/Modern Padavan.

## Decision and evidence boundary

1. Keep this source catalog and the three specific PPP patches as candidates.
   Do not modify WR1200JS WAN until pinned-source and route-behavior checks.
2. Keep the Mi Mini wrapper and multi-board selector as references for the
   already planned later board stages. They do not qualify a new board.
3. The owner's Padavan fork contains board defaults and user network rules,
   not an IoT/driver fix. No source or router configuration was changed by
   this audit.
4. Apply component licenses and attribution individually before importing
   any future code. GitHub repository license metadata alone does not cover
   inherited OpenWrt, kernel, package and upstream contents.
