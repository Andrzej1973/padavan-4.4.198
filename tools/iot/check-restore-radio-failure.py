"""Actual root refuses Main after uncertain RAM state submission."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
tree=ast.parse((here/'check-restart-restore.py').read_text())
code=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets))
code=code.split('int main(void)',1)[0]
old='int wr_iot_rc_restart_radio_state(int reload){assert(reload==0||reload==1);return 1;}'
assert code.count(old)==1
code=code.replace(old,'static int state_calls;\nint wr_iot_rc_restart_radio_state(int reload){assert(reload==0||reload==1);state_calls++;return 0;}')
code+=r'''
int main(void){
 struct wr_iot_restart_restore s={0};unsigned char id[16]={1};wr_iot_rc_shutdown.active=1;
 assert(wr_iot_restart_restore_begin(&s,id));assert(!wr_iot_restart_restore_step(&s));
 assert(!wr_iot_restart_restore_step(&s)&&state_calls==1&&!ups&&s.radio_state_attempted&&s.phase==WR_RESTORE_RETAINED);
 for(int i=0;i<4;i++)assert(!wr_iot_restart_restore_step(&s)&&state_calls==1&&!ups);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-radio-failure-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual restore radio-state failure: attempt marked before call, retained once, zero Main UP and no setter replay; component actors injected')
