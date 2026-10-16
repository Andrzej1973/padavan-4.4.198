#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <net/if.h>
#include "link-observation.h"

static unsigned char packet[4096];
static const uint32_t sequence=77;
static struct sockaddr_nl sender;
static size_t attr(unsigned char *out,size_t at,unsigned int type,const void *data,size_t size)
{
    struct rtattr a; a.rta_type=(unsigned short)type;a.rta_len=(unsigned short)RTA_LENGTH(size);
    assert(at+RTA_ALIGN(a.rta_len)<=sizeof(packet));
    memcpy(out+at,&a,sizeof(a));memcpy(out+at+RTA_LENGTH(0),data,size);
    return at+RTA_ALIGN(a.rta_len);
}
static size_t link_packet(const char *name,const char *kind,const char *owner)
{
    struct nlmsghdr h;struct ifinfomsg info;unsigned char nested[128];
    uint32_t mtu=1420;size_t at=NLMSG_LENGTH(sizeof(info)),n=0;
    memset(packet,0,sizeof(packet));memset(&h,0,sizeof(h));memset(&info,0,sizeof(info));memset(nested,0,sizeof(nested));
    info.ifi_index=41;info.ifi_flags=IFF_UP;
    at=attr(packet,at,IFLA_IFNAME,name,strlen(name)+1);
    at=attr(packet,at,IFLA_IFALIAS,owner,strlen(owner)+1);
    at=attr(packet,at,IFLA_MTU,&mtu,sizeof(mtu));
    n=attr(nested,n,IFLA_INFO_KIND,kind,strlen(kind)+1);
    at=attr(packet,at,IFLA_LINKINFO,nested,n);
    h.nlmsg_len=(uint32_t)at;h.nlmsg_type=RTM_NEWLINK;h.nlmsg_seq=sequence;
    memcpy(packet,&h,sizeof(h));memcpy(packet+NLMSG_HDRLEN,&info,sizeof(info));return at;
}
static enum wr_vpn_link_result decode(size_t size,int flags,struct wr_vpn_link *out)
{ return wr_vpn_link_decode(packet,size,&sender,sizeof(sender),flags,sequence,"wrvpn2",out); }
int main(void)
{
    struct wr_vpn_link observed,zero;struct wr_vpn_resources resources;
    struct nlmsghdr header;struct nlmsgerr error;struct rtattr broken;
    size_t size,i;uint32_t master=5;
    memset(&zero,0,sizeof(zero));memset(&sender,0,sizeof(sender));sender.nl_family=AF_NETLINK;
    assert(wr_vpn_resources_make(&resources,2,WR_VPN_WIREGUARD));
    size=link_packet("wrvpn2","wireguard","wrvpn:2:session-a");
    assert(decode(size,0,&observed)==WR_VPN_LINK_PRESENT && observed.index==41 && observed.mtu==1420);
    assert(wr_vpn_link_owned(&resources,&observed,41,"wrvpn:2:session-a"));
    assert(!wr_vpn_link_owned(&resources,&observed,42,"wrvpn:2:session-a"));
    assert(!wr_vpn_link_owned(&resources,&observed,41,"wrvpn:2:session-b"));
    assert(!wr_vpn_link_owned(&resources,&observed,41,""));
    strcpy(resources.interface,"wg0");strcpy(observed.name,"wg0");
    assert(!wr_vpn_link_owned(&resources,&observed,41,"wrvpn:2:session-a"));
    assert(wr_vpn_resources_make(&resources,2,WR_VPN_WIREGUARD));
    for (i=0;i<size;i++) {
        memset(&observed,0xa5,sizeof(observed));
        assert(decode(i,0,&observed)==WR_VPN_LINK_UNKNOWN && !memcmp(&observed,&zero,sizeof(zero)));
    }
    assert(decode(size,MSG_TRUNC,&observed)==WR_VPN_LINK_UNKNOWN);
    sender.nl_pid=10;assert(decode(size,0,&observed)==WR_VPN_LINK_UNKNOWN);sender.nl_pid=0;
    memcpy(&header,packet,sizeof(header));header.nlmsg_seq++;memcpy(packet,&header,sizeof(header));
    assert(decode(size,0,&observed)==WR_VPN_LINK_UNKNOWN);
    size=link_packet("wrvpn3","wireguard","wrvpn:2:session-a");assert(decode(size,0,&observed)==WR_VPN_LINK_UNKNOWN);
    size=link_packet("wrvpn2","amneziawg","wrvpn:2:session-a");
    assert(decode(size,0,&observed)==WR_VPN_LINK_PRESENT && !wr_vpn_link_owned(&resources,&observed,41,"wrvpn:2:session-a"));
    size=link_packet("wrvpn2","wireguard","foreign");
    assert(decode(size,0,&observed)==WR_VPN_LINK_PRESENT && !wr_vpn_link_owned(&resources,&observed,41,"wrvpn:2:session-a"));
    size=link_packet("wrvpn2","wireguard","wrvpn:2:session-a");
    size=attr(packet,size,IFLA_MASTER,&master,sizeof(master));memcpy(&header,packet,sizeof(header));header.nlmsg_len=(uint32_t)size;memcpy(packet,&header,sizeof(header));
    assert(decode(size,0,&observed)==WR_VPN_LINK_PRESENT && !wr_vpn_link_owned(&resources,&observed,41,"wrvpn:2:session-a"));
    size=link_packet("wrvpn2","wireguard","wrvpn:2:session-a");
    size=attr(packet,size,IFLA_IFNAME,"wrvpn2",7);memcpy(&header,packet,sizeof(header));header.nlmsg_len=(uint32_t)size;memcpy(packet,&header,sizeof(header));
    assert(decode(size,0,&observed)==WR_VPN_LINK_UNKNOWN);
    size=link_packet("wrvpn2","wireguard","wrvpn:2:session-a");
    memcpy(&broken,packet+NLMSG_LENGTH(sizeof(struct ifinfomsg)),sizeof(broken));broken.rta_len=0;
    memcpy(packet+NLMSG_LENGTH(sizeof(struct ifinfomsg)),&broken,sizeof(broken));assert(decode(size,0,&observed)==WR_VPN_LINK_UNKNOWN);
    memset(packet,0,sizeof(packet));memset(&header,0,sizeof(header));memset(&error,0,sizeof(error));
    size=NLMSG_LENGTH(sizeof(error));header.nlmsg_len=(uint32_t)size;header.nlmsg_type=NLMSG_ERROR;header.nlmsg_seq=sequence;
    error.error=-ENODEV;error.msg.nlmsg_type=RTM_GETLINK;error.msg.nlmsg_seq=sequence;error.msg.nlmsg_flags=NLM_F_REQUEST;
    memcpy(packet,&header,sizeof(header));memcpy(packet+NLMSG_HDRLEN,&error,sizeof(error));assert(decode(size,0,&observed)==WR_VPN_LINK_ABSENT);
    error.error=-EPERM;memcpy(packet+NLMSG_HDRLEN,&error,sizeof(error));assert(decode(size,0,&observed)==WR_VPN_LINK_UNKNOWN);
    assert(wr_vpn_link_query("lo",&observed)==WR_VPN_LINK_PRESENT && observed.index==if_nametoindex("lo"));
    assert(wr_vpn_link_query("wrv_abs_8724",&observed)==WR_VPN_LINK_ABSENT);
    assert(wr_vpn_link_query("../unsafe",&observed)==WR_VPN_LINK_UNKNOWN);
    puts("PASS VPN link observation: bounded kernel replies, absent/unknown distinction, index/kind/session ownership and read-only host loopback query; no network mutations");
    return 0;
}
