#!/usr/bin/env python3
"""Actual ACTIVE backend/OFF owner -> physical session/fence -> resume snapshot."""
from pathlib import Path
import ast,subprocess,sys,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-rc-backend-composition.py').read_text()
ns={'__file__':str(here/'check-rc-backend-composition.py')}
exec(compile(source[:source.index('with tempfile.TemporaryDirectory(')],'<RC fixture setup>','exec'),ns)
units=next(ast.literal_eval(n.value) for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='units' for t in n.targets))
body=ns['body'];a=body.index('int main(void){')
hooks=r'''
#include "rc-physical-stop.c"
int wr_iot_restart_scheduler_prepare(void){assert(!wr_iot_rc_shutdown.active);return 1;}
int wr_iot_restart_prehandoff_cancel_check(struct wr_iot_restart_restore*s){(void)s;return 0;}
int wr_iot_restart_generation_rollback_current(const struct wr_iot_restart_generation*g){(void)g;return 0;}
int wr_iot_restart_restore_finish_check(struct wr_iot_restart_restore*s){(void)s;return 0;}
int wr_iot_restart_restore_cancel_check(struct wr_iot_restart_restore*s,const struct wr_iot_rc_quiesce*q){(void)s;(void)q;return 0;}
#include "physical-stop-down.h"
static int physical_calls,physical_downs,physical_aux;
int wr_iot_rc_physical_aux_down(unsigned slot){assert(depth>=2&&slot==(unsigned)physical_aux&&!physical_calls&&!physical_downs);physical_aux++;return 1;}
enum wr_iot_physical_down_result wr_iot_physical_stop_down(void){assert(physical_aux==6);physical_downs++;return WR_PHYSICAL_DOWN_UNCERTAIN;}
enum wr_iot_physical_call_result wr_iot_physical_stop_call(const struct wr_iot_physical_stop_request*r,struct wr_iot_physical_stop_response*out){
 assert(depth>=2&&physical_aux==6&&r->epoch==1&&r->generation==2&&r->open_token==3&&r->closed_serial==observed_serial);
 physical_calls++;out->identity=*r;out->identity.attempt=7;
 out->status=r->action==WR_STOP_ARM?WR_STOP_ARMED:r->action==WR_STOP_RELEASE?WR_STOP_RELEASED:WR_STOP_COMPLETE;
 return WR_PHYSICAL_CALL_ACKNOWLEDGED;
}
'''
body=body[:a]+hooks+body[a:]
a=body.index(' submit(&off);');b=body.index(' char path[PATH_MAX];',a)
body=body[:a]+r'''
 struct wr_iot_request desired=backend.start.input.request;
 struct wr_iot_rc_physical_intent intent={1,1,0};
 struct wr_iot_rc_physical_resume resume={0};
 off.created=on.created+1;
 assert(wr_iot_rc_physical_begin_quiesce(&intent,&off)&&depth==2&&wr_iot_rc_shutdown.active);
 assert(physical.quiesce.active&&physical.quiesce.resume_needed);
 assert(!memcmp(&physical.quiesce.desired,&desired,sizeof(desired)));
 assert(!wr_iot_rc_physical_resume_read(&resume)&&!resume.physical.epoch);
 for(unsigned i=0;i<60&&backend.stop.stop.phase!=WR_IOT_STOP_ISOLATE;i++)wr_iot_rc_physical_step();
 assert(backend.stop.stop.phase==WR_IOT_STOP_ISOLATE&&!physical_aux&&!physical_calls&&!physical_downs);
 quarantine_ready=0;
 for(unsigned i=0;i<3;i++)wr_iot_rc_physical_step();
 assert(closes==1&&!physical_aux&&!physical_calls&&!physical_downs&&wr_iot_rc_physical_pending());
 quarantine_ready=1;
 for(unsigned i=0;i<100&&wr_iot_rc_physical_pending();i++)wr_iot_rc_physical_step();
 assert(backend.phase==WR_IOT_OWNER_OFF&&!backend.start.input.request.password[0]);
 assert(!wr_iot_rc_physical_pending()&&physical_aux==6&&physical_downs==1&&physical_calls==3);
 assert(wr_iot_rc_physical_resume_read(&resume)&&resume.resume_needed);
 assert(!memcmp(&resume.desired,&desired,sizeof(desired))&&resume.physical.action==WR_STOP_RELEASE);
 assert(resume.physical.epoch==1&&resume.physical.generation==2&&resume.physical.attempt==7);
 assert(depth==1&&wr_iot_rc_shutdown.active);
 resume.desired.password[0]='X';assert(wr_iot_rc_physical_resume_read(&resume));
 assert(!memcmp(&resume.desired,&desired,sizeof(desired)));
 struct wr_iot_rc_physical_intent taken={0};assert(!wr_iot_rc_physical_take(&taken));
 assert(!raise(SIGTERM)&&!shutdowns&&wr_iot_rc_shutdown.active);
 /* SIGTERM is blocked by the real physical fence, not delivered until a
  * future verified resume consumer ends it. Fixture exits without bypass. */

'''+body[b:]
body=body.replace('PASS actual RC backend/mailbox/server/client/owner/runner/OFF: ON and OFF published APPLIED, duplicate dispatch refused, delayed isolation retains guard, pending SIGTERM delivered only after terminal publication; external resource/driver hooks injected','PASS actual backend ACTIVE to private OFF then physical RELEASE; resume snapshot retained; no public OFF publication or resume completion claimed')
with tempfile.TemporaryDirectory(prefix='wr-rc-physical-quiesce-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(ns['prefix']+'\n#include "check-reopen-unused.h"\n'+body)
 binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
print('PASS actual ACTIVE backend/normal OFF/physical session/fence composition: no AUX/ARM before CLOSE, desired ON survives runner wipe, exact RELEASE snapshot, guards retained; driver/resources injected')
