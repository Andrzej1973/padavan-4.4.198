"""Actual resume plus WAN controller; dispatch only after successful take."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
tree=ast.parse((here/'check-restart-resume.py').read_text())
code=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets)).split('int main(void)',1)[0]
code=code.replace('if(finish_ok)s->phase=WR_RESTORE_FINISHED;','if(finish_ok){s->phase=WR_RESTORE_FINISHED;wr_iot_rc_shutdown.active=0;}')
code='#define WR_IOT_IAPP_POLICY_H\n#define WR_IOT_IAPP_POLICY_PREPARED 1\n'+code
code+=r'''
static int dispatches;
int wr_iot_rc_restart_wan_current(int on,enum wr_iot_wan_followup p){return on==1&&p==WR_WAN_RECONNECT;}
int wr_iot_rc_restart_wan_plan(int on,enum wr_iot_wan_followup*out){assert(on==1);*out=WR_WAN_RECONNECT;return 1;}
void wr_iot_rc_restart_wan_submit(enum wr_iot_wan_followup p){assert(p==WR_WAN_RECONNECT&&!wr_iot_rc_shutdown.active&&takes==2);dispatches++;}
#include "restart-wan-followup.c"
int main(void){
 struct wr_iot_restart_resume s={0};unsigned char id[16]={7};wr_iot_rc_shutdown.active=1;
 assert(wr_iot_restart_resume_begin(&s,id,10));prepared=active=finish_ok=1;
 assert(!wr_iot_restart_resume_step(&s)&&s.phase==WR_RESUME_REBIND);
 assert(!wr_iot_restart_resume_step(&s)&&s.phase==WR_RESUME_FINISH);
 take_ok=0;assert(!wr_iot_restart_resume_step(&s)&&takes==1&&!dispatches&&s.wan.owner);
 take_ok=1;assert(!wr_iot_restart_resume_step(&s)&&takes==2&&!dispatches&&s.phase==WR_RESUME_WAN);
 wr_iot_rc_shutdown.active=1;assert(!wr_iot_restart_resume_step(&s)&&takes==2&&!dispatches);wr_iot_rc_shutdown.active=0;
 wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_restart_resume_step(&s)&&!dispatches);wr_iot_rc_shutdown.pending=0;
 assert(wr_iot_restart_resume_step(&s)&&dispatches==1&&s.phase==WR_RESUME_DONE);
 assert(wr_iot_restart_resume_step(&s)&&dispatches==1&&takes==2);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-resume-wan-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=5)
print('PASS actual resume/WAN controller: capture before cleanup, failed take holds, successful take once enters deferred phase, active/pending block, one SDK dispatch then DONE; physical/SDK actors injected')
