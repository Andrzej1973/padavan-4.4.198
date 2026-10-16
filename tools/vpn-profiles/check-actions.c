#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <limits.h>
#include "link-actions.h"
static struct wr_vpn_session session;
static unsigned int calls,sends;
static int mode;
static int fixture_socket(int domain,int type,int protocol)
{
    assert(domain==AF_NETLINK && type==(SOCK_RAW|SOCK_CLOEXEC) && protocol==NETLINK_ROUTE);
    sends++;errno=EIO;return -1; /* lost/unknown transport, never mutate host */
}
static enum wr_vpn_link_result fixture_query(const char *name,struct wr_vpn_link *out)
{
    struct wr_vpn_resources r;char owner[64];
    assert(wr_vpn_resources_make(&r,session.id,session.protocol));assert(!strcmp(name,r.interface));
    calls++;memset(out,0,sizeof(*out));
    if (mode==0 || (mode==1 && calls==1) || (mode==4 && calls==2)) return WR_VPN_LINK_ABSENT;
    if (mode==2) return WR_VPN_LINK_UNKNOWN;
    assert(wr_vpn_session_owner(&session,owner,sizeof(owner)));
    strcpy(out->name,name);strcpy(out->owner,mode==3?"foreign":owner);
    strcpy(out->kind,session.protocol==WR_VPN_WIREGUARD?"wireguard":"amneziawg");out->index=41;
    return WR_VPN_LINK_PRESENT;
}
#define socket fixture_socket
#define wr_vpn_link_query fixture_query
#include "link-actions.c"
#undef socket
#undef wr_vpn_link_query
static void packet_checks(enum wr_vpn_protocol protocol)
{
    unsigned char buffer[512],before[512];struct nlmsghdr h;struct ifinfomsg info;
    struct rtattr a;size_t size,at;int name=0,owner=0,kind=0;
    assert(wr_vpn_session_new(&session,2,protocol,1));
    memset(buffer,0xa5,sizeof(buffer));memcpy(before,buffer,sizeof(buffer));
    assert(!wr_vpn_link_request(&session,0,7,buffer,1) && !memcmp(before,buffer,sizeof(buffer)));
    size=wr_vpn_link_request(&session,0,7,buffer,sizeof(buffer));assert(size);
    memcpy(&h,buffer,sizeof(h));memcpy(&info,buffer+NLMSG_HDRLEN,sizeof(info));
    assert(h.nlmsg_len==size && h.nlmsg_type==RTM_NEWLINK && h.nlmsg_seq==7);
    assert(h.nlmsg_flags==(NLM_F_REQUEST|NLM_F_ACK|NLM_F_CREATE|NLM_F_EXCL));
    assert(info.ifi_index==0 && !info.ifi_change && !info.ifi_flags);
    at=NLMSG_LENGTH(sizeof(info));
    while (at<size) {
        memcpy(&a,buffer+at,sizeof(a));assert(a.rta_len>=RTA_LENGTH(0) && at+RTA_ALIGN(a.rta_len)<=size);
        if (a.rta_type==IFLA_IFNAME) { assert(!strcmp((char *)buffer+at+RTA_LENGTH(0),"wrvpn2"));name++; }
        else if (a.rta_type==IFLA_IFALIAS) { assert(!strncmp((char *)buffer+at+RTA_LENGTH(0),"wrvpn:2:",8));owner++; }
        else if (a.rta_type==IFLA_LINKINFO) {
            struct rtattr nested;const char *value;
            memcpy(&nested,buffer+at+RTA_LENGTH(0),sizeof(nested));assert(nested.rta_type==IFLA_INFO_KIND);
            value=(char *)buffer+at+2*RTA_LENGTH(0);
            assert(!strcmp(value,protocol==WR_VPN_WIREGUARD?"wireguard":"amneziawg"));kind++;
        } else assert(0);
        at+=RTA_ALIGN(a.rta_len);
    }
    assert(name==1 && owner==1 && kind==1);
    assert(!wr_vpn_link_request(&session,1,7,buffer,sizeof(buffer)));
    session.index=41;assert(!wr_vpn_link_request(&session,0,7,buffer,sizeof(buffer)));
    size=wr_vpn_link_request(&session,1,7,buffer,sizeof(buffer));assert(size==NLMSG_LENGTH(sizeof(info)));
    memcpy(&h,buffer,sizeof(h));memcpy(&info,buffer+NLMSG_HDRLEN,sizeof(info));
    assert(h.nlmsg_type==RTM_DELLINK && h.nlmsg_flags==(NLM_F_REQUEST|NLM_F_ACK) && info.ifi_index==41);
}
int main(void)
{
    struct wr_vpn_link out;
    packet_checks(WR_VPN_WIREGUARD);packet_checks(WR_VPN_AMNEZIAWG);
    session.index=0;calls=sends=0;mode=1;
    assert(wr_vpn_link_create(&session,&out)==WR_VPN_ACTION_OK && out.index==41 && sends==1);
    calls=sends=0;mode=3;assert(wr_vpn_link_create(&session,&out)==WR_VPN_ACTION_REFUSED && !sends);
    calls=sends=0;mode=2;assert(wr_vpn_link_create(&session,&out)==WR_VPN_ACTION_UNKNOWN && !sends);
    calls=sends=0;mode=0;assert(wr_vpn_link_create(&session,&out)==WR_VPN_ACTION_UNKNOWN && sends==1);
    session.index=41;calls=sends=0;mode=3;
    assert(wr_vpn_link_remove(&session)==WR_VPN_ACTION_REFUSED && !sends);
    calls=sends=0;mode=4;assert(wr_vpn_link_remove(&session)==WR_VPN_ACTION_OK && sends==1);
    calls=sends=0;mode=0;assert(wr_vpn_link_remove(&session)==WR_VPN_ACTION_OK && !sends);
    session.index=42;calls=sends=0;mode=5;assert(wr_vpn_link_remove(&session)==WR_VPN_ACTION_REFUSED && !sends);
    puts("PASS VPN link action adapter: exclusive create with owner/kind/name, delete by recorded index, foreign/unknown refusal and lost-ACK postchecks; mock transport, no host network changes");
    return 0;
}
