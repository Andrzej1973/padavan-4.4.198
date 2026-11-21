#!/usr/bin/env python3
"""Require explicit auxiliary close completion before unregister (not callback retirement)."""
import argparse,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
specs=[('ap/ap_apcli.c','INT ApCli_Remove(', '5680ab360d551edec64ec85458b18469f4214b1dea7aba70a72b92f1a5275ea5'),
 ('sniffer/sniffer_radiotap.c','INT Monitor_Remove(', '848c3043686e9a2398d7b52c61a820c95ad473d391749b8ff59fcf177bbbd06a')]
changed={}
for name,sig,digest in specs:
 raw=(src/name).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
 s=raw.decode();start=s.index(sig);end=s.index('\n}',start)+2;body=s[start:end]
 anchor='RtmpOSNetDevProtect(1);'
 if body.count(anchor)!=1:p.error('changed remove lock scope')
 body=body.replace(anchor,anchor+'''
            /* unregister does not propagate a failed ndo_stop. Explicitly
             * close first and retain the object if its owner is still live. */
            RtmpOSNetDevClose(wdev->if_dev);
            if (wr_iot_netdev_close_phase_idle(pAd, wdev->if_dev) != NDIS_STATUS_SUCCESS) {
                RtmpOSNetDevProtect(0);
                return NDIS_STATUS_FAILURE;
            }''',1)
 changed[name]=s[:start]+body+s[end:]
shutil.copytree(src,out)
for name,s in changed.items():(out/name).write_text(s,encoding='utf-8',newline='\n')
print('Prepared APCLI/Monitor explicit close guard; callback retirement/free remains unaccepted')
