#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "link-observation.h"
#include <errno.h>
#include <limits.h>
#include <linux/if_link.h>
#include <sys/time.h>
#include <unistd.h>

static int wr_link_name(const char *name)
{
    size_t n;
    if (!name || !(n=strnlen(name,16)) || n>=16 || !strcmp(name,".") || !strcmp(name,"..")) return 0;
    return strspn(name,"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")==n;
}
static int wr_link_string(const unsigned char *data,size_t size,char *out,size_t capacity)
{
    if (!size || size>capacity || data[size-1] || memchr(data,0,size-1)) return 0;
    memcpy(out,data,size); return 1;
}
static int wr_link_attrs(const unsigned char *data,size_t size,int nested,struct wr_vpn_link *out)
{
    unsigned int seen=0,count=0;
    while (size) {
        struct rtattr header; size_t length,aligned,payload; unsigned int type,bit=0;
        const unsigned char *value;
        if (++count>128 || size<sizeof(header)) return 0;
        memcpy(&header,data,sizeof(header));length=header.rta_len;
        if (length<RTA_LENGTH(0) || length>size || (aligned=RTA_ALIGN(length))>size) return 0;
        type=header.rta_type&0x3fff;payload=length-RTA_LENGTH(0);value=data+RTA_LENGTH(0);
        if (nested) { if (type==IFLA_INFO_KIND) bit=1; }
        else {
            if (type==IFLA_IFNAME) bit=1;
            else if (type==IFLA_IFALIAS) bit=2;
            else if (type==IFLA_LINKINFO) bit=4;
            else if (type==IFLA_MTU) bit=8;
            else if (type==IFLA_MASTER) bit=16;
        }
        if (bit && (seen&bit)) return 0;
        seen|=bit;
        if (nested && bit) {
            if (!wr_link_string(value,payload,out->kind,sizeof(out->kind))) return 0;
        } else if (!nested && bit) {
            if (type==IFLA_IFNAME) { if (!wr_link_string(value,payload,out->name,sizeof(out->name))) return 0; }
            else if (type==IFLA_IFALIAS) { if (!wr_link_string(value,payload,out->owner,sizeof(out->owner))) return 0; }
            else if (type==IFLA_LINKINFO) { if (!wr_link_attrs(value,payload,1,out)) return 0; }
            else {
                if (payload!=sizeof(uint32_t)) return 0;
                if (type==IFLA_MTU) memcpy(&out->mtu,value,payload);
                else memcpy(&out->master,value,payload);
            }
        }
        data+=aligned;size-=aligned;
    }
    return nested || (seen&1);
}
enum wr_vpn_link_result wr_vpn_link_decode(const void *data,size_t size,
    const struct sockaddr_nl *sender,socklen_t sender_size,int message_flags,
    uint32_t sequence,const char *name,struct wr_vpn_link *out)
{
    struct nlmsghdr header;struct ifinfomsg info;struct wr_vpn_link link;
    const unsigned char *bytes=data;size_t offset=NLMSG_LENGTH(sizeof(info));
    if (!out) return WR_VPN_LINK_UNKNOWN;
    memset(out,0,sizeof(*out));memset(&link,0,sizeof(link));
    if (!data || !sender || sender_size!=sizeof(*sender) || sender->nl_family!=AF_NETLINK ||
        sender->nl_pid || sender->nl_groups || (message_flags&(MSG_TRUNC|MSG_CTRUNC)) ||
        !wr_link_name(name) || size<sizeof(header) || size>4096) return WR_VPN_LINK_UNKNOWN;
    memcpy(&header,data,sizeof(header));
    if (header.nlmsg_seq!=sequence || header.nlmsg_len!=size || (header.nlmsg_flags&NLM_F_MULTI)) return WR_VPN_LINK_UNKNOWN;
    if (header.nlmsg_type==NLMSG_ERROR) {
        struct nlmsgerr error;
        if (size<NLMSG_LENGTH(sizeof(error))) return WR_VPN_LINK_UNKNOWN;
        memcpy(&error,bytes+NLMSG_HDRLEN,sizeof(error));
        if (error.msg.nlmsg_type!=RTM_GETLINK || error.msg.nlmsg_seq!=sequence ||
            !(error.msg.nlmsg_flags&NLM_F_REQUEST)) return WR_VPN_LINK_UNKNOWN;
        return error.error==-ENODEV || error.error==-ENOENT?WR_VPN_LINK_ABSENT:WR_VPN_LINK_UNKNOWN;
    }
    if (header.nlmsg_type!=RTM_NEWLINK || size<offset) return WR_VPN_LINK_UNKNOWN;
    memcpy(&info,bytes+NLMSG_HDRLEN,sizeof(info));
    if (info.ifi_index<=0 || !wr_link_attrs(bytes+offset,size-offset,0,&link) || strcmp(link.name,name)) return WR_VPN_LINK_UNKNOWN;
    link.index=(uint32_t)info.ifi_index;link.flags=info.ifi_flags;*out=link;
    return WR_VPN_LINK_PRESENT;
}
enum wr_vpn_link_result wr_vpn_link_query(const char *name,struct wr_vpn_link *out)
{
    unsigned char request[128],reply[4096];struct nlmsghdr header;struct ifinfomsg info;
    struct rtattr attr;struct sockaddr_nl local,kernel,sender;
    struct timeval timeout={1,0};struct msghdr message;struct iovec io;
    enum wr_vpn_link_result result=WR_VPN_LINK_UNKNOWN;
    const uint32_t sequence=UINT32_C(0x5756504c);
    size_t size,length;int fd;ssize_t received;
    if (!out) return result;
    memset(out,0,sizeof(*out));if (!wr_link_name(name)) return result;
    length=strlen(name);memset(request,0,sizeof(request));memset(&header,0,sizeof(header));memset(&info,0,sizeof(info));
    size=NLMSG_LENGTH(sizeof(info));attr.rta_type=IFLA_IFNAME;attr.rta_len=(unsigned short)RTA_LENGTH(length+1);
    memcpy(request+size,&attr,sizeof(attr));memcpy(request+size+RTA_LENGTH(0),name,length+1);
    size+=RTA_ALIGN(attr.rta_len);header.nlmsg_len=(uint32_t)size;header.nlmsg_type=RTM_GETLINK;
    header.nlmsg_flags=NLM_F_REQUEST;header.nlmsg_seq=sequence;info.ifi_family=AF_UNSPEC;
    memcpy(request,&header,sizeof(header));memcpy(request+NLMSG_HDRLEN,&info,sizeof(info));
    fd=socket(AF_NETLINK,SOCK_RAW|SOCK_CLOEXEC,NETLINK_ROUTE);if (fd<0) return result;
    memset(&local,0,sizeof(local));local.nl_family=AF_NETLINK;
    memset(&kernel,0,sizeof(kernel));kernel.nl_family=AF_NETLINK;
    if (setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout)) ||
        setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout)) ||
        bind(fd,(struct sockaddr *)&local,sizeof(local)) ||
        sendto(fd,request,size,0,(struct sockaddr *)&kernel,sizeof(kernel))!=(ssize_t)size) goto done;
    memset(&message,0,sizeof(message));memset(&sender,0,sizeof(sender));
    io.iov_base=reply;io.iov_len=sizeof(reply);message.msg_name=&sender;message.msg_namelen=sizeof(sender);
    message.msg_iov=&io;message.msg_iovlen=1;
    received=recvmsg(fd,&message,0);
    if (received>0) result=wr_vpn_link_decode(reply,(size_t)received,&sender,message.msg_namelen,message.msg_flags,sequence,name,out);
done:
    close(fd);return result;
}
int wr_vpn_link_owned(const struct wr_vpn_resources *r,const struct wr_vpn_link *link,
                     uint32_t index,const char *owner)
{
    const char *kind;
    struct wr_vpn_resources canonical;
    if (!r || !link || !owner || !index || index>INT_MAX || !*owner ||
        strnlen(owner,sizeof(link->owner))>=sizeof(link->owner) ||
        strnlen(r->interface,sizeof(r->interface))>=sizeof(r->interface) ||
        strnlen(link->name,sizeof(link->name))>=sizeof(link->name) ||
        strnlen(link->kind,sizeof(link->kind))>=sizeof(link->kind) ||
        strnlen(link->owner,sizeof(link->owner))>=sizeof(link->owner)) return 0;
    if (!wr_vpn_resources_make(&canonical,r->id,r->protocol) || strcmp(canonical.interface,r->interface)) return 0;
    if (r->protocol==WR_VPN_WIREGUARD) kind="wireguard";
    else if (r->protocol==WR_VPN_AMNEZIAWG) kind="amneziawg";
    else return 0;
    return link->index==index && !link->master && !strcmp(link->name,r->interface) &&
        !strcmp(link->kind,kind) && !strcmp(link->owner,owner);
}
