#!/usr/bin/env python3
"""Execute private thaw using the boundary fixture's lock/ticket model."""
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
prefix=prefix.replace('unsigned flags;\n struct wr_iot_mcu_boot_ticket ticket;',
                      'unsigned flags; unsigned wr_iot_boot_dma_saved_valid;\n struct wr_iot_mcu_boot_ticket ticket;')
prefix=prefix[:prefix.index('static int wr_iot_mcu_boot_pse_empty')]
prefix=prefix.replace('static unsigned held, pse_ok, peer_ok, drift_after_pse;', 'static unsigned held,peer_ok;')
prefix+='''
#define fRTMP_ADAPTER_SUSPEND 8u
#define fRTMP_ADAPTER_START_UP 16u
#define fRTMP_ADAPTER_INTERRUPT_ACTIVE 32u
#define fRTMP_ADAPTER_MCU_SEND_IN_BAND_CMD 64u
#define RTMP_SET_FLAG(ad,f) ((ad)->flags|=(f))
'''
test=r'''
int main(void){
 for(unsigned fault=0;fault<9;fault++){
  RTMP_ADAPTER a={0};a.ticket=(struct wr_iot_mcu_boot_ticket){1,2,3,4,5};peer_ok=1;
  a.wr_iot_boot_frozen=1;a.wr_iot_boot_hw_state=2;a.wr_iot_boot_hw_stage=6;
  a.wr_iot_boot_ring_stage=4;a.wr_iot_boot_ctrl_state=a.wr_iot_boot_rx_state=2;
  a.wr_iot_boot_irq_state=a.wr_iot_boot_dma_state=a.wr_iot_boot_irq_unmask_state=2;
  a.wr_iot_boot_dma_saved_valid=a.wr_iot_boot_mcu_only=a.wr_iot_boot_epoch_done=1;
  a.wr_iot_boot_epoch_radio_serial=2;a.wr_iot_boot_epoch_radio_epoch=3;a.MCUCtrl.flags=1;a.flags=48;
  switch(fault){case 1:a.wr_iot_sequence.quarantined=2;break;case 2:a.wr_iot_boot_hw_stage=5;break;
  case 3:a.wr_iot_boot_epoch_radio_epoch++;break;case 4:a.flags|=8;break;case 5:a.flags=16;break;
  case 6:a.wr_iot_boot_dma_saved_valid=0;break;case 7:peer_ok=0;break;case 8:a.wr_iot_sequence.retired=2;break;}
  RTMP_ADAPTER before=a;
  assert(wr_iot_mcu_boot_thaw(&a,&a.ticket)==(fault?1:0)&&!held);
  if(fault)assert(!memcmp(&a,&before,sizeof(a)));
  else{assert(!a.wr_iot_boot_frozen&&(a.flags&64));assert(wr_iot_mcu_boot_thaw(&a,&a.ticket)==1);}
 }
 puts("PASS private thaw success, duplicate refusal and eight invalid contexts; injected owner/lock model");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-boot-thaw-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+(a.candidate/'include/wr-iot-mcu-boot-thaw.inc').read_text()+test)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
