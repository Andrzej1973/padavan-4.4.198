#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "link-actions.h"
#include <sys/time.h>
#include <unistd.h>

static size_t append_attr(unsigned char *buffer,size_t at,unsigned int type,const void *data,size_t size)
{
    struct rtattr a;
    a.rta_type=(unsigned short)type;a.rta_len=(unsigned short)RTA_LENGTH(size);
    memcpy(buffer+at,&a,sizeof(a));memcpy(buffer+at+RTA_LENGTH(0),data,size);
    return at+RTA_ALIGN(a.rta_len);
}
size_t wr_vpn_link_request(const struct wr_vpn_session *s,int remove,uint32_t sequence,void *out,size_t capacity)
{
    unsigned char buffer[512],nested[64];struct nlmsghdr h;struct ifinfomsg info;
    struct wr_vpn_resources r;char owner[64];const char *kind;size_t size,n;
    if (!out || !sequence || !wr_vpn_session_owner(s,owner,sizeof(owner)) ||
        !wr_vpn_resources_make(&r,s->id,s->protocol) || (remove!=0 && remove!=1) ||
        (remove?!s->index:s->index!=0)) return 0;
    memset(buffer,0,sizeof(buffer));memset(nested,0,sizeof(nested));
    memset(&h,0,sizeof(h));memset(&info,0,sizeof(info));info.ifi_family=AF_UNSPEC;
    h.nlmsg_type=remove?RTM_DELLINK:RTM_NEWLINK;h.nlmsg_seq=sequence;
    h.nlmsg_flags=NLM_F_REQUEST|NLM_F_ACK;
    size=NLMSG_LENGTH(sizeof(info));
    if (remove) info.ifi_index=(int)s->index;
    else {
        h.nlmsg_flags|=NLM_F_CREATE|NLM_F_EXCL;
        size=append_attr(buffer,size,IFLA_IFNAME,r.interface,strlen(r.interface)+1);
        size=append_attr(buffer,size,IFLA_IFALIAS,owner,strlen(owner)+1);
        kind=s->protocol==WR_VPN_WIREGUARD?"wireguard":"amneziawg";
        n=append_attr(nested,0,IFLA_INFO_KIND,kind,strlen(kind)+1);
        size=append_attr(buffer,size,IFLA_LINKINFO,nested,n);
    }
    if (size>capacity) return 0;
    h.nlmsg_len=(uint32_t)size;memcpy(buffer,&h,sizeof(h));memcpy(buffer+NLMSG_HDRLEN,&info,sizeof(info));
    memcpy(out,buffer,size);return size;
}
/* An ACK timeout is unknown: the kernel may already have applied the request.
 * The lifecycle uses session-tagged postchecks to recover such operations.
 */
static int send_request(const void *request,size_t size)
{
    struct sockaddr_nl local,kernel,sender;struct timeval timeout={1,0};
    struct msghdr message;struct iovec io;unsigned char reply[4096];
    struct nlmsghdr sent,header;struct nlmsgerr ack;ssize_t got;int fd,ok=0;
    memcpy(&sent,request,sizeof(sent));
    fd=socket(AF_NETLINK,SOCK_RAW|SOCK_CLOEXEC,NETLINK_ROUTE);if (fd<0) return 0;
    memset(&local,0,sizeof(local));local.nl_family=AF_NETLINK;
    memset(&kernel,0,sizeof(kernel));kernel.nl_family=AF_NETLINK;
    if (setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout)) ||
        setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout)) ||
        bind(fd,(struct sockaddr *)&local,sizeof(local)) ||
        sendto(fd,request,size,0,(struct sockaddr *)&kernel,sizeof(kernel))!=(ssize_t)size) goto done;
    memset(&message,0,sizeof(message));memset(&sender,0,sizeof(sender));
    io.iov_base=reply;io.iov_len=sizeof(reply);message.msg_name=&sender;message.msg_namelen=sizeof(sender);
    message.msg_iov=&io;message.msg_iovlen=1;got=recvmsg(fd,&message,0);
    if (got<(ssize_t)NLMSG_LENGTH(sizeof(ack)) || message.msg_namelen!=sizeof(sender) ||
        sender.nl_family!=AF_NETLINK || sender.nl_pid || sender.nl_groups ||
        (message.msg_flags&(MSG_TRUNC|MSG_CTRUNC))) goto done;
    memcpy(&header,reply,sizeof(header));memcpy(&ack,reply+NLMSG_HDRLEN,sizeof(ack));
    ok=header.nlmsg_len==(size_t)got && header.nlmsg_type==NLMSG_ERROR &&
        !(header.nlmsg_flags&NLM_F_MULTI) && header.nlmsg_seq==sent.nlmsg_seq &&
        ack.msg.nlmsg_type==sent.nlmsg_type && ack.msg.nlmsg_seq==sent.nlmsg_seq &&
        ack.msg.nlmsg_flags==sent.nlmsg_flags && ack.msg.nlmsg_len==sent.nlmsg_len && !ack.error;
