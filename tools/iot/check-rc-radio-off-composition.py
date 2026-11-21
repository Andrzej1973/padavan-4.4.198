"""Actual RC ppoll runtime plus OFF consumer; physical/SDK actors injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code='#define WR_IOT_RUNTIME_FIXTURE_EXTERNAL_ADMISSION\n'+(here/'check-rc-runtime.c').read_text()
old='int wr_iot_radio_off_begin(struct wr_iot_radio_off_owner*s,const struct wr_iot_control_request*r){(void)s;(void)r;return 0;}\nint wr_iot_radio_off_step(struct wr_iot_radio_off_owner*s,int reload){(void)s;(void)reload;assert(0);return 0;}'
assert code.count(old)==1
code=code.replace(old,r'''
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int off_transport,off_terminal,policy_allowed,policy_reads,off_base;
int wr_iot_rc_physical_begin_quiesce(const struct wr_iot_rc_physical_intent*i,const struct wr_iot_control_request*r){
 assert(!i->restart&&!i->radio_on&&!i->reload&&!r->request.enabled);
 off_transport=physical_pending=1;wr_iot_rc_shutdown.active=1;return 1;
}
int wr_iot_rc_radio_off_policy(int reload,struct wr_iot_radio_off_policy*p){
 assert(wr_iot_rc_shutdown.active&&physical_steps==off_base);policy_reads++;
 if(!policy_allowed)return 0;
 *p=(struct wr_iot_radio_off_policy){reload,0,0,WR_WAN_NONE};return 1;
}
int wr_iot_rc_physical_off_failed(const char*i,unsigned long long t){(void)i;(void)t;return 0;}
int wr_iot_rc_physical_off_read(const char*i,unsigned long long t,struct wr_iot_physical_stop_request*p){
 (void)i;(void)t;*p=(struct wr_iot_physical_stop_request){WR_STOP_RELEASE,1,2,3,4,5,{1}};return off_terminal==1;
}
int wr_iot_rc_physical_take_off(const char*i,unsigned long long t){assert(!strcmp(i,"11111111111111111111111111111111")&&t==7);return off_terminal;}
#include "radio-off-owner.c"
''')
code=code.replace('int wr_iot_off_followup_begin(struct wr_iot_off_followup*s,const struct wr_iot_radio_off_owner*o){(void)s;(void)o;assert(0);return 0;}', 'static int followup_begins,followup_steps;\nint wr_iot_off_followup_begin(struct wr_iot_off_followup*s,const struct wr_iot_radio_off_owner*o){assert(o==&radio_off_owner&&o->result==1&&!physical_pending);followup_begins++;s->owner=getpid();s->released=o->released;s->phase=WR_OFF_FOLLOWUP_PROFILE_BEGIN;return 1;}')
code=code.replace('enum wr_iot_off_followup_phase wr_iot_off_followup_step(struct wr_iot_off_followup*s){(void)s;assert(0);return WR_OFF_FOLLOWUP_IDLE;}', 'enum wr_iot_off_followup_phase wr_iot_off_followup_step(struct wr_iot_off_followup*s){assert(s->owner==getpid()&&followup_begins==1);followup_steps++;s->phase=WR_OFF_FOLLOWUP_NETWORK_PENDING;return s->phase;}')
code=code.replace('int wr_iot_off_followup_finish(struct wr_iot_off_followup*s,struct wr_iot_radio_off_owner*o){(void)s;(void)o;assert(0);return 0;}', 'static int finish_calls,finish_allowed,redispatches;\nint wr_iot_off_followup_finish(struct wr_iot_off_followup*s,struct wr_iot_radio_off_owner*o){finish_calls++;if(!finish_allowed)return 0;memset(o,0,sizeof(*o));s->phase=WR_OFF_FOLLOWUP_DONE;wr_iot_rc_shutdown.radio_off_owned=0;return 1;}')
code=code.replace('int wr_iot_rc_dispatch(void){assert(0);return 0;}', 'int wr_iot_rc_dispatch(void){assert(!radio_off_owner.owner&&!radio_off_followup.owner&&!wr_iot_rc_shutdown.radio_off_owned);redispatches++;return 0;}')
code=code.replace('void wr_iot_rc_physical_step(void){physical_steps++;}', 'void wr_iot_rc_physical_step(void){physical_steps++;if(off_transport){assert(policy_reads&&policy_allowed);physical_pending=0;wr_iot_rc_shutdown.active=0;off_terminal=1;}}')
a=' assert(wr_iot_status_endpoint_close(&endpoint));'
assert code.count(a)==1
code=code.replace(a,r'''
 struct wr_iot_control_request off={.id="11111111111111111111111111111111",.created=7};
 off_base=physical_steps;int ordinary=steps,scheduled=resume_steps;
 struct wr_iot_physical_stop_request receipt={0};assert(!wr_iot_rc_radio_off_receipt(&receipt)&&!receipt.epoch);
 assert(!wr_iot_rc_radio_off_begin(&off,2));
 assert(wr_iot_rc_radio_off_begin(&off,1));
 pending=resume_pending=1;
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(policy_reads==1&&physical_steps==off_base&&steps==ordinary&&resume_steps==scheduled);
 policy_allowed=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(policy_reads==2&&physical_steps==off_base+1&&steps==ordinary&&resume_steps==scheduled);
 assert(wr_iot_rc_shutdown.radio_off_owned&&radio_off_owner.result==1&&radio_off_pending()&&radio_off_owner.policy_ready);
 assert(!wr_iot_rc_radio_off_begin(&off,1)); /* Follow-up has not acknowledged it. */
 assert(!followup_begins&&!followup_steps);
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(physical_steps==off_base+1&&steps==ordinary&&resume_steps==scheduled&&policy_reads==2);
 assert(followup_begins==1&&!followup_steps);
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(followup_begins==1&&followup_steps==1&&radio_off_followup.phase==WR_OFF_FOLLOWUP_NETWORK_PENDING);
 assert(physical_steps==off_base+1&&policy_reads==2&&steps==ordinary&&resume_steps==scheduled);


 radio_off_followup.phase=WR_OFF_FOLLOWUP_FINAL_PENDING;
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);assert(finish_calls==1&&!redispatches&&radio_off_owner.owner);
 finish_allowed=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(finish_calls==2&&radio_off_followup.phase==WR_OFF_FOLLOWUP_DONE&&!radio_off_owner.owner&&!redispatches);
 assert(!wr_iot_rc_radio_off_begin(&off,1));
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);assert(!radio_off_followup.owner&&radio_off_redispatch&&!redispatches);assert(!wr_iot_rc_radio_off_begin(&off,1));
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);assert(redispatches==1&&!radio_off_redispatch);
 assert(wr_iot_rc_radio_off_receipt(&receipt)&&receipt.action==WR_STOP_RELEASE&&receipt.epoch==1&&receipt.attempt==5);
 receipt.epoch++;assert(wr_iot_rc_radio_off_receipt(&receipt)&&receipt.epoch==1);
 assert(!wr_iot_rc_radio_off_begin(&off,1));
 pending=resume_pending=0;notification=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(physical_steps==off_base+1&&policy_reads==2);notification=0;
'''+a)
prepared_code=('#define _GNU_SOURCE\nstatic char rollback_profile_path[128];\n#define WR_IOT_RADIO_PROFILE_PATH rollback_profile_path\n'+code).replace('int wr_iot_service_guard_dup(void){assert(0);return -1;}',
 'static int receipt_guard;\nint wr_iot_service_guard_enter(int on){assert(on==1&&!receipt_guard);receipt_guard=1;return 1;}\nint wr_iot_service_guard_dup(void){return receipt_guard?open("/dev/null",O_RDONLY):-1;}')
prepared_code=prepared_code.replace('void wr_iot_service_guard_leave(int token){(void)token;assert(0);}',
 'void wr_iot_service_guard_leave(int token){assert(token==1&&receipt_guard);receipt_guard=0;}')
prepared_code+='\nint wr_iot_generation_config_owned(const struct wr_iot_generation_config *p){return p&&p->owner==getpid()&&p->self==(uintptr_t)p&&p->created;}\nint wr_iot_generation_config_release(struct wr_iot_generation_config *p){(void)p;assert(0);return 0;}\n'
prepared_code=prepared_code.replace('int main(void){',r'''
static int rollback_partial(int mode){
 assert(mode==0&&receipt_guard);FILE *f=fopen(radio_off_profile_receipt.path,"w");
 assert(f&&fputs("partial generation\n",f)>=0&&!fclose(f));return -1;
}
int main(void){''')
needle='s->phase=WR_OFF_FOLLOWUP_DONE;wr_iot_rc_shutdown.radio_off_owned=0;return 1;'
assert needle in prepared_code
prepared_code=prepared_code.replace(needle, r'''snprintf(s->profile_receipt.path,sizeof(s->profile_receipt.path),"%s/profile",directory);
 strcpy(rollback_profile_path,s->profile_receipt.path);
 FILE *profile=fopen(s->profile_receipt.path,"w");assert(profile&&fputs("owned profile\n",profile)>=0&&!fclose(profile));
 assert(wr_iot_generated_capture(&s->profile_receipt.file,s->profile_receipt.path));
 s->profile_receipt.owner=getpid();s->profile_receipt.valid=1;
 s->phase=WR_OFF_FOLLOWUP_DONE;wr_iot_rc_shutdown.radio_off_owned=0;return 1;''')
needle='receipt.epoch++;assert(wr_iot_rc_radio_off_receipt(&receipt)&&receipt.epoch==1);'
assert needle in prepared_code
prepared_code=prepared_code.replace(needle,needle+r'''
 assert(!wr_iot_rc_radio_off_profile_current(&receipt));
 assert(wr_iot_service_guard_enter(1)==1&&wr_iot_rc_radio_off_profile_current(&receipt));
 struct wr_iot_physical_stop_request foreign=receipt;foreign.nonce[0]++;
 assert(!wr_iot_rc_radio_off_profile_current(&foreign));
 struct wr_iot_on_admission rollback={.owner=getpid(),.busy=1,.guard=1,
  .phase=WR_ON_ADMISSION_CAPTURED,.fence={.owner=getpid(),.level=1},.released=receipt};
 struct wr_iot_on_generation generation={.owner=getpid(),.phase=WR_ON_GEN_RESTORED,.admission=&rollback};
 generation.config_revision.owner=getpid();generation.config_revision.self=(uintptr_t)&generation.config_revision;
 generation.config_revision.created=receipt.closed_serial;
 strcpy(generation.config_revision.id,"11111111111111111111111111111111");
 assert(wr_iot_radio_profile_take(&rollback.profile));
 assert(!wr_iot_radio_profile_generate(&rollback.profile,rollback_partial));
 assert(wr_iot_radio_profile_restore(&rollback.profile));
 assert(!wr_iot_rc_radio_off_profile_current(&receipt)); /* Restore uses a new inode. */
 wr_iot_rc_shutdown.active=wr_iot_rc_shutdown.radio_on_owned=wr_iot_rc_shutdown.radio_off_owned=1;
 struct wr_iot_on_generation copied_generation=generation;
 assert(!wr_iot_rc_radio_on_rollback_receipt(&copied_generation));
 generation.main_may_have_started=1;assert(!wr_iot_rc_radio_on_rollback_receipt(&generation));generation.main_may_have_started=0;
 rollback.released.nonce[0]++;assert(!wr_iot_rc_radio_on_rollback_receipt(&generation));rollback.released.nonce[0]--;
 rollback.profile.files.saved[0].metadata.st_ino++;assert(!wr_iot_rc_radio_on_rollback_receipt(&generation));rollback.profile.files.saved[0].metadata.st_ino--;
 rollback.profile.files.saved[0].data[0]^=1;assert(!wr_iot_rc_radio_on_rollback_receipt(&generation));rollback.profile.files.saved[0].data[0]^=1;
 assert(wr_iot_rc_radio_on_rollback_receipt(&generation)&&wr_iot_rc_radio_off_profile_current(&receipt));
 assert(wr_iot_rc_radio_on_rollback_receipt(&generation)); /* Same guarded retry. */
 wr_iot_bundle_release(&rollback.profile.files);
 wr_iot_rc_shutdown.active=wr_iot_rc_shutdown.radio_on_owned=wr_iot_rc_shutdown.radio_off_owned=0;
 assert(!unlink(radio_off_profile_receipt.path));
 assert(!wr_iot_rc_radio_off_profile_current(&receipt));
 wr_iot_service_guard_leave(1);
''')
with tempfile.TemporaryDirectory(prefix='wr-rc-off-') as d:
 p=Path(d)/'check.c';b=Path(d)/'check'
 for prepared,fixture in ((0,code),(1,prepared_code)):
  p.write_text(fixture)
  subprocess.run(['gcc','-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED='+str(prepared),'-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'control-mailbox.c'),str(here/'status-endpoint.c'),str(here/'status-channel.c'),'-o',str(b)],check=True)
  subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual RC ppoll/OFF consumer prepared0/1: guarded profile receipt survives cleanup, wrong physical nonce/absent file/absent guard refused; policy and terminal ownership retained; SDK/physical/final actors injected')

print('PASS prepared RC rollback receipt: actual partial generation/rename restoration refreshes identity once; Main-start, wrong nonce, foreign baseline and mismatched bytes refuse; guarded retry idempotent')
