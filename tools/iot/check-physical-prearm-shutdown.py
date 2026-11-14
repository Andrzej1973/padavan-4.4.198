"""Actual pre-ARM cancellation with real pending signal and mask fault."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=(here/'check-rc-physical-stop.c').read_text().split('int main(void)',1)[0]
code+=r'''
static int fail_mask;
static int checked_mask(int op,const sigset_t*s,sigset_t*old){if(op==SIG_SETMASK&&fail_mask)return -1;return sigprocmask(op,s,old);}
#define sigprocmask checked_mask
#include "radio-stop-fence.c"
#undef sigprocmask
static void observed_shutdown(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(!physical.guard&&!depth&&physical.result==-1&&!physical.quiesce.desired.password[0]);
 shutdowns++;
}
int main(void){
 (void)handler;struct sigaction sa={0};sa.sa_handler=observed_shutdown;sigemptyset(&sa.sa_mask);assert(!sigaction(SIGTERM,&sa,NULL));
 struct wr_iot_rc_physical_intent intent={1,1,1},out={0};
 assert(wr_iot_rc_physical_begin(&intent));
 physical.auth.owner=getpid();physical.auth.phase=WR_AUTH_RETAINED;
 strcpy(physical.quiesce.desired.password,"retained-secret");
 assert(!wr_iot_rc_physical_prearm_cancel());
 assert(!kill(getpid(),SIGTERM));closed_fail=1;
 wr_iot_rc_physical_step();assert(wr_iot_rc_shutdown.pending==SIGTERM&&depth==1&&!physical.result&&!shutdowns);
 closed_fail=0;physical.session.owner=getpid();assert(!wr_iot_rc_physical_prearm_cancel());physical.session.owner=0;
 fail_mask=1;wr_iot_rc_physical_step();assert(depth==1&&!physical.result&&!shutdowns&&physical.quiesce.desired.password[0]);
 fail_mask=0;wr_iot_rc_physical_step();
 assert(shutdowns==1&&!depth&&!wr_iot_rc_shutdown.active&&!calls&&!downs&&!aux_calls);
 assert(wr_iot_rc_physical_take(&out)==-1&&out.restart&&!wr_iot_rc_physical_take(&out));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-prearm-shutdown-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual pre-ARM shutdown: real blocked SIGTERM, fresh CLOSE/session-owner/mask faults retain, uncertain auth does not require replay, private wipe/guard before signal replay, no AUX/ARM/Main, take once; backend/auth actors injected')
