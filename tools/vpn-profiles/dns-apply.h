#ifndef WR_VPN_DNS_APPLY_H
#define WR_VPN_DNS_APPLY_H
#include "config-plan.h"

enum wr_vpn_dns_result {
    WR_VPN_DNS_DONE,     /* the profile DNS list was written */
    WR_VPN_DNS_EMPTY,    /* the profile carries no DNS lines */
    WR_VPN_DNS_INVALID,  /* malformed address; nothing was written */
    WR_VPN_DNS_IO        /* the file could not be written */
};

/* Writes the profile's DNS servers to `<directory>/<resources.dns>`, one
 * address per line, atomically (temp file + rename, mode 0600). The controller
 * hands that file to dnsmasq only when the profile's DNS preference is enabled;
 * resolv.conf keeps 127.0.0.1 first, so losing the tunnel cannot leave the
 * router without a resolver.
 */
enum wr_vpn_dns_result wr_vpn_dns_write(const struct wr_vpn_config_plan *plan,
    const char *directory);

#endif
