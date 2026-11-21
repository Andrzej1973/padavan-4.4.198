"""Actual mailbox OFF terminal publication hands deferred shutdown to armed route."""
from pathlib import Path
import subprocess,tempfile,sys,ast
here=Path(__file__).resolve().parent
source=(here/'check-rc-backend-composition.py').read_text()
ns={'__file__':str(here/'check-rc-backend-composition.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<actual RC mailbox>','exec'),ns)
body=ns['body']
a=' submit(&off);assert(wr_iot_rc_dispatch()&&wr_iot_rc_shutdown.active);'
assert body.count(a)==1
body=body.replace(a,' assert(wr_iot_rc_shutdown_route_arm());\n'+a,1)
a='assert(!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&!shutdowns&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM);'
assert body.count(a)==1
body=body.replace(a,'assert(!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&!shutdowns&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM);',1)
a=' terminal(off.id);assert(!wr_iot_rc_continue());'
assert body.count(a)==1
body=body.replace(a,a+r'''
 struct wr_iot_activation_owner retained=backend;
 unsigned completed_closes=closes,completed_progresses=progresses,completed_releases=releases;
 assert(!wr_iot_rc_dispatch()&&!wr_iot_rc_continue());
 assert(!raise(SIGTERM)&&!shutdowns&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 assert(!wr_iot_rc_shutdown.active&&!wr_iot_continuation.active&&!depth);
 assert(!memcmp(&retained,&backend,sizeof(backend)));
 assert(closes==completed_closes&&progresses==completed_progresses&&releases==completed_releases);
''',1)
units=next(ast.literal_eval(n.value) for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='units' for t in n.targets))
with tempfile.TemporaryDirectory(prefix='wr-mailbox-shutdown-') as d:
 p=Path(d);subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 (p/'test.c').write_text(ns['prefix']+'\n#include "check-reopen-unused.h"\n'+body)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p/'test.c'),*[str(here/n) for n in units],'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True,timeout=20)
print('PASS actual mailbox OFF terminal publication routes deferred TERM, preserves APPLIED and completed backend, refuses new dispatch/duplicate CLOSE; driver/network actors, physical normal consumer separately tested')
