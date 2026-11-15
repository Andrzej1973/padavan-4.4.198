"""Compose actual ACTIVE backend, shutdown OFF, physical RELEASE and stock replay."""
from pathlib import Path
import subprocess,sys,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-rc-physical-quiesce.py').read_text()
ns={'__file__':str(here/'check-rc-physical-quiesce.py')}
exec(compile(source[:source.index("\nwith tempfile.TemporaryDirectory(")],'<physical backend fixture>','exec'),ns)
body=ns['body']
body=body.replace('int main(void){',r'''
static void routed_signal(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(sig==SIGTERM&&!depth&&!physical.owner&&!wr_iot_rc_shutdown.active);
 assert(!wr_iot_rc_shutdown.normal_route_armed&&!wr_iot_rc_shutdown.normal_route_requested);
 shutdowns++;
}
int main(void){''',1)
a=body.index(' struct wr_iot_request desired=backend.start.input.request;')
b=body.index(' char path[PATH_MAX];',a)
body=body[:a]+r'''
 assert(signal(SIGTERM,routed_signal)!=SIG_ERR);
 assert(wr_iot_rc_shutdown_route_arm()&&!raise(SIGTERM)&&!shutdowns);
 off.created=on.created+1;
 assert(wr_iot_rc_physical_begin_routed_shutdown(&off));
 assert(physical.quiesce.active&&!physical.quiesce.resume_needed);
 for(unsigned i=0;i<sizeof(physical.quiesce.desired);i++)assert(!((unsigned char*)&physical.quiesce.desired)[i]);
 for(unsigned i=0;i<60&&backend.stop.stop.phase!=WR_IOT_STOP_ISOLATE;i++)wr_iot_rc_physical_step();
 assert(backend.stop.stop.phase==WR_IOT_STOP_ISOLATE&&!physical_aux&&!physical_calls&&!physical_downs);
 quarantine_ready=0;
 for(unsigned i=0;i<3;i++)wr_iot_rc_physical_step();
 assert(closes==1&&!physical_aux&&!physical_calls&&!physical_downs&&wr_iot_rc_physical_pending());
 assert(!wr_iot_rc_physical_shutdown_release(off.id,off.created));
 quarantine_ready=1;
 for(unsigned i=0;i<100&&wr_iot_rc_physical_pending();i++)wr_iot_rc_physical_step();
 assert(backend.phase==WR_IOT_OWNER_OFF&&!backend.start.input.request.password[0]);
 assert(!wr_iot_rc_physical_pending()&&physical_aux==6&&physical_downs==1&&physical_calls==3);
 assert(!depth&&!wr_iot_rc_shutdown.active&&!shutdowns);
 struct wr_iot_physical_stop_request receipt={0};
 assert(wr_iot_rc_physical_off_read(off.id,off.created,&receipt)&&receipt.action==WR_STOP_RELEASE);
 assert(!wr_iot_rc_physical_take_off(off.id,off.created));
 assert(wr_iot_rc_physical_shutdown_release(off.id,off.created)&&shutdowns==1);
 assert(backend.phase==WR_IOT_OWNER_OFF&&!physical.owner);
 assert(!wr_iot_rc_physical_shutdown_release(off.id,off.created)&&shutdowns==1);
''' +body[b:]
body=body.replace('PASS actual backend ACTIVE to private OFF then physical RELEASE; resume snapshot retained; no public OFF publication or resume completion claimed','PASS actual routed backend OFF, physical RELEASE and final stock signal')
with tempfile.TemporaryDirectory(prefix='wr-rc-routed-shutdown-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(ns['ns']['prefix']+'\n#include "check-reopen-unused.h"\n'+body)
 binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in ns['units']],str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
print('PASS actual ACTIVE backend/shutdown OFF/physical RELEASE/stock signal composition: delayed isolation blocks physical work, secrets wiped, one CLOSE/Main DOWN/RELEASE, private retirement before replay; driver/resources injected')
