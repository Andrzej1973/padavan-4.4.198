#!/usr/bin/env python3
"""Actual ON owner with absent/configured native desired records, host only."""
from pathlib import Path
import ast,resource,signal,subprocess,sys,tempfile
here=Path(__file__).resolve().parent
text=(here/'check-radio-on-owner.py').read_text()
ns={'__file__':str(here/'check-radio-on-owner.py')}
exec(compile(text[:text.index('\nwith tempfile.TemporaryDirectory(')],'<on-owner>','exec'),ns)
tree=ast.parse((here/'check-cold-config-revision.py').read_text())
provider=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='provider' for t in n.targets))
provider=provider.replace('#include "saved-config-store.c"','#define admitted wr_saved_fixture_admitted\n#include "saved-config-store.c"\n#undef admitted')
body=ns['body'];anchor='#include "radio-on-generation.c"';assert body.count(anchor)==1
body=body.replace(anchor,provider+'\n'+anchor)
# RC receipt storage is outside this isolated owner fixture. All entries use
# reload1; its historical file observer must stay unused. Rollback receipt
# publication is a validated injected boundary, exercised in RC composition.
body=body.replace('#include "radio-on-release-runtime.h"',r'''
static struct wr_iot_restart_profile_receipt radio_off_profile_receipt;
int wr_iot_rc_radio_off_profile_current(const struct wr_iot_physical_stop_request *r){(void)r;assert(0);return 0;}
int wr_iot_rc_radio_on_rollback_receipt(const struct wr_iot_on_generation *g){
 assert(depth==1&&g&&g->owner==getpid()&&!g->busy&&!g->main_may_have_started&&
  g->phase==WR_ON_GEN_RESTORED&&g->admission&&g->admission->profile.recovered);
 return 1;
}
#include "radio-on-release-runtime.h"
''')
configured=body
anchor='struct wr_iot_control_request r={.id="01000000000000000000000000000000",.created=10,.request=desired},wrong=r;'
assert configured.count(anchor)==1
configured=configured.replace(anchor,r'''struct wr_iot_saved_config next={.profile=desired};
 record_present=1;record_error=0;
 assert(wr_iot_saved_config_encode(desired_record,sizeof(desired_record),&next));
 strcpy(saved_ssid,"IoT"); /* Legacy stays old. */
'''+anchor,1)
configured=configured.replace('static void make_saved_profile(void){',r'''#include "generation-profile.h"
static void make_saved_profile(void){
 struct wr_iot_precreated_profile_request captured={0};
 assert(wr_iot_generation_profile_request(&captured)==1);
''',1)
configured=configured.replace('wr_iot_precreated_profile(in,out,saved_ssid,saved_password,0)',
 'wr_iot_precreated_profile(in,out,captured.ssid,captured.password,0)',1)
configured=configured.replace('assert(done&&saw_release&&ups==1&&wan_submits==1&&child_begins==1&&begins==1);',
 'assert(done&&saw_release&&ups==1&&wan_submits==1&&child_begins==1&&begins==1);\n {struct wr_iot_generation_config empty={0};struct wr_iot_saved_config clear={0};\n assert(!memcmp(&on_owner.restore.generation.config_revision,&empty,sizeof(empty)));\n assert(!memcmp(&on_owner.restore.generation.provisioning,&clear,sizeof(clear)));}')

