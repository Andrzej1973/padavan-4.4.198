#include <string.h>
#include <unistd.h>
#include "config-owner.h"
#include "control-record.h"
#include "rc-shutdown-admission.h"
#include "service-guard.h"

static int identity(const struct wr_iot_config_owner *owner,const char *id,unsigned long long created)
{
 return owner&&owner->owner==getpid()&&owner->self==(uintptr_t)owner&&created&&
  memchr(owner->id,0,sizeof(owner->id))&&id&&wr_iot_control_id(id)&&
  owner->created==created&&!strcmp(owner->id,id);
}
static int held(const struct wr_iot_config_owner *owner)
{
 int fd;
 if(!owner->admitted||owner->token!=1||wr_iot_rc_shutdown.active!=1||
    wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned)return 0;
 fd=wr_iot_service_guard_dup();return fd>=0&&close(fd)==0;
}
static int begin(struct wr_iot_config_owner *owner,const char *id,
 unsigned long long created,const struct wr_iot_saved_config *config,int admitted)
{
 int token,pending;struct wr_iot_config_backend baseline={0};
 if(!owner||owner->owner||owner->self||owner->token||owner->admitted||owner->phase||
    owner->busy||owner->owns_admission||owner->store.owner||owner->store.self||owner->store.token||owner->store.phase||
    !id||!wr_iot_control_id(id)||!created||!config||
    wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned||
    (admitted?wr_iot_rc_shutdown.active!=1:!wr_iot_rc_shutdown_begin()))return 0;
 token=wr_iot_service_guard_enter(1);
 if(token!=1||!wr_iot_rc_config_backend_capture(&baseline)){
  if(token==1)wr_iot_service_guard_leave(token);
  pending=admitted?0:wr_iot_rc_shutdown_end();
  if(pending)raise(pending);
  return 0;
 }
 /* Initialize at the final address: the nested journal binds its own address
  * and must never be copied from a temporary owner. */
 owner->owner=getpid();owner->self=(uintptr_t)owner;owner->token=token;owner->admitted=1;
 owner->owns_admission=!admitted;
 memcpy(owner->id,id,sizeof(owner->id));owner->created=created;owner->backend=baseline;
 owner->phase=WR_IOT_CONFIG_REJECTED;
 if(wr_iot_saved_store_begin(&owner->store,id,created,config))owner->phase=WR_IOT_CONFIG_WRITING;
 return 1;
}
int wr_iot_config_owner_begin(struct wr_iot_config_owner *owner,const char *id,
 unsigned long long created,const struct wr_iot_saved_config *config)
{return begin(owner,id,created,config,0);}
int wr_iot_config_owner_begin_admitted(struct wr_iot_config_owner *owner,const char *id,
 unsigned long long created,const struct wr_iot_saved_config *config)
{return begin(owner,id,created,config,1);}
enum wr_iot_config_phase wr_iot_config_owner_step(struct wr_iot_config_owner *owner,
 const char *id,unsigned long long created,int cancel)
{
 enum wr_iot_saved_store_phase phase;
 if(!identity(owner,id,created)||owner->busy||!held(owner))return WR_IOT_CONFIG_RECOVERY;
 owner->busy=1;
 if(!wr_iot_rc_config_backend_current(&owner->backend))goto recovery;
 if(owner->phase==WR_IOT_CONFIG_REJECTED)goto done;
 if((cancel||wr_iot_rc_shutdown.pending)&&wr_iot_saved_store_cancel(&owner->store)){
  owner->phase=WR_IOT_CONFIG_REJECTED;goto done;
 }
 if((cancel||wr_iot_rc_shutdown.pending)&&!owner->store.attempted)goto recovery;
 phase=wr_iot_saved_store_step(&owner->store);
 if(phase==WR_IOT_SAVED_NO_SPACE&&wr_iot_saved_store_cancel(&owner->store)){
  owner->phase=WR_IOT_CONFIG_REJECTED;goto done;
 }
 if(phase!=WR_IOT_SAVED_RAM_READY)goto recovery;
 if(!wr_iot_rc_config_backend_current(&owner->backend))goto recovery;
 owner->phase=WR_IOT_CONFIG_RAM_READY;goto done;
 recovery:owner->phase=WR_IOT_CONFIG_RECOVERY;
 done:owner->busy=0;return owner->phase;
}
int wr_iot_config_owner_observed(struct wr_iot_config_owner *owner,const char *id,
 unsigned long long created)
{
 int token,ok=0;
 if(!identity(owner,id,created)||owner->busy)return 0;
 if(owner->phase==WR_IOT_CONFIG_REJECTED)return !owner->admitted||
  (held(owner)&&wr_iot_rc_config_backend_current(&owner->backend));
 if(owner->phase!=WR_IOT_CONFIG_RAM_READY&&owner->phase!=WR_IOT_CONFIG_RAM_COMMITTED)return 0;
 owner->busy=1;
 token=wr_iot_service_guard_enter(1);
 if(token==1){
  if(owner->phase==WR_IOT_CONFIG_RAM_READY)
   ok=held(owner)&&wr_iot_rc_config_backend_current(&owner->backend)&&
      wr_iot_saved_record_current(owner->store.desired);
  else ok=!owner->admitted&&wr_iot_saved_record_current(owner->expected);
 }
 if(token==1)wr_iot_service_guard_leave(token);
 owner->busy=0;return ok;
}
int wr_iot_config_owner_finish(struct wr_iot_config_owner *owner,const char *id,
 unsigned long long created)
{
 int token,pending,owns_admission;
 if(!identity(owner,id,created)||owner->busy||!held(owner))return 0;
 owner->busy=1;
 if(!wr_iot_rc_config_backend_current(&owner->backend))goto done;
 if(owner->phase==WR_IOT_CONFIG_RAM_READY){
  memcpy(owner->expected,owner->store.desired,sizeof(owner->expected));
  if(!wr_iot_saved_store_finish(&owner->store)){
   wr_iot_saved_wipe(owner->expected,sizeof(owner->expected));goto done;
  }
  owner->phase=WR_IOT_CONFIG_RAM_COMMITTED;
 }else if(owner->phase!=WR_IOT_CONFIG_REJECTED||owner->store.owner)goto done;
 token=owner->token;owns_admission=owner->owns_admission;
 owner->token=0;owner->admitted=0;owner->owns_admission=0;
 wr_iot_saved_wipe(&owner->backend,sizeof(owner->backend));
 owner->busy=0;wr_iot_service_guard_leave(token);
 pending=owns_admission?wr_iot_rc_shutdown_end():0;
 if(pending)raise(pending);
 return 1;
 done:owner->busy=0;return 0;
}
int wr_iot_config_owner_retire(struct wr_iot_config_owner *owner)
{
 if(!owner||owner->owner!=getpid()||owner->self!=(uintptr_t)owner||owner->busy||
    owner->admitted||owner->owns_admission||owner->token||owner->store.owner||owner->store.self||
    owner->store.token||owner->store.phase||
    (owner->phase!=WR_IOT_CONFIG_RAM_COMMITTED&&owner->phase!=WR_IOT_CONFIG_REJECTED))return 0;
 wr_iot_saved_wipe(owner,sizeof(*owner));return 1;
}
