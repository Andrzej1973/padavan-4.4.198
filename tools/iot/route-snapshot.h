/* Read-only all-table IPv4 route dump. Caller serializes configuration changes. */
#ifndef WR_IOT_ROUTE_SNAPSHOT_H
#define WR_IOT_ROUTE_SNAPSHOT_H
#include "route-prefix.h"
#include <poll.h>
#include <errno.h>
static int wr_iot_route_snapshot(struct wr_iot_inventory *out) {
 struct {struct nlmsghdr header;struct rtmsg route;} request;
 struct sockaddr_nl local,kernel;struct wr_iot_inventory candidate;
 union {struct nlmsghdr alignment;unsigned char bytes[32768];} buffer;
 int fd,ok=0;unsigned int batch;
 if(!out||out->count>WR_IOT_INVENTORY_MAX)return 0;
 candidate=*out;
 memset(&local,0,sizeof(local));local.nl_family=AF_NETLINK;
 memset(&kernel,0,sizeof(kernel));kernel.nl_family=AF_NETLINK;
 fd=socket(AF_NETLINK,SOCK_RAW,NETLINK_ROUTE);if(fd<0)return 0;
 if(bind(fd,(struct sockaddr *)&local,sizeof(local)))goto done;
 memset(&request,0,sizeof(request));request.header.nlmsg_len=NLMSG_LENGTH(sizeof(struct rtmsg));
 request.header.nlmsg_type=RTM_GETROUTE;request.header.nlmsg_flags=NLM_F_REQUEST|NLM_F_DUMP;
 request.header.nlmsg_seq=1;request.route.rtm_family=AF_INET;request.route.rtm_table=RT_TABLE_UNSPEC;
 if(sendto(fd,&request,request.header.nlmsg_len,0,(struct sockaddr *)&kernel,sizeof(kernel))!=(ssize_t)request.header.nlmsg_len)goto done;
 for(batch=0;batch<128;batch++) {
  struct pollfd ready;struct sockaddr_nl sender;struct iovec io;struct msghdr message;
  struct nlmsghdr *header;ssize_t received;int length;
  memset(&ready,0,sizeof(ready));ready.fd=fd;ready.events=POLLIN;
  if(poll(&ready,1,3000)!=1||!(ready.revents&POLLIN)||(ready.revents&(POLLERR|POLLHUP|POLLNVAL)))goto done;
  memset(&message,0,sizeof(message));memset(&sender,0,sizeof(sender));
  io.iov_base=buffer.bytes;io.iov_len=sizeof(buffer.bytes);message.msg_iov=&io;message.msg_iovlen=1;
  message.msg_name=&sender;message.msg_namelen=sizeof(sender);
  received=recvmsg(fd,&message,0);
  if(received<=0||received>(ssize_t)sizeof(buffer.bytes)||(message.msg_flags&(MSG_TRUNC|MSG_CTRUNC))||
     message.msg_namelen!=sizeof(sender)||sender.nl_family!=AF_NETLINK||sender.nl_pid!=0)goto done;
  length=(int)received;
  for(header=(struct nlmsghdr *)buffer.bytes;NLMSG_OK(header,length);header=NLMSG_NEXT(header,length)) {
   if(header->nlmsg_seq!=1||(header->nlmsg_flags&NLM_F_DUMP_INTR))goto done;
   if(header->nlmsg_type==NLMSG_DONE) {
    int status=0;size_t payload=header->nlmsg_len-NLMSG_HDRLEN;
    if(payload&&payload<sizeof(status))goto done;
    if(payload)memcpy(&status,NLMSG_DATA(header),sizeof(status));
    if(status||NLMSG_ALIGN(header->nlmsg_len)!=(unsigned int)length)goto done;
    *out=candidate;ok=1;goto done;
   }
   if(header->nlmsg_type!=RTM_NEWROUTE||!wr_iot_route_prefix(&candidate,header,header->nlmsg_len))goto done;
  }
  if(length)goto done;
 }
done:close(fd);return ok;
}
#endif
