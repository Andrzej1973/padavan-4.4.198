#include <string.h>
#include <unistd.h>
#include "start-runner.h"
#include "reopen-start.h"
#include "reopen-network.h"
#include "reopen-rollback.h"
#include "rc-shutdown-admission.h"
#include "service-guard.h"
#include "dns-activation.h"
static const char *runner_read(void *context,const char *key)
{
 const struct wr_iot_request *r=context;
 if(!strcmp(key,"wr_iot_enable"))return r->enabled==1?"1":"0";
#define FIELD(k,f) if(!strcmp(key,k))return r->f;
 FIELD("wr_iot_ssid",ssid) FIELD("wr_iot_psk",password)
 FIELD("wr_iot_gateway",gateway) FIELD("wr_iot_mask",mask)
 FIELD("wr_iot_start",first) FIELD("wr_iot_end",last)
#undef FIELD
 return NULL;
}
static int runner_begin(struct wr_iot_start_runner *s,
 const struct wr_iot_control_request *input,int router,int radio,int mode,
 const struct wr_iot_reopen_witness *previous)
{
 struct wr_iot_request checked;unsigned i;
 if(!s||!input||s->owner||s->phase!=WR_IOT_RUN_IDLE||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    !memchr(input->id,0,sizeof(input->id))||!wr_iot_control_id(input->id)||
    !input->created||input->request.enabled!=1)return 0;
#define BOUNDED(f) if(!memchr(input->request.f,0,sizeof(input->request.f)))return 0;
 BOUNDED(ssid) BOUNDED(password) BOUNDED(gateway) BOUNDED(mask) BOUNDED(first) BOUNDED(last)
#undef BOUNDED
 if(!wr_iot_request_read(&checked,runner_read,(void *)&input->request,router,radio,mode,NULL,0))return 0;
 s->owner=getpid();s->input=*input;s->input.request=checked;
 for(i=0;i<16;i++){
  unsigned char a=input->id[2*i],b=input->id[2*i+1];
  s->nonce[i]=(unsigned char)(((a<='9'?a-'0':a-'a'+10)<<4)|(b<='9'?b-'0':b-'a'+10));
 }
 if(previous)s->prior_closed=*previous;
 if(!(previous?wr_iot_reopen_start_begin(&s->admission,&s->prior_closed):
              wr_iot_start_admission_begin(&s->admission,s->nonce))){
  s->phase=s->admission.snapshot.active?WR_IOT_RUN_UNCERTAIN:WR_IOT_RUN_REJECTED;
  return 0;
 }
 s->phase=WR_IOT_RUN_STAGE;return 1;
}
int wr_iot_start_runner_begin(struct wr_iot_start_runner *s,
 const struct wr_iot_control_request *r,int router,int radio,int mode)
{return runner_begin(s,r,router,radio,mode,NULL);}
int wr_iot_start_runner_begin_reopen(struct wr_iot_start_runner *s,
 const struct wr_iot_control_request *r,int router,int radio,int mode,
 const struct wr_iot_reopen_witness *w)
{
 if(!w||w->owner!=getpid()||!w->valid||w->submitted)return 0;
 return runner_begin(s,r,router,radio,mode,w);
}
static void runner_recover(struct wr_iot_start_runner *s)
{
 s->network.phase=WR_IOT_NET_RECOVERY;
 if(s->open.phase==WR_IOT_OPEN_IDLE||s->open.phase==WR_IOT_OPEN_NOT_SUBMITTED)
  s->phase=WR_IOT_RUN_PRE_ROLLBACK;
 else if(s->open.phase==WR_IOT_OPEN_CONFIRMED||s->open.phase==WR_IOT_OPEN_RECOVERY)
  s->phase=WR_IOT_RUN_CLOSE;
 else s->phase=WR_IOT_RUN_UNCERTAIN;
}
static enum wr_iot_result_state runner_step(struct wr_iot_start_runner *s)
{
 if(!s||s->owner!=getpid())return WR_IOT_RESULT_RECOVERY;
 switch(s->phase){
 case WR_IOT_RUN_STAGE:
  if(s->prior_closed.valid?wr_iot_reopen_start_stage(&s->admission,&s->prior_closed,runner_read,&s->input.request,1,1,0):wr_iot_start_admission_stage(&s->admission,s->nonce,runner_read,&s->input.request,1,1,0))s->phase=WR_IOT_RUN_NETWORK;
  else if(s->admission.mutation_started)runner_recover(s);
  else if(wr_iot_start_admission_cancel(&s->admission))s->phase=WR_IOT_RUN_REJECTED;
  else s->phase=WR_IOT_RUN_UNCERTAIN;
  break;
 case WR_IOT_RUN_NETWORK:
  if(s->prior_closed.valid?wr_iot_reopen_network_step(&s->network,&s->admission,&s->input.request,&s->prior_closed):wr_iot_start_network_step(&s->network,&s->admission,&s->input.request,s->nonce))s->phase=WR_IOT_RUN_OPEN;
  else if(s->network.phase==WR_IOT_NET_RECOVERY)runner_recover(s);
  break;
 case WR_IOT_RUN_OPEN:
  if(wr_iot_rc_shutdown.pending){runner_recover(s);break;}
  if(s->prior_closed.valid&&!wr_iot_reopen_witness_current(&s->prior_closed)){runner_recover(s);break;}
  if(wr_iot_open_controller_submit(&s->open,s->input.id,&s->input.request))s->phase=WR_IOT_RUN_COMMIT;
  else runner_recover(s);
  if(s->prior_closed.valid&&s->open.phase!=WR_IOT_OPEN_IDLE&&s->open.phase!=WR_IOT_OPEN_NOT_SUBMITTED)
   s->prior_closed.submitted=1;
  break;
 case WR_IOT_RUN_COMMIT: {
  enum wr_iot_start_commit_phase before=s->commit.phase;
  if(wr_iot_start_commit_step(&s->commit,&s->admission,&s->network,&s->open,&s->input.request))s->phase=WR_IOT_RUN_ACTIVE;
  else if(s->commit.phase==WR_IOT_COMMIT_IDLE)runner_recover(s);
  else if(s->commit.phase==WR_IOT_COMMIT_DNS_UNCERTAIN)s->phase=WR_IOT_RUN_UNCERTAIN;
  else if(before==WR_IOT_COMMIT_DNS_COMMITTED&&
          s->commit.phase==WR_IOT_COMMIT_DNS_COMMITTED)s->phase=WR_IOT_RUN_COMMITTED_OFF;
  /* Confirmed commit uses a fresh normal-OFF transaction, never DNS abort. */
  break;
 }
 case WR_IOT_RUN_COMMITTED_OFF:
  if(s->stop.phase==WR_IOT_STOP_IDLE){
   (void)wr_iot_precreated_stop_begin(&s->stop,&s->open.attempt);
   break;
  }
  if(wr_iot_precreated_stop_step(&s->stop)){
   s->close.owner=getpid();s->close.attempt=s->open.attempt;
   s->close.close=s->stop.close;s->close.close_serial=s->stop.close_serial;
   s->network.phase=WR_IOT_NET_RECOVERY;
   s->phase=WR_IOT_RUN_CLOSED_ROLLBACK;
  }
  break;
 case WR_IOT_RUN_CLOSE:
  if(wr_iot_start_close_step(&s->close,&s->admission,&s->open))s->phase=WR_IOT_RUN_CLOSED_ROLLBACK;
  break;
 case WR_IOT_RUN_PRE_ROLLBACK:
  if(s->prior_closed.valid?wr_iot_reopen_rollback_step(&s->rollback,&s->network,&s->admission,&s->open,&s->prior_closed):wr_iot_start_network_rollback_step(&s->rollback,&s->network,&s->admission,&s->open,s->nonce))s->phase=WR_IOT_RUN_REJECTED;
  break;
 case WR_IOT_RUN_CLOSED_ROLLBACK:
  if(wr_iot_start_closed_rollback_step(&s->rollback,&s->network,&s->admission,&s->open,&s->close))s->phase=WR_IOT_RUN_REJECTED;
  break;
 default:break;
 }
 if(s->phase==WR_IOT_RUN_ACTIVE)return WR_IOT_RESULT_APPLIED;
 if(s->phase==WR_IOT_RUN_REJECTED)return WR_IOT_RESULT_REJECTED;
 return WR_IOT_RESULT_RECOVERY;
}

