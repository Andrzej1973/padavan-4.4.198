#!/usr/bin/env python3
"""Bind the isolated APCLI/Monitor retry scheduler to a new candidate tree."""
import argparse
import hashlib
import re
import shutil
from pathlib import Path

import runpy
reviewed_predecessor=runpy.run_path(str(Path(__file__).with_name('reviewed-recovery-predecessor.py')))['reviewed_predecessor']

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
src=a.source.resolve(strict=True)
out=a.output.resolve()
here=Path(__file__).resolve().parent
if out.exists() or src==out or src in out.parents or out in src.parents:
 p.error('new separate output required')

pins={
 'os/linux/rt_rbus_pci_drv.c':'5cc40f6025acb085449199d32ee24cb6c8cc06249b184e0ad91ffce31c7275e3',
 'include/wr-iot-nettask-schedule.inc':'ea7f19155520b33b76f3d9ef15562b5a2692382aacc5592375648b96835f9e70',
 'common/cmm_mac_pci.c':'f013d5b5c91924564050db44198c70dc87ca5814502ee74601eb211dd95e3622',
 'common/rtmp_init_inf.c':'b0fac876abddfc5d9a10d9f19bb7cd419ca47ea20fc30778954bc2e629d45c3e',
 'hw_ctrl/cmm_asic_mt.c':'63680cb3fc61df6c67a39aa2ac9581afc3740fd6fadee2e9321610ad597603e1',
 'mcu/andes_mt.c':'e7e49e1b523461c89c8ed5dd4bc58f0a82e7a533fc9863eb632ea36a7b0dd0f8',
 'include/wr-iot-peer-open-client.inc':'bd352de23d2af6ece8d15cb1f9291586a3a01039f3f54f31a796313afc20be23',
 'os/linux/rt_main_dev.c':'7413803d8c757189d7280d55d25448aa178c9e1c53ae8f4e596092088037a8a2',
 'include/rtmp.h':'e253c027620c29ff69a5d14601633945097a85644cc32b416ab3a4c943167487',
 'common/rtmp_init.c':'c32609217ff1ce100b8b1ee21b1bec4f0e2bdb52303c2abd1f66264a2fd13018',
 'ap/ap_apcli_inf.c':'77ab94573ef99c3981fa34bc70f12725e3f866ad0b9c912d65dcb976a075aa66',
 'os/linux/rt_profile.c':'481163e79d1d21c2a9ce164e10ca0f07ef1d3271568828f38251acbc3ac5621b',
 'os/linux/pci_main_dev.c':'b0b38e403134f4ba2d02860efc1eb4f725b82515ab5a83d773d3214666885065',
 'include/wr-iot-peer-adapter-release.inc':'dec8a72a223aa37781f9ea82f9ee3f45f618d57b90bd793cd713940e1d975141',
 'include/wr-iot-aux-family-close-owned.inc':'83206308482680326e07ab6ac4e854b52f82dbd188c08224ff48a55c78b22912',
}
texts={}
for name,digest in pins.items():
 raw=(src/name).read_bytes()
 if hashlib.sha256(reviewed_predecessor(raw,name)).hexdigest()!=digest:
  p.error('unreviewed predecessor: '+name)
 texts[name]=raw.decode()

def one(name,old,new):
 if texts[name].count(old)!=1:p.error('changed anchor '+name+': '+old[:60])
 texts[name]=texts[name].replace(old,new,1)

def all_occurrences(name,old,new):
 count=texts[name].count(old)
 if not count:p.error('missing anchor '+name+': '+old[:60])
 texts[name]=texts[name].replace(old,new)

# Tasklet submissions include hard-IRQ callers. RTMP_IRQ_LOCK is only
# spin_lock_bh without MULTI_CORE_SUPPORT; every user of this shared lock
# must instead use the vendor IRQ-save primitive, including process context.
for name,locks,unlocks in [
 ('os/linux/rt_rbus_pci_drv.c',3,3),
 ('include/wr-iot-nettask-schedule.inc',6,7),
 ('include/wr-iot-peer-adapter-release.inc',1,1)]:
 for old,new,count in [('RTMP_IRQ_LOCK','RTMP_INT_LOCK',locks),
                       ('RTMP_IRQ_UNLOCK','RTMP_INT_UNLOCK',unlocks)]:
  anchor=old+'(&pAd->wr_iot_nettask_lock,'
  if texts[name].count(anchor)!=count:p.error('nettask lock inventory changed: '+name)
  texts[name]=texts[name].replace(anchor,new+'(&pAd->wr_iot_nettask_lock,')
 # RTMP_INT_LOCK passes the flags address to a vendor helper.
 if name!='os/linux/rt_rbus_pci_drv.c':
  texts[name]=texts[name].replace('ULONG flags;', 'ULONG flags = 0;')
 texts[name]=texts[name].replace('ULONG wr_flags;', 'ULONG wr_flags = 0;')

