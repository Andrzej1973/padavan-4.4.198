"""Candidate RC-private handoff binding; parent/start/ACTIVE observer injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <string.h>
#include <unistd.h>
#include "rc-cold-start.h"
#include "activation-owner.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static struct wr_iot_activation_owner backend;
static struct {pid_t owner;} rebind;
static int depth,prepared=1,start_calls,start_claim=1,epoch_drift,active_proof,continues;
int wr_iot_service_guard_enter(int enabled){assert(enabled==1);depth++;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth);depth--;}
int wr_iot_cold_owner_step(struct wr_iot_cold_owner*p){assert(depth&&p);return prepared;}
int wr_iot_start_runner_begin(struct wr_iot_start_runner*s,const struct wr_iot_control_request*r,int a,int b,int c){
 assert(depth&&a==1&&b==1&&c==0);start_calls++;
 if(!start_claim)return 0;
 s->owner=getpid();s->phase=WR_IOT_RUN_STAGE;s->input=*r;s->admission.admitted=1;
 s->admission.idle=(struct wr_iot_idle_result){5+epoch_drift,2,9};return 1;
}
int wr_iot_activation_owner_observed(const struct wr_iot_activation_owner*s,const struct wr_iot_control_result*r){
 assert(depth&&s==&backend&&r->state==WR_IOT_RESULT_APPLIED);return active_proof;
}
enum wr_iot_result_state wr_iot_activation_owner_continue(struct wr_iot_activation_owner*s,const char*id,unsigned long long created){
 assert(s==&backend&&depth&&!strcmp(id,s->start.input.id)&&created==s->start.input.created);continues++;
 s->phase=WR_IOT_OWNER_ACTIVE;s->start.phase=WR_IOT_RUN_ACTIVE;s->start.open.attempt.identity=(struct wr_iot_driver_identity){5,2};return WR_IOT_RESULT_APPLIED;
}
static int initial_restart_retained(void){return 0;}
#include "rc-cold-start.inc"
#include "rc-cold-detach.inc"
static int fail_unmask,detach_calls;
static int detach_mask(int how,const sigset_t *set,sigset_t *old){if(how==SIG_SETMASK&&fail_unmask)return -1;return sigprocmask(how,set,old);}
#define sigprocmask detach_mask
#include "radio-stop-fence.c"
#undef sigprocmask
static void detach_cleanup(void *unused){(void)unused;detach_calls++;wr_iot_cold_detach_commit();}
int main(void){
 struct wr_iot_control_request input={0};memset(input.id,'1',32);input.created=9;input.request.enabled=1;
 strcpy(input.request.ssid,"IoT");strcpy(input.request.password,"iot-password");
 for(int fault=0;fault<=8;fault++){
  struct wr_iot_cold_owner parent={0};parent.owner=getpid();parent.phase=WR_COLD_OWNER_PREPARED;
  parent.input=input;memset(&parent.input.request,0,sizeof(parent.input.request));parent.generation.desired=input.request;
  parent.main.identity=(struct wr_iot_driver_identity){5,2};
  parent.admission.owner=parent.generation.owner=getpid();parent.admission.guard=parent.admission.busy=1;
  parent.admission.fence=(struct wr_iot_radio_stop_fence){getpid(),1};
  parent.generation.main_may_have_started=1;parent.generation.admission=&parent.admission;parent.main.generation=&parent.generation;
  memset(&backend,0,sizeof(backend));wr_iot_cold_backend_parent=NULL;memset(&wr_iot_cold_backend_identity,0,sizeof(wr_iot_cold_backend_identity));
  wr_iot_rc_shutdown.active=wr_iot_rc_shutdown.radio_off_owned=1;wr_iot_rc_shutdown.pending=0;
  prepared=fault!=1;start_claim=fault!=2;epoch_drift=fault==3;start_calls=continues=0;active_proof=0;
  struct wr_iot_control_request request=input;
  if(fault==4)request.created++;
  if(fault==5)backend.owner=getpid()+1;
  if(fault==6)strcpy(request.request.ssid,"foreign");
  if(fault>=7){backend.owner=getpid();backend.phase=WR_IOT_OWNER_INITIAL_OFF;backend.initial_off.owner=getpid();backend.initial_off.ready=1;backend.initial_off.created=8;memset(backend.initial_off.id,fault==7?'1':'2',32);}
  int claimed=wr_iot_rc_cold_start_begin(&parent,&request);
  assert(claimed==(fault==0||fault==3||fault==8)&&!depth);
  assert(start_calls==((fault==0||fault==2||fault==3||fault==8)?1:0));
  if(!claimed)continue;
  assert(!wr_iot_rc_cold_start_begin(&parent,&request)&&start_calls==1);
  assert(!wr_iot_rc_cold_active_current(&parent,&request));
  if(fault==3){assert(backend.start.phase==WR_IOT_RUN_UNCERTAIN&&!wr_iot_rc_cold_start_progress(&parent,&request)&&!continues);continue;}
  request.created++;assert(!wr_iot_rc_cold_start_progress(&parent,&request)&&!continues);request.created--;
  assert(wr_iot_rc_cold_start_progress(&parent,&request)&&continues==1);
  assert(!wr_iot_rc_cold_start_progress(&parent,&request)&&continues==1);
  backend.phase=WR_IOT_OWNER_ACTIVE;backend.start.phase=WR_IOT_RUN_ACTIVE;
  backend.start.open.attempt.identity=parent.main.identity;
  assert(!wr_iot_rc_cold_active_current(&parent,&request));active_proof=1;
  assert(wr_iot_rc_cold_active_current(&parent,&request)&&!depth);
  request.created++;assert(!wr_iot_rc_cold_active_current(&parent,&request));request.created--;
  parent.main.identity.adapter_epoch++;assert(!wr_iot_rc_cold_active_current(&parent,&request));parent.main.identity.adapter_epoch--;
  wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_rc_cold_active_current(&parent,&request));wr_iot_rc_shutdown.pending=0;
  rebind.owner=getpid();assert(!wr_iot_rc_cold_active_current(&parent,&request));rebind.owner=0;
  assert(wr_iot_cold_detach_preflight(&parent,&request));
  parent.main.identity.device_generation++;assert(!wr_iot_cold_detach_preflight(&parent,&request));parent.main.identity.device_generation--;
  assert(wr_iot_cold_detach_preflight(&parent,&request));
  struct wr_iot_activation_owner saved_backend=backend;
  struct wr_iot_cold_owner saved_parent=parent;
  /* Use the real outer fence: failed unmask cannot run detach. */
  wr_iot_rc_shutdown.active=0;memset(&parent.admission.fence,0,sizeof(parent.admission.fence));
  assert(wr_iot_radio_stop_fence_begin(&parent.admission.fence));
  saved_parent=parent;detach_calls=0;fail_unmask=1;
  assert(!wr_iot_radio_stop_fence_end_cleanup(&parent.admission.fence,detach_cleanup,NULL));
  assert(!detach_calls&&wr_iot_cold_backend_parent==&parent&&wr_iot_rc_shutdown.active);
  assert(!memcmp(&saved_backend,&backend,sizeof(backend))&&!memcmp(&saved_parent,&parent,sizeof(parent)));
  fail_unmask=0;assert(wr_iot_radio_stop_fence_end_cleanup(&parent.admission.fence,detach_cleanup,NULL)&&detach_calls==1);
  memset(&saved_parent.admission.fence,0,sizeof(saved_parent.admission.fence));
  assert(!wr_iot_cold_backend_parent&&!wr_iot_cold_backend_identity.adapter_epoch&&!wr_iot_cold_backend_identity.device_generation);
  assert(!memcmp(&saved_backend,&backend,sizeof(backend))&&!memcmp(&saved_parent,&parent,sizeof(parent)));
  assert(!wr_iot_cold_detach_preflight(&parent,&request)&&!wr_iot_rc_cold_active_current(&parent,&request));
  assert(!wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.radio_off_owned);
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-rc-cold-start-') as d:
 p=Path(d)/'check.c';p.write_text(body);b=Path(d)/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS private cold detach candidate: exact parent/request/identity, one initial begin, mismatch retained, ACTIVE requires full observer not APPLIED; ACTIVE backend and parent bytewise preserved, failed real fence unmask retains binding; successful callback removes binding only; no runtime composition')
