#!/usr/bin/env python3
"""Compose actual auxiliary OPEN/UP and CLOSE/DOWN into one host ownership cycle."""
import argparse,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();here=Path(__file__).resolve().parent
base=a.output.with_name(a.output.name+'.close-base.c')
if a.output.exists() or base.exists():p.error('new outputs required')
subprocess.run([sys.executable,str(here/'prepare-aux-family-owned-check.py'),str(a.candidate),str(base)],check=True)
s=base.read_text();s=s[:s.index('int main(void){')]
s=s.replace('#include "aux-close-claim.h"','#include "aux-close-claim.h"\n#include "virtual-open-claim.h"',1)
source=(a.candidate/'common/cmm_cfg.c').read_text();start=source.index('case CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP:')
case=source[start:source.index('case CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN:',start)]
assert 'WR_IOT_CLAIM_ONLY_UP' in case
extra=r'''
typedef RTMP_ADAPTER *PRTMP_ADAPTER;
typedef unsigned int UINT;
typedef struct {int (*rt28xx_open)(void *);int (*rt28xx_close)(void *);
 void *if_dev;unsigned long owner_generation,owner_serial,owner_epoch;int owner_operation;} RT_CMD_INF_UP_DOWN;
#define CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP 1
#define VIRTUAL_IF_INC(ad) ((ad)->count++)
static int physical_open(void *dev){(void)dev;assert(0);return 1;}
static int actual_up_case(RTMP_ADAPTER *pAd,RT_CMD_INF_UP_DOWN *request){void *pData=request;
 switch(CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP){
'''+case+r'''
 }return NDIS_STATUS_SUCCESS;}
static int cycle_up(RTMP_ADAPTER *ad,void *dev,const struct wr_iot_radio_ticket *t,unsigned long gen){
 RT_CMD_INF_UP_DOWN r={physical_open,0,dev,gen,t->serial,t->epoch,t->operation};
 return actual_up_case(ad,&r)?-1:0;
}
#define VIRTUAL_IF_UP_CLAIM(ad,dev,t,g) cycle_up(ad,dev,t,g)
#define RT_MOD_INC_USE_COUNT() (++pins)
#undef RT_MOD_DEC_USE_COUNT
#define RT_MOD_DEC_USE_COUNT() do{assert(!held&&pins>0);pins--;}while(0)
static int open_family_calls,registrations,open_family_result;
static int open_family(RTMP_ADAPTER *ad,void *dev){
 assert(ad==wrapper_ad&&dev&&!held&&pins==1);
 assert(ad->wr_iot_interface_refs[1].phase==WR_REF_RESERVED);
 open_family_calls++;return open_family_result;
}
#undef RTMP_AP_IoctlHandle
#undef RTMP_COM_IoctlHandle
#define RTMP_AP_IoctlHandle(ad,wrq,cmd,sub,dev,flags) open_family(ad,dev)
#define RTMP_COM_IoctlHandle(ad,wrq,cmd,sub,dev,flags) open_family(ad,dev)
#define RT_MOD_HNAT_REG(dev) do{assert(dev&&!held&&pins==1);assert(wrapper_ad->wr_iot_interface_refs[1].phase==WR_REF_OWNED);registrations++;}while(0)
#define RTMP_OS_NETDEV_CARRIER_OFF(dev) ((void)(dev))
'''
for rel,sig in [('ap/ap_apcli_inf.c','INT ApCli_VirtualIF_Open('),('os/linux/rt_profile.c','INT Monitor_VirtualIF_Open(')]:
 text=(a.candidate/rel).read_text();begin=text.index(sig);extra+=text[begin:text.index('\n}',begin)+2]+'\n'
