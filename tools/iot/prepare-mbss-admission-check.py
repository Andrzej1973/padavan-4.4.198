#!/usr/bin/env python3
"""Extract the final raw MBSS wrapper and compile admission with injected IO."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('bundle',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():raise SystemExit('Refusing overwrite')
s=(a.bundle/'ap/ap_mbss_inf.c').read_text();sig='static INT wr_iot_mbss_open_raw(PNET_DEV pDev)'
if s.count(sig)!=1:raise SystemExit('Changed final raw MBSS wrapper')
start=s.index(sig);raw=s[start:s.index('\n}',start)+2]
fragment=(a.bundle/'include/wr-iot-mbss-open-admission.inc').read_text()
prefix=r'''#include "radio-transition.h"
#include "interface-registry.h"
#define WDEV_NUM_MAX 1
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef int INT;typedef void VOID;typedef unsigned long ULONG;
struct device;
typedef struct adapter {int wr_iot_transition_lock;struct wr_iot_radio_transition wr_iot_transition;struct device *net_dev;struct wr_iot_interface_ref wr_iot_interface_refs[2];
 struct {int BssidNum;struct {struct {struct device *if_dev;} wdev;} MBSSID[3];} ApCfg;} *PRTMP_ADAPTER;
typedef struct device {PRTMP_ADAPTER ad;} *PNET_DEV;
static int held,refs,commands,open_error,up_error,abort_calls,queue_starts,mode,observes;
#define IS_MT7603(ad) 1
static int observe_main(PRTMP_ADAPTER ad){
 assert(!held&&ad->wr_iot_transition.busy==WR_RADIO_BSS_OPEN);observes++;
 if(mode==5)wr_iot_radio_request_reset(&ad->wr_iot_transition);
 if(mode==6)wr_iot_radio_main_down(&ad->wr_iot_transition);
 if(mode==7)wr_iot_radio_request_close(&ad->wr_iot_transition);
 return mode!=4;
}
#define WR_IOT_MBSS_OBSERVE_MAIN(ad) observe_main(ad)
#define RTMP_IRQ_LOCK(lock,flags) ((flags)=0,(void)(lock),assert(!held),held=1)
#define RTMP_IRQ_UNLOCK(lock,flags) ((void)(flags),(void)(lock),assert(held),held=0)
#define RT_MOD_INC_USE_COUNT() (++refs)
#define RT_MOD_DEC_USE_COUNT() (--refs)
#define RTMP_OS_NETDEV_GET_PRIV(dev) ((dev)->ad)
#define DBGPRINT(level,args) ((void)0)
#define NDIS_STATUS_SUCCESS 0
#define CMD_RTPRIV_IOCTL_MBSS_OPEN 1
#define CMD_RTPRIV_IOCTL_MBSS_ABORT_OPEN 2
#define CMD_RTPRIV_IOCTL_MBSS_CR_ENABLE 3
static int RTMP_AP_IoctlHandle(VOID *p,VOID *unused,int command,int z,PNET_DEV dev,int n){
 PRTMP_ADAPTER ad=p;assert(!held&&ad==dev->ad&&!unused&&!z&&!n);
 assert(ad->wr_iot_transition.busy==WR_RADIO_BSS_OPEN);commands++;
 if(command==1)return open_error;
 if(command==2)abort_calls++;
 return 0;
}
#define VIRTUAL_IF_UP(ad) ((void)(ad),assert(!held),up_error)
#define RTMP_OS_NETDEV_START_QUEUE(dev) ((void)(dev),assert(!held),queue_starts++)
#define RT_MOD_HNAT_REG(dev) ((void)(dev),assert(!held))
'''
suffix=r'''
int main(void){
 struct adapter ad;struct device main_dev={&ad},dev={&ad};struct wr_iot_radio_ticket t;struct wr_iot_interface_ref *record;unsigned long generation;
 for(mode=0;mode<9;mode++){
  memset(&ad,0,sizeof(ad));ad.net_dev=&main_dev;ad.ApCfg.BssidNum=3;
  ad.ApCfg.MBSSID[2].wdev.if_dev=mode==8?&main_dev:&dev;
  refs=commands=abort_calls=queue_starts=held=observes=0;
  wr_iot_radio_transition_init(&ad.wr_iot_transition);
  generation=0;record=wr_iot_registry_add(ad.wr_iot_interface_refs,2,&generation,&dev);assert(record);record->published=1;
  assert(wr_iot_radio_begin(&ad.wr_iot_transition,ad.wr_iot_transition.epoch,WR_RADIO_START,&t));
  if(mode==0)wr_iot_radio_finish_unverified(&ad.wr_iot_transition,&t);
  else wr_iot_radio_finish(&ad.wr_iot_transition,&t,1);
  open_error=mode==1;up_error=mode==2;
  int ret=MBSS_VirtualIF_Open(&dev);
  assert(!held&&!ad.wr_iot_transition.busy);
  if(mode==0)assert(ret==-1&&!commands&&!refs&&record->phase==WR_REF_IDLE);
  if(mode==1)assert(ret==-1&&commands==1&&!refs&&!queue_starts&&record->phase==WR_REF_IDLE);
  if(mode==2)assert(ret==-1&&abort_calls==1&&!refs&&!queue_starts&&record->phase==WR_REF_IDLE);
  if(mode==3){assert(ret==0&&refs==1&&queue_starts==1&&record->phase==WR_REF_OWNED);RT_MOD_DEC_USE_COUNT();}
  if(mode>=4&&mode<=7)assert(ret==-1&&!commands&&!refs&&!queue_starts&&record->phase==WR_REF_IDLE);
  if(mode==4)assert(ad.wr_iot_transition.main_ready&&ad.wr_iot_transition.phase==WR_RADIO_READY);
  if(mode==5)assert(!ad.wr_iot_transition.main_ready&&ad.wr_iot_transition.reset_pending);
  if(mode==6)assert(!ad.wr_iot_transition.main_ready&&ad.wr_iot_transition.main_inhibited);
  if(mode==7)assert(!ad.wr_iot_transition.main_ready&&ad.wr_iot_transition.phase==WR_RADIO_CLOSING);
  if(mode==8){assert(ret==0&&refs==1&&queue_starts==1&&record->phase==WR_REF_OWNED);RT_MOD_DEC_USE_COUNT();}
  assert(observes==(mode==0||mode==8?0:1));
 }
 assert(MBSS_VirtualIF_Open(NULL)==-1);
 assert(MBSS_VirtualIF_Open(&main_dev)==-1);
 puts("PASS final MBSS admission: observed IoT main radio, stale reset/main-down/close refusal, guest bypass and raw failure balance; driver IO injected");return 0;
}
'''
a.output.write_text(prefix+raw+'\n'+fragment+suffix,encoding='utf-8')
