#!/usr/bin/env python3
"""Propagate APCLI/Monitor family-close failure before generic DOWN and pin release."""
import argparse,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
specs=[('ap/ap_apcli_inf.c','INT ApCli_VirtualIF_Close(',
 'cc741c101e7e5510a7122e7ffabe26ab71f4457b6fdb7ba9b159e60ad446767b',
 'RTMP_AP_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_APC_CLOSE, 0, dev_p, 0);'),
 ('os/linux/rt_profile.c','INT Monitor_VirtualIF_Close(',
 'c7b7566a915b78bf48059836a30b301289db7bc7319c818a52266ba207b60103',
 'RTMP_COM_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_SNIFF_CLOSE, 0, dev_p, 0);')]
changed={}
for name,sig,digest,call in specs:
 raw=(src/name).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
 s=raw.decode();start=s.index(sig);end=s.index('\n}',start)+2;body=s[start:end]
 if body.count(call)!=1:p.error('changed family-close call')
 body=body.replace(call,'if ('+call[:-1]+' != NDIS_STATUS_SUCCESS) return -EBUSY;',1)
 changed[name]=s[:start]+body+s[end:]
shutil.copytree(src,out)
for name,s in changed.items():(out/name).write_text(s,encoding='utf-8',newline='\n')
print('Prepared family-close failure propagation; no automatic replay/recovery binding')
