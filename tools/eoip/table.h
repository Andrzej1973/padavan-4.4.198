#ifndef WR_EOIP_TABLE_H
#define WR_EOIP_TABLE_H
#include "config.h"

/* Input profiles must already have passed wr_eoip_validate. Disabled profiles
 * do not reserve tunnel tuples. The managed controller always uses link=0 and
 * ARPHRD_ETHER, so the remaining kernel eoip_tunnel_find identity consists of
 * local, remote and tunnel id. Neither bridge nor MTU disambiguates a tuple.
 * This check describes requested state only, not observed kernel state. */
static inline int wr_eoip_table_valid(const struct wr_eoip_config *profiles,
                                      size_t count)
{
    size_t i, j;
    if ((!profiles && count) || count > WR_EOIP_SLOTS) return 0;
    for (i = 0; i < count; i++) {
        if (profiles[i].slot >= WR_EOIP_SLOTS || profiles[i].enabled > 1 ||
            profiles[i].autostart > 1) return 0;
        for (j = 0; j < i; j++) {
            if (profiles[i].slot == profiles[j].slot) return 0;
            if (profiles[i].enabled && profiles[j].enabled &&
                profiles[i].local.s_addr == profiles[j].local.s_addr &&
                profiles[i].remote.s_addr == profiles[j].remote.s_addr &&
                profiles[i].tunnel_id == profiles[j].tunnel_id) return 0;
        }
    }
    return 1;
}
#endif
