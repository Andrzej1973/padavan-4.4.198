/* Actual kernel reply -> errno transport -> RC client -> CLOSE controller.
 * Admission/netdev/syscalls are boundary actors; no real ioctl or RF proof. */
#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <assert.h>
#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-client.h"
#include "driver-close-controller.h"
typedef int INT;
typedef struct {unsigned users;} RTMP_ADAPTER;
typedef struct {int running;} device,*PNET_DEV;
static RTMP_ADAPTER adapter;
static device dev;
static int task;
#define current (&task)
static unsigned enters,net_closes,finishes,progresses,submissions;
static int after_close_error,finish_ok=1,fd_close_error,progress_error,positive_reply,legacy_module;
static int netif_running(PNET_DEV target){assert(target==&dev);return target->running;}
static int wr_iot_driver_close_request_enter(RTMP_ADAPTER *ad,PNET_DEV target,
 const struct wr_iot_driver_close_request *request,const void *owner){
 assert(ad==&adapter&&target==&dev&&owner==current&&request->adapter_epoch==1&&
        request->device_generation==2&&request->open_token==3&&request->open_request_id[0]==1);
 enters++;return ad->users?-EBUSY:0;
}
static int dev_close(PNET_DEV target){assert(target==&dev);target->running=0;net_closes++;return after_close_error;}
static int wr_iot_driver_close_finish_recover(RTMP_ADAPTER *ad,PNET_DEV target,
 const void *owner,int status,int *handoff){
 assert(ad==&adapter&&target==&dev&&owner==current&&status==after_close_error);
 *handoff=0;finishes++;return finish_ok;
}
#include "driver-api-close-entry.inc"
#undef current
static int fixture_socket(int domain,int type,int protocol){assert(domain==AF_INET&&type==(SOCK_DGRAM|SOCK_CLOEXEC)&&!protocol);return 10;}
static int fixture_close(int fd){assert(fd==10);return fd_close_error?-1:0;}
static int fixture_ioctl(int fd,unsigned long command,...){
 va_list args;va_start(args,command);struct ifreq *request=va_arg(args,struct ifreq *);va_end(args);
 assert(fd==10&&command==WR_IOT_DRIVER_IOCTL_CLOSED_CONFIG&&!strcmp(request->ifr_name,"ra2"));
 unsigned char *wire=(unsigned char *)request->ifr_data;int result;
 if(wire[4]==WR_IOT_DRIVER_CLOSE_REQUEST_OPCODE||wire[4]==WR_IOT_DRIVER_CLOSE_DEFER_REQUEST_OPCODE){
  submissions++;
  struct wr_iot_driver_close_request decoded;
  if(legacy_module&&!wr_iot_driver_close_request_decode(&decoded,wire,64))result=-EINVAL;
  else result=wr_iot_driver_close_reply(&adapter,&dev,request,wire);
 }else if(wire[4]==WR_IOT_DRIVER_CLOSE_PROGRESS_OPCODE){progresses++;result=-progress_error;}
 else {assert(wire[4]==WR_IOT_DRIVER_CLOSE_RELEASE_OPCODE);result=0;}
 if(positive_reply){errno=EBUSY;return 1;}
 if(result){errno=-result;return -1;}return 0;
}
#define socket fixture_socket
#define close fixture_close
#define ioctl fixture_ioctl
#include "driver-api-client.c"
#include "driver-close-controller.c"
static void reset(void){
 adapter.users=0;dev.running=1;enters=net_closes=finishes=progresses=submissions=0;
 after_close_error=fd_close_error=progress_error=positive_reply=legacy_module=0;finish_ok=1;
}
int main(void){
 struct wr_iot_driver_attempt attempt={.identity={1,2},.request_id={1}};
 struct wr_iot_driver_open_current_result receipt={1,2,3};
 struct wr_iot_close_controller controller={0};
 reset();adapter.users=1;
 assert(!wr_iot_close_controller_begin(&controller,&attempt,&receipt));
 assert(controller.phase==WR_IOT_CLOSE_IDLE&&submissions==1&&!net_closes&&!finishes);
 struct wr_iot_driver_close_request empty={0};assert(!memcmp(&controller.request,&empty,sizeof(empty)));
 adapter.users=0;
 assert(wr_iot_close_controller_begin(&controller,&attempt,&receipt));
 assert(controller.phase==WR_IOT_CLOSE_SUBMITTED&&submissions==2&&net_closes==1&&finishes==1);
 for(unsigned i=0;i<3;i++)assert(!wr_iot_close_controller_begin(&controller,&attempt,&receipt)&&submissions==2);
 progress_error=EAGAIN;assert(!wr_iot_close_controller_progress(&controller)&&progresses==1&&submissions==2);
 progress_error=0;assert(wr_iot_close_controller_progress(&controller));
 assert(wr_iot_close_controller_release(&controller)&&net_closes==1&&submissions==2);
 /* Any error after admission, including EBUSY, is normalized to EUCLEAN. */
 for(unsigned fault=0;fault<5;fault++){
  reset();memset(&controller,0,sizeof(controller));
  if(fault==0)after_close_error=-EBUSY;
  if(fault==1){adapter.users=1;fd_close_error=1;}
  if(fault==2)finish_ok=0;
  if(fault==3)positive_reply=1;
  if(fault==4)legacy_module=1;
  assert(!wr_iot_close_controller_begin(&controller,&attempt,&receipt));
  assert(controller.phase==WR_IOT_CLOSE_UNCERTAIN&&submissions==1);
  if(fault==4)assert(!enters&&!net_closes&&!finishes);
  unsigned closed=net_closes;adapter.users=0;fd_close_error=0;
  assert(!wr_iot_close_controller_begin(&controller,&attempt,&receipt)&&submissions==1&&net_closes==closed);
  progress_error=EAGAIN;assert(!wr_iot_close_controller_progress(&controller)&&submissions==1&&net_closes==closed);
 }
 puts("PASS actual kernel CLOSE/client/controller composition: pre-admission busy leaves IDLE then one admitted close; post-admission EBUSY, failed fd close, refused finish and positive reply remain uncertain without CLOSE replay; syscall/admission/netdev actors, no RF proof");
 return 0;
}
