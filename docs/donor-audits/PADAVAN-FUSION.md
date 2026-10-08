# Donor audit: RikudouPatrickstar/padavan-fusion

Inspected 2026-10-08 at main `6f59c3d6f827fe9349aa8eb4e3401021d281bfd5` (2024-04-14). Only main was returned by the branch listing. Source: https://github.com/RikudouPatrickstar/padavan-fusion

## Candidate decisions

- **Base:** actual kernel Makefile specifies Linux 3.4.113. Retain our Linux 4.4.198 base; use this repository for focused implementation comparisons.
- **Compiler:** MIPS little-endian GCC 7 sample, local uClibc-ng 1.0.32 and Linux 3.4 headers. Download helper uses hanwckf/padavan-toolchain v1.1 without checksum validation. No newer or verified-compatible toolchain was established.
- **Useful roaming integration:** both advanced wireless pages expose rt_/wl_HT_80211KV and HT_80211R selectors. variables.c associates them with EVM_RESTART_WIFI2/5. ralink.c emits RRMEnable/WNMEnable from HT_80211KV and FtSupport from HT_80211R. This is actual source-level UI/backend/profile wiring, not a router runtime test.
- **Defaults differ from our requirement:** shared/defaults.c enables k/v by default (1) and disables r (0). Any port must instead keep new roaming features disabled by default and capability-gate controls for the actual driver.
- **Driver scope:** 5.0.4.0/mt7615 has RRM, WNM and FT source modules; its config.mk adds CONFIG_STEERING_API_SUPPORT, CONFIG_11KV_API_SUPPORT, CONFIG_DOT11V_WNM and DOT11K_RRM_SUPPORT directly in a later flags block. The tree also contains 7.3.0.1/mt7915. These driver versions target MT7615/MT7915; their numbers do not prove replacement compatibility with WR1200JS MT7603/MT7612.
- **Our board:** donor WR1200JS config correctly specifies 128 MB RAM but leaves MT7603 r/k/WNM/WPA3/OWE and legacy RT_DOT11R_FT/RT_DOT11K_RRM disabled. The inspected 4.1.X.X/mt76x3 config.mk also defaults r/k/v support to n. Generic UI controls do not establish these features working on WR1200JS.
- **Port review finding:** the BOARD_MT7915_DBDC branch of ralink.c calls fprintf with two FtSupport integer placeholders but only one integer argument, in both radio branches. Do not copy that block; it has undefined behavior. This finding is outside the WR1200JS branch but demonstrates the need for compiler format checks during extraction.
- **mtkiappd:** README mentions 802.11f/r/k, but this audit has not validated those code paths, build selection, protocol completeness or device behavior. Do not treat the daemon name/documentation as proof of complete k/v/r.
- **Other candidates:** README describes RTL8367S switch support and Xray/XTLS integration. RTL8367S targets other board hardware, not our MT7621 integrated switch. Xray is outside current lightweight firmware priorities; inspect package version, dependencies and footprint separately if requested.

## Preserved board references

22 original files for WR1200JS, MI-MINI, D12G, MSG1500-7615 and RT-AC85P were retained byte-for-byte under reference/boards/rikudoupatrickstar-padavan-fusion, with Git blob verification and SHA256 provenance. The complete, non-truncated boards subtree catalogue contains 340 files. References retain their Linux 3.4 names, are not adapted profiles, and do not enable automatic builds.

## Follow-up priority

Use the existing k/v/r UI -> variables -> profile path as a candidate design for our disabled-by-default, capability-aware WebUI. Trace and compile the actual MT7603/MT7612 feature modules against Linux 4.4 before exposing functional controls. Verify FT configuration and two-AP interoperability separately; k/v alone is not fast transition. No donor code has been enabled in production by this audit.
