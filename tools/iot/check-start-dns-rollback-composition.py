#!/usr/bin/env python3
"""Actual startup/snapshot/CLOSED rollback plus installed DNS recovery chain."""
import ast
from pathlib import Path
import subprocess,sys,tempfile
here=Path(__file__).resolve().parent
fixture=(here/'check-start-closed-rollback-composition.c').read_text()
fixture='\n'.join(line for line in fixture.splitlines() if not line.startswith(('static int rollback_dns,','int wr_iot_dns_activation_recovery_state(', 'int wr_iot_dns_activation_abort(')))+'\n'
module=ast.parse((here/'check-dns-abort-composition.py').read_text())
prefix=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prefix' for t in n.targets))
prefix='\n'.join(line for line in prefix.splitlines() if not line.startswith(('static int wr_iot_service_guard_dup(', 'static int close(', 'static void wr_iot_service_guard_leave(')))+'\n'
prefix=prefix.replace(',guard_leaves;', ';')
source=(here/'restart-controller.inc').read_text()
def function(signature):
 start=source.index(signature);end=source.index('{',start)+1;depth=1
 while depth:
  depth+=(source[end]=='{')-(source[end]=='}');end+=1
 return source[start:end]
prefix+='\n'.join(function(s) for s in ('static int wr_iot_restart_finish(void)','static int wr_iot_restart_recover(void)','int wr_iot_dns_activation_recovery_state(void)','int wr_iot_dns_activation_abort(void)'))
for name in ('wr_iot_generated_capture','wr_iot_saved_restore','wr_iot_saved_release'):
 prefix=prefix.replace(name,'fixture_'+name)
fixture=fixture.replace('int main(void){',prefix+'\nint main(void){')
fixture=fixture.replace('reset();idle_reads=0;abort_calls=0;rollback_dns=1;', '''reset();idle_reads=0;
  fault=0;stops=restores=captures=launches=releases=0;running=1;
  wr_iot_restart_active=wr_iot_restart_guard=wr_iot_restart_bound=wr_iot_restart_prepared=1;
  wr_iot_restart_state.transaction.active=1;wr_iot_restart_disabling=0;
  wr_iot_restart_stopped_candidate=0;wr_iot_restart_old_running=1;
  wr_iot_restart_lease_captured=wr_iot_restart_lease_owned=1;
  wr_iot_restart_lease_observed=wr_iot_restart_lease_restored=0;''')
anchor='  while(rollback.phase<WR_IOT_ROLL_SETTINGS)'
idx=fixture.index(anchor)
fixture=fixture[:idx]+'''  assert(wr_iot_service_guard_enter(1)==1&&depth==2);
  while(rollback.phase<WR_IOT_ROLL_DNS)assert(!wr_iot_start_closed_rollback_step(&rollback,&network,&owner,&open,&closed));
  fault=failure%9;
  if(fault){
   assert(!wr_iot_start_closed_rollback_step(&rollback,&network,&owner,&open,&closed));
   assert(rollback.phase==WR_IOT_ROLL_DNS&&depth==2&&owner.snapshot.active&&wr_iot_restart_active);
   fault=0;
  }
'''+fixture[idx:]
fixture=fixture.replace('!bridge_index&&!rollback_dns&&abort_calls==1&&depth==1','!bridge_index&&!wr_iot_restart_active&&stops==1&&releases==1&&depth==1')
fixture=fixture.replace('DNS/bridge/driver hooks injected','actual DNS abort/recover/finish; file/daemon/bridge/driver operations injected')
with tempfile.TemporaryDirectory(prefix='iot-start-dns-rollback-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(fixture);binary=Path(d)/'check'
 units=('start-closed-rollback.c','start-close.c','start-admission.c','request-stage.c','request-snapshot.c','disable-services.c','disable-controller.c','profile.c')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
