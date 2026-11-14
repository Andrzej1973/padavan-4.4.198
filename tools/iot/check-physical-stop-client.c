#define _GNU_SOURCE
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include "physical-stop-client.h"
static int fail_socket,fail_ioctl,fail_close,bad,opens,calls,closes;
static int mock_socket(int domain,int type,int protocol){
 assert(domain==AF_INET&&type==(SOCK_DGRAM|SOCK_CLOEXEC)&&!protocol);opens++;
 return fail_socket?-1:12;
}
static int mock_ioctl(int fd,unsigned long command,...){
 va_list ap;struct ifreq *r;struct wr_iot_physical_stop_request request;
 assert(fd==12&&command==WR_IOT_DRIVER_IOCTL_CLOSED_CONFIG);calls++;
 va_start(ap,command);r=va_arg(ap,struct ifreq *);va_end(ap);
 assert(!strcmp(r->ifr_name,"ra0"));
 assert(wr_iot_physical_stop_request_decode(&request,(unsigned char *)r->ifr_data,64));
 if(fail_ioctl)return -1;
 unsigned status=request.action==WR_STOP_ARM?WR_STOP_ARMED:
  request.action==WR_STOP_QUERY?WR_STOP_RUNNING:
  request.action==WR_STOP_CANCEL?WR_STOP_CANCELLED:WR_STOP_RELEASED;
 assert(wr_iot_physical_stop_response_encode((unsigned char *)r->ifr_data,64,
   &request,request.action==WR_STOP_ARM?9:request.attempt,status));
 if(bad==1)r->ifr_data[48]^=1;
 if(bad==2)r->ifr_data[0]='?';
 return 0;
}
static int mock_close(int fd){assert(fd==12);closes++;return fail_close?-1:0;}
#define socket mock_socket
#define ioctl mock_ioctl
#define close mock_close
#include "physical-stop-client.c"
int main(void){
 for(unsigned action=WR_STOP_ARM;action<=WR_STOP_RELEASE;action++){
  for(unsigned fault=0;fault<7;fault++){
   struct wr_iot_physical_stop_request request={.action=action,.epoch=1,
    .generation=2,.open_token=3,.closed_serial=4,.attempt=action==WR_STOP_ARM?0:9,.nonce={7}};
   struct wr_iot_physical_stop_response out;
   memset(&out,0xa5,sizeof(out));opens=calls=closes=0;
   fail_socket=fault==1;fail_ioctl=fault==2;fail_close=fault==3;
   bad=fault==4?1:fault==5?2:0;if(fault==6)request.epoch=0;
   enum wr_iot_physical_call_result result=wr_iot_physical_stop_call(&request,&out);
   assert(result==(fault==0?WR_PHYSICAL_CALL_ACKNOWLEDGED:
     fault==1||fault==6?WR_PHYSICAL_CALL_NOT_SUBMITTED:WR_PHYSICAL_CALL_UNCERTAIN));
   assert(calls==(fault==1||fault==6?0:1)&&closes==calls);
   if(!fault)assert(out.identity.attempt==9&&out.identity.open_token==3);
   else{struct wr_iot_physical_stop_response zero={0};assert(!memcmp(&out,&zero,sizeof(out)));}
  }
 }
 fail_socket=fail_ioctl=fail_close=bad=0;
 struct wr_iot_physical_stop_response alias={.identity={.action=WR_STOP_QUERY,
   .epoch=1,.generation=2,.open_token=3,.closed_serial=4,.attempt=9,.nonce={7}}};
 assert(wr_iot_physical_stop_call(&alias.identity,&alias)==WR_PHYSICAL_CALL_ACKNOWLEDGED);
 assert(alias.identity.attempt==9);
 puts("PASS fixed ra0 physical client:4 actions, no retries, socket failures not submitted, ioctl/close/malformed replies uncertain, exact response and input/output alias; kernel mocked");
}
