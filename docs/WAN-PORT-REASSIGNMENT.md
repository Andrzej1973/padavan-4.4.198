# WR1200JS WAN socket reassignment — implementation checkpoint

Requirement: PROJECT-DELIVERY-SCOPE.md, WAN port reassignment section. Replace
a damaged original WAN socket with LAN1–LAN4, retain existing connection
settings and isolate the old WAN where supported. No remote port change is
authorized by this requirement.

## Source evidence

Pinned base: c25283e915a2a00a763774dd255b14aff997285e.

- trunk/configs/boards/WR1200JS/kernel-4.4.x.config assigns
  CONFIG_RAETH_ESW_PORT_WAN=0 and LAN1..LAN4=1..4. This is source mapping,
  not physical socket validation or proof of the effective built mapping.
- trunk/user/rc/net_wan.c, phy_status_port_link_wan reads wan_src_phy for link
  monitoring. The corresponding web variable alone does not reassign VLANs.
- trunk/user/rc/net_lan.c, switch_config_vlan sets VLAN rules before calling
  phy_bridge_mode; restart_switch_config_vlan coordinates link detection and
  may perform full_restart_wan.
- trunk/linux-4.4.x/drivers/net/ethernet/raeth/mtk_esw/ioctl_mt762x.c maps UAPI
  port IDs and masks through WAN_PORT_X, LAN_PORT_* and MASK_* definitions.
  WAN/LAN masks also feed bridge membership and VLAN entries. Changing only
  the link-monitor key would leave forwarding membership unchanged.

## Current code

The initial planner CI passed: run 38793467150 at f745a93. The downloaded
kernel-effective.config from successful build 309 confirms WAN=0 and
LAN1..LAN4=1..4. However, effective topology is not determined by that config
alone: esw_common.h explicitly defines CONFIG_MT7530_GSW,
CONFIG_GE2_INTERNAL_GMAC_P5 and CONFIG_RAETH_BOTH_GMAC. The corresponding
ioctl_mt762x.h branch defines CPU WAN=5 and CPU LAN=6. Never assume a shared
CPU port merely because these definitions are absent from the Kconfig file.

collect-topology.py now compiles a small host-only program against the exact
driver/common headers and relevant effective Kconfig defines. It records
resolved CPU/external masks and all five plans, plus config/header hashes,
as wan-port-topology.json in the full build. No switch access is performed.
Its first compiler execution is pending CI; the Windows environment has no
gcc in PATH, so a local compiled result is not claimed. The report remains
source_only=true and runtime_verified=false even after a successful run.

tools/wan-port/plan.h is a pure, uninstalled planner for external membership:
selection 0 restores original WAN; selections 1..4 use the supplied labelled
LAN mapping. The selected socket is removed from LAN and the old WAN is kept
in a separate isolated mask rather than silently made a LAN socket. Maps
must contain five unique valid bit positions. The planner does not read or
write NVRAM, issue ioctls or assume CPU membership/VLAN IDs.

check-plan.c is wired into a named sanitizer CI step. It covers every choice,
reversed mappings, original restoration, disjoint membership and invalid maps.
Its first execution is pending. No firmware option, driver change or WebUI
control has been activated by this increment.

## Required remaining work

### VLAN-table transformation candidate

tools/wan-port/vlan-plan.h now transforms a freshly generated original-role
VLAN table into a selected-port plan. It copies original WAN membership,
untag/swap behavior and PVID to the selected normal LAN socket, removes that
socket from its old LAN entry and excludes the damaged original WAN from all
active VLAN entries. CPU bits, VLAN IDs and other sockets' egress/PVID values
remain unchanged. Tagged Internet/IPTV rules on the WAN and IPTV reservations
on different LAN sockets are preserved.

Selecting an IPTV/tagged/reserved socket refuses with a conflict rather than
clearing its rules. Merged LAN/WAN baseline membership also refuses replacement.
Duplicate VLAN IDs, invalid egress masks, CPU/external overlap and missing
baseline LAN membership are rejected. Restoration means regenerating the
original-role baseline from preserved configuration, not transforming an
already remapped output back again. In-place transformation is not supported.

The result separately reports actual LAN VLAN membership and reserved external
sockets: the lower-level generic LAN inventory mask alone must not be used as
a forwarding matrix when IPTV reservations exist. Old-WAN isolation still
requires the driver to apply ingress security/port-matrix controls in addition
to VLAN membership exclusion. No registers, PVIDs or NVRAM are written by this
candidate. Its sanitizer fixture is wired into CI; first execution is pending.

### Driver/controller integration still open

The driver part is now written: `overlay/padavan-4.4/patches/wan-port-runtime.diff`
adds a runtime WAN-port override with an unchanged default path, and
`docs/WAN-RUNTIME-ABI.md` records the verified ABI and the remaining work. The
paragraph below still describes what is missing after that patch.

Inspect effective board/GMAC/CPU switch topology, then implement coherent
runtime driver support for WAN/LAN masks, VLAN membership/PVIDs, UAPI port
mapping and status. Preserve existing IPTV/VLAN rules and reject conflicting
changes without silently clearing settings. Coordinate WAN restart, firewall,
hardware NAT and link monitoring; add authenticated selection/restore,
confirmation, observed vs requested state, default-original NVRAM and the
model guide. An external-port mask planner is not a working WAN replacement.

Physical acceptance must establish labelled socket mapping, DHCP/IPoE on each
chosen port, old-WAN and remaining-LAN isolation, VLAN/IPTV behavior, supported
hardware acceleration, reboot persistence and restore-original operation.
Retain recovery access and get specific authorization before any live change.
