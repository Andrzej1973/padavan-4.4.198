#define _GNU_SOURCE
#include <assert.h>
#include <stdarg.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include "physical-rebind-client.h"
static int failure,opens,calls,closes;
static int mock_socket(int domain,int type,int protocol)
{assert(domain==AF_INET&&type==(SOCK_DGRAM|SOCK_CLOEXEC)&&!protocol);opens++;return failure==1?-1:12;}
static int mock_ioctl(int fd,unsigned long command,...)
{
 va_list ap;struct ifreq *r;struct wr_iot_physical_rebind_request decoded;
 unsigned char *wire;unsigned length;
 assert(fd==12&&command==WR_IOT_DRIVER_IOCTL_CLOSED_CONFIG);calls++;
 va_start(ap,command);r=va_arg(ap,struct ifreq *);va_end(ap);
 assert(!strcmp(r->ifr_name,"ra2"));wire=(unsigned char *)r->ifr_data;
 length=wire[5]==WR_REBIND_OBSERVE?72:216;
 assert(wr_iot_physical_rebind_decode(&decoded,wire,length));
 wr_iot_physical_rebind_wipe(&decoded);return failure==2?-1:0;
}
static int mock_close(int fd){assert(fd==12);closes++;return failure==3?-1:0;}
#define socket mock_socket
#define ioctl mock_ioctl
#define close mock_close
#include "physical-rebind-client.c"
int main(void)
{
 unsigned operation;
 for(operation=1;operation<=2;operation++)for(failure=0;failure<5;failure++){
  struct wr_iot_physical_rebind_request r={.operation=operation};
  struct wr_iot_physical_rebind_request before;
  r.physical=(struct wr_iot_physical_stop_request){.action=WR_STOP_RELEASE,.epoch=5,.generation=2,.open_token=3,.closed_serial=4,.attempt=6,.nonce={1}};
  r.open=(struct wr_iot_driver_open_request){.adapter_epoch=7,.device_generation=2,.request_id={8},.ssid_length=3,.password_length=8,.ssid="IoT",.password="password"};
  if(failure==4)r.physical.attempt=0;
  before=r;opens=calls=closes=0;
  assert(wr_iot_physical_rebind_call(&r)==(failure==0?WR_REBIND_IOCTL_RETURNED:failure==1||failure==4?WR_REBIND_NOT_SUBMITTED:WR_REBIND_UNCERTAIN));
  assert(calls==(failure==1||failure==4?0:1)&&closes==calls);
  assert(!memcmp(&r,&before,sizeof(r)));
 }
 assert(wr_iot_physical_rebind_call(0)==WR_REBIND_NOT_SUBMITTED);return 0;
}
