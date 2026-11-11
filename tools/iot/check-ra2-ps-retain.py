#!/usr/bin/env python3
"""Execute actual SDK PS queue maintenance and completion with local ra2 policy."""
import argparse
import importlib.util
from pathlib import Path
import subprocess
import tarfile
import tempfile

here = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--archive', type=Path)
parser.add_argument('--driver', type=Path)
args = parser.parse_args()
if bool(args.archive) == bool(args.driver):
    parser.error('Select one source archive or prepared driver')
if args.archive:
    spec = importlib.util.spec_from_file_location('ra2_policy', here / 'ra2-ps-composition.py')
    policy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(policy)
    with tarfile.open(args.archive) as archive:
        sources = {name: archive.extractfile('trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/' + name).read().decode()
                   for name in ['ap/ap.c', 'tx_rx/txs.c']}
    original = dict(sources)
    with tempfile.TemporaryDirectory(prefix='wr-ra2-ps-compose-') as scratch:
        root = Path(scratch)
        sources = policy.compose(sources, root, here)
        try:
            policy.compose(sources, root, here)
        except ValueError:
            pass
        else:
            raise AssertionError('Repeated preparation accepted')
    assert original['ap/ap.c'].count('wr_iot_ra2_sleeping_pending') == 0
else:
    sources = {name: (args.driver / name).read_text()
               for name in ['ap/ap.c', 'tx_rx/txs.c', 'include/ra2-ps-retain.h']}
assert sources['include/ra2-ps-retain.h'] == (here / 'ra2-ps-retain.h').read_text()
ap = sources['ap/ap.c']
start = ap.index('\t\t/* 3. garbage collect the ps_queue')
end = ap.index('\n#ifdef UAPSD_SUPPORT', start)
maintenance = ap[start:end]
txs = sources['tx_rx/txs.c']
start = txs.index('INT32 PsDataTxSHandler(')
completion = txs[start:txs.index('\n}', start) + 2]
assert 'wr_iot_ra2_sleeping_pending' in maintenance and 'wr_iot_ra2_sleeping_pending' in completion
prefix = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define MAX_LEN_OF_MAC_TABLE 4
#define MAX_LEN_OF_TR_TABLE 4
#define WLAN_MAX_NUM_OF_TIM 8
#define PWR_SAVE 1
#define PWR_ACTIVE 0
#define SST_ASSOC 1
#define APPS_RETRIEVE_DONE 1
#define APPS_RETRIEVE_IDLE 0
#define IS_ENTRY_CLIENT(e) ((e)->client)
#define IS_MT7603(ad) ((ad)->mt)
#define RT_DEBUG_TRACE 0
#define DBGPRINT(level,args) do{(void)(level);}while(0)
typedef int INT32;
typedef unsigned int UINT32;
typedef char CHAR;
struct device {int running;};
struct wifi_dev {struct device *if_dev;};
typedef struct {unsigned int wcid,func_tb_idx,Aid,NoDataIdleCount,StaIdleTimeout;int client,Sst,PsMode;struct wifi_dev *wdev;} MAC_TABLE_ENTRY;
typedef struct {unsigned int wcid,func_tb_idx,enqCount,PsQIdleCount,PsDeQWaitCnt;int PsMode,ps_state;} STA_TR_ENTRY;
typedef struct {int mt;struct {int BssidNum;struct {struct wifi_dev wdev;struct {int bBcnSntReq;} bcn_buf;} MBSSID[3];} ApCfg;
 struct {MAC_TABLE_ENTRY Content[4];STA_TR_ENTRY tr_entry[4];} MacTab;} RTMP_ADAPTER;
