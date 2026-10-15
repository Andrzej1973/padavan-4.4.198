# WAN reassignment — runtime switch ABI (source-verified)

Requirement: `docs/PROJECT-DELIVERY-SCOPE.md`, WAN port reassignment section, and
the remaining-work list in `docs/WAN-PORT-REASSIGNMENT.md`. This document records
the *runtime* ABI that any implementation must use. It is analysis plus a plan;
no driver or firmware change is claimed by this file.

## Verified sources

Pinned base `c25283e915a2a00a763774dd255b14aff997285e` of
`https://github.com/vipshmily/padavan-4.4` (`sources.lock.json`,
`id: padavan-kernel-userspace-base`):

- `trunk/linux-4.4.x/drivers/net/ethernet/raeth/mtk_esw/ioctl_mt762x.h`
  sha256 `8a902e1df1a229fd4e7dd65580956f9f88cc1ea2dd34116458cfc725a96c9c20`.
- `.../mtk_esw/esw_common.h` sha256
  `b94722a49e6122a40dd418dbbb34f915f710b54d97fefcb3e287540e8a92ba3c`.
- `.../mtk_esw/ioctl.c` (dispatcher), `.../mtk_esw/ioctl.h` (UAPI),
  `.../mtk_esw/ioctl_mt762x.c` (49,453 bytes).
- `trunk/user/rc/switch.h`, `trunk/user/rc/switch_mtk_esw.c` (15,803 bytes),
  `trunk/user/rc/net_lan.c`, `trunk/user/rc/net_wan.c`.

Both header hashes above are the ones recorded by build 310's
`wan-port-topology.json` and were re-derived from the pinned archive on
2026-10-15, so the topology report is verified end to end.

## Physical switch layout for WR1200JS

`esw_common.h` lines 4–6 define `CONFIG_MT7530_GSW`,
`CONFIG_GE2_INTERNAL_GMAC_P5` and `CONFIG_RAETH_BOTH_GMAC` in the header itself;
they are absent from the Kconfig file, which is why the effective topology cannot
be read from `kernel-effective.config` alone. Under those defines
`ioctl_mt762x.h` lines 48–55 select:

- `WAN_PORT_X` = `CONFIG_RAETH_ESW_PORT_WAN` = 0, `MASK_WAN_PORT_X` = `1u<<0`
- `WAN_PORT_CPU` = 5, `MASK_WAN_PORT_CPU` = `1u<<5`
- `LAN_PORT_CPU` = 6, `MASK_LAN_PORT_CPU` = `1u<<6`
- `ESW_EPHY_ID_MAX` = 4, `ESW_MASK_EXCLUDE` = 0

This matches `WR1200JS-BUILD310-TOPOLOGY.json` exactly (WAN 0, LAN 1–4, CPU WAN
5, CPU LAN 6, masks 1/30/32/64, excluded 0).

## Two port spaces, and the mapping between them

User space never uses physical port numbers. `ioctl.h` lines 96–117 define the
hardware-independent space: ports `SWAPI_PORT_WAN`=0, `SWAPI_PORT_LAN1..4`=1..4,
`SWAPI_PORT_LAN5`=5, `SWAPI_PORT_CPU_LAN`=14, `SWAPI_PORT_CPU_WAN`=15, with
`SWAPI_PORTMASK_*` bits, and `SWAPI_VLAN_RULE_WAN_INET`=0 … `WAN_LAN4`=5
(`ioctl.h:150`).

`get_ports_mask_from_uapi()` and `get_port_from_uapi()` in `ioctl_mt762x.c`
translate that space into physical masks *through the compile-time macros*, so
`SWAPI_PORTMASK_WAN` always means physical port `WAN_PORT_X`, and
`SWAPI_VLAN_RULE_WAN_INET` always means "the WAN port". A reassignment therefore
cannot be expressed purely as a different UAPI mask today.

## Command encoding and available commands

An ioctl request is `(param << 8) | command` (`ioctl.h:28`); `ioctl.c` splits it
back and the parameter selects the port or sub-index. Commands exported to `rc`
through `switch.h` / `switch_mtk_esw.c`:

