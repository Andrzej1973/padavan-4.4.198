"""Actual RC wait/scheduler RELEASE-to-fresh-begin composition."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-rc-scheduler-composition.py').read_text()
ns={'__file__':str(here/'check-rc-scheduler-composition.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<RC composition fixture>','exec'),ns)
code=ns['code']
old='unsigned char resume_id[16]={7};assert(wr_iot_restart_scheduler_begin(resume_id,10));'
assert code.count(old)==1
code=code.replace(old,'')
old='#include "restart-scheduler.c"'
assert code.count(old)==1
code=code.replace(old,'''static int entropy_ready;
static int auto_entropy(void*b,unsigned n,unsigned f){assert(n==32&&f==1);memset(b,7,n);return entropy_ready?32:-1;}
#define WR_IOT_GETRANDOM(b,n,f) auto_entropy(b,n,f)
#include "restart-scheduler.c"''')
old='assert(resume_steps==1&&steps==2);'
assert code.count(old)==1
code=code.replace(old,'''assert(!resume.owner&&!resume_steps&&steps==2&&wr_iot_restart_scheduler_pending());
 entropy_ready=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(resume.owner&&!resume_steps&&steps==2);
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(resume_steps==1&&steps==2);''')
with tempfile.TemporaryDirectory(prefix='wr-rc-resume-auto-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'control-mailbox.c'),str(here/'status-endpoint.c'),str(here/'status-channel.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual RC/scheduler RELEASE-to-fresh-begin: entropy refusal holds ordinary path, next tick begins once, later tick advances resume; physical priority/status/signal wake retained; physical/resume owner actors injected')
