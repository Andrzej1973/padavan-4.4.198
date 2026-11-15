#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "rc-normal-shutdown.h"
#include "rc-shutdown-admission.h"
#include "rc-physical-stop.h"
#include "control-channel.h"
#include "precreated-entropy.h"
static struct {
 pid_t owner;
 struct wr_iot_control_request off;
 int generated,claimed,retained,spent;
} normal_shutdown;
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
{return !normal_shutdown.spent&&(normal_shutdown.owner==getpid()||requested());}
static void normal_shutdown_retire(void *context)
{
 (void)context;
 memset(&normal_shutdown,0,sizeof(normal_shutdown));normal_shutdown.spent=1;
}
int wr_iot_rc_normal_shutdown_step(void)
{
 unsigned char bytes[32]={0};unsigned i,nonzero=0;
 unsigned long long now;static const char hex[]="0123456789abcdef";
 if(!wr_iot_rc_normal_shutdown_pending()||!requested()||normal_shutdown.retained)return 0;
 if(normal_shutdown.owner&&normal_shutdown.owner!=getpid())return 0;
 if(!normal_shutdown.claimed){
  /* Existing owners must drain, not be replaced by this controller. */
  if(wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
     wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned)return 0;
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