# Reuse the complete native-provider/actual owner composition for disabled B.
# The control request intentionally contains no credentials; the captured
# revision supplies generation provisioning before its release-time wipe.
disabled=configured.split('int main(int argc',1)[0]+r'''
int main(int argc,char **argv){
 (void)check;(void)shutdown_handler;assert(argc==2);
 snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 make_profile();membership=guest_desired=guest_isolate=1;mc_read=aux_ok=1;
 up_result=WR_RESTART_UP_RETURNED;
 struct wr_iot_saved_config b={.profile={.enabled=0,.ssid="Disabled B",.password="disabled-b-password",
  .gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"}};
 record_present=1;assert(wr_iot_saved_config_encode(desired_record,sizeof(desired_record),&b));
 assert(!strcmp(saved_ssid,"IoT")); /* Historical A is unchanged. */
 struct wr_iot_control_request request={.id="01000000000000000000000000000000",.created=10};
 assert(wr_iot_rc_radio_on_begin(&request,1));
 int done=0,released=0,mask_retry=0;
 for(int tick=0;tick<60&&!done;tick++){
  if(on_owner.phase==ON_OWNER_RELEASE&&!mask_retry){
   mask_retry=1;fail_unmask=1;
   assert(!wr_iot_radio_on_step()&&on_owner.admission.profile.active&&radio_off_receipt_valid&&depth==1);
   assert(on_owner.restore.generation.config_revision.owner==getpid());
   assert(!strcmp(on_owner.restore.generation.provisioning.profile.ssid,"Disabled B"));
   fail_unmask=0;network_current=0;
   assert(!wr_iot_radio_on_step()&&on_owner.admission.profile.active&&radio_off_receipt_valid&&depth==1);
   network_current=1;
   strcpy(b.profile.ssid,"Later C");strcpy(b.profile.password,"later-c-password");
   assert(wr_iot_saved_config_encode(desired_record,sizeof(desired_record),&b));
  }
  done=wr_iot_radio_on_step();
  if(on_owner.restore.phase==WR_ON_RESTORE_RELEASED&&!released){
   released=1;
   struct wr_iot_generation_config empty={0};struct wr_iot_saved_config clear={0};
   assert(!memcmp(&on_owner.restore.generation.config_revision,&empty,sizeof(empty)));
   assert(!memcmp(&on_owner.restore.generation.provisioning,&clear,sizeof(clear)));
   assert(!radio_off_receipt_valid&&!depth&&wr_iot_rc_shutdown.radio_on_owned);
   /* The completed file remains B after desired C is saved. */
   strcpy(b.profile.ssid,"Later C");strcpy(b.profile.password,"later-c-password");
   assert(wr_iot_saved_config_encode(desired_record,sizeof(desired_record),&b));
  }
 }
 assert(done&&released&&mask_retry&&generator_calls==1&&ups==1&&!begins&&wan_submits==1&&child_begins==1);
 network_current=0;assert(!wr_iot_radio_on_retire()&&on_owner.owner);network_current=1;
 on_owner.disabled.idle.idle.epoch++;assert(!wr_iot_radio_on_retire());on_owner.disabled.idle.idle.epoch--;
 on_owner.disabled.idle.idle.generation++;assert(!wr_iot_radio_on_retire());on_owner.disabled.idle.idle.generation--;
 /* A foreign file cannot acquire the completed B receipt, even with idle true. */
 char foreign[1100];snprintf(foreign,sizeof(foreign),"%s/foreign",argv[1]);
 assert(!rename(profile_path,foreign));make_profile();
 assert(!wr_iot_radio_on_retire()&&on_owner.owner&&generator_calls==1&&ups==1);
 assert(!unlink(profile_path)&&!rename(foreign,profile_path));
 /* Rename changes ctime, so restoring a path is insufficient authority. */
 assert(!wr_iot_radio_on_retire()&&on_owner.owner);
 /* Fixture-only teardown of deliberately retained foreign-file state. */
 on_owner_wipe(&on_owner,sizeof(on_owner));wr_iot_rc_shutdown.radio_on_owned=0;
 assert(!unlink(profile_path)&&!depth);
}
'''

# Also complete actual root retirement with B/C continuity. The separate
# foreign-file mode deliberately retains the root instead.
disabled_success=disabled.split(' /* A foreign file cannot acquire',1)[0]+r'''
 assert(wr_iot_radio_on_retire()&&!on_owner.owner&&!wr_iot_radio_on_pending());
 assert(!wr_iot_rc_shutdown.radio_on_owned&&!depth&&!unlink(profile_path));
}
'''

