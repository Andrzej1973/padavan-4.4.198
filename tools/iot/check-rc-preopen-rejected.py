"""Actual RC owner/runner/pre-OPEN rollback and rejected observation."""
from pathlib import Path
import ast,subprocess,tempfile,sys
here=Path(__file__).resolve().parent
source=(here/'check-rc-rebind-owner.py').read_text();ns={'__file__':str(here/'check-rc-rebind-owner.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<owner fixture>','exec'),ns)
units=next(ast.literal_eval(n.value) for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='units' for t in n.targets))
units+=next(ast.literal_eval(n.value) for n in ast.walk(ast.parse(source)) if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='units')
body=ns['body'].split(' for(unsigned i=0;i<10&&rebind.phase!=WR_REBIND_OWNER_ACTIVE;',1)[0]+r'''
 for(unsigned i=0;i<4&&rebind.start.phase!=WR_IOT_RUN_OPEN;i++)(void)wr_iot_activation_continue(on.id,on.created);
 assert(rebind.start.phase==WR_IOT_RUN_OPEN&&!submits);
 wr_iot_rc_shutdown.pending=SIGTERM;
 for(unsigned i=0;i<30&&rebind.phase!=WR_REBIND_OWNER_REJECTED;i++)(void)wr_iot_activation_continue(on.id,on.created);
 assert(rebind.phase==WR_REBIND_OWNER_REJECTED&&!submits&&!rebind.start.start.admission.snapshot.active&&!depth);
 struct wr_iot_control_result original={.id="03030303030303030303030303030303",.created=3};
 struct wr_iot_driver_identity identity={2,2};
 assert(wr_iot_rc_rebind_preopen_rejected(&original,&physical,&identity));
 strcpy(values[10].value,"foreign");assert(!wr_iot_rc_rebind_preopen_rejected(&original,&physical,&identity));values[10].value[0]=0;
 original.created++;assert(!wr_iot_rc_rebind_preopen_rejected(&original,&physical,&identity));original.created--;
 physical.attempt++;assert(!wr_iot_rc_rebind_preopen_rejected(&original,&physical,&identity));physical.attempt--;
 rebind.start.open.attempt.request_id[0]=1;assert(!wr_iot_rc_rebind_preopen_rejected(&original,&physical,&identity));rebind.start.open.attempt.request_id[0]=0;
 rebind.start.start.admission.snapshot.active=1;assert(!wr_iot_rc_rebind_preopen_rejected(&original,&physical,&identity));rebind.start.start.admission.snapshot.active=0;
 assert(wr_iot_rc_rebind_preopen_rejected(&original,&physical,&identity)&&!submits&&!depth);
 puts("PASS actual RC pre-OPEN rejection witness: pending rollback releases owned snapshot/resources, exact ID/RELEASE/new Main, no driver attempt, fresh closed configuration; no OFF token invented; driver/network actors injected");
}
'''
# The injected old OFF provenance must have normal-OFF-cleared temporary credentials.
body=body.replace('reset();rollback_dns=0;', 'reset();values[10].value[0]=values[11].value[0]=0;rollback_dns=0;',1)
with tempfile.TemporaryDirectory(prefix='wr-preopen-rejected-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'test.c';unit.write_text(ns['prefix']+'\n#include "check-reopen-unused.h"\n'+body.replace('#include "rc-backend.c"','#include "check-legacy-start-unused.h"\n#include "rc-backend.c"'))
 binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
