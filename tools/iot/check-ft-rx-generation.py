#!/usr/bin/env python3
"""Exercise ordinary FT RX ingress binding against the pinned SDK source."""
import argparse
import runpy
import subprocess
import tempfile
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
a = p.parse_args()
here = Path(__file__).resolve().parent
src = a.source.resolve()

changes = runpy.run_path(str(here/'assoc-generation-composition.py'))['compose']({}, src, here)
mlme = changes['common/mlme.c']
pending_enqueue = runpy.run_path(
    str(here/'ft-pending-enqueue-composition.py'))
mlme = pending_enqueue['lifecycle'](mlme)
mlme, active_proto = runpy.run_path(
    str(here/'ft-enqueue-generation-composition.py'))['compose'](mlme)
mlme, pending_proto = pending_enqueue['compose'](mlme)
prepared = runpy.run_path(
    str(here/'ft-rx-generation-composition.py'))['compose'](mlme, active_proto, pending_proto)
queue_source = changes['common/mlme.c']
queue_dispatch = queue_source[queue_source.index('VOID MlmeHandler('):]
queue_dispatch = queue_dispatch[:queue_dispatch.index('\n}', queue_dispatch.index('{')) + 2]
for field in ('assoc_gen', 'assoc_wcid', 'assoc_addr'):
    if queue_source.count('Queue->Entry[Tail].' + field) != 1:
        raise AssertionError('stamped MLME requeue lost field: ' + field)
if 'wr_assoc_event_current(pAd, Elem)' not in queue_source:
    raise AssertionError('stale MLME event guard missing')
if 'case WPA_STATE_MACHINE:' not in queue_dispatch or 'StateMachinePerformAction' not in queue_dispatch:
    raise AssertionError('native MLME dispatch body not found')
if queue_dispatch.index('wr_assoc_event_current(pAd, Elem)') > queue_dispatch.index('StateMachinePerformAction'):
    raise AssertionError('stale event guard occurs after native MLME dispatch')
if 'Machine == WPA_STATE_MACHINE && !wr_stamp.gen' not in queue_source:
    raise AssertionError('association generation capture admission changed')
start = prepared.index('BOOLEAN MlmeEnqueueForRecv(')
end = prepared.index('\n}', start) + 2
wrapper = prepared[start:end]
assert 'wr_ft_pending_reserve_locked' in wrapper
assert 'wr_ft_mlme_enqueue_for_recv' in wrapper
assert 'wr_ft_pending_enqueue_for_recv' in wrapper
assert wrapper.index('NdisAcquireSpinLock(&pAd->MacTabLock)') < wrapper.index('wr_ft_peer_capture_locked')
assert wrapper.index('wr_ft_peer_capture_locked') < wrapper.index('NdisReleaseSpinLock(&pAd->MacTabLock)')
assert wrapper.index('wr_ft_pending_enqueue_for_recv') < wrapper.index('wr_ft_pending_release_locked')
ordinary_rx_source = (src/'tx_rx/wdev_rx.c').read_text()
if 'REPORT_MGMT_FRAME_TO_MLME(pAd, pRxBlk->wcid,' not in ordinary_rx_source:
    raise AssertionError('ordinary RX hardware WCID handoff missing from pinned producer')
over_ds = (src/'common/ft_iocl.c').read_text()
over_ds_call = over_ds[over_ds.index('REPORT_MGMT_FRAME_TO_MLME'):]
over_ds_call = over_ds_call[:over_ds_call.index(';') + 1]
if ('FT_OverDs_SimReq' not in over_ds or 'FtEntry->Aid' not in over_ds_call or
        'FtEntry->func_tb_idx' not in over_ds):
    raise AssertionError('FT-over-DS synthetic enqueue producer not covered')

