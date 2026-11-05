#!/usr/bin/env python3
"""Actual ROM observer with injected MMIO/ticket races; no epoch reset."""
import argparse
import ast
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
tree=ast.parse(Path(__file__).with_name('check-mcu-boot-hardware.py').read_text())
node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='fixture' for t in n.targets))
prefix=ast.literal_eval(node.value.left.left.func.value)
sdk=(a.candidate/'include/iface/rtmp_reg_pcirbs.h').read_text()
start=sdk.rfind('#ifdef RT_BIG_ENDIAN',0,sdk.index('typedef\tunion _WPDMA_GLO_CFG_STRUC'))
end=sdk.index('#endif /* RT_BIG_ENDIAN */',start)+len('#endif /* RT_BIG_ENDIAN */')
prefix=prefix.replace('@@LAYOUT@@',sdk[start:end])
prefix=prefix.replace('unsigned ledger[5];','unsigned wr_iot_boot_rom_kind;unsigned long wr_iot_boot_rom_peer_serial,wr_iot_boot_rom_radio_serial,wr_iot_boot_rom_radio_epoch;struct {unsigned messages;} wr_iot_mcu_sender_owner;unsigned ledger[5];')
fixture=prefix+(a.candidate/'include/wr-iot-mcu-boot-hardware.inc').read_text()+r'''
static RTMP_ADAPTER *current;
static int wr_iot_mcu_sender_drained(void *s){assert(s&&held==2);return 1;}
static unsigned rom_read(void){reads++;if(fault==1||(fault==2&&reads==2))return 2;if(fault==3)return ~0u;return 1;}
#undef RTMP_IO_READ32
#define RTMP_IO_READ32(ad,reg,out) do{assert(ad==current&&!held&&(reg)==0x1134);*(out)=rom_read();}while(0)
#define RtmpusecDelay(n) do{assert((n)==1000&&!held);if(fault==11)current->ticket.radio_epoch++;if(fault==12)current->flags|=1;if(fault==16)current->ticket.peer_serial++;}while(0)
'''+(a.candidate/'include/wr-iot-mcu-boot-rom-observe.inc').read_text()+r'''
int main(void){
 for(unsigned restarted=0;restarted<2;restarted++)for(fault=0;fault<=16;fault++){
  RTMP_ADAPTER ad={0};current=&ad;ad.ticket=(struct wr_iot_mcu_boot_ticket){1,2,3,4,5};
  held=calls=reads=aborts=stops=0;context=1;ad.MCUCtrl.flags=ad.wr_iot_boot_mcu_only=1;
  for(unsigned i=0;i<5;i++)ad.ledger[i]=100+i;
  struct wr_iot_mcu_boot_ticket supplied=ad.ticket;
  unsigned acked=restarted;
  switch(fault){case 4:ad.wr_iot_mcu_sender_owner.messages=1;break;case 5:ad.wr_iot_boot_frozen=1;break;
   case 6:ad.MCUCtrl.flags=0;break;case 7:ad.wr_iot_boot_mcu_only=0;break;case 8:ad.wr_iot_boot_hw_state=1;break;
   case 9:ad.wr_iot_boot_rom_kind=1;break;case 10:supplied.peer_serial++;break;case 13:acked=2;break;
   case 14:ad.wr_iot_boot_ring_stage=1;break;case 15:ad.flags=1;break;}
  const struct wr_iot_mcu_boot_ticket *t=fault==10?&supplied:&ad.ticket;
  assert(wr_iot_mcu_boot_rom_observe(&ad,t,acked)==(fault?1:0)&&!held&&!calls&&!aborts&&!stops);
  if((fault>=4&&fault<=10)||(fault>=13&&fault<=15))assert(!reads);
  for(unsigned i=0;i<5;i++)assert(ad.ledger[i]==100+i);
  if(!fault){assert(ad.wr_iot_boot_rom_kind==restarted+1&&ad.wr_iot_boot_rom_peer_serial==1&&ad.wr_iot_boot_rom_radio_serial==2&&ad.wr_iot_boot_rom_radio_epoch==3);assert(wr_iot_mcu_boot_rom_observe(&ad,t,acked)==1&&reads==2);}
  else assert(ad.wr_iot_boot_rom_kind==(fault==9?1u:0u)&&!ad.wr_iot_boot_rom_radio_serial&&!ad.wr_iot_boot_rom_radio_epoch);
 }
 puts("PASS actual ROM observer: cold/restart provenance, two ROM reads, bus/state/owner/message refusal, ticket/NIC race and duplicate rejection; ledger unchanged, MMIO injected, no epoch grant");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-rom-observe-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
