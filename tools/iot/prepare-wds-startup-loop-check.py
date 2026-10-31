#!/usr/bin/env python3
"""Extract configured WDS loops; lower insertion/record readiness mocked."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'ap/ap_wds.c').read_text()
def body(sig):
 st=s.index(sig);return s[st:s.index('\n}',st)+2]
prefix=r'''
#include "peer-open-owner.h"
#include <assert.h>
#include <stddef.h>
#include <string.h>
#define TRUE 1
#define FALSE 0
#define MAX_WDS_ENTRY 3
#define WDS_LAZY_MODE 2
#define MODE_HTMIX 3
#define MODE_CCK 1
#define MODE_OFDM 2
#define WMODE_B 1
#define WMODE_CAP_N(p) ((p)==3)
#define WMODE_EQUAL(p,q) ((p)==(q))
typedef int BOOLEAN;typedef void VOID;typedef unsigned int UINT;typedef unsigned char UCHAR;
typedef struct {int value;} MAC_TABLE_ENTRY;
typedef struct {struct {int PhyMode;} wdev;int Valid;UCHAR PeerWdsAddr[6];} RT_802_11_WDS_ENTRY;
typedef struct {int MacTabLock;struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 struct wr_iot_peer_open_owner wr_iot_peer_open_owner;struct {int PhyMode;} CommonCfg;
 struct {int Mode;RT_802_11_WDS_ENTRY WdsEntry[3];} WdsTab;} RTMP_ADAPTER;
static int held,calls,fail_index=-1,retain_index=-1;static MAC_TABLE_ENTRY peer;
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=1;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;}while(0)
static MAC_TABLE_ENTRY *wr_iot_wds_insert_transaction(RTMP_ADAPTER *a,UCHAR *addr,UINT index,UINT mode){
 (void)a;(void)addr;assert(!held&&mode==2);calls++;return (int)index==fail_index?NULL:&peer;}
static MAC_TABLE_ENTRY *wr_iot_wds_insert_startup(RTMP_ADAPTER *a,UCHAR *addr,UINT index,const struct wr_iot_peer_open_ticket *t){
 (void)addr;assert(!held&&wr_iot_peer_open_matches(&a->wr_iot_peer_open_owner,&a->wr_iot_peer_table_owner,t));calls++;
 if((int)index==retain_index)assert(wr_iot_peer_open_finish(&a->wr_iot_peer_open_owner,&a->wr_iot_peer_table_owner,t,0));
 return (int)index==fail_index?NULL:&peer;}
'''
tail=r'''
static RTMP_ADAPTER a;static int device;static struct wr_iot_peer_open_ticket t;
static void setup(void){memset(&a,0,sizeof a);held=calls=0;fail_index=retain_index=-1;
 wr_iot_peer_table_owner_init(&a.wr_iot_peer_table_owner);wr_iot_peer_open_owner_init(&a.wr_iot_peer_open_owner);
 assert(wr_iot_peer_open_begin(&a.wr_iot_peer_open_owner,&a.wr_iot_peer_table_owner,&device,1,&t));
 assert(wr_iot_peer_open_startup(&a.wr_iot_peer_open_owner,&a.wr_iot_peer_table_owner,&t));}
int main(void){setup();assert(wr_iot_wds_startup_table(&a,&t)&&!calls&&!held);
 for(int mode=1;mode<=3;mode++){
 setup();a.WdsTab.Mode=WDS_LAZY_MODE;a.CommonCfg.PhyMode=mode;
 a.WdsTab.WdsEntry[0].Valid=a.WdsTab.WdsEntry[2].Valid=1;
 assert(wr_iot_wds_startup_table(&a,&t)&&calls==2&&!held);
 for(int i=0;i<3;i++)assert(a.WdsTab.WdsEntry[i].wdev.PhyMode==mode);
 }
 setup();a.WdsTab.WdsEntry[0].Valid=a.WdsTab.WdsEntry[2].Valid=1;fail_index=0;
 assert(!wr_iot_wds_startup_table(&a,&t)&&calls==1&&!held);
 calls=0;AsicUpdateWdsRxWCIDTable(&a);assert(calls==2);
 setup();a.WdsTab.WdsEntry[2].Valid=1;retain_index=2;
 assert(!wr_iot_wds_startup_table(&a,&t)&&calls==1&&!held);
 setup();t.serial++;assert(!wr_iot_wds_startup_table(&a,&t)&&!calls&&!held);
 assert(!wr_iot_wds_startup_table(NULL,&t));assert(!wr_iot_wds_startup_table(&a,NULL));
 return 0;}
'''
a.output.write_text(prefix+body('VOID AsicUpdateWdsRxWCIDTable(')+'\n'+body('BOOLEAN wr_iot_wds_startup_table(')+tail,encoding='utf-8')
print('Extracted legacy/checked configured WDS loops; actual lower transaction/readiness not tested')
