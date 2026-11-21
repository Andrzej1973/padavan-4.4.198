"""Signal publication boundary only; readiness/consumer integration is not mocked as proven."""
from pathlib import Path
import subprocess
import tempfile

here = Path(__file__).resolve().parent
body = r'''
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <signal.h>
#include <stdlib.h>
#include <unistd.h>
#include "radio-stop-fence.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int stock,cleaned,where,requested_signal;
static void handler(int sig){if(!wr_iot_rc_shutdown_note(sig))stock++;}
static void cleanup(void *context){
 assert(context==&cleaned&&wr_iot_rc_shutdown.active&&!cleaned);
 /* Existing public arm cannot be used inside the active cleanup callback. */
 assert(!wr_iot_rc_shutdown_route_arm());
 if(where==0)assert(!raise(requested_signal));
 /* Explicit publication actor. Production must separately prove consumer
  * readiness and exact ACTIVE owner before reaching this nonfallible point. */
 wr_iot_rc_shutdown.normal_route_armed=1;
 if(where==1)assert(!raise(requested_signal));
 assert(!stock);cleaned=1;
}
int main(int argc,char **argv){
 assert(argc==3);where=atoi(argv[1]);requested_signal=atoi(argv[2])?SIGQUIT:SIGTERM;
 struct sigaction sa={0};sa.sa_handler=handler;sigemptyset(&sa.sa_mask);
 assert(!sigaction(SIGTERM,&sa,0)&&!sigaction(SIGQUIT,&sa,0));
 sigset_t blocked,original,after;sigemptyset(&blocked);
 sigaddset(&blocked,SIGTERM);sigaddset(&blocked,SIGQUIT);
 assert(!sigprocmask(SIG_SETMASK,0,&original));
 if(where==4)assert(!sigprocmask(SIG_BLOCK,&blocked,0));
 struct wr_iot_radio_stop_fence fence={0};
 assert(wr_iot_radio_stop_fence_begin(&fence));
 if(where==3){
  assert(!raise(requested_signal));
  assert(!wr_iot_radio_stop_fence_end_cleanup_unless_shutdown(&fence,cleanup,&cleaned));
  assert(!cleaned&&!stock&&fence.owner==getpid()&&wr_iot_rc_shutdown.active);
  assert(wr_iot_rc_shutdown.pending==requested_signal&&!wr_iot_rc_shutdown.normal_route_armed);
  return 0; /* No cleanup permission: fixture process owns remaining state. */
 }
 if(where==4)assert(!raise(requested_signal));
 assert(wr_iot_radio_stop_fence_end_cleanup_unless_shutdown(&fence,cleanup,&cleaned));
 assert(cleaned&&!fence.owner&&!wr_iot_rc_shutdown.active&&!stock);
 assert(!sigprocmask(SIG_SETMASK,0,&after));
 assert(sigismember(&after,SIGTERM)==(where==4?1:sigismember(&original,SIGTERM)));
 if(where==4)assert(!sigprocmask(SIG_SETMASK,&original,0));
 if(where==2)assert(!raise(requested_signal));
 assert(wr_iot_rc_shutdown.normal_route_requested==requested_signal);
 assert(!wr_iot_rc_shutdown.pending&&!stock&&!wr_iot_rc_shutdown_begin());
 assert(!raise(requested_signal==SIGTERM?SIGQUIT:SIGTERM));
 assert(wr_iot_rc_shutdown.normal_route_requested==requested_signal&&!stock);
 assert(!wr_iot_rc_shutdown_note(SIGPWR)&&!wr_iot_rc_shutdown_note(SIGSEGV));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-fence-publication-') as directory:
    root = Path(directory)
    source = root / 'test.c'
    binary = root / 'test'
    source.write_text(body)
    subprocess.run(['gcc', '-std=c11', '-D_POSIX_C_SOURCE=200809L', '-Wall',
                    '-Wextra', '-Werror', '-O2', '-fsanitize=address,undefined',
                    '-fno-pie', '-no-pie', '-I'+str(here), str(source),
                    str(here/'radio-stop-fence.c'), '-o', str(binary)], check=True)
    for where in range(5):
        for sig in range(2):
            subprocess.run([str(binary), str(where), str(sig)], check=True, timeout=10)
print('PASS real TERM/QUIT before/during/after cleanup route publication and inherited mask: '
      'first request retained; precleanup pending refuses cleanup; faults unchanged. '
      'Publication actor only: no ACTIVE readiness, automatic route or physical completion proof')
