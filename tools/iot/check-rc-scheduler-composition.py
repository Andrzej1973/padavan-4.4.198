"""Actual ppoll RC runtime + private scheduler; resume owner actor injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=(here/'check-rc-runtime.c').read_text()
def replace_once(text, old, new):
 assert text.count(old)==1, 'RC fixture anchor changed: '+old
 return text.replace(old,new,1)
code=replace_once(code,'int wr_iot_restart_scheduler_pending(void){return resume_pending;}','')
code=replace_once(code,'int wr_iot_restart_scheduler_step(void){resume_steps++;return 0;}','''#include "restart-resume.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
int wr_iot_rc_physical_restart_ready(struct wr_iot_rc_physical_intent*i){i->restart=i->radio_on=1;return 1;}
int wr_iot_restart_resume_begin(struct wr_iot_restart_resume*s,const unsigned char*id,unsigned long long created){assert(id[0]&&created);s->owner=getpid();s->phase=WR_RESUME_RESTORE;return 1;}
int wr_iot_restart_resume_step(struct wr_iot_restart_resume*s){assert(s->owner==getpid());resume_steps++;return 0;}
int wr_iot_restart_resume_shutdown(struct wr_iot_restart_resume*s,const struct wr_iot_control_request*r){(void)s;(void)r;assert(0);return 0;}
int wr_iot_restart_resume_retire(struct wr_iot_restart_resume*s){(void)s;assert(0);return 0;}
#include "restart-scheduler.c"
''')
code=replace_once(code,'resume_pending=pending=1;', 'resume_pending=pending=1;wr_iot_rc_shutdown.active=1;unsigned char resume_id[16]={7};assert(wr_iot_restart_scheduler_begin(resume_id,10));')
code=replace_once(code,'resume_pending=pending=0;', 'resume_pending=pending=0;resume.phase=WR_RESUME_DONE;')
with tempfile.TemporaryDirectory(prefix='wr-rc-scheduler-compose-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'control-mailbox.c'),str(here/'status-endpoint.c'),str(here/'status-channel.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual RC ppoll/private scheduler composition: physical priority then stable resume, ordinary commands held,100ms cadence, status endpoint and signal wake retained; resume owner actor injected')
