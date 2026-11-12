#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <stdarg.h>
#include <errno.h>
#include "driver-api-client.h"
static unsigned sockets,calls,closes;static int socket_error,ioctl_error,close_error,bad_reply,open_only_error;
static unsigned char observed_id[16];
static int bad_closed_reply,current_only_error,current_close_error,current_response;
static unsigned fail_socket_at;
static int close_control_error;
static int fake_socket(int domain,int type,int protocol){
 assert(domain==AF_INET&&type==(SOCK_DGRAM|SOCK_CLOEXEC)&&!protocol);sockets++;
 return (socket_error||sockets==fail_socket_at)?-1:10;
}
static int fake_close(int fd){assert(fd==10);closes++;return (close_error||(current_close_error&&current_response))?-1:0;}
static int fake_ioctl(int fd,unsigned long command,...){
 va_list ap;va_start(ap,command);struct ifreq *r=va_arg(ap,struct ifreq *);va_end(ap);
 assert(fd==10&&!strcmp(r->ifr_name,"ra2"));calls++;current_response=0;
 if(command==WR_IOT_DRIVER_IOCTL_IDENTITY){
  unsigned char id[16];assert(wr_iot_driver_query_decode(id,(unsigned char *)r->ifr_data,32));
  assert(wr_iot_driver_identity_encode((unsigned char *)r->ifr_data,32,1,2));
  if(bad_reply)r->ifr_data[4]=99;
 }else if(command==WR_IOT_DRIVER_IOCTL_CLOSED_CONFIG){
  unsigned char id[16];unsigned char *wire=(unsigned char *)r->ifr_data;
  if(wire[4]==10||wire[4]==13){
   struct wr_iot_driver_close_request decoded;
   assert((wire[4]==10?wr_iot_driver_close_request_decode(&decoded,wire,64):
           wr_iot_driver_close_progress_decode(&decoded,wire,64)));
   assert(decoded.adapter_epoch==1&&decoded.device_generation==2&&decoded.open_token==3);
   assert(decoded.open_request_id[0]==1);
   errno=close_control_error;
   return close_control_error?-1:0;
  }else if(wire[4]==11){
   current_response=1;
   assert(wr_iot_driver_open_current_query_decode(id,wire,64));
   assert(wr_iot_driver_open_current_encode(wire,64,id,1,2,3));
  }else if(wire[4]==8){
   assert(wr_iot_driver_uncertain_query_decode(id,wire,64));
   assert(wr_iot_driver_uncertain_encode(wire,64,id,1,2,3));
  }else if(wire[4]==6){
   assert(wr_iot_driver_refusal_query_decode(id,wire,64));
   assert(wr_iot_driver_refusal_encode(wire,64,id,1,2,3));
   if(bad_closed_reply==5)wire[48]=1;
  }else{
   assert(wr_iot_driver_closed_query_decode(id,wire,64));
   assert(wr_iot_driver_closed_encode(wire,64,id,1,2,3,4));
  }
  if(bad_closed_reply==1)wire[8]^=1;
  if(bad_closed_reply==2)wire[63]=3;
  if(bad_closed_reply==3)memset(wire+24,0,8);
  if(bad_closed_reply==4)wire[3]='1';
  if(bad_closed_reply==5&&wire[4]==5)memset(wire+48,0,8);
 }else{
  struct wr_iot_driver_open_request decoded;
  assert(command==WR_IOT_DRIVER_IOCTL_OPEN&&wr_iot_driver_open_decode(&decoded,(unsigned char *)r->ifr_data,144));
  assert(decoded.adapter_epoch==1&&decoded.device_generation==2&&!strcmp((char *)decoded.password,"password"));
  memcpy(observed_id,decoded.request_id,16);
  wr_iot_driver_request_wipe(&decoded);
 }
 return (ioctl_error||(open_only_error&&command==WR_IOT_DRIVER_IOCTL_OPEN)||(current_only_error&&current_response))?-1:0;
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
 assert(wr_iot_driver_open_submit(&q)==WR_IOT_DRIVER_OPEN_COMPLETED&&calls==before+4);
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
 assert(wr_iot_driver_open_requested(id,&requested)==WR_IOT_DRIVER_OPEN_COMPLETED&&calls==baseline+4);
 assert(observed_id[0]==0x01&&observed_id[1]==0x23&&observed_id[7]==0xef&&observed_id[15]==0xef);
 ioctl_error=1;assert(wr_iot_driver_open_requested(id,&requested)==WR_IOT_DRIVER_NOT_SUBMITTED);ioctl_error=0;
 open_only_error=1;unsigned prior=calls;
 assert(wr_iot_driver_open_requested(id,&requested)==WR_IOT_DRIVER_OPEN_UNCERTAIN&&calls==prior+2);open_only_error=0;
 assert(!strcmp(requested.password,"password"));
 struct wr_iot_driver_closed_result state={99,99,99,99};unsigned char empty_id[16]={0};
 baseline=calls;
 assert(!wr_iot_driver_closed_configuration_read(empty_id,&state)&&calls==baseline&&!state.adapter_epoch);
 assert(!wr_iot_driver_closed_configuration_read(query_id,NULL)&&calls==baseline);
 socket_error=1;assert(!wr_iot_driver_closed_configuration_read(query_id,&state)&&calls==baseline);socket_error=0;
 ioctl_error=1;assert(!wr_iot_driver_closed_configuration_read(query_id,&state)&&!state.close_serial);ioctl_error=0;
 close_error=1;assert(!wr_iot_driver_closed_configuration_read(query_id,&state)&&!state.open_token);close_error=0;
 for(bad_closed_reply=1;bad_closed_reply<=5;bad_closed_reply++){
  assert(!wr_iot_driver_closed_configuration_read(query_id,&state));
  assert(!state.adapter_epoch&&!state.device_generation&&!state.open_token&&!state.close_serial);
 }
 bad_closed_reply=0;assert(wr_iot_driver_closed_configuration_read(query_id,&state));
 assert(state.adapter_epoch==1&&state.device_generation==2&&state.open_token==3&&state.close_serial==4);
 struct wr_iot_driver_refusal_result refusal={99,99,99};
 baseline=calls;
 assert(!wr_iot_driver_refusal_read(empty_id,&refusal)&&calls==baseline&&!refusal.adapter_epoch);
 socket_error=1;assert(!wr_iot_driver_refusal_read(query_id,&refusal)&&calls==baseline);socket_error=0;
 ioctl_error=1;assert(!wr_iot_driver_refusal_read(query_id,&refusal)&&!refusal.attempt_token);ioctl_error=0;
 close_error=1;assert(!wr_iot_driver_refusal_read(query_id,&refusal)&&!refusal.attempt_token);close_error=0;
 for(bad_closed_reply=1;bad_closed_reply<=5;bad_closed_reply++){
  assert(!wr_iot_driver_refusal_read(query_id,&refusal));
  assert(!refusal.adapter_epoch&&!refusal.device_generation&&!refusal.attempt_token);
 }
 bad_closed_reply=0;assert(wr_iot_driver_refusal_read(query_id,&refusal));
 assert(refusal.adapter_epoch==1&&refusal.device_generation==2&&refusal.attempt_token==3);
 struct wr_iot_driver_attempt attempt;
 memset(&attempt,0xff,sizeof(attempt));
 assert(wr_iot_driver_open_requested_tracked("bad",&requested,&attempt)==WR_IOT_DRIVER_NOT_SUBMITTED);
 assert(!attempt.identity.adapter_epoch&&!attempt.request_id[0]);
 open_only_error=1;
 assert(wr_iot_driver_open_requested_tracked(id,&requested,&attempt)==WR_IOT_DRIVER_OPEN_UNCERTAIN);
 open_only_error=0;
 assert(attempt.identity.adapter_epoch==1&&attempt.identity.device_generation==2&&attempt.request_id[0]==1);
 assert(wr_iot_driver_attempt_refused(&attempt));
 struct wr_iot_driver_uncertain_result diagnostic;
 assert(wr_iot_driver_uncertain_read(&attempt,&diagnostic)&&diagnostic.attempt_token==3);
 socket_error=1;assert(!wr_iot_driver_uncertain_read(&attempt,&diagnostic)&&!diagnostic.attempt_token);socket_error=0;
 close_error=1;assert(!wr_iot_driver_uncertain_read(&attempt,&diagnostic)&&!diagnostic.attempt_token);close_error=0;
 attempt.identity.device_generation++;assert(!wr_iot_driver_uncertain_read(&attempt,&diagnostic)&&!diagnostic.device_generation);attempt.identity.device_generation--;

 attempt.identity.adapter_epoch++;assert(!wr_iot_driver_uncertain_read(&attempt,&diagnostic)&&!diagnostic.attempt_token);attempt.identity.adapter_epoch--;
 ioctl_error=1;assert(!wr_iot_driver_uncertain_read(&attempt,&diagnostic)&&!diagnostic.adapter_epoch);ioctl_error=0;
 for(bad_closed_reply=1;bad_closed_reply<=4;bad_closed_reply++)assert(!wr_iot_driver_uncertain_read(&attempt,&diagnostic));
 bad_closed_reply=0;

 attempt.identity.adapter_epoch++;assert(!wr_iot_driver_attempt_refused(&attempt));attempt.identity.adapter_epoch--;
 attempt.identity.device_generation++;assert(!wr_iot_driver_attempt_refused(&attempt));attempt.identity.device_generation--;
 ioctl_error=1;assert(!wr_iot_driver_attempt_refused(&attempt));ioctl_error=0;
 assert(!wr_iot_driver_attempt_refused(NULL));
 assert(wr_iot_driver_attempt_closed(&attempt,&state)&&state.close_serial==4);
 attempt.identity.adapter_epoch++;assert(!wr_iot_driver_attempt_closed(&attempt,&state));
 assert(!state.adapter_epoch&&!state.open_token&&!state.close_serial);attempt.identity.adapter_epoch--;
 attempt.identity.device_generation++;assert(!wr_iot_driver_attempt_closed(&attempt,&state));
 assert(!state.device_generation);attempt.identity.device_generation--;
 ioctl_error=1;assert(!wr_iot_driver_attempt_closed(&attempt,&state));ioctl_error=0;
 assert(!wr_iot_driver_attempt_closed(NULL,&state)&&!state.close_serial);
 assert(!wr_iot_driver_attempt_closed(&attempt,NULL));
 struct wr_iot_driver_open_current_result current;
 assert(wr_iot_driver_open_current_read(&attempt,&current)&&current.open_token==3);
 attempt.identity.adapter_epoch++;assert(!wr_iot_driver_open_current_read(&attempt,&current)&&!current.open_token);attempt.identity.adapter_epoch--;
 attempt.identity.device_generation++;assert(!wr_iot_driver_open_current_read(&attempt,&current)&&!current.open_token);attempt.identity.device_generation--;
 for(bad_closed_reply=1;bad_closed_reply<=4;bad_closed_reply++)assert(!wr_iot_driver_open_current_read(&attempt,&current)&&!current.open_token);
 bad_closed_reply=0;ioctl_error=1;assert(!wr_iot_driver_open_current_read(&attempt,&current)&&!current.open_token);ioctl_error=0;
 close_error=1;assert(!wr_iot_driver_open_current_read(&attempt,&current)&&!current.open_token);close_error=0;
 socket_error=1;assert(!wr_iot_driver_open_current_read(&attempt,&current)&&!current.open_token);socket_error=0;
 assert(!wr_iot_driver_open_current_read(NULL,&current)&&!current.open_token);
 socket_error=1;
 assert(wr_iot_driver_open_requested_tracked(id,&requested,&attempt)==WR_IOT_DRIVER_NOT_SUBMITTED);
 assert(!attempt.identity.adapter_epoch&&!attempt.identity.device_generation);
 for(unsigned j=0;j<16;j++)assert(!attempt.request_id[j]);
 socket_error=0;

 /* OPEN succeeds, but readback is absent/corrupt/fails: retain exact attempt
  * and report uncertainty, with one OPEN and no transport retry. */
 for(unsigned fault=0;fault<4;fault++){
  unsigned prior_calls=calls;
  current_only_error=fault==0;bad_closed_reply=fault==1?1:0;
  current_close_error=fault==2;fail_socket_at=fault==3?sockets+3:0;
  assert(wr_iot_driver_open_requested_tracked(id,&requested,&attempt)==WR_IOT_DRIVER_OPEN_UNCERTAIN);
  assert(calls==prior_calls+(fault==3?2:3));
  assert(attempt.identity.adapter_epoch==1&&attempt.identity.device_generation==2);
  assert(!memcmp(attempt.request_id,observed_id,16));
  assert(!strcmp(requested.password,"password"));
 }
 current_only_error=current_close_error=bad_closed_reply=0;fail_socket_at=0;
 struct wr_iot_driver_close_request close_request={{1},1,2,3};
 for(unsigned mode=0;mode<2;mode++){
  for(unsigned fault=0;fault<8;fault++){
   struct wr_iot_driver_close_request input=close_request;
   unsigned prior_calls=calls,prior_closes=closes;
   close_control_error=0;socket_error=close_error=0;
   switch(fault){
    case 1:input.open_token=0;break;
    case 2:socket_error=1;break;
    case 3:close_control_error=EAGAIN;break;
    case 4:close_control_error=EINPROGRESS;break;
    case 5:close_control_error=EBUSY;break;
    case 6:close_error=1;break;
    case 7:close_control_error=EAGAIN;close_error=1;break;
   }
   enum wr_iot_driver_close_submit_result outcome=mode?
    wr_iot_driver_close_progress_submit(&input):wr_iot_driver_close_submit(&input);
   enum wr_iot_driver_close_submit_result expected=fault==0?WR_IOT_DRIVER_CLOSE_CALL_COMPLETED:
    fault<=2?WR_IOT_DRIVER_CLOSE_NOT_SUBMITTED:
    mode&&(fault==3||fault==4)?WR_IOT_DRIVER_CLOSE_PENDING:WR_IOT_DRIVER_CLOSE_UNCERTAIN;
   assert(outcome==expected);
   assert(calls==prior_calls+((fault==1||fault==2)?0:1));
   assert(closes==prior_closes+((fault==1||fault==2)?0:1));
   assert(!memcmp(&close_request,&(struct wr_iot_driver_close_request){{1},1,2,3},sizeof(close_request)));
  }
 }
 close_error=socket_error=close_control_error=0;
 assert(wr_iot_driver_close_submit(NULL)==WR_IOT_DRIVER_CLOSE_NOT_SUBMITTED);
 assert(wr_iot_driver_close_progress_submit(NULL)==WR_IOT_DRIVER_CLOSE_NOT_SUBMITTED);
 puts("PASS actual RC API client: fixed ra2/CLOEXEC, strict identity response, no OPEN before validation, transaction ID/ON validation, one OPEN/no retry, uncertain ioctl/close outcomes and strict CLOSED configuration response; system calls injected, no device operation");return 0;
}
