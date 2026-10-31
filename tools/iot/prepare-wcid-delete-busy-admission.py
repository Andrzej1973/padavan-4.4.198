#!/usr/bin/env python3
"""Refuse checked WTBL deletion before writes if a prior command is busy."""
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
receipt=json.loads(src.with_name(src.name+'-hardware-delete-consumer.json').read_text())
if hashlib.sha256((src/'mgmt/mgmt_entrytb.c').read_bytes()).hexdigest()!=receipt['output_sha256']:
    p.error('hardware-consumer predecessor mismatch')
rel='hw_ctrl/cmm_asic_mt.c';raw=(src/rel).read_bytes();s=raw.decode()
if hashlib.sha256(raw).hexdigest()!='f1bdeb46285c750bd9df114c2cc6a9974b66f58bc7849d50378c2729e9e9e602':
    p.error('unreviewed WTBL implementation')
start=s.index('INT wr_iot_delete_wcid_checked(');end=s.index('\n}',start)+2
body=s[start:end]
lock='#ifdef RTMP_PCI_SUPPORT\n\t\tNdisAcquireSpinLock(&pAd->IndirectUpdateLock);\n#endif'
if body.count(lock)!=1:p.error('unreviewed indirect lock layout')
body=body.replace(lock,'',1)
anchor='        dw0->field.wm = 0;'
if body.count(anchor)!=1:p.error('unreviewed first-write setup')
gate='''        /* Do not overwrite an unresolved command from an earlier owner.
         * PCI serialization now spans direct WTBL writes and indirect commands. */
#ifdef RTMP_PCI_SUPPORT
        NdisAcquireSpinLock(&pAd->IndirectUpdateLock);
#endif
        RTMP_IO_READ32(pAd, WTBL_OFF_WIUCR, &Value);
        if (Value & IU_BUSY) {
#ifdef RTMP_PCI_SUPPORT
            NdisReleaseSpinLock(&pAd->IndirectUpdateLock);
#endif
            return wr_iot_wrote ? WR_IOT_WCID_PARTIAL : WR_IOT_WCID_NOT_WRITTEN;
        }

'''
body=body.replace(anchor,gate+anchor,1)
shutil.copytree(src,out)
(out/rel).write_text(s[:start]+body+s[end:],encoding='utf-8',newline='\n')
out.with_name(out.name+'-delete-busy-admission.json').write_text(json.dumps({
 'input_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256((out/rel).read_bytes()).hexdigest(),
 'scope':'checked deletion initial busy refusal and PCI lock span; other WTBL writers/retry safety remain open',
 'target_compiled':False,'production_installed':False,
},indent=2)+'\n')
print('Staged checked WTBL deletion busy refusal before first write')
