#!/usr/bin/env python3
"""Execute actual API-generated MBSS wrapper; hardware/key hooks are injected."""
import argparse, subprocess, tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('driver',type=Path);a=p.parse_args()
fragment=(a.driver/'include/wr-iot-mbss-open-admission.inc').read_text()
assert fragment.count('wr_iot_driver_owner_take(')==1
assert fragment.index('wr_iot_precreated_key_matches(')<fragment.index('ret=wr_iot_mbss_open_raw(')
code=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-owner.h"
#define WR_IOT_PRECREATED_KEY_MATCH_H
#define WDEV_NUM_MAX 2
typedef int INT;typedef unsigned long ULONG;
struct device;
typedef struct adapter {
 struct device *net_dev;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[3];
 struct wr_iot_driver_owner wr_iot_driver_owner;
 int wr_iot_transition_lock,wr_iot_ticket_wait;unsigned int count;
 struct {unsigned BssidNum;struct {struct {struct device *if_dev;} wdev;} MBSSID[3];} ApCfg;
} *PRTMP_ADAPTER;
typedef struct device {PRTMP_ADAPTER ad;} *PNET_DEV;
static int current_identity,fault;static unsigned raw_calls,key_calls,main_calls;
#define current (&current_identity)
#define IS_MT7603(ad) 1
#define RTMP_OS_NETDEV_GET_PRIV(dev) ((dev)->ad)
#define VIRTUAL_IF_NUM(ad) ((ad)->count)
#define wake_up_all(queue) (++*(queue))
#define RTMP_IRQ_LOCK(lock,flags) do{(flags)=0;assert(!*(lock));*(lock)=1;}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do{(void)(flags);assert(*(lock));*(lock)=0;}while(0)
static int key_matches(PRTMP_ADAPTER ad,PNET_DEV dev,const unsigned char *ssid,
 unsigned int ssid_length,const char *password,unsigned int password_length){
 assert(!ad->wr_iot_transition_lock&&ad->wr_iot_transition.busy==WR_RADIO_BSS_OPEN);
 assert(dev==ad->ApCfg.MBSSID[2].wdev.if_dev&&ssid_length==3&&!memcmp(ssid,"IoT",3));
 assert(password_length==8&&!memcmp(password,"password",8));key_calls++;
 if(fault==2)wr_iot_radio_request_reset(&ad->wr_iot_transition);
 return fault!=1;
}
#define wr_iot_precreated_key_matches key_matches
static int observe_main(PRTMP_ADAPTER ad){assert(!ad->wr_iot_transition_lock);main_calls++;return fault!=3;}
#define WR_IOT_MBSS_OBSERVE_MAIN observe_main
static int observe_bss(PRTMP_ADAPTER ad,PNET_DEV dev,unsigned int index){assert(!ad->wr_iot_transition_lock&&dev->ad==ad&&(index==1||index==2));return fault!=5;}
#define WR_IOT_MBSS_OBSERVE_BSS observe_bss
static int wr_iot_mbss_open_raw(PNET_DEV dev,const struct wr_iot_radio_ticket *ticket,unsigned long generation){
 PRTMP_ADAPTER ad=dev->ad;raw_calls++;
 assert(!ad->wr_iot_transition_lock&&generation&&ad->wr_iot_transition.serial==ticket->serial);
 assert(ticket->operation==WR_RADIO_BSS_OPEN);
 if(fault==4)return -1;
 ad->count++;return 0;
}
'''+fragment+r'''
int main(void){
 for(fault=0;fault<8;fault++){
  struct adapter ad={0};struct device main_dev={&ad},guest={&ad},iot={&ad};
  struct wr_iot_interface_ref *ref;struct wr_iot_driver_open_request q={0};unsigned long sequence=0;
  ad.net_dev=&main_dev;ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[1].wdev.if_dev=&guest;ad.ApCfg.MBSSID[2].wdev.if_dev=&iot;ad.count=1;
  wr_iot_radio_transition_init(&ad.wr_iot_transition);ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
  ref=wr_iot_registry_add_family(ad.wr_iot_interface_refs,3,&sequence,&main_dev,WR_REF_FAMILY_MAIN);ref->published=1;ref->phase=WR_REF_OWNED;
  ref=wr_iot_registry_add_family(ad.wr_iot_interface_refs,3,&sequence,&guest,WR_REF_FAMILY_MBSS);ref->published=1;
  ref=wr_iot_registry_add_family(ad.wr_iot_interface_refs,3,&sequence,&iot,WR_REF_FAMILY_MBSS);ref->published=1;
  q.request_id[0]=1;q.adapter_epoch=ad.wr_iot_transition.epoch;q.device_generation=ref->generation;q.ssid_length=3;q.password_length=8;memcpy(q.ssid,"IoT",3);memcpy(q.password,"password",8);
  raw_calls=key_calls=main_calls=0;
  if(fault==6){assert(MBSS_VirtualIF_Open(&iot)==-1&&!raw_calls&&!key_calls);continue;}
  if(fault==7){assert(!MBSS_VirtualIF_Open(&guest)&&raw_calls==1&&!key_calls&&!main_calls&&ad.count==2);continue;}
  assert(wr_iot_driver_owner_query(&ad.wr_iot_driver_owner,q.request_id,q.adapter_epoch,q.device_generation));
  assert(wr_iot_driver_owner_reserve(&ad.wr_iot_driver_owner,&ad.wr_iot_transition,ad.wr_iot_interface_refs,3,&main_dev,&iot,1,current,&q,0,0));
  unsigned long serial=ad.wr_iot_transition.serial;
  int result=MBSS_VirtualIF_Open(&iot);
  assert(ad.wr_iot_transition.serial==serial&&key_calls==1);
  if(fault>=1&&fault<=3)assert(result==-1&&!raw_calls&&ad.count==1);
  else if(fault==4)assert(result==-1&&raw_calls==1&&ad.count==1);
  else assert(result==0&&raw_calls==1&&ad.count==2);
  if(fault==0)assert(ad.wr_iot_transition.phase==WR_RADIO_READY);
  if(fault==5)assert(ad.wr_iot_transition.phase==WR_RADIO_UNVERIFIED);
  int clean=wr_iot_driver_owner_leave(&ad.wr_iot_driver_owner,current,&iot,
   &ad.wr_iot_transition,ad.wr_iot_interface_refs,3);
  assert(clean==(fault==0||fault==1||fault==3));
  if(fault==0)assert(ad.wr_iot_driver_owner.receipt.valid&&
   ad.wr_iot_driver_owner.receipt.open_token==serial&&
   ad.wr_iot_driver_owner.receipt.request_id[0]==q.request_id[0]);
  if(fault==5)assert(ad.wr_iot_driver_owner.poisoned);
  assert(!ad.wr_iot_driver_owner.request.password[0]);
  assert(!ad.wr_iot_transition_lock);
 }
 puts("PASS actual generated MBSS: borrowed single ticket, key/main/reset refusals before raw mutation, no-owner rejection, Guest path and post-open unverified state; hardware/key hooks injected, not RF proof");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-iot-api-mbss-') as d:
 source=Path(d)/'check.c';source.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.driver/'include'),'-Itools/iot',str(source),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
