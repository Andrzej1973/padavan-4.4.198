#!/usr/bin/env python3
"""Bind MBSS work contexts/callback and live-work guards without admission."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.source.resolve(strict=True);out=a.output.resolve();here=Path(__file__).resolve().parent
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
m=json.loads(src.with_name(src.name+'.manifest.json').read_text());actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if actual!=m['merged_driver_sha256'] or m.get('production_installed') is not False or 'raw_recovery_free_fence_layer' not in m:p.error('changed/unsupported input')
changes={};undo=[]
def one(rel,old,new):
 s=changes.get(rel,(src/rel).read_text())
 if s.count(old)!=1:p.error('unreviewed MBSS work anchor: '+rel)
 undo.append((rel,old,new));changes[rel]=s.replace(old,new,1)
one('include/rtmp.h','struct _RTMP_ADAPTER {','''struct wr_iot_mbss_work_context {
 struct work_struct work;
 RTMP_ADAPTER *adapter;
 unsigned int slot;
};
struct _RTMP_ADAPTER {''')
one('include/rtmp.h',' struct wr_iot_mbss_recovery_owner wr_iot_mbss_recovery[WDEV_NUM_MAX + 1];',' struct wr_iot_mbss_recovery_owner wr_iot_mbss_recovery[WDEV_NUM_MAX + 1];\n struct wr_iot_mbss_work_context wr_iot_mbss_work[WDEV_NUM_MAX + 1];')
one('include/rtmp.h','VOID wr_iot_main_recovery_work_fn(struct work_struct *work);','''VOID wr_iot_main_recovery_work_fn(struct work_struct *work);
VOID wr_iot_mbss_recovery_work_fn(struct work_struct *work);
BOOLEAN wr_iot_mbss_recovery_idle_locked(RTMP_ADAPTER *ad);
INT wr_iot_mbss_begin_close(PNET_DEV dev,struct wr_iot_radio_ticket *ticket,unsigned long *generation);
INT wr_iot_mbss_close_checked(PNET_DEV dev,unsigned long generation,const struct wr_iot_radio_ticket *ticket);''')
one('common/rtmp_init.c','#include "aux-close-claim.h"','#include "aux-close-claim.h"\n#include "wr-iot-mbss-recovery-work.inc"')
one('common/rtmp_init.c',' wr_iot_mbss_recovery_init(&pAd->wr_iot_mbss_recovery[wr_iot_slot]);',''' wr_iot_mbss_recovery_init(&pAd->wr_iot_mbss_recovery[wr_iot_slot]);
 pAd->wr_iot_mbss_work[wr_iot_slot].adapter=pAd;
 pAd->wr_iot_mbss_work[wr_iot_slot].slot=wr_iot_slot;
 INIT_WORK(&pAd->wr_iot_mbss_work[wr_iot_slot].work,wr_iot_mbss_recovery_work_fn);''')
for rel,old,new in [
 ('include/wr-iot-peer-adapter-release.inc','wr_iot_mbss_recovery_storage_idle(pAd->wr_iot_mbss_recovery,WDEV_NUM_MAX+1)','wr_iot_mbss_recovery_idle_locked(pAd)'),
 ('include/wr-iot-raw-recovery-free-fence.inc','wr_iot_mbss_recovery_storage_idle(ad->wr_iot_mbss_recovery,WDEV_NUM_MAX+1)','wr_iot_mbss_recovery_idle_locked(ad)'),
 ('os/linux/rt_main_dev.c','wr_iot_mbss_recovery_storage_idle(adapter->wr_iot_mbss_recovery,WDEV_NUM_MAX+1)','wr_iot_mbss_recovery_idle_locked(adapter)')]:one(rel,old,new)
one('include/wr-iot-mbss-open-admission.inc',' if(!record){',' if(!record||!wr_iot_mbss_recovery_idle_locked(adapter)){')
rel='include/wr-iot-netdev-registration.inc';text=(src/rel).read_text()
start=text.index('INT wr_iot_mbss_begin_remove(');end=text.index('\n}',start)+2
body=text[start:end];old=' state=&pAd->wr_iot_mbss[bss];'
assert body.count(old)==1
one(rel,body,body.replace(old,' if(!wr_iot_mbss_recovery_idle_locked(pAd))goto out;\n'+old,1))
restored=dict(changes)
for rel,old,new in reversed(undo):restored[rel]=restored[rel].replace(new,old,1)
assert all(s==(src/rel).read_text() for rel,s in restored.items())
asset='include/wr-iot-mbss-recovery-work.inc'
if (src/asset).exists():p.error('unexpected work helper')
shutil.copytree(src,out)
for rel,s in changes.items():(out/rel).write_text(s)
shutil.copyfile(here/'mbss-recovery-work.inc',out/asset)
for rel in [*changes,asset]:
 digest=hashlib.sha256((out/rel).read_bytes()).hexdigest();m['merged_driver_sha256'][rel]=digest;m['candidate_driver_sha256'][rel]=digest
m.update(production_installed=False,target_compiled=False,runtime_verified=False)
m['mbss_work_binding_layer']={'admission_bound':False,'pci_join_bound':False,'target_compiled':False,'runtime_verified':False}
out.with_name(out.name+'.manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('Staged MBSS work/owner callback with live-work guards; normal admission and PCI joins remain unbound')
