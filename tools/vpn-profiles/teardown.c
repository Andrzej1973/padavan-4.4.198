#include "teardown.h"
#include <string.h>

enum wr_vpn_teardown_result wr_vpn_profile_cleanup(
    const struct wr_vpn_config_plan *plan,
    const struct wr_vpn_resources *resources,
    const char *runtime_root,
    int configuration_valid,
    const struct wr_vpn_exec *exec,
    struct wr_vpn_teardown_report *report)
{
    if (!resources || !runtime_root || !exec || !exec->run || !report ||
        (configuration_valid && !plan)) return WR_VPN_TEARDOWN_INVALID;
    report->routes=WR_VPN_ROUTE_EMPTY;
    report->addresses=WR_VPN_ADDR_EMPTY;
    report->dns=WR_VPN_DNS_EMPTY;

    if (configuration_valid && plan->allowed[0])
        report->routes=wr_vpn_routes_apply(&plan->resources,plan->allowed,0,exec);
    else
        report->routes=wr_vpn_rule_remove(resources,exec);

    /* Retain the address and link context while any policy rule or route can
     * still direct traffic into the tunnel. A later down() retries cleanup. */
    if (report->routes!=WR_VPN_ROUTE_DONE && report->routes!=WR_VPN_ROUTE_EMPTY)
        return WR_VPN_TEARDOWN_PARTIAL;

    if (!configuration_valid) {
        struct wr_vpn_config_plan cleanup_plan;
        memset(&cleanup_plan,0,sizeof(cleanup_plan));
        cleanup_plan.resources=*resources;
        report->dns=wr_vpn_dns_remove(&cleanup_plan,runtime_root);
        if (report->dns!=WR_VPN_DNS_DONE && report->dns!=WR_VPN_DNS_EMPTY)
            return WR_VPN_TEARDOWN_PARTIAL;
        return WR_VPN_TEARDOWN_UNKNOWN;
    }

    if (plan->addresses[0])
        report->addresses=wr_vpn_addresses_apply(plan,0,NULL,0,exec);
    if (report->addresses!=WR_VPN_ADDR_DONE && report->addresses!=WR_VPN_ADDR_EMPTY)
        return WR_VPN_TEARDOWN_PARTIAL;

    /* Also remove a stale per-profile resolver file when the edited profile
     * no longer contains DNS entries. */
    report->dns=wr_vpn_dns_remove(plan,runtime_root);
    if (report->dns!=WR_VPN_DNS_DONE && report->dns!=WR_VPN_DNS_EMPTY)
        return WR_VPN_TEARDOWN_PARTIAL;
    return WR_VPN_TEARDOWN_DONE;
}
