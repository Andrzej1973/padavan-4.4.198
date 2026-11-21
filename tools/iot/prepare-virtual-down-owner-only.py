#!/usr/bin/env python3
"""Reject unused unclaimed DOWN API; keep direct checked ticket path intact."""
import argparse,hashlib,re,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
for f in src.rglob('*.c'):
 if re.search(rb'\bVIRTUAL_IF_DOWN\s*\(',f.read_bytes()):p.error('unmigrated DOWN caller: '+str(f))
name='common/cmm_cfg.c';raw=(src/name).read_bytes()
if hashlib.sha256(raw).hexdigest()!='4d2f0626b37123be41f74fa9e84a47abe5c8954803ab141b7f3eb050af343e47':p.error('unreviewed dispatcher predecessor')
s=raw.decode();begin=s.index('case CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN:');end=s.index('case CMD_RTPRIV_IOCTL_VIRTUAL_INF_GET:',begin)
body='''case CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN:
            /* WR_IOT_OWNER_ONLY_DOWN: logical/physical DOWN must use
             * wr_iot_virtual_down_checked with its live exact ticket. */
            return NDIS_STATUS_FAILURE;

        '''
shutil.copytree(src,out);(out/name).write_text(s[:begin]+body+s[end:],encoding='utf-8',newline='\n')
print('Rejected unclaimed legacy DOWN; direct checked-ticket function unchanged')
