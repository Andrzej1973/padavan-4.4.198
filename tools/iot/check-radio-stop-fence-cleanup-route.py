"""Real TERM/QUIT during cleanup must queue the armed normal-shutdown route.

This exercises signal admission only, not the physical shutdown consumer.
"""
from pathlib import Path
import subprocess
import tempfile

here = Path(__file__).resolve().parent
body = r'''
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <signal.h>
#include <string.h>
#include <unistd.h>
#include "radio-stop-fence.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int cleaned,stock,signal_to_send;
static void handler(int sig){if(!wr_iot_rc_shutdown_note(sig))stock++;}
static void cleanup(void *context){
 int *owned=context;
 assert(*owned&&wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending);
 assert(!raise(signal_to_send));
 assert(wr_iot_rc_shutdown.pending==signal_to_send&&!stock);
 *owned=0;cleaned++;
}
int main(void){
 struct sigaction action={0};action.sa_handler=handler;sigemptyset(&action.sa_mask);
 assert(!sigaction(SIGTERM,&action,0)&&!sigaction(SIGQUIT,&action,0));
 for(int i=0;i<2;i++){
  struct wr_iot_radio_stop_fence fence={0};int owned=1;
  memset(&wr_iot_rc_shutdown,0,sizeof(wr_iot_rc_shutdown));
  signal_to_send=i?SIGQUIT:SIGTERM;
  assert(wr_iot_rc_shutdown_route_arm());
  assert(wr_iot_radio_stop_fence_begin(&fence));
  assert(wr_iot_radio_stop_fence_end_cleanup_unless_shutdown(&fence,cleanup,&owned));
  assert(!owned&&cleaned==i+1&&!fence.owner&&!stock);
  assert(!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending);
  assert(wr_iot_rc_shutdown.normal_route_requested==signal_to_send);
  assert(!wr_iot_rc_shutdown_begin());
  /* A later signal preserves the first requested shutdown, without stock exit. */
  assert(!raise(i?SIGTERM:SIGQUIT)&&!stock);
  assert(wr_iot_rc_shutdown.normal_route_requested==signal_to_send);
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-fence-cleanup-route-') as directory:
    root = Path(directory)
    source = root / 'test.c'
    source.write_text(body)
    binary = root / 'test'
    subprocess.run(['gcc', '-std=c11', '-D_POSIX_C_SOURCE=200809L', '-Wall', '-Wextra', '-Werror', '-O2',
                    '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                    '-I'+str(here), str(source), str(here/'radio-stop-fence.c'),
                    '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True, timeout=10)
print('PASS real TERM/QUIT during conditional fence cleanup: armed normal route '
      'retains first request after owner cleanup; no stock exit or new admission; '
      'physical shutdown consumer not exercised')
