"""Actual physical admission/scheduler/retirement composition, no hardware."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=(here/'check-rc-physical-stop.c').read_text().split('int main(void)',1)[0]
old='static int scheduler_refuse,scheduler_prepares;\nint wr_iot_restart_scheduler_prepare(void){assert(!depth&&!wr_iot_rc_shutdown.active);scheduler_prepares++;return !scheduler_refuse;}'
assert code.count(old)==1;code=code.replace(old,'')
code+=r'''
#include "restart-scheduler.c"
#include "restart-resume-retire.c"
int wr_iot_restart_resume_begin(struct wr_iot_restart_resume*s,const unsigned char*i,unsigned long long t){(void)s;(void)i;(void)t;assert(0);return 0;}
int wr_iot_restart_resume_step(struct wr_iot_restart_resume*s){(void)s;assert(0);return 0;}
int wr_iot_restart_resume_shutdown(struct wr_iot_restart_resume*s,const struct wr_iot_control_request*r){(void)s;(void)r;assert(0);return 0;}
int main(void){
 (void)handler;struct wr_iot_rc_physical_intent intent={0},out={0};
 resume.owner=getpid();resume.phase=WR_RESUME_RETAINED;
 assert(!wr_iot_rc_physical_begin(&intent)&&!physical.owner&&!depth&&!calls&&!downs&&!wr_iot_rc_shutdown.active);
 resume.phase=WR_RESUME_DONE;resume.restore.owner=getpid();resume.restore.phase=WR_RESTORE_FINISHED;
 resume.restore.generation.phase=WR_RESTART_GEN_COMMITTED;resume.restore.generation.profile.active=1;
 assert(!wr_iot_rc_physical_begin(&intent)&&resume.owner&&!physical.owner&&!depth);
 resume.restore.generation.profile.active=0;entropy_fail=1;
 assert(wr_iot_rc_physical_begin(&intent)&&!resume.owner&&physical.owner&&wr_iot_rc_shutdown.active);
 wr_iot_rc_physical_step();assert(wr_iot_rc_physical_take(&out)==-1&&!depth&&!wr_iot_rc_shutdown.active);
 assert(wr_iot_restart_scheduler_prepare());
}
'''
with tempfile.TemporaryDirectory(prefix='wr-physical-scheduler-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual physical begin/scheduler/retirement: uncertain/live-profile refuse before fence/owner/driver, terminal retires before new admission, later preparation refusal balances fence; hardware/backend actors injected')