# Tasklet completion must not restore an interrupt mask after submission has
# been blocked for join. Callers already hold LockInterrupt; scheduling uses
# that same outer->nettask order. Keep this leaf free of waits/nested locks.
rbus='os/linux/rt_rbus_pci_drv.c'
begin=texts[rbus].index('static inline void rt2860_int_enable(')
end=texts[rbus].index('\n}',begin)+2
original=texts[rbus][begin:end]
guarded=original.replace('UINT32 regValue;', '''UINT32 regValue;
 ULONG wr_rearm_flags = 0;
 RTMP_INT_LOCK(&pAd->wr_iot_nettask_lock,wr_rearm_flags);
 if(pAd->wr_iot_nettask_owner.blocked || pAd->wr_iot_nettask_owner.poisoned){
  RTMP_INT_UNLOCK(&pAd->wr_iot_nettask_lock,wr_rearm_flags);
  return;
 }''',1)
guarded=guarded[:-2]+'\n RTMP_INT_UNLOCK(&pAd->wr_iot_nettask_lock,wr_rearm_flags);\n}'
if guarded==original:p.error('missing tasklet rearm guard anchor')
one(rbus,original,guarded)

# Disabling selected sources also writes the remaining nonzero mask. It must
# obey the same block fence, otherwise it can restore IRQs after full masking.
begin=texts[rbus].index('static inline void rt2860_int_disable(')
end=texts[rbus].index('\n}',begin)+2
original=texts[rbus][begin:end]
guarded=original.replace('UINT32 regValue;', 'UINT32 regValue;\n ULONG wr_rearm_flags = 0;\n RTMP_INT_LOCK(&pAd->wr_iot_nettask_lock,wr_rearm_flags);\n if(pAd->wr_iot_nettask_owner.blocked || pAd->wr_iot_nettask_owner.poisoned){\n  RTMP_INT_UNLOCK(&pAd->wr_iot_nettask_lock,wr_rearm_flags);\n  return;\n }',1)
guarded=guarded[:-2]+'\n RTMP_INT_UNLOCK(&pAd->wr_iot_nettask_lock,wr_rearm_flags);\n}'
one(rbus,original,guarded)


# Vendor module-release macro includes a trailing semicolon. Brace its
# if/else arm so expansion cannot terminate the conditional before else.
one('os/linux/rt_main_dev.c',
    '  if (closed)\n   RT_MOD_DEC_USE_COUNT();\n  else if',
    '  if (closed) {\n   RT_MOD_DEC_USE_COUNT();\n  } else if')

one('include/wr-iot-peer-open-client.inc',
    'static INT wr_iot_peer_open_release_config(',
    'static inline INT wr_iot_peer_open_release_config(')

# Match the existing implementation/type guard for repeater-only API.
one('include/rtmp.h',
    'REPEATER_CLIENT_ENTRY *lookup_rept_entry(RTMP_ADAPTER *pAd, PUCHAR address);',
    '#ifdef MAC_REPEATER_SUPPORT\nREPEATER_CLIENT_ENTRY *lookup_rept_entry(RTMP_ADAPTER *pAd, PUCHAR address);\n#endif')

one('include/rtmp.h','#include "aux-family-close.h"',
    '#include "aux-family-close.h"\n#include "aux-family-retry-scheduler.h"')
one('include/rtmp.h','\tstruct work_struct wr_iot_main_recovery_work;',
    '\tstruct work_struct wr_iot_main_recovery_work;\n'
    '\tstruct wr_iot_aux_retry_owner wr_iot_aux_family_retry;\n'
    '\tstruct work_struct wr_iot_aux_family_retry_work;')
