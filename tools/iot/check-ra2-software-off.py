#!/usr/bin/env python3
"""Exercise scoped software queue gating and reopen using injected SDK locks."""
import argparse
from pathlib import Path
import runpy
import subprocess
import tarfile
import tempfile

here = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--archive', type=Path)
group.add_argument('--driver', type=Path)
args = parser.parse_args()
names = ('ap/ap_mbss.c', 'ap/ap_data.c')
if args.archive:
    with tarfile.open(args.archive) as archive:
        sources = {name: archive.extractfile(
            'trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/' + name
        ).read().decode() for name in names}
    pristine = dict(sources)
    with tempfile.TemporaryDirectory(prefix='wr-ra2-off-compose-') as directory:
        compose = runpy.run_path(str(here / 'ra2-software-off-composition.py'))['compose']
        sources = compose(sources, Path(directory), here)
        # Exercise the prepared beacon lock and rollback layout too.
        prepared = dict(pristine)
        text = prepared['ap/ap_mbss.c']
        begin = text.index('INT32 MBSS_Open(PNET_DEV pDev)')
        end = text.index('\n}', begin) + 2
        opening = text[begin:end].replace('#ifdef AIRPLAY_SUPPORT',
            '\tRTMP_SEM_LOCK(&pAd->BcnRingLock);\n#ifdef AIRPLAY_SUPPORT', 1)
        text = text[:begin] + opening + text[end:]
        abort = ('INT MBSS_AbortOpen(PNET_DEV pDev)\n{\n'
                 '    if (!wr_iot_bcn_revoke_and_drain(pAd, BssId)) return -1;\n'
                 '    return 0;\n}\n')
        text = text.replace('INT MBSS_Close(PNET_DEV pDev)',
                            abort+'INT MBSS_Close(PNET_DEV pDev)', 1)
        prepared['ap/ap_mbss.c'] = text
        checked = compose(prepared, Path(directory), here)['ap/ap_mbss.c']
        opening = checked.split('INT32 MBSS_Open(PNET_DEV pDev)', 1)[1].split('INT MBSS_AbortOpen', 1)[0]
        assert opening.index('wr_iot_ra2_software_open') < opening.index('RTMP_SEM_LOCK')
        abort = checked.split('INT MBSS_AbortOpen', 1)[1].split('INT MBSS_Close', 1)[0]
        assert abort.index('wr_iot_ra2_software_stop') < abort.index('wr_iot_bcn_revoke_and_drain')
        try:
            compose(sources, Path(directory), here)
        except ValueError:
            pass
        else:
            raise AssertionError('Repeated software OFF preparation accepted')
else:
    sources = {name: (args.driver / name).read_text() for name in names}
    assert (args.driver / 'include/ra2-software-off.h').read_bytes() == (here / 'ra2-software-off.h').read_bytes()
expected_stops = 2 if 'INT MBSS_AbortOpen(PNET_DEV pDev)' in sources['ap/ap_mbss.c'] else 1
assert sources['ap/ap_mbss.c'].count('wr_iot_ra2_software_stop(pAd,pDev)') == expected_stops
assert sources['ap/ap_mbss.c'].count('wr_iot_ra2_software_open(pAd,pDev)') == 1
opening = sources['ap/ap_mbss.c'].split('INT32 MBSS_Open(PNET_DEV pDev)', 1)[1].split('INT MBSS_Close(PNET_DEV pDev)', 1)[0]
if 'RTMP_SEM_LOCK(&pAd->BcnRingLock);' in opening:
    assert opening.index('wr_iot_ra2_software_open') < opening.index('RTMP_SEM_LOCK(&pAd->BcnRingLock);')
