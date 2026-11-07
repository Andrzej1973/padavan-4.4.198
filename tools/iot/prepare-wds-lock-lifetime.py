#!/usr/bin/env python3
"""Initialize Linux WDS table lock once, before adapter publication."""
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
receipt=json.loads(src.with_name(src.name+'-ageout-transaction.json').read_text())
raw=(src/'ap/ap_wds.c').read_bytes()
if hashlib.sha256(raw).hexdigest()!=receipt['output_sha256']:
    p.error('age-out predecessor mismatch')
init=(src/'common/rtmp_init.c').read_bytes()
pin='b15793fa589af7f316b34f4b134914cf6413a4dbd5616a7fbe9663d990f365be'
if hashlib.sha256(init).hexdigest()!=pin:p.error('unreviewed adapter allocation source')
linux=(src/'include/os/rt_linux.h').read_text()
if 'spin_lock_init((spinlock_t *)(__lock));' not in linux:
    p.error('Linux spinlock implementation not recognized')
allocation='NdisAllocateSpinLock(pAd, &pAd->WdsTabLock);'
s=raw.decode();anchor='\t'+allocation
if s.count(allocation)!=1:p.error('unreviewed WDS lock initialization count')
s=s.replace(anchor,'\t/* WdsTabLock is adapter-owned; never reinitialize a published lock. */',1)
t=init.decode();anchor='\t\tNdisAllocateSpinLock(pAd, &pAd->wr_iot_transition_lock);'
if t.count(anchor)!=1 or allocation in t:p.error('unreviewed adapter lock anchor')
t=t.replace(anchor,'''#ifdef WDS_SUPPORT
\t\t/* Before profile parsing/netdev publication; survives radio reopen. */
\t\tNdisAllocateSpinLock(pAd, &pAd->WdsTabLock);
#endif
'''+anchor,1)
shutil.copytree(src,out)
(out/'ap/ap_wds.c').write_text(s,encoding='utf-8',newline='\n')
(out/'common/rtmp_init.c').write_text(t,encoding='utf-8',newline='\n')
out.with_name(out.name+'-wds-lock-lifetime.json').write_text(json.dumps({
 'input_sha256':{'ap/ap_wds.c':hashlib.sha256(raw).hexdigest(),'common/rtmp_init.c':pin},
 'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ('ap/ap_wds.c','common/rtmp_init.c')},
 'scope':'Linux WDS lock initialization lifetime; not adapter callback quiescence',
 'target_compiled':False,'production_installed':False,
},indent=2)+'\n')
print('Staged once-per-adapter WDS lock initialization')
