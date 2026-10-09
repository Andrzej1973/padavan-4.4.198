# WR1200JS IoT driver isolation source audit

Pinned source: vipshmily/padavan-4.4 commit `c25283e915a2a00a763774dd255b14aff997285e`.
This is source evidence only; target radio traffic remains unverified.

## Current 2.4 GHz candidate

The WR board l1profile selects MT7603 for ra0 and its ra virtual interfaces.
The candidate third BSS is ra2; production activation remains absent.
In `trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/ap/ap_data.c`
lines 3992-4004, associated destinations on another SSID set `to_os=TRUE`
and `to_air=FALSE`. Global inter-BSS isolation or differing VLAN IDs then
suppress delivery to the OS as well. For this path, bridge/routing firewall
integration must enforce the intended isolation and controller exceptions.
Blindly forcing global isolation would prevent these exceptions.

## Different behavior on MT76x2

In `trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x2/ap/ap_data.c`
lines 6377-6418, an associated destination sets direct forwarding, and
cross-BSS handling disables it only when global isolation or different VLAN
IDs apply. This can bypass Linux bridge/firewall handling. Do not extend the
IoT candidate to the 5 GHz driver without a scoped forwarding change and
packet/runtime verification. The current IoT generator targets 2.4 GHz only.

## Remaining acceptance work

- Audit multicast, broadcast, MWDS/APCLI and accelerated forwarding paths.
- Integrate rules before generic accepts in normal/default IPv4/IPv6 builders.
- Verify on the actual router that three SSIDs coexist, isolated DHCP/DNS work,
  primary/guest settings remain intact, and controller exceptions are scoped.
- Repeat packet checks for actual Wi-Fi stations, including L2 cross-BSS traffic.

Earlier shorthand treating both driver paths as equivalent was incomplete;
the MT76x2 direct forwarding branch above is the authoritative distinction.