prefix = r'''#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define IN
#define VOID void
typedef unsigned char UCHAR;
typedef unsigned int ULONG;
typedef int BOOLEAN;
#define TRUE 1
#define FALSE 0
#define DOT11R_FT_SUPPORT 1
#define OPMODE_AP 1
#define FC_TYPE_MGMT 0
#define SUBTYPE_ACTION 13
#define SUBTYPE_ACTION_NO_ACK 14
#define FT_CATEGORY_BSS_TRANSITION 6
#define FT_ACTION_BT_REQ 1
#define FT_ACTION_BT_CONFIRM 2
#define LENGTH_802_11 24
#define MAX_LEN_OF_MAC_TABLE 8
#define RESERVED_WCID 0
#define SST_AUTH 1
#define SST_ASSOC 2
#define MAC_ADDR_EQUAL(a,b) (!memcmp((a),(b),6))
#define IS_ENTRY_NONE(e) (!(e)->used)
#define IS_ENTRY_CLIENT(e) ((e)->client)
struct raw_rssi_info { UCHAR raw_rssi[3], raw_snr; };
struct frame_control { UCHAR Type, SubType; };
typedef struct {
 struct frame_control FC; UCHAR duration[2]; UCHAR Addr1[6],Addr2[6],Addr3[6],seq[2];
} HEADER_802_11;
typedef struct { HEADER_802_11 Hdr; } FRAME_802_11, *PFRAME_802_11;
typedef struct { UCHAR Category,Action,StaMac[6],TargetApAddr[6],Oct[1]; } FT_ACTION, *PFT_ACTION;
struct wifi_dev { UCHAR bssid[6]; unsigned func_idx; };
struct mbssid { struct wifi_dev wdev; };
struct ap_config { unsigned BssidNum; struct mbssid MBSSID[4]; };
typedef struct {
 int used,client,Sst; unsigned wcid,func_tb_idx; UCHAR Addr[6]; struct wifi_dev *wdev;
 unsigned assoc_gen;
} MAC_TABLE_ENTRY, *PMAC_TABLE_ENTRY;
struct mac_table { MAC_TABLE_ENTRY Content[MAX_LEN_OF_MAC_TABLE]; };
struct wr_ft_pending_ledger { unsigned next; int live; unsigned bss; UCHAR addr[6]; };
typedef struct _RTMP_ADAPTER {
 int OpMode,MacTabLock; struct ap_config ApCfg; struct mac_table MacTab;
 struct wr_ft_pending_ledger wr_ft_pending;
} RTMP_ADAPTER;
typedef struct _RTMP_ADAPTER *PRTMP_ADAPTER;
struct wr_ft_peer_stamp { unsigned generation,wcid,bss; UCHAR addr[6]; };
struct wr_ft_pending_token { unsigned generation,slot,bss; UCHAR addr[6]; };
static unsigned active_calls,pending_calls,native_calls;
static unsigned active_wcid,active_bss,pending_wcid,pending_bss;
static UCHAR active_addr[6],pending_addr[6];
static int active_ok=1,pending_ok=1;
static void NdisAcquireSpinLock(int *lock){assert(!*lock);*lock=1;}
static void NdisReleaseSpinLock(int *lock){assert(*lock);*lock=0;}
static int wr_ft_peer_capture_locked(RTMP_ADAPTER *ad,unsigned wcid,unsigned bss,
 const UCHAR *addr,struct wr_ft_peer_stamp *stamp){
 MAC_TABLE_ENTRY *e=&ad->MacTab.Content[wcid];
 if(!ad->MacTabLock||wcid>=MAX_LEN_OF_MAC_TABLE||!e->used||!e->client||
    (e->Sst!=SST_AUTH&&e->Sst!=SST_ASSOC)||e->wcid!=wcid||
    e->func_tb_idx!=bss||e->wdev!=&ad->ApCfg.MBSSID[bss].wdev||
    !MAC_ADDR_EQUAL(e->Addr,addr)||!e->assoc_gen)return 0;
 stamp->generation=e->assoc_gen;stamp->wcid=wcid;stamp->bss=bss;
 memcpy(stamp->addr,addr,6);return 1;
}
static int wr_ft_pending_reserve_locked(struct wr_ft_pending_ledger *ledger,
 unsigned bss,const UCHAR *addr,struct wr_ft_pending_token *ticket){
 if(ledger->live)return 0;
 ledger->live=1;ledger->bss=bss;ledger->next++;memcpy(ledger->addr,addr,6);
 ticket->generation=ledger->next;ticket->slot=0;ticket->bss=bss;memcpy(ticket->addr,addr,6);return 1;
}
static int wr_ft_pending_release_locked(struct wr_ft_pending_ledger *ledger,
 struct wr_ft_pending_token *ticket){
 if(!ledger->live||ledger->next!=ticket->generation||ledger->bss!=ticket->bss||
    !MAC_ADDR_EQUAL(ledger->addr,ticket->addr))return 0;
 ledger->live=0;ticket->generation=0;return 1;
}
'''

