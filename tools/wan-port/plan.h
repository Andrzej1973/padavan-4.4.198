#ifndef WR_WAN_PORT_PLAN_H
#define WR_WAN_PORT_PLAN_H
#include <stdint.h>
#include <string.h>
/* External switch ports only. CPU membership, VLAN IDs/PVIDs, link monitoring
 * and hardware NAT are deliberately NOT inferred by this pure planner. */
struct wr_wan_port_board {
    unsigned original_wan;
    unsigned lan[4];
};
struct wr_wan_port_plan {
    unsigned selection, wan_phy;
    uint32_t wan_external, lan_external, isolated_external;
};
/* Selection 0 restores the original WAN; 1..4 select the labelled LAN socket.
 * Board mapping must come from the actual effective board config, not a
 * product-name guess. This function performs no ioctl or NVRAM operation. */
static inline int wr_wan_port_plan(const struct wr_wan_port_board *board,
                                  unsigned selection, struct wr_wan_port_plan *out)
{
    uint32_t all = 0, lans = 0;
    unsigned ports[5], i;
    if (!out) return 0;
    memset(out, 0, sizeof(*out));
    if (!board || selection > 4) return 0;
    ports[0] = board->original_wan;
    for (i = 0; i < 4; i++) ports[i+1] = board->lan[i];
    for (i = 0; i < 5; i++) {
        uint32_t bit;
        if (ports[i] >= 32) return 0;
        bit = UINT32_C(1) << ports[i];
        if (all & bit) return 0;
        all |= bit;
        if (i) lans |= bit;
    }
    out->selection = selection;
    out->wan_phy = ports[selection];
    out->wan_external = UINT32_C(1) << out->wan_phy;
    out->lan_external = lans & ~out->wan_external;
    out->isolated_external = selection ? UINT32_C(1) << ports[0] : 0;
    return !(out->wan_external & out->lan_external) &&
        !(out->isolated_external & (out->wan_external | out->lan_external)) &&
        (out->wan_external | out->lan_external | out->isolated_external) == all;
}
#endif