one('include/rtmp.h','VOID wr_iot_main_recovery_work_fn(struct work_struct *work);',
    'VOID wr_iot_main_recovery_work_fn(struct work_struct *work);\n'
    'VOID wr_iot_aux_family_retry_work_fn(struct work_struct *work);\n'
    'INT wr_iot_aux_family_retry_submit(RTMP_ADAPTER *ad,PNET_DEV dev,'
    'enum wr_iot_ref_family family);\n'
    'INT wr_iot_aux_family_retry_rearm_joined(RTMP_ADAPTER *ad);')

one('include/wr-iot-aux-family-close-owned.inc',
    'static inline INT wr_iot_aux_family_close_retry_owned(RTMP_ADAPTER *ad,PNET_DEV dev,\n enum wr_iot_ref_family family)',
    'static inline INT wr_iot_aux_family_close_retry_owned(RTMP_ADAPTER *ad,PNET_DEV dev,\n'
    ' enum wr_iot_ref_family family,struct wr_iot_aux_retry_owner *retry_owner)')
one('include/wr-iot-aux-family-close-owned.inc','#include "aux-close-claim.h"',
    '#include "aux-close-claim.h"\n#include "aux-family-retry-scheduler.h"')
old_success=' RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);\n if(!consumed)return -EBUSY;'
new_success=(' if(!consumed)goto reject;\n'
             ' if(retry_owner&&!wr_iot_aux_retry_mark_completed(retry_owner,r,state,1))\n'
             '  goto reject;\n'
             ' RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);')
retry_source=texts['include/wr-iot-aux-family-close-owned.inc']
if retry_source.count(old_success)!=2:
 p.error('changed retry completion anchors')
first_success=retry_source.index(old_success)
second_success=retry_source.index(old_success,first_success+len(old_success))
texts['include/wr-iot-aux-family-close-owned.inc']=(
 retry_source[:second_success]+new_success+
 retry_source[second_success+len(old_success):])

one('common/rtmp_init.c',
    '\t\tINIT_WORK(&pAd->wr_iot_main_recovery_work, wr_iot_main_recovery_work_fn);',
    '\t\twr_iot_aux_retry_init(&pAd->wr_iot_aux_family_retry);\n'
    '\t\tINIT_WORK(&pAd->wr_iot_main_recovery_work, wr_iot_main_recovery_work_fn);\n'
    '\t\tINIT_WORK(&pAd->wr_iot_aux_family_retry_work, wr_iot_aux_family_retry_work_fn);')

