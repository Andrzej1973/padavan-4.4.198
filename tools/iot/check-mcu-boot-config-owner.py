#!/usr/bin/env python3
"""Exercise actual configuration ownership and task-reference lifetime."""
import argparse
import ast
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
tree=ast.parse(Path(__file__).with_name('check-mcu-boot-retired-boundary.py').read_text())
prefix=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prefix' for t in n.targets))
prefix=prefix[:prefix.index('static int wr_iot_mcu_boot_pse_empty')]
prefix=prefix.replace('static unsigned held, pse_ok, peer_ok, drift_after_pse;','static unsigned held,peer_ok;')
prefix=prefix.replace('typedef struct { unsigned flags; } MCU;', 'typedef struct { unsigned flags,Stage; } MCU;')
prefix=prefix.replace('struct wr_iot_mcu_boot_ticket ticket;',
 'unsigned wr_iot_boot_config_state,wr_iot_boot_active,wr_iot_boot_failed,wr_iot_boot_scheduler_state,wr_iot_boot_fw_state,bPCIclkOff;unsigned long wr_iot_boot_fw_radio_serial,wr_iot_boot_fw_radio_epoch;struct task_struct *wr_iot_boot_config_task;struct wr_iot_mcu_boot_ticket ticket;')
prefix+=r'''
#define wr_iot_boot_ticket ticket
#define FW_RUN_TIME 3
#define fRTMP_ADAPTER_SUSPEND 8u
struct task_struct {unsigned refs;};
static struct task_struct owner,foreign,*current;
static void get_task_struct(struct task_struct *task){assert(task&&!held);task->refs++;}
static void put_task_struct(struct task_struct *task){assert(task&&!held&&task->refs);task->refs--;}
'''
tail=r'''
static RTMP_ADAPTER valid(void){
 RTMP_ADAPTER ad={0};ad.ticket=(struct wr_iot_mcu_boot_ticket){1,2,3,4,5};
 ad.wr_iot_boot_active=ad.wr_iot_boot_frozen=ad.wr_iot_boot_mcu_only=1;
 ad.wr_iot_boot_hw_state=2;ad.wr_iot_boot_hw_stage=6;
 ad.wr_iot_boot_fw_state=ad.wr_iot_boot_scheduler_state=2;
 ad.wr_iot_boot_fw_radio_serial=2;ad.wr_iot_boot_fw_radio_epoch=3;
 ad.wr_iot_boot_ctrl_state=ad.wr_iot_boot_rx_state=ad.wr_iot_boot_irq_state=2;
 ad.wr_iot_boot_dma_state=ad.wr_iot_boot_irq_unmask_state=2;ad.MCUCtrl.Stage=FW_RUN_TIME;
 return ad;
}
int main(void){unsigned fault;
for(fault=0;fault<8;fault++){
 RTMP_ADAPTER ad=valid();struct wr_iot_mcu_boot_ticket t=ad.ticket;
 current=&owner;peer_ok=1;assert(!owner.refs&&!foreign.refs);
 assert(!wr_iot_mcu_boot_config_begin(&ad,&t)&&owner.refs==1&&ad.wr_iot_boot_config_task==current);
 assert(wr_iot_mcu_boot_config_begin(&ad,&t)==1&&owner.refs==1);
 switch(fault){case 1:current=&foreign;break;case 2:t.close_epoch++;break;
 case 3:peer_ok=0;break;case 4:ad.wr_iot_boot_dma_state=1;break;
 case 5:ad.wr_iot_boot_failed=1;break;case 6:ad.wr_iot_mcu_sender_owner.messages=1;break;}
 assert(wr_iot_mcu_boot_config_finish(&ad,&t,fault!=7)==(fault?1:0));
 if(fault==1||fault==2){
 assert(owner.refs==1&&ad.wr_iot_boot_config_state==1);current=&owner;t=ad.ticket;
 assert(!wr_iot_mcu_boot_config_finish(&ad,&t,1));
 }else assert(ad.wr_iot_boot_config_state==(fault?3u:2u));
 assert(!owner.refs&&!foreign.refs&&!ad.wr_iot_boot_config_task&&ad.wr_iot_boot_frozen);
 assert(wr_iot_mcu_boot_config_finish(&ad,&t,1)==1&&!owner.refs);
}
for(fault=0;fault<7;fault++){
 RTMP_ADAPTER ad=valid();peer_ok=1;current=&owner;
 switch(fault){case 0:ad.wr_iot_boot_fw_state=0;break;case 1:ad.wr_iot_boot_scheduler_state=0;break;
 case 2:ad.wr_iot_boot_fw_radio_epoch++;break;case 3:ad.wr_iot_boot_frozen=0;break;
 case 4:ad.wr_iot_sequence.quarantined=2;break;case 5:ad.bPCIclkOff=1;break;case 6:ad.flags=8;break;}
 assert(wr_iot_mcu_boot_config_begin(&ad,&ad.ticket)==1&&!owner.refs&&!ad.wr_iot_boot_config_state);
}
puts("PASS configuration owner: task pin/release, foreign task/ticket refusal, duplicate, stale receipts, drained state, retained failure and no constructor thaw; context/locks/task references injected");}
'''
with tempfile.TemporaryDirectory(prefix='wr-config-owner-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+(a.candidate/'include/wr-iot-mcu-boot-config-owner.inc').read_text()+tail)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
