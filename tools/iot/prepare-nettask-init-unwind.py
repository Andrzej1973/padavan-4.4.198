#!/usr/bin/env python3
"""Prepare isolated checked network-task initialization and partial unwind."""
import argparse
import hashlib
import re
import shutil
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
src = a.source.resolve(strict=True)
out = a.output.resolve()
if out.exists() or src == out or src in out.parents or out in src.parents:
    p.error('new separate output required')
name = 'os/linux/rt_rbus_pci_drv.c'
raw = (src / name).read_bytes()
if hashlib.sha256(raw).hexdigest() != 'acecc5dc9f9f92f7ad5601e48df3426bb3046c38885a01c498a23ea5d49f54c9':
    p.error('unreviewed predecessor')
for dependency, digest in {
    'os/linux/rt_linux.c': '0a85539938acd21d242ec2f1941fbac0f61f419ff91855ef5798118bee64cbee',
    'include/os/rt_linux_cmm.h': 'effa9f4e64fad8604b9f51cf5443f759d20a72c90247a4001a680d2e12a7d130',
}.items():
    if hashlib.sha256((src / dependency).read_bytes()).hexdigest() != digest:
        p.error('unreviewed OS tasklet allocation/join contract: ' + dependency)
s = raw.decode()
start = s.index('NDIS_STATUS RtmpNetTaskInit(')
end = s.index('\n}', start) + 2
body = s[start:end]
count = body.count('RTMP_OS_TASKLET_INIT(')
if count != 20:
    p.error('changed initialization inventory')
body = body.replace('POS_COOKIE pObj;', '''POS_COOKIE pObj;
 RTMP_NET_TASK_STRUCT *wr_created[20];
 unsigned int wr_count=0;ULONG wr_flags;
 /* Reservation remains held until every successfully initialized object is
  * joined on failure. No producer can submit while this lane is active. */
#ifdef OS_ABL_FUNC_SUPPORT
#define WR_IOT_INIT_ONE(ad,task,func,data) do { \\
 if(!RTMP_OS_TASKLET_INIT(ad,task,func,data))goto wr_init_failed; \\
 wr_created[wr_count++]=(task); \\
 } while(0)
#else
#define WR_IOT_INIT_ONE(ad,task,func,data) do { \\
 RTMP_OS_TASKLET_INIT(ad,task,func,data); \\
 wr_created[wr_count++]=(task); \\
 } while(0)
#endif''', 1)
# Change only the original call sites, leaving the wrappers above intact.
body = re.sub(r'(?m)^(\s*)RTMP_OS_TASKLET_INIT\(pAd,', r'\1WR_IOT_INIT_ONE(pAd,', body)
body = body.replace('return wr_iot_nettask_open(pAd);', '''if(wr_iot_nettask_open(pAd)!=NDIS_STATUS_SUCCESS)goto wr_init_failed;
 return NDIS_STATUS_SUCCESS;
wr_init_failed:
 while(wr_count) {
  RTMP_NET_TASK_STRUCT *wr_task=wr_created[--wr_count];
  RTMP_OS_TASKLET_KILL(wr_task);
 }
 RTMP_IRQ_LOCK(&pAd->wr_iot_nettask_lock,wr_flags);
 pAd->wr_iot_nettask_initializing=0;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_nettask_lock,wr_flags);
 return NDIS_STATUS_FAILURE;
#undef WR_IOT_INIT_ONE''')
shutil.copytree(src, out)
(out / name).write_text(s[:start] + body + s[end:], encoding='utf-8', newline='\n')
print('Prepared checked tasklet init: 20 source sites; reverse partial unwind before reservation release')