retry_impl=r'''
/* Exact-ticket APCLI/Monitor continuation. The adapter lock is never held
 * while calling vendor close paths or while waiting for RTNL. */
INT wr_iot_aux_family_retry_submit(RTMP_ADAPTER *ad,PNET_DEV dev,
 enum wr_iot_ref_family family)
{
 struct wr_iot_aux_retry_owner *owner;
 struct wr_iot_interface_ref *record=NULL;
 struct wr_iot_family_close *state;
 unsigned int i;
 ULONG flags;
 int queued=0,accepted;
 if(!ad||!dev||(family!=WR_REF_FAMILY_APCLI&&family!=WR_REF_FAMILY_MONITOR))
  return -EBUSY;
 owner=&ad->wr_iot_aux_family_retry;
 dev_hold(dev);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(!ad->wr_iot_transition.retiring)
  for(i=0;i<WDEV_NUM_MAX+1;i++)
   if(ad->wr_iot_interface_refs[i].device==dev){
    if(record){record=NULL;break;}
    record=&ad->wr_iot_interface_refs[i];
   }
 if(record&&record->family==family){
  state=&ad->wr_iot_family_close[record-ad->wr_iot_interface_refs];
  queued=wr_iot_aux_retry_queue(owner,record,state,1,1,1);
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!queued){dev_put(dev);return -EBUSY;}
 accepted=schedule_work(&ad->wr_iot_aux_family_retry_work);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 (void)wr_iot_aux_retry_schedule_result(owner,accepted);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return accepted?0:-EBUSY;
}

VOID wr_iot_aux_family_retry_work_fn(struct work_struct *work)
{
 RTMP_ADAPTER *ad;
 struct wr_iot_aux_retry_owner *owner;
 struct wr_iot_interface_ref *record;
 PNET_DEV dev;
 enum wr_iot_ref_family family;
 ULONG flags;
 int result=-EBUSY,drop=0;
 if(!work)return;
 ad=container_of(work,RTMP_ADAPTER,wr_iot_aux_family_retry_work);
 owner=&ad->wr_iot_aux_family_retry;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
  owner->device,owner->generation);
 if(!record||!wr_iot_aux_retry_begin(owner,record,
    &ad->wr_iot_family_close[record-ad->wr_iot_interface_refs])||
    !wr_iot_aux_retry_action(owner,record,
    &ad->wr_iot_family_close[record-ad->wr_iot_interface_refs])){
  (void)wr_iot_aux_retry_abandon(owner);
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
  return;
 }
 dev=(PNET_DEV)owner->device;family=owner->family;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);

 rtnl_lock();
 result=wr_iot_aux_family_close_retry_owned(ad,dev,family,owner);
 rtnl_unlock();

 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(result==0&&owner->completed)
  (void)wr_iot_aux_retry_complete(owner,1,&drop);
 if(!drop)(void)wr_iot_aux_retry_retain(owner);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(drop)dev_put((struct net_device *)dev);
}

'''
retry_impl+=r'''
/* Process context only: caller holds neither RTNL nor transition lock and
 * pins adapter lifetime. Do not call from this work item or ndo_stop. This
 * entry performs one bounded continuation, not an unbounded retry loop. */
INT wr_iot_aux_family_retry_rearm_joined(RTMP_ADAPTER *ad)
{
 struct wr_iot_interface_ref *record;
 struct wr_iot_aux_retry_owner *owner;
 ULONG flags;
 int accepted=0;
 if(!ad)return -EBUSY;
 flush_work(&ad->wr_iot_aux_family_retry_work);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 owner=&ad->wr_iot_aux_family_retry;
 record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
  owner->device,owner->generation);
 if(!ad->wr_iot_transition.retiring &&
    !work_busy(&ad->wr_iot_aux_family_retry_work) && record &&
    wr_iot_aux_retry_rearm_retained(owner,record,
     &ad->wr_iot_family_close[record-ad->wr_iot_interface_refs],1,3)){
  accepted=schedule_work(&ad->wr_iot_aux_family_retry_work);
  (void)wr_iot_aux_retry_schedule_result(owner,accepted);
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return accepted?0:-EBUSY;
}

'''

# Shared retry work must exist even when the APCLI object is not selected.
# Reuse the exact already-transformed inline retry body; no ownership changes.
retry_body=texts['include/wr-iot-aux-family-close-owned.inc']
retry_body=retry_body[retry_body.index('static inline INT wr_iot_aux_family_close_retry_owned('):]
one('common/rtmp_init.c','#include "queued-work.h"',
    '#include "queued-work.h"\n#include <linux/rtnetlink.h>\n'
    '#include "aux-close-claim.h"\n'+retry_body+'\n'+retry_impl)
one('ap/ap_apcli_inf.c',
    ' return wr_iot_aux_family_close_owned(RTMP_OS_NETDEV_GET_PRIV(dev_p),dev_p,WR_REF_FAMILY_APCLI,wr_iot_apcli_close_ioctl);\n}',
    ' {\n'
    '  RTMP_ADAPTER *ad=RTMP_OS_NETDEV_GET_PRIV(dev_p);\n'
    '  INT result=wr_iot_aux_family_close_owned(ad,dev_p,WR_REF_FAMILY_APCLI,wr_iot_apcli_close_ioctl);\n'
    '  if(result==-EBUSY)(void)wr_iot_aux_family_retry_submit(ad,dev_p,WR_REF_FAMILY_APCLI);\n'
    '  return result;\n'
    ' }\n}')
one('os/linux/rt_profile.c',
    ' return wr_iot_aux_family_close_owned(RTMP_OS_NETDEV_GET_PRIV(dev_p),dev_p,WR_REF_FAMILY_MONITOR,wr_iot_monitor_close_ioctl);\n}',
    ' {\n'
    '  RTMP_ADAPTER *ad=RTMP_OS_NETDEV_GET_PRIV(dev_p);\n'
    '  INT result=wr_iot_aux_family_close_owned(ad,dev_p,WR_REF_FAMILY_MONITOR,wr_iot_monitor_close_ioctl);\n'
    '  if(result==-EBUSY)(void)wr_iot_aux_family_retry_submit(ad,dev_p,WR_REF_FAMILY_MONITOR);\n'
    '  return result;\n'
    ' }\n}')
