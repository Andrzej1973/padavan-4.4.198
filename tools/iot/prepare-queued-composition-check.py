#!/usr/bin/env python3
"""Compose staged actual enqueue with producer/worker; OS primitives injected."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('enqueue_candidate',type=Path)
p.add_argument('output',type=Path)
p.add_argument('--cleanup-candidate',type=Path)
a=p.parse_args()
if a.output.exists():raise SystemExit('Refusing overwrite')
here=Path(__file__).parent
result=(here/'check-queued-result.c').read_text()
anchor='#include "queued-result.h"'
if result.count(anchor)!=1:raise SystemExit('Changed result fixture prefix')
primitives=result[:result.index(anchor)]
enqueue=(a.enqueue_candidate/'checked-enqueue.inc').read_text()
if enqueue.count('static NDIS_STATUS wr_enqueue_internal_cmd(')!=1:
    raise SystemExit('Changed shared enqueue fixture')
prefix=(here/'check-checked-enqueue-prefix.inc').read_text()
hook='''
#include "queued-work.h"
static void composition_wake(int *task);
#undef RTCMDUp
#define RTCMDUp composition_wake
'''
tail=(here/'check-queued-composition-tail.inc').read_text()
if a.cleanup_candidate:
    dispatch=(a.cleanup_candidate/'common/rtmp_init.c').read_text()
    shutdown=(a.cleanup_candidate/'os/linux/rt_rbus_pci_drv.c').read_text()
    start=dispatch.index('VOID CMDHandler(')
    gate=dispatch.index('\t\tif(!(RTMP_TEST_FLAG',start)
    gate_end=dispatch.index('\n\t\t{',gate)
    condition=dispatch[gate:gate_end]
    start=dispatch.index('\t\twr_iot_queue_cleanup(cmdqelmt);',start)
    end=dispatch.index('\n\t}\n}',start)
    release=dispatch[start:end]
    start=shutdown.index('INT RTPCICmdThread(')
    start=shutdown.index('\t\t\tif (pCmdQElmt)',start)
    end=shutdown.index('\n\t\t}\n\n\t\tNdisReleaseSpinLock',start)
    pending=shutdown[start:end]
    if release.count('wr_iot_queue_cleanup(')!=1 or pending.count('wr_iot_queue_cleanup(')!=1:
        raise SystemExit('Changed cleanup slices')
    slices='''
#define fRTMP_ADAPTER_HALT_IN_PROGRESS 2
static void actual_dispatch_slice(PRTMP_ADAPTER pAd,PCmdQElmt cmdqelmt,
 int (*execute)(PRTMP_ADAPTER)) {
'''+condition+''' {
 wr_iot_queue_dispatch(pAd,cmdqelmt,execute);
 }
'''+release+'''
}
static void actual_shutdown_slice(PRTMP_ADAPTER pAd,PCmdQElmt pCmdQElmt) {
'''+pending+'''
}
'''
    anchor='static void consume(void){'
    start=tail.index(anchor);end=tail.index('\n}',start)+2
    tail=tail[:start]+slices+'''static void consume(void){
 PCmdQElmt cmd=owned;assert(cmd&&!held);
 if(mode==8)current_ad->flags=fRTMP_ADAPTER_HALT_IN_PROGRESS;
 if(mode==11)current_ad->flags=fRTMP_ADAPTER_NIC_NOT_EXIST;
 if(mode==12){held=1;actual_shutdown_slice(current_ad,cmd);held=0;}
 else actual_dispatch_slice(current_ad,cmd,mode==5?NULL:operation);
 owned=NULL;
}'''+tail[end:]
    tail=tail.replace('mode<=10','mode<=12').replace('mode==6||mode==8','mode==6||mode==8||mode==11||mode==12')
    tail=tail.replace('OS primitives injected','actual HALT/NIC guard and cleanup slices, OS primitives injected')
a.output.write_text(primitives+'\n'+prefix+'\n'+hook+enqueue+'\n'+tail,encoding='utf-8')
