#ifndef WR_EOIP_NETLINK_QUERY_H
#define WR_EOIP_NETLINK_QUERY_H
#include "observation.h"
#include <errno.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>
/* 0 unknown/error, 1 confirmed absent, 2 observed interface (possibly foreign). */
static int wr_eoip_link_reply(const void *buffer,size_t size,const struct sockaddr_nl *sender,
 socklen_t sender_length,int flags,uint32_t sequence,const char *name,const char *owner,
 struct wr_eoip_observation *out)
{
 struct nlmsghdr header;
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!buffer||!sender||sender_length!=sizeof(*sender)||sender->nl_family!=AF_NETLINK||
    sender->nl_pid!=0||sender->nl_groups!=0||(flags&(MSG_TRUNC|MSG_CTRUNC))||
    size<sizeof(header)||size>4096)return 0;
 memcpy(&header,buffer,sizeof(header));
 if(header.nlmsg_seq!=sequence||header.nlmsg_len!=size)return 0;
 if(header.nlmsg_type==NLMSG_ERROR){
  struct nlmsgerr error;
  if(size<NLMSG_LENGTH(sizeof(error)))return 0;
  memcpy(&error,(const unsigned char *)buffer+NLMSG_HDRLEN,sizeof(error));
  if(error.msg.nlmsg_type!=RTM_GETLINK||error.msg.nlmsg_seq!=sequence)return 0;
  return error.error==-ENODEV||error.error==-ENOENT ? 1 : 0;
 }
 return wr_eoip_decode_link(buffer,size,sequence,name,owner,out)?2:0;
}
/* Read-only RTM_GETLINK. Use from a supervised service worker, not HTTP's loop. */
static int wr_eoip_query_link(const char *name,const char *owner,struct wr_eoip_observation *out)
{
 unsigned char request[128],reply[4096];struct nlmsghdr header;struct ifinfomsg info;
 struct rtattr attr;struct sockaddr_nl local,kernel,sender;struct timeval timeout;
 struct iovec iov;struct msghdr message;size_t length,name_length;int fd,result=0;ssize_t received;
 const uint32_t sequence=0x57454f49U;
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!name||!owner||!*name||!*owner||(name_length=strlen(name))>=16||strlen(owner)>=64||
    strspn(name,"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-")!=name_length)return 0;
 memset(request,0,sizeof(request));memset(&header,0,sizeof(header));memset(&info,0,sizeof(info));
 length=NLMSG_LENGTH(sizeof(info));attr.rta_type=IFLA_IFNAME;attr.rta_len=(unsigned short)RTA_LENGTH(name_length+1);
 memcpy(request+length,&attr,sizeof(attr));memcpy(request+length+RTA_LENGTH(0),name,name_length+1);
 length+=RTA_ALIGN(attr.rta_len);header.nlmsg_len=(unsigned)length;header.nlmsg_type=RTM_GETLINK;
 header.nlmsg_flags=NLM_F_REQUEST;header.nlmsg_seq=sequence;info.ifi_family=AF_UNSPEC;
 memcpy(request,&header,sizeof(header));memcpy(request+NLMSG_HDRLEN,&info,sizeof(info));
 fd=socket(AF_NETLINK,SOCK_RAW,NETLINK_ROUTE);if(fd<0)return 0;
 memset(&local,0,sizeof(local));local.nl_family=AF_NETLINK;
 memset(&kernel,0,sizeof(kernel));kernel.nl_family=AF_NETLINK;
 timeout.tv_sec=1;timeout.tv_usec=0;
 if(fcntl(fd,F_SETFD,FD_CLOEXEC)<0||
    setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout))||
    setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout))||
    bind(fd,(struct sockaddr *)&local,sizeof(local))||
    sendto(fd,request,length,0,(struct sockaddr *)&kernel,sizeof(kernel))!=(ssize_t)length)goto done;
 memset(&sender,0,sizeof(sender));memset(&message,0,sizeof(message));
 iov.iov_base=reply;iov.iov_len=sizeof(reply);message.msg_name=&sender;message.msg_namelen=sizeof(sender);
 message.msg_iov=&iov;message.msg_iovlen=1;
 received=recvmsg(fd,&message,0);
 if(received>0)result=wr_eoip_link_reply(reply,(size_t)received,&sender,message.msg_namelen,
  message.msg_flags,sequence,name,owner,out);
 done:
 close(fd);return result;
}
#endif
