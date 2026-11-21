"""Real signal/fence handoff into an inert-by-default PID1 shutdown slot."""
from pathlib import Path
import tempfile,subprocess
here=Path(__file__).resolve().parent
body=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <signal.h>
#include <string.h>
#include <unistd.h>
#include "rc-shutdown-admission.h"
#include "radio-stop-fence.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int stock,cleaned;
static void handler(int sig){if(!wr_iot_rc_shutdown_note(sig))stock++;}
static void cleanup(void*p){assert(p==&cleaned&&wr_iot_rc_shutdown.active);cleaned=1;}
int main(void){
 struct sigaction sa={0};sa.sa_handler=handler;sigemptyset(&sa.sa_mask);
 assert(!sigaction(SIGTERM,&sa,NULL)&&!sigaction(SIGQUIT,&sa,NULL));
 assert(!raise(SIGTERM)&&stock==1&&!wr_iot_rc_shutdown.normal_route_requested);
 assert(wr_iot_rc_shutdown_route_arm());assert(!raise(SIGTERM)&&stock==1&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 assert(!raise(SIGQUIT)&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM); /* first request wins */
 assert(!wr_iot_rc_shutdown_route_arm());
 assert(!wr_iot_rc_shutdown_begin()); /* no new ordinary owner after shutdown request */
 assert(!wr_iot_rc_shutdown_note(SIGPWR)&&!wr_iot_rc_shutdown_note(SIGSEGV));
 /* Fixture resets only: no production acknowledgement API is supplied. */
 wr_iot_rc_shutdown.normal_route_requested=0;
 struct wr_iot_radio_stop_fence fence={0};assert(wr_iot_radio_stop_fence_begin(&fence));
 assert(!wr_iot_rc_shutdown_route_arm());assert(!raise(SIGTERM));
 assert(!wr_iot_rc_shutdown.normal_route_requested&&!wr_iot_rc_shutdown.pending&&!cleaned);
 assert(wr_iot_radio_stop_fence_end_cleanup(&fence,cleanup,&cleaned));
 assert(cleaned&&!fence.owner&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending);
 assert(wr_iot_rc_shutdown.normal_route_requested==SIGTERM&&stock==1);
 /* A new signal after the last unmask is routed too; no active fence required. */
 assert(!raise(SIGQUIT)&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM&&stock==1);
 assert(!wr_iot_rc_shutdown_note(SIGPWR));
 /* Claim the retained request without clearing it or permitting ordinary work. */
 struct wr_iot_radio_stop_fence routed={0},other={0};
 assert(wr_iot_radio_stop_fence_begin_routed_shutdown(&routed));
 assert(wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.pending==SIGTERM);
 assert(wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 assert(!wr_iot_radio_stop_fence_begin(&other));
 assert(!wr_iot_radio_stop_fence_begin_routed_shutdown(&other));
 assert(!raise(SIGQUIT)); /* blocked duplicate cannot replace original intent */
 cleaned=0;
 assert(wr_iot_radio_stop_fence_end_cleanup(&routed,cleanup,&cleaned));
 assert(cleaned&&!routed.owner&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending);
 assert(stock==1&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 assert(!wr_iot_rc_shutdown_begin());
 /* Fixture-only reset: invalid/unarmed claims fail without publishing owner. */
 wr_iot_rc_shutdown.normal_route_requested=0;
 assert(!wr_iot_radio_stop_fence_begin_routed_shutdown(&routed)&&!routed.owner);
 wr_iot_rc_shutdown.normal_route_requested=SIGPWR;
 assert(!wr_iot_radio_stop_fence_begin_routed_shutdown(&routed)&&!routed.owner);
 wr_iot_rc_shutdown.normal_route_requested=SIGTERM;wr_iot_rc_shutdown.normal_route_armed=0;
 assert(!wr_iot_radio_stop_fence_begin_routed_shutdown(&routed)&&!routed.owner);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-normal-shutdown-route-') as d:
 p=Path(d)/'check.c';p.write_text(body);binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'radio-stop-fence.c'),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=10)
print('PASS inert normal-shutdown route: real SIGTERM/QUIT first request retained, transaction fence replay handed to PID1 slot after cleanup, late signal routed outside fence, faults unchanged; no production arm/physical-stop consumer')
