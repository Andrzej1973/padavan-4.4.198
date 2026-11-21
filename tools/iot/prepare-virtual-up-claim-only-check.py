#!/usr/bin/env python3
"""Extract actual UP dispatcher case; test absent/stale/exact ticket admission."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'common/cmm_cfg.c').read_text();begin=s.index('case CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP:')
case=s[begin:s.index('case CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN:',begin)]
assert 'WR_IOT_CLAIM_ONLY_UP' in case
prefix=r'''
#include "virtual-open-claim.h"
#include <assert.h>
#include <string.h>
#include <stddef.h>
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP 1
#define WDEV_NUM_MAX 1
#define IN
typedef void VOID;typedef unsigned int UINT;typedef unsigned long ULONG;
typedef struct {int wr_iot_transition_lock;void *net_dev;unsigned int count;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[2];} RTMP_ADAPTER,*PRTMP_ADAPTER;
typedef struct {int (*rt28xx_open)(void *);int (*rt28xx_close)(void *);
 void *if_dev;unsigned long owner_generation,owner_serial,owner_epoch;int owner_operation;} RT_CMD_INF_UP_DOWN;
static int held,opens,beacons;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
#define VIRTUAL_IF_NUM(ad) ((ad)->count)
#define VIRTUAL_IF_INC(ad) ((ad)->count++)
#define VIRTUAL_IF_DEC(ad) ((ad)->count--)
static int open_radio(void *dev){assert(dev&&!held);opens++;return 0;}
VOID APMakeAllBssBeacon(PRTMP_ADAPTER ad){assert(ad&&!held);beacons++;}
VOID APUpdateAllBeaconFrame(PRTMP_ADAPTER ad){assert(ad&&!held);beacons++;}
static int dispatch(RTMP_ADAPTER *pAd,RT_CMD_INF_UP_DOWN *request){void *pData=request;
 switch(CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP){
'''
post=r'''
 }return NDIS_STATUS_SUCCESS;}
static void setup(RTMP_ADAPTER *a,int *dev){
 memset(a,0,sizeof *a);wr_iot_radio_transition_init(&a->wr_iot_transition);a->net_dev=&dev[0];
 for(int i=0;i<2;i++){wr_iot_ref_init(&a->wr_iot_interface_refs[i],&dev[i],i+1);
  a->wr_iot_interface_refs[i].published=1;}
 a->wr_iot_interface_refs[0].family=WR_REF_FAMILY_MAIN;
 a->wr_iot_interface_refs[1].family=WR_REF_FAMILY_APCLI;
 opens=beacons=0;
}
static void claim(RT_CMD_INF_UP_DOWN *r,void *dev,unsigned long generation,const struct wr_iot_radio_ticket *t){
 memset(r,0,sizeof *r);r->rt28xx_open=open_radio;r->if_dev=dev;
 r->owner_generation=generation;r->owner_serial=t->serial;r->owner_epoch=t->epoch;r->owner_operation=t->operation;
}
int main(void){RTMP_ADAPTER a;RT_CMD_INF_UP_DOWN r;struct wr_iot_radio_ticket t;
 unsigned long generation;int dev[2];
 for(int mode=0;mode<3;mode++){
  setup(&a,dev);a.count=mode==2?~0U:(unsigned int)mode;memset(&r,0,sizeof r);r.rt28xx_open=open_radio;
  unsigned int before=a.count;
  assert(dispatch(&a,NULL)==1&&dispatch(&a,&r)==1);
  assert(a.count==before&&!opens&&!beacons&&!held);
 }
 setup(&a,dev);
 assert(wr_iot_main_open_reserve(&a.wr_iot_transition,a.wr_iot_interface_refs,2,&dev[0],0,&t,&generation));
 claim(&r,&dev[0],generation,&t);r.owner_generation++;
 assert(dispatch(&a,&r)==1&&!a.count&&!opens);r.owner_generation--;
 assert(dispatch(&a,&r)==0&&a.count==1&&opens==1);
 assert(dispatch(&a,&r)==1&&a.count==1&&opens==1);
 setup(&a,dev);a.count=1;a.wr_iot_transition.phase=WR_RADIO_READY;a.wr_iot_transition.main_ready=1;
 a.wr_iot_interface_refs[0].phase=WR_REF_OWNED;a.wr_iot_interface_refs[0].last_token=1;
 assert(wr_iot_aux_open_reserve(&a.wr_iot_transition,a.wr_iot_interface_refs,2,&dev[1],WR_REF_FAMILY_APCLI,1,&t,&generation));
 claim(&r,&dev[1],generation,&t);r.owner_epoch++;
 assert(dispatch(&a,&r)==1&&a.count==1&&!opens&&!beacons);r.owner_epoch--;
 assert(dispatch(&a,&r)==0&&a.count==2&&!opens);
 assert(dispatch(&a,&r)==1&&a.count==2);
 assert(!held);return 0;}
'''
a.output.write_text(prefix+case+post,encoding='utf-8')
print('Extracted actual UP case; kernel/physical open/beacon operations mocked')