enum wr_iot_result_state wr_iot_start_runner_step(struct wr_iot_start_runner *s)
{
 enum wr_iot_result_state result;
 if(!s||s->owner!=getpid()||s->busy||!wr_iot_rc_shutdown.active)
  return WR_IOT_RESULT_RECOVERY;
 s->busy=1;result=runner_step(s);s->busy=0;
 return result;
}
enum wr_iot_result_state wr_iot_start_runner_continue(struct wr_iot_start_runner *s,
 const char *id,unsigned long long created)
{
 if(!s||!id||!created||s->owner!=getpid()||s->busy||
    !wr_iot_control_id(id)||
    !memchr(s->input.id,0,sizeof(s->input.id))||
    strcmp(id,s->input.id)||created!=s->input.created)
  return WR_IOT_RESULT_RECOVERY;
 return wr_iot_start_runner_step(s);
}

int wr_iot_start_runner_cancel_network(struct wr_iot_start_runner *s,
 const char *id,unsigned long long created)
{
 int fd;unsigned i;
 if(!s||!id||!created||s->owner!=getpid()||s->busy||
    s->phase!=WR_IOT_RUN_NETWORK||s->prior_closed.valid||s->admission.reopened||
    !wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||!wr_iot_control_id(id)||!memchr(s->input.id,0,sizeof(s->input.id))||
    strcmp(id,s->input.id)||created!=s->input.created||
    !s->admission.admitted||!s->admission.mutation_started||!s->admission.staged||
    s->admission.snapshot.owner!=getpid()||!s->admission.snapshot.active||
    s->admission.snapshot.token!=1||
    (s->open.phase!=WR_IOT_OPEN_IDLE&&s->open.phase!=WR_IOT_OPEN_NOT_SUBMITTED)||
    s->open.attempt.identity.adapter_epoch||s->open.attempt.identity.device_generation)return 0;
 for(i=0;i<16;i++)if(s->open.attempt.request_id[i])return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;
 if(close(fd))return 0;
 s->busy=1;runner_recover(s);s->busy=0;return 1;
}

