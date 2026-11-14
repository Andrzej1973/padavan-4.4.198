"""Actual RC rebind ACTIVE -> normal OFF with pending shutdown; no reopen."""
from pathlib import Path
import ast,subprocess,tempfile,sys
here=Path(__file__).resolve().parent
source=(here/'check-rc-rebind-owner.py').read_text()
ns={'__file__':str(here/'check-rc-rebind-owner.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<RC owner fixture>','exec'),ns)
units=next(ast.literal_eval(n.value) for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='units' for t in n.targets))
units+=next(ast.literal_eval(n.value) for n in ast.walk(ast.parse(source)) if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='units')
body=ns['body']
anchor=' assert(wr_iot_rc_quiesce_begin(&q,&off)&&q.resume_needed&&q.active&&rebind.phase==WR_REBIND_OWNER_STOP);'
assert anchor in body
body=body.replace(anchor,''' assert(!wr_iot_rc_quiesce_shutdown_begin(&q,&off)&&!q.owner);
 wr_iot_rc_shutdown.pending=SIGTERM;
 assert(!wr_iot_rc_quiesce_begin(&q,&off)&&!q.owner);
 assert(wr_iot_rc_quiesce_shutdown_begin(&q,&off)&&!q.resume_needed&&q.active&&rebind.phase==WR_REBIND_OWNER_STOP);''')
body=body.replace('wr_iot_rc_quiesce_begin(&already,&off)','wr_iot_rc_quiesce_shutdown_begin(&already,&off)')
body=body.replace('q.complete&&q.resume_needed','q.complete&&!q.resume_needed')
body=body.replace('!memcmp(&q.desired,&desired,sizeof(desired))', '!q.desired.enabled&&!q.desired.password[0]')
body=body.replace(' observed_serial++;assert(!wr_iot_rc_backend_closed(&receipt)', r'''
 struct wr_iot_control_result original_on={.id="03030303030303030303030303030303",.created=3};
 assert(wr_iot_rc_rebind_shutdown_closed(&original_on,&physical,&expected_identity,&q,&receipt));
 original_on.created++;assert(!wr_iot_rc_rebind_shutdown_closed(&original_on,&physical,&expected_identity,&q,&receipt)&&!receipt.close_serial);original_on.created--;
 physical.attempt++;assert(!wr_iot_rc_rebind_shutdown_closed(&original_on,&physical,&expected_identity,&q,&receipt));physical.attempt--;
 expected_identity.adapter_epoch++;assert(!wr_iot_rc_rebind_shutdown_closed(&original_on,&physical,&expected_identity,&q,&receipt));expected_identity.adapter_epoch--;
 q.resume_needed=1;assert(!wr_iot_rc_rebind_shutdown_closed(&original_on,&physical,&expected_identity,&q,&receipt));q.resume_needed=0;
 assert(wr_iot_rc_rebind_shutdown_closed(&original_on,&physical,&expected_identity,&q,&receipt));
 observed_serial++;assert(!wr_iot_rc_backend_closed(&receipt)''')
# Original fixture retains desired solely for its normal-resume assertions.
body=body.replace('struct wr_iot_request desired=rebind.start.input.request;', 'struct wr_iot_request desired=rebind.start.input.request;(void)desired;')
with tempfile.TemporaryDirectory(prefix='wr-rebind-shutdown-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(ns['prefix']+'\n#include "check-reopen-unused.h"\n'+body.replace('#include "rc-backend.c"','#include "check-legacy-start-unused.h"\n#include "rc-backend.c"'))
 binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
print('PASS actual RC rebind pending shutdown OFF: normal resume admission refuses, shutdown-only closes once with retained isolation, no desired ON copy retained; driver/network actors injected')