| Command | ID | Notes |
| --- | --- | --- |
| `MTK_ESW_IOCTL_STATUS_LINK_PORT` / `_PORTS_WAN` / `_PORTS_LAN` | 10/11/12 | link state |
| `MTK_ESW_IOCTL_PORTS_WAN_LAN_POWER` | 42 | `param` selects WAN or LAN half |
| `MTK_ESW_IOCTL_BRIDGE_MODE` | 50 | `phy_bridge_mode(mode, isolation)` |
| `MTK_ESW_IOCTL_PORT_FORWARD_MASK` | 55 | GSW only; exposed solely as the debug CLI form `55 [MASK] [PORT]` |
| `MTK_ESW_IOCTL_VLAN_RESET_TABLE` | 60 | |
| `MTK_ESW_IOCTL_VLAN_ACCEPT_PORT_MODE` | 62 | |
| `MTK_ESW_IOCTL_VLAN_CREATE_PORT_VID` | 63 | `phy_vlan_create_port_vid()` |
| `MTK_ESW_IOCTL_VLAN_CREATE_ENTRY` | 64 | `phy_vlan_create_entry()` |
| `MTK_ESW_IOCTL_VLAN_RULE_SET` | 65 | `phy_vlan_rule_set()` |

`phy_vlan_create_entry(vid, member, untag, fid)` packs
`(fid<<16 | vid)` into the parameter and `(untag<<16 | member)` into the value
with UAPI masks; `phy_vlan_rule_set(rule, vid, prio, tagged)` packs
`(tagged<<24 | prio<<16 | vid)`.

## Why this is a driver change, not a user-space reconfiguration

Every WAN/LAN classification decision in `ioctl_mt762x.c` is derived from
`WAN_PORT_X` / `MASK_WAN_PORT_X` / `WAN_PORT_CPU` / `MASK_WAN_PORT_CPU`, at the
port matrix (`:323`, `:945`–`:1006`), VLAN bridge membership and PVID
(`:655`, `:677`–`:678`, `:709`–`:731`, `:791`, `:809`), the MAC-table mask
(`:1044`), link status and power (`:1240`–`:1362`) and the WAN interface
statistics (`:1820`–`:1824`).

The rebuild path that gives the switch its state is `change_bridge_mode()`
(`:1372`), which calls `esw_mask_bridge_isolate()` and
`esw_vlan_bridge_isolate()`, and `esw_ioctl_init_post()`, which runs both again
at init. User space drives it from `switch_config_vlan()` (`net_lan.c:413`,
called at `net_lan.c:106`, `net_lan.c:489` via `restart_switch_config_vlan()`,
and `net_wan.c:1475` inside `full_restart_wan()`), applying
`phy_vlan_rule_set()` (`net_lan.c:465`) and then `phy_bridge_mode()`
(`net_lan.c:467`).

Today `wan_src_phy` only changes which port the link monitor watches
(`net_wan.c:1936`–`:1945`); it does not move forwarding membership. That matches
the finding already recorded in `docs/WAN-PORT-REASSIGNMENT.md`.

## Chosen approach

Add a runtime WAN-port override inside the switch driver, so the existing WAN
semantics (ingress rule, PVID, bridge/VLAN membership, link monitoring, power and
statistics) stay exactly as they are and only the physical external port they
apply to changes. Concretely:

1. Replace the compile-time `WAN_PORT_X` / `WAN_PORT_CPU` uses in
   `ioctl_mt762x.c` with runtime accessors initialised from the macros, so the
   default behaviour is unchanged and provably identical.
2. Add one command (for example `MTK_ESW_IOCTL_WAN_PORT_X_SET`) that validates a
   requested external port against `ESW_EPHY_ID_MAX`, rejects the CPU ports,
   rejects `ESW_MASK_EXCLUDE` bits, stores the override and then re-runs the
   existing rebuild path plus `esw_mac_table_clear()`.
3. Keep the old WAN port out of every active VLAN entry and give it an empty
   forward mask, which is the isolation the requirement asks for.
4. Expose the result to `rc` through `switch.h`; keep `wan_src_phy` in step for
   link monitoring.

