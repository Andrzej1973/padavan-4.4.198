#!/usr/bin/env python3
"""Exercise actual direct-free entry before cookie/free with cold/live owners."""
import argparse,re,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
init=(a.candidate/'common/rtmp_init.c').read_text()
positions=[init.index(t) for t in ['pAd->wr_iot_recovery_storage_live=0;','NdisAllocateSpinLock(pAd, &pAd->wr_iot_transition_lock);','wr_iot_mbss_recovery_init(&pAd->wr_iot_mbss_recovery[wr_iot_slot]);','WRITE_ONCE(pAd->wr_iot_recovery_storage_live,1);','*ppAdapter = (VOID *)pAd;']]
assert positions==sorted(positions)
exit_body=init[init.index('BOOLEAN RtmpRaDevCtrlExit(IN VOID *pAdSrc)'):]
assert exit_body.index('wr_iot_raw_recovery_free_fence(pAd)')<exit_body.index('wr_iot_mcu_sender_release_begin(pAd)')<exit_body.index('wr_iot_adapter_release_begin(pAd)')

source=(a.candidate/'os/linux/rt_profile.c').read_text();start=source.index('BOOLEAN RTMPFreeAdapter(VOID *pAdSrc)');end=source.index('os_cookie=(POS_COOKIE)pAd->OS_Cookie;',start)+len('os_cookie=(POS_COOKIE)pAd->OS_Cookie;')
entry=source[start:end];assert entry.index('wr_iot_raw_recovery_free_fence(pAd)')<entry.index('wr_iot_mcu_sender_release_begin(pAd)')<entry.index('pAd->OS_Cookie')
entry,n=re.subn(r'\tint index;\s*\n','',entry,count=1);assert n==1
code=r'''
#include "wr-iot-main-reopen-admission.h"
#include "mbss-recovery-storage.h"
#include <assert.h>
#define WDEV_NUM_MAX 1
#define TRUE 1
#define FALSE 0
#define READ_ONCE(x) (x)
#define NDIS_STATUS_SUCCESS 0
typedef int BOOLEAN;typedef unsigned long ULONG;typedef unsigned int UINT;
typedef void VOID;typedef void *POS_COOKIE;
struct work_struct {unsigned int busy;};
typedef struct {
 unsigned int wr_iot_recovery_storage_live,wr_iot_registration_inflight;
 void *OS_Cookie;int wr_iot_transition_lock;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_main_recovery_owner wr_iot_main_recovery;
 struct wr_iot_mbss_recovery_owner wr_iot_mbss_recovery[2];
 struct wr_iot_interface_ref wr_iot_interface_refs[2];
 struct work_struct wr_iot_main_recovery_work,wr_iot_aux_family_retry_work;
 struct {struct work_struct work;} wr_iot_main_recovery_reap_work;
 struct {unsigned int deferred_owners;} wr_iot_aux_family_retry;
} RTMP_ADAPTER,*PRTMP_ADAPTER;
static int held,locks,destructive_steps,sender_steps,sender_result;
static RTMP_ADAPTER *current;
static int wr_iot_mcu_sender_release_begin(RTMP_ADAPTER *ad){assert(ad);sender_steps++;return sender_result;}
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held&&current->wr_iot_recovery_storage_live);held=1;locks++;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
static unsigned int work_busy(struct work_struct *w){assert(held&&current->wr_iot_recovery_storage_live);return w->busy;}
#include "wr-iot-raw-recovery-free-fence.inc"
'''+entry+r'''
 (void)os_cookie;destructive_steps++;return TRUE;
}
static void ready(RTMP_ADAPTER *ad,int live){
 *ad=(RTMP_ADAPTER){0};ad->wr_iot_recovery_storage_live=live;current=ad;
 wr_iot_radio_transition_init(&ad->wr_iot_transition);
 wr_iot_main_recovery_init(&ad->wr_iot_main_recovery);
 for(unsigned int i=0;i<2;i++){
  wr_iot_mbss_recovery_init(&ad->wr_iot_mbss_recovery[i]);
  wr_iot_ref_init(&ad->wr_iot_interface_refs[i],0,0);
 }
 held=locks=destructive_steps=sender_steps=sender_result=0;
}
static void refused(RTMP_ADAPTER *ad){assert(!RTMPFreeAdapter(ad)&&!held&&locks==1&&!destructive_steps&&!sender_steps&&ad->wr_iot_transition.retiring);}
int main(void){RTMP_ADAPTER ad;
 assert(!RTMPFreeAdapter(0));
 ready(&ad,0);ad.wr_iot_main_recovery_work.busy=2;
 assert(RTMPFreeAdapter(&ad)&&!locks&&destructive_steps==1);
 ready(&ad,1);assert(RTMPFreeAdapter(&ad)&&locks==1&&destructive_steps==1&&ad.wr_iot_transition.retiring);
 ready(&ad,1);sender_result=-1;assert(!RTMPFreeAdapter(&ad)&&sender_steps==1&&!destructive_steps);
 ready(&ad,1);ad.wr_iot_mbss_recovery[1].deferred_owners=1;refused(&ad);
 ready(&ad,1);ad.wr_iot_mbss_recovery[1].phase=WR_MBSS_OWNER_RETAINED;refused(&ad);
 ready(&ad,1);ad.wr_iot_main_recovery.deferred_owners=1;refused(&ad);
 ready(&ad,1);ad.wr_iot_main_recovery_reap_work.work.busy=2;refused(&ad);
 ready(&ad,1);ad.wr_iot_aux_family_retry.deferred_owners=1;refused(&ad);
 ready(&ad,1);ad.wr_iot_aux_family_retry_work.busy=1;refused(&ad);
 ready(&ad,1);ad.wr_iot_registration_inflight=1;refused(&ad);
 ready(&ad,1);ad.wr_iot_interface_refs[0].published=1;refused(&ad);
 ready(&ad,1);ad.wr_iot_interface_refs[0].device=&ad;refused(&ad);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-raw-recovery-fence-') as d:
 c=Path(d)/'check.c';c.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),'-I'+str(here),str(c),'-o',d+'/check'],check=True);subprocess.run([d+'/check'],check=True)
print('PASS direct-free prefix: cold recovery-lock bypass, live owner/work/reference refusal before sender release or destruction')
