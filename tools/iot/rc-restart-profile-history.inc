/* Private backend completion preflight. Cancellation never calls commit. */
#include "restart-profile-history.h"
static int restart_history_file(struct wr_iot_restart_restore *s,
 struct wr_iot_restart_profile_receipt *out)
{
 struct wr_iot_radio_profile_state *p=&s->generation.profile;
 struct wr_iot_restart_profile_receipt r={0};size_t n;
 if(!wr_iot_radio_profile_owned(p)||p->files.count!=1||p->files.pending||
    p->recovering||p->removing||!memchr(p->files.paths[0],0,sizeof(p->files.paths[0])))return 0;
 n=strlen(p->files.paths[0]);if(!n||n>=sizeof(r.path))return 0;
 memcpy(r.path,p->files.paths[0],n+1);r.file=p->files.generated[0];r.owner=getpid();r.valid=1;
 if(r.file.existed!=1||r.file.metadata.st_size<=0||!wr_iot_restart_profile_receipt_current(&r))return 0;
 *out=r;return 1;
}
int wr_iot_rc_restart_profile_prepare(struct wr_iot_restart_restore *s,
 struct wr_iot_restart_profile_history *out)
{
 static const char hex[]="0123456789abcdef";
 struct wr_iot_restart_profile_history candidate={0};struct wr_iot_control_request request={0};
 struct wr_iot_profile_binding after={0};unsigned i;
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!s||s->owner!=getpid()||s->busy||!wr_iot_rc_shutdown.active||
    wr_iot_rc_shutdown.pending||!wr_iot_restart_restore_finish_check(s)||
    !restart_history_file(s,&candidate.profile))return 0;
 if(s->generation.origin.desired.enabled){
  for(i=0;i<16;i++){candidate.binding.id[2*i]=hex[s->open_id[i]>>4];candidate.binding.id[2*i+1]=hex[s->open_id[i]&15];}
  candidate.binding.created=s->handoff_created;candidate.binding.identity=s->main.identity;
  candidate.binding.kind=s->generation.origin.origin==WR_PHYSICAL_ORIGIN_INITIAL?
   WR_PROFILE_BACKEND_ACTIVE:WR_PROFILE_BACKEND_REBIND_ACTIVE;
  /* INITIAL still retains its parent until successful cleanup. Observe through
   * its exact existing parent proof rather than generic post-detach routing. */
  if(candidate.binding.kind==WR_PROFILE_BACKEND_ACTIVE){
   if(!wr_iot_restart_initial_active_current(s)||wr_iot_initial_restart_parent!=s||
      backend.owner!=getpid()||backend.busy||backend.phase!=WR_IOT_OWNER_ACTIVE||
      strcmp(candidate.binding.id,backend.start.input.id)||
      candidate.binding.created!=backend.start.input.created||
      candidate.binding.identity.adapter_epoch!=backend.start.open.attempt.identity.adapter_epoch||
      candidate.binding.identity.device_generation!=backend.start.open.attempt.identity.device_generation)return 0;
  }else if(!profile_history_backend(&after)||!profile_history_equal(&candidate.binding,&after))return 0;
 }else{
  /* Distinct INITIAL disabled completion: fresh new-Main never-opened proof.
   * No ACTIVE context or old CLOSE is synthesized. */
  if(s->generation.origin.origin!=WR_PHYSICAL_ORIGIN_INITIAL||rebind.owner||backend.busy||
     wr_iot_initial_restart_parent||wr_iot_cold_backend_parent||
     backend.start.owner||backend.stop.owner||backend.start.admission.snapshot.active||
     backend.start.admission.snapshot.token||
     !((!backend.owner&&backend.phase==WR_IOT_OWNER_IDLE)||
       (backend.owner==getpid()&&backend.phase==WR_IOT_OWNER_INITIAL_OFF)))return 0;
  for(i=0;i<16;i++){request.id[2*i]=hex[s->open_id[i]>>4];request.id[2*i+1]=hex[s->open_id[i]&15];}
  request.created=physical_initial.created;
  if(!request.created||!wr_iot_initial_off_begin(&candidate.idle,&request)||
     candidate.idle.idle.epoch!=s->main.identity.adapter_epoch||
     candidate.idle.idle.generation!=s->main.identity.device_generation||
     !wr_iot_initial_off_observed(&candidate.idle))return 0;
  candidate.binding.kind=WR_PROFILE_BACKEND_INITIAL_OFF;
  memcpy(candidate.binding.id,candidate.idle.id,sizeof(candidate.binding.id));
  candidate.binding.created=candidate.idle.created;candidate.binding.identity=s->main.identity;
 }
 if(!profile_history_equal(&candidate.binding,&candidate.binding)||
    !wr_iot_restart_restore_finish_check(s)||!wr_iot_restart_profile_receipt_current(&candidate.profile)||
    wr_iot_rc_shutdown.pending)return 0;
 *out=candidate;return 1;
}
void wr_iot_rc_restart_profile_commit(const struct wr_iot_restart_profile_history *s)
{
 if(s->binding.kind==WR_PROFILE_BACKEND_INITIAL_OFF){
  backend.initial_off=s->idle;backend.owner=getpid();backend.phase=WR_IOT_OWNER_INITIAL_OFF;
 }
 profile_history_commit(&s->binding,&s->profile);
}

int wr_iot_rc_restart_profile_current(const struct wr_iot_restart_restore *s)
{
 static const char hex[]="0123456789abcdef";char id[33]={0};unsigned i;
 struct wr_iot_profile_binding binding={0};struct wr_iot_restart_profile_receipt file={0};
 if(!s||s->owner!=getpid()||s->busy||s->phase!=WR_RESTORE_FINISHED||
    s->main.identity.adapter_epoch!=s->completion.binding.identity.adapter_epoch||
    s->main.identity.device_generation!=s->completion.binding.identity.device_generation||
    (s->generation.origin.origin==WR_PHYSICAL_ORIGIN_CLOSE?
      s->completion.binding.kind!=WR_PROFILE_BACKEND_REBIND_ACTIVE:
      (s->generation.origin.origin!=WR_PHYSICAL_ORIGIN_INITIAL||
       (s->completion.binding.kind!=WR_PROFILE_BACKEND_ACTIVE&&s->completion.binding.kind!=WR_PROFILE_BACKEND_INITIAL_OFF)))||
    (s->completion.binding.kind!=WR_PROFILE_BACKEND_INITIAL_OFF&&s->handoff_created!=s->completion.binding.created))return 0;
 for(i=0;i<16;i++){id[2*i]=hex[s->open_id[i]>>4];id[2*i+1]=hex[s->open_id[i]&15];}
 return memchr(s->completion.binding.id,0,sizeof(s->completion.binding.id))&&
  !strcmp(id,s->completion.binding.id)&&
  wr_iot_restart_profile_receipt_current(&s->completion.profile)&&
  wr_iot_rc_profile_history_read(&binding,&file)&&
  profile_history_equal(&binding,&s->completion.binding)&&
  !strcmp(file.path,s->completion.profile.path)&&
  wr_iot_restart_profile_receipt_current(&s->completion.profile);
}