# Compose the real private backend handoff with the actual native owner chain.
# Only the old completed origin and SDK idle reader are injected.
handoff=disabled_success
anchor='int main(int argc,char **argv){'
backend_actor=r'''
#include "activation-owner.h"
#include "rebind-owner.h"
static struct wr_iot_activation_owner backend;
static struct wr_iot_rebind_owner rebind;
static const struct wr_iot_cold_owner *wr_iot_cold_backend_parent;
static int initial_restart_retained(void){return 0;}
int wr_iot_activation_owner_observed(const struct wr_iot_activation_owner*s,const struct wr_iot_control_result*r){
 assert(s==&backend&&depth&&r->state==WR_IOT_RESULT_APPLIED);
 const char *id=s->phase==WR_IOT_OWNER_INITIAL_OFF?s->initial_off.id:s->start.input.id;
 unsigned long long created=s->phase==WR_IOT_OWNER_INITIAL_OFF?s->initial_off.created:s->start.input.created;
 return network_current&&!strcmp(id,r->id)&&created==r->created;
}
int wr_iot_rebind_owner_observed(const struct wr_iot_rebind_owner*s,const struct wr_iot_control_result*r){
 assert(s==&rebind&&depth&&r->state==WR_IOT_RESULT_APPLIED);
 return network_current&&!strcmp(s->start.input.id,r->id)&&s->start.input.created==r->created;
}
#include "rc-profile-history.inc"
#include "rc-on-disabled-retire.inc"
static void old_backend(void){
 wr_iot_rc_shutdown.normal_route_armed=1;
 backend.owner=getpid();backend.phase=WR_IOT_OWNER_OFF;
 backend.start.owner=backend.stop.owner=getpid();backend.start.phase=WR_IOT_RUN_STOPPED;
 backend.start.open.attempt.identity=(struct wr_iot_driver_identity){1,2};
 strcpy(backend.stop.id,"02000000000000000000000000000000");backend.stop.created=2;
 backend.stop.active=&backend.start;backend.stop.complete=1;
 backend.stop.stop.owner=getpid();backend.stop.stop.phase=WR_IOT_STOP_COMPLETE;
 backend.stop.stop.close.phase=WR_IOT_CLOSE_OWNER_RELEASED;
 backend.stop.stop.close.request.open_token=3;backend.stop.stop.close_serial=4;
}
'''
assert handoff.count(anchor)==1
boot_idle=(here/'rc-backend.c').read_text().split('int wr_iot_rc_boot_idle(void)',1)[1].split('/* Only fully completed OFF',1)[0]
backend_actor+='\nint wr_iot_rc_boot_idle(void)'+boot_idle
backend_actor+=r'''
#include "restart-restore.h"
static struct wr_iot_restart_restore *wr_iot_initial_restart_parent;
static struct wr_iot_initial_off physical_initial;
static int restart_finish_ok=1;
int wr_iot_restart_restore_finish_check(struct wr_iot_restart_restore*s){return s&&restart_finish_ok&&network_current;}
int wr_iot_restart_initial_active_current(struct wr_iot_restart_restore*s){return s&&s==wr_iot_initial_restart_parent&&network_current;}
#include "rc-restart-profile-history.inc"
'''

# Execute the exact prepared enabled cold retirement producer with synthetic
# terminal bookkeeping. Whole cold orchestration remains covered separately.
cold_retire=(here/'rc-cold-terminal.inc').read_text().split('static int wr_iot_cold_terminal_retire(',1)[1]
backend_actor+=r'''
#include "rc-cold-completion.h"
static void wr_iot_cold_release_wipe(void *data,size_t n){volatile unsigned char *p=data;while(n--)*p++=0;}
static int wr_iot_cold_followup_active(const struct wr_iot_cold_release*r){
 if(r->owner!=getpid()||r->parent||r->handoff||backend.phase!=WR_IOT_OWNER_ACTIVE||
  strcmp(r->id,backend.start.input.id)||r->created!=backend.start.input.created||
  r->identity.adapter_epoch!=backend.start.open.attempt.identity.adapter_epoch||
  r->identity.device_generation!=backend.start.open.attempt.identity.device_generation)return 0;
 int g=wr_iot_service_guard_enter(1);int ok=wr_iot_restart_profile_receipt_current(&r->profile);
 wr_iot_service_guard_leave(g);return ok;
}
'''+'\nstatic int wr_iot_cold_terminal_retire('+cold_retire

