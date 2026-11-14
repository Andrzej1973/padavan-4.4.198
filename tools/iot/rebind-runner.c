#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "rebind-runner.h"
#include "rc-shutdown-admission.h"
#include "request-stage.h"
#include "network-check.h"
#include "bridge.h"
#include "quarantine.h"
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

static void request_wipe(struct wr_iot_request *r)
{
 volatile unsigned char *p=(volatile unsigned char *)r;unsigned i;
 for(i=0;i<sizeof(*r);i++)p[i]=0;
}
int wr_iot_rebind_runner_begin(struct wr_iot_rebind_runner *s,
 const struct wr_iot_control_request *input,
 const struct wr_iot_physical_stop_request *physical,int router,int radio,int mode)
{
 struct wr_iot_request checked={0};unsigned char nonce[16];unsigned i,nonzero=0;
 if(!s||!input||!physical||s->owner||s->phase!=WR_IOT_RUN_IDLE||
    physical->action!=WR_STOP_RELEASE||!wr_iot_physical_stop_request_valid(physical)||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    !memchr(input->id,0,sizeof(input->id))||!wr_iot_control_id(input->id)||
    !input->created||input->request.enabled!=1)return 0;
#define BOUNDED(f) if(!memchr(input->request.f,0,sizeof(input->request.f)))return 0;
 BOUNDED(ssid) BOUNDED(password) BOUNDED(gateway) BOUNDED(mask) BOUNDED(first) BOUNDED(last)
#undef BOUNDED
 for(i=0;i<16;i++){
  unsigned char a=input->id[2*i],b=input->id[2*i+1];
  nonce[i]=(unsigned char)(((a<='9'?a-'0':a-'a'+10)<<4)|(b<='9'?b-'0':b-'a'+10));
  nonzero|=nonce[i];
 }
 if(!nonzero)return 0;
 if(!wr_iot_request_read(&checked,runner_read,(void *)&input->request,router,radio,mode,NULL,0)){
  request_wipe(&checked);return 0;
 }
 s->owner=getpid();s->input=*input;s->input.request=checked;request_wipe(&checked);
 if(!wr_iot_rebind_start_begin(&s->start,physical,nonce)){
  s->phase=s->start.admission.snapshot.active?WR_IOT_RUN_UNCERTAIN:WR_IOT_RUN_REJECTED;
  return 0;
 }
 s->phase=WR_IOT_RUN_STAGE;return 1;
}
/* A single OPEN submission with the exact new identity and existing network
 * predicates. A zero ioctl result alone does not advance to COMMIT. */
