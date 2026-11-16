from pathlib import Path
import subprocess,tempfile,sys
here=Path(__file__).resolve().parent;root=Path(__file__).resolve().parent
def setup(name):
 p=root/name;s=p.read_text();ns={'__file__':str(p)};exec(compile(s[:s.index('\nwith tempfile.TemporaryDirectory(')],'<'+name+'>','exec'),ns);return ns
pn=setup('check-parent.py');bn=setup('check-backend-composed.py')
parent=pn['body'].split('int main(int argc',1)[0].replace('struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;','extern struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;')
parent=parent.replace('int wr_iot_restart_guest_admin_state(int*out){*out=1;return 1;}',
 'static int cancel_guest_up=1; int wr_iot_restart_guest_admin_state(int*out){*out=cancel_guest_up;return 1;}')
parent+=r'''
#include "restart-initial-handoff.c"
#include "restart-cancel-check.c"
void parent_fixture_closed_cancel_check(struct wr_iot_restart_restore *s,const struct wr_iot_rc_quiesce *q){
 assert(!wr_iot_restart_restore_cancel_check(s,q));
 cancel_guest_up=0;s->guest.phase=s->guest.desired?WR_GUEST_DOWN_OBSERVED:WR_GUEST_POLICY_OFF;
 assert(wr_iot_restart_restore_cancel_check(s,q)&&!s->busy);
 assert(!wr_iot_restart_restore_cancel_check(s,NULL));
}
void parent_fixture_cancel_check(struct wr_iot_restart_restore *s,int opened){
 assert(wr_iot_restart_restore_preopen_rejected(s)==!opened);
 assert(!wr_iot_restart_restore_cancel_check(s,NULL));
 cancel_guest_up=0;
 s->guest.phase=s->guest.desired?WR_GUEST_DOWN_OBSERVED:WR_GUEST_POLICY_OFF;
 assert(wr_iot_restart_restore_cancel_check(s,NULL)&&!s->busy);
 struct wr_iot_rc_quiesce off={0};
 assert(!wr_iot_restart_restore_cancel_check(s,&off));
 cancel_guest_up=1;assert(!wr_iot_restart_restore_cancel_check(s,NULL));cancel_guest_up=0;
}
void parent_fixture_prepare(struct wr_iot_restart_restore *s,const char *directory){
 snprintf(profile_path,sizeof(profile_path),"%s/profile",directory);(void)check;(void)restored;(void)active_ok;
 initial_mode=1;origin=(struct wr_iot_rc_physical_resume){.origin=WR_PHYSICAL_ORIGIN_INITIAL,.intent={1,1,1},
 .initial={.action=WR_STOP_RELEASE,.epoch=1,.generation=2,.idle_serial=3,.attempt=4,.nonce={9}},
 .resume_needed=1,.desired={.enabled=1,.ssid="IoT",.password="iot-password",.gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"}};
 strcpy(saved_enabled,"1");char before[4096];size_t n;capture_baseline(before,&n);probe_ok=1;
 unsigned char id[16]={7};assert(wr_iot_restart_restore_begin(s,id));
 for(unsigned i=0;i<30&&s->phase!=WR_RESTORE_PREPARED;i++)wr_iot_restart_restore_step(s);
 assert(s->phase==WR_RESTORE_PREPARED&&s->main.identity.adapter_epoch==2);
}
void parent_fixture_drift(int bad){auth_ok=!bad;}
void parent_fixture_dispose(struct wr_iot_restart_restore *s){wr_iot_bundle_release(&s->generation.profile.files);assert(!unlink(profile_path));}
'''
backend=bn['body'].split('int main(void)',1)[0]
backend+='int wr_iot_rc_normal_shutdown_arm_ready(void){return wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending;}\nvoid wr_iot_rc_normal_shutdown_arm_commit(void){assert(wr_iot_rc_shutdown.active);wr_iot_rc_shutdown.normal_route_armed=1;}\n'
a=backend.index('static int parent_ok=1;');b=backend.index('#include "rc-initial-restart-start.inc"',a);backend=backend[:a]+backend[b:]
backend=backend.replace('#include "rc-initial-restart-start.inc"', '#include "rc-initial-restart-start.inc"\n#include "rc-initial-restart-detach.inc"')
# Use actual two-step commit; only DNS transaction primitives remain actors.
backend='\n'.join(line for line in backend.splitlines() if not line.startswith('int wr_iot_start_commit_step('))+'\n'
backend=backend.replace('bridge_index=7;rollback_dns=0;', 'bridge_index=7;rollback_dns=1;')
backend+='\nstatic int actual_dns_commits; int wr_iot_dns_activation_commit(void){assert(depth&&rollback_dns==1);actual_dns_commits++;if(getenv("WR_INITIAL_UNCERTAIN_CANCEL_TEST"))return 0;rollback_dns=0;return 1;}\n'
backend=backend.replace('(struct wr_iot_driver_open_recovery_result){1,2,3}', '(struct wr_iot_driver_open_recovery_result){2,2,3}')
backend=backend.replace('s->attempt=(struct wr_iot_driver_attempt){{1,2},{1}}','s->attempt=(struct wr_iot_driver_attempt){{2,2},{1}}').replace('live_token=3,live_epoch=1','live_token=3,live_epoch=2')
prefix='#define wr_iot_driver_initial_idle_read fixture_old_idle\n'+bn['ns']['prefix']+'\n#undef wr_iot_driver_initial_idle_read\n'
prefix=prefix.replace('static int rollback_dns,abort_calls;', 'static int rollback_dns,abort_calls,uncertain_abort_fail;').replace('abort_calls++;rollback_dns=0;return 1;', 'if(uncertain_abort_fail)return 0;abort_calls++;rollback_dns=0;return 1;')
prefix=prefix.replace('a->identity.adapter_epoch==1&&', 'a->identity.adapter_epoch==2&&').replace('(struct wr_iot_driver_closed_result){1,2,3,observed_serial}', '(struct wr_iot_driver_closed_result){2,2,3,observed_serial}')
prefix+='''void admission_fault_guard(int);
static int admission_fault_taken;
static int cancel_idle_failure;
int wr_iot_driver_initial_idle_read(const unsigned char *n,struct wr_iot_idle_result *r){unsigned char actor_nonce[16];assert(n&&n[0]==7);memcpy(actor_nonce,n,16);actor_nonce[0]=1;int ok=fixture_old_idle(actor_nonce,r);if(ok)r->epoch=2;if(getenv("WR_INITIAL_ADMISSION_CANCEL_TEST")&&idle_reads==2&&!admission_fault_taken){admission_fault_taken=1;if(!strcmp(getenv("WR_INITIAL_ADMISSION_CANCEL_TEST"),"retained"))admission_fault_guard(1);return 0;}if(cancel_idle_failure==1)return 0;if(cancel_idle_failure==2)r->serial=1;if(cancel_idle_failure==3)r->epoch=99;return ok;}\n'''
backend+=r'''
void admission_fault_guard(int value){guard_invalid=value;}
void parent_fixture_prepare(struct wr_iot_restart_restore *,const char *);
void parent_fixture_drift(int);
void parent_fixture_dispose(struct wr_iot_restart_restore *);
void parent_fixture_cancel_check(struct wr_iot_restart_restore *,int);
void parent_fixture_closed_cancel_check(struct wr_iot_restart_restore *,const struct wr_iot_rc_quiesce *);
int main(int argc,char **argv){
 assert(argc==2||argc==3);assert(candidate_read(NULL,"wr_iot_enable"));reset();idle_reads=0;rollback_dns=0;
 for(unsigned i=7;i<16;i++)strcpy(values[i].value,i<10?"0":"");
 wr_iot_rc_shutdown.active=1;struct wr_iot_restart_restore parent={0};parent_fixture_prepare(&parent,argv[1]);
 struct wr_iot_control_request input={.id="07000000000000000000000000000000",.created=19};input.request=parent.generation.origin.desired;
 if(argc==3){
  parent_fixture_drift(1);assert(!wr_iot_restart_initial_handoff_begin(&parent,&input)&&!backend.owner&&parent.phase==WR_RESTORE_HANDOFF);
  parent_fixture_drift(0);assert(!wr_iot_restart_initial_handoff_begin(&parent,&input)&&!backend.owner);
  parent_fixture_dispose(&parent);return 0;
 }
 if(getenv("WR_INITIAL_UNCLAIMED_CANCEL_TEST")){
  parent_fixture_drift(1);
  assert(!wr_iot_restart_initial_handoff_begin(&parent,&input)&&!parent.initial_start_claimed&&!backend.start.owner&&!initial_restart_retained());
  parent_fixture_drift(0);assert(!wr_iot_restart_initial_handoff_begin(&parent,&input));
  assert(!wr_iot_restart_initial_cancel_step(&parent));wr_iot_rc_shutdown.pending=SIGTERM;parent.busy=1;
  struct wr_iot_activation_owner before=backend;
  for(cancel_idle_failure=1;cancel_idle_failure<=3;cancel_idle_failure++)assert(!wr_iot_rc_initial_restart_unclaimed_current(&parent,&input));
  cancel_idle_failure=0;backend.start.owner=getpid();assert(!wr_iot_rc_initial_restart_unclaimed_current(&parent,&input));backend.start.owner=0;
  assert(!memcmp(&before,&backend,sizeof(before))&&wr_iot_rc_initial_restart_unclaimed_current(&parent,&input));
  parent.busy=0;assert(wr_iot_restart_initial_cancel_step(&parent)&&!wr_iot_restart_initial_active_current(&parent));
  parent_fixture_cancel_check(&parent,0);
  wr_iot_rc_initial_restart_detach_commit();assert(!initial_restart_retained()&&!backend.start.input.request.password[0]);
  parent_fixture_dispose(&parent);return 0;
 }
 assert(wr_iot_restart_initial_handoff_begin(&parent,&input)&&parent.initial_start_claimed);
 if(getenv("WR_INITIAL_CANCEL_TEST")||getenv("WR_INITIAL_NETWORK_CANCEL_TEST")||getenv("WR_INITIAL_STAGE_CANCEL_TEST")||getenv("WR_INITIAL_COMMIT_CANCEL_TEST")||getenv("WR_INITIAL_COMMITTED_CANCEL_TEST")||getenv("WR_INITIAL_UNCERTAIN_CANCEL_TEST")||getenv("WR_INITIAL_ADMISSION_CANCEL_TEST")){
  int network_cancel=getenv("WR_INITIAL_NETWORK_CANCEL_TEST")!=NULL;
  int stage_cancel=getenv("WR_INITIAL_STAGE_CANCEL_TEST")!=NULL;
  int commit_cancel=getenv("WR_INITIAL_COMMIT_CANCEL_TEST")!=NULL;
  int committed_cancel=getenv("WR_INITIAL_COMMITTED_CANCEL_TEST")!=NULL;
  int uncertain_cancel=getenv("WR_INITIAL_UNCERTAIN_CANCEL_TEST")!=NULL;
  int admission_cancel=getenv("WR_INITIAL_ADMISSION_CANCEL_TEST")!=NULL;
  int retained_admission=admission_cancel&&!strcmp(getenv("WR_INITIAL_ADMISSION_CANCEL_TEST"),"retained");
  if(admission_cancel){admission_fault_guard(0);assert(admission_fault_taken&&!backend.start.admission.admitted);assert(backend.start.admission.snapshot.active==retained_admission);}
  enum wr_iot_start_runner_phase cancel_phase=admission_cancel?(retained_admission?WR_IOT_RUN_UNCERTAIN:WR_IOT_RUN_REJECTED):(commit_cancel||committed_cancel||uncertain_cancel)?WR_IOT_RUN_COMMIT:stage_cancel?WR_IOT_RUN_STAGE:network_cancel?WR_IOT_RUN_NETWORK:WR_IOT_RUN_OPEN;
  while(backend.phase==WR_IOT_OWNER_START&&backend.start.phase!=cancel_phase)
   assert(wr_iot_restart_initial_handoff_step(&parent)==0);
  assert(backend.start.phase==cancel_phase);
  if(committed_cancel){
   assert(!wr_iot_restart_initial_handoff_step(&parent));
   assert(backend.start.phase==WR_IOT_RUN_COMMIT&&backend.start.commit.phase==WR_IOT_COMMIT_DNS_COMMITTED&&actual_dns_commits==1);
  }
  if(uncertain_cancel){
   assert(!wr_iot_restart_initial_handoff_step(&parent));
   assert(backend.start.phase==WR_IOT_RUN_UNCERTAIN&&backend.start.commit.phase==WR_IOT_COMMIT_DNS_UNCERTAIN&&actual_dns_commits==1);
  }
  struct wr_iot_activation_owner before=backend;
  assert(!wr_iot_rc_initial_restart_cancel_progress(&parent,&input));
  assert(!memcmp(&before,&backend,sizeof(before)));
  wr_iot_rc_shutdown.pending=SIGTERM;
  assert(!wr_iot_restart_initial_handoff_step(&parent));
  assert(!memcmp(&before,&backend,sizeof(before)));
  parent.busy=1;
  wr_iot_rc_shutdown.pending=SIGINT;
  assert(!wr_iot_rc_initial_restart_cancel_progress(&parent,&input));
  wr_iot_rc_shutdown.pending=SIGTERM;
  struct wr_iot_control_request wrong=input;wrong.created++;
  assert(!wr_iot_rc_initial_restart_cancel_progress(&parent,&wrong));
  enum wr_iot_start_runner_phase saved_phase=backend.start.phase;
  backend.start.phase=WR_IOT_RUN_COMMIT;
  enum wr_iot_start_commit_phase commit_phase=backend.start.commit.phase;
  backend.start.commit.phase=WR_IOT_COMMIT_DNS_UNCERTAIN;
  assert(!wr_iot_rc_initial_restart_cancel_progress(&parent,&input));
  assert(backend.start.phase==WR_IOT_RUN_COMMIT);
  backend.start.commit.phase=commit_phase;backend.start.phase=saved_phase;
  struct wr_iot_restart_restore foreign=parent;
  assert(!wr_iot_rc_initial_restart_cancel_progress(&foreign,&input));
  assert(!memcmp(&before,&backend,sizeof(before)));
  if(network_cancel||stage_cancel){
   backend.start.open.attempt.request_id[0]=1;
   assert(!wr_iot_rc_initial_restart_cancel_progress(&parent,&input));
   backend.start.open.attempt.request_id[0]=0;
  }
  if(uncertain_cancel){
   rollback_dns=-1;assert(!wr_iot_rc_initial_restart_cancel_progress(&parent,&input));
   rollback_dns=0;assert(!wr_iot_rc_initial_restart_cancel_progress(&parent,&input));rollback_dns=1;
   assert(!memcmp(&before,&backend,sizeof(before)));
  }
  if(network_cancel){
   unsigned attempted=backend.start.network.attempted;
   parent.busy=0;assert(!wr_iot_restart_initial_cancel_step(&parent));parent.busy=1;
   assert(backend.start.phase==WR_IOT_RUN_PRE_ROLLBACK&&backend.start.network.attempted==attempted);
  }
  if(admission_cancel){
   for(cancel_idle_failure=1;cancel_idle_failure<=3;cancel_idle_failure+=2){
    assert(!wr_iot_rc_initial_restart_cancel_progress(&parent,&input));
    assert(!memcmp(&before,&backend,sizeof(before)));
   }
   cancel_idle_failure=0;admission_fault_guard(1);
   assert(!wr_iot_rc_initial_restart_cancel_progress(&parent,&input));admission_fault_guard(0);
   assert(!memcmp(&before,&backend,sizeof(before)));
   parent.busy=0;assert(wr_iot_restart_initial_cancel_step(&parent));parent.busy=1;
  }
  if(commit_cancel||committed_cancel||uncertain_cancel)close_result=progress_result=release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
  int injected_dns_absence=0;
  for(unsigned i=0;i<50&&backend.phase==WR_IOT_OWNER_START;i++){
   if(uncertain_cancel&&!injected_dns_absence&&backend.start.phase==WR_IOT_RUN_CLOSED_ROLLBACK&&backend.start.rollback.phase==WR_IOT_ROLL_DNS){
    rollback_dns=0;parent.busy=0;assert(!wr_iot_restart_initial_cancel_step(&parent));parent.busy=1;
    assert(backend.start.rollback.phase==WR_IOT_ROLL_DNS&&!backend.start.rollback.dns_abort_confirmed&&backend.start.admission.snapshot.active);
    rollback_dns=1;uncertain_abort_fail=1;parent.busy=0;assert(!wr_iot_restart_initial_cancel_step(&parent));parent.busy=1;
    assert(backend.start.rollback.phase==WR_IOT_ROLL_DNS&&!backend.start.rollback.dns_abort_confirmed);
    uncertain_abort_fail=0;injected_dns_absence=1;
   }
   parent.busy=0;(void)wr_iot_restart_initial_cancel_step(&parent);
   assert(!parent.busy);parent.busy=1;
  }
  assert(backend.phase==WR_IOT_OWNER_REJECTED);
  if(stage_cancel||admission_cancel){
   assert(!backend.start.admission.admitted&&!backend.start.admission.snapshot.active&&!backend.start.admission.snapshot.token);
   assert(backend.start.admission.idle.epoch==2&&backend.start.admission.idle.generation==2&&backend.start.admission.idle.serial);
   assert(!backend.start.network.attempted);
  }
  if(commit_cancel||committed_cancel||uncertain_cancel){
   int (*observe)(struct wr_iot_restart_restore *,const struct wr_iot_control_request *)=
    committed_cancel?wr_iot_rc_initial_restart_committed_closed:wr_iot_rc_initial_restart_rollback_closed;
   struct wr_iot_close_controller *closed_ctl=committed_cancel?&backend.start.stop.close:&backend.start.close.close;
   if(committed_cancel)assert(actual_dns_commits==1&&!abort_calls&&!backend.start.rollback.owner&&backend.start.rollback.phase==WR_IOT_ROLL_BRIDGE_DOWN);
   else if(uncertain_cancel)assert(actual_dns_commits==1&&abort_calls==1&&injected_dns_absence&&backend.start.rollback.dns_abort_required==1&&backend.start.rollback.dns_abort_confirmed==1);
   else assert(!actual_dns_commits);
   assert(backend.start.open.phase==WR_IOT_OPEN_CONFIRMED&&closes==1&&releases==1);
   assert(!wr_iot_rc_initial_restart_preopen_rejected(&parent,&input));
   assert(observe(&parent,&input));
   if(uncertain_cancel){backend.start.rollback.dns_abort_confirmed=0;assert(!observe(&parent,&input));backend.start.rollback.dns_abort_confirmed=1;}
   backend.start.open.owner++;assert(!observe(&parent,&input));backend.start.open.owner--;
   observed_serial++;assert(!observe(&parent,&input));observed_serial--;
   closed_ctl->request.open_token++;assert(!observe(&parent,&input));closed_ctl->request.open_token--;
   parent.busy=0;assert(wr_iot_restart_initial_cancel_step(&parent));
   parent_fixture_cancel_check(&parent,1);
   wr_iot_rc_initial_restart_detach_commit();assert(!initial_restart_retained()&&!backend.start.input.request.password[0]);
   parent_fixture_dispose(&parent);return 0;
  }
  assert(backend.start.open.phase==WR_IOT_OPEN_IDLE||backend.start.open.phase==WR_IOT_OPEN_NOT_SUBMITTED);
  assert(initial_restart_retained()&&wr_iot_initial_restart_parent==&parent);
  before=backend;
  assert(wr_iot_rc_initial_restart_preopen_rejected(&parent,&input));
  assert(!memcmp(&before,&backend,sizeof(before)));
  for(cancel_idle_failure=1;cancel_idle_failure<=3;cancel_idle_failure++)
   assert(!wr_iot_rc_initial_restart_preopen_rejected(&parent,&input));
  cancel_idle_failure=0;
  backend.start.admission.snapshot.active=1;
  assert(!wr_iot_rc_initial_restart_preopen_rejected(&parent,&input));
  backend.start.admission.snapshot.active=0;
  backend.start.open.attempt.request_id[0]=1;
  assert(!wr_iot_rc_initial_restart_preopen_rejected(&parent,&input));
  backend.start.open.attempt.request_id[0]=0;
  assert(wr_iot_rc_initial_restart_preopen_rejected(&parent,&input));

  assert(!wr_iot_rc_initial_restart_cancel_progress(&parent,&input));
  parent.busy=0;
  assert(wr_iot_restart_initial_cancel_step(&parent)&&!parent.busy);
  parent_fixture_cancel_check(&parent,0);
  wr_iot_rc_initial_restart_detach_commit();assert(!initial_restart_retained()&&!backend.start.input.request.password[0]);
  wr_iot_rc_shutdown.pending=0;
  assert(!wr_iot_restart_initial_cancel_step(&parent)&&!parent.busy);
  parent_fixture_dispose(&parent);return 0;
 }

 for(unsigned i=0;i<50&&backend.phase==WR_IOT_OWNER_START;i++)wr_iot_restart_initial_handoff_step(&parent);
 assert(backend.phase==WR_IOT_OWNER_ACTIVE);
 assert(wr_iot_restart_initial_active_current(&parent));
 if(getenv("WR_INITIAL_OFF_TEST")){
  struct wr_iot_control_request off={.id="08000000000000000000000000000000",.created=20};
  struct wr_iot_rc_quiesce q={0};parent.busy=1;
  struct wr_iot_activation_owner before=backend;
  assert(!wr_iot_rc_initial_restart_shutdown_begin(&parent,&input,&off,&q));
  wr_iot_rc_shutdown.pending=SIGTERM;
  struct wr_iot_restart_restore foreign=parent;
  assert(!wr_iot_rc_initial_restart_shutdown_begin(&foreign,&input,&off,&q));
  filter_ok=0;assert(!wr_iot_rc_initial_restart_shutdown_begin(&parent,&input,&off,&q));filter_ok=1;
  assert(!memcmp(&before,&backend,sizeof(before))&&!q.owner);
  assert(!wr_iot_rc_quiesce_shutdown_begin(&q,&off));
  assert(wr_iot_rc_initial_restart_shutdown_begin(&parent,&input,&off,&q));
  assert(q.owner==getpid()&&q.active&&!q.resume_needed&&!q.desired.password[0]);
  assert(backend.phase==WR_IOT_OWNER_STOP&&backend.start.phase==WR_IOT_RUN_STOPPING);
  assert(backend.stop.active==&backend.start&&initial_restart_retained());
  assert(!wr_iot_rc_initial_restart_shutdown_begin(&parent,&input,&off,&q));
  struct wr_iot_driver_closed_result closed={0};
  assert(!wr_iot_rc_initial_restart_shutdown_closed(&parent,&input,&q,&closed)&&!closed.open_token);
  close_result=progress_result=release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
  int terminal=0;
  for(unsigned i=0;i<60&&terminal!=2;i++){
   parent.busy=0;terminal=wr_iot_restart_initial_shutdown_step(&parent,&off,&q);
   assert(!parent.busy);parent.busy=1;
  }
  assert(terminal==2);
  assert(q.complete&&!q.active&&backend.phase==WR_IOT_OWNER_OFF);
  assert(!backend.start.input.request.password[0]);
  assert(wr_iot_rc_initial_restart_shutdown_closed(&parent,&input,&q,&closed));
  assert(closed.adapter_epoch==2&&closed.device_generation==2&&closed.open_token==3&&closed.close_serial);
  observed_serial++;assert(!wr_iot_rc_initial_restart_shutdown_closed(&parent,&input,&q,&closed)&&!closed.open_token);observed_serial--;
  backend.start.commit.open_token++;assert(!wr_iot_rc_initial_restart_shutdown_closed(&parent,&input,&q,&closed));backend.start.commit.open_token--;
  assert(wr_iot_rc_initial_restart_shutdown_closed(&parent,&input,&q,&closed)&&initial_restart_retained());
  parent.busy=0;parent_fixture_closed_cancel_check(&parent,&q);
  parent_fixture_dispose(&parent);return 0;
 }
 parent_fixture_drift(1);assert(!wr_iot_restart_initial_active_current(&parent));parent_fixture_drift(0);
 filter_ok=0;assert(!wr_iot_restart_initial_active_current(&parent));filter_ok=1;
 assert(wr_iot_restart_restore_finish_check(&parent));
 assert(wr_iot_restart_initial_active_current(&parent));
 parent_fixture_dispose(&parent);return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-initial-parent-backend-') as d:
 p=Path(d);subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True);(p/'rc.h').write_text((p/'rc.h').read_text()+'\nconst char *nvram_safe_get(const char *);\n')
 (p/'parent.c').write_text(parent);(p/'backend.c').write_text(prefix+'\n#include "check-reopen-unused.h"\n'+backend)
 flags=['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(root)]
 subprocess.run(flags+['-c',str(p/'parent.c'),'-o',d+'/parent-inventory.o'],check=True)
 symbols=subprocess.check_output(['nm','--defined-only',d+'/parent-inventory.o'],text=True)
 public={'wr_iot_restart_initial_enabled_profile_current','wr_iot_restart_main_bridge_current','parent_fixture_closed_cancel_check','wr_iot_restart_initial_shutdown_step','wr_iot_restart_generation_origin_current','parent_fixture_cancel_check','parent_fixture_prepare','parent_fixture_drift','parent_fixture_dispose','wr_iot_restart_initial_parent_current','wr_iot_restart_initial_handoff_begin','wr_iot_restart_initial_handoff_step','wr_iot_restart_initial_active_current','wr_iot_restart_initial_cancel_step','wr_iot_restart_restore_finish_check'}
 renames=['-D'+line.split()[2]+'=parent_fixture_'+line.split()[2] for line in symbols.splitlines() if len(line.split())==3 and line.split()[1]=='T' and line.split()[2] not in public]
 subprocess.run(flags+renames+['-c',str(p/'parent.c'),'-o',d+'/parent.o'],check=True)
 # Stage every translation unit beside one candidate header search path;
 # quoted includes in baseline source directories must not select old layouts.
 units_dir=p/'units';units_dir.mkdir();compile_units=[]
 for n in [*bn['units'],'start-commit.c']:
  source=(root if n in ('start-runner.c','start-closed-rollback.c') else here)/n
  unit=units_dir/n;unit.write_bytes(source.read_bytes());compile_units.append(str(unit))
 subprocess.run(flags+[str(p/'backend.c'),*compile_units,d+'/parent.o','-o',d+'/check'],check=True)
 for args in [[],['refused-parent']]:subprocess.run([d+'/check',d]+args,check=True,timeout=30)
 import os
 subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_INITIAL_CANCEL_TEST':'1'})
 subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_INITIAL_NETWORK_CANCEL_TEST':'1'})
 subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_INITIAL_STAGE_CANCEL_TEST':'1'})
 subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_INITIAL_COMMIT_CANCEL_TEST':'1'})
 subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_INITIAL_COMMITTED_CANCEL_TEST':'1'})
 subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_INITIAL_UNCERTAIN_CANCEL_TEST':'1'})
 for kind in ['clean','retained']:
  subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_INITIAL_ADMISSION_CANCEL_TEST':kind})
 subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_INITIAL_UNCLAIMED_CANCEL_TEST':'1'})
 subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_INITIAL_OFF_TEST':'1'})
print('PASS actual INITIAL generation/Main/restore/parent predicate/handoff/backend/runner/ACTIVE/finish plus pending STAGE/NETWORK/COMMIT idle/committed/uncertain recovery and ACTIVE normal CLOSED; fixture hooks namespaced per translation unit, shared shutdown state; driver/network/Guest/auth operations actors, no device claim')
