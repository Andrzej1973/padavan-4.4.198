"""Actual adapter CANCEL cleanup and retained typed reply, host kernel mocks."""
from pathlib import Path
import runpy,subprocess,tempfile
here=Path(__file__).resolve().parent
base=runpy.run_path(str(here/'check-physical-stop-arm-publication.py'))
context=base['context'].replace('int main(void){',r'''
struct pid {int refs;};static struct pid identity={1};
static struct pid *task_pid(struct task_struct *t){assert(t==current);return &identity;}
static struct pid *get_pid(struct pid *p){assert(p==&identity&&!held);p->refs++;return p;}
static void put_pid(struct pid *p){assert(p==&identity&&!held&&p->refs>1);p->refs--;}
#include "physical-stop-terminal.inc"
#include "physical-stop-cancel.inc"
int main(void){''')
body=base['body'].replace(' struct wr_iot_physical_stop_pins detached={0};','');anchor=' assert(wr_iot_physical_stop_arm_abort_unpublished(&ad,&main_dev,serial)==-EBUSY);'
body=body[:body.index(anchor)]+r'''
 struct wr_iot_physical_stop_terminal terminal={0};
 struct wr_iot_physical_stop_request cancel=arm;
 unsigned char wire[64];struct wr_iot_physical_stop_response response;
 cancel.action=WR_STOP_CANCEL;cancel.attempt=attempt;
 ad.wr_iot_interface_refs[0].generation++;
 assert(wr_iot_physical_stop_cancel_owned(&ad,&main_dev,&cancel,serial,&terminal)==-EBUSY);
 assert(identity.refs==1&&!terminal.owner&&modules==2&&!held);
 ad.wr_iot_interface_refs[0].generation--;
 ad.wr_iot_physical_stop.phase=WR_PHYS_STOP_RUNNING;
 assert(wr_iot_physical_stop_cancel_owned(&ad,&main_dev,&cancel,serial,&terminal)==-EBUSY);
 assert(identity.refs==1&&!terminal.owner&&ad.wr_iot_physical_lifetime.active);
 ad.wr_iot_physical_stop.phase=WR_PHYS_STOP_ARMED;
 assert(!wr_iot_physical_stop_cancel_owned(&ad,&main_dev,&cancel,serial,&terminal));
 assert(!ad.wr_iot_physical_lifetime.active&&modules==1&&tasks==1&&devices==1);
 assert(terminal.ready&&identity.refs==2);
 for(unsigned retry=0;retry<3;retry++){
  assert(wr_iot_physical_stop_terminal_reply(&terminal,&cancel,wire,sizeof(wire)));
  assert(wr_iot_physical_stop_response_decode(&response,wire,sizeof(wire),&cancel));
  assert(response.status==WR_STOP_CANCELLED);
  assert(modules==1&&tasks==1&&devices==1&&identity.refs==2);
 }
 assert(wr_iot_physical_stop_terminal_clear(&terminal));
 assert(identity.refs==1&&!terminal.owner);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-stop-cancel-') as d:
 c=Path(d)/'check.c';c.write_text(base['base']['prefix']+context+body)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS actual CANCEL: Main drift/RUNNING refuse without leaks, extras returned before lifetime end, retained reply survives lost copy retries; kernel ops injected')