A user-space-only variant using commands 55/63/64/65/62 is rejected as the
primary mechanism: it cannot re-point the WAN rule and PVID space, it is
re-applied inconsistently across `full_restart_wan()`, and it would have to
mirror internal masks that only the driver knows.

## Status

### Implemented, awaiting CI compile evidence

`overlay/padavan-4.4/patches/wan-port-runtime.diff` carries the change and the
full build applies it and then runs `tools/wan-port/verify-runtime-patch.py`:

- `g_wan_port_x` and `g_mask_wan_port_x` replace `WAN_PORT_X` and
  `MASK_WAN_PORT_X` at every runtime use. Both initialise from the board macros,
  so an untouched system behaves exactly as before; preprocessor conditions keep
  the original macros, and the WAN identifier was moved out of the one `case`
  label it appeared in.
- `MTK_ESW_IOCTL_WAN_PORT_X_SET` (66) validates the requested port (external PHY,
  not a CPU port, not excluded by the board mapping) and, once the switch is
  initialised, re-runs the existing bridge and VLAN rebuild plus a MAC table
  clear. `MTK_ESW_IOCTL_WAN_PORT_X_GET` (67) reads the effective port back.
- `get_ports_mask_lan()` and the VLAN builder keep the WAN port out of the LAN
  side, and `get_isolated_port_x()` marks the board's original WAN socket while
  the WAN role is elsewhere: it is skipped by the LAN VLAN entry and its port
  matrix is forced to zero, so the damaged socket is isolated instead of
  silently becoming a LAN port. Restoring the board socket clears the isolation
  because the value is derived from `g_wan_port_x`, not stored.

Verification so far is local only: the patch applies cleanly to the pinned tree
(`git apply --check` on all three files), and the structural verifier passes on
the patched tree while failing on the unpatched tree. The MIPS cross-compile in
the full build is pending, and no device behaviour is claimed.

#### rc wiring

`overlay/padavan-4.4/scripts/integrate-wan-port.py` adds `phy_wan_port_x_set()`
to `switch.h` and `switch_mtk_esw.c`, adds `wan_switch_port()` to `net_lan.c`,
and calls it from `switch_config_vlan()` before `phy_bridge_mode()`, so the
selection is in place before the rebuild that consumes it:

- The socket comes from `wan_src_phy`, the key the WAN settings page already
  exposes as the WAN source port next to `wan_stb_x`
  (`trunk/user/www/n56u_ribbon_fixed/Advanced_WAN_Content.asp`), and `net_wan.c`
  keeps using the same key for link monitoring.
- Values outside `LAN1..LAN4` fall back to the board socket. With `vlan_filter=1`
  a socket whose tag-based rule has a valid VID is refused the same way, instead
  of having its rules silently cleared.
- Behaviour change to be explicit about: a non-zero `wan_src_phy` now moves the
  WAN role. With the key unset or zero the previous behaviour is unchanged, and
  the WAN page normalises the field back to `WAN` when `wan_stb_x` is 0.

Local end-to-end check on a copy of the pinned tree: the patch applies, the
service verifier fails before the integration step and passes after it.

### Known limits

- Only external PHYs can carry the WAN role; CPU ports and board-excluded ports
  are rejected.
- The `RAETH_GE2_MAC_TO_GPHY` branches of the status and MIB helpers still treat
  the WAN port as GE2; WR1200JS does not define that macro, and those branches
  are untouched.
- `SWAPI_WAN_BRIDGE_DISABLE_WAN` keeps its existing meaning, where the WAN socket
  acts as a LAN port.

### Remaining

1. An apply path that reports requested versus effective state (the read-back
   command exists but nothing consumes it yet), an authenticated way to change
   `wan_src_phy`, and the model guide entry.
2. Image-level evidence from the project verifiers already used for builds
   294–310, then physical acceptance on the device with explicit permission.

Physical acceptance still has to establish labelled socket mapping, DHCP/IPoE on
the chosen port, isolation of the old WAN and the remaining LAN sockets,
VLAN/IPTV behaviour, hardware acceleration, reboot persistence and
restore-original. No live change is authorised by this document.
