#!/usr/bin/env python3
"""Execute actual IRQ owner coordinator with the existing injected RX harness."""
import argparse
import ast
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
# Reuse only the literal C harness; never execute another Python checker.
tree=ast.parse(Path(__file__).with_name('check-mcu-boot-rx-restart.py').read_text())
assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='fixture' for t in n.targets))
prefix=ast.literal_eval(assignment.value.left.left)
prefix=prefix.replace('wr_iot_boot_mcu_only;','wr_iot_boot_mcu_only,wr_iot_boot_irq_state,wr_iot_boot_dma_state,wr_iot_boot_dma_saved_valid,wr_iot_boot_dma_stop_verified;')
prefix=prefix.replace('fault==11&&ad->wr_iot_boot_mcu_only&&++late_checks==2',
                      'fault==11&&ad->wr_iot_boot_dma_state==1&&++late_checks==3')
fixture=prefix+(a.candidate/'include/wr-iot-mcu-boot-rx-restart.inc').read_text()+r'''
INT32 wr_iot_mcu_boot_dma_start(RTMP_ADAPTER *ad);
INT32 wr_iot_mcu_boot_dma_owned(RTMP_ADAPTER *ad);
static int wr_iot_mcu_boot_other_tx_idle(RTMP_ADAPTER *ad){assert(ad&&!held);return fault==10?1:0;}
static unsigned stops;
static int wr_iot_mcu_boot_dma_start_hw(RTMP_ADAPTER *ad){
 assert(!held&&wr_iot_mcu_boot_dma_owned(ad));initialized++;ad->wr_iot_boot_dma_saved_valid=1;
 if(fault==5)assert(wr_iot_mcu_boot_dma_start(ad)==1&&!ad->wr_iot_boot_failed);
 if(fault==3)context=0;
 return fault==2||fault==9||fault==13?1:0;
}
static int wr_iot_mcu_boot_dma_stop_hw(RTMP_ADAPTER *ad){assert(!held&&ad->wr_iot_boot_dma_state==1&&initialized==1);stops++;ad->wr_iot_boot_dma_stop_verified=fault==13?0:1;return fault==13?1:0;}
'''+(a.candidate/'include/wr-iot-mcu-boot-dma-owner.inc').read_text()+r'''
int main(void){
 for(fault=0;fault<=13;fault++){
  RTMP_ADAPTER ad={0};held=initialized=joined=late_checks=stops=0;context=1;
  ad.MCUCtrl.flags=1;ad.wr_iot_boot_ticket.peer_serial=1;ad.wr_iot_boot_frozen=1;
  ad.wr_iot_boot_ring_stage=4;ad.wr_iot_boot_ctrl_state=ad.wr_iot_boot_rx_state=2;ad.wr_iot_boot_mcu_only=1;
  for(unsigned i=0;i<5;i++)ad.ledger[i]=100+i;
  ad.wr_iot_boot_irq_state=2;
  if(fault==6)ad.wr_iot_boot_irq_state=1;
  if(fault==7)ad.wr_iot_boot_dma_state=2;
  if(fault==12)ad.wr_iot_mcu_sender_owner.messages=1;
  unsigned success=fault==0||fault==5;
  unsigned refused=fault==1||fault==4||fault==6||fault==7||fault==8||fault==10||fault==12;
  assert(wr_iot_mcu_boot_dma_start(&ad)==(success?0:1)&&!held);
  for(unsigned i=0;i<5;i++)assert(ad.ledger[i]==100+i);
  assert(ad.wr_iot_boot_frozen&&ad.MCUCtrl.flags==1&&ad.wr_iot_boot_mcu_only&&!joined);
  if(refused){assert(!initialized&&!ad.wr_iot_boot_failed);continue;}
  assert(initialized==1&&ad.wr_iot_boot_dma_state==(success?2u:fault==13?4u:3u));
  assert(ad.wr_iot_boot_failed==(unsigned)!success&&stops==(unsigned)!success);
  assert(wr_iot_mcu_boot_dma_start(&ad)==1&&initialized==1);
 }
 puts("PASS actual DMA owner: exclusive lease, stage/idle/other-TX gates, nested/duplicate refusal, hardware/context/final failure and verified vs unknown stop; hardware actor injected, no epoch proof");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-dma-owner-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
