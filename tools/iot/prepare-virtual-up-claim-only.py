#!/usr/bin/env python3
"""Reject unclaimed virtual UP after migrating all in-tree source callers."""
import argparse,hashlib,re,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
for f in src.rglob('*.c'):
 if re.search(rb'\bVIRTUAL_IF_UP\s*\(',f.read_bytes()):p.error('unmigrated C caller: '+str(f))
name='common/cmm_cfg.c';raw=(src/name).read_bytes()
if hashlib.sha256(raw).hexdigest()!='b396db70d1edd8ed3aa16f50d00ddead726dce272e8ac0da26aca71f37aae214':p.error('unreviewed dispatcher predecessor')
s=raw.decode();start=s.index('case CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP:');end=s.index('case CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN:',start)
body=s[start:end];marker='\t\t\t/* Arithmetic guard only; shared owner must stabilize the count. */'
if body.count(marker)!=1:p.error('changed unclaimed fallback')
body=body[:body.index(marker)]+'''            /* WR_IOT_CLAIM_ONLY_UP: legacy zero-owner requests cannot mutate
             * count, start hardware or regenerate beacons. */
            return NDIS_STATUS_FAILURE;
        }
            break;

        '''
anchor='RT_CMD_INF_UP_DOWN *pInfConf = (RT_CMD_INF_UP_DOWN *)pData;'
if body.count(anchor)!=1:p.error('changed request cast')
body=body.replace(anchor,anchor+'\n            if (!pInfConf) return NDIS_STATUS_FAILURE;',1)
shutil.copytree(src,out);(out/name).write_text(s[:start]+body+s[end:],encoding='utf-8',newline='\n')
print('Rejected zero-owner virtual UP; native/OS_ABL target ABI remains uncompiled')
