"""Actual resume pump + RC backend/rebind owner/normal OFF; radio actors injected."""
from pathlib import Path
import subprocess,tempfile,sys
here=Path(__file__).resolve().parent
source=(here/'check-rc-rebind-shutdown.py').read_text();fixture={'__file__':str(here/'check-rc-rebind-shutdown.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<shutdown fixture>','exec'),fixture)
body=fixture['body']
hooks=r'''
#include "restart-resume.h"
int wr_iot_restart_restore_begin(struct wr_iot_restart_restore*s,const unsigned char*i){(void)s;(void)i;assert(0);return 0;}
int wr_iot_restart_restore_step(struct wr_iot_restart_restore*s){(void)s;assert(0);return 0;}
int wr_iot_restart_restore_handoff(struct wr_iot_restart_restore*s,const struct wr_iot_control_request*r){(void)s;(void)r;assert(0);return 0;}
int wr_iot_restart_restore_rebind_current(struct wr_iot_restart_restore*s){(void)s;assert(0);return 0;}
int wr_iot_rc_physical_resume_finish(struct wr_iot_restart_restore*s){(void)s;assert(0);return 0;}
int wr_iot_rc_physical_take(struct wr_iot_rc_physical_intent*i){(void)i;assert(0);return 0;}
int wr_iot_restart_guest_step(struct wr_iot_restart_guest*g){(void)g;return 0;}
int wr_iot_rc_physical_resume_cancel(struct wr_iot_restart_restore*s,const struct wr_iot_rc_quiesce*q){(void)s;(void)q;return 0;}
#include "restart-resume.c"
static int pump_advance(struct wr_iot_restart_resume*p,struct wr_iot_driver_closed_result*out){
 assert(!wr_iot_restart_resume_step(p));
 return p->shutdown.complete&&wr_iot_rc_backend_closed(out);
}
'''
body=body.replace('int main(void){',hooks+'\nint main(void){',1)
body=body.replace('struct wr_iot_rc_quiesce q={0};',r'''struct wr_iot_restart_resume pump={0};pump.owner=getpid();pump.created=on.created;pump.phase=WR_RESUME_REBIND;
 pump.restore.phase=WR_RESTORE_HANDOFF;memcpy(pump.restore.open_id,rebind.start.start.open_id,16);
#define q pump.shutdown
''')
body=body.replace('assert(wr_iot_rc_quiesce_shutdown_begin(&q,&off)&&!q.resume_needed&&q.active&&rebind.phase==WR_REBIND_OWNER_STOP);',r'''assert(wr_iot_restart_resume_shutdown(&pump,&off));
 assert(!wr_iot_restart_resume_step(&pump)&&q.active&&!q.resume_needed&&rebind.phase==WR_REBIND_OWNER_STOP);''')
body=body.replace('wr_iot_rc_quiesce_advance(&q,&receipt)','pump_advance(&pump,&receipt)')
body=body.replace(' puts("PASS actual RC rebind routing', ''' assert(pump.phase==WR_RESUME_SHUTDOWN_CLOSED&&!wr_iot_restart_resume_step(&pump));
 assert(submits==1&&closes==1&&progresses==1&&releases==1);
 puts("PASS actual RC rebind routing''')
with tempfile.TemporaryDirectory(prefix='wr-pump-backend-shutdown-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(fixture['ns']['prefix']+'\n#include "check-reopen-unused.h"\n'+body.replace('#include "rc-backend.c"','#include "check-legacy-start-unused.h"\n#include "rc-backend.c"'))
 binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in fixture['units']],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
print('PASS actual pump/backend/rebind/OFF composition: pending shutdown closes once, isolation refusal retains ownership, exact CLOSED, no OPEN replay or ordinary finish; radio/network/final cancellation gate actors injected')
