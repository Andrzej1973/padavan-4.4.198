"""Actual restore drains retained IAPP receipt before shutdown cancellation."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
tree=ast.parse((here/'check-restart-restore.py').read_text())
code=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets))
code=code.split('int main(void)',1)[0]
actor=(here/'check-multicast-owner-actor.h').read_text()
old='int wr_iot_iapp_child_step(struct wr_iot_iapp_child*s){(void)s;assert(0);return -2;}'
assert actor.count(old)==1
actor=actor.replace(old,'static int receipts,outcome;\nint wr_iot_iapp_child_step(struct wr_iot_iapp_child*s){receipts++;if(s->result)return s->result;if(outcome){s->result=outcome;s->fd=-1;}return outcome;}')
code=code.replace('#include "check-multicast-owner-actor.h"',actor)
code+=r'''
int main(void){
 struct wr_iot_restart_restore s={0};unsigned char id[16]={1};wr_iot_rc_shutdown.active=1;
 assert(wr_iot_restart_restore_begin(&s,id));
 s.iapp=(struct wr_iot_iapp_child){.owner=getpid(),.attempted=1,.fd=9};
 wr_iot_rc_shutdown.pending=SIGTERM;
 assert(!wr_iot_restart_restore_step(&s)&&receipts==1&&!ups&&!guest_calls);
 outcome=-2;assert(!wr_iot_restart_restore_step(&s)&&receipts==2&&!wr_iot_iapp_child_closed(&s.iapp));
 assert(!wr_iot_restart_restore_step(&s)&&receipts==3&&!ups&&!guest_calls);
 outcome=-1;assert(!wr_iot_restart_restore_step(&s)&&receipts==4&&!wr_iot_iapp_child_closed(&s.iapp));
 /* Separate fixture scenario: a still-pending child delivers confirmed failure. */
 s.iapp.result=0;s.iapp.fd=9;
 assert(!wr_iot_restart_restore_step(&s)&&receipts==5&&wr_iot_iapp_child_closed(&s.iapp));
 assert(!wr_iot_restart_restore_step(&s)&&receipts==5&&!ups);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-restore-iapp-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=5)
print('PASS actual restore IAPP drain: pending shutdown reads existing receipt before other work, unknown retains, confirmed failure closes without another launch; child/component actors injected')
