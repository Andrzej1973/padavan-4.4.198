#ifndef WR_VPN_LINK_OBSERVATION_H
#define WR_VPN_LINK_OBSERVATION_H
#include "resources.h"
#include <linux/netlink.h>
#include <linux/rtnetlink.h>
#include <linux/if_link.h>
#include <sys/socket.h>

enum wr_vpn_link_result { WR_VPN_LINK_UNKNOWN, WR_VPN_LINK_ABSENT, WR_VPN_LINK_PRESENT };
struct wr_vpn_link {
    uint32_t index,flags,mtu,master;
    char name[16],kind[16],owner[128];
};
enum wr_vpn_link_result wr_vpn_link_decode(const void *data,size_t size,
    const struct sockaddr_nl *sender,socklen_t sender_size,int message_flags,
    uint32_t sequence,const char *name,struct wr_vpn_link *out);
/* Read-only one-request socket. Timeout/errors mean UNKNOWN, never ABSENT. */
enum wr_vpn_link_result wr_vpn_link_query(const char *name,struct wr_vpn_link *out);
/* Matching kind alone does not grant ownership. Caller also holds lifecycle
 * lock and verifies the current recorded session/index before any mutation.
 */
int wr_vpn_link_owned(const struct wr_vpn_resources *resources,
                     const struct wr_vpn_link *link,uint32_t index,const char *owner);
#endif
