#define _GNU_SOURCE
#include "route-prefix.h"
#include <assert.h>
#include <errno.h>
#include <poll.h>
#include <time.h>
#include <stdio.h>
static int scenario,reads,polls,closed,sockets;
static long elapsed;
static int fake_clock(clockid_t clock,struct timespec *now)
{
 assert(clock==CLOCK_MONOTONIC);
 if(scenario==3)return -1;
 now->tv_sec=elapsed/1000;now->tv_nsec=(elapsed%1000)*1000000;
 return 0;
}
static int fake_socket(int family,int kind,int protocol)
{
 assert(family==AF_NETLINK&&protocol==NETLINK_ROUTE);
 assert(kind==(SOCK_RAW|SOCK_NONBLOCK|SOCK_CLOEXEC));sockets++;return 9;
}
static int fake_bind(int fd,const struct sockaddr *address,socklen_t length)
{assert(fd==9&&address&&length==sizeof(struct sockaddr_nl));return 0;}
static ssize_t fake_send(int fd,const void *buffer,size_t length,int flags,const struct sockaddr *address,socklen_t size)
{assert(fd==9&&buffer&&!flags&&address&&size==sizeof(struct sockaddr_nl));return (ssize_t)length;}
static int fake_poll(struct pollfd *fd,nfds_t count,int timeout)
{
 assert(fd->fd==9&&count==1&&timeout==3000-elapsed);
 polls++;fd->revents=POLLIN;return 1;
}
static ssize_t fake_recv(int fd,struct msghdr *message,int flags)
{
 struct nlmsghdr *header=message->msg_iov[0].iov_base;
 struct sockaddr_nl *sender=message->msg_name;
 assert(fd==9&&!flags);reads++;
 if(scenario==2){errno=EAGAIN;return -1;}
 memset(header,0,128);header->nlmsg_seq=1;
 sender->nl_family=AF_NETLINK;sender->nl_pid=0;
 if(reads==1){
  struct rtmsg *route;
  struct rtattr *attribute;
  uint32_t address=htonl(0x0a010200U);
  header->nlmsg_type=RTM_NEWROUTE;
  header->nlmsg_len=NLMSG_LENGTH(sizeof(struct rtmsg))+RTA_LENGTH(sizeof(address));
  route=NLMSG_DATA(header);route->rtm_family=AF_INET;
  route->rtm_dst_len=24;route->rtm_type=RTN_UNICAST;
  attribute=RTM_RTA(route);attribute->rta_type=RTA_DST;
  attribute->rta_len=RTA_LENGTH(sizeof(address));
  memcpy(RTA_DATA(attribute),&address,sizeof(address));
 }else{header->nlmsg_type=NLMSG_DONE;header->nlmsg_len=NLMSG_HDRLEN;}
 elapsed+=scenario==1?1500:100;
 return header->nlmsg_len;
}
static int fake_close(int fd){assert(fd==9);closed++;return 0;}
#define clock_gettime fake_clock
#define socket fake_socket
#define bind fake_bind
#define sendto fake_send
#define poll fake_poll
#define recvmsg fake_recv
#define close fake_close
#include "route-snapshot.h"
int main(void)
{
 for(scenario=0;scenario<4;scenario++){
  struct wr_iot_inventory inventory={0},before;
  assert(wr_iot_inventory_add(&inventory,0xc0a80100U,0xffffff00U));before=inventory;
  elapsed=reads=polls=closed=sockets=0;
  assert(wr_iot_route_snapshot(&inventory)==(scenario==0));
  if(scenario==0){assert(inventory.count==2&&reads==2&&polls==2);}
  else assert(!memcmp(&before,&inventory,sizeof(before)));
  assert(closed==sockets);
  if(scenario==1)assert(elapsed==3000&&reads==2&&polls==2);
  if(scenario==2)assert(reads==1&&polls==1);
  if(scenario==3)assert(!sockets);
 }
 puts("PASS actual route dump total deadline, nonblocking socket, EAGAIN/clock failure and unchanged output on incomplete dump; I/O/time injected");
 return 0;
}