handoff=handoff.replace(anchor,backend_actor+'\n'+anchor)
anchor=' assert(wr_iot_rc_radio_on_begin(&request,1));'
assert handoff.count(anchor)==1
handoff=handoff.replace(anchor,' old_backend();\n'+anchor)
anchor=' assert(wr_iot_radio_on_retire()&&!on_owner.owner&&!wr_iot_radio_on_pending());'
assert handoff.count(anchor)==1
handoff=handoff.replace(anchor,r'''
 wr_iot_rc_shutdown.normal_route_armed=0;assert(!wr_iot_radio_on_retire());wr_iot_rc_shutdown.normal_route_armed=1;
 wr_iot_rc_shutdown.normal_route_requested=SIGUSR1;assert(!wr_iot_radio_on_retire());wr_iot_rc_shutdown.normal_route_requested=0; /* Fixture-only invalid route reset. */
 on_owner.disabled.idle.created++;assert(!wr_iot_radio_on_retire());on_owner.disabled.idle.created--;
 on_owner.disabled.idle.id[0]='2';assert(!wr_iot_radio_on_retire());on_owner.disabled.idle.id[0]='0';
 backend.busy=1;assert(!wr_iot_radio_on_retire()&&on_owner.owner);backend.busy=0;
 backend.start.stop.owner=getpid();assert(!wr_iot_radio_on_retire());backend.start.stop.owner=0;
 backend.start.close.owner=getpid();assert(!wr_iot_radio_on_retire());backend.start.close.owner=0;
 backend.start.rollback.owner=getpid();assert(!wr_iot_radio_on_retire());backend.start.rollback.owner=0;
 on_owner.admission.released.nonce[0]++;assert(!wr_iot_radio_on_retire());on_owner.admission.released.nonce[0]--;
 on_owner.admission.released.attempt++;assert(!wr_iot_radio_on_retire());on_owner.admission.released.attempt--;
 backend.stop.stop.close_serial++;assert(!wr_iot_radio_on_retire());backend.stop.stop.close_serial--;
 backend.stop.stop.disable.services.settings.active=1;assert(!wr_iot_radio_on_retire());backend.stop.stop.disable.services.settings.active=0;
 wr_iot_rc_shutdown.normal_route_requested=SIGTERM; /* Already completed root must yield to this queued route. */
 assert(wr_iot_rc_on_disabled_backend_retire(&on_owner.disabled,&on_owner.admission.released));
 assert(wr_iot_rc_on_disabled_backend_retire(&on_owner.disabled,&on_owner.admission.released));
 assert(!rebind.owner&&backend.owner==getpid()&&backend.phase==WR_IOT_OWNER_INITIAL_OFF);
 assert(backend.initial_off.created==10&&backend.initial_off.idle.epoch==2&&backend.initial_off.idle.generation==2);
 assert(!backend.start.owner&&!backend.stop.owner&&wr_iot_rc_profile_history.profile.valid);
 assert(wr_iot_rc_boot_idle()); /* Actual next cold-origin eligibility only. */
 {struct wr_iot_profile_binding b={0};struct wr_iot_restart_profile_receipt p={0};
  int g=wr_iot_service_guard_enter(1);assert(g==1);
  assert(wr_iot_rc_profile_history_read(&b,&p)&&b.kind==WR_PROFILE_BACKEND_INITIAL_OFF&&b.created==10);
  backend.initial_off.created++;assert(!wr_iot_rc_profile_history_read(&b,&p)&&!p.valid&&!b.kind);backend.initial_off.created--;
  backend.initial_off.idle.epoch++;assert(!wr_iot_rc_profile_history_read(&b,&p));backend.initial_off.idle.epoch--;
  network_current=0;assert(!wr_iot_rc_profile_history_read(&b,&p));network_current=1;
  assert(wr_iot_rc_profile_history_read(&b,&p));
  wr_iot_service_guard_leave(g);
 }
 assert(wr_iot_rc_shutdown.normal_route_requested==SIGTERM&&wr_iot_rc_shutdown.normal_route_armed);
'''+anchor)
history_cases=r'''
 {struct wr_iot_profile_binding binding={0};struct wr_iot_restart_profile_receipt file={0};
  int g=wr_iot_service_guard_enter(1);assert(wr_iot_rc_profile_history_read(&binding,&file));
  wr_iot_service_guard_leave(g);
  backend.phase=WR_IOT_OWNER_ACTIVE;backend.start.owner=getpid();backend.start.phase=WR_IOT_RUN_ACTIVE;
  strcpy(backend.start.input.id,"04000000000000000000000000000000");backend.start.input.created=11;
  backend.start.open.attempt.identity=(struct wr_iot_driver_identity){2,2};
  g=wr_iot_service_guard_enter(1);assert(!wr_iot_rc_profile_history_read(&binding,&file));wr_iot_service_guard_leave(g);
  struct wr_iot_cold_release release={.owner=getpid(),.created=11,.identity={2,2}};
  strcpy(release.id,backend.start.input.id);release.profile=wr_iot_rc_profile_history.profile;
  release.wan.attempted=release.wan.returned=1;
  struct wr_iot_cold_parent_release parent={.release=&release,.released=1};
  struct wr_iot_cold_terminal terminal={.owner=getpid(),.phase=WR_COLD_TERM_DONE,.parent_release=&parent,
   .led_attempted=1,.led_returned=1,.child={.owner=getpid(),.attempted=1,.fd=-1,.result=1}};
  terminal.terminal.result=1;wr_iot_rc_shutdown.radio_on_owned=1;
  release.identity.device_generation++;assert(!wr_iot_cold_terminal_retire(&terminal)&&release.owner);release.identity.device_generation--;
  assert(wr_iot_cold_terminal_retire(&terminal)&&!release.owner&&!terminal.owner&&!parent.release);
  assert(!wr_iot_rc_shutdown.radio_on_owned&&backend.phase==WR_IOT_OWNER_ACTIVE);
  g=wr_iot_service_guard_enter(1);
  assert(wr_iot_rc_profile_history_read(&binding,&file)&&binding.kind==WR_PROFILE_BACKEND_ACTIVE&&binding.created==11);
  memset(&wr_iot_rc_profile_history,0,sizeof(wr_iot_rc_profile_history));
  assert(!wr_iot_rc_profile_history_active()); /* Empty retained request, no guess from file. */
  backend.start.input.request.enabled=1;
  strcpy(backend.start.input.request.ssid,"Disabled B");strcpy(backend.start.input.request.password,"disabled-b-password");
  assert(wr_iot_rc_profile_history_active()&&wr_iot_rc_profile_history_read(&binding,&file));
  backend.start.input.request.password[0]='X';
  assert(!wr_iot_rc_profile_history_active());backend.start.input.request.password[0]='d';
  assert(wr_iot_rc_profile_history_active());

  binding.created++;assert(!wr_iot_rc_profile_history_remember(&binding,&file));binding.created--;
  assert(wr_iot_rc_profile_history_read(&binding,&file));
  rebind.owner=getpid();rebind.phase=WR_REBIND_OWNER_ACTIVE;
  strcpy(rebind.start.input.id,"05000000000000000000000000000000");rebind.start.input.created=12;
  rebind.start.start.identity=(struct wr_iot_driver_identity){3,2};
  struct wr_iot_profile_binding next={.kind=WR_PROFILE_BACKEND_REBIND_ACTIVE,.created=12,.identity={3,2}};
  strcpy(next.id,rebind.start.input.id);
  struct wr_iot_restart_profile_receipt clear={0};
  assert(!wr_iot_rc_profile_history_read(&binding,&clear)&&!clear.valid);
  next.identity.adapter_epoch++;assert(!wr_iot_rc_profile_history_remember(&next,&file));next.identity.adapter_epoch--;
  assert(wr_iot_rc_profile_history_remember(&next,&file)&&wr_iot_rc_profile_history_read(&binding,&clear));
  assert(binding.kind==WR_PROFILE_BACKEND_REBIND_ACTIVE&&binding.created==12);

  /* Actual restart preflight and inert commit; physical fence callback is
   * checked by the separate actual session/unmask fixture. */
  {struct wr_iot_restart_restore root={.owner=getpid()};struct wr_iot_restart_profile_history stage={0};
   root.generation.origin.origin=WR_PHYSICAL_ORIGIN_CLOSE;root.generation.origin.desired.enabled=1;
   root.handoff_created=12;root.open_id[0]=5;root.main.identity=(struct wr_iot_driver_identity){3,2};
   assert(wr_iot_radio_profile_take(&root.generation.profile));
   wr_iot_rc_shutdown.active=1;
   restart_finish_ok=0;assert(!wr_iot_rc_restart_profile_prepare(&root,&stage)&&!stage.binding.kind);restart_finish_ok=1;
   assert(wr_iot_rc_restart_profile_prepare(&root,&stage)&&stage.binding.kind==WR_PROFILE_BACKEND_REBIND_ACTIVE);
   root.main.identity.adapter_epoch++;assert(!wr_iot_rc_restart_profile_prepare(&root,&stage));root.main.identity.adapter_epoch--;
   assert(wr_iot_rc_restart_profile_prepare(&root,&stage));wr_iot_rc_restart_profile_commit(&stage);
   assert(wr_iot_rc_profile_history_read(&binding,&clear));
   memset(&rebind,0,sizeof(rebind));backend.phase=WR_IOT_OWNER_ACTIVE;
   strcpy(backend.start.input.id,"06000000000000000000000000000000");backend.start.input.created=13;
   backend.start.open.attempt.identity=(struct wr_iot_driver_identity){4,2};
   root.generation.origin.origin=WR_PHYSICAL_ORIGIN_INITIAL;root.handoff_created=13;root.open_id[0]=6;
   root.main.identity=(struct wr_iot_driver_identity){4,2};wr_iot_initial_restart_parent=&root;
   assert(wr_iot_rc_restart_profile_prepare(&root,&stage)&&stage.binding.kind==WR_PROFILE_BACKEND_ACTIVE);
   wr_iot_rc_restart_profile_commit(&stage);wr_iot_initial_restart_parent=NULL;
   assert(wr_iot_rc_profile_history_read(&binding,&clear)&&binding.created==13);
   /* Disabled INITIAL uses a fresh never-opened idle actor, not ACTIVE. */
   memset(&backend,0,sizeof(backend));root.generation.origin.desired.enabled=0;
   root.main.identity=(struct wr_iot_driver_identity){2,2};root.open_id[0]=1;physical_initial.created=14;
   assert(wr_iot_rc_restart_profile_prepare(&root,&stage)&&stage.binding.kind==WR_PROFILE_BACKEND_INITIAL_OFF);
   assert(!backend.owner);wr_iot_rc_restart_profile_commit(&stage);
   assert(backend.phase==WR_IOT_OWNER_INITIAL_OFF&&backend.initial_off.created==14);
   assert(wr_iot_rc_profile_history_read(&binding,&clear)&&binding.kind==WR_PROFILE_BACKEND_INITIAL_OFF);
   wr_iot_rc_shutdown.active=0;wr_iot_bundle_release(&root.generation.profile.files);
  }
  network_current=0;assert(!wr_iot_rc_profile_history_read(&binding,&clear));network_current=1;
  assert(wr_iot_rc_profile_history_read(&binding,&clear));
  FILE *f=fopen(profile_path,"a");assert(f&&fputs("# foreign drift\n",f)>=0&&!fclose(f));
  assert(!wr_iot_rc_profile_history_read(&binding,&clear)&&!clear.valid);
  wr_iot_service_guard_leave(g);
 }
'''
anchor=' assert(!wr_iot_rc_shutdown.radio_on_owned&&!depth&&!unlink(profile_path));'
assert handoff.count(anchor)==1
handoff=handoff.replace(anchor,history_cases+anchor)

