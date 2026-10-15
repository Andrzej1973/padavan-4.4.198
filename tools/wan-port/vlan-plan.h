#ifndef WR_WAN_VLAN_PLAN_H
#define WR_WAN_VLAN_PLAN_H
#include "plan.h"
#define WR_WAN_VLAN_ENTRIES 16
struct wr_wan_vlan_entry {
    unsigned valid, vid;
    uint32_t members, untag, swap;
};
struct wr_wan_vlan_table {
    unsigned count;
    struct wr_wan_vlan_entry entries[WR_WAN_VLAN_ENTRIES];
    unsigned pvid[32];
};
struct wr_wan_vlan_result {
    struct wr_wan_port_plan ports;
    struct wr_wan_vlan_table table;
    uint32_t lan_members_external, reserved_external;
};
enum wr_wan_vlan_status { WR_WAN_VLAN_INVALID, WR_WAN_VLAN_OK, WR_WAN_VLAN_CONFLICT };
/* Transform a freshly rebuilt ORIGINAL-role table. Do not feed an already
 * remapped table back here to restore roles: rebuild it from preserved rules.
 * CPU membership/egress and all other sockets are preserved. The driver must
 * also enforce isolated_external through ingress/port-matrix controls.
 * This pure function issues no register/ioctl/NVRAM operations. */
static inline int wr_wan_vlan_plan(const struct wr_wan_port_board *board,
    unsigned selection, uint32_t cpu_lan, uint32_t cpu_wan, unsigned lan_vid,
    const struct wr_wan_vlan_table *baseline, struct wr_wan_vlan_result *out)
{
    struct wr_wan_port_plan ports;
    uint32_t all_external, allowed, old_wan, selected;
    unsigned i, j, selected_entries = 0, old_pvid_member = 0, lan_entry = WR_WAN_VLAN_ENTRIES;
    if (!out) return WR_WAN_VLAN_INVALID;
    if (baseline == &out->table) return WR_WAN_VLAN_INVALID; /* No in-place operation. */
    memset(out, 0, sizeof(*out));
    if (!baseline || !baseline->count || baseline->count > WR_WAN_VLAN_ENTRIES ||
        lan_vid < 1 || lan_vid > 4094 || !cpu_lan || !cpu_wan ||
        (cpu_lan & (cpu_lan-1)) || (cpu_wan & (cpu_wan-1)) ||
        !wr_wan_port_plan(board, selection, &ports)) return WR_WAN_VLAN_INVALID;
    all_external = ports.wan_external | ports.lan_external | ports.isolated_external;
    if (all_external & (cpu_lan | cpu_wan)) return WR_WAN_VLAN_INVALID;
    allowed = all_external | cpu_lan | cpu_wan;
    old_wan = UINT32_C(1) << board->original_wan;
    selected = ports.wan_external;
    for (i = 0; i < baseline->count; i++) {
        const struct wr_wan_vlan_entry *entry = &baseline->entries[i];
        if (entry->valid > 1) return WR_WAN_VLAN_INVALID;
        if (!entry->valid) continue;
        if (entry->vid < 1 || entry->vid > 4094 || (entry->members & ~allowed) ||
            ((entry->untag | entry->swap) & ~entry->members)) return WR_WAN_VLAN_INVALID;
        for (j = 0; j < i; j++)
            if (baseline->entries[j].valid && baseline->entries[j].vid == entry->vid)
                return WR_WAN_VLAN_INVALID;
        if (entry->vid == lan_vid) {
            lan_entry = i;
            if (!(entry->members & cpu_lan)) return WR_WAN_VLAN_INVALID;
            if (selection && (entry->members & old_wan)) return WR_WAN_VLAN_CONFLICT;
        }
        if ((entry->members & old_wan) && entry->vid == baseline->pvid[board->original_wan])
            old_pvid_member = 1;
        if (selection && (entry->members & selected)) {
            selected_entries++;
            /* A port already assigned to IPTV/tagged traffic cannot be taken
             * silently. Preserve its configuration and report the conflict. */
            if (entry->vid != lan_vid || !(entry->untag & selected) || (entry->swap & selected))
                return WR_WAN_VLAN_CONFLICT;
        }
    }
    if (lan_entry == WR_WAN_VLAN_ENTRIES) return WR_WAN_VLAN_INVALID;
    if (selection && (selected_entries != 1 || baseline->pvid[ports.wan_phy] != lan_vid ||
        !old_pvid_member)) return WR_WAN_VLAN_CONFLICT;
    out->ports = ports;
    out->table = *baseline;
    if (!selection) {
        out->lan_members_external = baseline->entries[lan_entry].members & all_external;
        out->reserved_external = ports.lan_external & ~out->lan_members_external;
        return WR_WAN_VLAN_OK;
    }
    for (i = 0; i < baseline->count; i++) {
        const struct wr_wan_vlan_entry *before = &baseline->entries[i];
        struct wr_wan_vlan_entry *after = &out->table.entries[i];
        uint32_t removed = old_wan | selected;
        if (!before->valid) continue;
        after->members = (before->members & ~removed) | ((before->members & old_wan) ? selected : 0);
        after->untag = (before->untag & ~removed) | ((before->untag & old_wan) ? selected : 0);
        after->swap = (before->swap & ~removed) | ((before->swap & old_wan) ? selected : 0);
    }
    out->table.pvid[ports.wan_phy] = baseline->pvid[board->original_wan];
    out->lan_members_external = out->table.entries[lan_entry].members & all_external;
    out->reserved_external = ports.lan_external & ~out->lan_members_external;
    return WR_WAN_VLAN_OK;
}
#endif
