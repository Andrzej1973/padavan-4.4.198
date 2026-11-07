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
#define CMD_SET 1
#define CMD_QUERY 0
#define MCU_INIT 0
#define OS_TEST_BIT(bit,p) ((void)(bit),*(p)&1)
#define le2cpu32(value) (value)
#define NdisMoveMemory memcpy
struct cmd_msg {unsigned seq,wr_iot_checked,wr_iot_response_done,need_wait,cmd_type,ext_cmd_type,set_query,wr_iot_config_ext_result,wr_iot_config_mac_query,wr_iot_config_mac_address,wr_iot_config_mac_value,wr_iot_config_rf_query,wr_iot_config_rf_stream,wr_iot_config_rf_address,wr_iot_config_rf_value;int wr_iot_firmware_result,ack_done;};
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
if (a.candidate/'include/mcu-config-result.h').exists():
 fixture='#include "mcu-config-result.h"\n'+fixture
 pos=fixture.index(' puts("PASS actual allocation-free checked RX:')
 fixture=fixture[:pos]+r'''
 ad.MCUCtrl.flags=1;
 for(unsigned status=0;status<5;status++){
 struct cmd_msg msg={.seq=7,.wr_iot_checked=1,.need_wait=1,.cmd_type=0xed,.ext_cmd_type=0x0e,.set_query=CMD_SET,.wr_iot_firmware_result=1};
 memset(&ev,0,sizeof(ev));memset(packet,0,sizeof(packet));
 ev.fw_rxd_0.field.length=sizeof(ev)+32;ev.fw_rxd_1.field.seq_num=7;
 ev.fw_rxd_1.field.eid=0xed;ev.fw_rxd_2.field.ext_eid=0x0e;
 memcpy(packet,&ev,sizeof(ev));if(status)packet[sizeof(ev)+19+status]=1;
 ad.MCUCtrl.ackq.msg=&msg;
 assert(wr_iot_mcu_checked_rx_packet(&ad,packet,sizeof(ev)+32));
 assert(msg.ack_done==1&&msg.wr_iot_firmware_result==(status?1:0));
 assert(wr_iot_mcu_checked_rx_packet(&ad,packet,sizeof(ev)+32)&&msg.ack_done==1);
 msg.wr_iot_response_done=msg.ack_done=0;msg.set_query=0;
 assert(wr_iot_mcu_checked_rx_packet(&ad,packet,sizeof(ev)+32));
 assert(msg.ack_done==1&&msg.wr_iot_firmware_result==1);
 }
 puts("PASS actual direct MAC-write ACK: firmware status propagated, query refusal and duplicate completion gate; SDK event layout, no allocation/callback");
'''+fixture[pos:]
if (a.candidate/'include/wr-iot-mcu-config-rf-read.inc').exists():
 pos=fixture.index(' puts("PASS actual allocation-free checked RX:')
 fixture=fixture[:pos]+r'''
 ad.MCUCtrl.flags=1;
 for(unsigned bad=0;bad<13;bad++){
 struct cmd_msg msg={.seq=7,.wr_iot_checked=1,.need_wait=1,.cmd_type=0xed,.ext_cmd_type=2,.set_query=CMD_QUERY,
 .wr_iot_config_rf_query=1,.wr_iot_config_rf_stream=1,.wr_iot_config_rf_address=2,.wr_iot_config_rf_value=0x89abcdefU,.wr_iot_firmware_result=1};
 memset(&ev,0,sizeof(ev));memset(packet,0,sizeof(packet));ev.fw_rxd_0.field.length=sizeof(ev)+12;
 ev.fw_rxd_1.field.seq_num=7;ev.fw_rxd_1.field.eid=0xed;ev.fw_rxd_2.field.ext_eid=2;
 memcpy(packet,&ev,sizeof(ev));packet[sizeof(ev)]=1;packet[sizeof(ev)+4]=2;
 packet[sizeof(ev)+8]=0xef;packet[sizeof(ev)+9]=0xcd;packet[sizeof(ev)+10]=0xab;packet[sizeof(ev)+11]=0x89;
 if(bad)packet[sizeof(ev)+bad-1]^=1;
 ad.MCUCtrl.ackq.msg=&msg;
 assert(wr_iot_mcu_checked_rx_packet(&ad,packet,sizeof(ev)+12));
 assert(msg.ack_done==1&&msg.wr_iot_firmware_result==(bad?1:0));
 assert(wr_iot_mcu_checked_rx_packet(&ad,packet,sizeof(ev)+12)&&msg.ack_done==1);
 }
 puts("PASS actual checked RF read RX: exact stream/address/full value, all12 mismatches and duplicate completion; SDK event layout, no generic callback");
'''+fixture[pos:]
if (a.candidate/'include/wr-iot-mcu-config-mac-read.inc').exists():
 pos=fixture.index(' puts("PASS actual allocation-free checked RX:')
 fixture=fixture[:pos]+r'''
 ad.MCUCtrl.flags=1;
 for(unsigned bad=0;bad<14;bad++){
 struct cmd_msg msg={.seq=7,.wr_iot_checked=1,.need_wait=1,.cmd_type=0xed,.ext_cmd_type=0x0e,.set_query=CMD_QUERY,
 .wr_iot_config_mac_query=1,.wr_iot_config_mac_address=2,.wr_iot_config_mac_value=0x89abcdefU,.wr_iot_firmware_result=1};
 memset(&ev,0,sizeof(ev));memset(packet,0,sizeof(packet));ev.fw_rxd_0.field.length=sizeof(ev)+32;
 ev.fw_rxd_1.field.seq_num=7;ev.fw_rxd_1.field.eid=0xed;ev.fw_rxd_2.field.ext_eid=0x0e;
 memcpy(packet,&ev,sizeof(ev));packet[sizeof(ev)+24]=2;
 packet[sizeof(ev)+28]=0xef;packet[sizeof(ev)+29]=0xcd;packet[sizeof(ev)+30]=0xab;packet[sizeof(ev)+31]=0x89;
 if(bad&&bad<13)packet[sizeof(ev)+19+bad]^=1;
 if(bad==13)msg.set_query=CMD_SET;
 ad.MCUCtrl.ackq.msg=&msg;
 assert(wr_iot_mcu_checked_rx_packet(&ad,packet,sizeof(ev)+32));
 assert(msg.ack_done==1&&msg.wr_iot_firmware_result==(bad?1:0));
 assert(wr_iot_mcu_checked_rx_packet(&ad,packet,sizeof(ev)+32)&&msg.ack_done==1);
 }
 puts("PASS actual MAC read RX: every type/address/value byte, wrong direction and duplicate completion");
'''+fixture[pos:]
if 'wr_iot_config_ext_result&&' in (a.candidate/'include/wr-iot-mcu-rx-direct.inc').read_text():
 pos=fixture.index(' puts("PASS actual allocation-free checked RX:')
 fixture=fixture[:pos]+r'''
 ad.MCUCtrl.flags=1;
 for(unsigned ext=8;ext<=33;ext=ext==8?17:ext==17?33:34)for(unsigned bad=0;bad<8;bad++){
 struct cmd_msg msg={.seq=7,.wr_iot_checked=1,.need_wait=1,.cmd_type=0xed,.ext_cmd_type=ext,.set_query=CMD_SET,
 .wr_iot_config_ext_result=1,.wr_iot_firmware_result=1};
 memset(&ev,0,sizeof(ev));memset(packet,0,sizeof(packet));ev.fw_rxd_0.field.length=sizeof(ev)+8;
 ev.fw_rxd_1.field.seq_num=7;ev.fw_rxd_1.field.eid=0xed;
 if(bad==6)ev.fw_rxd_2.field.ext_eid=ext;
 memcpy(packet,&ev,sizeof(ev));packet[sizeof(ev)]=(unsigned char)ext;
 if(bad>=1&&bad<=4)packet[sizeof(ev)+3+bad]=1;
 if(bad==5)packet[sizeof(ev)]^=1;
 if(bad==7)msg.set_query=CMD_QUERY;
 ad.MCUCtrl.ackq.msg=&msg;assert(wr_iot_mcu_checked_rx_packet(&ad,packet,sizeof(ev)+8));
 assert(msg.ack_done==1&&msg.wr_iot_firmware_result==(bad?1:0));
 assert(wr_iot_mcu_checked_rx_packet(&ad,packet,sizeof(ev)+8)&&msg.ack_done==1);
 }
 puts("PASS actual extended RX: channel/TX-power/EFUSE status bytes, command echo, event, SET direction and duplicate completion");
 /* New host messages, same captured old event; production retirement is
  * intentionally bypassed. In-message response_done is not an epoch. */
 for(unsigned ext=8;ext<=33;ext=ext==8?17:ext==17?33:34){
  memset(&ev,0,sizeof(ev));memset(packet,0,sizeof(packet));
  ev.fw_rxd_0.field.length=sizeof(ev)+8;ev.fw_rxd_1.field.seq_num=7;
  ev.fw_rxd_1.field.eid=0xed;memcpy(packet,&ev,sizeof(ev));
  packet[sizeof(ev)]=(unsigned char)ext;
  for(unsigned request_generation=1;request_generation<=2;request_generation++){
   struct cmd_msg fresh={.seq=7,.wr_iot_checked=1,.need_wait=1,.cmd_type=0xed,
    .ext_cmd_type=ext,.set_query=CMD_SET,.wr_iot_config_ext_result=1,
    .wr_iot_firmware_result=1};
   ad.MCUCtrl.ackq.msg=&fresh;
   assert(wr_iot_mcu_checked_rx_packet(&ad,packet,sizeof(ev)+8));
   assert(fresh.wr_iot_response_done&&fresh.ack_done==1&&!fresh.wr_iot_firmware_result);
  }
 }
 ad.MCUCtrl.ackq.msg=NULL;
 puts("NEGATIVE CONTROL direct extended ACK: retirement bypassed, identical old result completes fresh same-command/same-ID request; parser is not a generation fence");
'''+fixture[pos:]
with tempfile.TemporaryDirectory(prefix='wr-mcu-rx-direct-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),'-I'+str(here),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
