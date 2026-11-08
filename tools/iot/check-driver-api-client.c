#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <stdarg.h>
#include "driver-api-client.h"
static unsigned sockets,calls,closes;static int socket_error,ioctl_error,close_error,bad_reply,open_only_error;
static unsigned char observed_id[16];
static int fake_socket(int domain,int type,int protocol){
 assert(domain==AF_INET&&type==(SOCK_DGRAM|SOCK_CLOEXEC)&&!protocol);sockets++;
 return socket_error?-1:10;
}
static int fake_close(int fd){assert(fd==10);closes++;return close_error?-1:0;}
static int fake_ioctl(int fd,unsigned long command,...){
 va_list ap;va_start(ap,command);struct ifreq *r=va_arg(ap,struct ifreq *);va_end(ap);
 assert(fd==10&&!strcmp(r->ifr_name,"ra2"));calls++;
 if(command==WR_IOT_DRIVER_IOCTL_IDENTITY){
  unsigned char id[16];assert(wr_iot_driver_query_decode(id,(unsigned char *)r->ifr_data,32));
  assert(wr_iot_driver_identity_encode((unsigned char *)r->ifr_data,32,1,2));
  if(bad_reply)r->ifr_data[4]=99;
 }else{
  struct wr_iot_driver_open_request decoded;
  assert(command==WR_IOT_DRIVER_IOCTL_OPEN&&wr_iot_driver_open_decode(&decoded,(unsigned char *)r->ifr_data,144));
  assert(decoded.adapter_epoch==1&&decoded.device_generation==2&&!strcmp((char *)decoded.password,"password"));
  memcpy(observed_id,decoded.request_id,16);
  wr_iot_driver_request_wipe(&decoded);
 }
 return (ioctl_error||(open_only_error&&command==WR_IOT_DRIVER_IOCTL_OPEN))?-1:0;
}
#define socket fake_socket
#define close fake_close
#define ioctl fake_ioctl
#include "driver-api-client.c"
int main(void){
 unsigned char query_id[16]={1};struct wr_iot_driver_identity identity={99,99};struct wr_iot_driver_open_request q={0};
 socket_error=1;assert(!wr_iot_driver_identity_read(&identity,query_id)&&!identity.adapter_epoch&&!calls&&!closes);
 socket_error=0;bad_reply=1;assert(!wr_iot_driver_identity_read(&identity,query_id)&&calls==1&&closes==1);bad_reply=0;
 assert(wr_iot_driver_identity_read(&identity,query_id)&&identity.adapter_epoch==1&&identity.device_generation==2);
 q.adapter_epoch=1;q.device_generation=2;q.request_id[0]=1;q.ssid_length=3;q.password_length=8;
 memcpy(q.ssid,"IoT",3);memcpy(q.password,"password",8);
 unsigned before=calls,opened=sockets;
 assert(wr_iot_driver_open_submit(NULL)==WR_IOT_DRIVER_NOT_SUBMITTED&&calls==before&&sockets==opened);
 socket_error=1;assert(wr_iot_driver_open_submit(&q)==WR_IOT_DRIVER_NOT_SUBMITTED&&calls==before);socket_error=0;
 ioctl_error=1;assert(wr_iot_driver_open_submit(&q)==WR_IOT_DRIVER_OPEN_UNCERTAIN&&calls==before+1);ioctl_error=0;
 close_error=1;assert(wr_iot_driver_open_submit(&q)==WR_IOT_DRIVER_OPEN_UNCERTAIN&&calls==before+2);close_error=0;
 assert(wr_iot_driver_open_submit(&q)==WR_IOT_DRIVER_OPEN_COMPLETED&&calls==before+3);
 assert(closes==calls);
 struct wr_iot_request requested={.enabled=1};
 const char *id="0123456789abcdef0123456789abcdef";
 memcpy(requested.ssid,"IoT",4);memcpy(requested.password,"password",9);
 unsigned baseline=calls;
 assert(wr_iot_driver_open_requested("bad",&requested)==WR_IOT_DRIVER_NOT_SUBMITTED&&calls==baseline);
 assert(wr_iot_driver_open_requested("00000000000000000000000000000000",&requested)==WR_IOT_DRIVER_NOT_SUBMITTED&&calls==baseline);
 requested.enabled=0;assert(wr_iot_driver_open_requested(id,&requested)==WR_IOT_DRIVER_NOT_SUBMITTED&&calls==baseline);requested.enabled=1;
 memset(requested.ssid,'x',sizeof(requested.ssid));
 assert(wr_iot_driver_open_requested(id,&requested)==WR_IOT_DRIVER_NOT_SUBMITTED&&calls==baseline);
 memcpy(requested.ssid,"IoT",4);
 bad_reply=1;assert(wr_iot_driver_open_requested(id,&requested)==WR_IOT_DRIVER_NOT_SUBMITTED&&calls==baseline+1);bad_reply=0;
 assert(wr_iot_driver_open_requested(id,&requested)==WR_IOT_DRIVER_OPEN_COMPLETED&&calls==baseline+3);
 assert(observed_id[0]==0x01&&observed_id[1]==0x23&&observed_id[7]==0xef&&observed_id[15]==0xef);
 ioctl_error=1;assert(wr_iot_driver_open_requested(id,&requested)==WR_IOT_DRIVER_NOT_SUBMITTED);ioctl_error=0;
 open_only_error=1;unsigned prior=calls;
 assert(wr_iot_driver_open_requested(id,&requested)==WR_IOT_DRIVER_OPEN_UNCERTAIN&&calls==prior+2);open_only_error=0;
 assert(!strcmp(requested.password,"password"));
 puts("PASS actual RC API client: fixed ra2/CLOEXEC, strict identity response, no OPEN before validation, transaction ID/ON validation, one OPEN/no retry, uncertain ioctl/close outcomes; system calls injected, no device operation");return 0;
}
