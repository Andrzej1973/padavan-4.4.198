#!/usr/bin/env python3
"""Execute generated MLME join admission and shutdown failure propagation."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
s=(a.candidate/'common/mlme.c').read_text();start=s.index('static BOOLEAN wr_iot_mlme_halt_body(')
end=s.index('#if (defined(MT_WOW_SUPPORT)',start)
# Cancelled belongs to the later timer cleanup, excluded from this join fixture.
prefix=s[start:end].replace('\tBOOLEAN Cancelled;','',1)+' cleanups++;return TRUE;\n}\n'
wstart=s.index('VOID MlmeHalt(RTMP_ADAPTER *pAd)',end);wend=s.index('\n}',s.index('BOOLEAN wr_iot_mlme_halt_checked(',wstart))+2
wrappers=s[wstart:wend]
caller=(a.candidate/'common/rtmp_init_inf.c').read_text();start=caller.index(' if (!wr_iot_mlme_halt_checked(pAd)) {');end=caller.index('\n }',start)+3
block=caller[start:end]
has_timer_join='wr_iot_timer_join_checked(' in wrappers
code=r'''
#include <assert.h>
#define VOID void
#define BOOLEAN int
#define TRUE 1
#define FALSE 0
#define NDIS_STATUS_FAILURE -1
#define RT_DEBUG_TRACE 0
#define RT_DEBUG_ERROR 0
#define DBGPRINT(a,b) ((void)0)
#define IF_DEV_CONFIG_OPMODE_ON_AP(ad) if ((ad)!=0)
typedef struct {int handle;} RTMP_OS_TASK;
typedef struct {int id;} RALINK_TIMER_STRUCT;
#define MAX_APCLI_NUM 2
typedef struct {struct {RALINK_TIMER_STRUCT PeriodicTimer,RxAntEvalTimer,APSDPeriodicTimer;} Mlme;struct {RALINK_TIMER_STRUCT ApQuickResponeForRateUpTimer;struct {struct {RALINK_TIMER_STRUCT ProbeTimer,ApCliAssocTimer,ApCliAuthTimer;} MlmeAux;struct {RALINK_TIMER_STRUCT WscProfileRetryTimer;} WscControl;} ApCliTab[MAX_APCLI_NUM];} ApCfg;struct {RALINK_TIMER_STRUCT APScanTimer;} ScanCtrl;RTMP_OS_TASK mlmeTask;int wr_iot_transition_lock;struct {unsigned int shutdown_stage;} wr_iot_transition;} RTMP_ADAPTER;
static int kill_result,kill_calls,context_bad,identity,cleanups,held;
static int RtmpOSTaskKill(RTMP_OS_TASK *t){assert(t&&!held);kill_calls++;return kill_result;}
static int wr_iot_os_join_context(void){return context_bad;}
static int wr_iot_os_timer_task_current(RTMP_OS_TASK *t){assert(t);return identity;}
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
'''
if has_timer_join:
 code+=r'''
static int timer_calls,timer_fail;
#ifdef CONFIG_AP_SUPPORT
#ifdef APCLI_SUPPORT
#ifdef WSC_AP_SUPPORT
#define JOIN_APCLI_WIDTH 4
#else
#define JOIN_APCLI_WIDTH 3
#endif
#define JOIN_APCLI (JOIN_APCLI_WIDTH*MAX_APCLI_NUM)
#else
#define JOIN_APCLI 0
#endif
#ifdef AP_SCAN_SUPPORT
#define JOIN_SCAN 1
#else
#define JOIN_SCAN 0
#endif
#define JOIN_COUNT (4+JOIN_APCLI+JOIN_SCAN)
#else
#define JOIN_COUNT 2
#endif
static int wr_iot_timer_join_checked(RTMP_ADAPTER *ad,RALINK_TIMER_STRUCT *t,unsigned long timeout){
 assert(ad&&t&&!held&&timeout==5000);timer_calls++;
 RALINK_TIMER_STRUCT *expected[13]={&ad->Mlme.PeriodicTimer,&ad->Mlme.RxAntEvalTimer,&ad->Mlme.APSDPeriodicTimer,&ad->ApCfg.ApQuickResponeForRateUpTimer};
#if defined(CONFIG_AP_SUPPORT) && defined(APCLI_SUPPORT)
 for(unsigned int i=0;i<MAX_APCLI_NUM;i++){
  expected[4+JOIN_APCLI_WIDTH*i]=&ad->ApCfg.ApCliTab[i].MlmeAux.ProbeTimer;
  expected[5+JOIN_APCLI_WIDTH*i]=&ad->ApCfg.ApCliTab[i].MlmeAux.ApCliAssocTimer;
  expected[6+JOIN_APCLI_WIDTH*i]=&ad->ApCfg.ApCliTab[i].MlmeAux.ApCliAuthTimer;
#ifdef WSC_AP_SUPPORT
  expected[7+JOIN_APCLI_WIDTH*i]=&ad->ApCfg.ApCliTab[i].WscControl.WscProfileRetryTimer;
#endif
 }
#endif
#if defined(CONFIG_AP_SUPPORT) && defined(AP_SCAN_SUPPORT)
 expected[JOIN_COUNT-1]=&ad->ScanCtrl.APScanTimer;
#endif
 assert(t==expected[(timer_calls-1)%JOIN_COUNT]);
 return timer_fail!=timer_calls;
}
'''
code+=prefix+wrappers+r'''
static int close_stage(RTMP_ADAPTER *pAd){unsigned long flags;
'''+block+r'''
return 0;}
int main(void){RTMP_ADAPTER ad={0};
 kill_result=-1;assert(!wr_iot_mlme_halt_checked(&ad)&&kill_calls==1&&!cleanups);
 assert(close_stage(&ad)==-1&&ad.wr_iot_transition.shutdown_stage==3&&!cleanups&&!held);
 kill_result=0;assert(wr_iot_mlme_halt_checked(&ad)&&cleanups==1);
 int before=kill_calls;identity=1;assert(!wr_iot_mlme_halt_checked(&ad)&&kill_calls==before);
 identity=-1;assert(!wr_iot_mlme_halt_checked(&ad)&&kill_calls==before);
 identity=0;context_bad=1;assert(!wr_iot_mlme_halt_checked(&ad)&&kill_calls==before);
 context_bad=0;assert(!wr_iot_mlme_halt_checked(0)&&kill_calls==before);
 kill_result=-1;MlmeHalt(&ad);assert(cleanups==2);
 return 0;}
'''
if has_timer_join:
 code=code.replace(' return 0;}','''
 kill_result=0;int previous_kills=kill_calls;
 for(int fail=1;fail<=JOIN_COUNT;fail++){
  timer_calls=0;timer_fail=fail;assert(!wr_iot_mlme_halt_checked(&ad)&&timer_calls==fail&&kill_calls==previous_kills);
 }
 timer_calls=0;timer_fail=0;assert(wr_iot_mlme_halt_checked(&ad)&&timer_calls==JOIN_COUNT&&kill_calls==previous_kills+1);
 return 0;}''')
with tempfile.TemporaryDirectory(prefix='wr-mlme-halt-check-') as d:
 c=Path(d)/'check.c';c.write_text(code)
 for flags in ([[],['-DCONFIG_AP_SUPPORT'],['-DCONFIG_AP_SUPPORT','-DAPCLI_SUPPORT','-DAP_SCAN_SUPPORT'],['-DCONFIG_AP_SUPPORT','-DAPCLI_SUPPORT','-DAP_SCAN_SUPPORT','-DWSC_AP_SUPPORT']] if has_timer_join else [[]]):
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,str(c),'-o',d+'/check'],check=True)
  subprocess.run([d+'/check'],check=True)
print('PASS MLME checked join failure before cleanup, self/unknown/context refusal, shutdown stage retention and legacy entry')
