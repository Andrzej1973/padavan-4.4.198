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
prefix=prefix.replace('wr_iot_boot_mcu_only;','wr_iot_boot_mcu_only,wr_iot_boot_irq_state,wr_iot_boot_dma_state,wr_iot_boot_dma_saved_valid,wr_iot_boot_dma_stop_verified,wr_iot_boot_irq_unmask_state,wr_iot_boot_irq_startup_owned,flags;')
prefix=prefix.replace('fault==11&&ad->wr_iot_boot_mcu_only&&++late_checks==2',
                      'fault==11&&ad->wr_iot_boot_irq_unmask_state==1&&++late_checks==3')
prefix=prefix.replace('assert(held==2&&t==&ad->wr_iot_boot_ticket);','assert(held==2&&t==&ad->wr_iot_boot_ticket);if(fault==14&&ad->wr_iot_boot_irq_unmask_state==1&&++late_checks==3)ad->flags|=1;')
prefix+='#define RTMP_TEST_FLAG(ad,f) ((ad)->flags&(f))\n#define fRTMP_ADAPTER_NIC_NOT_EXIST 1u\n#define fRTMP_ADAPTER_RESET_IN_PROGRESS 2u\n#define fRTMP_ADAPTER_HALT_IN_PROGRESS 4u\n'
fixture=prefix+(a.candidate/'include/wr-iot-mcu-boot-rx-restart.inc').read_text()+r'''
INT32 wr_iot_mcu_boot_irq_unmask(RTMP_ADAPTER *ad);
INT32 wr_iot_mcu_boot_irq_unmask_owned(RTMP_ADAPTER *ad);
static unsigned stops,aborts;
static int wr_iot_nettask_boot_irq_abort(RTMP_ADAPTER *ad){assert(!held&&ad->wr_iot_boot_irq_unmask_state==1);aborts++;return 0;}
static int wr_iot_nettask_boot_irq_unmask(RTMP_ADAPTER *ad){
 assert(!held&&wr_iot_mcu_boot_irq_unmask_owned(ad));initialized++;ad->wr_iot_boot_dma_saved_valid=1;
 if(fault==5)assert(wr_iot_mcu_boot_irq_unmask(ad)==1&&!ad->wr_iot_boot_failed);
 if(fault==3)context=0;
 return fault==2||fault==9||fault==13?1:0;
}
static int wr_iot_mcu_boot_dma_stop_hw(RTMP_ADAPTER *ad){assert(!held&&ad->wr_iot_boot_dma_state==1&&initialized==1&&aborts==1);stops++;ad->wr_iot_boot_dma_stop_verified=fault==13?0:1;return fault==13?1:0;}
'''+(a.candidate/'include/wr-iot-mcu-boot-irq-unmask-owner.inc').read_text()+r'''
int main(void){
 for(fault=0;fault<=14;fault++){
  RTMP_ADAPTER ad={0};held=initialized=joined=late_checks=stops=aborts=0;context=1;
  ad.MCUCtrl.flags=1;ad.wr_iot_boot_ticket.peer_serial=1;ad.wr_iot_boot_frozen=1;
  ad.wr_iot_boot_ring_stage=4;ad.wr_iot_boot_ctrl_state=ad.wr_iot_boot_rx_state=2;ad.wr_iot_boot_mcu_only=1;
  for(unsigned i=0;i<5;i++)ad.ledger[i]=100+i;
  ad.wr_iot_boot_irq_state=2;
  ad.wr_iot_boot_dma_state=2;ad.wr_iot_boot_dma_saved_valid=1;
  if(fault==1)ad.flags=4;
  if(fault==4)ad.flags=2;
  if(fault==8)ad.flags=1;
  if(fault==10)ad.wr_iot_boot_dma_saved_valid=0;
  if(fault==6)ad.wr_iot_boot_dma_state=1;
  if(fault==7)ad.wr_iot_boot_irq_unmask_state=2;
  if(fault==12)ad.wr_iot_mcu_sender_owner.messages=1;
  unsigned success=fault==0||fault==5;
  unsigned refused=fault==1||fault==4||fault==6||fault==7||fault==8||fault==10||fault==12;
  assert(wr_iot_mcu_boot_irq_unmask(&ad)==(success?0:1)&&!held);
  for(unsigned i=0;i<5;i++)assert(ad.ledger[i]==100+i);
  assert(ad.wr_iot_boot_frozen&&ad.MCUCtrl.flags==1&&ad.wr_iot_boot_mcu_only&&!joined);
  if(refused){assert(!initialized&&!ad.wr_iot_boot_failed);continue;}
  assert(initialized==1&&ad.wr_iot_boot_irq_unmask_state==(success?2u:3u)&&ad.wr_iot_boot_dma_state==(success?2u:fault==13?4u:3u));
  assert(ad.wr_iot_boot_failed==(unsigned)!success&&stops==(unsigned)!success&&aborts==stops);
  assert(wr_iot_mcu_boot_irq_unmask(&ad)==1&&initialized==1);
 }
 puts("PASS actual IRQ unmask owner: exclusive frozen lease, stage/device flags, nested/duplicate refusal, helper/final failure, abort before verified/unknown DMA stop; leaf/OS injected, no epoch proof");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-irq-unmask-owner-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
