#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "rc-physical-stop.h"
#include "rc-backend.h"
#include "physical-stop-session.h"
#include "radio-stop-fence.h"
#include "rc-shutdown-admission.h"
#include "service-guard.h"
#include "precreated-entropy.h"
static struct {
 pid_t owner;
 struct wr_iot_rc_physical_intent intent;
 struct wr_iot_physical_session session;
 struct wr_iot_radio_stop_fence fence;
 unsigned int aux_next;
 unsigned char nonce[16];
 int guard,finishing,result;
} physical;
int wr_iot_rc_physical_begin(const struct wr_iot_rc_physical_intent *intent)
{
 struct wr_iot_driver_closed_result closed={0};
 struct wr_iot_physical_stop_request request={0};unsigned char entropy[32];
 if(!intent||intent->restart>1||intent->radio_on>1||intent->reload>1||
    (!intent->restart&&(intent->radio_on||intent->reload))||physical.owner||
    wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 if(!wr_iot_radio_stop_fence_begin(&physical.fence))return 0;
 physical.owner=getpid();physical.intent=*intent;
 physical.guard=wr_iot_service_guard_enter(1);
 if(physical.guard!=1)goto refuse;
 if(!wr_iot_rc_backend_closed(&closed)||
    wr_iot_precreated_entropy(NULL,entropy,sizeof(entropy))!=(int)sizeof(entropy))goto refuse;
 request.action=WR_STOP_ARM;request.epoch=closed.adapter_epoch;
 request.generation=closed.device_generation;request.open_token=closed.open_token;
 request.closed_serial=closed.close_serial;memcpy(request.nonce,entropy,16);
 if(!wr_iot_physical_stop_request_valid(&request))goto refuse;
 memcpy(physical.nonce,request.nonce,sizeof(physical.nonce));
 return 1;
 refuse:physical.finishing=-1;return 1;
}
int wr_iot_rc_physical_pending(void)
{return physical.owner==getpid()&&!physical.result;}
void wr_iot_rc_physical_step(void)
{
 struct wr_iot_driver_closed_result closed={0};
 struct wr_iot_physical_stop_request request={0};
 int guard,result=0;
 if(!wr_iot_rc_physical_pending())return;
 if(!physical.finishing){
  /* Revalidate the retained lock, balancing only this nested guard. Missing
   * admission retains ownership instead of progressing driver operations. */
  if(!wr_iot_rc_shutdown.active||physical.guard!=1)return;
  guard=wr_iot_service_guard_enter(1);if(guard!=1)return;
  if(physical.session.phase==WR_PHYSICAL_SESSION_IDLE){
   if(physical.aux_next<6){
    if(wr_iot_rc_physical_aux_down(physical.aux_next)==1)physical.aux_next++;
   }else if(wr_iot_rc_backend_closed(&closed)){
    /* AUX closure can change driver state. Capture the actual current CLOSE
     * again after all six administrative downs, before creating the ARM. */
    request.action=WR_STOP_ARM;request.epoch=closed.adapter_epoch;
    request.generation=closed.device_generation;request.open_token=closed.open_token;
    request.closed_serial=closed.close_serial;memcpy(request.nonce,physical.nonce,16);
    (void)wr_iot_physical_session_begin(&physical.session,&request);
   }
  }else result=wr_iot_physical_session_advance(&physical.session);
  wr_iot_service_guard_leave(guard);
  if(!result)return;
  physical.finishing=result;
 }
 if(physical.guard==1){wr_iot_service_guard_leave(1);physical.guard=0;}
 /* Clear guards before restoring signals; a pending normal shutdown can run
  * only after exact terminal cleanup. Failed mask restoration retains fence. */
 if(!wr_iot_radio_stop_fence_end(&physical.fence))return;
 physical.result=physical.finishing;
}
int wr_iot_rc_physical_take(struct wr_iot_rc_physical_intent *intent)
{
 int result;
 if(!intent||physical.owner!=getpid()||!physical.result)return 0;
 *intent=physical.intent;result=physical.result;
 memset(&physical,0,sizeof(physical));return result;
}
