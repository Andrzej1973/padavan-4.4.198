#include <string.h>
#include <unistd.h>
#include "config-save-owner.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
#include "native-flash-prepared.h"
#include "config-snapshot-prepared.h"
static int identity(const struct wr_iot_config_save_owner *s,const char *id,unsigned long long created)
{
 return s&&s->owner==getpid()&&s->self==(uintptr_t)s&&!s->busy&&id&&wr_iot_control_id(id)&&
  memchr(s->id,0,sizeof(s->id))&&!strcmp(s->id,id)&&created==s->created&&created&&
  (s->mode==WR_IOT_FLASH_SAVE_AUTO||s->mode==WR_IOT_FLASH_SAVE_EXPLICIT);
}
static int fresh(struct wr_iot_config_save_owner *s,int backend)
{
 int token,ok=0;token=wr_iot_service_guard_enter(1);
 if(token==1)ok=(!backend||wr_iot_rc_config_backend_current(&s->baseline))&&
   wr_iot_config_owner_observed(&s->ram,s->id,s->created);
 if(token==1)wr_iot_service_guard_leave(token);
 return ok;
}
static int proof(const struct wr_iot_config_save_owner *s)
{
 return s->decision!=WR_IOT_CONFIG_SAVE_FLASH||
  (wr_iot_flash_worker_receipt_valid(&s->proof)&&s->proof.phase==WR_IOT_FLASH_SAVE_OBSERVED&&
   !strcmp(s->proof.id,s->id)&&s->proof.created==s->created&&s->proof.mode==(int)s->mode);
}
int wr_iot_config_save_begin_admitted(struct wr_iot_config_save_owner *s,const char *id,
 unsigned long long created,enum wr_iot_flash_save_mode mode,const struct wr_iot_saved_config *config)
{
 if(WR_IOT_NATIVE_FLASH_READBACK_PREPARED!=1||WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED!=1||
    !s||s->owner||s->self||s->busy||s->phase||s->decision||s->finished||s->ram.owner||s->worker.owner||
    !id||!wr_iot_control_id(id)||!created||(mode!=WR_IOT_FLASH_SAVE_AUTO&&mode!=WR_IOT_FLASH_SAVE_EXPLICIT)||
    !wr_iot_config_owner_begin_admitted(&s->ram,id,created,config))return 0;
 s->owner=getpid();s->self=(uintptr_t)s;memcpy(s->id,id,sizeof(s->id));s->created=created;s->mode=mode;
 s->baseline=s->ram.backend;s->phase=WR_IOT_CONFIG_SAVE_STORING;
 if(s->ram.phase==WR_IOT_CONFIG_REJECTED)s->phase=s->decision=WR_IOT_CONFIG_SAVE_REJECTED;
 return 1;
}
static void decide(struct wr_iot_config_save_owner *s)
{
 if(s->decision)return;
 switch(s->worker.phase){
 case WR_IOT_FLASH_WORKER_OBSERVED:
  s->proof=s->worker.receipt;s->decision=WR_IOT_CONFIG_SAVE_FLASH;break;
 case WR_IOT_FLASH_WORKER_MANUAL_PENDING:
  s->decision=WR_IOT_CONFIG_SAVE_RAM_ONLY;s->reason=WR_IOT_CONFIG_SAVE_MANUAL_POLICY;break;
 case WR_IOT_FLASH_WORKER_NOT_STORED:
  s->decision=WR_IOT_CONFIG_SAVE_RAM_ONLY;s->reason=WR_IOT_CONFIG_SAVE_NOT_SUBMITTED;break;
 case WR_IOT_FLASH_WORKER_NOT_STARTED:
  s->decision=WR_IOT_CONFIG_SAVE_RAM_ONLY;s->reason=WR_IOT_CONFIG_SAVE_NO_CHILD;break;
 default:break;
 }
}
enum wr_iot_config_save_phase wr_iot_config_save_step(struct wr_iot_config_save_owner *s,
 const char *id,unsigned long long created,int cancel)
{
 enum wr_iot_config_phase ram_phase;
 if(!identity(s,id,created)||wr_iot_rc_shutdown.active!=1)return WR_IOT_CONFIG_SAVE_RECOVERY;
 s->busy=1;
 if(s->finished){s->phase=fresh(s,1)&&proof(s)?s->decision:WR_IOT_CONFIG_SAVE_RECOVERY;goto done;}
 /* Drain already submitted work even if the backend has temporarily drifted. */
 if(s->worker.owner){wr_iot_flash_worker_step(&s->worker,id,created);decide(s);}
 if(s->ram.phase!=WR_IOT_CONFIG_RAM_READY&&s->ram.phase!=WR_IOT_CONFIG_REJECTED){
  ram_phase=wr_iot_config_owner_step(&s->ram,id,created,cancel);
  if(ram_phase==WR_IOT_CONFIG_REJECTED)s->decision=WR_IOT_CONFIG_SAVE_REJECTED;
  else if(ram_phase!=WR_IOT_CONFIG_RAM_READY)goto recovery;
 }
 if(!fresh(s,1))goto recovery;
 if(s->decision){s->phase=proof(s)?s->decision:WR_IOT_CONFIG_SAVE_RECOVERY;goto done;}
 if(s->worker.owner){
  s->phase=s->worker.phase==WR_IOT_FLASH_WORKER_RUNNING?WR_IOT_CONFIG_SAVE_SAVING:WR_IOT_CONFIG_SAVE_RECOVERY;
  goto done;
 }
 if(cancel||wr_iot_rc_shutdown.pending){
  s->phase=s->decision=WR_IOT_CONFIG_SAVE_RAM_ONLY;s->reason=WR_IOT_CONFIG_SAVE_CANCELLED;goto done;
 }
 if(wr_iot_flash_worker_begin(&s->worker,id,created,s->mode,s->ram.store.desired,strlen(s->ram.store.desired))){
  s->phase=WR_IOT_CONFIG_SAVE_SAVING;goto done;
 }
 decide(s);
 if(!s->worker.owner){s->decision=WR_IOT_CONFIG_SAVE_RAM_ONLY;s->reason=WR_IOT_CONFIG_SAVE_NO_CHILD;}
 if(s->decision){s->phase=s->decision;goto done;}
 recovery:s->phase=WR_IOT_CONFIG_SAVE_RECOVERY;
 done:s->busy=0;return s->phase;
}
int wr_iot_config_save_terminal_ready(struct wr_iot_config_save_owner *s,const char *id,unsigned long long created)
{
 int ok=0;
 if(!identity(s,id,created)||wr_iot_rc_shutdown.active!=1||!s->decision)return 0;
 s->busy=1;
 if(!fresh(s,1)||!proof(s)){s->phase=WR_IOT_CONFIG_SAVE_RECOVERY;goto done;}
 if(!s->finished){
  if(s->worker.owner&&!wr_iot_flash_worker_retire(&s->worker,id,created)){s->phase=WR_IOT_CONFIG_SAVE_RECOVERY;goto done;}
  if(!wr_iot_config_owner_finish(&s->ram,id,created)){s->phase=WR_IOT_CONFIG_SAVE_RECOVERY;goto done;}
  s->finished=1;
 }
 ok=fresh(s,1)&&proof(s);s->phase=ok?s->decision:WR_IOT_CONFIG_SAVE_RECOVERY;
 done:s->busy=0;return ok;
}
int wr_iot_config_save_observed(struct wr_iot_config_save_owner *s,const char *id,unsigned long long created)
{
 int ok;
 if(!identity(s,id,created)||!s->finished||!s->decision)return 0;
 s->busy=1;ok=fresh(s,0)&&proof(s);s->busy=0;return ok;
}
int wr_iot_config_save_retire(struct wr_iot_config_save_owner *s)
{
 if(!s||s->owner!=getpid()||s->self!=(uintptr_t)s||s->busy||!s->finished||s->worker.owner||
    !wr_iot_config_owner_retire(&s->ram))return 0;
 wr_iot_saved_wipe(s,sizeof(*s));return 1;
}
