#!/usr/bin/env python3
"""Extract candidate checked ACK branch; locks/events are injected in fixture."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('candidate', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
if a.output.exists():
    raise SystemExit('Refusing to overwrite output')
source = (a.candidate / 'mcu/andes_mt.c').read_text(encoding='utf-8')
branch_path = a.candidate / 'checked-ack-branch.inc'
if branch_path.exists() and not (a.candidate/'include/mcu-boot-result.h').exists():
    branch = branch_path.read_text(encoding='utf-8')
else:
    # Merged driver inventories omit standalone fixture fragments. Extract the
    # same bounded branch directly, retaining the existing placement checks.
    start = source.index('                if (msg->wr_iot_checked) {')
    end = source.index('\n\t\t\t#if defined(RTMP_USB_SUPPORT)', start)
    branch = source[start:end]
if source.count(branch) != 1:
    raise SystemExit('Candidate checked branch missing/duplicated')
pos = source.index(branch)
if source.rfind('if (msg->seq == event_rxd->fw_rxd_1.field.seq_num)', 0, pos) < 0:
    raise SystemExit('Sequence gate missing')
if not source[pos + len(branch):].startswith('\n\t\t\t#if defined(RTMP_USB_SUPPORT)'):
    raise SystemExit('Checked branch no longer precedes original lock release')
prefix = r'''#include "radio-result.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define EXT_CID 0xed
#define EXT_CMD_RADIO_ON_OFF_CTRL 5
#define EXT_EVENT 0xed
#define EXT_EVENT_CMD_RESULT 0
#define TRUE 1
struct event {
 struct {struct {unsigned int length;} field;} fw_rxd_0;
 struct {struct {unsigned int eid,seq_num;} field;} fw_rxd_1;
 struct {struct {unsigned int ext_eid;} field;} fw_rxd_2;
};
struct message {int wr_iot_checked,wr_iot_firmware_result,need_wait,cmd_type,ext_cmd_type,ack_done;unsigned int seq;int wr_iot_response_done;};
struct packet {unsigned char bytes[128];size_t size;};
static int lock_held,generic_calls;
#define GET_OS_PKT_LEN(pkt) ((pkt)->size)
#define GET_OS_PKT_DATAPTR(pkt) ((pkt)->bytes)
static void complete(int *done){assert(lock_held);(*done)++;}
#define RTMP_OS_COMPLETE complete
static void dispatch(struct message *msg,struct event *event_rxd,struct packet *net_pkt){
 lock_held=1;
 do {
  if(msg->seq!=event_rxd->fw_rxd_1.field.seq_num)break;
'''
tail = r'''
  lock_held=0;generic_calls++;
 } while(0);
 lock_held=0;
}
int main(void){
 struct message base={1,1,1,EXT_CID,5,0,7,0},msg;
 struct event ev={{ {sizeof(struct event)+8} },{{EXT_EVENT,7}},{{0}}},bad;
 struct packet pkt={{0},sizeof(struct event)+8},altered;
 unsigned int mode;
 pkt.bytes[sizeof(ev)]=5;
 msg=base;dispatch(&msg,&ev,&pkt);assert(!msg.wr_iot_firmware_result&&msg.ack_done==1&&!generic_calls);
 altered=pkt;altered.bytes[sizeof(ev)+4]=1;dispatch(&msg,&ev,&altered);
 assert(!msg.wr_iot_firmware_result&&msg.ack_done==1);
 msg=base;dispatch(&msg,&ev,&altered);dispatch(&msg,&ev,&pkt);
 assert(msg.wr_iot_firmware_result==1&&msg.ack_done==1);
 for(mode=0;mode<8;mode++){
  msg=base;bad=ev;altered=pkt;
  if(mode==0)altered.bytes[sizeof(ev)+4]=1;
  if(mode==1)altered.bytes[sizeof(ev)]=6;
  if(mode==2)altered.size--;
  if(mode==3)bad.fw_rxd_0.field.length--;
  if(mode==4)bad.fw_rxd_1.field.eid=1;
  if(mode==5)bad.fw_rxd_2.field.ext_eid=1;
  if(mode==6)msg.cmd_type=0;
  if(mode==7)msg.ext_cmd_type=6;
  dispatch(&msg,&bad,&altered);assert(msg.wr_iot_firmware_result==1&&msg.ack_done==1&&!generic_calls);
 }
 msg=base;msg.seq=8;dispatch(&msg,&ev,&pkt);assert(!msg.ack_done&&msg.wr_iot_firmware_result==1);
 msg=base;msg.need_wait=0;dispatch(&msg,&ev,&pkt);assert(!msg.ack_done&&msg.wr_iot_firmware_result==1);
 msg=base;msg.wr_iot_checked=0;dispatch(&msg,&ev,&pkt);assert(!msg.ack_done&&generic_calls==1);
 puts("PASS extracted checked ACK branch: completion under injected lock, exact envelope/payload, sequence gate, generic bypass; real concurrency not tested");
 return 0;
}
'''
if (a.candidate/'include/mcu-boot-result.h').exists():
 prefix='#include "mcu-boot-result.h"\n'+prefix
if (a.candidate/'include/mcu-config-result.h').exists():
 prefix='#include "mcu-config-result.h"\n#define CMD_SET 1\n'+prefix
 prefix=prefix.replace('int wr_iot_response_done;', 'int wr_iot_response_done,set_query;')
 tail=tail.replace('base={1,1,1,EXT_CID,5,0,7,0}', 'base={1,1,1,EXT_CID,5,0,7,0,0}')
 pos=tail.index(' puts("PASS extracted checked ACK branch:')
 tail=tail[:pos]+r'''
 base.ext_cmd_type=0x0e;base.set_query=CMD_SET;
 ev.fw_rxd_0.field.length=sizeof(ev)+32;ev.fw_rxd_2.field.ext_eid=0x0e;
 pkt.size=sizeof(ev)+32;memset(pkt.bytes,0,sizeof(pkt.bytes));generic_calls=0;
 msg=base;dispatch(&msg,&ev,&pkt);assert(!msg.wr_iot_firmware_result&&msg.ack_done==1&&!generic_calls);
 for(unsigned byte=20;byte<24;byte++){
  altered=pkt;altered.bytes[sizeof(ev)+byte]=1;msg=base;
  dispatch(&msg,&ev,&altered);assert(msg.wr_iot_firmware_result==1&&msg.ack_done==1&&!generic_calls);
 }
 msg=base;msg.set_query=0;dispatch(&msg,&ev,&pkt);assert(msg.wr_iot_firmware_result==1&&msg.ack_done==1);
 msg=base;msg.seq++;dispatch(&msg,&ev,&pkt);assert(msg.wr_iot_firmware_result==1&&!msg.ack_done);
 puts("PASS checked MAC-write result: payload failure propagates, read query refused and sequence gate retained; no generic callback");
'''+tail[pos:]
a.output.write_text(prefix + branch + tail, encoding='utf-8')
