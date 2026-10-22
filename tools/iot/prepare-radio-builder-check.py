#!/usr/bin/env python3
"""Extract staged OFF builder; allocation/init/append injected, no command sent."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():raise SystemExit('Refusing overwrite')
s=(a.candidate/'mcu/andes_mt.c').read_text()
anchor='static inline struct cmd_msg *wr_iot_prepare_radio_off(RTMP_ADAPTER *pAd)'
if s.count(anchor)!=1:raise SystemExit('Changed builder signature')
start=s.index(anchor);end=s.index('\n}',start)+2
prefix=r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef struct {int unused;} RTMP_ADAPTER;
struct cmd_msg {int wr_iot_checked;};
struct _EXT_CMD_RADIO_ON_OFF_CTRL_T {unsigned char ucWiFiRadioCtrl,aucReserve[3];};
#define TRUE 1
#define FALSE 0
#define P1_Q0 1
#define EXT_CID 0xed
#define CMD_SET 1
#define EXT_CMD_RADIO_ON_OFF_CTRL 5
#define WIFI_RADIO_OFF 2
static struct cmd_msg message;
static int fail,allocated,initialized,appended;
static struct cmd_msg *AndesAllocCmdMsg(RTMP_ADAPTER *ad,unsigned int size){
 assert(ad&&size==4);allocated++;if(fail)return NULL;
 memset(&message,0,sizeof(message));return &message;
}
static void AndesInitCmdMsg(struct cmd_msg *msg,int pq,int cmd,int set,int ext,
 int wait,int timeout,int retry,int rsp,int len,void *payload,void *handler){
 assert(msg==&message&&pq==P1_Q0&&cmd==EXT_CID&&set==CMD_SET&&ext==5);
 assert(wait&&!timeout&&!retry&&rsp&&len==8&&!payload&&!handler);
 initialized++;
}
static void AndesAppendCmdMsg(struct cmd_msg *msg,char *data,unsigned int size){
 const unsigned char expected[4]={2,0,0,0};
 assert(msg==&message&&msg->wr_iot_checked&&size==4&&!memcmp(data,expected,4));appended++;
}
'''
tail=r'''
int main(void){
 RTMP_ADAPTER ad;
 fail=1;assert(!wr_iot_prepare_radio_off(&ad)&&allocated==1&&!initialized&&!appended);
 fail=0;assert(wr_iot_prepare_radio_off(&ad)==&message);
 assert(allocated==2&&initialized==1&&appended==1&&message.wr_iot_checked);
 puts("PASS staged OFF builder: allocation failure, checked synchronous no-retry init, exact OFF/reserved bytes; no send or radio proof");
 return 0;
}
'''
a.output.write_text(prefix+s[start:end]+tail,encoding='utf-8')
