#!/usr/bin/env python3
"""Actual initial OFF -> first ON -> requested OFF owner composition."""
from pathlib import Path
import ast,subprocess,sys,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-activation-owner-composition.py').read_text()
body=next(ast.literal_eval(n.value) for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='body' for t in n.targets))
prefix=(here/'check-start-closed-rollback-composition.c').read_text().split('int main(void){',1)[0]
prefix='\n'.join(line for line in prefix.splitlines() if not line.startswith(('int wr_iot_open_controller_recovery_read(', 'int wr_iot_close_controller_begin(', 'int wr_iot_close_controller_advance(')))+'\n'
prefix+=(here/'check-driver-close-controller.c').read_text().split('int main(void)',1)[0]
observer_source=(here/'check-activation-observe-composition.py').read_text()
hooks=next(ast.literal_eval(n.value) for n in ast.parse(observer_source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='hooks' for t in n.targets))
body=body.replace('#include "activation-owner.h"','#include "activation-observe.h"')
body=body.replace('s->phase=WR_IOT_COMMIT_ACTIVE;return 1;','s->owner=getpid();s->open_token=3;s->phase=WR_IOT_COMMIT_ACTIVE;return 1;')
body=body.replace('int main(void){',hooks+'int main(void){',1)
anchor='  assert(wr_iot_activation_owner_execute(&owner,&input,1,1,0)==WR_IOT_RESULT_RECOVERY&&depth==1);'
assert anchor in body
body=body.replace(anchor,r'''  for(unsigned i=7;i<16;i++)strcpy(values[i].value,i<10?"0":"");
  struct wr_iot_control_request cold={.id="01020202020202020202020202020202",.created=1};
  int writes_before=writes;
  assert(wr_iot_activation_owner_execute(&owner,&cold,1,1,0)==WR_IOT_RESULT_APPLIED&&!depth&&writes==writes_before);
  assert(owner.phase==WR_IOT_OWNER_INITIAL_OFF);
  struct wr_iot_control_result observed={.state=WR_IOT_RESULT_APPLIED,.created=1};strcpy(observed.id,cold.id);
  assert(wr_iot_activation_owner_observed(&owner,&observed)&&!depth);
  assert(wr_iot_activation_owner_continue(&owner,cold.id,1)==WR_IOT_RESULT_APPLIED);
  assert(wr_iot_activation_owner_execute(&owner,&cold,1,1,0)==WR_IOT_RESULT_REJECTED&&!depth);
  strcpy(values[8].value,"1");assert(!wr_iot_activation_owner_observed(&owner,&observed));strcpy(values[8].value,"0");
'''+anchor)
anchor='  assert(!depth&&s.admission.snapshot.active&&!s.admission.snapshot.token);'
body=body.replace(anchor,anchor+'\n  assert(!wr_iot_activation_owner_observed(&owner,&observed));')
body=body.replace('PASS retained activation owner with actual runner/admission/snapshot/normal OFF:', 'PASS actual owner initial OFF/live observation -> first ON -> normal OFF:')
with tempfile.TemporaryDirectory(prefix='iot-initial-off-owner-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(prefix+'\n#include "check-reopen-unused.h"\n'+body);binary=Path(d)/'check'
 units=('activation-observe.c','initial-off.c','activation-owner.c','active-stop.c','start-runner.c','start-network-rollback.c','start-close.c','start-closed-rollback.c','precreated-stop.c','start-admission.c','request-stage.c','request-snapshot.c','disable-services.c','disable-controller.c','profile.c')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
