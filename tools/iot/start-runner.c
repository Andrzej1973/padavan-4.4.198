#include <string.h>
#include <unistd.h>
#include "start-runner.h"
#include "rc-shutdown-admission.h"
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
int wr_iot_start_runner_begin(struct wr_iot_start_runner *s,
 const struct wr_iot_control_request *input,int router,int radio,int mode)
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
 if(!wr_iot_start_admission_begin(&s->admission,s->nonce)){
  s->phase=s->admission.snapshot.active?WR_IOT_RUN_UNCERTAIN:WR_IOT_RUN_REJECTED;
  return 0;
 }
 s->phase=WR_IOT_RUN_STAGE;return 1;
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
  if(wr_iot_start_admission_stage(&s->admission,s->nonce,runner_read,&s->input.request,1,1,0))s->phase=WR_IOT_RUN_NETWORK;
  else if(s->admission.mutation_started)runner_recover(s);
  else if(wr_iot_start_admission_cancel(&s->admission))s->phase=WR_IOT_RUN_REJECTED;
  else s->phase=WR_IOT_RUN_UNCERTAIN;
  break;
 case WR_IOT_RUN_NETWORK:
  if(wr_iot_start_network_step(&s->network,&s->admission,&s->input.request,s->nonce))s->phase=WR_IOT_RUN_OPEN;
  else if(s->network.phase==WR_IOT_NET_RECOVERY)runner_recover(s);
  break;
 case WR_IOT_RUN_OPEN:
  if(wr_iot_rc_shutdown.pending){runner_recover(s);break;}
  if(wr_iot_open_controller_submit(&s->open,s->input.id,&s->input.request))s->phase=WR_IOT_RUN_COMMIT;
  else runner_recover(s);
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
  if(wr_iot_start_network_rollback_step(&s->rollback,&s->network,&s->admission,&s->open,s->nonce))s->phase=WR_IOT_RUN_REJECTED;
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
