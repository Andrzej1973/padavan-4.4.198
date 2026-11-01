#!/usr/bin/env python3
"""Audit the staged APCLI/Monitor retry scheduler binding, without target claims."""
import re
import argparse
import hashlib
import json
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
root=a.candidate.resolve(strict=True)
if a.output.exists():p.error('new report required')

def text(name):
 return (root/name).read_text(encoding='utf-8')

def body(source,signature):
 start=source.index(signature)
 brace=source.index('{',start)
 depth=0
 for end in range(brace,len(source)):
  if source[end]=='{':depth+=1
  elif source[end]=='}':
   depth-=1
   if depth==0:return source[start:end+1]
 raise ValueError('unterminated function: '+signature)

rtmp=text('include/rtmp.h')
init=text('common/rtmp_init.c')
apcli=text('ap/ap_apcli_inf.c')
monitor=text('os/linux/rt_profile.c')
pci=text('os/linux/pci_main_dev.c')
release=text('include/wr-iot-peer-adapter-release.inc')
retry=text('include/wr-iot-aux-family-close-owned.inc')

active_init=re.sub(r'/\*.*?\*/|//[^\n]*', '', init, flags=re.S)
assert active_init.count('#include <linux/rtnetlink.h>')==1
assert init.index('#include <linux/rtnetlink.h>') < init.index('VOID wr_iot_aux_family_retry_work_fn(')
assert 'VOID wr_iot_aux_family_retry_work_fn(' not in apcli

submit=body(init,'INT wr_iot_aux_family_retry_submit(')
worker=body(init,'VOID wr_iot_aux_family_retry_work_fn(')
rearm=body(init,'INT wr_iot_aux_family_retry_rearm_joined(')
assert rearm.index('flush_work(')<rearm.index('RTMP_IRQ_LOCK(')
assert rearm.index('wr_iot_registry_find(')<rearm.index('wr_iot_aux_retry_rearm_retained(')
assert rearm.index('wr_iot_aux_retry_rearm_retained(')<rearm.index('schedule_work(')
assert rearm.index('schedule_work(')<rearm.index('wr_iot_aux_retry_schedule_result(')<rearm.index('RTMP_IRQ_UNLOCK(')
assert '!ad->wr_iot_transition.retiring' in rearm
assert '!work_busy(&ad->wr_iot_aux_family_retry_work)' in rearm
assert 'rtnl_lock(' not in rearm and 'dev_put(' not in rearm
assert 'for(' not in rearm and 'while(' not in rearm

assert '#include "aux-family-retry-scheduler.h"' in rtmp
assert 'struct wr_iot_aux_retry_owner wr_iot_aux_family_retry;' in rtmp
assert 'struct work_struct wr_iot_aux_family_retry_work;' in rtmp
assert 'VOID wr_iot_aux_family_retry_work_fn(struct work_struct *work);' in rtmp
assert 'wr_iot_aux_retry_init(&pAd->wr_iot_aux_family_retry);' in init
assert 'INIT_WORK(&pAd->wr_iot_aux_family_retry_work,' in init
assert '!pAd->wr_iot_aux_family_retry.deferred_owners' in release
assert '!work_busy(&pAd->wr_iot_aux_family_retry_work)' in release

assert submit.index('dev_hold(dev);')<submit.index('RTMP_IRQ_LOCK(')
assert submit.index('RTMP_IRQ_UNLOCK(')<submit.index('schedule_work(')
assert 'wr_iot_aux_retry_queue(' in submit
assert 'wr_iot_aux_retry_schedule_result(' in submit

assert 'container_of(work,RTMP_ADAPTER,wr_iot_aux_family_retry_work)' in worker
assert 'wr_iot_aux_retry_begin(' in worker
assert 'wr_iot_aux_retry_action(' in worker
assert 'wr_iot_aux_retry_complete(owner,1,&drop)' in worker
assert worker.index('rtnl_lock();')<worker.index('wr_iot_aux_family_close_retry_owned(')
assert worker.index('wr_iot_aux_family_close_retry_owned(')<worker.index('rtnl_unlock();')
assert 'dev_close(' not in worker
assert 'if(drop)dev_put((struct net_device *)dev);' in worker

for source,name in ((apcli,'APCLI'),(monitor,'MONITOR')):
 assert source.count('if(result==-EBUSY)(void)wr_iot_aux_family_retry_submit(')==1,name