typedef struct {unsigned int wlan_idx;} TXS_D_3;
typedef struct {unsigned int LE;} TXS_D_0;
typedef struct {TXS_D_0 txs_d0;TXS_D_3 txs_d3;} TXS_STRUC;
#ifdef WR_IOT_PSM_DIAG
static unsigned diag_hits;
#define wr_iot_ps_diag(e,b,p,x,y) do{assert((e)==6&&(b)==2&&(p)==1);(void)(x);assert((y)==2);diag_hits++;}while(0)
#endif
static int tim,flushes;
#define WLAN_MR_TIM_BIT_SET(ad,bss,aid) do{assert((ad)&&(bss)==2&&(aid)==1);tim=1;}while(0)
#define WLAN_MR_TIM_BIT_CLEAR(ad,bss,aid) do{}while(0)
static void rtmp_tx_swq_exit(RTMP_ADAPTER *ad,unsigned int wcid){flushes++;ad->MacTab.tr_entry[wcid].enqCount=0;}
'''
main = r'''
int main(void)
{
 for(int fault=0;fault<21;fault++){
  struct device dev={1};struct wifi_dev foreign={&dev};
  RTMP_ADAPTER ad={.mt=1,.ApCfg.BssidNum=3};
  MAC_TABLE_ENTRY *entry=&ad.MacTab.Content[1];STA_TR_ENTRY *traffic=&ad.MacTab.tr_entry[1];
  ad.ApCfg.MBSSID[2].wdev.if_dev=&dev;ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=1;
  *entry=(MAC_TABLE_ENTRY){.wcid=1,.func_tb_idx=2,.Aid=1,.StaIdleTimeout=300,
   .client=1,.Sst=SST_ASSOC,.PsMode=PWR_SAVE,.wdev=&ad.ApCfg.MBSSID[2].wdev};
  *traffic=(STA_TR_ENTRY){.wcid=1,.func_tb_idx=2,.enqCount=2,.PsQIdleCount=2,.PsDeQWaitCnt=1,.PsMode=PWR_SAVE,.ps_state=APPS_RETRIEVE_DONE};
  switch(fault){
   case 1:ad.mt=0;break;
   case 2:ad.ApCfg.BssidNum=2;break;
   case 3:entry->func_tb_idx=0;break;
   case 4:entry->func_tb_idx=1;break;
   case 5:traffic->func_tb_idx=1;break;
   case 6:entry->wdev=&foreign;break;
   case 7:entry->wdev=NULL;break;
   case 8:ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=0;break;
   case 9:entry->client=0;break;
   case 10:entry->Sst=0;break;
   case 11:entry->NoDataIdleCount=300;break;
   case 12:entry->Aid=64;break;
   case 13:entry->wcid=2;break;
   case 14:traffic->wcid=2;break;
   case 15:traffic->PsMode=PWR_ACTIVE;break;
   case 16:traffic->enqCount=0;break;
   case 17:entry->PsMode=PWR_ACTIVE;break;
   case 18:entry->Aid=0;break;
   case 19:ad.ApCfg.MBSSID[2].wdev.if_dev=NULL;break;
   case 20:traffic->ps_state=APPS_RETRIEVE_IDLE;break;
  }
  assert(!wr_iot_ra2_sleeping_pending(NULL,1));
  assert(!wr_iot_ra2_sleeping_pending(&ad,MAX_LEN_OF_MAC_TABLE));
  assert(!wr_iot_ra2_sleeping_pending(&ad,~0U));
  assert(wr_iot_ra2_sleeping_pending(&ad,1)==(fault==0||fault==20));
  TXS_STRUC report={.txs_d3.wlan_idx=1};tim=flushes=0;
  assert(!PsDataTxSHandler(NULL,(CHAR *)&report,0));
  assert(!PsDataTxSHandler(&ad,NULL,0));
  assert(!PsDataTxSHandler(&ad,(CHAR *)&report,0));
  assert(tim==(fault==0||fault==20)&&traffic->PsDeQWaitCnt==0&&traffic->enqCount==(fault==16?0U:2U));
#ifdef WR_IOT_PSM_DIAG
  assert(diag_hits==0);
  report.txs_d0.LE=1;
  assert(!PsDataTxSHandler(&ad,(CHAR *)&report,0));
  assert(diag_hits==(unsigned)(fault==0||fault==20));
  diag_hits=0;
#endif
  /* Maintenance receives its current entry pointer, so the mismatched-WCID
   * cases are tested by the helper/completion above only. */
  if(fault==13||fault==14)continue;
  tim=0;maintenance(&ad,entry,traffic);
  if(fault==0||fault==20){
   assert(!flushes&&traffic->enqCount==2&&tim&&traffic->PsQIdleCount==0);
   entry->PsMode=PWR_ACTIVE;traffic->PsMode=PWR_ACTIVE;
   maintenance(&ad,entry,traffic);
   assert(!traffic->PsQIdleCount&&!flushes&&traffic->enqCount==2);
   /* Sleeping again must not retain data after the association idle deadline. */
   entry->PsMode=PWR_SAVE;traffic->PsMode=PWR_SAVE;
   traffic->PsQIdleCount=2;entry->NoDataIdleCount=entry->StaIdleTimeout;
   tim=0;maintenance(&ad,entry,traffic);
   assert(flushes==1&&traffic->enqCount==0&&!tim);
  }else if(fault==17)assert(!flushes&&traffic->enqCount==2&&!traffic->PsQIdleCount);
  else if(fault!=16)assert(flushes==1&&traffic->enqCount==0);
 }
 puts("PASS actual SDK PS maintenance/completion: scoped ra2 retention/TIM, Main/Guest/foreign/expired/wake refusal, bounded AID and existing completion accounting; station I/O and wake dequeue injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ra2-ps-check-') as scratch:
    root = Path(scratch)
    code = prefix + sources['include/ra2-ps-retain.h'] + '\n' + completion
    code += '\nstatic void maintenance(RTMP_ADAPTER *pAd,MAC_TABLE_ENTRY *pEntry,STA_TR_ENTRY *tr_entry){\n' + maintenance + '\n}\n' + main
    (root / 'check.c').write_text(code)
    for mode in ('off', 'on'):
        command = ['gcc', '-std=gnu11', '-O2', '-Wall', '-Wextra', '-Werror',
                   '-Wno-unused-parameter', '-fsanitize=address,undefined',
                   '-fno-pie', '-no-pie', str(root / 'check.c'), '-o', str(root / 'check')]
        if mode == 'on':
            command.append('-DWR_IOT_PSM_DIAG')
        subprocess.run(command, check=True)
        subprocess.run([str(root / 'check')], check=True)
    size = sum(path.stat().st_size for path in root.iterdir())
assert not root.exists()
print('Owned scratch removed bytes', size)