text = sources['ap/ap_data.c']
begin = text.index('\tif (IS_MT7603(pAd) && pAd->ApCfg.BssidNum == 3 &&')
end = text.index('\tRTMP_QueryPacketInfo(', begin)
admission = text[begin:end]
prefix = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define TRUE 1
#define WRITE_ONCE(field,value) ((field)=(value))
#define FALSE 0
#define MAX_LEN_OF_TR_TABLE 256
#define WCID_ALL 255
typedef unsigned char UCHAR;
#define ENTRY_CAT_MCAST 2
#define IS_MT7603(ad) ((ad)->mt)
#define IS_ENTRY_NONE(tr) ((tr)->EntryType==0)
typedef unsigned long ULONG;
typedef int *PNET_DEV;
struct wifi_dev {PNET_DEV if_dev;unsigned int tr_tb_idx;};
typedef struct {
 unsigned int wcid,func_tb_idx;
 struct wifi_dev *wdev;
 int EntryType,enq_cap,deq_cap,PsDeQWaitCnt,PsQIdleCount,queued;
} STA_TR_ENTRY;
typedef struct {
 int mt,MacTabLock,irq_lock,BcnRingLock;
 struct {unsigned int BssidNum;struct {struct wifi_dev wdev;
  struct {int bBcnSntReq;} bcn_buf;} MBSSID[3];} ApCfg;
 struct {STA_TR_ENTRY tr_entry[MAX_LEN_OF_TR_TABLE];} MacTab;
} RTMP_ADAPTER;
static unsigned int flushes;
#ifdef WR_IOT_PSM_DIAG
#define KERN_INFO ""
static unsigned int logs;
static void printk_ratelimited(const char *message)
{
 assert(strstr(message,"ra2 software-off queues-gated"));
 logs++;
}
#endif
static void NdisAcquireSpinLock(int *lock){assert(!*lock);*lock=1;}
static void NdisReleaseSpinLock(int *lock){assert(*lock);*lock=0;}
#define RTMP_SEM_LOCK(lock) do{assert(!ad->MacTabLock&&!ad->irq_lock);NdisAcquireSpinLock(lock);}while(0)
#define RTMP_SEM_UNLOCK(lock) NdisReleaseSpinLock(lock)
#define RTMP_IRQ_LOCK(lock,flags) do{(flags)=0;assert(ad->MacTabLock);NdisAcquireSpinLock(lock);}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do{(void)(flags);NdisReleaseSpinLock(lock);}while(0)
static void rtmp_tx_swq_exit(RTMP_ADAPTER *ad,unsigned int wcid)
{
 assert(ad->MacTabLock && !ad->irq_lock && wcid==5);
 ad->MacTab.tr_entry[wcid].queued=0;
 flushes++;
}
'''
main = r'''
int main(void)
{
 for(unsigned int fault=0;fault<9;fault++){
  int device[3]={0};
  RTMP_ADAPTER ad={.mt=1,.ApCfg.BssidNum=3};
  for(unsigned int bss=0;bss<3;bss++){
   ad.ApCfg.MBSSID[bss].wdev.if_dev=&device[bss];
   ad.ApCfg.MBSSID[bss].bcn_buf.bBcnSntReq=1;
  }
  ad.ApCfg.MBSSID[2].wdev.tr_tb_idx=5;
  for(unsigned int i=0;i<6;i++){
   unsigned int bss=i<3?i:2;
   ad.MacTab.tr_entry[i]=(STA_TR_ENTRY){.wcid=i,.func_tb_idx=bss,
    .wdev=&ad.ApCfg.MBSSID[bss].wdev,.EntryType=(i==5?2:1),.enq_cap=1,.deq_cap=1,
    .PsDeQWaitCnt=2,.PsQIdleCount=3,.queued=2};
  }
  /* Foreign and mismatched slots cannot be gated by the ra2 sweep. */
  ad.MacTab.tr_entry[2].func_tb_idx=1;
  ad.MacTab.tr_entry[2].wdev=&ad.ApCfg.MBSSID[1].wdev;
  ad.MacTab.tr_entry[4].wcid=99;
  if(fault==1)ad.mt=0;
  if(fault==2)ad.ApCfg.BssidNum=2;
  if(fault==3)ad.ApCfg.MBSSID[2].wdev.if_dev=NULL;
  if(fault==4)ad.MacTab.tr_entry[5].EntryType=0;
  if(fault==5)ad.MacTab.tr_entry[5].wdev=&ad.ApCfg.MBSSID[1].wdev;
  if(fault==6)ad.ApCfg.MBSSID[2].wdev.tr_tb_idx=MAX_LEN_OF_TR_TABLE;
  if(fault==7)ad.MacTab.tr_entry[5].EntryType=1;
  if(fault==8){
   ad.ApCfg.MBSSID[2].wdev.tr_tb_idx=WCID_ALL;
   ad.MacTab.tr_entry[WCID_ALL]=(STA_TR_ENTRY){.EntryType=ENTRY_CAT_MCAST,
    .wcid=WCID_ALL,.func_tb_idx=2,.wdev=&ad.ApCfg.MBSSID[2].wdev};
  }
  flushes=0;
#ifdef WR_IOT_PSM_DIAG
  logs=0;
#endif
  assert(!wr_iot_ra2_software_stop(NULL,&device[2]));
  assert(!wr_iot_ra2_software_stop(&ad,NULL));
  assert(!wr_iot_ra2_software_open(NULL,&device[2]));
  assert(!wr_iot_ra2_software_stop(&ad,&device[1]));
  int stopped=wr_iot_ra2_software_stop(&ad,&device[2]);
  int expected=0;
  if(fault==0)expected=1;
  else if(fault>=4)expected=-1;
  assert(stopped==expected);
  assert(!ad.MacTabLock && !ad.irq_lock && !ad.BcnRingLock);
#ifdef WR_IOT_PSM_DIAG
  assert(logs==(unsigned)(stopped!=0));
#endif
  assert(ad.MacTab.tr_entry[0].enq_cap && ad.MacTab.tr_entry[1].enq_cap);
  assert(ad.MacTab.tr_entry[2].enq_cap && ad.MacTab.tr_entry[4].enq_cap);
  if(!stopped){assert(!flushes);continue;}
  assert(!ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq);
  assert(!ad.MacTab.tr_entry[3].enq_cap && !ad.MacTab.tr_entry[3].deq_cap);
  assert(!ad.MacTab.tr_entry[3].PsDeQWaitCnt);
  /* Owned unicast packets await the existing vendor station destructor. */
  assert(ad.MacTab.tr_entry[3].queued==2);
  assert(!data_allowed(&ad,&ad.ApCfg.MBSSID[2].wdev));
  assert(data_allowed(&ad,&ad.ApCfg.MBSSID[0].wdev));
  assert(data_allowed(&ad,&ad.ApCfg.MBSSID[1].wdev));
  assert(flushes==(fault==0));
  assert(wr_iot_ra2_software_open(&ad,&device[2])==(fault==0));
  if(!fault){
   assert(ad.MacTab.tr_entry[5].enq_cap && ad.MacTab.tr_entry[5].deq_cap);
   /* OPEN restores capabilities while data admission stays closed until
    * the vendor path publishes its ordinary beacon-enable state. */
   assert(!data_allowed(&ad,&ad.ApCfg.MBSSID[2].wdev));
   ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=1;
   assert(data_allowed(&ad,&ad.ApCfg.MBSSID[2].wdev));
   assert(wr_iot_ra2_software_stop(&ad,&device[2]) && flushes==2);
  }
 }
 puts("PASS scoped ra2 software stop/open: current WCID/wdev gates, owned multicast drain, Main/Guest preservation, invalid table refusal and admission ordering; locks/queue release injected, DMA/runtime pending");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ra2-software-off-check-') as directory:
    root = Path(directory)
    code = prefix + (here / 'ra2-software-off.h').read_text()
    code += '\nstatic int data_allowed(RTMP_ADAPTER *pAd,struct wifi_dev *wdev)\n{\n'
    code += admission + '\n\treturn 1;\n}\n' + main
    source, binary = root / 'check.c', root / 'check'
    source.write_text(code)
    (root / 'linux').mkdir()
    (root / 'linux/ratelimit.h').write_text('/* printk rate limiter injected */\n')
    for mode in ('off', 'on'):
        command = ['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                   '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                   '-I'+str(root), str(source), '-o', str(binary)]
        if mode == 'on':
            command.append('-DWR_IOT_PSM_DIAG')
        subprocess.run(command, check=True)
        subprocess.run([str(binary)], check=True)
