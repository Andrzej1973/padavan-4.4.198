#!/usr/bin/env python3
"""Actual DNS commit/finish composed with startup and snapshot suspension."""
import ast
from pathlib import Path
import subprocess,sys,tempfile
here=Path(__file__).resolve().parent
fixture=(here/'check-start-commit-composition.c').read_text()
fixture='\n'.join(line for line in fixture.splitlines() if not line.startswith(('int wr_iot_dns_activation_recovery_state(', 'int wr_iot_dns_activation_commit(')))+'\n'
fixture=fixture.replace('static int dns=1,commits;','static int commits;')
module=ast.parse((here/'check-dns-abort-composition.py').read_text())
prefix=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prefix' for t in n.targets))
# Only finish/state/commit are used here; omit recovery-only injected helpers.
omit=('static int wr_iot_service_guard_dup(', 'static int close(', 'static void wr_iot_service_guard_leave(', 'static void wr_iot_stop_dns_raw(', 'static int wr_iot_restart_wait(', 'static int wr_iot_service_state_recover(', 'static int wr_iot_generated_capture(', 'static int wr_iot_saved_restore(', 'static int is_dns_dhcpd_run(', 'static int eval(', 'static int wr_iot_restart_service_wait(')
prefix='\n'.join(line for line in prefix.splitlines() if not line.startswith(omit))+'\n'
prefix=prefix.replace('static int fault,stops,restores,captures,launches,releases,running,guard_leaves;','static int fault,releases;')
prefix='\n'.join(line for line in prefix.splitlines() if not line.startswith(('static int wr_iot_restart_stopped_candidate,','static unsigned wr_iot_restart_old_port,','static int wr_iot_restart_old_dhcp4;','static char wr_iot_restart_old_gateway[16];','static int wr_iot_restart_lease_captured,','static int wr_iot_restart_lease_observed,')))+'\n'
prefix=prefix.replace('wr_iot_restart_lease,wr_iot_restart_lease_generated','wr_iot_restart_lease')
source=(here/'restart-controller.inc').read_text()
def function(signature):
 start=source.index(signature);end=source.index('{',start)+1;depth=1
 while depth:
  depth+=(source[end]=='{')-(source[end]=='}');end+=1
 return source[start:end]
prefix+='\n'+function('static int wr_iot_restart_finish(void)')+'\n'+function('int wr_iot_dns_activation_recovery_state(void)')
prefix+='\nstatic int wr_iot_dns_activation_ready(void){assert(depth==2);return 1;}\n'
prefix+=function('int wr_iot_dns_activation_commit(void)').replace('wr_iot_dns_activation_commit','fixture_dns_commit')
prefix+='\nint wr_iot_dns_activation_commit(void){commits++;return fixture_dns_commit();}\n'
prefix=prefix.replace('wr_iot_saved_release','fixture_saved_release')
fixture=fixture.replace('int main(void){',prefix+'\nint main(void){')
fixture=fixture.replace(' bridge_index=7;',' wr_iot_restart_active=wr_iot_restart_guard=wr_iot_restart_bound=wr_iot_restart_prepared=wr_iot_restart_state.transaction.active=1;\n bridge_index=7;')
fixture=fixture.replace('DNS/driver/network adapters injected','actual DNS commit/finish with readiness/file/service adapters injected; driver/network injected')
with tempfile.TemporaryDirectory(prefix='iot-start-dns-commit-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(fixture);binary=Path(d)/'check'
 units=('start-commit.c','start-admission.c','request-stage.c','request-snapshot.c','disable-services.c','disable-controller.c','profile.c')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