done:
    close(fd);return ok;
}
enum wr_vpn_action_result wr_vpn_link_create(const struct wr_vpn_session *s,struct wr_vpn_link *out)
{
    unsigned char request[512];struct wr_vpn_resources r;struct wr_vpn_link link;
    enum wr_vpn_link_result status;size_t size;char owner[64];
    if (!out) return WR_VPN_ACTION_REFUSED;
    memset(out,0,sizeof(*out));
    size=wr_vpn_link_request(s,0,UINT32_C(0x57564352),request,sizeof(request));
    if (!size || !wr_vpn_resources_make(&r,s->id,s->protocol) || !wr_vpn_session_owner(s,owner,sizeof(owner))) return WR_VPN_ACTION_REFUSED;
    status=wr_vpn_link_query(r.interface,&link);
    if (status==WR_VPN_LINK_UNKNOWN) return WR_VPN_ACTION_UNKNOWN;
    if (status!=WR_VPN_LINK_ABSENT) return WR_VPN_ACTION_REFUSED;
    (void)send_request(request,size);
    status=wr_vpn_link_query(r.interface,&link);
    if (status==WR_VPN_LINK_PRESENT && wr_vpn_link_owned(&r,&link,link.index,owner)) {
        *out=link;return WR_VPN_ACTION_OK;
    }
    return WR_VPN_ACTION_UNKNOWN;
}
enum wr_vpn_action_result wr_vpn_link_remove(const struct wr_vpn_session *s)
{
    unsigned char request[512];struct wr_vpn_resources r;struct wr_vpn_link link;
    enum wr_vpn_link_result status;size_t size;char owner[64];
    size=wr_vpn_link_request(s,1,UINT32_C(0x57564445),request,sizeof(request));
    if (!size || !wr_vpn_resources_make(&r,s->id,s->protocol) || !wr_vpn_session_owner(s,owner,sizeof(owner))) return WR_VPN_ACTION_REFUSED;
    status=wr_vpn_link_query(r.interface,&link);
    if (status==WR_VPN_LINK_ABSENT) return WR_VPN_ACTION_OK;
    if (status==WR_VPN_LINK_UNKNOWN) return WR_VPN_ACTION_UNKNOWN;
    if (!wr_vpn_link_owned(&r,&link,s->index,owner)) return WR_VPN_ACTION_REFUSED;
    /* Index prevents deleting a same-name replacement with another ifindex.
     * A competing privileged controller can still race index reuse; the global
     * manager lock only coordinates this manager's own operations.
     */
    (void)send_request(request,size);
    return wr_vpn_link_query(r.interface,&link)==WR_VPN_LINK_ABSENT?WR_VPN_ACTION_OK:WR_VPN_ACTION_UNKNOWN;
}
