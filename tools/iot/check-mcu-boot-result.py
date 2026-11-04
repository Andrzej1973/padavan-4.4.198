#!/usr/bin/env python3
"""Execute actual checked dispatcher/wrapper for boot responses; mocked transport."""
import argparse
from pathlib import Path
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
tests=r'''
 generic_calls=0;
 for(unsigned command_index=0;command_index<3;command_index++){
  unsigned command=(unsigned[]){1,2,0xef}[command_index];
  struct event boot=ev;struct packet boot_packet=pkt;
  boot.fw_rxd_1.field.eid=command==0xef?0xef:1;
  boot.fw_rxd_0.field.length=sizeof(boot);boot_packet.size=sizeof(boot);
  for(unsigned status=0;status<7;status++){
   msg=base;msg.cmd_type=command;msg.ext_cmd_type=0;
   boot.fw_rxd_2.field.ext_eid=status;
   dispatch(&msg,&boot,&boot_packet);
   assert(msg.wr_iot_firmware_result==(status?1:0)&&msg.ack_done==1&&!generic_calls);
   boot.fw_rxd_2.field.ext_eid=status?0:1;
   dispatch(&msg,&boot,&boot_packet);
   assert(msg.wr_iot_firmware_result==(status?1:0)&&msg.ack_done==1);
  }
  boot.fw_rxd_2.field.ext_eid=0;
  for(unsigned fault=0;fault<5;fault++){
   struct event wrong=boot;struct packet packet=boot_packet;
   msg=base;msg.cmd_type=command;msg.ext_cmd_type=0;
   if(fault==0)wrong.fw_rxd_1.field.eid=command==0xef?1:0xef;
   if(fault==1)packet.size++;
   if(fault==2)wrong.fw_rxd_0.field.length++;
   if(fault==3)msg.ext_cmd_type=1;
   if(fault==4)msg.cmd_type=5; /* ROM patch remains outside this change. */
   dispatch(&msg,&wrong,&packet);
   assert(msg.wr_iot_firmware_result==1&&msg.ack_done==1&&!generic_calls);
  }
 }
 puts("PASS extracted boot ACK status, exact envelope, command/EID selection and duplicate completion; no generic callback");
'''
wrapper_prefix=r'''
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include "mcu-sender-owner.h"
#include "mcu-boot-result.h"
typedef int INT32;typedef unsigned long ULONG;
#define EXT_CID 0xed
#define EXT_CMD_RADIO_ON_OFF_CTRL 5
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE -1
typedef struct {int wr_iot_mcu_sender_lock,wr_iot_mcu_sender_wait;struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;} RTMP_ADAPTER,*PRTMP_ADAPTER;
struct cmd_msg {unsigned cmd_type,ext_cmd_type,wr_iot_checked;};
static int held,sent,refused,nest,result;
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(!held);held=1;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
#define wake_up_all(q) ((void)(q),assert(held))
static struct cmd_msg *message(unsigned command){struct cmd_msg *m=calloc(1,sizeof(*m));assert(m);m->cmd_type=command;return m;}
static void AndesForceFreeCmdMsg(struct cmd_msg *msg){assert(!held);refused++;free(msg);}
INT32 AndesSendCmdMsg(PRTMP_ADAPTER ad,struct cmd_msg *msg);
static INT32 wr_iot_mcu_send_body(PRTMP_ADAPTER ad,struct cmd_msg *msg){
 assert(!held&&ad->wr_iot_mcu_sender_owner.inflight==1);
 assert(msg->wr_iot_checked&&ad->wr_iot_mcu_sender_owner.radio_active);
 sent++;
 if(nest){nest=0;assert(AndesSendCmdMsg(ad,message(0xef))==-1);}
 free(msg);return result;
}
'''
wrapper_tail=r'''
int main(void){
 RTMP_ADAPTER ad={0};wr_iot_mcu_sender_init(&ad.wr_iot_mcu_sender_owner);
 nest=1;
 for(unsigned i=0;i<3;i++)assert(AndesSendCmdMsg(&ad,message((unsigned[]){1,2,0xef}[i]))==0);
 assert(sent==3&&refused==1&&!ad.wr_iot_mcu_sender_owner.radio_active);
 result=-7;assert(AndesSendCmdMsg(&ad,message(0xef))==-7);
 assert(ad.wr_iot_mcu_sender_owner.closed&&ad.wr_iot_mcu_sender_owner.uncertain);
 assert(AndesSendCmdMsg(&ad,message(1))==-1&&sent==4&&refused==2&&!held);
 puts("PASS actual boot wrapper serialization, checked selection, uncertainty retention and consumed-message lifetime");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-boot-result-check-') as temporary:
    root=Path(temporary);c=root/'dispatch.c'
    subprocess.run(['python3',str(here/'prepare-mcu-result-check.py'),str(a.candidate),str(c)],check=True)
    source=c.read_text();anchor=' puts("PASS extracted checked ACK branch:'
    pos=source.index(anchor);c.write_text(source[:pos]+tests+source[pos:])
    (root/'wrapper.c').write_text(wrapper_prefix+(a.candidate/'include/wr-iot-mcu-sender-wrapper.inc').read_text()+wrapper_tail)
    for name in ('dispatch','wrapper'):
        subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror',
                        '-fsanitize=address,undefined','-fno-pie','-no-pie',
                        '-I'+str(a.candidate/'include'),'-I'+str(here),
                        str(root/(name+'.c')),'-o',str(root/name)],check=True)
        subprocess.run([str(root/name)],check=True)
