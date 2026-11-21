#!/usr/bin/env python3
"""Fence initialized direct RTMPFreeAdapter before any destructive action."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.source.resolve(strict=True);out=a.output.resolve();here=Path(__file__).resolve().parent
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
m=json.loads(src.with_name(src.name+'.manifest.json').read_text());actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if actual!=m['merged_driver_sha256'] or m.get('production_installed') is not False or 'mbss_owner_storage_layer' not in m:p.error('changed/unsupported input')
changes={};undo=[]
def one(rel,old,new):
 s=changes.get(rel,(src/rel).read_text())
 if s.count(old)!=1:p.error('unreviewed raw-free anchor: '+rel)
 undo.append((rel,old,new));changes[rel]=s.replace(old,new,1)
one('include/rtmp.h',' struct wr_iot_mbss_recovery_owner wr_iot_mbss_recovery[WDEV_NUM_MAX + 1];',' struct wr_iot_mbss_recovery_owner wr_iot_mbss_recovery[WDEV_NUM_MAX + 1];\n unsigned int wr_iot_recovery_storage_live;')
one('common/rtmp_init.c','\t\t\t/* init resource list (must be after pAd allocation) */','\t\t\tpAd->wr_iot_recovery_storage_live=0;\n\t\t\t/* init resource list (must be after pAd allocation) */')
one('common/rtmp_init.c','\t\t*ppAdapter = (VOID *)pAd;','        /* All recovery locks/work/owners/refs are initialized before publication. */\n        WRITE_ONCE(pAd->wr_iot_recovery_storage_live,1);\n\t\t*ppAdapter = (VOID *)pAd;')
one('common/rtmp_init.c','BOOLEAN RtmpRaDevCtrlExit(IN VOID *pAdSrc)', '#include "wr-iot-raw-recovery-free-fence.inc"\nBOOLEAN RtmpRaDevCtrlExit(IN VOID *pAdSrc)')
one('common/rtmp_init.c','\tif (wr_iot_mcu_sender_release_begin(pAd)!=NDIS_STATUS_SUCCESS) return FALSE;', '\tif (!wr_iot_raw_recovery_free_fence(pAd)) return FALSE;\n\tif (wr_iot_mcu_sender_release_begin(pAd)!=NDIS_STATUS_SUCCESS) return FALSE;')
one('os/linux/rt_profile.c','BOOLEAN RTMPFreeAdapter(VOID *pAdSrc)','''#include "wr-iot-raw-recovery-free-fence.inc"
BOOLEAN RTMPFreeAdapter(VOID *pAdSrc)''')
one('os/linux/rt_profile.c','\tif (wr_iot_mcu_sender_release_begin(pAd)!=NDIS_STATUS_SUCCESS) return FALSE;', '\tif (!wr_iot_raw_recovery_free_fence(pAd)) return FALSE;\n\tif (wr_iot_mcu_sender_release_begin(pAd)!=NDIS_STATUS_SUCCESS) return FALSE;')
restored=dict(changes)
for rel,old,new in reversed(undo):restored[rel]=restored[rel].replace(new,old,1)
assert all(s==(src/rel).read_text() for rel,s in restored.items())
asset='include/wr-iot-raw-recovery-free-fence.inc'
if (src/asset).exists():p.error('unexpected raw-free helper')
shutil.copytree(src,out)
for rel,s in changes.items():(out/rel).write_text(s)
shutil.copyfile(here/'raw-recovery-free-fence.inc',out/asset)
for rel in [*changes,asset]:
 digest=hashlib.sha256((out/rel).read_bytes()).hexdigest();m['merged_driver_sha256'][rel]=digest;m['candidate_driver_sha256'][rel]=digest
m.update(production_installed=False,target_compiled=False,runtime_verified=False)
m['raw_recovery_free_fence_layer']={'worker_dispatched':False,'hardware_retirement_proven':False,'target_compiled':False,'runtime_verified':False}
out.with_name(out.name+'.manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('Staged direct-free cold/live recovery fence; hardware/callback proofs remain separate')
