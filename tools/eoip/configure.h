#ifndef WR_EOIP_CONFIGURE_H
#define WR_EOIP_CONFIGURE_H
/* Applies MTU, admin state and one explicit bridge master to an already
 * observed, owned EoIP interface.
 *
 * No mutation happens without a fresh ownership and interface-index
 * observation, and every mutation is verified by a second observation. The
 * bridge is never chosen implicitly and is only accepted when the kernel
 * reports it as a bridge; an interface with an existing master is refused
 * rather than detached. This configures one interface; it is not a service
 * controller and it establishes no tunnel reachability. */
#include "config.h"
#include "netlink-query.h"
#include <fcntl.h>
#include <net/if.h>
#include <stdint.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/uio.h>
#include <unistd.h>

#define WR_EOIP_CHANGE_LENGTH 256

static inline int wr_eoip_managed_name(const char *name)
{
 size_t length;

 if(!name)return 0;
 length=strlen(name);
 return length>0&&length<16&&
  strspn(name,"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-")==length;
}

/* One bounded RTM_NEWLINK change that addresses the interface by index only.
 * The name is deliberately not repeated: the caller verified the index. */
static inline int wr_eoip_build_change(unsigned char *request,size_t capacity,unsigned index,
 unsigned mtu,unsigned master,uint32_t sequence,size_t *length)
{
 struct nlmsghdr header;
 struct ifinfomsg info;
 struct rtattr attribute;
 size_t offset;
 uint32_t value;

 if(!request||!length||!index||mtu<68||mtu>WR_EOIP_MAX_MTU)return 0;
 offset=NLMSG_LENGTH(sizeof(info));
 if(offset+RTA_SPACE(sizeof(uint32_t))*2>capacity)return 0;
 memset(request,0,capacity);
 memset(&header,0,sizeof(header));
 memset(&info,0,sizeof(info));
 info.ifi_family=AF_UNSPEC;
 info.ifi_index=(int)index;
 info.ifi_flags=IFF_UP;
 info.ifi_change=IFF_UP;
 memcpy(request+NLMSG_HDRLEN,&info,sizeof(info));
 attribute.rta_type=IFLA_MTU;
 attribute.rta_len=RTA_LENGTH(sizeof(uint32_t));
 value=mtu;
 memcpy(request+offset,&attribute,sizeof(attribute));
 memcpy(request+offset+RTA_LENGTH(0),&value,sizeof(value));
 offset+=RTA_ALIGN(attribute.rta_len);
 if(master){
  attribute.rta_type=IFLA_MASTER;
  attribute.rta_len=RTA_LENGTH(sizeof(uint32_t));
  value=master;
  memcpy(request+offset,&attribute,sizeof(attribute));
  memcpy(request+offset+RTA_LENGTH(0),&value,sizeof(value));
  offset+=RTA_ALIGN(attribute.rta_len);
 }
 header.nlmsg_len=(unsigned)offset;
 header.nlmsg_type=RTM_NEWLINK;
 header.nlmsg_flags=NLM_F_REQUEST|NLM_F_ACK;
 header.nlmsg_seq=sequence;
 memcpy(request,&header,sizeof(header));
 *length=offset;
 return 1;
}

/* 1 only for a zero-error acknowledgement of this change from the kernel port.
 * A permission error, a different sequence or an echoed other request is not
 * an applied configuration. */
static inline int wr_eoip_change_reply(const void *buffer,size_t size,const struct sockaddr_nl *sender,
 socklen_t sender_length,int flags,uint32_t sequence)
{
 struct nlmsghdr header;
 struct nlmsgerr error;

 if(!buffer||!sender||sender_length!=sizeof(*sender)||sender->nl_family!=AF_NETLINK||
    sender->nl_pid!=0||sender->nl_groups!=0||(flags&(MSG_TRUNC|MSG_CTRUNC)))return 0;
 if(size<sizeof(header)||size>4096)return 0;
 memcpy(&header,buffer,sizeof(header));
 if(header.nlmsg_len!=size||header.nlmsg_seq!=sequence||header.nlmsg_type!=NLMSG_ERROR)return 0;
 if(size<NLMSG_LENGTH(sizeof(error)))return 0;
 memcpy(&error,(const unsigned char *)buffer+NLMSG_HDRLEN,sizeof(error));
 return !error.error&&error.msg.nlmsg_type==RTM_NEWLINK&&error.msg.nlmsg_seq==sequence;
}

/* Sends one acknowledged change. Returns 0 only when the kernel acknowledged
 * it; the descriptor is closed on every path. */
