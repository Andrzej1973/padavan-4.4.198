#!/usr/bin/env python3
"""Actual reopen rollback/snapshot with injected CLOSED and network resources."""
from pathlib import Path
import subprocess,sys,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-start-rollback-composition.c').read_text()
source=source.replace('#include "start-network-rollback.h"','#include "reopen-rollback.h"')
anchor='int main(void){'
hooks='''static int witness_ok=1;
int wr_iot_reopen_witness_current(const struct wr_iot_reopen_witness *w){assert(depth&&w&&w->owner==getpid());return witness_ok;}
'''
source=source.replace(anchor,hooks+anchor)
a='  char baseline[9][128];';assert a in source
source=source.replace(a,'''  owner.reopened=1;
  struct wr_iot_reopen_witness witness={.owner=getpid(),.valid=1,.attempt={.identity={1,2}},.close_serial=owner.idle.serial};
'''+a)
# Stage through initial path only for fixture setup, then keep explicit reopened context.
a='  assert(wr_iot_start_admission_stage(&owner,nonce,candidate_read,NULL,1,1,0));';assert a in source
source=source.replace(a,'''  owner.reopened=0;
'''+a+'''
  owner.reopened=1;witness.close_serial=owner.idle.serial;
''')
source=source.replace('wr_iot_start_network_rollback_step(&rollback,&network,&owner,&open,nonce)','wr_iot_reopen_rollback_step(&rollback,&network,&owner,&open,&witness)')
a='  bridge_index=7;wr_iot_rc_shutdown.pending=SIGTERM;';assert a in source
source=source.replace(a,a+'''
  unsigned initial_before=idle_reads;int writes_before=writes;
  witness_ok=0;
  assert(!wr_iot_reopen_rollback_step(&rollback,&network,&owner,&open,&witness)&&bridge_index==7&&writes==writes_before&&depth==1);
  witness_ok=1;
  open.attempt.identity.adapter_epoch=1;
  assert(!wr_iot_reopen_rollback_step(&rollback,&network,&owner,&open,&witness)&&bridge_index==7);
  open.attempt.identity.adapter_epoch=0;open.attempt.request_id[0]=1;
  assert(!wr_iot_reopen_rollback_step(&rollback,&network,&owner,&open,&witness)&&bridge_index==7);
  open.attempt.request_id[0]=0;
''')
source=source.replace(' puts("PASS', ' assert(idle_reads==initial_before);\n puts("PASS') if False else source
# initial_before lives in each scenario; check before the scenario scope ends.
a='  assert(wr_iot_rc_shutdown.pending==SIGTERM);';assert a in source
source=source.replace(a,a+'\n  assert(idle_reads==initial_before);')
source=source.replace('PASS actual admission/stage/snapshot/pre-OPEN rollback:', 'PASS actual reopen rollback/snapshot:')
with tempfile.TemporaryDirectory(prefix='iot-reopen-rollback-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(source);binary=Path(d)/'check'
 units=('reopen-rollback.c','start-admission.c','request-stage.c','request-snapshot.c','disable-services.c','disable-controller.c','profile.c')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
