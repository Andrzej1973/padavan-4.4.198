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
code=code.replace('int wr_iot_off_followup_begin(struct wr_iot_off_followup*s,const struct wr_iot_radio_off_owner*o){(void)s;(void)o;assert(0);return 0;}', 'static int followup_begins,followup_steps;\nint wr_iot_off_followup_begin(struct wr_iot_off_followup*s,const struct wr_iot_radio_off_owner*o){assert(o==&radio_off_owner&&o->result==1&&!physical_pending);followup_begins++;s->owner=getpid();s->phase=WR_OFF_FOLLOWUP_PROFILE_BEGIN;return 1;}')
code=code.replace('enum wr_iot_off_followup_phase wr_iot_off_followup_step(struct wr_iot_off_followup*s){(void)s;assert(0);return WR_OFF_FOLLOWUP_IDLE;}', 'enum wr_iot_off_followup_phase wr_iot_off_followup_step(struct wr_iot_off_followup*s){assert(s->owner==getpid()&&followup_begins==1);followup_steps++;s->phase=WR_OFF_FOLLOWUP_NETWORK_PENDING;return s->phase;}')
code=code.replace('void wr_iot_rc_physical_step(void){physical_steps++;}', 'void wr_iot_rc_physical_step(void){physical_steps++;if(off_transport){assert(policy_reads&&policy_allowed);physical_pending=0;wr_iot_rc_shutdown.active=0;off_terminal=1;}}')
a=' assert(wr_iot_status_endpoint_close(&endpoint));'
assert code.count(a)==1
code=code.replace(a,r'''
 struct wr_iot_control_request off={.id="11111111111111111111111111111111",.created=7};
 off_base=physical_steps;int ordinary=steps,scheduled=resume_steps;
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


 pending=resume_pending=0;notification=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(physical_steps==off_base+1&&policy_reads==2);notification=0;
'''+a)
with tempfile.TemporaryDirectory(prefix='wr-rc-off-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'control-mailbox.c'),str(here/'status-endpoint.c'),str(here/'status-channel.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual RC ppoll/OFF consumer: policy refusal prevents physical bypass, one physical step per cadence, OFF priority over resume/ordinary, retained terminal no replay/new admission; SDK/physical actors injected, entry unbound')
