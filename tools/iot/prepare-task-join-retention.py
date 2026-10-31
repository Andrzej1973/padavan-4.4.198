#!/usr/bin/env python3
"""Preserve task storage on failed join; outer adapter retention still required."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();root=a.source.resolve();out=a.output.resolve()
if out.exists() or out==root or root in out.parents or out in root.parents:raise SystemExit('New separate output required')
name='os/linux/rt_linux.c';data=(root/name).read_bytes()
if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!='db61215d188d82a50f3468747fff871318fc4b72':raise SystemExit('Unreviewed task source')
s=data.decode();old='\t\tStatus = __RtmpOSTaskKill(pTask);\n\t\tRtmpOSTaskFree(pTaskOrg);\n\t\treturn Status;'
new='\t\tStatus = __RtmpOSTaskKill(pTask);\n\t\t/* Failed join must retain task storage for the still-live worker. */\n\t\tif (Status == NDIS_STATUS_SUCCESS)\n\t\t\tRtmpOSTaskFree(pTaskOrg);\n\t\treturn Status;'
if s.count(old)!=1:raise SystemExit('Changed task wrapper')
s=s.replace(old,new,1)
if (root/name).read_bytes()!=data:raise SystemExit('Source changed')
(out/'os/linux').mkdir(parents=True);(out/name).write_text(s,encoding='utf-8')
# WSC is another producer; do not release its buffers/locks after failed join.
wname='common/wsc.c'; wdata=(root/wname).read_bytes()
if hashlib.sha1(b'blob '+str(len(wdata)).encode()+b'\0'+wdata).hexdigest()!='3281fb30199c425e67916ae4796242b6618178ea':raise SystemExit('Unreviewed WSC source')
w=wdata.decode(); signature='BOOLEAN WscThreadExit(RTMP_ADAPTER *pAd)'
start=w.index(signature);end=w.index('\n}',start)+2;f=w[start:end]
old='\tif (ret == NDIS_STATUS_FAILURE)\n\t{\n\t\tDBGPRINT(RT_DEBUG_ERROR, ("kill wsc task failed!\\n"));\n\t}'
new='\tif (ret != NDIS_STATUS_SUCCESS)\n\t{\n\t\tDBGPRINT(RT_DEBUG_ERROR, ("kill wsc task failed!\\n"));\n\t\t/* Worker may still use WSC buffers and locks. */\n\t\treturn FALSE;\n\t}'
if f.count(old)!=1:raise SystemExit('Changed WSC failed-join branch')
w=w[:start]+f.replace(old,new,1)+w[end:]
if (root/wname).read_bytes()!=wdata:raise SystemExit('WSC source changed')
(out/'common').mkdir();(out/wname).write_text(w,encoding='utf-8')
(out/'manifest.json').write_text(json.dumps({'production_installed':False,'failed_join_task_storage_retained':True,'failed_join_wsc_resources_retained':True,'outer_adapter_retention_proven':False,'effective_wrapper_verified':False,'target_compiled':False},indent=2)+'\n')
print('Staged failed-join task storage retention; outer shutdown integration pending')
