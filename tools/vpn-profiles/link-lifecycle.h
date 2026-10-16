#ifndef WR_VPN_LINK_LIFECYCLE_H
#define WR_VPN_LINK_LIFECYCLE_H
#include "link-actions.h"
struct wr_vpn_link_ops {
    enum wr_vpn_link_result (*query)(const char *,struct wr_vpn_link *);
    enum wr_vpn_action_result (*create)(const struct wr_vpn_session *,struct wr_vpn_link *);
    enum wr_vpn_action_result (*remove)(const struct wr_vpn_session *);
};
extern const struct wr_vpn_link_ops wr_vpn_system_links;
enum wr_vpn_lifecycle_result { WR_VPN_LIFECYCLE_UNKNOWN, WR_VPN_LIFECYCLE_REFUSED,
    WR_VPN_LIFECYCLE_BUSY, WR_VPN_LIFECYCLE_OK };
/* Link ownership only: OK never claims VPN configuration/connectivity.
 * Controller must retain this same lock across later configure/routes/DNS work.
 * Operations take an already held global runtime lock (no nested lock order).
 */
enum wr_vpn_lifecycle_result wr_vpn_link_acquire(struct wr_vpn_runtime *,unsigned int,
    enum wr_vpn_protocol,uint64_t,const struct wr_vpn_link_ops *,struct wr_vpn_session *);
/* Controller cleans scoped policy first. Record is cleared only after absence. */
enum wr_vpn_lifecycle_result wr_vpn_link_release(struct wr_vpn_runtime *,unsigned int,const struct wr_vpn_link_ops *);
#endif
