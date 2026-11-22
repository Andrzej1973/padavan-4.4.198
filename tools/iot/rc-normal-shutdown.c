#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "rc-normal-shutdown.h"
#include "rc-shutdown-admission.h"
#include "rc-physical-stop.h"
#include "control-channel.h"
#include "precreated-entropy.h"
#include "radio-on-owner.h"
static struct {
 pid_t owner;
 struct wr_iot_control_request off;
 int generated,claimed,retained,spent;
} normal_shutdown;
static pid_t notification_owner;
/* INITIAL finish preflight, PID1 process context under active admission.
 * Notification ownership is preserved: an admitted batch drains before OFF.
 * The caller separately proves its exact ACTIVE backend and physical owner. */
static int normal_shutdown_consumer_available(void)
{
 return wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&
  !wr_iot_rc_shutdown.normal_route_requested&&!wr_iot_rc_shutdown.replay_signal&&
  !normal_shutdown.owner&&!normal_shutdown.generated&&!normal_shutdown.claimed&&
  !normal_shutdown.retained&&!normal_shutdown.spent;
}
int wr_iot_rc_normal_shutdown_arm_ready(void)
{
 return normal_shutdown_consumer_available()&&
  !wr_iot_rc_shutdown.radio_on_owned&&!wr_iot_rc_shutdown.radio_off_owned;
}
/* Private cold parent release only: caller separately proves its exact
 * ACTIVE parent/backend and outer fence. Retain the cold OFF exclusion until
 * cleanup transfers it to the ON follow-up owner. This grants no admission. */
int wr_iot_rc_normal_shutdown_cold_arm_ready(void)
{
 return normal_shutdown_consumer_available()&&
  wr_iot_rc_shutdown.radio_off_owned==1&&!wr_iot_rc_shutdown.radio_on_owned;
}
/* Only after successful readiness and exact ACTIVE finish preflight.
 * Signals may have become pending inside cleanup: publish anyway so fence
 * replay reaches the normal consumer, rather than falling through to stock.
 * Single process-context writer; no fallible work at this commit point. */
void wr_iot_rc_normal_shutdown_arm_commit(void)
{wr_iot_rc_shutdown.normal_route_armed=1;}
/* Cold released-root handoff only. No new transaction is admitted here;
 * exact backend/root and no-live-child proof belongs to the private caller. */
int wr_iot_rc_normal_shutdown_cold_handoff_ready(void)
{
 return !wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&
  wr_iot_rc_shutdown.normal_route_armed&&
  (wr_iot_rc_shutdown.normal_route_requested==SIGTERM
#ifdef SIGQUIT
   ||wr_iot_rc_shutdown.normal_route_requested==SIGQUIT
#endif
  )&&!wr_iot_rc_shutdown.replay_signal&&
  wr_iot_rc_shutdown.radio_on_owned==1&&!wr_iot_rc_shutdown.radio_off_owned&&
  !notification_owner&&!normal_shutdown.owner&&!normal_shutdown.generated&&
  !normal_shutdown.claimed&&!normal_shutdown.retained&&!normal_shutdown.spent;
}
static int normal_signal(int sig)
{
 return sig==SIGTERM
#ifdef SIGQUIT
  ||sig==SIGQUIT
#endif
 ;
}
static int requested(void)
{
 return wr_iot_rc_shutdown.normal_route_armed&&
  (wr_iot_rc_shutdown.normal_route_requested==SIGTERM
#ifdef SIGQUIT
   ||wr_iot_rc_shutdown.normal_route_requested==SIGQUIT
#endif
  );
}
int wr_iot_rc_normal_shutdown_pending(void)
{return wr_iot_rc_shutdown_replay_pending()||(!normal_shutdown.spent&&(normal_shutdown.owner==getpid()||requested()||
 (wr_iot_rc_shutdown.normal_route_armed&&normal_signal(wr_iot_rc_shutdown.pending))));}
/* Single PID1 process-context writer. The owner claim linearizes admission
 * before a later signal; no signal mask is inherited by asynchronous Wi-Fi
 * fences started in the notification handler. Signal context only records the
 * normal request, and cannot run the physical shutdown controller. */
