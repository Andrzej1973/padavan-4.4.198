#!/usr/bin/env python3
"""Bind network tasklet submission fence, drain and preserved early callback join."""
import argparse,hashlib,shutil,re,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'include/rtmp.h':'b56e19e01a97069fcb5a3e47979eed575f50be763c2537c694653715e5ba7418',
 'common/rtmp_init.c':'76daa0108997474e0ebd58fdc181d3e815848d04030189a33cf390126b01567c',
 'os/linux/rt_profile.c':'71d1f26a465ab6e9a0dd5d1aa2e4e16a5878a4a7f26eb9f84a1d66d583da8082',
 'os/linux/rt_rbus_pci_drv.c':'32916c0162e3c9ddf43b836b78cfac276487335f22452285456b197d8391a3de',
 'common/ba_action.c':'51326425640e6e56b21bb69907a928dd70a758f352769c5ce70fd0a9a45c71ca',
 'common/cmm_data_pci.c':'344f9ebe14a27217c2f09b8bc5f97bff63d1efc13a7551a6b293877aed506860',
 'common/uapsd.c':'8702bbdc06a076536e9953daf3d3f7d71426baf870406e8f7a555f5debc21fac'}
texts={}
for name,digest in pins.items():
 if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
 texts[name]=(src/name).read_text()
def one(name,old,new):
 if texts[name].count(old)!=1:p.error('changed anchor '+name+': '+old)
 texts[name]=texts[name].replace(old,new,1)
one('include/rtmp.h','#include "peer-table-owner.h"','#include "peer-table-owner.h"\n#include "tasklet-schedule-owner.h"')
one('include/rtmp.h','NDIS_SPIN_LOCK wr_iot_transition_lock;', '''NDIS_SPIN_LOCK wr_iot_transition_lock;
 NDIS_SPIN_LOCK wr_iot_nettask_lock;
 struct wr_iot_tasklet_schedule_owner wr_iot_nettask_owner;
 wait_queue_head_t wr_iot_nettask_wait;
 unsigned int wr_iot_nettask_joined;''')
one('include/rtmp.h','INT RtmpNetTaskExit(RTMP_ADAPTER *pAd);', '''INT RtmpNetTaskExit(RTMP_ADAPTER *pAd);
#ifdef RTMP_MAC_PCI
VOID wr_iot_nettask_schedule(RTMP_ADAPTER *pAd,RTMP_NET_TASK_STRUCT *task);
#define WR_IOT_NETTASK_SCHEDULE(ad,task) wr_iot_nettask_schedule((ad),(task))
#else
#define WR_IOT_NETTASK_SCHEDULE(ad,task) RTMP_OS_TASKLET_SCHE(task)
#endif''')
one('common/rtmp_init.c','NdisAllocateSpinLock(pAd, &pAd->wr_iot_transition_lock);', '''NdisAllocateSpinLock(pAd, &pAd->wr_iot_transition_lock);
 NdisAllocateSpinLock(pAd,&pAd->wr_iot_nettask_lock);
 wr_iot_tasklet_schedule_init(&pAd->wr_iot_nettask_owner);
 init_waitqueue_head(&pAd->wr_iot_nettask_wait);
 pAd->wr_iot_nettask_joined=1; /* Fresh adapter has never submitted a tasklet. */''')
one('os/linux/rt_profile.c','NdisFreeSpinLock(&pAd->wr_iot_transition_lock);',
 'NdisFreeSpinLock(&pAd->wr_iot_nettask_lock);\n\tNdisFreeSpinLock(&pAd->wr_iot_transition_lock);')
counts={}
for name,count in [('os/linux/rt_rbus_pci_drv.c',29),('common/ba_action.c',1),('common/cmm_data_pci.c',2),('common/uapsd.c',3)]:
 s=texts[name];s,n=re.subn(r'RTMP_OS_TASKLET_SCHE\(([^;\n]+)\)',r'WR_IOT_NETTASK_SCHEDULE(pAd,\1)',s)
 if n!=count:p.error('changed schedule inventory: '+name)
 counts[name]=n;texts[name]=s
name='os/linux/rt_rbus_pci_drv.c'
one(name,'NDIS_STATUS RtmpNetTaskInit(RTMP_ADAPTER *pAd)',
 '#include "wr-iot-nettask-schedule.inc"\nNDIS_STATUS RtmpNetTaskInit(RTMP_ADAPTER *pAd)')
s=texts[name];start=s.index('NDIS_STATUS RtmpNetTaskInit(');end=s.index('\n}',start)+2;body=s[start:end]
anchor='pObj = (POS_COOKIE) pAd->OS_Cookie;'
assert body.count(anchor)==1
body=body.replace(anchor,'if(!wr_iot_nettask_may_initialize(pAd))return NDIS_STATUS_FAILURE;\n\t'+anchor,1)
body=body.replace('return NDIS_STATUS_SUCCESS;','return wr_iot_nettask_open(pAd);',1)
s=s[:start]+body+s[end:];start=s.index('INT RtmpNetTaskExit(');end=s.index('\n}',start)+2;body=s[start:end]
anchor='POS_COOKIE pObj = (POS_COOKIE) pAd->OS_Cookie;'
assert body.count(anchor)==1
body=body.replace(anchor,anchor+'''
 ULONG wr_flags;int wr_joined;
 if(wr_iot_nettask_block_drain(pAd)!=NDIS_STATUS_SUCCESS)return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&pAd->wr_iot_nettask_lock,wr_flags);
 wr_joined=pAd->wr_iot_nettask_joined;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_nettask_lock,wr_flags);
 if(wr_joined)return NDIS_STATUS_SUCCESS;
''',1)
body=body.replace('return NDIS_STATUS_SUCCESS;', '''return NDIS_STATUS_SUCCESS;''',1)
pos=body.rindex('return NDIS_STATUS_SUCCESS;')
body=body[:pos]+'''RTMP_IRQ_LOCK(&pAd->wr_iot_nettask_lock,wr_flags);
 pAd->wr_iot_nettask_joined=1;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_nettask_lock,wr_flags);
 '''+body[pos:]
texts[name]=s[:start]+body+s[end:]
shutil.copytree(src,out)
for name,text in texts.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
for local,target in [('tasklet-schedule-owner.h','tasklet-schedule-owner.h'),('nettask-schedule.inc','wr-iot-nettask-schedule.inc')]:
 shutil.copyfile(Path(__file__).with_name(local),out/'include'/target)
out.with_name(out.name+'-manifest.json').write_text(json.dumps({'input_sha256':pins,'network_submission_sites':counts,
 'target_compiled':False,'runtime_verified':False,'all_lifetime_paths_accepted':False},indent=2)+'\n')
print('Bound35 network scheduling sites and early block/drain/join; MCU/recovery/polling unchanged')
