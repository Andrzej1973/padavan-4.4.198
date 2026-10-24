#!/usr/bin/env python3
"""Stage arithmetic guards only; caller serialization/lifetime is still required."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args(); root=a.source.resolve(); out=a.output.resolve()
if out.exists() or out==root or root in out.parents or out in root.parents:
    raise SystemExit('New separate output required')
name='common/cmm_cfg.c'; data=(root/name).read_bytes()
if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!='cb3e9607326e473436862132b18de9679cc6c154':
    raise SystemExit('Unreviewed counter dispatcher source')
s=data.decode('utf-8')
for command,guard in [('UP','VIRTUAL_IF_NUM(pAd) == (UINT)~0U'),('DOWN','VIRTUAL_IF_NUM(pAd) == 0')]:
    start=s.index('case CMD_RTPRIV_IOCTL_VIRTUAL_INF_'+command+':')
    end=s.index('\n\t\t\tbreak;',start)
    part=s[start:end]
    anchor='RT_CMD_INF_UP_DOWN *pInfConf = (RT_CMD_INF_UP_DOWN *)pData;'
    if part.count(anchor)!=1: raise SystemExit('Changed counter dispatcher anchor')
    addition='\n\t\t\t/* Arithmetic guard only; shared owner must stabilize the count. */\n\t\t\tif ('+guard+')\n\t\t\t\treturn NDIS_STATUS_FAILURE;'
    s=s[:start]+part.replace(anchor,anchor+addition,1)+s[end:]
if (root/name).read_bytes()!=data: raise SystemExit('Source changed')
(out/'common').mkdir(parents=True)
(out/name).write_text(s+'\n#include "wr-iot-virtual-down.inc"\n',encoding='utf-8')
(out/'include').mkdir();(out/'include/wr-iot-virtual-down.inc').write_bytes(Path(__file__).with_name('virtual-down-checked.inc').read_bytes())
(out/name).write_text((out/name).read_text()+'\n#include "wr-iot-netdev-registration.inc"\n',encoding='utf-8')
(out/'include/wr-iot-netdev-registration.inc').write_bytes(Path(__file__).with_name('netdev-registration.inc').read_bytes())
(out/'manifest.json').write_text(json.dumps({'production_installed':False,
 'arithmetic_guards_staged':True,'count_serialization_proven':False,
 'stop_result_propagated':False,'target_compiled':False},indent=2)+'\n')
print('Staged counter bounds; synchronization and mandatory stop remain unresolved')