int wr_iot_rc_normal_notification_begin(void)
{
 if(wr_iot_rc_shutdown.replay_signal)return 0;
 if(!wr_iot_rc_shutdown.normal_route_armed)return 1;
 if(notification_owner||requested()||normal_signal(wr_iot_rc_shutdown.pending))return 0;
 notification_owner=getpid();
 if(requested()||normal_signal(wr_iot_rc_shutdown.pending)){
  notification_owner=0;return 0;
 }
 return 1;
}
void wr_iot_rc_normal_notification_end(void)
{if(notification_owner==getpid())notification_owner=0;}
static void normal_shutdown_retire(void *context)
{
 (void)context;
 memset(&normal_shutdown,0,sizeof(normal_shutdown));normal_shutdown.spent=1;
}
int wr_iot_rc_normal_shutdown_step(void)
{
 unsigned char bytes[32]={0};unsigned i,nonzero=0;
 unsigned long long now;static const char hex[]="0123456789abcdef";
 if(wr_iot_rc_shutdown_replay_pending())return wr_iot_rc_shutdown_replay_step();
 if(notification_owner||!wr_iot_rc_normal_shutdown_pending()||!requested()||normal_shutdown.retained)return 0;
 if(normal_shutdown.owner&&normal_shutdown.owner!=getpid())return 0;
 if(!normal_shutdown.claimed){
  /* Existing owners must drain, not be replaced by this controller. */
  if(wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
     (wr_iot_rc_shutdown.radio_on_owned&&!wr_iot_radio_on_off_ready())||wr_iot_rc_shutdown.radio_off_owned)return 0;
  if(!normal_shutdown.generated){
   now=wr_iot_control_now();if(!now)return 0;
   if(wr_iot_precreated_entropy(NULL,bytes,sizeof(bytes))!=(int)sizeof(bytes))goto wipe;
   for(i=0;i<16;i++)nonzero|=bytes[i];
   if(!nonzero)goto wipe;
   for(i=0;i<16;i++){
    normal_shutdown.off.id[2*i]=hex[bytes[i]>>4];
    normal_shutdown.off.id[2*i+1]=hex[bytes[i]&15];
   }
   normal_shutdown.off.created=now;normal_shutdown.generated=1;
  }
  normal_shutdown.owner=getpid();
  if(wr_iot_rc_physical_begin_routed_shutdown(&normal_shutdown.off))normal_shutdown.claimed=1;
  goto wipe;
 }
 if(wr_iot_rc_physical_pending()){
  /* Even a preparation refusal must balance its existing fence first. */
  wr_iot_rc_physical_step();return 0;
 }
 if(wr_iot_rc_physical_off_failed(normal_shutdown.off.id,normal_shutdown.off.created)){
  normal_shutdown.retained=1;return 0;
 }
 return wr_iot_rc_physical_shutdown_release_cleanup(normal_shutdown.off.id,
  normal_shutdown.off.created,normal_shutdown_retire,NULL);
 wipe:{volatile unsigned char *p=bytes;for(i=0;i<sizeof(bytes);i++)p[i]=0;}
 return 0;
}

/* Existing ACTIVE terminal handoff, not permission to start new ON work. */
int wr_iot_rc_normal_shutdown_terminal_arm_ready(void)
{
 return wr_iot_rc_shutdown.active==1&&
  (!wr_iot_rc_shutdown.pending||wr_iot_rc_shutdown.pending==SIGTERM
#ifdef SIGQUIT
   ||wr_iot_rc_shutdown.pending==SIGQUIT
#endif
  )&&!wr_iot_rc_shutdown.normal_route_requested&&!wr_iot_rc_shutdown.replay_signal&&
  !wr_iot_rc_shutdown.radio_on_owned&&!wr_iot_rc_shutdown.radio_off_owned&&
  !normal_shutdown.owner&&!normal_shutdown.generated&&!normal_shutdown.claimed&&
  !normal_shutdown.retained&&!normal_shutdown.spent;
}