actors = r'''
BOOLEAN wr_ft_mlme_enqueue_for_recv(RTMP_ADAPTER *pAd,ULONG Wcid,
 struct raw_rssi_info *rssi_info,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
 UCHAR Snr0,UCHAR Snr1,
#endif
 ULONG MsgLen,VOID *Msg,UCHAR OpMode,const struct wr_ft_peer_stamp *expected){
 (void)pAd;(void)rssi_info;(void)MsgLen;(void)Msg;(void)OpMode;
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
 (void)Snr0;(void)Snr1;
#endif
 active_calls++;active_wcid=Wcid;active_bss=expected->bss;memcpy(active_addr,expected->addr,6);
 return active_ok;
}
BOOLEAN wr_ft_pending_enqueue_for_recv(RTMP_ADAPTER *pAd,ULONG Wcid,
 struct raw_rssi_info *rssi_info,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
 UCHAR Snr0,UCHAR Snr1,
#endif
 ULONG MsgLen,VOID *Msg,UCHAR OpMode,struct wr_ft_pending_token *ticket){
 (void)pAd;(void)rssi_info;(void)MsgLen;(void)Msg;(void)OpMode;
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
 (void)Snr0;(void)Snr1;
#endif
 pending_calls++;pending_wcid=Wcid;pending_bss=ticket->bss;memcpy(pending_addr,ticket->addr,6);
 if(pending_ok)ticket->generation=0;
 return pending_ok;
}
static BOOLEAN wr_ft_native_mlme_enqueue_for_recv(RTMP_ADAPTER *pAd,ULONG Wcid,
 struct raw_rssi_info *rssi_info,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
 UCHAR Snr0,UCHAR Snr1,
#endif
 ULONG MsgLen,VOID *Msg,UCHAR OpMode){
 (void)pAd;(void)Wcid;(void)rssi_info;(void)MsgLen;(void)Msg;(void)OpMode;
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
 (void)Snr0;(void)Snr1;
#endif
 native_calls++;return TRUE;
}
'''

