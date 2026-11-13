#define _GNU_SOURCE
#include "control-channel.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static struct {
 char id[33];unsigned long long created;pid_t owner;
 int active,busy,terminal;enum wr_iot_result_state outcome;
} wr_iot_continuation;
int wr_iot_rc_dispatch(void){
 struct wr_iot_mailbox m;struct wr_iot_control_request request={0};
 struct wr_iot_control_result previous;
 enum wr_iot_result_state outcome;unsigned long long now;int claimed,finished=0,pending,retain_shutdown=0;
 if(!wr_iot_rc_shutdown_begin())return 0;
 now=wr_iot_control_now();if(!now)goto done;
 wr_iot_mailbox_init(&m);
 if(!wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,0))goto done;
 claimed=wr_iot_mailbox_claim(&m,now,&request);
 if(!claimed){
  /* Retry only credential-file cleanup after an already terminal result.
   * Never replay a RUNNING or RECOVERY operation after interruption. */
  finished=wr_iot_mailbox_result(&m,&previous)&&
   (previous.state==WR_IOT_RESULT_APPLIED||previous.state==WR_IOT_RESULT_REJECTED)&&
   wr_iot_mailbox_finish(&m,previous.id,previous.state,now);
  wr_iot_mailbox_close(&m);goto done;
 }
 wr_iot_mailbox_close(&m);
 /* RUNNING is visible before execution and prevents replay/replacement even
  * when RC dies or its backend cannot finish recovery. Do not hold the queue
  * lock while taking the distinct activation/service guard. */
 outcome=wr_iot_activation_execute(&request);
 if(outcome!=WR_IOT_RESULT_APPLIED&&outcome!=WR_IOT_RESULT_REJECTED)
  outcome=WR_IOT_RESULT_RECOVERY;
 /* Recovery still owns resources/isolation after this request returns.
  * Do not replay a pending shutdown into the stock fatal path, which would
  * continue LAN teardown even if the Wi-Fi stop helper refuses. Only a
  * separately confirmed recovery owner may release this admission fence. */
 retain_shutdown=outcome==WR_IOT_RESULT_RECOVERY;
 if(retain_shutdown){
  memcpy(wr_iot_continuation.id,request.id,sizeof(request.id));
  wr_iot_continuation.created=request.created;
  wr_iot_continuation.owner=getpid();wr_iot_continuation.active=1;
 }

 now=wr_iot_control_now();
 if(!now||!wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,0)){
  memset(&request,0,sizeof(request));goto done;
 }
 finished=wr_iot_mailbox_finish(&m,request.id,outcome,now);
 wr_iot_mailbox_close(&m);memset(&request,0,sizeof(request));
done:
 /* Only terminal activation results may release this request's fence.
  * RECOVERY keeps both admission and the first pending shutdown signal;
  * result publication does not establish resource or RF retirement. */
 if(retain_shutdown)return finished;
 pending=wr_iot_rc_shutdown_end();
 if(pending)raise(pending);
 return finished;
}

int wr_iot_rc_continue(void){
 struct wr_iot_mailbox m;struct wr_iot_control_result current;
 enum wr_iot_result_state outcome;unsigned long long now;int finished,pending;
 if(!wr_iot_continuation.active||wr_iot_continuation.busy||
    wr_iot_continuation.owner!=getpid()||!wr_iot_rc_shutdown.active)return 0;
 now=wr_iot_control_now();if(!now)return 0;
 wr_iot_mailbox_init(&m);
 if(!wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,0))return 0;
 finished=wr_iot_mailbox_result(&m,&current)&&
  !strcmp(current.id,wr_iot_continuation.id)&&
  current.created==wr_iot_continuation.created&&
  (current.state==WR_IOT_RESULT_RUNNING||current.state==WR_IOT_RESULT_RECOVERY||
   (wr_iot_continuation.terminal&&current.state==wr_iot_continuation.outcome));
 wr_iot_mailbox_close(&m);if(!finished)return 0;
 wr_iot_continuation.busy=1;
 if(wr_iot_continuation.terminal)outcome=wr_iot_continuation.outcome;
 else {
  outcome=wr_iot_activation_continue(wr_iot_continuation.id,wr_iot_continuation.created);
  if(outcome!=WR_IOT_RESULT_APPLIED&&outcome!=WR_IOT_RESULT_REJECTED)
   outcome=WR_IOT_RESULT_RECOVERY;
  if(outcome!=WR_IOT_RESULT_RECOVERY){
   wr_iot_continuation.terminal=1;wr_iot_continuation.outcome=outcome;
  }
 }
 now=wr_iot_control_now();
 if(!now||!wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,0)){
  wr_iot_continuation.busy=0;return 0;
 }
 finished=wr_iot_mailbox_result(&m,&current)&&
  !strcmp(current.id,wr_iot_continuation.id)&&current.created==wr_iot_continuation.created&&
  (current.state==WR_IOT_RESULT_RUNNING||current.state==WR_IOT_RESULT_RECOVERY||
   (wr_iot_continuation.terminal&&current.state==wr_iot_continuation.outcome))&&
  wr_iot_mailbox_finish_continued(&m,wr_iot_continuation.id,
   wr_iot_continuation.created,wr_iot_continuation.owner,outcome,now);
 wr_iot_mailbox_close(&m);wr_iot_continuation.busy=0;
 if(!finished||!wr_iot_continuation.terminal)return finished;
 memset(&wr_iot_continuation,0,sizeof(wr_iot_continuation));
 pending=wr_iot_rc_shutdown_end();if(pending)raise(pending);
 return 1;
}

int wr_iot_rc_pending(void){
 return wr_iot_continuation.active&&wr_iot_continuation.owner==getpid()&&
  wr_iot_rc_shutdown.active;
}
