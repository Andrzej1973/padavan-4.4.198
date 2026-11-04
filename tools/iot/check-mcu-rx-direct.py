#!/usr/bin/env python3
"""Execute actual allocation-free checked RX entry with SDK event types."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
sdk=(a.candidate/'include/mcu/andes_mt.h').read_text()
start=sdk.rfind('#ifdef RT_BIG_ENDIAN',0,sdk.index('typedef union _FW_RXD_0'))
end=sdk.index('} EVENT_RXD;',start)+len('} EVENT_RXD;');types=sdk[start:end]
helper=(a.candidate/'include/wr-iot-mcu-rx-direct.inc').read_text()
fixture=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "radio-result.h"
#include "mcu-boot-result.h"
typedef uint32_t UINT32;typedef unsigned char UCHAR;typedef int BOOLEAN;
#define GNU_PACKED __attribute__((packed))
@@EVENT_TYPES@@
#define TRUE 1
#define FALSE 0
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define EXT_CID 0xed
#define EXT_CMD_RADIO_ON_OFF_CTRL 5
#define EXT_EVENT 0xed
#define EXT_EVENT_CMD_RESULT 0
#define MCU_INIT 0
#define OS_TEST_BIT(bit,p) ((void)(bit),*(p)&1)
#define le2cpu32(value) (value)
#define NdisMoveMemory memcpy
struct cmd_msg {unsigned seq,wr_iot_checked,wr_iot_response_done,need_wait,cmd_type,ext_cmd_type;int wr_iot_firmware_result,ack_done;};
struct queue {struct cmd_msg *msg;};
struct MCU_CTRL {unsigned flags;int ackq_lock;struct queue ackq;};
typedef struct {struct MCU_CTRL MCUCtrl;} RTMP_ADAPTER;
static int held;
#define RTMP_SPIN_LOCK_IRQSAVE(lock,flags) do{(void)(lock);*(flags)=0;assert(!held);held=1;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(lock,flags) do{(void)(lock);(void)(flags);assert(held);held=0;}while(0)
#define DlListForEachSafe(msg,tmp,queue,type,member) for((msg)=(queue)->msg,(tmp)=NULL;(void)(tmp),(msg);(msg)=NULL)
#define RTMP_OS_COMPLETE(done) (assert(held),++*(done))
'''.replace('@@EVENT_TYPES@@',types)+helper+r'''
int main(void){
 RTMP_ADAPTER ad={.MCUCtrl={.flags=1}};unsigned char packet[64];EVENT_RXD ev;
 for(unsigned c=0;c<4;c++)for(unsigned status=0;status<7;status++){
  struct cmd_msg msg={.seq=7,.wr_iot_checked=1,.need_wait=1,.wr_iot_firmware_result=1};
  memset(&ev,0,sizeof(ev));memset(packet,0,sizeof(packet));
  msg.cmd_type=(unsigned[]){1,2,0xef,0xed}[c];msg.ext_cmd_type=c==3?5:0;
  unsigned len=sizeof(ev)+(c==3?8:0);
  ev.fw_rxd_0.field.length=len;ev.fw_rxd_1.field.seq_num=7;
  ev.fw_rxd_1.field.eid=c==2?0xef:c==3?0xed:1;
  ev.fw_rxd_2.field.ext_eid=c==3?0:status;
  memcpy(packet,&ev,sizeof(ev));if(c==3){packet[sizeof(ev)]=5;packet[sizeof(ev)+4]=status;}
  ad.MCUCtrl.ackq.msg=&msg;
  assert(wr_iot_mcu_checked_rx_packet(&ad,packet,len));
  assert(msg.ack_done==1&&msg.wr_iot_firmware_result==(status?1:0)&&!held);
  /* Duplicate cannot overwrite even a failure result. */
  memset(packet+sizeof(ev),0,8);ev.fw_rxd_2.field.ext_eid=0;memcpy(packet,&ev,sizeof(ev));
  assert(wr_iot_mcu_checked_rx_packet(&ad,packet,len));
  assert(msg.ack_done==1&&msg.wr_iot_firmware_result==(status?1:0));
  msg.wr_iot_response_done=msg.ack_done=0;msg.seq=8;
  assert(!wr_iot_mcu_checked_rx_packet(&ad,packet,len)&&!msg.ack_done);
  msg.seq=7;msg.wr_iot_checked=0;
  assert(!wr_iot_mcu_checked_rx_packet(&ad,packet,len)&&!msg.ack_done);
 }
 ad.MCUCtrl.ackq.msg=NULL;
 assert(!wr_iot_mcu_checked_rx_packet(&ad,packet,sizeof(EVENT_RXD)+8));
 for(unsigned len=0;len<sizeof(EVENT_RXD);len++)assert(wr_iot_mcu_checked_rx_packet(&ad,packet,len));
 assert(wr_iot_mcu_checked_rx_packet(&ad,NULL,12));
 ad.MCUCtrl.flags=0;assert(wr_iot_mcu_checked_rx_packet(&ad,packet,20));
 puts("PASS actual allocation-free checked RX: SDK boot/radio statuses, correlation, duplicates, generic fallback, short input and inactive controller; lock operations injected");
}
'''
# No allocator/destructor declaration is present: compiling the actual helper
# also rejects accidental construction or freeing in this bounded path.
with tempfile.TemporaryDirectory(prefix='wr-mcu-rx-direct-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),'-I'+str(here),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
