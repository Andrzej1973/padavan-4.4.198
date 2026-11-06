#!/usr/bin/env python3
"""Execute scheduler lease with injected context and lock model."""
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
prefix=prefix[:prefix.index('static int wr_iot_mcu_boot_pse_empty')]
prefix=prefix.replace('static unsigned held, pse_ok, peer_ok, drift_after_pse;','static unsigned held,peer_ok;')
prefix=prefix.replace('struct wr_iot_mcu_boot_ticket ticket;',
 'unsigned wr_iot_boot_active,wr_iot_boot_failed,wr_iot_boot_scheduler_state,bPCIclkOff;struct wr_iot_mcu_boot_ticket ticket;')
prefix=prefix.replace('typedef struct { unsigned flags; } MCU;', 'typedef struct { unsigned flags,Stage; } MCU;')
prefix+='\n#define wr_iot_boot_ticket ticket\n#define FW_RUN_TIME 3\n#define fRTMP_ADAPTER_SUSPEND 8u\n'
prefix+=r'''
static unsigned hw_fail,aborted;
INT32 wr_iot_mcu_boot_scheduler_finish(RTMP_ADAPTER *,const struct wr_iot_mcu_boot_ticket *,int);
static int wr_iot_mcu_boot_scheduler_check(RTMP_ADAPTER *ad){assert(!held&&ad->wr_iot_boot_scheduler_state==1&&ad->wr_iot_boot_frozen);return hw_fail;}
static int wr_iot_mcu_boot_loader_abort(RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *t){assert(ad&&t&&!held&&ad->wr_iot_boot_failed);aborted++;return 0;}
'''
tail=r'''
int main(void){for(unsigned fault=0;fault<5;fault++){
 RTMP_ADAPTER a={0};a.ticket=(struct wr_iot_mcu_boot_ticket){1,2,3,4,5};
 a.wr_iot_boot_active=1;a.wr_iot_boot_hw_state=2;a.wr_iot_boot_hw_stage=6;a.MCUCtrl.Stage=3;peer_ok=1;
 struct wr_iot_mcu_boot_ticket t=a.ticket;
 if(fault==1)a.wr_iot_sequence.quarantined=2;
 assert(wr_iot_mcu_boot_scheduler_claim(&a,&t)==(fault==1?1:0)&&!held);
 if(fault==1){assert(!a.wr_iot_boot_scheduler_state&&!a.wr_iot_boot_frozen);continue;}
 assert(a.wr_iot_boot_frozen&&a.wr_iot_boot_scheduler_state==1);
  assert(wr_iot_mcu_boot_scheduler_owned(&a));
 assert(wr_iot_mcu_boot_scheduler_claim(&a,&t)==1);
 if(fault==2)peer_ok=0;
  if(fault==2)assert(!wr_iot_mcu_boot_scheduler_owned(&a));
 if(fault==3)t.close_epoch++;
 assert(wr_iot_mcu_boot_scheduler_finish(&a,&t,fault!=4)==(fault?1:0)&&!held);
 if(fault==3){assert(a.wr_iot_boot_scheduler_state==1);continue;}
 assert(a.wr_iot_boot_scheduler_state==(fault?3u:2u)&&a.wr_iot_boot_frozen);
 assert(a.wr_iot_boot_failed==(unsigned)(fault!=0));
 assert(wr_iot_mcu_boot_scheduler_finish(&a,&t,1)==1);
}
for(hw_fail=0;hw_fail<2;hw_fail++){
 RTMP_ADAPTER a={0};a.ticket=(struct wr_iot_mcu_boot_ticket){1,2,3,4,5};
 a.wr_iot_boot_active=1;a.wr_iot_boot_hw_state=2;a.wr_iot_boot_hw_stage=6;a.MCUCtrl.Stage=3;peer_ok=1;aborted=0;
 assert(wr_iot_mcu_boot_scheduler_run(&a,&a.ticket)==(int)hw_fail);
 assert(aborted==hw_fail&&a.wr_iot_boot_frozen&&a.wr_iot_boot_scheduler_state==(hw_fail?3u:2u));
}
puts("PASS scheduler claim/finish/run: freeze, duplicate, quarantine, wrong ticket, peer loss and hardware abort; context/locks/hardware injected");}
'''
with tempfile.TemporaryDirectory(prefix='wr-scheduler-owner-') as td:
 tail=tail.replace('a.wr_iot_boot_active=1;',
  'a.wr_iot_boot_ctrl_state=a.wr_iot_boot_rx_state=a.wr_iot_boot_irq_state=a.wr_iot_boot_dma_state=a.wr_iot_boot_irq_unmask_state=2;a.wr_iot_boot_mcu_only=1;a.wr_iot_boot_active=1;')
 c=Path(td)/'test.c';c.write_text(prefix+(a.candidate/'include/wr-iot-mcu-boot-scheduler-owner.inc').read_text()+tail)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/test'],check=True)
 subprocess.run([td+'/test'],check=True)
