"""Actual ppoll RC runtime + private scheduler; resume owner actor injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code='#define WR_IOT_RUNTIME_FIXTURE_EXTERNAL_ADMISSION\n'+(here/'check-rc-runtime.c').read_text()
def replace_once(text, old, new):
 assert text.count(old)==1, 'RC fixture anchor changed: '+old
 return text.replace(old,new,1)
code=replace_once(code,'int wr_iot_restart_scheduler_retire(void){assert(0);return 0;}','')
code=replace_once(code,'int wr_iot_restart_scheduler_pending(void){return resume_pending;}','')
code=replace_once(code,'int wr_iot_restart_scheduler_step(void){resume_steps++;return 0;}','''#include "restart-resume.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
int wr_iot_rc_physical_restart_ready(struct wr_iot_rc_physical_intent*i){i->restart=i->radio_on=1;return 1;}
int wr_iot_restart_resume_begin(struct wr_iot_restart_resume*s,const unsigned char*id,unsigned long long created){assert(id[0]&&created);s->owner=getpid();s->phase=WR_RESUME_RESTORE;return 1;}
static int retire_ok,retire_calls;
int wr_iot_restart_resume_step(struct wr_iot_restart_resume*s){assert(s->owner==getpid());resume_steps++;return s->phase==WR_RESUME_CANCELLED?-1:s->phase==WR_RESUME_DONE;}
int wr_iot_restart_resume_shutdown(struct wr_iot_restart_resume*s,const struct wr_iot_control_request*r){(void)s;(void)r;assert(0);return 0;}
int wr_iot_restart_resume_retire_for_off(struct wr_iot_restart_resume*s){(void)s;assert(0);return 0;}
int wr_iot_restart_resume_retire(struct wr_iot_restart_resume*s){assert(s->phase==WR_RESUME_DONE||s->phase==WR_RESUME_CANCELLED);retire_calls++;if(!retire_ok)return 0;memset(s,0,sizeof(*s));return 1;}
int wr_iot_rc_physical_preresume_cancel(void){assert(0);return 0;}
int wr_iot_rc_physical_take(struct wr_iot_rc_physical_intent*i){(void)i;assert(0);return 0;}
#include "restart-scheduler.c"
''')
code=replace_once(code,'resume_pending=pending=1;', 'resume_pending=pending=1;wr_iot_rc_shutdown.active=1;unsigned char resume_id[16]={7};assert(wr_iot_restart_scheduler_begin(resume_id,10));')
code=replace_once(code,'resume_pending=pending=0;', 'resume_pending=pending=0;resume.phase=WR_RESUME_DONE;')
code=replace_once(code,'int wr_iot_rc_dispatch(void){assert(0);return 0;}','static int dispatches;int wr_iot_rc_dispatch(void){dispatches++;return 1;}')
code=replace_once(code,' normal_pending=1;notification=1;',r'''
 wr_iot_rc_shutdown.active=0;
 assert(wr_iot_restart_scheduler_pending());
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(retire_calls==1&&resume.owner&&!dispatches);
 retire_ok=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(retire_calls==2&&!resume.owner&&radio_off_redispatch);
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(dispatches==1&&!radio_off_redispatch&&!wr_iot_restart_scheduler_pending());
 resume.owner=getpid();resume.phase=WR_RESUME_CANCELLED;
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(retire_calls==3&&!resume.owner&&radio_off_redispatch);
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(dispatches==2&&!radio_off_redispatch);

 radio_off_redispatch=1;normal_pending=1;
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(normal_steps==1&&dispatches==2&&radio_off_redispatch);
 normal_pending=0;
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(dispatches==3&&!radio_off_redispatch);
 normal_steps=0;
 normal_pending=1;notification=1;
''')
with tempfile.TemporaryDirectory(prefix='wr-rc-scheduler-compose-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'control-mailbox.c'),str(here/'status-endpoint.c'),str(here/'status-channel.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual RC ppoll/private scheduler composition: physical priority then stable resume, ordinary commands held,100ms cadence, failed retirement retries, DONE/cancellation retire then one deferred redispatch, status/signal wake retained; resume owner actor injected')
