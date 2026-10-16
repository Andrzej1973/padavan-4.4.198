#ifndef WR_VPN_LINK_ACTIONS_H
#define WR_VPN_LINK_ACTIONS_H
#include "runtime-state.h"
#include "link-observation.h"
/* Low-level adapter only. Caller holds the global operation lock, has saved
 * pre-create intent, and records the returned index before configuration.
 * No routes, addresses, DNS, flags or legacy links are changed here.
 */
enum wr_vpn_action_result { WR_VPN_ACTION_UNKNOWN, WR_VPN_ACTION_REFUSED, WR_VPN_ACTION_OK };
size_t wr_vpn_link_request(const struct wr_vpn_session *,int remove,uint32_t sequence,void *,size_t);
enum wr_vpn_action_result wr_vpn_link_create(const struct wr_vpn_session *,struct wr_vpn_link *);
enum wr_vpn_action_result wr_vpn_link_remove(const struct wr_vpn_session *);
#endif
