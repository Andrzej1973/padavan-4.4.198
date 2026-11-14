"""Actual successful/failed ARM terminal replacement with PID reference checks."""
from pathlib import Path
import runpy,subprocess,tempfile
here=Path(__file__).resolve().parent
base=runpy.run_path(str(here/'check-physical-stop-cancel.py'))
context=base['context'].replace('int main(void){','#include "physical-stop-terminal-replace.inc"\nint main(void){')
body=base['body'];old=''' assert(wr_iot_physical_stop_terminal_clear(&ad.wr_iot_physical_terminal));
 assert(identity.refs==1&&!ad.wr_iot_physical_terminal.owner);'''
new=r'''
 {struct wr_iot_physical_stop_request next=arm;
  unsigned long next_serial=77;
  assert(wr_iot_physical_stop_arm_replace_terminal(&ad,&main_dev,&next,&next_serial)==-EBUSY);
  assert(identity.refs==2&&next_serial==77);
  next.nonce[0]++;
  next.open_token++;
  assert(wr_iot_physical_stop_arm_replace_terminal(&ad,&main_dev,&next,&next_serial)<0);
  assert(identity.refs==2&&ad.wr_iot_physical_terminal.ready&&next_serial==77);
  assert(wr_iot_physical_stop_terminal_reply(&ad.wr_iot_physical_terminal,
    &cancel,wire,sizeof(wire)));
  next.open_token--;
  assert(!wr_iot_physical_stop_arm_replace_terminal(&ad,&main_dev,&next,&next_serial));
  assert(identity.refs==1&&!ad.wr_iot_physical_terminal.owner&&next_serial==2);
  assert(ad.wr_iot_physical_lifetime.active);
  assert(!wr_iot_physical_stop_arm_abort_unpublished(&ad,&main_dev,next_serial));
  assert(!ad.wr_iot_physical_lifetime.active);
 }
'''
assert old in body;body=body.replace(old,new)
with tempfile.TemporaryDirectory(prefix='wr-stop-terminal-replace-') as d:
 c=Path(d)/'check.c';c.write_text(base['base']['base']['prefix']+context+body)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS actual terminal replacement: same nonce refuses, failed ARM restores cached reply/PID, accepted ARM returns old PID exactly once; target/runtime pending')
