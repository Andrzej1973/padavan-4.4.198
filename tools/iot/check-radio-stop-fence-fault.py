"""Actual RC fence failure retention and signal dispatch order; syscalls injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <signal.h>
#include <stdio.h>
#include <unistd.h>
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int fail_restore,restores,raises,cleaned;
static int fake_mask(int op,const sigset_t*set,sigset_t*old){
 assert(set);if(old)sigemptyset(old);
 if(op==SIG_SETMASK){restores++;return fail_restore?-1:0;}
 assert(op==SIG_BLOCK);return 0;
}
static int fake_raise(int sig){assert(sig==SIGTERM&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending);if(raises==1)assert(cleaned==1);raises++;return 0;}
#define sigprocmask fake_mask
#define raise fake_raise
#include "radio-stop-fence.c"
static void cleanup(void *context){
 struct wr_iot_radio_stop_fence *token=context,extra={0};
 assert(wr_iot_rc_shutdown.active&&fence_depth==1&&fence_finishing&&raises==1);
 assert(!wr_iot_radio_stop_fence_end(token));assert(!wr_iot_radio_stop_fence_begin(&extra));
 cleaned++;
}
int main(void){
 struct wr_iot_radio_stop_fence outer={0},inner={0};
 assert(wr_iot_radio_stop_fence_begin(&outer));assert(wr_iot_radio_stop_fence_begin(&inner));
 assert(!wr_iot_radio_stop_fence_end(&outer)&&!restores);
 assert(wr_iot_radio_stop_fence_end(&inner)&&fence_depth==1);
 assert(wr_iot_rc_shutdown_note(SIGTERM));fail_restore=1;
 assert(!wr_iot_radio_stop_fence_end(&outer)&&outer.owner==getpid()&&outer.level==1&&fence_depth==1);
 assert(wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.pending==SIGTERM&&!raises);
 fail_restore=0;assert(wr_iot_radio_stop_fence_end(&outer));
 assert(!outer.owner&&!fence_depth&&!wr_iot_rc_shutdown.active&&raises==1&&restores==2);
 assert(!wr_iot_radio_stop_fence_end(&outer)&&raises==1);
 assert(wr_iot_radio_stop_fence_begin(&outer));assert(wr_iot_radio_stop_fence_begin(&inner));
 assert(!wr_iot_radio_stop_fence_end_cleanup(&inner,cleanup,&outer)&&!cleaned);
 assert(wr_iot_radio_stop_fence_end(&inner));
 assert(wr_iot_rc_shutdown_note(SIGTERM));
 fail_restore=1;assert(!wr_iot_radio_stop_fence_end_cleanup(&outer,cleanup,&outer)&&!cleaned&&wr_iot_rc_shutdown.active);
 fail_restore=0;assert(wr_iot_radio_stop_fence_end_cleanup(&outer,cleanup,&outer)&&cleaned==1&&!wr_iot_rc_shutdown.active&&raises==2);
 assert(!wr_iot_radio_stop_fence_end_cleanup(&outer,cleanup,&outer)&&cleaned==1);
 puts("PASS actual signal fence fault: failed mask restore retains exact token/depth/admission/pending, same token retry dispatches once, outer LIFO refused; syscall/signal actors injected, no RF proof");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-fence-fault-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
