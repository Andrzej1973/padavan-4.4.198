#ifndef WR_VPN_ADDR_APPLY_H
#define WR_VPN_ADDR_APPLY_H
#include "config-plan.h"

/* The controller supplies the real runner, tests record argv. */
enum wr_vpn_exec_result {
    WR_VPN_EXEC_DONE,
    WR_VPN_EXEC_FAILED,
    WR_VPN_EXEC_UNKNOWN,
    WR_VPN_EXEC_PRESENT /* exact rule already existed before add */
};

struct wr_vpn_exec {
    /* DONE: command completed. FAILED: command was rejected before mutation.
     * UNKNOWN: runner lost certainty after dispatch (timeout/transport loss). */
    enum wr_vpn_exec_result (*run)(void *context, const char *const argv[]);
    void *context;
};

enum wr_vpn_addr_result {
    WR_VPN_ADDR_DONE,      /* every address was applied */
    WR_VPN_ADDR_EMPTY,     /* the profile carries no Address lines */
    WR_VPN_ADDR_INVALID,   /* malformed address; nothing was executed */
    WR_VPN_ADDR_CONFLICT,  /* overlaps a protected prefix; nothing was executed */
    WR_VPN_ADDR_FAILED     /* the runner refused a command */
};

/* Adds (add!=0) or removes the profile's addresses on its own interface with
 * `ip address replace|del <cidr> dev <interface>`.
 *
 * Before executing anything, every IPv4 address is checked against the
 * protected prefixes - the router's management and LAN networks. An overlap
 * refuses the whole operation, because a connected route for such a prefix can
 * move the router's own traffic. IPv6 addresses are validated but not compared.
 */
enum wr_vpn_addr_result wr_vpn_addresses_apply(const struct wr_vpn_config_plan *plan,
    int add, const char *const *protected_prefixes, size_t protected_count,
    const struct wr_vpn_exec *exec);

#endif
