#!/usr/bin/env python3
"""Serialize checked WTBL update and refuse a busy prior command before writes."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
    p.error('new separate output required')
receipt=json.loads(src.with_name(src.name+'-delete-busy-admission.json').read_text())
rel='hw_ctrl/cmm_asic_mt.c';raw=(src/rel).read_bytes()
if hashlib.sha256(raw).hexdigest()!=receipt['output_sha256']:
    p.error('delete-busy predecessor mismatch')
s=raw.decode();start=s.index('INT wr_iot_update_rx_wcid_checked(');end=s.index('\n}',start)+2
body=s[start:end]
lock='#ifdef RTMP_PCI_SUPPORT\n\t\tNdisAcquireSpinLock(&pAd->IndirectUpdateLock);\n#endif'
if body.count(lock)!=2:p.error('unreviewed update lock layout')
body=body.replace(lock,'')
release='#ifdef RTMP_PCI_SUPPORT\n        NdisReleaseSpinLock(&pAd->IndirectUpdateLock);\n#endif'
if body.count(release)!=1:p.error('unreviewed intermediate release')
body=body.replace(release,'',1)
anchor='    if (WCID >= 0) {'
if body.count(anchor)!=1:p.error('unreviewed first write boundary')
gate='''#ifdef RTMP_PCI_SUPPORT
    NdisAcquireSpinLock(&pAd->IndirectUpdateLock);
#endif
    /* Serialized checked update: no WTBL or queue write before admission. */
    RTMP_IO_READ32(pAd, WTBL_OFF_WIUCR, &Value);
    if (Value & IU_BUSY) {
#ifdef RTMP_PCI_SUPPORT
        NdisReleaseSpinLock(&pAd->IndirectUpdateLock);
#endif
        return WR_IOT_WCID_NOT_WRITTEN;
    }
    { /* WCID already validated above. */'''
body=body.replace(anchor,gate,1)
# Restart belongs to the same serialized queue operation even on timeout.
old='''#ifdef RTMP_PCI_SUPPORT
\t\t\tNdisReleaseSpinLock(&pAd->IndirectUpdateLock);
#endif
            //AsicSetMacTxRx(pAd, ASIC_MAC_TX, TRUE);
\t\tMtAsicACQueue(pAd, AC_QUEUE_START, apidx, 0xF);'''
new='''            //AsicSetMacTxRx(pAd, ASIC_MAC_TX, TRUE);
\t\tMtAsicACQueue(pAd, AC_QUEUE_START, apidx, 0xF);
#ifdef RTMP_PCI_SUPPORT
\t\t\tNdisReleaseSpinLock(&pAd->IndirectUpdateLock);
#endif'''
if body.count(old)!=1:p.error('unreviewed queue restart boundary')
body=body.replace(old,new,1)
shutil.copytree(src,out)
(out/rel).write_text(s[:start]+body+s[end:],encoding='utf-8',newline='\n')
out.with_name(out.name+'-update-busy-admission.json').write_text(json.dumps({
 'input_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256((out/rel).read_bytes()).hexdigest(),
 'scope':'PCI checked WTBL update/delete serialization; other aliases/firmware writers and DMA lifetime unproved',
 'target_compiled':False,'production_installed':False,
},indent=2)+'\n')
print('Staged checked WTBL update initial busy refusal and one PCI lock span')
