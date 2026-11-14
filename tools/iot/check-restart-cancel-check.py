from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "restart-restore.h"
#include "rc-quiesce.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int rejected_ok,origin_ok=1,closed_ok=1,guest_up,observations;
int wr_iot_restart_generation_origin_current(const struct wr_iot_restart_generation*g){assert(g);return origin_ok;}
int wr_iot_restart_guest_admin_state(int*out){*out=guest_up;return 1;}
int wr_iot_rc_rebind_shutdown_closed(const struct wr_iot_control_result*on,const struct wr_iot_physical_stop_request*p,const struct wr_iot_driver_identity*i,const struct wr_iot_rc_quiesce*q,struct wr_iot_driver_closed_result*out){assert(!strcmp(on->id,"07000000000000000000000000000000")&&on->created==10&&p&&i&&q);observations++;*out=(struct wr_iot_driver_closed_result){2,2,3,4};return closed_ok;}
int wr_iot_rc_rebind_preopen_rejected(const struct wr_iot_control_result*on,const struct wr_iot_physical_stop_request*p,const struct wr_iot_driver_identity*i){assert(on&&p&&i);return rejected_ok;}
#include "restart-cancel-check.c"
int main(void){
 struct wr_iot_restart_restore s={0};struct wr_iot_rc_quiesce off={0};
 s.owner=s.main.owner=s.guest.owner=getpid();s.phase=WR_RESTORE_HANDOFF;s.handoff_created=10;s.open_id[0]=7;
 s.main.generation=&s.generation;s.generation.main_may_have_started=s.generation.profile.active=1;
 s.guest.main=&s.main;s.guest.desired=1;s.guest.phase=WR_GUEST_DOWN_OBSERVED;
 wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=SIGTERM;
 assert(wr_iot_restart_restore_cancel_check(&s,&off));
 guest_up=1;assert(!wr_iot_restart_restore_cancel_check(&s,&off));guest_up=0;
 s.guest.phase=WR_GUEST_ADMIN_UP;assert(!wr_iot_restart_restore_cancel_check(&s,&off));s.guest.phase=WR_GUEST_DOWN_OBSERVED;
 closed_ok=0;assert(!wr_iot_restart_restore_cancel_check(&s,&off));closed_ok=1;
 origin_ok=0;assert(!wr_iot_restart_restore_cancel_check(&s,&off));origin_ok=1;
 wr_iot_rc_shutdown.pending=0;assert(!wr_iot_restart_restore_cancel_check(&s,&off));wr_iot_rc_shutdown.pending=SIGTERM;
 assert(wr_iot_restart_restore_cancel_check(&s,&off)&&s.generation.profile.active);
 assert(!wr_iot_restart_restore_cancel_check(&s,NULL));rejected_ok=1;
 assert(wr_iot_restart_restore_preopen_rejected(&s)&&wr_iot_restart_restore_cancel_check(&s,NULL));
 guest_up=1;assert(!wr_iot_restart_restore_cancel_check(&s,NULL));guest_up=0;
 rejected_ok=0;assert(!wr_iot_restart_restore_preopen_rejected(&s)&&!wr_iot_restart_restore_cancel_check(&s,NULL));
 puts("PASS cancel software gate: exact reconstructed ON and physical binding, Guest DOWN observation required, pending/owned-origin/current CLOSED refusal retains baseline; backend/transport/origin actors injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-cancel-check-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
