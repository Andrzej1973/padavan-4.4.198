"""Actual pump and retire candidate across terminal reuse; components injected."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
tree=ast.parse((here/'check-restart-resume.py').read_text())
code=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets))
code=code.split('int main(void)',1)[0]
code=code.replace('if(finish_ok)s->phase=WR_RESTORE_FINISHED;', 'if(finish_ok){s->phase=WR_RESTORE_FINISHED;s->generation.phase=WR_RESTART_GEN_COMMITTED;wr_iot_rc_shutdown.active=0;wr_iot_rc_shutdown.pending=0;}')
code+=r'''
#include "restart-resume-retire.c"
int main(void){
 struct wr_iot_restart_resume s={0};unsigned char id[16]={7};
 for(int cycle=0;cycle<2;cycle++){
  wr_iot_rc_shutdown.active=1;prepared=active=finish_ok=0;take_ok=1;
  assert(wr_iot_restart_resume_begin(&s,id,10));
  assert(!wr_iot_restart_resume_retire(&s));
  prepared=1;assert(!wr_iot_restart_resume_step(&s));
  active=1;assert(!wr_iot_restart_resume_step(&s));
  finish_ok=1;assert(wr_iot_restart_resume_step(&s)&&s.phase==WR_RESUME_DONE);
  int prior=begins;assert(wr_iot_restart_resume_retire(&s)&&!s.owner&&!s.restore.owner);
  assert(!wr_iot_restart_resume_retire(&s)&&begins==prior);
 }
 assert(begins==2&&handoffs==2&&finishes==2&&takes==2);
 puts("PASS actual resume pump/retire reuse: two terminal cycles at same address, no retirement while live, no retained identity/credential context, each begin/handoff/finish/take once; component actors injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-resume-reuse-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