static int runner_open(struct wr_iot_rebind_runner *s)
{
 struct wr_iot_physical_rebind_request r={0};
 struct wr_iot_driver_identity identity={0};
 struct wr_iot_driver_open_current_result current={0};int submitted;
 if(s->network.phase!=WR_IOT_NET_READY||wr_iot_rc_shutdown.pending||
    !wr_iot_request_stage_matches(&s->input.request)||!wr_iot_bss_is_down()||
    !wr_iot_network_check(s->input.request.gateway,s->input.request.mask,
                         s->input.request.first,s->input.request.last)||
    !wr_iot_bridge_address_matches(s->input.request.gateway,s->input.request.mask)||
    !wr_iot_network_services_ready(s->input.request.gateway)||
    !wr_iot_active_filter_ready_current()||
    !wr_iot_rebind_configuration_current(&s->start.physical,s->start.open_id,&identity)||
    identity.adapter_epoch!=s->start.identity.adapter_epoch||
    identity.device_generation!=s->start.identity.device_generation||
    !wr_iot_request_stage_matches(&s->input.request)||wr_iot_rc_shutdown.pending)return 0;
 r.operation=WR_REBIND_OPEN;r.physical=s->start.physical;
 r.open.adapter_epoch=identity.adapter_epoch;r.open.device_generation=identity.device_generation;
 memcpy(r.open.request_id,s->start.open_id,sizeof(r.open.request_id));
 r.open.ssid_length=strlen(s->input.request.ssid);
 r.open.password_length=strlen(s->input.request.password);
 memcpy(r.open.ssid,s->input.request.ssid,r.open.ssid_length);
 memcpy(r.open.password,s->input.request.password,r.open.password_length);
 submitted=wr_iot_rebind_open_submit(&s->open,&r);
 wr_iot_physical_rebind_wipe(&r);
 return submitted&&!wr_iot_rc_shutdown.pending&&
  wr_iot_rebind_open_current(&s->open,&current)&&
  wr_iot_active_filter_observed_current()&&wr_iot_request_stage_matches(&s->input.request);
}
static void runner_recover(struct wr_iot_rebind_runner *s)
{
 s->network.phase=WR_IOT_NET_RECOVERY;
 if(s->open.phase==WR_REBIND_OPEN_IDLE||s->open.phase==WR_REBIND_OPEN_NOT_SUBMITTED)
  s->phase=WR_IOT_RUN_PRE_ROLLBACK;
 else if(s->open.phase==WR_REBIND_OPEN_CURRENT||s->open.phase==WR_REBIND_OPEN_RETAINED)
  s->phase=WR_IOT_RUN_CLOSE;
 else s->phase=WR_IOT_RUN_UNCERTAIN;
}
static enum wr_iot_result_state runner_step(struct wr_iot_rebind_runner *s)
{
 if(!s||s->owner!=getpid())return WR_IOT_RESULT_RECOVERY;
 switch(s->phase){
 case WR_IOT_RUN_STAGE:
  if(wr_iot_rebind_start_stage(&s->start,runner_read,&s->input.request,1,1,0))s->phase=WR_IOT_RUN_NETWORK;
  else if(s->start.admission.mutation_started)runner_recover(s);
  else if(wr_iot_start_admission_cancel(&s->start.admission))s->phase=WR_IOT_RUN_REJECTED;
  else s->phase=WR_IOT_RUN_UNCERTAIN;
  break;
 case WR_IOT_RUN_NETWORK:
  if(wr_iot_rebind_network_step(&s->network,&s->start,&s->input.request))s->phase=WR_IOT_RUN_OPEN;
  else if(s->network.phase==WR_IOT_NET_RECOVERY)runner_recover(s);
  break;
 case WR_IOT_RUN_OPEN:
  if(wr_iot_rc_shutdown.pending){runner_recover(s);break;}
  if(runner_open(s))s->phase=WR_IOT_RUN_COMMIT;
  else runner_recover(s);
  break;
 case WR_IOT_RUN_COMMIT: {
  enum wr_iot_start_commit_phase before=s->commit.phase;
  if(wr_iot_rebind_commit_step(&s->commit,&s->start,&s->network,&s->open,&s->input.request))s->phase=WR_IOT_RUN_ACTIVE;
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
  if(wr_iot_rebind_close_step(&s->close,&s->start,&s->open))s->phase=WR_IOT_RUN_CLOSED_ROLLBACK;
  break;
 case WR_IOT_RUN_PRE_ROLLBACK:
  if(wr_iot_rebind_rollback_step(&s->rollback,&s->network,&s->start,&s->open))s->phase=WR_IOT_RUN_REJECTED;
  break;
 case WR_IOT_RUN_CLOSED_ROLLBACK:
  if(wr_iot_rebind_closed_rollback_step(&s->rollback,&s->network,&s->start,&s->open,&s->close))s->phase=WR_IOT_RUN_REJECTED;
  break;
 default:break;
 }
 if(s->phase==WR_IOT_RUN_ACTIVE)return WR_IOT_RESULT_APPLIED;
 if(s->phase==WR_IOT_RUN_REJECTED)return WR_IOT_RESULT_REJECTED;
 return WR_IOT_RESULT_RECOVERY;
}

enum wr_iot_result_state wr_iot_rebind_runner_step(struct wr_iot_rebind_runner *s)
{
 enum wr_iot_result_state result;
 if(!s||s->owner!=getpid()||s->busy||!wr_iot_rc_shutdown.active)
  return WR_IOT_RESULT_RECOVERY;
 s->busy=1;result=runner_step(s);s->busy=0;
 return result;
}
enum wr_iot_result_state wr_iot_rebind_runner_continue(struct wr_iot_rebind_runner *s,
 const char *id,unsigned long long created)
{
 if(!s||!id||!created||s->owner!=getpid()||s->busy||
    !wr_iot_control_id(id)||
    !memchr(s->input.id,0,sizeof(s->input.id))||
    strcmp(id,s->input.id)||created!=s->input.created)
  return WR_IOT_RESULT_RECOVERY;
 return wr_iot_rebind_runner_step(s);
}
