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
branch = (a.candidate / 'checked-ack-branch.inc').read_text(encoding='utf-8')
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
a.output.write_text(prefix + branch + tail, encoding='utf-8')