static inline int wr_eoip_socket_change(void *context,const void *request,size_t length,uint32_t sequence)
{
 unsigned char reply[4096];
 struct sockaddr_nl local,kernel,sender;
 struct timeval timeout;
 struct iovec vector;
 struct msghdr message;
 int descriptor,result=-1;
 ssize_t received;

 (void)context;
 if(!request||length<NLMSG_LENGTH(sizeof(struct ifinfomsg))||length>WR_EOIP_CHANGE_LENGTH)return -1;
 descriptor=socket(AF_NETLINK,SOCK_RAW,NETLINK_ROUTE);
 if(descriptor<0)return -1;
 memset(&local,0,sizeof(local));
 local.nl_family=AF_NETLINK;
 memset(&kernel,0,sizeof(kernel));
 kernel.nl_family=AF_NETLINK;
 timeout.tv_sec=1;
 timeout.tv_usec=0;
 if(fcntl(descriptor,F_SETFD,FD_CLOEXEC)<0||
    setsockopt(descriptor,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout))||
    setsockopt(descriptor,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout))||
    bind(descriptor,(struct sockaddr *)&local,sizeof(local))||
    sendto(descriptor,request,length,0,(struct sockaddr *)&kernel,sizeof(kernel))!=(ssize_t)length)goto done;
 memset(&sender,0,sizeof(sender));
 memset(&message,0,sizeof(message));
 vector.iov_base=reply;
 vector.iov_len=sizeof(reply);
 message.msg_name=&sender;
 message.msg_namelen=sizeof(sender);
 message.msg_iov=&vector;
 message.msg_iovlen=1;
 received=recvmsg(descriptor,&message,0);
 if(received>0&&wr_eoip_change_reply(reply,(size_t)received,&sender,message.msg_namelen,
    message.msg_flags,sequence))result=0;
 done:
 close(descriptor);
 return result;
}

static inline int wr_eoip_query_via_link(void *context,const char *name,const char *owner,
 struct wr_eoip_observation *out)
{
 (void)context;
 return wr_eoip_query_link(name,owner,out);
}

/* talk returns 0 when one acknowledged change was accepted by the kernel;
 * query follows the netlink-query.h contract (0 unknown, 1 absent, 2 present).
 * Returns 1 only when the requested state is observed afterwards, 0 refuses
 * without changing anything. master_out reports the applied master index. */
static inline int wr_eoip_configure(int (*talk)(void *,const void *,size_t,uint32_t),void *talk_context,
 int (*query)(void *,const char *,const char *,struct wr_eoip_observation *),void *query_context,
 const char *name,const char *owner,unsigned index,unsigned mtu,const char *bridge,unsigned *master_out)
{
 unsigned char request[WR_EOIP_CHANGE_LENGTH];
 struct wr_eoip_observation observed,probe;
 const uint32_t sequence=0x57454f43U;
 unsigned master=0;
 size_t length=0;
 int result;

 if(!master_out)return 0;
 *master_out=0;
 if(!talk||!query||!owner||!*owner||!wr_eoip_managed_name(name)||!index||
    mtu<68||mtu>WR_EOIP_MAX_MTU||!bridge)return 0;
 if(query(query_context,name,owner,&observed)!=2||!observed.owned||observed.ifindex!=(int)index)return 0;
 if(*bridge){
  if(!strcmp(bridge,name)||!wr_eoip_managed_name(bridge)||
     query(query_context,bridge,owner,&probe)!=2||strcmp(probe.kind,"bridge")||
     probe.ifindex<=0||(unsigned)probe.ifindex==index)return 0;
  master=(unsigned)probe.ifindex;
 }else if(observed.master)return 0;
 if(observed.mtu==mtu&&(observed.flags&IFF_UP)&&observed.master==master){
  *master_out=master;
  return 1;
 }
 if(!wr_eoip_build_change(request,sizeof(request),index,mtu,master,sequence,&length)||
    talk(talk_context,request,length,sequence))return 0;
 result=query(query_context,name,owner,&observed);
 if(result!=2||!observed.owned||observed.ifindex!=(int)index||observed.mtu!=mtu||
    !(observed.flags&IFF_UP)||observed.master!=master)return 0;
 *master_out=master;
 return 1;
}

static inline int wr_eoip_configure_link(const char *name,const char *owner,unsigned index,unsigned mtu,
 const char *bridge,unsigned *master_out)
{
 return wr_eoip_configure(wr_eoip_socket_change,NULL,wr_eoip_query_via_link,NULL,
  name,owner,index,mtu,bridge,master_out);
}
#endif