assert 'wr_iot_aux_family_close_retry_owned(ad,dev,family,owner)' in worker
assert 'wr_iot_aux_family_close_retry_owned(RTMP_OS_NETDEV_GET_PRIV(dev_p),dev_p,WR_REF_FAMILY_APCLI,NULL)' in apcli
assert 'wr_iot_aux_family_close_retry_owned(RTMP_OS_NETDEV_GET_PRIV(dev_p),dev_p,WR_REF_FAMILY_MONITOR,NULL)' in monitor

retry_sig='enum wr_iot_ref_family family,struct wr_iot_aux_retry_owner *retry_owner)'
assert retry.count(retry_sig)==1
assert retry.count('wr_iot_aux_retry_mark_completed(retry_owner,r,state,1)')==1
mark=retry.index('wr_iot_aux_retry_mark_completed(retry_owner,r,state,1)')
retry_fn=retry.index('static inline INT wr_iot_aux_family_close_retry_owned(')
function_tail=retry[retry_fn:]
mark_in_function=function_tail.index('wr_iot_aux_retry_mark_completed(retry_owner,r,state,1)')
assert function_tail.index('if(!consumed)goto reject;')<mark_in_function
assert mark_in_function<function_tail.index('RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);',mark_in_function)
assert mark_in_function<function_tail.index('RT_MOD_DEC_USE_COUNT();')

assert pci.count('cancel_work_sync(&adapter->wr_iot_aux_family_retry_work);')>=2
assert pci.count('cancel_work_sync(&((PRTMP_ADAPTER)pAd)->wr_iot_aux_family_retry_work);')==1
assert pci.count('flush_work(&adapter->wr_iot_aux_family_retry_work);')>=2
# Counts alone cannot establish ordering of the actual removal path.
remove=body(pci,'static VOID DEVEXIT rt_pci_remove(')
first_flush=remove.index('flush_work(&adapter->wr_iot_aux_family_retry_work);')
assert remove.index('wr_iot_aux_family_retry_rearm_joined(adapter)')<first_flush
assert 'rtnl_lock(' not in remove[:first_flush]
assert 'RTMP_IRQ_LOCK(' not in remove[:first_flush]
retire=remove.index('wr_iot_radio_retire(')
first_join=remove.index('cancel_work_sync(&adapter->wr_iot_aux_family_retry_work);')
children=remove.index('RtmpPhyNetDevExit(pAd, net_dev)')
second_join=remove.index('cancel_work_sync(&adapter->wr_iot_aux_family_retry_work);',first_join+1)
release_adapter=remove.index('RtmpRaDevCtrlExit(pAd)')
assert first_flush<retire<first_join<children<second_join<release_adapter
for start,end in ((first_join,children),(second_join,release_adapter)):
 section=remove[start:end]
 assert 'adapter->wr_iot_aux_family_retry.deferred_owners' in section
 assert 'work_busy(&adapter->wr_iot_aux_family_retry_work)' in section
 assert 'return;' in section
assert pci.count('adapter->wr_iot_aux_family_retry.deferred_owners')>=4
assert pci.count('work_busy(&adapter->wr_iot_aux_family_retry_work)')>=4

files=[
 'include/rtmp.h','common/rtmp_init.c','ap/ap_apcli_inf.c',
 'os/linux/rt_profile.c','os/linux/pci_main_dev.c',
 'include/wr-iot-peer-adapter-release.inc',
 'include/wr-iot-aux-family-close-owned.inc',
 'include/aux-family-retry-scheduler.h',
]
report={
 'scope':'source-order and binding audit; no kernel concurrency or target ABI proof',
 'source_sha256':{
  name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files
 },
 'structure_ready':True,
 'target_compiled':False,
 'runtime_verified':False,
 'lifecycle_accepted':False,
 'bound':{
  'netdev_hold_before_schedule':True,
  'module_release_after_exact_completion':True,
  'worker_uses_rtnl':True,
  'family_ioctl_replay':False,
  'adapter_release_fence':True,
  'pci_stop_and_join_paths':True,
 },
 'open':[
  'target RTNL/workqueue ABI and all build configurations are uncompiled',
  'worker cancellation versus concurrent ndo_open reuse needs target stress evidence',
  'callback, timer, tasklet, IRQ and DMA quiescence remain outside scheduler ownership',
  'retained failed/canceled work intentionally blocks adapter free and has no reaper',
 ],
}
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('PASS scheduler binding structure; target ABI, concurrency and runtime remain open')