one('ap/ap_apcli_inf.c',
    ' return wr_iot_aux_family_close_retry_owned(RTMP_OS_NETDEV_GET_PRIV(dev_p),dev_p,WR_REF_FAMILY_APCLI);',
    ' return wr_iot_aux_family_close_retry_owned(RTMP_OS_NETDEV_GET_PRIV(dev_p),dev_p,WR_REF_FAMILY_APCLI,NULL);')
one('ap/ap_apcli_inf.c',
    '/* Caller pins device/adapter and holds RTNL; no automatic retry scheduler. */',
    '/* Direct/manual exact-ticket retry entry; ndo_stop schedules the worker. */')
one('os/linux/rt_profile.c',
    ' return wr_iot_aux_family_close_retry_owned(RTMP_OS_NETDEV_GET_PRIV(dev_p),dev_p,WR_REF_FAMILY_MONITOR);',
    ' return wr_iot_aux_family_close_retry_owned(RTMP_OS_NETDEV_GET_PRIV(dev_p),dev_p,WR_REF_FAMILY_MONITOR,NULL);')
one('os/linux/rt_profile.c',
    '/* Caller pins device/adapter and holds RTNL; no automatic retry scheduler. */',
    '/* Direct/manual exact-ticket retry entry; ndo_stop schedules the worker. */')

one('include/wr-iot-peer-adapter-release.inc',
    '!pAd->wr_iot_registration_inflight && !pAd->wr_iot_main_recovery.deferred_owners;',
    '!pAd->wr_iot_registration_inflight && !pAd->wr_iot_main_recovery.deferred_owners &&\n'
    '  !pAd->wr_iot_aux_family_retry.deferred_owners &&\n'
    '  !work_busy(&pAd->wr_iot_aux_family_retry_work);')

# Preserve unrelated AGG_TEMP bits, including the firmware radio-off request.
# This fixes the mask only; shared-register RMW serialization is still required.
one('hw_ctrl/cmm_asic_mt.c', 'Value &= (0<<1);', 'Value &= ~(1U << 1);')

# A separate leaf IRQ lock covers every AGG_TEMP CPU RMW. No sleeping calls,
# transition lock acquisition or firmware wait is allowed inside these blocks.
one('include/rtmp.h','\tNDIS_SPIN_LOCK wr_iot_transition_lock;',
    '\tNDIS_SPIN_LOCK wr_iot_agg_temp_lock;\n\tNDIS_SPIN_LOCK wr_iot_transition_lock;')
one('common/rtmp_init.c','\t\tNdisAllocateSpinLock(pAd, &pAd->irq_lock);',
    '\t\tNdisAllocateSpinLock(pAd, &pAd->wr_iot_agg_temp_lock);\n'
    '\t\tNdisAllocateSpinLock(pAd, &pAd->irq_lock);')
one('os/linux/rt_profile.c','\tNdisFreeSpinLock(&pAd->wr_iot_transition_lock);',
    '\tNdisFreeSpinLock(&pAd->wr_iot_agg_temp_lock);\n'
    '\tNdisFreeSpinLock(&pAd->wr_iot_transition_lock);')

def agg_locked(match):
 body=match.group(0)
 return ('{ ULONG wr_agg_flags = 0;\n'
         'RTMP_INT_LOCK(&pAd->wr_iot_agg_temp_lock, wr_agg_flags);\n'+body+
         '\nRTMP_INT_UNLOCK(&pAd->wr_iot_agg_temp_lock, wr_agg_flags);\n}')
for name,expected in [('hw_ctrl/cmm_asic_mt.c',6),('common/cmm_mac_pci.c',1),
                      ('common/rtmp_init_inf.c',1)]:
 # Preserve original conditional write for RTS; include its closing brace.
 pattern=(r'RTMP_IO_READ32\(pAd, AGG_TEMP, &Value\);\s*'
          r'if \(\(Value & \(1<<1\)\) [!=]= 0\) \{\s*'
          r'Value [|&]= [^;]+;\s*RTMP_IO_WRITE32\(pAd, AGG_TEMP, Value\);\s*\}'
          r'|RTMP_IO_READ32\(pAd, AGG_TEMP, &value\);\s*'
          r'value [|&]= [^;]+;\s*RTMP_IO_WRITE32\(pAd, AGG_TEMP, value\);')
 texts[name],count=re.subn(pattern,agg_locked,texts[name])
 if count!=expected:p.error('AGG_TEMP RMW inventory changed: '+name+': '+str(count))

