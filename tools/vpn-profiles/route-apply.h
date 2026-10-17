#ifndef WR_VPN_ROUTE_APPLY_H
#define WR_VPN_ROUTE_APPLY_H
#include "addr-apply.h"

enum wr_vpn_route_result {
    WR_VPN_ROUTE_DONE,     /* routes and the marked rule are in place */
    WR_VPN_ROUTE_EMPTY,    /* the profile carries no AllowedIPs */
    WR_VPN_ROUTE_INVALID,  /* malformed prefix; nothing was executed */
    WR_VPN_ROUTE_FAILED    /* the runner refused a command */
};

/* Adds or removes the profile's routes and its policy rule.
 *
 * Routes go only to the profile table (never the main table):
 *   ip route replace|del <prefix> dev <interface> table <table>
 * Redirecting is done only for packets the daemon marks:
 *   ip rule add|del fwmark <mark>/0xffffffff lookup <table> priority <priority_tunnel>
 *
 * On removal the rule goes first, so traffic stops being redirected before the
 * table is emptied. On removal the runner should treat "no such route/rule" as
 * success; the controller reconciles observed state. Adding never creates a
 * `from all` rule, so the router's own traffic keeps using the main table.
 */
enum wr_vpn_route_result wr_vpn_routes_apply(const struct wr_vpn_resources *resources,
    const char *allowed_ips, int add, const struct wr_vpn_exec *exec);

#endif
