#define _GNU_SOURCE
#include <time.h>
#include "config-edit-server.h"
#include "config-edit-lease.h"
#include "config-save-server.h"
#include "config-runtime-request.h"
#include "rc-backend.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
#include "native-flash-prepared.h"
#include "precreated-entropy.h"
#ifndef WR_IOT_EDIT_CLOCK
static unsigned long long edit_clock(void)
{
 struct timespec now;
 return clock_gettime(CLOCK_MONOTONIC,&now)||now.tv_sec<=0?0:(unsigned long long)now.tv_sec;
}
#define WR_IOT_EDIT_CLOCK edit_clock
#else
unsigned long long WR_IOT_EDIT_CLOCK(void);
#endif
#ifndef WR_IOT_EDIT_ENTROPY
#define WR_IOT_EDIT_ENTROPY wr_iot_precreated_entropy
#else
int WR_IOT_EDIT_ENTROPY(void *,unsigned char *,unsigned int);
#endif
static struct wr_iot_config_edit_lease lease;
static pid_t installed;
int wr_iot_rc_edit_backend_ready(void){return installed==getpid();}
static struct {
 pid_t owner;char id[33];unsigned long long created;
 enum wr_iot_operation target;int attempted,rejected,complete,owns_lease;
} transaction;
static int identity(const char *id,unsigned long long created)
{
 return installed==getpid()&&transaction.owner==getpid()&&id&&
  wr_iot_control_id(id)&&!strcmp(id,transaction.id)&&created==transaction.created;
}
int wr_iot_rc_edit_view(unsigned int lifetime,struct wr_iot_config_view *out,char revision[33])
{
 int token,ok=0;unsigned long long now;
 if(!out||!revision||!lifetime||lifetime>300||installed!=getpid()||wr_iot_rc_pending()||
    (transaction.owner&&!transaction.complete)||wr_iot_rc_shutdown.active||
    wr_iot_rc_shutdown.pending||wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned)return 0;
 now=WR_IOT_EDIT_CLOCK();if(!now)return 0;
 token=wr_iot_service_guard_enter(1);if(token!=1)return 0;
 if(lease.phase&&!wr_iot_config_edit_lease_release(&lease))goto done;
 ok=wr_iot_config_edit_lease_open(&lease,now,lifetime,WR_IOT_EDIT_ENTROPY,NULL,out,revision);
 done:wr_iot_service_guard_leave(token);return ok;
}
static enum wr_iot_result_state execute(const struct wr_iot_control_request *request)
{
 struct wr_iot_control_request converted={0};struct wr_iot_saved_config config={0};
 unsigned long long now;int token=0;enum wr_iot_result_state result=WR_IOT_RESULT_REJECTED;
 if(installed!=getpid()||!request||!wr_iot_operation_is_edit(request->operation)||
    !memchr(request->id,0,sizeof(request->id))||
    !wr_iot_config_edit_record_valid(&request->edit)||strcmp(request->id,request->edit.id)||
    request->created!=request->edit.created||
    request->operation!=WR_IOT_OPERATION_CONFIG_EDIT_RAM+request->edit.mode)return result;
 if(transaction.owner&&!transaction.complete)return WR_IOT_RESULT_RECOVERY;
 memset(&transaction,0,sizeof(transaction));transaction.owner=getpid();
 memcpy(transaction.id,request->id,sizeof(transaction.id));transaction.created=request->created;transaction.rejected=1;
 transaction.target=request->operation==WR_IOT_OPERATION_CONFIG_EDIT_RUNTIME?WR_IOT_OPERATION_RUNTIME:
  request->operation==WR_IOT_OPERATION_CONFIG_EDIT_RAM?WR_IOT_OPERATION_CONFIG:
  request->operation==WR_IOT_OPERATION_CONFIG_EDIT_AUTO?WR_IOT_OPERATION_CONFIG_SAVE_AUTO:WR_IOT_OPERATION_CONFIG_SAVE_EXPLICIT;
 if(wr_iot_rc_shutdown.active!=1||wr_iot_rc_shutdown.pending||
    wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned)goto done;
 token=wr_iot_service_guard_enter(1);if(token!=1)goto done;
 transaction.owns_lease=wr_iot_generation_config_owned(&lease.pin)&&!strcmp(lease.pin.id,request->edit.revision);
 now=WR_IOT_EDIT_CLOCK();if(!now)goto done;
 if(!wr_iot_config_edit_lease_claim(&lease,request->edit.revision,now,&request->edit.fields,request->edit.action,&config))goto done;
 memcpy(converted.id,request->id,sizeof(converted.id));converted.created=request->created;
 converted.operation=transaction.target;converted.request=config.profile;
 if(transaction.target==WR_IOT_OPERATION_RUNTIME&&
    (!lease.pin.present||!wr_iot_config_runtime_request(&converted.request,&config,lease.pin.record)))goto done;
 transaction.attempted=1;transaction.rejected=0;
 result=transaction.target==WR_IOT_OPERATION_RUNTIME?wr_iot_activation_execute(&converted):
  transaction.target==WR_IOT_OPERATION_CONFIG?wr_iot_rc_config_execute(&converted):wr_iot_rc_save_execute(&converted);
 done:if(token==1)wr_iot_service_guard_leave(token);
 wr_iot_saved_wipe(&config,sizeof(config));wr_iot_saved_wipe(&converted,sizeof(converted));return result;
}
static enum wr_iot_result_state progress(const char *id,unsigned long long created)
{
 if(!identity(id,created)||!transaction.attempted||transaction.complete)return WR_IOT_RESULT_RECOVERY;
 return transaction.target==WR_IOT_OPERATION_RUNTIME?wr_iot_activation_continue(id,created):
  transaction.target==WR_IOT_OPERATION_CONFIG?wr_iot_rc_config_continue(id,created):wr_iot_rc_save_continue(id,created);
}
static int terminal(const struct wr_iot_control_result *result)
{
 int ready;
 if(!result||!memchr(result->id,0,sizeof(result->id))||!identity(result->id,result->created))return 0;
 ready=transaction.rejected?result->state==WR_IOT_RESULT_REJECTED:
  transaction.target==WR_IOT_OPERATION_RUNTIME?(result->state==WR_IOT_RESULT_REJECTED||
   (result->state==WR_IOT_RESULT_APPLIED&&wr_iot_rc_backend_applied_route(result->id,result->created))):
  transaction.target==WR_IOT_OPERATION_CONFIG?wr_iot_rc_config_terminal_ready(result):wr_iot_rc_save_terminal_ready(result);
 if(!ready)return 0;
 if(transaction.owns_lease){
  if(!wr_iot_config_edit_lease_release(&lease))return 0;
  transaction.owns_lease=0;
 }
 transaction.complete=1;return 1;
}
int wr_iot_rc_edit_observed(const struct wr_iot_control_result *result)
{
 if(!result||!memchr(result->id,0,sizeof(result->id))||!identity(result->id,result->created)||
    !transaction.complete||transaction.rejected)return 0;
 return transaction.target==WR_IOT_OPERATION_RUNTIME?wr_iot_rc_backend_observed(result):
  transaction.target==WR_IOT_OPERATION_CONFIG?wr_iot_rc_config_observed(result):wr_iot_rc_save_observed(result);
}
int wr_iot_rc_edit_backend_install(void)
{
 const struct wr_iot_save_backend_hooks hooks={execute,progress,terminal};
 if(installed||WR_IOT_NATIVE_FLASH_READBACK_PREPARED!=1||WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED!=1||
    !wr_iot_rc_register_edit_backend(&hooks))return 0;
 installed=getpid();return 1;
}
