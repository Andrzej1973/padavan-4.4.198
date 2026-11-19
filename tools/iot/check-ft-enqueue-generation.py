#!/usr/bin/env python3
"""Execute the complete explicit-stamp native receive enqueue with host actors."""
import argparse,runpy,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
prepared=runpy.run_path(str(here/'assoc-generation-composition.py'))['compose']({},a.source,here)['common/mlme.c']
compose=runpy.run_path(str(here/'ft-enqueue-generation-composition.py'))['compose']
changed,prototype=compose(prepared)
assert changed.count('BOOLEAN wr_ft_mlme_enqueue_for_recv(')==2
start=changed.rindex('BOOLEAN wr_ft_mlme_enqueue_for_recv(')
body=changed[start:changed.index('\n}',start)+2]
assert 'wr_assoc_capture(' not in body and body.count('wr_stamp.gen=wr_expected->generation')==2
assert body.count('wr_assoc_publish(')==2
assert changed.replace('\n#ifdef DOT11R_FT_SUPPORT\n#include "ft-peer-generation.h"\n'+prototype+'\n'+body+'\n#endif\n','',1)==prepared
try:compose(changed)
except ValueError:pass
else:raise AssertionError('duplicate accepted')
prefix=r'''
#include <assert.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include "peer-table-owner.h"
#define IN
#define TRUE 1
#define FALSE 0
#define MAC_ADDR_LEN 6
#define LENGTH_802_11 24
#define MGMT_DMA_BUFFER_SIZE 1600
#define MAX_LEN_OF_MAC_TABLE 8
#define MAX_LEN_OF_MLME_QUEUE 4
#define MAX_LEN_OF_EAP_QUEUE 4
#define RESERVED_WCID 0
#define SST_AUTH 1
#define SST_ASSOC 2
#define IS_ENTRY_CLIENT(e) ((e)->client)
#define MAC_ADDR_EQUAL(a,b) (!memcmp(a,b,6))
#define COPY_MAC_ADDR(a,b) memcpy(a,b,6)
#define NdisMoveMemory memcpy
#define DBGPRINT_ERR(args) ((void)0)
#define DBGPRINT(level,args) ((void)0)
#define RTMP_TEST_FLAG(ad,flags) ((void)(flags),0)
#define fRTMP_ADAPTER_HALT_IN_PROGRESS 1
#define fRTMP_ADAPTER_NIC_NOT_EXIST 2
#define CONFIG_AP_SUPPORT
#define IF_DEV_CONFIG_OPMODE_ON_AP(ad) if(1)
#define ACTION_STATE_MACHINE 7
#define WPA_STATE_MACHINE 1
#define FT_CATEGORY_BSS_TRANSITION 6
#define BW_40 1
#define RTMP_MLME_HANDLER(ad) ((ad)->dispatches++)
typedef unsigned char UCHAR;
typedef unsigned long ULONG;
typedef unsigned int UINT32;
typedef int INT,BOOLEAN;
typedef void VOID;
struct raw_rssi_info{unsigned char raw_rssi[3],raw_snr;};
typedef struct {unsigned char Addr1[6],Addr2[6],rest[12];} HEADER_802_11;
typedef struct {HEADER_802_11 Hdr;unsigned char Octet[14];} FRAME_802_11,*PFRAME_802_11;
typedef struct {unsigned char Category,Action,StaMac[6],TargetApAddr[6],Oct[0];} FT_ACTION;
typedef struct {unsigned assoc_gen;unsigned short assoc_wcid;unsigned char assoc_addr[6],Msg[1600];
 ULONG Machine,MsgType,MsgLen,OpMode,Priv;unsigned Wcid,Signal,Channel,Snr0,Snr1;
 struct {struct {UINT32 LowPart,HighPart;} u;} TimeStamp;struct raw_rssi_info rssi_info;int Occupied;} MLME_QUEUE_ELEM;
typedef struct {int Lock,Tail,Num;MLME_QUEUE_ELEM Entry[4];} MLME_QUEUE,EAP_MLME_QUEUE;
struct wifi_dev{unsigned char bssid[6];};
typedef struct {unsigned assoc_gen,wcid,func_tb_idx;int Sst,client;unsigned char Addr[6];struct wifi_dev *wdev;} MAC_TABLE_ENTRY;
typedef struct {struct {unsigned BssidNum;struct {struct wifi_dev wdev;} MBSSID[3];} ApCfg;
 struct {MAC_TABLE_ENTRY Content[8];} MacTab;unsigned wr_iot_peer_delete_active,wr_assoc_event_users[8];
 struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 struct {MLME_QUEUE Queue,EAP_Queue;} Mlme;struct {int BBPCurrentBW,Channel;} CommonCfg;
 struct {int Channel;} LatchRfRegs;int dispatches;} RTMP_ADAPTER;
#include "ft-peer-generation.h"
struct wr_assoc_stamp{unsigned gen,wcid;unsigned char addr[6];};
static void wr_assoc_publish(MLME_QUEUE_ELEM *e,const struct wr_assoc_stamp *s){e->assoc_gen=s->gen;e->assoc_wcid=s->wcid;COPY_MAC_ADDR(e->assoc_addr,s->addr);}
static int MlmeQueueFull(MLME_QUEUE *q,int n){(void)n;return q->Num>=4;}
static int EAPMlmeQueueFull(EAP_MLME_QUEUE *q){return q->Num>=4;}
static int APMsgTypeSubst(RTMP_ADAPTER *ad,PFRAME_802_11 f,int *machine,int *type){(void)ad;(void)f;*machine=ACTION_STATE_MACHINE;*type=FT_CATEGORY_BSS_TRANSITION;return 1;}
static RTMP_ADAPTER *hook;static int replace_before_queue;
static void NdisAcquireSpinLock(int *lock){
 assert(!*lock);*lock=1;
 if(replace_before_queue){hook->MacTab.Content[7].assoc_gen++;replace_before_queue=0;}
}
static void NdisReleaseSpinLock(int *lock){assert(*lock);*lock=0;}
'''
main=r'''
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
#define ENQUEUE(a,w,r,n,f,s) wr_ft_mlme_enqueue_for_recv(a,w,r,0,0,n,f,0,s)
#else
#define ENQUEUE(a,w,r,n,f,s) wr_ft_mlme_enqueue_for_recv(a,w,r,n,f,0,s)
#endif
int main(void){
 RTMP_ADAPTER ad={0};ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.bssid[0]=2;
 MAC_TABLE_ENTRY *e=&ad.MacTab.Content[7];*e=(MAC_TABLE_ENTRY){.assoc_gen=1,.wcid=7,.func_tb_idx=2,.Sst=SST_ASSOC,.client=1,.Addr={42},.wdev=&ad.ApCfg.MBSSID[2].wdev};
 struct wr_ft_peer_stamp expected={0};assert(wr_ft_peer_capture_locked(&ad,7,2,e->Addr,&expected));
 FRAME_802_11 frame={0};frame.Hdr.Addr1[0]=2;frame.Hdr.Addr2[0]=42;
 struct raw_rssi_info rssi={0};hook=&ad;replace_before_queue=1;
 assert(ENQUEUE(&ad,7,&rssi,sizeof(frame),&frame,&expected));
 MLME_QUEUE_ELEM *queued=&ad.Mlme.Queue.Entry[0];
 assert(e->assoc_gen==2&&queued->assoc_gen==1&&queued->assoc_wcid==7);
 assert(!memcmp(queued->assoc_addr,expected.addr,6)&&queued->Wcid==7);
 assert(queued->Machine==ACTION_STATE_MACHINE&&queued->MsgType==6&&queued->Occupied);
 assert(!memcmp(queued->Msg,&frame,sizeof(frame))&&ad.Mlme.Queue.Num==1);
 assert(!wr_ft_peer_current_locked(&ad,&expected));
 assert(!ENQUEUE(&ad,7,&rssi,sizeof(frame),&frame,NULL));
 assert(!ENQUEUE(&ad,3,&rssi,sizeof(frame),&frame,&expected));
 struct wr_ft_peer_stamp invalid=expected;invalid.wcid=300;
 assert(!ENQUEUE(&ad,300,&rssi,sizeof(frame),&frame,&invalid));
 frame.Hdr.Addr1[0]=0;assert(!ENQUEUE(&ad,7,&rssi,sizeof(frame),&frame,&expected));frame.Hdr.Addr1[0]=2;
 frame.Hdr.Addr2[0]=43;assert(!ENQUEUE(&ad,7,&rssi,sizeof(frame),&frame,&expected));frame.Hdr.Addr2[0]=42;
 for(unsigned len=0;len<sizeof(frame);len++){
  unsigned char *short_frame=calloc(1,len?len:1);assert(short_frame);
  assert(!ENQUEUE(&ad,7,&rssi,len,short_frame,&expected));free(short_frame);
 }
 assert(ad.Mlme.Queue.Num==1);
 assert(wr_ft_peer_capture_locked(&ad,7,2,e->Addr,&expected));
 assert(ENQUEUE(&ad,7,&rssi,sizeof(frame),&frame,&expected));
 assert(ad.Mlme.Queue.Entry[1].assoc_gen==2);
 ad.Mlme.Queue.Entry[2].Occupied=1;assert(!ENQUEUE(&ad,7,&rssi,sizeof(frame),&frame,&expected));
 assert(ad.Mlme.Queue.Num==2&&!ad.Mlme.Queue.Lock);
 ad.Mlme.Queue.Num=4;assert(!ENQUEUE(&ad,7,&rssi,sizeof(frame),&frame,&expected));
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ft-enqueue-') as td:
 src=Path(td)/'check.c';exe=Path(td)/'check';src.write_text(prefix+prototype+"\n"+body+main)
 for flags in ([],['-DEAPOL_QUEUE_SUPPORT'],['-DCUSTOMER_DCC_FEATURE']):
  subprocess.run(['gcc','-std=gnu11','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),*flags,str(src),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
print('PASS | explicit FT native enqueue | immutable generation across slot reuse, exact queue metadata, BSS/MAC/WCID refusal, occupied/full queue, EAP/SNR variants; uninstalled')