int wr_iot_start_runner_cancel_stage(struct wr_iot_start_runner *s,
 const char *id,unsigned long long created)
{
 struct wr_iot_idle_result idle;unsigned i;int fd;
 if(!s||!id||!created||s->owner!=getpid()||s->busy||
    s->phase!=WR_IOT_RUN_STAGE||s->prior_closed.valid||s->admission.reopened||
    !wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||!wr_iot_control_id(id)||!memchr(s->input.id,0,sizeof(s->input.id))||
    strcmp(id,s->input.id)||created!=s->input.created||
    !s->admission.admitted||s->admission.mutation_started||s->admission.staged||
    s->admission.snapshot.owner!=getpid()||!s->admission.snapshot.active||
    s->admission.snapshot.token!=1||s->network.phase!=WR_IOT_NET_BRIDGE||s->network.attempted||
    s->open.phase!=WR_IOT_OPEN_IDLE||s->open.attempt.identity.adapter_epoch||
    s->open.attempt.identity.device_generation)return 0;
 for(i=0;i<16;i++)if(s->open.attempt.request_id[i])return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;
 if(close(fd))return 0;
 idle=s->admission.idle;s->busy=1;
 if(!wr_iot_start_admission_cancel(&s->admission)){s->busy=0;return 0;}
 /* Cancel zeroes admission ownership. Retain only its read-only lifetime/
  * serial receipt for terminal validation; admitted remains false. */
 s->admission.idle=idle;s->phase=WR_IOT_RUN_REJECTED;s->busy=0;return 1;
}

/* DNS has not been attempted while commit remains IDLE. Obtain explicit
 * CLOSE via the existing recovery path before rolling back any resources. */
int wr_iot_start_runner_cancel_uncommitted(struct wr_iot_start_runner *s,
 const char *id,unsigned long long created)
{
 int fd;unsigned i,nonzero=0;
 if(!s||!id||!created||s->owner!=getpid()||s->busy||s->phase!=WR_IOT_RUN_COMMIT||
    s->commit.phase!=WR_IOT_COMMIT_IDLE||s->prior_closed.valid||s->admission.reopened||
    !wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||!wr_iot_control_id(id)||!memchr(s->input.id,0,sizeof(s->input.id))||
    strcmp(id,s->input.id)||created!=s->input.created||
    !s->admission.admitted||!s->admission.mutation_started||!s->admission.staged||
    s->admission.snapshot.owner!=getpid()||!s->admission.snapshot.active||
    s->admission.snapshot.token!=1||s->admission.snapshot.recovering||s->admission.snapshot.disabling||
    s->open.owner!=getpid()||s->open.phase!=WR_IOT_OPEN_CONFIRMED||
    s->open.attempt.identity.adapter_epoch!=s->admission.idle.epoch||
    s->open.attempt.identity.device_generation!=s->admission.idle.generation)return 0;
 for(i=0;i<16;i++)nonzero|=s->open.attempt.request_id[i];
 if(!nonzero)return 0;
 if(s->commit.owner){
  if(s->commit.owner!=getpid()||!s->commit.open_token||
     memcmp(&s->commit.attempt,&s->open.attempt,sizeof(s->open.attempt)))return 0;
 }else if(s->commit.open_token)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;
 if(close(fd))return 0;
 s->busy=1;runner_recover(s);s->busy=0;return 1;
}