handoff='#define WR_IOT_FIXTURE_REAL_DISABLED_RETIRE 1\n'+handoff
rebind_handoff=handoff.replace(' old_backend();',r'''
 old_backend();
 rebind.owner=getpid();rebind.phase=WR_REBIND_OWNER_OFF;
 rebind.start.owner=rebind.stop.owner=getpid();rebind.start.phase=WR_IOT_RUN_STOPPED;
 rebind.start.open.attempt.identity=(struct wr_iot_driver_identity){1,2};
 rebind.stop.active=&rebind.start;rebind.stop.complete=1;
 strcpy(rebind.stop.id,"03000000000000000000000000000000");rebind.stop.created=3;
 rebind.stop.stop.owner=getpid();rebind.stop.stop.phase=WR_IOT_STOP_COMPLETE;
 rebind.stop.stop.close.phase=WR_IOT_CLOSE_OWNER_RELEASED;
 rebind.stop.stop.close.request.open_token=3;rebind.stop.stop.close_serial=4;
''')
rebind_handoff=rebind_handoff.replace('backend.stop.stop.close_serial++;assert(!wr_iot_radio_on_retire());backend.stop.stop.close_serial--;','rebind.stop.stop.close_serial++;assert(!wr_iot_radio_on_retire());rebind.stop.stop.close_serial--;')

