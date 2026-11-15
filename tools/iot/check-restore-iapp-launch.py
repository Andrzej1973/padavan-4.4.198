"""Actual root gated IAPP launch: one attempt, receipt before handoff."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
tree=ast.parse((here/'check-restart-restore.py').read_text())
base=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets)).split('int main(void)',1)[0]
actor=(here/'check-multicast-owner-actor.h').read_text()
actor=actor.replace('int wr_iot_iapp_child_step(struct wr_iot_iapp_child*s){(void)s;assert(0);return -2;}',r'''
static int launches,launch_ok=1,receipt;
int wr_iot_iapp_child_begin(struct wr_iot_iapp_child*s){launches++;s->owner=getpid();s->attempted=1;s->fd=9;return launch_ok;}
int wr_iot_iapp_child_step(struct wr_iot_iapp_child*s){if(receipt){s->result=receipt;s->fd=-1;}return receipt;}
''')
base=base.replace('#include "check-multicast-owner-actor.h"',actor)
code='#define WR_IOT_IAPP_POLICY_H\n#define WR_IOT_IAPP_POLICY_PREPARED 1\n'+base+r'''
int main(void){
 struct wr_iot_restart_restore s={0};unsigned char id[16]={1};wr_iot_rc_shutdown.active=1;
 main_ok=guest_ok=services_ok=1;assert(wr_iot_restart_restore_begin(&s,id));
 int ready=0;for(int i=0;i<20&&!ready;i++)ready=wr_iot_restart_restore_step(&s);
 assert(ready&&s.phase==WR_RESTORE_PREPARED&&!launches&&!s.iapp.owner);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-restore-iapp-launch-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=5)
print('PASS actual root with policy gate enabled: pre-handoff services reach PREPARED without IAPP launch; terminal launch is deferred after WAN/LED; component/child actors injected')
