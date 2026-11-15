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
 for(int outcome=0;outcome<3;outcome++){
  struct wr_iot_restart_restore s={0};unsigned char id[16]={1};phase=0;launches=0;receipt=0;launch_ok=outcome!=2;
  main_ok=guest_ok=services_ok=1;wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=0;
  assert(wr_iot_restart_restore_begin(&s,id));
  for(int i=0;i<15&&!launches;i++)assert(!wr_iot_restart_restore_step(&s));
  assert(launches==1&&s.iapp_launch_attempted&&s.phase!=WR_RESTORE_PREPARED);
  for(int i=0;i<3;i++)assert(!wr_iot_restart_restore_step(&s)&&launches==1);
  if(outcome==2){assert(s.phase==WR_RESTORE_SERVICE_WAIT);continue;}
  receipt=outcome==0?1:-1;assert(!wr_iot_restart_restore_step(&s));
  assert(wr_iot_restart_restore_step(&s)==(outcome==0)&&launches==1);
  if(outcome==0)assert(s.phase==WR_RESTORE_PREPARED);
  else assert(s.phase!=WR_RESTORE_PREPARED);
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-restore-iapp-launch-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=5)
print('PASS actual root with policy gate enabled: one launch after services, pending holds, success alone permits PREPARED, command/admission failure no replay; component/child actors injected')
