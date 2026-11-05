#!/usr/bin/env python3
"""Execute actual RX parser prefix/event dispatch with exact valid-byte buffers."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
s=(a.candidate/'common/cmm_data.c').read_text()
start=s.index('UINT32 parse_rx_packet_type(')
end=s.index('switch (rx_pkt_type)',start)
prefix=s[start:end]
start=s.index('        case RMAC_RX_PKT_TYPE_RX_EVENT:',end)
end=s.index('#ifdef MT_PS',start)
event=s[start:end]
sdk=(a.candidate/'include/mcu/andes_mt.h').read_text()
start=sdk.rfind('#ifdef RT_BIG_ENDIAN',0,sdk.index('typedef union _FW_RXD_0'))
end=sdk.index('} EVENT_RXD;',start)+len('} EVENT_RXD;')
event_types=sdk[start:end]
fixture=r'''
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
typedef uint32_t UINT32;typedef void VOID;
#define RTMP_PCI_SUPPORT 1
#define RX_BUFFER_AGGRESIZE 2048
#define RMAC_RX_PKT_TYPE_RX_EVENT 7
#define RMAC_RX_PKT_TYPE(x) ((x)>>29)
#define RMAC_RX_PKT_RX_BYTE_COUNT(x) ((x)&0xffffu)
#define DBGPRINT(level,args) ((void)0)
union rmac_rxd_0 {UINT32 word;};
#define GNU_PACKED __attribute__((packed))
@@EVENT_TYPES@@
typedef struct {unsigned PDMALen,Flags;} RX_BLK;
typedef struct {struct {void (*rx_event_handler)(void *,void *);} chipOps;} RTMP_ADAPTER;
#define GET_OS_PKT_DATAPTR(pkt) (pkt)
#define fRX_CMD_RSP 1
#define RX_BLK_SET_FLAG(blk,flag) ((blk)->Flags|=(flag))
static unsigned calls;
static void receive(void *ad,void *ptr){
 (void)ad;volatile unsigned char *bytes=ptr;
 for(unsigned i=0;i<sizeof(EVENT_RXD);i++)(void)bytes[i];
 calls++;
}
'''+prefix+'switch(rx_pkt_type){\n'+event+r'''
default: break;
}
return rx_hw_hdr_len;
}
int main(void){
 RTMP_ADAPTER ad={.chipOps={receive}};
 unsigned lengths[]={0,1,2,3,4,5,8,11,12,13,2048,2049};
 for(unsigned i=0;i<sizeof(lengths)/sizeof(*lengths);i++){
  unsigned len=lengths[i];unsigned char *packet=calloc(len?len:1,1);assert(packet);
  if(len>=4){UINT32 word=(7u<<29)|len;memcpy(packet,&word,4);}
  RX_BLK blk={.PDMALen=len};calls=0;
  assert(parse_rx_packet_type(&ad,&blk,packet)==0);
  unsigned valid=len>=sizeof(EVENT_RXD)&&len<=RX_BUFFER_AGGRESIZE;
  assert(calls==valid&&blk.Flags==valid);
  free(packet);
 }
 unsigned char packet[12]={0};UINT32 word=(7u<<29)|13;memcpy(packet,&word,4);
 RX_BLK blk={.PDMALen=sizeof(packet)};calls=0;
 assert(parse_rx_packet_type(&ad,&blk,packet)==0&&!calls&&!blk.Flags);
 assert(parse_rx_packet_type(&ad,NULL,packet)==0&&!calls);
 blk.PDMALen=12;assert(parse_rx_packet_type(&ad,&blk,NULL)==0&&!calls);
 puts("PASS actual PCI RX prefix/event case rejects short/oversized/mismatched buffers before dispatch; valid event sizes preserved; DMA operations untested");
}
'''
fixture=fixture.replace('@@EVENT_TYPES@@',event_types)
if (a.candidate/'include/wr-iot-mcu-rx-direct.inc').exists():
    fixture=fixture.replace('static unsigned calls;',
        'static unsigned calls,direct_calls,direct_handled;\n'
        'static int wr_iot_mcu_checked_rx_packet(RTMP_ADAPTER *ad,void *data,unsigned length){\n'
        ' assert(ad&&data&&length>=sizeof(EVENT_RXD));direct_calls++;return direct_handled;\n}\n')
    fixture='#define MT_MAC 1\n'+fixture
    fixture=fixture.replace('RX_BLK blk={.PDMALen=len};calls=0;',
                            'RX_BLK blk={.PDMALen=len};calls=direct_calls=0;')
    fixture=fixture.replace('assert(calls==valid&&blk.Flags==valid);',
        'assert(calls==valid&&direct_calls==valid&&blk.Flags==valid);\n'
        '  if(valid){calls=direct_calls=0;direct_handled=1;blk.Flags=0;\n'
        '   assert(parse_rx_packet_type(&ad,&blk,packet)==0);\n'
        '   assert(!calls&&direct_calls==1&&blk.Flags==1);direct_handled=0;}')
if (a.candidate/'include/wr-iot-mcu-nettask-bootstrap.inc').exists():
 fixture='#define CONFIG_ANDES_SUPPORT 1\n'+fixture
 fixture=fixture.replace('typedef struct {struct {void (*rx_event_handler)(void *,void *);} chipOps;} RTMP_ADAPTER;',
                         'typedef struct {struct {void (*rx_event_handler)(void *,void *);} chipOps;unsigned wr_iot_boot_mcu_only;} RTMP_ADAPTER;')
 fixture=fixture.replace('static unsigned calls,direct_calls,direct_handled;',
                         'static unsigned calls,direct_calls,direct_handled,normal_calls;')
 fixture=fixture.replace('default: break;', 'case 2: normal_calls++;break;\ndefault: break;')
 anchor=' puts("PASS actual PCI RX prefix/event case'
 pos=fixture.index(anchor)
 fixture=fixture[:pos]+r'''
 word=(2u<<29)|12;memcpy(packet,&word,4);ad.wr_iot_boot_mcu_only=1;
 blk.PDMALen=12;blk.Flags=0;calls=direct_calls=normal_calls=0;
 assert(parse_rx_packet_type(&ad,&blk,packet)==0&&!normal_calls&&!direct_calls&&!calls);
 ad.wr_iot_boot_mcu_only=0;
 assert(parse_rx_packet_type(&ad,&blk,packet)==0&&normal_calls==1);
 word=(7u<<29)|12;memcpy(packet,&word,4);ad.wr_iot_boot_mcu_only=1;
 calls=direct_calls=0;direct_handled=0;blk.Flags=0;
 assert(parse_rx_packet_type(&ad,&blk,packet)==0&&!calls&&direct_calls==1&&blk.Flags==1);
 direct_handled=1;blk.Flags=0;
 assert(parse_rx_packet_type(&ad,&blk,packet)==0&&!calls&&direct_calls==2&&blk.Flags==1);
'''+fixture[pos:]
if 'ad->wr_iot_boot_active && rx_pkt_type' in s:
 fixture=fixture.replace('unsigned wr_iot_boot_mcu_only;', 'unsigned wr_iot_boot_mcu_only,wr_iot_boot_active;')
 fixture=fixture.replace('ad.wr_iot_boot_mcu_only','ad.wr_iot_boot_active')
with tempfile.TemporaryDirectory(prefix='wr-mcu-rx-bounds-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
