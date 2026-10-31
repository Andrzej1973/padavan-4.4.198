#!/usr/bin/env python3
"""Bind the isolated APCLI/Monitor retry scheduler to a new candidate tree."""
import argparse
import hashlib
import shutil
from pathlib import Path

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
 if hashlib.sha256(raw).hexdigest()!=digest:
  p.error('unreviewed predecessor: '+name)
 texts[name]=raw.decode()

def one(name,old,new):
 if texts[name].count(old)!=1:p.error('changed anchor '+name+': '+old[:60])
 texts[name]=texts[name].replace(old,new,1)

def all_occurrences(name,old,new):
 count=texts[name].count(old)
 if not count:p.error('missing anchor '+name+': '+old[:60])
 texts[name]=texts[name].replace(old,new)

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
    'enum wr_iot_ref_family family);')

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
one('ap/ap_apcli_inf.c','INT ApCli_VirtualIF_Close(PNET_DEV dev_p)',
    retry_impl+'INT ApCli_VirtualIF_Close(PNET_DEV dev_p)')
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

pci='os/linux/pci_main_dev.c'
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
    '\t\tflush_work(&adapter->wr_iot_aux_family_retry_work);')

shutil.copytree(src,out)
for name,text in texts.items():
 (out/name).write_text(text,encoding='utf-8',newline='\n')
shutil.copyfile(here/'aux-family-retry-scheduler.h',
                out/'include/aux-family-retry-scheduler.h')
print('Bound APCLI/Monitor exact-ticket retry worker to netdev/adapter lifetime; '
      'target ABI and runtime remain unverified')
