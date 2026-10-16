#ifndef WR_VPN_CONFIG_APPLY_H
#define WR_VPN_CONFIG_APPLY_H
#include "config-plan.h"
/* Low-level transport, not a start controller. Caller must hold the runtime
 * lock, verify session/index/owner immediately before calling, pin endpoints
 * outside the tunnel, and reconcile ownership/configuration afterwards.
 * ACKNOWLEDGED means only setconf exited zero, never connectivity or readback.
 * UNKNOWN may include partial kernel changes; do not blindly retry or delete.
 * Not packaged/exposed until transaction, rollback and readback are integrated.
 */
enum wr_vpn_apply_result { WR_VPN_APPLY_REFUSED, WR_VPN_APPLY_NOT_STARTED,
    WR_VPN_APPLY_UNKNOWN, WR_VPN_APPLY_ACKNOWLEDGED };
enum wr_vpn_apply_result wr_vpn_config_apply(const struct wr_vpn_record *);
#endif