/* A failed commit is not evidence of either commit or rollback. Only a
 * positively retained owned startup transaction may enter abort recovery. */
int wr_iot_start_runner_cancel_uncertain(struct wr_iot_start_runner *s,
 const char *id,unsigned long long created)
{
 int fd;
 if(!s||!id||!created||s->owner!=getpid()||s->busy||s->phase!=WR_IOT_RUN_UNCERTAIN||
    s->commit.phase!=WR_IOT_COMMIT_DNS_UNCERTAIN||s->commit.owner!=getpid()||!s->commit.open_token||
    s->prior_closed.valid||s->admission.reopened||!wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||!wr_iot_control_id(id)||!memchr(s->input.id,0,sizeof(s->input.id))||
    strcmp(id,s->input.id)||created!=s->input.created||
    !s->admission.admitted||!s->admission.mutation_started||!s->admission.staged||
    s->admission.snapshot.owner!=getpid()||!s->admission.snapshot.active||
    s->admission.snapshot.token!=1||s->admission.snapshot.recovering||s->admission.snapshot.disabling||
    s->open.owner!=getpid()||s->open.phase!=WR_IOT_OPEN_CONFIRMED||
    s->network.phase!=WR_IOT_NET_READY||
    memcmp(&s->commit.attempt,&s->open.attempt,sizeof(s->open.attempt))||
    s->rollback.owner||s->rollback.phase!=WR_IOT_ROLL_BRIDGE_DOWN||
    s->rollback.dns_abort_required||s->rollback.dns_abort_confirmed)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;
 if(close(fd)||wr_iot_dns_activation_recovery_state()!=1)return 0;
 s->busy=1;s->rollback.dns_abort_required=1;runner_recover(s);s->busy=0;return 1;
}

/* Failed admission may still retain its read-only snapshot. No setter or
 * OPEN is allowed here; prove the exact new Main idle on both sides of its
 * release, and retain only that nonsecret receipt for terminal validation. */
int wr_iot_start_runner_cancel_admission(struct wr_iot_start_runner *s,
 const char *id,unsigned long long created,const struct wr_iot_driver_identity *expected)
{
 struct wr_iot_idle_result before={0},after={0};int fd;unsigned i;
 if(!s||!id||!created||!expected||!expected->adapter_epoch||!expected->device_generation||
    s->owner!=getpid()||s->busy||
    (s->phase!=WR_IOT_RUN_UNCERTAIN&&s->phase!=WR_IOT_RUN_REJECTED)||
    s->prior_closed.valid||s->admission.reopened||s->admission.admitted||s->admission.idle.serial||
    s->admission.mutation_started||s->admission.staged||
    s->commit.phase!=WR_IOT_COMMIT_IDLE||s->commit.owner||s->commit.open_token||
    s->open.owner||s->open.phase!=WR_IOT_OPEN_IDLE||
    s->open.attempt.identity.adapter_epoch||s->open.attempt.identity.device_generation||
    s->network.phase!=WR_IOT_NET_BRIDGE||s->network.attempted||
    s->rollback.owner||s->rollback.phase!=WR_IOT_ROLL_BRIDGE_DOWN||
    !wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||!wr_iot_control_id(id)||!memchr(s->input.id,0,sizeof(s->input.id))||
    strcmp(id,s->input.id)||created!=s->input.created)return 0;
 for(i=0;i<16;i++)if(s->open.attempt.request_id[i])return 0;
 if(s->admission.snapshot.active){
  if(s->admission.snapshot.owner!=getpid()||s->admission.snapshot.token!=1||
     s->admission.snapshot.recovering||s->admission.snapshot.disabling)return 0;
 }else if(s->admission.snapshot.owner||s->admission.snapshot.token)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;
 if(close(fd)||!wr_iot_driver_initial_idle_read(s->nonce,&before)||!before.serial||
    before.epoch!=expected->adapter_epoch||before.generation!=expected->device_generation)return 0;
 s->busy=1;
 if(s->admission.snapshot.active&&!wr_iot_start_admission_cancel(&s->admission)){s->busy=0;return 0;}
 if(!wr_iot_driver_initial_idle_read(s->nonce,&after)||after.serial<=before.serial||
    after.epoch!=expected->adapter_epoch||after.generation!=expected->device_generation){s->busy=0;return 0;}
 s->admission.idle=after;s->phase=WR_IOT_RUN_REJECTED;s->busy=0;return 1;
}