post=r'''
static void cycle_ready(RTMP_ADAPTER *ad,enum wr_iot_ref_family f,int *dev){
 ready(ad,f,dev);ad->net_dev=&dev[0];ad->count=1;
 ad->wr_iot_transition.serial=ad->wr_iot_transition.retired_serial=1;
 ad->wr_iot_interface_refs[1].phase=WR_REF_IDLE;
 ad->wr_iot_interface_refs[1].last_token=0;ad->wr_iot_interface_refs[1].removing=0;
 pins=0;family_result=down_result=open_family_result=0;open_family_calls=registrations=0;
}
int main(void){RTMP_ADAPTER ad;int dev[2];
 for(int monitor=0;monitor<2;monitor++){
  enum wr_iot_ref_family f=monitor?WR_REF_FAMILY_MONITOR:WR_REF_FAMILY_APCLI;
  for(int removing=0;removing<2;removing++){
   cycle_ready(&ad,f,dev);
   assert((monitor?Monitor_VirtualIF_Open(&dev[1]):ApCli_VirtualIF_Open(&dev[1]))==0);
   assert(pins==1&&ad.count==2&&open_family_calls==1);
   assert(ad.wr_iot_interface_refs[1].phase==WR_REF_OWNED);
   if(removing)assert(wr_iot_registry_begin_remove(&ad.wr_iot_interface_refs[1],&dev[1],2));
   assert((monitor?Monitor_VirtualIF_Close(&dev[1]):ApCli_VirtualIF_Close(&dev[1]))==0);
   assert(!pins&&ad.count==1&&family_calls==1&&down_calls==1);
   assert(ad.wr_iot_interface_refs[1].phase==WR_REF_IDLE);
   assert(ad.wr_iot_family_close[1].phase==WR_FAMILY_CLOSE_DONE);
   assert((monitor?Monitor_VirtualIF_Close(&dev[1]):ApCli_VirtualIF_Close(&dev[1]))==-EBUSY);
   assert(family_calls==1&&ad.count==1&&!pins);
   if(!removing){
    unsigned long old=ad.wr_iot_interface_refs[1].last_token;
    assert((monitor?Monitor_VirtualIF_Open(&dev[1]):ApCli_VirtualIF_Open(&dev[1]))==0);
    assert(ad.wr_iot_interface_refs[1].last_token>old&&pins==1&&ad.count==2);
    assert((monitor?Monitor_VirtualIF_Close(&dev[1]):ApCli_VirtualIF_Close(&dev[1]))==0);
    assert(!pins&&ad.count==1&&family_calls==2&&down_calls==2);
   }
  }
  cycle_ready(&ad,f,dev);open_family_result=1;
  assert((monitor?Monitor_VirtualIF_Open(&dev[1]):ApCli_VirtualIF_Open(&dev[1]))==-1);
  assert(pins==1&&ad.count==2&&ad.wr_iot_interface_refs[1].phase==WR_REF_UNCERTAIN_OPEN);
  assert((monitor?Monitor_VirtualIF_Close(&dev[1]):ApCli_VirtualIF_Close(&dev[1]))==-EBUSY);
  assert(pins==1&&ad.count==2&&!family_calls&&!down_calls);
  cycle_ready(&ad,f,dev);
  assert((monitor?Monitor_VirtualIF_Open(&dev[1]):ApCli_VirtualIF_Open(&dev[1]))==0);
  family_result=1;
  assert((monitor?Monitor_VirtualIF_Close(&dev[1]):ApCli_VirtualIF_Close(&dev[1]))==-EBUSY);
  assert(pins==1&&ad.count==2&&family_calls==1&&!down_calls);
  assert((monitor?Monitor_VirtualIF_Close(&dev[1]):ApCli_VirtualIF_Close(&dev[1]))==-EBUSY);
  assert((monitor?Monitor_VirtualIF_Open(&dev[1]):ApCli_VirtualIF_Open(&dev[1]))==-1);
  assert(pins==1&&ad.count==2&&family_calls==1&&open_family_calls==1);
 }
 assert(!held);return 0;}
'''
a.output.write_text(s+extra+post,encoding='utf-8')
print('Composed actual OPEN/claim-only UP/owned CLOSE/DOWN; auxiliary OWNED created by real OPEN')
