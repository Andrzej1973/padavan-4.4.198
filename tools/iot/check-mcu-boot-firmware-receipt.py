#!/usr/bin/env python3
"""Execute receipt commit against ticket, epoch and hardware-state failures."""
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
 'unsigned wr_iot_boot_fw_state,wr_iot_boot_failed,bPCIclkOff;unsigned long wr_iot_boot_fw_radio_serial,wr_iot_boot_fw_radio_epoch;struct wr_iot_mcu_boot_ticket ticket;')
prefix=prefix.replace('unsigned wr_iot_boot_fw_state,','unsigned wr_iot_boot_fw_retired,wr_iot_boot_fw_cursor;unsigned wr_iot_boot_fw_state,')
prefix+='#define FW_RUN_TIME 3\n#define fRTMP_ADAPTER_SUSPEND 8u\n'
tail=r'''
int main(void){unsigned fault;
 for(fault=0;fault<20;fault++){
 RTMP_ADAPTER ad={0};struct wr_iot_mcu_boot_ticket t={1,2,3,4,5};ad.ticket=t;peer_ok=1;
 ad.wr_iot_boot_hw_state=2;ad.wr_iot_boot_hw_stage=6;
 ad.wr_iot_boot_ctrl_state=ad.wr_iot_boot_rx_state=ad.wr_iot_boot_irq_state=2;
 ad.wr_iot_boot_dma_state=ad.wr_iot_boot_irq_unmask_state=2;
 ad.wr_iot_boot_mcu_only=ad.wr_iot_boot_epoch_done=1;
 ad.wr_iot_boot_epoch_radio_serial=2;ad.wr_iot_boot_epoch_radio_epoch=3;ad.MCUCtrl.Stage=FW_RUN_TIME;
 ad.wr_iot_sequence.retired=6;ad.wr_iot_sequence.cursor=2;
 switch(fault){
 case 1:peer_ok=0;break;case 2:t.radio_epoch++;break;case 3:ad.wr_iot_boot_frozen=1;break;
 case 4:ad.wr_iot_boot_failed=1;break;case 5:ad.bPCIclkOff=1;break;
 case 6:ad.wr_iot_boot_hw_stage=5;break;case 7:ad.wr_iot_boot_ctrl_state=1;break;
 case 8:ad.wr_iot_boot_rx_state=1;break;case 9:ad.wr_iot_boot_irq_state=1;break;
 case 10:ad.wr_iot_boot_dma_state=1;break;case 11:ad.wr_iot_boot_irq_unmask_state=1;break;
 case 12:ad.wr_iot_boot_epoch_radio_epoch++;break;case 13:ad.wr_iot_boot_epoch_radio_serial++;break;
 case 14:ad.MCUCtrl.Stage=1;break;case 15:ad.wr_iot_mcu_sender_owner.messages=1;break;
 case 16:ad.wr_iot_sequence.occupied=2;break;case 17:ad.wr_iot_sequence.quarantined=2;break;
 case 18:ad.wr_iot_sequence.poisoned=1;break;case 19:ad.flags=8;break;
 }
 assert(wr_iot_mcu_boot_firmware_receipt(&ad,&t)==(fault?1:0));assert(!held);
 if(fault)assert(!ad.wr_iot_boot_fw_state&&!ad.wr_iot_boot_fw_radio_serial&&!ad.wr_iot_boot_fw_radio_epoch);
 else {assert(ad.wr_iot_boot_fw_retired==6&&ad.wr_iot_boot_fw_cursor==2&&ad.wr_iot_sequence.retired==6);assert(ad.wr_iot_boot_frozen&&ad.wr_iot_boot_fw_state==2&&ad.wr_iot_boot_fw_radio_serial==2&&ad.wr_iot_boot_fw_radio_epoch==3);
 assert(wr_iot_mcu_boot_firmware_receipt(&ad,&t)==1);}
 }
 puts("PASS actual firmware receipt: exact ticket/epoch, duplicate refusal, hardware/constructor/ledger/device failure gates; context/locks injected, no hardware proof");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-fw-receipt-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+(a.candidate/'include/wr-iot-mcu-boot-firmware-receipt.inc').read_text()+tail)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
