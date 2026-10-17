#ifndef WR_VPN_ENDPOINT_PIN_H
#define WR_VPN_ENDPOINT_PIN_H
#include "store.h"

/* Resolve one hostname to a numeric address in text form (IPv4, or IPv6
 * without brackets). Returns non-zero on success. Injected so callers decide
 * when DNS is allowed and tests never touch the network.
 */
typedef int (*wr_vpn_resolver)(const char *host, char *numeric, size_t capacity);

enum wr_vpn_pin_result {
    WR_VPN_PIN_DONE,       /* every hostname endpoint was replaced */
    WR_VPN_PIN_UNCHANGED,  /* endpoints were already numeric */
    WR_VPN_PIN_REJECTED,   /* malformed endpoint line */
    WR_VPN_PIN_UNRESOLVED, /* resolver failed; nothing may be applied */
    WR_VPN_PIN_TOO_LONG    /* pinned configuration would not fit */
};

/* Copies the record and replaces each hostname endpoint with a numeric address,
 * so the native tool never resolves a name during the mutation. Only Endpoint
 * lines change; everything else is copied byte for byte. The caller resolves
 * outside the tunnel and applies the result separately.
 *
 * On any result other than DONE/UNCHANGED the output contents are unspecified
 * and must not be applied.
 */
enum wr_vpn_pin_result wr_vpn_pin_endpoints(const struct wr_vpn_record *input,
    wr_vpn_resolver resolve, struct wr_vpn_record *output);

#endif