main = r'''
static unsigned char bssid0[6]={2,0,0,0,0,10},bssid1[6]={2,0,0,0,0,11};
static unsigned char peer[6]={2,1,2,3,4,5},foreign[6]={2,1,2,3,4,6};
static RTMP_ADAPTER ad;static struct raw_rssi_info rssi;
static UCHAR *make_frame(UCHAR *buf,const UCHAR *bssid,const UCHAR *src,
 UCHAR action,const UCHAR *target,const UCHAR *sta,unsigned len){
 FRAME_802_11 *f=(FRAME_802_11 *)buf;FT_ACTION *a=(FT_ACTION *)(buf+LENGTH_802_11);
 memset(buf,0,128);f->Hdr.FC.Type=FC_TYPE_MGMT;f->Hdr.FC.SubType=SUBTYPE_ACTION;
 memcpy(f->Hdr.Addr1,bssid,6);memcpy(f->Hdr.Addr2,src,6);
 a->Category=FT_CATEGORY_BSS_TRANSITION;a->Action=action;
 memcpy(a->TargetApAddr,target,6);memcpy(a->StaMac,sta,6);(void)len;return buf;
}
static void reset_calls(void){active_calls=pending_calls=native_calls=0;active_ok=pending_ok=1;}
int main(void){
 UCHAR msg[128];struct raw_rssi_info *ri=&rssi;
 ad.OpMode=OPMODE_AP;ad.ApCfg.BssidNum=2;
 memcpy(ad.ApCfg.MBSSID[0].wdev.bssid,bssid0,6);ad.ApCfg.MBSSID[0].wdev.func_idx=0;
 memcpy(ad.ApCfg.MBSSID[1].wdev.bssid,bssid1,6);ad.ApCfg.MBSSID[1].wdev.func_idx=1;
 make_frame(msg,bssid1,peer,FT_ACTION_BT_CONFIRM,bssid1,peer,sizeof(msg));
 MAC_TABLE_ENTRY *e=&ad.MacTab.Content[3];e->used=e->client=1;e->Sst=SST_ASSOC;e->wcid=3;
 e->func_tb_idx=1;e->wdev=&ad.ApCfg.MBSSID[1].wdev;e->assoc_gen=9;memcpy(e->Addr,peer,6);
 reset_calls();assert(MlmeEnqueueForRecv(&ad,0,ri,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
  0,0,
#endif
  LENGTH_802_11+sizeof(FT_ACTION),msg,OPMODE_AP));
 assert(active_calls==1&&!pending_calls&&!native_calls&&active_wcid==3&&active_bss==1);
 assert(MAC_ADDR_EQUAL(active_addr,peer)&&!ad.MacTabLock);
 ad.MacTab.Content[4]=*e;reset_calls();
 assert(!MlmeEnqueueForRecv(&ad,3,ri,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
  0,0,
#endif
  LENGTH_802_11+sizeof(FT_ACTION),msg,OPMODE_AP));
 assert(!active_calls&&!pending_calls&&!native_calls&&!ad.MacTabLock);
 memset(&ad.MacTab.Content[4],0,sizeof(ad.MacTab.Content[4]));
 reset_calls();active_ok=0;
 assert(!MlmeEnqueueForRecv(&ad,3,ri,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
  0,0,
#endif
  LENGTH_802_11+sizeof(FT_ACTION),msg,OPMODE_AP));
 assert(active_calls==1&&!pending_calls&&!native_calls&&!ad.MacTabLock);

 /* Same MAC on another BSS is not an active match; local first-peer BT_REQ reserves BSS 1. */
 memset(ad.MacTab.Content,0,sizeof(ad.MacTab.Content));
 e=&ad.MacTab.Content[2];e->used=e->client=1;e->Sst=SST_ASSOC;e->wcid=2;
 e->func_tb_idx=0;e->wdev=&ad.ApCfg.MBSSID[0].wdev;e->assoc_gen=4;memcpy(e->Addr,peer,6);
 make_frame(msg,bssid1,peer,FT_ACTION_BT_REQ,bssid1,peer,sizeof(msg));reset_calls();
 assert(MlmeEnqueueForRecv(&ad,2,ri,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
  0,0,
#endif
  LENGTH_802_11+sizeof(FT_ACTION),msg,OPMODE_AP));
 assert(!active_calls&&pending_calls==1&&!native_calls&&pending_wcid==RESERVED_WCID&&pending_bss==1);
 assert(MAC_ADDR_EQUAL(pending_addr,peer)&&!ad.MacTabLock);

 /* Inactive or inconsistent same-BSS identity refuses; it never becomes a fresh ticket. */
 memset(ad.MacTab.Content,0,sizeof(ad.MacTab.Content));ad.wr_ft_pending.live=0;
 e=&ad.MacTab.Content[4];e->used=e->client=1;e->Sst=0;e->wcid=4;e->func_tb_idx=1;
 e->wdev=&ad.ApCfg.MBSSID[1].wdev;memcpy(e->Addr,peer,6);reset_calls();
 assert(!MlmeEnqueueForRecv(&ad,4,ri,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
  0,0,
#endif
  LENGTH_802_11+sizeof(FT_ACTION),msg,OPMODE_AP));
 assert(!active_calls&&!pending_calls&&!native_calls&&!ad.MacTabLock);
 e->Sst=SST_ASSOC;e->wdev=&ad.ApCfg.MBSSID[0].wdev;reset_calls();
 assert(!MlmeEnqueueForRecv(&ad,4,ri,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
  0,0,
#endif
  LENGTH_802_11+sizeof(FT_ACTION),msg,OPMODE_AP));
 assert(!active_calls&&!pending_calls&&!native_calls&&!ad.MacTabLock);

 /* Non-terminating requests and mismatched station identity cannot get a new-peer ticket. */
 memset(ad.MacTab.Content,0,sizeof(ad.MacTab.Content));ad.wr_ft_pending.live=0;
 make_frame(msg,bssid1,peer,FT_ACTION_BT_REQ,bssid0,peer,sizeof(msg));reset_calls();
 assert(!MlmeEnqueueForRecv(&ad,0,ri,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
  0,0,
#endif
  LENGTH_802_11+sizeof(FT_ACTION),msg,OPMODE_AP));
 make_frame(msg,bssid1,peer,FT_ACTION_BT_REQ,bssid1,foreign,sizeof(msg));reset_calls();
 assert(!MlmeEnqueueForRecv(&ad,0,ri,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
  0,0,
#endif
  LENGTH_802_11+sizeof(FT_ACTION),msg,OPMODE_AP));
 assert(!pending_calls&&!native_calls);

 /* Failed pending enqueue releases the producer reference; malformed context refuses. */
 make_frame(msg,bssid1,peer,FT_ACTION_BT_REQ,bssid1,peer,sizeof(msg));reset_calls();pending_ok=0;
 assert(!MlmeEnqueueForRecv(&ad,0,ri,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
  0,0,
#endif
  LENGTH_802_11+sizeof(FT_ACTION),msg,OPMODE_AP));
 assert(pending_calls==1&&!ad.wr_ft_pending.live&&!ad.MacTabLock);
 memset(msg,0,sizeof(msg));((FRAME_802_11 *)msg)->Hdr.FC.Type=FC_TYPE_MGMT;
 ((FRAME_802_11 *)msg)->Hdr.FC.SubType=SUBTYPE_ACTION;memcpy(((FRAME_802_11 *)msg)->Hdr.Addr1,bssid1,6);
 msg[LENGTH_802_11]=FT_CATEGORY_BSS_TRANSITION;reset_calls();
 assert(!MlmeEnqueueForRecv(&ad,0,ri,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
  0,0,
#endif
  LENGTH_802_11+1,msg,OPMODE_AP));assert(!pending_calls&&!active_calls);

 /* Non-FT and non-AP receive behavior remains routed through native enqueue. */
 msg[LENGTH_802_11]=3;reset_calls();
 assert(MlmeEnqueueForRecv(&ad,5,ri,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
  0,0,
#endif
  LENGTH_802_11+1,msg,OPMODE_AP));assert(native_calls==1&&!active_calls&&!pending_calls);
 make_frame(msg,bssid1,peer,FT_ACTION_BT_REQ,bssid1,peer,sizeof(msg));ad.OpMode=0;reset_calls();
 assert(MlmeEnqueueForRecv(&ad,5,ri,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
  0,0,
#endif
  LENGTH_802_11+sizeof(FT_ACTION),msg,OPMODE_AP));assert(native_calls==1&&!pending_calls&&!active_calls);
 puts("PASS | ordinary FT RX identity | exact active BSS stamp; duplicate, foreign, inactive, inconsistent and non-terminating entries refused; local first-peer BT_REQ ticket");
 puts("PASS | ordinary FT RX failure paths | enqueue refusal releases ticket; malformed identity refused; non-FT/native fallback preserved");
 return 0;
}
'''

source = prefix + active_proto + '\n' + pending_proto + '\n' + actors + '\n' + wrapper + '\n' + main
with tempfile.TemporaryDirectory(prefix='ft-rx-generation-') as td:
    cfile = Path(td)/'check.c'
    cfile.write_text(source)
    for variant in ([], ['-DCUSTOMER_DCC_FEATURE']):
        binary = Path(td)/('check-dcc' if variant else 'check')
        cmd = ['gcc', '-std=gnu11', '-O1', '-Wall', '-Wextra', '-Werror',
               '-Wno-unused-parameter', '-fsanitize=address,undefined',
               '-fno-pie', '-no-pie', *variant, str(cfile), '-o', str(binary)]
        build = subprocess.run(cmd, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stderr)
        result = subprocess.run([str(binary)], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        print(result.stdout, end='')
print('PASS | ordinary FT RX composition | pinned native enqueue wrapper, exact context lookup and duplicate preparation guard')
print('PASS | FT association generation provenance | queue copy/requeue, stale-before-dispatch gate and three pinned RX producer families')
