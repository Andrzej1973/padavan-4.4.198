#!/usr/bin/env python3
"""Execute actual periodic callback/enqueue after injected allocation/queue failure.
No worker scheduling, firmware, or hardware execution is modeled.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('driver',type=Path)
a=p.parse_args()
text=(a.driver/'common/cmm_cmd.c').read_text()
start=text.index('static NDIS_STATUS wr_enqueue_internal_cmd(')
end=text.index('\n}',text.index('NDIS_STATUS wr_iot_enqueue_internal_cmd(',start))+2
unit=text[start:end]
mlme=(a.driver/'common/mlme.c').read_text()
start=mlme.index('VOID MlmePeriodicExecTimer(')
callback=mlme[start:mlme.index('\n}',start)+2]
prefix=Path(__file__).with_name('check-checked-enqueue-prefix.inc').read_text()
prefix='#include "terminal-command-owner.h"\n#define MT7603 1\n#define DMA_RESET_SUPPORT 1\n'+prefix
prefix=prefix.replace('unsigned int flags;int CmdQLock', 'struct wr_iot_terminal_command_owner wr_iot_terminal_command;unsigned int flags;int CmdQLock')
prefix+='\n#define IN\n#define VOID void\ntypedef struct adapter RTMP_ADAPTER;\n#define CMDTHREAD_MLME_PERIOIDC_EXEC 7\n'
main=r'''
int main(void){
 struct adapter ad={0};
 wr_iot_terminal_command_init(&ad.wr_iot_terminal_command,1);
 /* Separate failed callback then successful callback; no fake immediate retry. */
 for(int mode=0;mode<2;mode++){
  allocations=frees=held=queued=wakes=0;owned=NULL;
  fail_at=mode==0?1:0;ad.CmdQ.CmdQState=mode==0?1:0;
  MlmePeriodicExecTimer(NULL,&ad,NULL,NULL);
  assert(!held&&!owned&&!queued&&!wakes);
  assert(allocations==1&&frees==(mode==0?0:1));
  fail_at=0;ad.CmdQ.CmdQState=1;
  MlmePeriodicExecTimer(NULL,&ad,NULL,NULL);
  assert(!held&&owned&&queued==1&&wakes==1);
  assert(owned->command==CMDTHREAD_MLME_PERIOIDC_EXEC);
  assert(!owned->buffer&&!owned->bufferlength);
  os_free_mem(&ad,owned);owned=NULL;
 }
 /* Terminal retirement cannot be undone by a later timer tick, even if the
  * legacy queue-state bit appears insertable. Exercise actual owner predicate. */
 assert(wr_iot_terminal_command_close(&ad.wr_iot_terminal_command,1));
 ad.CmdQ.CmdQState=1;
 for(int tick=0;tick<3;tick++){
  int old_wakes=wakes,old_queued=queued,old_frees=frees;
  MlmePeriodicExecTimer(NULL,&ad,NULL,NULL);
  assert(!owned&&!held&&wakes==old_wakes&&queued==old_queued);
  assert(frees==old_frees+1);
 }
 puts("PASS actual periodic callback/enqueue: allocation failure or closed queue followed by successful later tick; terminal fence rejects later ticks; callback delivery/worker/hardware not proved");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-iot-periodic-enqueue-') as d:
 source=Path(d)/'test.c';exe=Path(d)/'test'
 source.write_text(prefix+unit+'\n'+callback+'\n'+main)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.driver/'include'),str(source),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
