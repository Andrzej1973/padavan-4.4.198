#ifndef WR_VPN_ROUTE_APPLY_H
#define WR_VPN_ROUTE_APPLY_H
#include "addr-apply.h"

enum wr_vpn_route_result {
    WR_VPN_ROUTE_DONE,     /* routes and the marked rule are in place */
    WR_VPN_ROUTE_EMPTY,    /* the profile carries no AllowedIPs */
    WR_VPN_ROUTE_INVALID,  /* malformed prefix; nothing was executed */
    WR_VPN_ROUTE_FAILED,   /* operation failed and rollback completed */
    WR_VPN_ROUTE_PARTIAL   /* cleanup failed; owned state may remain */
};

/* Adds or removes the profile's routes and its policy rule.
 *
 * Routes go only to the profile table (never the main table):
 *   ip route replace|del <IPv4-prefix> dev <interface> table <table>
 *   ip -6 route replace|del <IPv6-prefix> dev <interface> table <table>
 * Redirecting is done only for packets the daemon marks:
 *   ip rule add|del fwmark <mark>/0xffffffff lookup <table> priority <priority_tunnel>
 *   ip -6 rule add|del fwmark <mark>/0xffffffff lookup <table> priority <priority_tunnel>
 *
 * On removal, each family's rule goes first. Its routes are kept if that
 * family's rule cannot be removed, preserving context for a later retry.
 * Missing routes and rules are idempotent cleanup successes. Adding never
 * creates a `from all` rule, so router-originated traffic keeps using main.
 */
enum wr_vpn_route_result wr_vpn_routes_apply(const struct wr_vpn_resources *resources,
    const char *allowed_ips, int add, const struct wr_vpn_exec *exec);

/* Removes only the profile's IPv4 and IPv6 marked rules. Teardown uses this when the stored
 * configuration cannot be parsed any more: the rule is derived from the
 * resource identity, so it can be dropped without a plan. The controller's
 * runner should treat "no such rule" as success.
 */
enum wr_vpn_route_result wr_vpn_rule_remove(const struct wr_vpn_resources *resources,
    const struct wr_vpn_exec *exec);

#endif