# Actual runtime OFF-file receipt observer, then reload0 mismatch refusal and
# a fresh reload1 B generation. The completed OFF transport is injected here;
# its real pre-quiesce/session/take path is checked by the OFF helpers.
runtime=(here/'rc-runtime.c').read_text()
start=runtime.index('int wr_iot_rc_radio_off_profile_current(')
observer=runtime[start:runtime.index('#endif',start)].strip().replace('&radio_off_receipt','&receipt')
sequence=configured.split('int main(int argc',1)[0]
stub='int wr_iot_rc_radio_off_profile_current(const struct wr_iot_physical_stop_request *r){(void)r;assert(0);return 0;}'
assert sequence.count(stub)==1
sequence=sequence.replace(stub,observer).replace('return down&&rollback_calls>0;','return down;')
sequence+=r'''
int main(int argc,char**argv){
 (void)check;(void)shutdown_handler;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 make_profile();
 strcpy(desired.ssid,"Desired B");strcpy(desired.password,"desired-b-password");
 strcpy(desired.gateway,"192.168.50.1");strcpy(desired.mask,"255.255.255.0");
 strcpy(desired.first,"192.168.50.20");strcpy(desired.last,"192.168.50.200");
 struct wr_iot_saved_config next={.profile=desired};record_present=1;
 assert(wr_iot_saved_config_encode(desired_record,sizeof(desired_record),&next));
 radio_off_profile_receipt.owner=getpid();radio_off_profile_receipt.valid=1;
 strcpy(radio_off_profile_receipt.path,profile_path);
 assert(wr_iot_generated_capture(&radio_off_profile_receipt.file,profile_path));
 {int g=wr_iot_service_guard_enter(1);struct wr_iot_physical_stop_request wrong=receipt;
  wrong.nonce[0]++;assert(!wr_iot_rc_radio_off_profile_current(&wrong));
  assert(wr_iot_rc_radio_off_profile_current(&receipt));wr_iot_service_guard_leave(g);
 }
 membership=guest_desired=guest_isolate=1;mc_read=aux_ok=1;up_result=WR_RESTART_UP_RETURNED;
 struct wr_iot_control_request request={.id="01000000000000000000000000000000",.created=10,.request=desired};
 admitted=active=1;begins=continues=0;
 request.id[1]='2';request.created=9; /* Separate refused transaction. */
 assert(wr_iot_rc_radio_on_begin(&request,0));
 assert(!wr_iot_radio_on_step()&&on_owner.phase==ON_OWNER_RETAINED&&!generator_calls&&!ups);
 assert(wr_iot_radio_on_step()==-1&&!on_owner.owner&&!depth&&radio_off_receipt_valid);
 assert(!generator_calls&&!ups&&!wan_submits&&!wr_iot_rc_shutdown.radio_on_owned);
 {int g=wr_iot_service_guard_enter(1);assert(wr_iot_rc_radio_off_profile_current(&receipt));wr_iot_service_guard_leave(g);}
 request.id[1]='1';request.created=10; /* Fresh request for reload1, no replay. */
 assert(wr_iot_rc_radio_on_begin(&request,1));
 int done=0,changed=0;
 for(int tick=0;tick<60&&!done;tick++){
  done=wr_iot_radio_on_step();
  if(on_owner.restore.phase==WR_ON_RESTORE_RELEASED&&!changed){
   changed=1;strcpy(next.profile.ssid,"Later C");
   assert(wr_iot_saved_config_encode(desired_record,sizeof(desired_record),&next));
  }
 }
 assert(done&&changed&&generator_calls==1&&ups==1&&begins==1&&wan_submits==1&&child_begins==1);
 {int g=wr_iot_service_guard_enter(1);assert(wr_iot_restart_profile_file_current(&desired));
  assert(!wr_iot_restart_profile_current(&desired));wr_iot_service_guard_leave(g);
 }
 assert(!strcmp(saved_ssid,"IoT")&&wr_iot_radio_on_retire()&&!on_owner.owner&&!depth&&!radio_off_receipt_valid);
 assert(!unlink(profile_path));
}
'''

