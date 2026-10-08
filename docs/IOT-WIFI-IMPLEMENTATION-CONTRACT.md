# WR1200JS separate IoT Wi-Fi implementation contract

Approved 2026-10-08. Source inspected at vipshmily/padavan-4.4 commit `c25283e915a2a00a763774dd255b14aff997285e`. This is an implementation contract and partial source audit, not device support proof.

## Current constraints

`trunk/user/rc/ralink.c` declares `i_fphy[2]` and `i_val_mbss[2]` and sets `i_ssid_num = 2` (main plus guest). It emits two-entry NoForwarding, NoForwardingMBCast, HideSSID and HT_MCS lists, and individual guest SSID/password fields. Raising BssidNum alone leaves profile fields incomplete and may introduce out-of-bounds accesses if loops are generalized.

`trunk/user/rc/net_wifi.c` explicitly starts/stops main and guest interfaces and adds the guest interface to `IFNAME_BR`. A third IoT interface needs its own lifecycle and bridge attachment. Existing guest isolation is not evidence of a separate IoT subnet.

Both driver families expose MBSS profile parsing and virtual-AP initialization. Their headers select `MAX_MBSSID_NUM` from chip capability only under `MBSS_SUPPORT`; otherwise it is 1. Beacon array capacity is not proof of effective chip capacity. Trace MT7603E and MT7612E capability initialization and actual build definitions, including AP-client/repeater reservations, before selecting an interface index or advertising three simultaneous SSIDs.

## Required implementation

1. Preserve main and guest network settings. IoT uses a third BSS, initially 2.4 GHz; shares the physical radio channel and width constraints.
2. Extend every relevant profile field consistently: SSID, authentication, cipher, PSK, isolation, hidden status, rate policy and other per-BSS settings. Default OFF retains the existing two-BSS profile where possible.
3. Create an isolated IoT bridge, non-overlapping subnet and scoped DHCP/DNS configuration. Start/stop the third interface with radio and network lifecycle; never attach it to the primary LAN bridge as a convenience.
4. Integrate IPv4 and IPv6 firewall policy, blocking primary-LAN and router-administration access by default while explicitly permitting DHCP/DNS and requested internet traffic. Evaluate hardware offload paths so isolation cannot be bypassed.
5. Add authenticated WebUI enable, SSID/security/password, subnet/status, local QR and explicit controller exceptions. Default WPA2-Personal/AES, runtime OFF. Discovery/mDNS and client isolation require deliberate policies compatible with the user's IoT devices.
6. Verify actual target compilation, image assets, lifecycle and persistence, followed by device tests with primary, guest and IoT simultaneous. Verify DHCP, DNS, inter-network isolation, allowed exceptions, restart behavior and AP-client/repeater compatibility separately.

## Evidence still missing

Effective per-chip third-BSS capacity, complete profile/lifecycle integration, isolated subnet/firewall, WebUI, target build and live-device behavior remain unverified. No router configuration changes are authorized by this audit.


## Capability initialization traced — 2026-10-08

MT7603 `mt7603_chip_init` calls `mt_bcn_buf_init`; the latter assigns BcnMaxHwNum=16 and BcnMaxNum=16. The header may reduce the array ceiling to 8 under ECONET_ALPHA_RELEASE, which still exceeds three; confirm effective definitions in a target probe.

MT76x2 initialization calls `rlt_bcn_buf_init`. Its MT76x2 branch assigns hardware beacon count 8. With APCLI_SUPPORT it sets BcnMaxNum to 8 minus MAX_MESH_NUM; the inspected header defines MAX_MESH_NUM as 0. This gives a source-level candidate capacity of eight, not proof of eight working networks.

The effective kernel configuration downloaded from successful WR1200JS run 37823022372 enables CONFIG_MT7603E_MBSS_SUPPORT and CONFIG_MT76X2_AP_MBSS. Effective driver preprocessing, target capacity probes and a third-BSS device test remain required. No production profile has been changed by this audit.
