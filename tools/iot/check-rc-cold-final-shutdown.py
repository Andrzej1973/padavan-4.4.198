"""Actual private final shutdown with real terminal fence; backend/child actors."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <string.h>
#include <unistd.h>
#include "cold-on-root.h"
#include "activation-observe.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static struct wr_iot_activation_owner backend;
static struct {pid_t owner;} rebind;
static const struct wr_iot_cold_owner *wr_iot_cold_backend_parent;
static int depth,signals,launches,child_ready,off_calls,advance_ready,closed_ok=1,drift,policy_ok=1,profile_ok=1,idle_ok=1,off_accept=1,fail_unmask;
static struct wr_iot_cold_root *live;
int wr_iot_service_guard_enter(int e){assert(e==1);depth++;return 1;}
void wr_iot_service_guard_leave(int t){assert(t==1&&depth);depth--;}
int wr_iot_iapp_child_begin(struct wr_iot_iapp_child*s){launches++;s->owner=getpid();s->attempted=1;s->fd=9;return 1;}
int wr_iot_iapp_child_step(struct wr_iot_iapp_child*s){if(child_ready){s->fd=-1;s->result=child_ready;}return child_ready;}
int wr_iot_cold_policy_current(const struct wr_iot_cold_policy*p){assert(depth&&p);return policy_ok;}
static int actor_profile_current(const struct wr_iot_restart_profile_receipt*p){assert(depth&&p);return profile_ok;}
int wr_iot_restart_disabled_profile_current(void){assert(depth);return 1;}
int wr_iot_initial_off_observed(const struct wr_iot_initial_off*s){assert(depth&&s==&backend.initial_off);return idle_ok;}
int wr_iot_rc_quiesce_shutdown_begin(struct wr_iot_rc_quiesce*s,const struct wr_iot_control_request*r){
 assert(depth&&wr_iot_rc_shutdown.pending&&r->created==8&&!r->request.enabled);off_calls++;
 if(!off_accept)return 0;
 s->owner=getpid();s->active=1;s->created=r->created;memcpy(s->id,r->id,33);
 backend.phase=WR_IOT_OWNER_STOP;backend.stop.owner=getpid();backend.stop.active=&backend.start;
 backend.stop.created=r->created;memcpy(backend.stop.id,r->id,33);profile_ok=0;return 1;
}
int wr_iot_rc_quiesce_advance(struct wr_iot_rc_quiesce*s,struct wr_iot_driver_closed_result*out){
 assert(depth&&s->owner==getpid());memset(out,0,sizeof(*out));if(!advance_ready)return 0;
 s->active=0;s->complete=1;backend.phase=WR_IOT_OWNER_OFF;backend.start.phase=WR_IOT_RUN_STOPPED;backend.stop.complete=1;
 backend.stop.stop.close.request.open_token=7;backend.stop.stop.close_serial=9;return 1;
}
int wr_iot_activation_owner_closed(const struct wr_iot_activation_owner*s,const struct wr_iot_control_result*r,struct wr_iot_driver_closed_result*out){
 assert(depth&&s==&backend&&r->created==8&&!strcmp(r->id,backend.stop.id));
 *out=(struct wr_iot_driver_closed_result){5,2,7,9};if(drift==1)out->adapter_epoch++;if(drift==2)out->open_token++;if(drift==3)out->close_serial++;
 return closed_ok;
}
static int mask_hook(int how,const sigset_t*set,sigset_t*old){if(how==SIG_SETMASK&&fail_unmask)return -1;return sigprocmask(how,set,old);}
#define sigprocmask mask_hook
#include "radio-stop-fence.c"
#undef sigprocmask
#define wr_iot_restart_profile_receipt_current actor_profile_current
#include "rc-cold-final-shutdown.inc"
#undef wr_iot_restart_profile_receipt_current
static void handler(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(!depth&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.radio_on_owned&&live&&!live->owner);
 assert(backend.phase==WR_IOT_OWNER_OFF||backend.phase==WR_IOT_OWNER_INITIAL_OFF);signals++;
}
static void setup(struct wr_iot_cold_root*s,int enabled){
 memset(s,0,sizeof(*s));memset(&backend,0,sizeof(backend));live=s;
 profile_ok=policy_ok=idle_ok=closed_ok=off_accept=1;drift=child_ready=advance_ready=0;
 s->owner=getpid();s->enabled=enabled;s->phase=WR_COLD_ROOT_TERMINAL;backend.owner=getpid();
 struct wr_iot_terminal_iapp *t;struct wr_iot_iapp_child *child;
 if(enabled){
  s->release.owner=getpid();s->release.created=7;memset(s->release.id,'1',32);s->release.identity=(struct wr_iot_driver_identity){5,2};
  s->released.released=1;s->released.release=&s->release;
  s->terminal.owner=getpid();s->terminal.phase=WR_COLD_TERM_IAPP;s->terminal.parent_release=&s->released;s->terminal.led_attempted=s->terminal.led_returned=1;
  t=&s->terminal.terminal;child=&s->terminal.child;
  backend.phase=WR_IOT_OWNER_ACTIVE;backend.start.owner=getpid();backend.start.phase=WR_IOT_RUN_ACTIVE;
  backend.start.input.created=7;memcpy(backend.start.input.id,s->release.id,33);backend.start.open.attempt.identity=s->release.identity;
 }else{
  s->disabled_release.owner=getpid();s->disabled_release.created=7;memset(s->disabled_release.id,'1',32);s->disabled_release.identity=(struct wr_iot_driver_identity){5,2};
  s->disabled_released.released=1;s->disabled_released.release=&s->disabled_release;
  s->disabled_terminal.owner=getpid();s->disabled_terminal.phase=WR_COLD_DISABLED_TERM_IAPP;s->disabled_terminal.parent_release=&s->disabled_released;s->disabled_terminal.led_attempted=s->disabled_terminal.led_returned=1;
  t=&s->disabled_terminal.terminal;child=&s->disabled_terminal.child;
  backend.phase=WR_IOT_OWNER_INITIAL_OFF;backend.initial_off.owner=getpid();backend.initial_off.ready=1;backend.initial_off.created=7;
  memcpy(backend.initial_off.id,s->disabled_release.id,33);backend.initial_off.idle.epoch=5;backend.initial_off.idle.generation=2;
 }
 wr_iot_rc_shutdown.radio_on_owned=1;
 assert(wr_iot_terminal_iapp_begin(t,child));assert(!wr_iot_terminal_iapp_step(t));
 assert(!raise(SIGTERM)&&wr_iot_rc_shutdown_note(SIGTERM));
}
int main(void){
 struct sigaction sa={0};sa.sa_handler=handler;sigemptyset(&sa.sa_mask);assert(!sigaction(SIGTERM,&sa,NULL));
 struct wr_iot_control_request off={0};off.created=8;memset(off.id,'2',32);
 for(int enabled=0;enabled<=1;enabled++){
  struct wr_iot_cold_root s,zero={0};setup(&s,enabled);int old_off=off_calls,old_signals=signals,old_launches=launches;
  assert(!wr_iot_rc_cold_root_final_shutdown(&s,&off)&&depth==1&&signals==old_signals&&off_calls==old_off);
  child_ready=1;
  if(enabled){
   assert(!wr_iot_rc_cold_root_final_shutdown(&s,&off)&&off_calls==old_off+1&&s.final_off_attempted);
   assert(!wr_iot_rc_cold_root_final_shutdown(&s,&off)&&off_calls==old_off+1);
   advance_ready=1;
   for(drift=1;drift<=3;drift++)assert(!wr_iot_rc_cold_root_final_shutdown(&s,NULL)&&s.owner&&depth==1);
   drift=0;closed_ok=0;assert(!wr_iot_rc_cold_root_final_shutdown(&s,NULL));closed_ok=1;
   s.final_off.resume_needed=1;assert(!wr_iot_rc_cold_root_final_shutdown(&s,NULL));s.final_off.resume_needed=0;
   s.final_off.desired.password[0]='x';assert(!wr_iot_rc_cold_root_final_shutdown(&s,NULL));s.final_off.desired.password[0]=0;
  }else{
   idle_ok=0;assert(!wr_iot_rc_cold_root_final_shutdown(&s,NULL));idle_ok=1;
   backend.initial_off.idle.generation++;assert(!wr_iot_rc_cold_root_final_shutdown(&s,NULL));backend.initial_off.idle.generation--;
  }
  rebind.owner=getpid();assert(!wr_iot_rc_cold_root_final_shutdown(&s,NULL));rebind.owner=0;
  policy_ok=0;assert(!wr_iot_rc_cold_root_final_shutdown(&s,NULL));policy_ok=1;
  fail_unmask=1;assert(!wr_iot_rc_cold_root_final_shutdown(&s,NULL)&&s.owner&&depth==1&&signals==old_signals);
  fail_unmask=0;assert(wr_iot_rc_cold_root_final_shutdown(&s,NULL)&&!memcmp(&zero,&s,sizeof(s))&&!depth&&signals==old_signals+1);
  assert(off_calls==old_off+enabled&&launches==old_launches);
 }
 /* A refused OFF is retained permanently, never replayed. */
 struct wr_iot_cold_root s;setup(&s,1);child_ready=1;off_accept=0;int old_off=off_calls;
 assert(!wr_iot_rc_cold_root_final_shutdown(&s,&off)&&s.final_off_attempted&&off_calls==old_off+1);
 for(int i=0;i<3;i++)assert(!wr_iot_rc_cold_root_final_shutdown(&s,&off)&&off_calls==old_off+1);
 /* Fixture teardown only: borrowed actor had not submitted any OFF. */
 sa.sa_handler=SIG_IGN;assert(!sigaction(SIGTERM,&sa,NULL));
 struct wr_iot_terminal_iapp*t=&s.terminal.terminal;wr_iot_rc_shutdown.radio_on_owned=0;
 assert(wr_iot_terminal_iapp_shutdown_finish(t,cold_final_cleanup,&s));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-cold-final-') as d:
 p=Path(d)/'check.c';p.write_text(body);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'restart-terminal-iapp.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=20)
print('PASS private final cold shutdown: real held terminal/SIGTERM, exact enabled CLOSED tuple or INITIAL_OFF receipt, no old profile check after owned OFF mutation, one OFF attempt/refusal retained, stale/rebind/policy/resume/credential refusal, failed mask retains, root/guard/exclusion cleared before signal; backend/child/proof actors')
