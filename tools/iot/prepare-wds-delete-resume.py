#!/usr/bin/env python3
"""Add explicit NOT_WRITTEN-only WDS delete checkpoint entry; no automatic worker."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
    p.error('new separate output required')
receipt=json.loads(src.with_name(src.name+'-update-busy-admission.json').read_text())
if hashlib.sha256((src/'hw_ctrl/cmm_asic_mt.c').read_bytes()).hexdigest()!=receipt['output_sha256']:
    p.error('update busy predecessor mismatch')
rel='mgmt/mgmt_entrytb.c';raw=(src/rel).read_bytes()
if hashlib.sha256(raw).hexdigest()!='aa793d442d08be48c0db0df75ee56d89b6f65b89a3730b12de939ac4b7351db2':
    p.error('unreviewed deletion source')
s=raw.decode();signature='BOOLEAN MacTableDeleteEntry(RTMP_ADAPTER *pAd, USHORT wcid, UCHAR *pAddr)'
start=s.index(signature);end=s.index('\n}',start)+2;body=s[start:end]
body=body.replace(signature,'''static BOOLEAN wr_iot_mac_delete_entry(RTMP_ADAPTER *pAd, USHORT wcid, UCHAR *pAddr,
 const void *wr_resume_device, unsigned long wr_resume_generation, unsigned long wr_resume_serial)''',1)
anchor='\tstruct wifi_dev *wdev = NULL;'
if body.count(anchor)!=1:p.error('unreviewed deletion locals')
body=body.replace(anchor,anchor+'''
#if defined(MT_MAC) && defined(WDS_SUPPORT)
 struct wr_iot_interface_ref *wr_resume_owner = NULL;
#endif''',1)
anchor='#include "wr-iot-wds-peer-delete-gate.inc"'
if body.count(anchor)!=1:p.error('unreviewed deletion gate')
body=body.replace(anchor,'#include "wr-iot-wds-delete-resume-admission.inc"\n'+anchor,1)
anchor='#include "wr-iot-wds-hardware-delete-result.inc"'
if body.count(anchor)!=1:p.error('unreviewed hardware checkpoint')
body=body.replace(anchor,'''#if defined(MT_MAC) && defined(WDS_SUPPORT)
wr_iot_wds_hardware_checkpoint: ;
#endif
'''+anchor,1)
anchor='\tNdisReleaseSpinLock(&pAd->MacTabLock);\n\t/*Update TX burst'
if body.count(anchor)!=1:p.error('unreviewed final unlock')
finish='''#if defined(MT_MAC) && defined(WDS_SUPPORT)
 if (wr_resume_owner) {
  ULONG wr_flags;
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, wr_flags);
  if (IS_ENTRY_NONE(pEntry) && !READ_ONCE(tr_entry->enq_cap) && !READ_ONCE(tr_entry->deq_cap) &&
      wr_resume_owner->device == wr_resume_device && wr_resume_owner->generation == wr_resume_generation)
   (void)wr_iot_wds_retirement_software_done(&wr_resume_owner->peer_operation, wr_resume_serial);
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, wr_flags);
 }
#endif
'''
body=body.replace(anchor,finish+anchor,1)
wrappers='''

BOOLEAN MacTableDeleteEntry(RTMP_ADAPTER *pAd, USHORT wcid, UCHAR *pAddr)
{
 return wr_iot_mac_delete_entry(pAd, wcid, pAddr, NULL, 0, 0);
}
#if defined(MT_MAC) && defined(WDS_SUPPORT)
/* Caller must retain adapter/netdev lifetime. This entry does not clear the
 * WDS slot or release the radio reservation; exact completion still required. */
BOOLEAN wr_iot_wds_resume_delete(RTMP_ADAPTER *pAd, USHORT wcid, UCHAR *pAddr,
 const void *device, unsigned long generation, unsigned long serial)
{
 if (!pAd || !pAddr || !device || !generation || !serial) return FALSE;
 return wr_iot_mac_delete_entry(pAd, wcid, pAddr, device, generation, serial);
}
#endif
'''
header=(src/'include/rtmp.h').read_text();anchor=signature+';'
if header.count(anchor)!=1:p.error('unreviewed public deletion prototype')
header=header.replace(anchor,anchor+'''
#if defined(MT_MAC) && defined(WDS_SUPPORT)
BOOLEAN wr_iot_wds_resume_delete(RTMP_ADAPTER *pAd, USHORT wcid, UCHAR *pAddr,
 const void *device, unsigned long generation, unsigned long serial);
#endif''',1)
shutil.copytree(src,out)
(out/rel).write_text(s[:start]+body+wrappers+s[end:],encoding='utf-8',newline='\n')
(out/'include/rtmp.h').write_text(header,encoding='utf-8',newline='\n')
for local,target in [('wds-peer-operation.h','wds-peer-operation.h'),('wds-delete-resume-admission.inc','wr-iot-wds-delete-resume-admission.inc')]:
    shutil.copyfile(Path(__file__).with_name(local),out/'include'/target)
out.with_name(out.name+'-delete-resume.json').write_text(json.dumps({
 'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in (rel,'include/rtmp.h','include/wds-peer-operation.h','include/wr-iot-wds-delete-resume-admission.inc')},
 'scope':'explicit NOT_WRITTEN resume entry; no caller worker/slot finalizer or PARTIAL replay',
 'target_compiled':False,'production_installed':False,
},indent=2)+'\n')
print('Staged explicit NOT_WRITTEN-only WDS hardware checkpoint continuation')
