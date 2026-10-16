#ifndef WR_VPN_CONFIG_PLAN_H
#define WR_VPN_CONFIG_PLAN_H
#include "validate-process.h"
/* Contains private keys. Do not log/serve this structure. Native config is for
 * setconf only: Address/DNS/MTU and route policy are separate controller work.
 * Hostname endpoints require explicit resolution and outside-tunnel pinning
 * before applying. This module performs no DNS, IPC or network mutations.
 */
struct wr_vpn_config_plan {
    struct wr_vpn_resources resources;
    char native[2*WR_VPN_CONFIG_MAX+128];
    char addresses[WR_VPN_CONFIG_MAX+1],dns[WR_VPN_CONFIG_MAX+1];
    unsigned int mtu; /* zero = controller chooses default */
    int hostname_endpoints;
};
enum wr_vpn_validation wr_vpn_prepare_config(const struct wr_vpn_record *,struct wr_vpn_config_plan *);
#endif