# Reuse existing checked message ownership/result handling, not generic callback.
sender=('#ifdef RTMP_PCI_SUPPORT\n'
    'INT32 wr_iot_send_radio_off_checked(RTMP_ADAPTER *pAd)\n'
    '{\n struct cmd_msg *msg;\n'
    ' if(!pAd)return NDIS_STATUS_FAILURE;\n'
    ' msg=wr_iot_prepare_radio_off(pAd);\n'
    ' if(!msg)return NDIS_STATUS_RESOURCES;\n'
    ' return AndesSendCmdMsg(pAd,msg);\n}\n'
    '#endif /* RTMP_PCI_SUPPORT */\n\n')
mcu=texts['mcu/andes_mt.c'];count=mcu.count('INT32 wr_iot_send_radio_off_checked(')
if count==0:
 one('mcu/andes_mt.c','INT32 CmdRadioOnOffCtrl(RTMP_ADAPTER *pAd, UINT8 On)',
     sender+'INT32 CmdRadioOnOffCtrl(RTMP_ADAPTER *pAd, UINT8 On)')
elif count!=1 or sender not in mcu:
 p.error('checked radio-off sender differs from reviewed implementation')
header=texts['include/rtmp.h'];prototype='INT32 wr_iot_send_radio_off_checked(RTMP_ADAPTER *pAd);'
if prototype not in header:
 one('include/rtmp.h','VOID wr_iot_aux_family_retry_work_fn(struct work_struct *work);',
     prototype+'\nVOID wr_iot_aux_family_retry_work_fn(struct work_struct *work);')
one('hw_ctrl/cmm_asic_mt.c',
    'if (CmdRadioOnOffCtrl(pAd, WIFI_RADIO_OFF) != NDIS_STATUS_SUCCESS)',
    'if (wr_iot_send_radio_off_checked(pAd) != NDIS_STATUS_SUCCESS)')

# Apply current MAC stop readbacks only after the historical pinned chain.
one('hw_ctrl/cmm_asic_mt.c',' UINT32 arb;',' UINT32 arb, rqcr, tqcr0;')
one('hw_ctrl/cmm_asic_mt.c',
    '  if (arb == 0xffffffffU || !(arb & MT_ARB_SCR_RXDIS)) return FALSE;',
    '  if (arb == 0xffffffffU || !(arb & MT_ARB_SCR_RXDIS)) return FALSE;\n'
    '  RTMP_IO_READ32(pAd, ARB_RQCR, &rqcr);\n'
    '  if (rqcr == 0xffffffffU || (rqcr & ARB_RQCR_RX_START)) return FALSE;')
one('hw_ctrl/cmm_asic_mt.c',
    '  if (!AsicSetWPDMA(pAd, PDMA_TX_RX, FALSE)) return FALSE;',
    '  RTMP_IO_READ32(pAd, ARB_TQCR0, &tqcr0);\n'
    '  if (tqcr0 == 0xffffffffU || tqcr0 != 0U) return FALSE;\n'
    '  RTMP_IO_READ32(pAd, ARB_RQCR, &rqcr);\n'
    '  if (rqcr == 0xffffffffU || (rqcr & ARB_RQCR_RX_START)) return FALSE;\n'
    '  if (!AsicSetWPDMA(pAd, PDMA_TX_RX, FALSE)) return FALSE;')

pci='os/linux/pci_main_dev.c'
# PCI core may invoke cleanup after partial setup. Validate netdev before
# reading its base address or private adapter; successful path is unchanged.
one(pci,
    '\tULONG csr_addr = net_dev->base_addr;\n\n\n\tGET_PAD_FROM_NET_DEV(pAd, net_dev);',
    '\tULONG csr_addr;\n\n\tif (!net_dev) return;\n\tcsr_addr = net_dev->base_addr;\n\tGET_PAD_FROM_NET_DEV(pAd, net_dev);')