same_profile=sequence.split('int main(int argc',1)[0]+r'''
int main(int argc,char**argv){
 (void)check;(void)shutdown_handler;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 strcpy(desired.gateway,"192.168.50.1");strcpy(desired.mask,"255.255.255.0");
 strcpy(desired.first,"192.168.50.20");strcpy(desired.last,"192.168.50.200");make_profile();
 struct wr_iot_saved_config next={.profile=desired};record_present=1;
 assert(wr_iot_saved_config_encode(desired_record,sizeof(desired_record),&next));
 radio_off_profile_receipt.owner=getpid();radio_off_profile_receipt.valid=1;
 strcpy(radio_off_profile_receipt.path,profile_path);
 assert(wr_iot_generated_capture(&radio_off_profile_receipt.file,profile_path));
 struct stat before,after;assert(!stat(profile_path,&before));
 membership=guest_desired=guest_isolate=1;mc_read=aux_ok=1;up_result=WR_RESTART_UP_RETURNED;
 admitted=active=1;begins=continues=0;
 struct wr_iot_control_request request={.id="01000000000000000000000000000000",.created=10,.request=desired};
 assert(wr_iot_rc_radio_on_begin(&request,0));
 int done=0;for(int tick=0;tick<60&&!done;tick++)done=wr_iot_radio_on_step();
 assert(done&&!generator_calls&&ups==1&&begins==1&&wan_submits==1&&child_begins==1);
 assert(wr_iot_radio_on_retire()&&!on_owner.owner&&!depth&&!radio_off_receipt_valid);
 assert(!stat(profile_path,&after)&&before.st_ino==after.st_ino&&
  before.st_mtim.tv_sec==after.st_mtim.tv_sec&&before.st_mtim.tv_nsec==after.st_mtim.tv_nsec&&
  before.st_ctim.tv_sec==after.st_ctim.tv_sec&&before.st_ctim.tv_nsec==after.st_ctim.tv_nsec);
 assert(!wr_iot_rc_radio_on_begin(&request,0)); /* A new ON needs a new OFF receipt. */
 assert(!unlink(profile_path));
}
'''

