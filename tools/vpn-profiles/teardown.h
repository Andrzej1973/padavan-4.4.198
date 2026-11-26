#ifndef WR_VPN_TEARDOWN_H
#define WR_VPN_TEARDOWN_H
#include "addr-apply.h"
#include "dns-apply.h"
#include "route-apply.h"

enum wr_vpn_teardown_result {
    WR_VPN_TEARDOWN_DONE,
    WR_VPN_TEARDOWN_PARTIAL,
    WR_VPN_TEARDOWN_UNKNOWN,
    WR_VPN_TEARDOWN_INVALID
};

struct wr_vpn_teardown_report {
    enum wr_vpn_route_result routes;
    enum wr_vpn_addr_result addresses;
    enum wr_vpn_dns_result dns;
};

/* Clean policy before the caller releases the owned link/session. On any
 * uncertain cleanup the caller must retain that recovery context. */
enum wr_vpn_teardown_result wr_vpn_profile_cleanup(
    const struct wr_vpn_config_plan *plan,
    const struct wr_vpn_resources *resources,
    const char *runtime_root,
    int configuration_valid,
    const struct wr_vpn_exec *exec,
    struct wr_vpn_teardown_report *report);
#endif
