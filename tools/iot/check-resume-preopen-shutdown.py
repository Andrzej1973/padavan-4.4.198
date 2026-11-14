"""Actual resume pump/rebind runner retains a rejected pre-OPEN shutdown."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
prefix=(here/'check-rebind-runner.c').read_text().split('int main(void)',1)[0]
code=prefix+r'''
#include "restart-resume.h"
static struct wr_iot_rebind_runner runner;
int wr_iot_restart_restore_begin(struct wr_iot_restart_restore*s,const unsigned char*i){(void)s;(void)i;assert(0);return 0;}
int wr_iot_restart_restore_step(struct wr_iot_restart_restore*s){(void)s;assert(0);return 0;}
int wr_iot_restart_restore_handoff(struct wr_iot_restart_restore*s,const struct wr_iot_control_request*r){(void)s;(void)r;assert(0);return 0;}
int wr_iot_restart_restore_rebind_current(struct wr_iot_restart_restore*s){(void)s;assert(0);return 0;}
enum wr_iot_result_state wr_iot_activation_continue(const char*id,unsigned long long created){return wr_iot_rebind_runner_continue(&runner,id,created);}
int wr_iot_rc_quiesce_shutdown_begin(struct wr_iot_rc_quiesce*q,const struct wr_iot_control_request*off){(void)q;(void)off;assert(runner.phase!=WR_IOT_RUN_ACTIVE);return 0;}
int wr_iot_rc_quiesce_advance(struct wr_iot_rc_quiesce*q,struct wr_iot_driver_closed_result*out){(void)q;(void)out;assert(0);return 0;}
int wr_iot_rc_physical_resume_finish(struct wr_iot_restart_restore*s){(void)s;assert(0);return 0;}
int wr_iot_rc_physical_resume_cancel(struct wr_iot_restart_restore*s,const struct wr_iot_rc_quiesce*q){(void)s;(void)q;assert(0);return 0;}
int wr_iot_rc_physical_take(struct wr_iot_rc_physical_intent*i){(void)i;assert(0);return 0;}
int wr_iot_restart_guest_step(struct wr_iot_restart_guest*g){(void)g;assert(0);return 0;}
#include "restart-resume.c"
int main(void){
 struct wr_iot_control_request on={.id="11111111111111111111111111111111",.created=1,.request={.enabled=1,.ssid="IoT",.password="password123",.gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"}};
 struct wr_iot_physical_stop_request physical={.action=WR_STOP_RELEASE,.epoch=1,.generation=2,.open_token=3,.closed_serial=4,.attempt=5,.nonce={1}};
 wr_iot_rc_shutdown.active=1;assert(wr_iot_rebind_runner_begin(&runner,&on,&physical,1,1,0));
 assert(wr_iot_rebind_runner_step(&runner)==WR_IOT_RESULT_RECOVERY);assert(wr_iot_rebind_runner_step(&runner)==WR_IOT_RESULT_RECOVERY&&runner.phase==WR_IOT_RUN_OPEN);
 struct wr_iot_restart_resume pump={0};pump.owner=getpid();pump.created=1;pump.phase=WR_RESUME_REBIND;pump.restore.phase=WR_RESTORE_HANDOFF;pump.restore.generation.profile.active=1;memset(pump.restore.open_id,0x11,16);
 struct wr_iot_control_request off={.id="22222222222222222222222222222222",.created=2};wr_iot_rc_shutdown.pending=SIGTERM;
 assert(wr_iot_restart_resume_shutdown(&pump,&off));
 for(int i=0;i<8;i++)assert(!wr_iot_restart_resume_step(&pump));
 assert(runner.phase==WR_IOT_RUN_REJECTED&&pre_rolls==1&&!opens&&!closes);
 assert(pump.phase==WR_RESUME_SHUTDOWN&&!pump.shutdown.owner&&pump.restore.generation.profile.active&&wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.pending==SIGTERM);
 puts("PASS actual pump/runner pre-OPEN shutdown: no OPEN, rollback once to REJECTED, not mislabeled OFF/CLOSED; root profile/admission retained pending separate rejected-state completion proof; component adapters injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-preopen-shutdown-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
