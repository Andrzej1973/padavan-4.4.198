"""Actual pump/RC rejection observer/root cancel gate; physical cleanup injected."""
from pathlib import Path
import subprocess,tempfile,sys
here=Path(__file__).resolve().parent
source=(here/'check-rc-preopen-rejected.py').read_text();fixture={'__file__':str(here/'check-rc-preopen-rejected.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<preopen fixture>','exec'),fixture)
body=fixture['body']
hooks=r'''
#include "restart-resume.h"
static int guest_up=1,cancel_calls,take_calls,guest_downs;
int wr_iot_restart_generation_origin_current(const struct wr_iot_restart_generation*g){return g->owner==getpid();}
int wr_iot_restart_guest_admin_state(int*out){*out=guest_up;return 1;}
#include "restart-cancel-check.c"
int wr_iot_restart_restore_begin(struct wr_iot_restart_restore*s,const unsigned char*i){(void)s;(void)i;assert(0);return 0;}
int wr_iot_restart_restore_step(struct wr_iot_restart_restore*s){(void)s;assert(0);return 0;}
int wr_iot_restart_restore_handoff(struct wr_iot_restart_restore*s,const struct wr_iot_control_request*r){(void)s;(void)r;assert(0);return 0;}
int wr_iot_restart_restore_rebind_current(struct wr_iot_restart_restore*s){(void)s;assert(0);return 0;}
int wr_iot_rc_physical_resume_finish(struct wr_iot_restart_restore*s){(void)s;assert(0);return 0;}
int wr_iot_rc_physical_resume_cancel(struct wr_iot_restart_restore*s,const struct wr_iot_rc_quiesce*q){assert(!q&&wr_iot_restart_restore_cancel_check(s,NULL));cancel_calls++;s->phase=WR_RESTORE_CANCELLED;s->generation.profile.active=0;return 1;}
int wr_iot_rc_physical_take(struct wr_iot_rc_physical_intent*out){take_calls++;out->restart=1;return -1;}
int wr_iot_restart_guest_step(struct wr_iot_restart_guest*g){guest_up=0;guest_downs++;g->phase=WR_GUEST_DOWN_OBSERVED;return 0;}
int wr_iot_rc_physical_premain_cancel(struct wr_iot_restart_restore*s){(void)s;return 0;}
int wr_iot_rc_physical_prehandoff_cancel(struct wr_iot_restart_restore*s){(void)s;return 0;}
#include "restart-resume.c"
'''
body=body.replace('int main(void){',hooks+'\nint main(void){',1)
body=body.replace(' puts("PASS actual RC pre-OPEN rejection witness:',r'''
 struct wr_iot_restart_resume pump={0};pump.owner=getpid();pump.created=on.created;pump.phase=WR_RESUME_SHUTDOWN;
 pump.restore.owner=getpid();pump.restore.phase=WR_RESTORE_HANDOFF;pump.restore.handoff_created=on.created;
 memcpy(pump.restore.open_id,rebind.start.start.open_id,16);
 pump.restore.generation.owner=getpid();pump.restore.generation.profile.active=1;pump.restore.generation.main_may_have_started=1;pump.restore.generation.origin.physical=physical;
 pump.restore.main.owner=getpid();pump.restore.main.generation=&pump.restore.generation;pump.restore.main.identity=identity;
 pump.restore.guest.owner=getpid();pump.restore.guest.main=&pump.restore.main;pump.restore.guest.desired=1;pump.restore.guest.phase=WR_GUEST_ADMIN_UP;
 assert(!wr_iot_restart_resume_step(&pump)&&pump.phase==WR_RESUME_SHUTDOWN_ROLLBACK&&!pump.shutdown.owner);
 assert(wr_iot_restart_resume_step(&pump)==-1&&pump.phase==WR_RESUME_CANCELLED);
 assert(cancel_calls==1&&take_calls==1&&guest_downs==1&&!submits&&!pump.shutdown.owner);
 assert(wr_iot_restart_resume_step(&pump)==-1&&cancel_calls==1&&take_calls==1);
 puts("PASS actual RC pre-OPEN rejection witness:''')
with tempfile.TemporaryDirectory(prefix='wr-rejected-pump-compose-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 p=Path(d)/'test.c';p.write_text(fixture['ns']['prefix']+'\n#include "check-reopen-unused.h"\n'+body.replace('#include "rc-backend.c"','#include "check-legacy-start-unused.h"\n#include "rc-backend.c"'));b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),*[str(here/n) for n in fixture['units']],'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual rejected rollback/backend/root cancel gate/pump: no OPEN/OFF invented, Guest DOWN before cancel, exact rejection witness, terminal cancellation once; radio/network/Guest/physical cleanup actors injected')
