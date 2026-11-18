#define _GNU_SOURCE
#include "control-channel.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static struct {
 char id[33];unsigned long long created;pid_t owner;
 int active,busy,terminal;enum wr_iot_result_state outcome;
 enum wr_iot_operation operation;
} wr_iot_continuation;
static struct wr_iot_save_backend_hooks save_hooks;
static pid_t save_hooks_owner;
static struct wr_iot_save_backend_hooks edit_hooks;
static pid_t edit_hooks_owner;
int wr_iot_rc_register_edit_backend(const struct wr_iot_save_backend_hooks *hooks)
{
 if(!hooks||!hooks->execute||!hooks->progress||!hooks->terminal||edit_hooks_owner||
    wr_iot_continuation.active||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned)return 0;
 edit_hooks=*hooks;edit_hooks_owner=getpid();return 1;
}
static int edit_bound(void)
{return edit_hooks_owner==getpid()&&edit_hooks.execute&&edit_hooks.progress&&edit_hooks.terminal;}
int wr_iot_rc_register_save_backend(const struct wr_iot_save_backend_hooks *hooks)
{
 if(!hooks||!hooks->execute||!hooks->progress||!hooks->terminal||save_hooks_owner||
    wr_iot_continuation.active||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned)return 0;
 save_hooks=*hooks;save_hooks_owner=getpid();return 1;
}
static int save_bound(void)
{return save_hooks_owner==getpid()&&save_hooks.execute&&save_hooks.progress&&save_hooks.terminal;}
static int wr_iot_terminal_ready(enum wr_iot_operation operation,
 enum wr_iot_result_state outcome,const char *id,unsigned long long created)
{
 struct wr_iot_control_result result={0};
 if(wr_iot_operation_is_edit(operation)){
  if(!edit_bound())return outcome==WR_IOT_RESULT_REJECTED;
  memcpy(result.id,id,sizeof(result.id));result.created=created;result.state=outcome;
  return edit_hooks.terminal(&result);
 }
 if(operation==WR_IOT_OPERATION_RUNTIME)
  return outcome!=WR_IOT_RESULT_APPLIED||wr_iot_rc_backend_applied_route(id,created);
 if(wr_iot_operation_is_save(operation)){
  if(!save_bound())return outcome==WR_IOT_RESULT_REJECTED;
  memcpy(result.id,id,sizeof(result.id));result.created=created;result.state=outcome;
  return save_hooks.terminal(&result);
 }
 if(operation!=WR_IOT_OPERATION_CONFIG)return 0;
 memcpy(result.id,id,sizeof(result.id));result.created=created;result.state=outcome;
 return wr_iot_rc_config_terminal_ready(&result);
}
static enum wr_iot_result_state wr_iot_operation_outcome(enum wr_iot_operation operation,
 enum wr_iot_result_state outcome)
{
 if(outcome==WR_IOT_RESULT_REJECTED||
    ((operation==WR_IOT_OPERATION_RUNTIME||operation==WR_IOT_OPERATION_CONFIG_EDIT_RUNTIME)&&outcome==WR_IOT_RESULT_APPLIED)||
    (operation==WR_IOT_OPERATION_CONFIG&&outcome==WR_IOT_RESULT_STORED_RAM)||
    (wr_iot_operation_is_edit_config(operation)&&(outcome==WR_IOT_RESULT_STORED_RAM||
     (operation!=WR_IOT_OPERATION_CONFIG_EDIT_RAM&&outcome==WR_IOT_RESULT_SAVED_FLASH)))||
    (wr_iot_operation_is_save(operation)&&(outcome==WR_IOT_RESULT_STORED_RAM||outcome==WR_IOT_RESULT_SAVED_FLASH)))return outcome;
 return WR_IOT_RESULT_RECOVERY;
}
int wr_iot_rc_dispatch(void){
 struct wr_iot_mailbox m;struct wr_iot_control_request request={0};
 struct wr_iot_control_result previous;
 enum wr_iot_result_state outcome;unsigned long long now;int claimed,finished=0,pending,retain_shutdown=0,terminal_ready=0;
 if(wr_iot_rc_shutdown.radio_off_owned||wr_iot_rc_shutdown.radio_on_owned||!wr_iot_rc_shutdown_begin())return 0;
 now=wr_iot_control_now();if(!now)goto done;
 wr_iot_mailbox_init(&m);
 if(!wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,0))goto done;
 claimed=wr_iot_mailbox_claim(&m,now,&request);
 if(!claimed){
  /* Retry only credential-file cleanup after an already terminal result.
   * Never replay a RUNNING or RECOVERY operation after interruption. */
  finished=wr_iot_mailbox_result(&m,&previous)&&
   (previous.state==WR_IOT_RESULT_APPLIED||previous.state==WR_IOT_RESULT_REJECTED||
    previous.state==WR_IOT_RESULT_STORED_RAM||previous.state==WR_IOT_RESULT_SAVED_FLASH)&&
   wr_iot_mailbox_finish(&m,previous.id,previous.state,now);
  wr_iot_mailbox_close(&m);goto done;
 }
 wr_iot_mailbox_close(&m);
 /* RUNNING is visible before execution and prevents replay/replacement even
  * when RC dies or its backend cannot finish recovery. Do not hold the queue
  * lock while taking the distinct activation/service guard. */
 outcome=request.operation==WR_IOT_OPERATION_CONFIG?wr_iot_rc_config_execute(&request):
  request.operation==WR_IOT_OPERATION_RUNTIME?wr_iot_activation_execute(&request):
  wr_iot_operation_is_edit(request.operation)&&edit_bound()?edit_hooks.execute(&request):
  wr_iot_operation_is_save(request.operation)&&save_bound()?save_hooks.execute(&request):WR_IOT_RESULT_REJECTED;
 outcome=wr_iot_operation_outcome(request.operation,outcome);
 /* Recovery still owns resources/isolation after this request returns.
  * Do not replay a pending shutdown into the stock fatal path, which would
  * continue LAN teardown even if the Wi-Fi stop helper refuses. Only a
  * separately confirmed recovery owner may release this admission fence. */
 /* Even an immediate terminal result must survive failed publication.
  * Retain only nonsecret identity/outcome; retry publication, never execute. */
 retain_shutdown=1;
 memcpy(wr_iot_continuation.id,request.id,sizeof(request.id));
 wr_iot_continuation.created=request.created;
 wr_iot_continuation.owner=getpid();wr_iot_continuation.active=1;
 wr_iot_continuation.terminal=outcome!=WR_IOT_RESULT_RECOVERY;
 wr_iot_continuation.outcome=outcome;
 wr_iot_continuation.operation=request.operation;
 terminal_ready=wr_iot_continuation.terminal&&
  wr_iot_terminal_ready(request.operation,outcome,request.id,request.created);
 if(wr_iot_continuation.terminal&&!terminal_ready)outcome=WR_IOT_RESULT_RECOVERY;

 now=wr_iot_control_now();
 if(!now||!wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,0)){
  memset(&request,0,sizeof(request));goto done;
 }
 finished=wr_iot_mailbox_finish(&m,request.id,outcome,now);
 wr_iot_mailbox_close(&m);memset(&request,0,sizeof(request));
 if(finished&&terminal_ready){
  memset(&wr_iot_continuation,0,sizeof(wr_iot_continuation));retain_shutdown=0;
 }
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
 enum wr_iot_result_state outcome;unsigned long long now;int finished,pending,terminal_ready;
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
  outcome=wr_iot_continuation.operation==WR_IOT_OPERATION_CONFIG?
   wr_iot_rc_config_continue(wr_iot_continuation.id,wr_iot_continuation.created):
   wr_iot_continuation.operation==WR_IOT_OPERATION_RUNTIME?
    wr_iot_activation_continue(wr_iot_continuation.id,wr_iot_continuation.created):
    wr_iot_operation_is_edit(wr_iot_continuation.operation)&&edit_bound()?
    edit_hooks.progress(wr_iot_continuation.id,wr_iot_continuation.created):
    wr_iot_operation_is_save(wr_iot_continuation.operation)&&save_bound()?
    save_hooks.progress(wr_iot_continuation.id,wr_iot_continuation.created):WR_IOT_RESULT_RECOVERY;
  outcome=wr_iot_operation_outcome(wr_iot_continuation.operation,outcome);
  if(outcome!=WR_IOT_RESULT_RECOVERY){
   wr_iot_continuation.terminal=1;wr_iot_continuation.outcome=outcome;
  }
 }
 terminal_ready=wr_iot_continuation.terminal&&
  wr_iot_terminal_ready(wr_iot_continuation.operation,outcome,wr_iot_continuation.id,wr_iot_continuation.created);
 if(wr_iot_continuation.terminal&&!terminal_ready)outcome=WR_IOT_RESULT_RECOVERY;
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
 if(!finished||!terminal_ready)return finished;
 memset(&wr_iot_continuation,0,sizeof(wr_iot_continuation));
 pending=wr_iot_rc_shutdown_end();if(pending)raise(pending);
 return 1;
}

int wr_iot_rc_pending(void){
 return wr_iot_continuation.active&&wr_iot_continuation.owner==getpid()&&
  wr_iot_rc_shutdown.active;
}
