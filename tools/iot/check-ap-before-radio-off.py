#!/usr/bin/env python3
"""Exercise extracted AP cleanup entries with host stubs; not target proof."""
from pathlib import Path
import subprocess, argparse, tempfile
p=argparse.ArgumentParser();p.add_argument("candidate",type=Path);a=p.parse_args()
workspace=tempfile.TemporaryDirectory(prefix="wr-ap-before-off-")
root=Path(workspace.name)
s=(a.candidate/'ap/ap.c').read_text()
def fn(sig):
 i=s.index(sig);return s[i:s.index('\n}',i)+2]
fns='\n'.join(fn(x) for x in ['static BOOLEAN wr_iot_ap_stop_body(RTMP_ADAPTER *pAd, BOOLEAN hardware)\n{','static BOOLEAN wr_iot_ap_shutdown_body(','BOOLEAN APStop(','BOOLEAN APShutdown(','BOOLEAN wr_iot_ap_shutdown_before_radio_off('])
prefix=r'''
#include <assert.h>
typedef int BOOLEAN;typedef int INT;
#define TRUE 1
#define FALSE 0
#define DBGPRINT(a,b) ((void)0)
#define fRTMP_ADAPTER_HALT_IN_PROGRESS 1
#define fRTMP_ADAPTER_NIC_NOT_EXIST 2
#define fOP_AP_STATUS_MEDIA_STATE_CONNECTED 1
#define NdisMediaStateDisconnected 0
#define ALLN_SETPROTECT 1
#define CCKSETPROTECT 2
#define OFDMSETPROTECT 4
#define BCN_TX_IDLE 0
#define MAX_MBSSID_NUM(a) 1
typedef struct {int REKEYTimerRunning,REKEYTimer;struct {int bcn_state;} bcn_buf;} BSS_STRUCT;
typedef struct {struct {BSS_STRUCT MBSSID[1];int CMTimerRunning,CounterMeasureTimer,BANClass3Data;} ApCfg;} RTMP_ADAPTER;
static int radios,irqs,resets,fail;
#define RTMP_ASIC_INTERRUPT_DISABLE(a) do{(void)(a);irqs++;}while(0)
#define RTMP_SET_FLAG(a,f) ((void)(a),(void)(f))
#define RTMP_TEST_FLAG(a,f) ((void)(a),(void)(f),0)
#define OPSTATUS_CLEAR_FLAG(a,f) ((void)(a),(void)(f))
static void MlmeRadioOff(RTMP_ADAPTER *a){(void)a;radios++;}
static int MacTableReset(RTMP_ADAPTER *a,int x){(void)a;(void)x;resets++;return !fail;}
#define AsicSetPreTbtt(a,b) ((void)(a),(void)(b))
#define RTMPSetPiggyBack(a,b) ((void)(a),(void)(b))
#define AsicUpdateProtect(a,b,c,d,e) ((void)(a),(void)(b),(void)(c),(void)(d),(void)(e))
#define AsicDisableSync(a) ((void)(a))
#define RTMPCancelTimer(a,b) do{(void)(a);*(b)=1;}while(0)
#define RTMP_IndicateMediaState(a,b) ((void)(a),(void)(b))
'''
tail=r'''
int main(void){RTMP_ADAPTER a={0};
assert(APStop(&a));assert(resets==1);
radios=irqs=resets=0;assert(APShutdown(&a));assert(radios==1);
#ifdef RTMP_MAC_PCI
assert(resets==1);
#ifdef CONFIG_MAC_PCI
assert(irqs==1);
#endif
#endif
radios=irqs=resets=0;assert(wr_iot_ap_shutdown_before_radio_off(&a));assert(!radios&&!irqs);
#ifdef RTMP_MAC_PCI
assert(resets==1);fail=1;assert(!wr_iot_ap_shutdown_before_radio_off(&a));assert(!APShutdown(&a));
#endif
return 0;}
'''
for pci in [False,True]:
 for irq in [False,True]:
  p=(root/'check.c');p.write_text(prefix+fns+tail)
  cmd=['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined']
  if pci:cmd+=['-DRTMP_MAC_PCI']
  if irq:cmd+=['-DCONFIG_MAC_PCI']
  subprocess.run(cmd+[str(p),'-o',str(p.with_suffix(''))],check=True)
  subprocess.run([str(p.with_suffix(''))],check=True)
print('PASS four PCI guards: extracted legacy/new AP entry behavior and cleanup refusal')

workspace.cleanup()
