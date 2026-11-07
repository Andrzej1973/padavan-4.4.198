#!/usr/bin/env python3
"""Execute loader abort with injected IRQ/DMA outcomes and retained ticket."""
import ast
import argparse
from pathlib import Path
import subprocess
import tempfile
root=Path(__file__).parent
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path)
a=p.parse_args()
tree=ast.parse((root/'check-mcu-boot-retired-boundary.py').read_text())
prefix=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
 and any(isinstance(t,ast.Name) and t.id=='prefix' for t in n.targets))
prefix=prefix[:prefix.index('static int wr_iot_mcu_boot_context_matches')]
prefix=prefix.replace('static unsigned held, pse_ok, peer_ok, drift_after_pse;', 'static unsigned held,calls,irq_fail,dma_fail;')
prefix=prefix.replace('unsigned flags;\n struct wr_iot_mcu_boot_ticket ticket;',
 'unsigned flags; unsigned wr_iot_boot_active,wr_iot_boot_failed,wr_iot_boot_dma_stop_verified;\n struct wr_iot_mcu_boot_ticket wr_iot_boot_ticket;')
prefix+=r'''
#define fRTMP_ADAPTER_MCU_SEND_IN_BAND_CMD 64u
#define RTMP_CLEAR_FLAG(ad,f) ((ad)->flags&=~(f))
static int wr_iot_nettask_boot_irq_abort(RTMP_ADAPTER *ad){
 assert(!held&&calls++==0&&ad->wr_iot_boot_failed&&ad->wr_iot_boot_frozen&&!(ad->flags&64));return irq_fail;
}
static int wr_iot_mcu_boot_dma_stop_hw(RTMP_ADAPTER *ad){
 assert(!held&&calls++==1&&!ad->wr_iot_boot_dma_stop_verified);
 ad->wr_iot_boot_dma_stop_verified=!dma_fail;return dma_fail;
}
'''
test=r'''
int main(void){
 for(unsigned fault=0;fault<4;fault++){
  RTMP_ADAPTER a={0};a.wr_iot_boot_ticket=(struct wr_iot_mcu_boot_ticket){1,2,3,4,5};
  struct wr_iot_mcu_boot_ticket t=a.wr_iot_boot_ticket;
  a.wr_iot_boot_active=1;a.wr_iot_boot_hw_state=2;a.flags=64;a.wr_iot_boot_dma_stop_verified=1;
  calls=0;irq_fail=fault==1;dma_fail=fault==2;if(fault==3)t.close_epoch++;
  assert(wr_iot_mcu_boot_loader_abort(&a,&t)==(fault?1:0)&&!held);
  if(fault==3){assert(!calls&&a.wr_iot_boot_hw_state==2&&a.flags==64);continue;}
  assert(calls==2&&a.wr_iot_boot_hw_state==3&&a.wr_iot_boot_irq_unmask_state==3);
  assert(a.wr_iot_boot_dma_state==(dma_fail?4u:3u));
  assert(wr_iot_mcu_boot_loader_abort(&a,&t)==1&&calls==2);
 }
 puts("PASS loader abort: IRQ before DMA, stale proof cleared, unknown stop retained, wrong ticket and duplicate refused; hardware injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-loader-abort-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+(a.candidate/'include/wr-iot-mcu-boot-loader-abort.inc').read_text()+test)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