prove_legacy='--prove-legacy-regression' in sys.argv
units=[('absent',body),('configured',configured),('disabled-configured',disabled_success),('disabled-foreign',disabled),('disabled-backend-handoff',handoff),('disabled-rebind-handoff',rebind_handoff),('reload0-next-reload1',sequence),('reload0-same-profile',same_profile)]
if prove_legacy:
 units=[('legacy-disabled-regression',disabled_success)]
elif '--reload-sequence-only' in sys.argv:
 units=[('reload0-next-reload1',sequence),('reload0-same-profile',same_profile)]
elif '--handoff-only' in sys.argv:
 units=[('disabled-backend-handoff',handoff),('disabled-rebind-handoff',rebind_handoff)]
with tempfile.TemporaryDirectory(prefix='wr-on-owner-desired-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\nint nvram_getall(char *,int,int);\nint nvram_set(const char *,const char *);\n')
 (root/'wr-band-settings-snapshot.h').write_bytes((here.parent/'band-steering/settings-snapshot.h').read_bytes())
 if prove_legacy:
  current=(here/'radio-on-disabled.c').read_text()
  start=current.index('#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED != 1',current.index('static int disabled_followup_observe'))
  end=current.index('  wr_iot_initial_off_observed(&s->idle);',start)
  legacy=current[:start]+'  wr_iot_restart_disabled_profile_current()&&\n'+current[end:]
  (root/'radio-on-disabled.c').write_text(legacy)
 for mode,unit in units:
  (root/'check.c').write_text('#define WR_IOT_IAPP_POLICY_H\n#define WR_IOT_IAPP_POLICY_PREPARED 1\n'+unit)
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=1','-DWR_IOT_NATIVE_NVRAM_SPACE=61440','-DWR_IOT_NATIVE_NVRAM_HEADER_BYTES=20','-I'+d,'-I'+str(here),str(root/'check.c'),str(here.parent/'band-steering/settings-snapshot.c'),'-o',str(root/'check')],check=True)
  if prove_legacy:
   def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
   result=subprocess.run([str(root/'check'),d],capture_output=True,timeout=15,preexec_fn=no_core)
   assert result.returncode==-signal.SIGABRT and b'done&&released&&mask_retry' in result.stderr,result.stderr[-1000:]
   print('PASS regression control: historical disabled legacy gate rejects completed B/C lifecycle; core disabled',flush=True)
  else:
   subprocess.run([str(root/'check'),d],check=True,timeout=15)
   print('PASS actual ON desired owner mode:',mode,flush=True)
if not prove_legacy:print('PASS actual ON owner/mode/native capture/generation/release/WAN/terminal with absent/configured/disabled B records, later C, exact idle/file refusal and retirement while legacy A stays old; SDK/backend actors, no device acceptance')
