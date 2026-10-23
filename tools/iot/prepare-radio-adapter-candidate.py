#!/usr/bin/env python3
"""Stage pinned adapter-owned transition storage/lock; not a driver installer."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args();root=a.source.resolve();out=a.output.resolve()
if out.exists() or out==root or root in out.parents or out in root.parents:
    raise SystemExit('New output separate from source required')
blobs={'include/rtmp.h':'f773e57abba168b39893c8e0c78952e2d198c9e5',
       'common/rtmp_init.c':'a0d9eb2adbbb2ac13e8314806a5ded2f30793623',
       'os/linux/rt_main_dev.c':'72c71a23ce3f64ded365482b631aacc8e7115ffe',
       'os/linux/rt_profile.c':'ac18439ec4611ed89543b957517a81b2ff2b5707'}
originals={};texts={}
for name,blob in blobs.items():
    data=(root/name).read_bytes()
    if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=blob:
        raise SystemExit('Unreviewed adapter source: '+name)
    originals[name]=data;texts[name]=data.decode('utf-8')
def once(text,old,new):
    if text.count(old)!=1:raise SystemExit('Changed adapter insertion anchor')
    return text.replace(old,new,1)
texts['include/rtmp.h']=once(texts['include/rtmp.h'],'#define __RTMP_H__',
 '#define __RTMP_H__\n#include "radio-transition.h"\n#include "interface-registry.h"')
texts['include/rtmp.h']=once(texts['include/rtmp.h'],
 'VOID PDMAResetAndRecovery(RTMP_ADAPTER *pAd);',
 'VOID PDMAResetAndRecovery(RTMP_ADAPTER *pAd);\nVOID wr_iot_radio_reset_drain(RTMP_ADAPTER *pAd);\nINT wr_iot_command_task_exit_checked(RTMP_ADAPTER *pAd);\nINT wr_iot_mgmt_exit_checked(RTMP_ADAPTER *pAd, const struct wr_iot_radio_ticket *ticket);\nINT wr_iot_drv_close_checked(VOID *pAd, VOID *net_dev, const struct wr_iot_radio_ticket *ticket);\nINT wr_iot_rt28xx_close_checked(VOID *dev, const struct wr_iot_radio_ticket *ticket);\nINT wr_iot_virtual_down_checked(RTMP_ADAPTER *pAd, const struct wr_iot_radio_ticket *ticket);\nINT wr_iot_netdev_attach_checked(RTMP_ADAPTER *pAd, UCHAR mode, PNET_DEV dev, RTMP_OS_NETDEV_OP_HOOK *hook);')
fields='\tNDIS_SPIN_LOCK wr_iot_transition_lock;\n\tstruct wr_iot_radio_transition wr_iot_transition;\n\t/* wdev capacity plus dedicated monitor slot; registration lifetime. */\n\tstruct wr_iot_interface_ref wr_iot_interface_refs[WDEV_NUM_MAX + 1];\n\tunsigned long wr_iot_registration_generation;\n'
texts['include/rtmp.h']=once(texts['include/rtmp.h'],'\tUINT VirtualIfCnt;',
 '\tUINT VirtualIfCnt;\n'+fields)
init='\t\t/* Last nonfailing initialization before adapter publication. */\n\t\tNdisAllocateSpinLock(pAd, &pAd->wr_iot_transition_lock);\n\t\twr_iot_radio_transition_init(&pAd->wr_iot_transition);\n\t\tpAd->wr_iot_registration_generation = 0;\n\t\t{\n\t\t\tUINT wr_iot_slot;\n\t\t\tfor (wr_iot_slot = 0; wr_iot_slot < WDEV_NUM_MAX + 1; wr_iot_slot++)\n\t\t\t\twr_iot_ref_init(&pAd->wr_iot_interface_refs[wr_iot_slot], NULL, 0);\n\t\t}\n'
publication='\t\t*ppAdapter = (VOID *)pAd;'
text=texts['common/rtmp_init.c']
start=text.index('NDIS_STATUS RTMPAllocAdapterBlock(')
end=text.index('\n}',start)+2
function=text[start:end]
if function.count(publication)!=1:raise SystemExit('Changed adapter publication')
# This insertion is after every failing break in the allocation do/while.
publish=function.index(publication)
if 'break;' in function[publish:function.index('} while (FALSE);',publish)]:
    raise SystemExit('New failure after publication')
texts['common/rtmp_init.c']=once(text,publication,init+publication)
free='\t/* Entry quiescence and adapter references must already be retired.\n\t * This allocation candidate alone does not prove that precondition. */\n\tNdisFreeSpinLock(&pAd->wr_iot_transition_lock);\n'
texts['os/linux/rt_profile.c']=once(texts['os/linux/rt_profile.c'],
 '\tNdisFreeSpinLock(&pAd->MgmtRingLock);',
 free+'\tNdisFreeSpinLock(&pAd->MgmtRingLock);')
# Bind only main-down invalidation, before every existing main-close mutation.
name='os/linux/rt_main_dev.c'
text=texts[name];signature='int MainVirtualIF_close(IN struct net_device *net_dev)'
start=text.index(signature);end=text.index('\n}',start)+2
original_close=text[start:end]
anchor='\tif (pAd == NULL)\n\t\treturn 0;'
invalidate='\n\t{\n\t\tPRTMP_ADAPTER adapter = (PRTMP_ADAPTER)pAd;\n\t\tULONG flags;\n\t\tRTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);\n\t\twr_iot_radio_main_down(&adapter->wr_iot_transition);\n\t\tRTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);\n\t}\n'
close=once(original_close,anchor,anchor+invalidate)
texts[name]=text[:start]+close+text[end:]
fixture=r'''#include "radio-transition.h"
#include <assert.h>
#include <stdio.h>
typedef void VOID;
typedef unsigned long ULONG;
#define IN
struct adapter {int wr_iot_transition_lock;struct wr_iot_radio_transition wr_iot_transition;};
typedef struct adapter *PRTMP_ADAPTER;
struct net_device {PRTMP_ADAPTER priv;};
static int held,mutations;
#define RTMP_OS_NETDEV_GET_PRIV(dev) ((dev)->priv)
#define RTMP_IRQ_LOCK(lock,flags) ((flags)=0,assert(!held),held=1,(void)(lock))
#define RTMP_IRQ_UNLOCK(lock,flags) ((void)(flags),(void)(lock),assert(held),held=0)
static void mutate(struct net_device *dev){assert(!held&&!dev->priv->wr_iot_transition.main_ready);mutations++;}
#define RT_MOD_HNAT_DEREG(dev) mutate(dev)
#define netif_carrier_off(dev) mutate(dev)
#define netif_stop_queue(dev) mutate(dev)
#define RTMPInfClose(ad) assert(!held&&!((PRTMP_ADAPTER)(ad))->wr_iot_transition.main_ready)
#define VIRTUAL_IF_DOWN(ad) assert(!held&&!((PRTMP_ADAPTER)(ad))->wr_iot_transition.main_ready)
#define RT_MOD_DEC_USE_COUNT() ((void)0)
'''+close+r'''
int main(void){
 struct adapter a={0};struct net_device dev={&a};struct wr_iot_radio_ticket t;
 wr_iot_radio_transition_init(&a.wr_iot_transition);
 assert(wr_iot_radio_begin(&a.wr_iot_transition,a.wr_iot_transition.epoch,WR_RADIO_START,&t));
 assert(wr_iot_radio_finish(&a.wr_iot_transition,&t,1));
 assert(MainVirtualIF_close(&dev)==0&&!held&&mutations>=2);
 assert(a.wr_iot_transition.main_inhibited&&!a.wr_iot_transition.main_ready);
 assert(!wr_iot_radio_begin(&a.wr_iot_transition,a.wr_iot_transition.epoch,WR_RADIO_BSS_OPEN,&t));
 dev.priv=NULL;assert(MainVirtualIF_close(&dev)==0&&!held);
 puts("PASS actual main-close wrapper invalidates readiness before mutations, releases short lock, refuses BSS open; primitives injected");return 0;
}
'''
# Balance the main wrapper's module reference on every existing early failure.
text=texts[name];signature='int MainVirtualIF_open(struct net_device *net_dev)'
start=text.index(signature);end=text.index('\n}',start)+2
main_open=text[start:end]
main_open=once(main_open,'\tif (pAd == NULL)\n\t\treturn 0;',
 '\tif (pAd == NULL) {\n\t\tRT_MOD_DEC_USE_COUNT();\n\t\treturn -1;\n\t}')
main_open=once(main_open,'\tif (VIRTUAL_IF_UP(pAd) != 0)\n\t\treturn -1;',
 '\tif (VIRTUAL_IF_UP(pAd) != 0) {\n\t\tRT_MOD_DEC_USE_COUNT();\n\t\treturn -1;\n\t}')
# Reserve before AP_MAIN_OPEN; never keep the short lock over driver calls.
main_open=once(main_open,'\tVOID *pAd = NULL;',
 '\tVOID *pAd = NULL;\n\tPRTMP_ADAPTER adapter;\n\tstruct wr_iot_radio_ticket ticket;\n\tULONG flags;\n\tint admitted, operation;')
anchor='\tif (pAd == NULL) {\n\t\tRT_MOD_DEC_USE_COUNT();\n\t\treturn -1;\n\t}'
reservation='''
    adapter = (PRTMP_ADAPTER)pAd;
    RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
    operation = adapter->wr_iot_transition.phase == WR_RADIO_DOWN ? WR_RADIO_START : WR_RADIO_MAIN_OPEN;
    admitted = wr_iot_radio_begin(&adapter->wr_iot_transition,
        adapter->wr_iot_transition.epoch, operation, &ticket);
    RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
    if (!admitted) { RT_MOD_DEC_USE_COUNT(); return -1; }
'''
main_open=once(main_open,anchor,anchor+reservation)
anchor='\tif (VIRTUAL_IF_UP(pAd) != 0) {\n\t\tRT_MOD_DEC_USE_COUNT();'
main_open=once(main_open,anchor,
 '''\tif (VIRTUAL_IF_UP(pAd) != 0) {
        RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
        wr_iot_radio_finish(&adapter->wr_iot_transition, &ticket, 0);
        RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
\t\tRT_MOD_DEC_USE_COUNT();''')
anchor='\treturn 0;'
main_open=once(main_open,anchor,'''    RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
    wr_iot_radio_finish_unverified(&adapter->wr_iot_transition, &ticket);
    RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
'''+anchor)
texts[name]=text[:start]+main_open+text[end:]
open_fixture=r'''#include "radio-transition.h"
#include <assert.h>
#include <stdio.h>
typedef void VOID;
typedef unsigned long ULONG;
struct adapter {int wr_iot_transition_lock;struct wr_iot_radio_transition wr_iot_transition;};
typedef struct adapter *PRTMP_ADAPTER;
struct net_device {void *priv;};
static int refs,up_result,mutations,held;
static struct adapter adapter;
#define RTMP_IRQ_LOCK(lock,flags) ((flags)=0,(void)(lock),assert(!held),held=1)
#define RTMP_IRQ_UNLOCK(lock,flags) ((void)(flags),(void)(lock),assert(held),held=0)
#define NDIS_STATUS_SUCCESS 0
#define RT_MOD_INC_USE_COUNT() (++refs)
#define RT_MOD_DEC_USE_COUNT() (--refs)
#define GET_PAD_FROM_NET_DEV(ad,dev) ((ad)=(dev)->priv)
#define RTMP_DRIVER_AP_MAIN_OPEN(ad) ((void)(ad),assert(!held&&((PRTMP_ADAPTER)(ad))->wr_iot_transition.busy),mutations++)
#define VIRTUAL_IF_UP(ad) ((void)(ad),up_result)
#define RT_MOD_HNAT_REG(dev) ((void)(dev),mutations++)
#define RTMP_DRIVER_IOCTL_SANITY_CHECK(ad,arg) ((void)(ad),(void)(arg),0)
#define OS_WAIT(ms) ((void)(ms))
#define DBGPRINT(level,args) ((void)0)
#define netif_start_queue(dev) ((void)(dev),mutations++)
#define netif_carrier_on(dev) ((void)(dev),mutations++)
#define netif_wake_queue(dev) ((void)(dev),mutations++)
'''+main_open+r'''
int main(void){
 struct net_device dev={NULL};
 assert(MainVirtualIF_open(&dev)==-1&&!refs&&!mutations);
 dev.priv=&adapter;wr_iot_radio_transition_init(&adapter.wr_iot_transition);
 adapter.wr_iot_transition.phase=WR_RADIO_CLOSING;
 assert(MainVirtualIF_open(&dev)==-1&&!refs&&!mutations&&!held);
 wr_iot_radio_transition_init(&adapter.wr_iot_transition);
#ifndef IFUP_IN_PROBE
 up_result=-1;assert(MainVirtualIF_open(&dev)==-1&&!refs&&!held);
 assert(!adapter.wr_iot_transition.busy&&adapter.wr_iot_transition.phase==WR_RADIO_FAULT);
 wr_iot_radio_transition_init(&adapter.wr_iot_transition);
#endif
 mutations=0;up_result=0;
 assert(MainVirtualIF_open(&dev)==0&&refs==1&&mutations>=3);
 assert(!held&&!adapter.wr_iot_transition.busy&&!adapter.wr_iot_transition.main_ready);
 assert(adapter.wr_iot_transition.phase==WR_RADIO_UNVERIFIED);
 RT_MOD_DEC_USE_COUNT();assert(!refs);
 puts("PASS actual main-open reference balance on NULL, virtual-up failure and success; primitives injected");return 0;
}
'''
# Separate result-returning bridge; legacy rt28xx_close is not redirected yet.
name='os/linux/rt_main_dev.c'
text=texts[name]; signature='int rt28xx_close(VOID *dev)'
start=text.index(signature);end=text.index('\n}',start)+2
texts[name]=text[:end]+'\n#include "wr-iot-physical-close-result.inc"\n'+text[end:]
# Publish removal intent before any child-interface unregister. This is an
# admission barrier only; destructor quiescence is still a separate obligation.
name='os/linux/rt_main_dev.c'
text=texts[name]; signature='BOOLEAN RtmpPhyNetDevExit(VOID *pAd, PNET_DEV net_dev)'
start=text.index(signature); end=text.index('\n}',start)+2
exit_function=text[start:end]
opening=signature+'\n{'
retire='\n\tif (pAd != NULL) {\n\t\tPRTMP_ADAPTER adapter = (PRTMP_ADAPTER)pAd;\n\t\tULONG flags;\n\t\tRTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);\n\t\twr_iot_radio_retire(&adapter->wr_iot_transition);\n\t\tRTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);\n\t}\n'
exit_function=once(exit_function,opening,opening+retire)
texts[name]=text[:start]+exit_function+text[end:]
# Optional monitor shares the same counter; balance failed UP without erasing
# the adapter-lock retirement edits already staged in rt_profile.c.
name='os/linux/rt_profile.c'
text=texts[name]; signature='INT Monitor_VirtualIF_Open(PNET_DEV dev_p)'
start=text.index(signature); end=text.index('\n}',start)+2
monitor_open=text[start:end]
monitor_open=once(monitor_open,
 '\tif (VIRTUAL_IF_UP(pAd) != 0)\n\t\treturn -1;',
 '\tif (VIRTUAL_IF_UP(pAd) != 0) {\n\t\tRT_MOD_DEC_USE_COUNT();\n\t\treturn -1;\n\t}')
texts[name]=text[:start]+monitor_open+text[end:]
for name,data in originals.items():
    if (root/name).read_bytes()!=data:raise SystemExit('Source changed')
out.mkdir()
for name,text in texts.items():
    target=out/name;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(text,encoding='utf-8')
header=Path(__file__).with_name('radio-transition.h').read_bytes()
(out/'include/radio-transition.h').write_bytes(header)
(out/'include/interface-reference.h').write_bytes(Path(__file__).with_name('interface-reference.h').read_bytes())
(out/'include/interface-registry.h').write_bytes(Path(__file__).with_name('interface-registry.h').read_bytes())
(out/'include/wr-iot-physical-close-result.inc').write_bytes(Path(__file__).with_name('physical-close-result.inc').read_bytes())
(out/'include/mt7603-main-observe.h').write_bytes(Path(__file__).with_name('mt7603-main-observe.h').read_bytes())
(out/'adapter-init.inc').write_text(init,encoding='utf-8')
(out/'adapter-free.inc').write_text(free,encoding='utf-8')
(out/'check-main-close.c').write_text(fixture,encoding='utf-8')
(out/'check-main-open.c').write_text(open_fixture,encoding='utf-8')
(out/'manifest.json').write_text(json.dumps({
 'source_revision':'c25283e915a2a00a763774dd255b14aff997285e',
 'source_blobs':blobs,'production_installed':False,'entrypoints_bound':False,'main_close_invalidation_staged':True,
 'phy_exit_retirement_intent_staged':True,'monitor_open_reference_repair_staged':True,'main_open_reference_repair_staged':True,'main_open_admission_staged':True,
 'interface_reference_storage_staged':True,'interface_reference_mapping_bound':False,'adapter_retirement_proven':False,'target_compiled':False,
 'overlap_review_required':['common/rtmp_init.c','include/rtmp.h'],
 'header_sha256':hashlib.sha256(header).hexdigest(),
 'files':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in texts}
},indent=2)+'\n',encoding='utf-8')
print('Prepared adapter-owned transition state/lock; entry and retirement bindings pending')
