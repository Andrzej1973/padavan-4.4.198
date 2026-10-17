#ifndef WR_VPN_PROFILE_APPLY_H
#define WR_VPN_PROFILE_APPLY_H
#include "addr-apply.h"
#include "config-transaction.h"
#include "route-apply.h"

struct wr_vpn_apply_options {
    /* Router management and LAN prefixes; addresses are refused without them. */
    const char *const *protected_prefixes;
    size_t protected_count;
};

struct wr_vpn_apply_outcome {
    enum wr_vpn_transaction_result protocol;
    enum wr_vpn_addr_result addresses;
    enum wr_vpn_route_result routes;
    int addresses_attempted;
    int routes_attempted;
};

/* One apply, in order: protocol configuration, addresses, routes.
 *
 * The protocol step carries its own lock, session check and readback; the
 * address and route steps run only after it lands. The first failing stage stops
 * the sequence, and the outcome records exactly which stages were attempted, so
 * a partial apply is reported as partial instead of success.
 *
 * A profile that carries addresses is refused when the caller supplies no
 * protected prefixes: without them the router's own management network could be
 * pulled into the tunnel.
 */
int wr_vpn_profile_apply(const char *runtime_root, const struct wr_vpn_record *record,
    const struct wr_vpn_session *expected, const struct wr_vpn_apply_options *options,
    const struct wr_vpn_exec *exec, struct wr_vpn_apply_outcome *outcome);

#endif
