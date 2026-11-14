"""Actual scheduler/pump/retirement repeated lifecycle, component actors injected."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
tree=ast.parse((here/'check-resume-retire-composition.py').read_text())
# Reuse only setup code; no subprocess or fixture execution during assembly.
source=(here/'check-resume-retire-composition.py').read_text();ns={'__file__':str(here/'check-resume-retire-composition.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<reuse fixture>','exec'),ns)
code=ns['code'].split('int main(void)',1)[0]+r'''
static int ready;
int wr_iot_rc_physical_restart_ready(struct wr_iot_rc_physical_intent*i){i->restart=i->radio_on=1;return ready;}
#include "restart-scheduler.c"
int main(void){
 unsigned char id[16]={7};
 assert(wr_iot_restart_scheduler_prepare());wr_iot_rc_shutdown.active=1;
 assert(!wr_iot_restart_scheduler_prepare());
 assert(!wr_iot_restart_scheduler_begin(id,10)&&!begins);ready=1;
 for(int cycle=0;cycle<2;cycle++){
  wr_iot_rc_shutdown.active=1;prepared=active=finish_ok=0;take_ok=1;
  assert(wr_iot_restart_scheduler_begin(id,10));
  assert(wr_iot_restart_scheduler_pending()&&!wr_iot_restart_scheduler_retire()&&!wr_iot_restart_scheduler_prepare());
  assert(!wr_iot_restart_scheduler_begin(id,11));prepared=1;
  assert(!wr_iot_restart_scheduler_step());active=1;
  assert(!wr_iot_restart_scheduler_step());finish_ok=1;
  assert(wr_iot_restart_scheduler_step()&&!wr_iot_restart_scheduler_pending());
  assert(!wr_iot_rc_shutdown.active);
  resume.restore.generation.profile.active=1;
  assert(!wr_iot_restart_scheduler_prepare()&&resume.owner);
  resume.restore.generation.profile.active=0;
  assert(wr_iot_restart_scheduler_prepare()&&!resume.owner);
  assert(wr_iot_restart_scheduler_prepare());
 }
 assert(begins==2&&handoffs==2&&finishes==2&&takes==2);
 puts("PASS actual scheduler/resume/retirement composition: physical ready gate, one static owner, live retirement/duplicate begin refuse, two completed cycles and reuse; component actors injected, no RC hook");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-scheduler-compose-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