all_occurrences(pci,'adapter->wr_iot_main_recovery.deferred_owners',
 '(adapter->wr_iot_main_recovery.deferred_owners ||\n'
 '     adapter->wr_iot_aux_family_retry.deferred_owners ||\n'
 '     work_busy(&adapter->wr_iot_aux_family_retry_work))')
all_occurrences(pci,'cancel_work_sync(&adapter->wr_iot_main_recovery_work);',
 'cancel_work_sync(&adapter->wr_iot_main_recovery_work);\n'
 '\t\tcancel_work_sync(&adapter->wr_iot_aux_family_retry_work);')
one(pci,'flush_work(&adapter->wr_iot_main_recovery_work);',
    'flush_work(&adapter->wr_iot_main_recovery_work);\n'
    '  flush_work(&adapter->wr_iot_aux_family_retry_work);')
one(pci,'cancel_work_sync(&pAd->wr_iot_main_recovery_work);',
    'cancel_work_sync(&pAd->wr_iot_main_recovery_work);\n'
    '\tcancel_work_sync(&pAd->wr_iot_aux_family_retry_work);')
one(pci,'\tif (pAd != NULL)\n\t{\n\t\tPRTMP_ADAPTER adapter = (PRTMP_ADAPTER)pAd;\n\t\tULONG flags;',
    '\tif (pAd != NULL)\n\t{\n\t\tPRTMP_ADAPTER adapter = (PRTMP_ADAPTER)pAd;\n\t\tULONG flags;\n'
    '\t\t/* Let an already-owned exact-ticket continuation finish before\n'
    '\t\t * the radio transition is permanently retired. */\n'
    '\t\t(void)wr_iot_aux_family_retry_rearm_joined(adapter);\n'
    '\t\tflush_work(&adapter->wr_iot_aux_family_retry_work);')

# Join admitted normal OPEN before the first retirement-state refusal.
# Drop the short transition lock before RTNL and release RTNL before workers.
one(pci,
    '\t\twr_iot_radio_retire(&adapter->wr_iot_transition);\n',
    '\t\twr_iot_radio_retire(&adapter->wr_iot_transition);\n'
    '\t\tRTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);\n'
    '\t\tRtmpOSNetDevProtect(1);\n'
    '\t\tRtmpOSNetDevProtect(0);\n'
    '\t\tRTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);\n')

# Closing queue admission is distinct from canceling one queued instance.
one(pci,
    'wr_iot_main_recovery_request_stop(&adapter->wr_iot_main_recovery);',
    'wr_iot_main_recovery_request_stop(&adapter->wr_iot_main_recovery);\n'
    '\t\t(void)wr_iot_aux_retry_request_stop(&adapter->wr_iot_aux_family_retry);')

# A stalled logical close must not leave recovery callbacks queued across
# driver-core unbind. Stop admission, join work, preserve unresolved owners.
one(pci,
    '\t\tif (!wr_iot_pci_recovery_drain(adapter))\n'
    '\t\t\treturn; /* Still-owned recovery blocks this isolated candidate. */',
    '\t\tif (!wr_iot_pci_recovery_drain(adapter)) {\n'
    '\t\t\tRTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);\n'
    '\t\t\t(void)wr_iot_main_recovery_request_stop(&adapter->wr_iot_main_recovery);\n'
    '\t\t\t(void)wr_iot_aux_retry_request_stop(&adapter->wr_iot_aux_family_retry);\n'
    '\t\t\tRTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);\n'
    '\t\t\tcancel_delayed_work_sync(&adapter->wr_iot_main_recovery_reap_work);\n'
    '\t\t\tcancel_work_sync(&adapter->wr_iot_main_recovery_work);\n'
    '\t\t\tcancel_work_sync(&adapter->wr_iot_aux_family_retry_work);\n'
    '\t\t\twr_iot_main_recovery_join_complete(adapter);\n'
    '\t\t\treturn; /* Retained owners; terminal DMA/IRQ fence still required. */\n'
    '\t\t}')

shutil.copytree(src,out)
for name,text in texts.items():
 (out/name).write_text(text,encoding='utf-8',newline='\n')
shutil.copyfile(here/'aux-family-retry-scheduler.h',
                out/'include/aux-family-retry-scheduler.h')
print('Bound APCLI/Monitor exact-ticket retry worker to netdev/adapter lifetime; '
      'target ABI and runtime remain unverified')
