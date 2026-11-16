"""Actual normal shutdown controller + ACTIVE backend + physical retirement."""
from pathlib import Path
import subprocess,tempfile,sys
here=Path(__file__).resolve().parent
source=(here/'check-rc-routed-shutdown.py').read_text()
ns={'__file__':str(here/'check-rc-routed-shutdown.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<routed backend>','exec'),ns)
body=ns['body']
body=body.replace('static int entropy_fail;', 'static int entropy_fail,normal_entropy;').replace('memset(out,1,n);return n;', 'memset(out,normal_entropy?2:1,n);return n;')
body=body.replace('assert(wr_iot_rc_shutdown_route_arm()&&!raise(SIGTERM)&&!shutdowns);','normal_entropy=1;assert(wr_iot_rc_shutdown_route_arm()&&!raise(SIGTERM)&&!shutdowns);')
body=body.replace('static void routed_signal(int sig){', '#include "rc-normal-shutdown.c"\nstatic void routed_signal(int sig){',1)
body=body.replace('assert(sig==SIGTERM&&!depth&&!physical.owner&&!wr_iot_rc_shutdown.active);','assert(sig==SIGTERM&&!depth&&!physical.owner&&!wr_iot_rc_shutdown.active&&normal_shutdown.spent&&!normal_shutdown.owner);',1)
a=' assert(wr_iot_rc_physical_begin_routed_shutdown(&off));'
assert a in body
body=body.replace(a,' assert(!wr_iot_rc_normal_shutdown_step()&&normal_shutdown.claimed);\n off=normal_shutdown.off;',1)
body=body.replace(')wr_iot_rc_physical_step();', ')wr_iot_rc_normal_shutdown_step();')
a=' struct wr_iot_physical_stop_request receipt={0};'
b=body.index(' char path[PATH_MAX];',body.index(a))
start=body.index(a)
body=body[:start]+r'''
 assert(wr_iot_rc_normal_shutdown_step()&&normal_shutdown.spent&&shutdowns==1);
 assert(backend.phase==WR_IOT_OWNER_OFF&&!physical.owner&&!normal_shutdown.off.id[0]);
 assert(!wr_iot_rc_normal_shutdown_pending()&&!wr_iot_rc_normal_shutdown_step());
''' +body[b:]
with tempfile.TemporaryDirectory(prefix='wr-normal-backend-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 p=Path(d)/'test.c';p.write_text(ns['ns']['ns']['prefix']+'\n#include "check-reopen-unused.h"\n'+body)
 b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),*[str(here/n) for n in ns['ns']['units']],str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS normal shutdown controller/ACTIVE backend/OFF/physical RELEASE composition: isolation blocks physical work; exact owner retirement before stock TERM, no duplicate dispatch; driver/resources actors, arming explicit')
