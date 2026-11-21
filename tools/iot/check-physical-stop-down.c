#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <string.h>
static int failure,sockets,reads,writes,closes;
static int test_socket(int domain,int type,int protocol){assert(domain==AF_INET&&type==(SOCK_DGRAM|SOCK_CLOEXEC)&&!protocol);sockets++;return failure==1?-1:7;}
static int test_close(int fd){assert(fd==7);closes++;return failure==5?-1:0;}
static int test_ioctl(int fd,unsigned long op,struct ifreq *r){
 assert(fd==7&&!strcmp(r->ifr_name,"ra0"));
 if(op==SIOCGIFFLAGS){reads++;r->ifr_flags=IFF_BROADCAST|(failure==3?0:IFF_UP);return failure==2?-1:0;}
 assert(op==SIOCSIFFLAGS);assert(r->ifr_flags==IFF_BROADCAST);writes++;return failure==4?-1:0;
}
#define socket test_socket
#define close test_close
#define ioctl test_ioctl
#include "physical-stop-down.c"
int main(void){
 for(failure=0;failure<=5;failure++){
  sockets=reads=writes=closes=0;
  enum wr_iot_physical_down_result r=wr_iot_physical_stop_down();
  assert(sockets==1&&reads==(failure!=1));
  assert(writes==(failure==0||failure>=4));
  assert(closes==(failure!=1));
  assert(r==(failure==0?WR_PHYSICAL_DOWN_IOCTL_RETURNED:failure>=4?WR_PHYSICAL_DOWN_UNCERTAIN:WR_PHYSICAL_DOWN_NOT_SUBMITTED));
 }
 puts("PASS fixed ra0 same-task DOWN: pre-submit failures/already-down refuse, single ioctl no retries, write/close errors uncertain, other flags preserved; no driver completion claim");
}
