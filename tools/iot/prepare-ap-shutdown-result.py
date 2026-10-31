#!/usr/bin/env python3
"""Bind AP shutdown refusal into checked close; legacy outer close still VOID."""
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
pins={
 'ap/ap.c':'87d10f9fc5adb22071ebf7cc7c73c915749acea0e006f961a90d513f2ad8c5df',
 'include/ap.h':'3bd6a3c18b7175f682446e92c5e51111844485bed246eda561d7d8d4d6745582',
 'common/rtmp_init_inf.c':'8b995d6bb9f44be4808bdbb66977f08c3b89500589fd465490cebdb9d20ce3f7',
}
for name,digest in pins.items():
 if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
texts={name:(src/name).read_text() for name in pins}
def one(s,old,new):
 if s.count(old)!=1:p.error('unreviewed anchor: '+old)
 return s.replace(old,new,1)
s=texts['ap/ap.c'];start=s.index('VOID APShutdown(');end=s.index('\n}',start)+2
body=s[start:end].replace('VOID APShutdown(', 'BOOLEAN APShutdown(',1)
body=one(body,'if (!APStop(pAd)) return;', 'if (!APStop(pAd)) return FALSE;')
body=body[:-1]+'\treturn TRUE;\n}'
texts['ap/ap.c']=s[:start]+body+s[end:]
texts['include/ap.h']=one(texts['include/ap.h'],'VOID APShutdown(', 'BOOLEAN APShutdown(')
s=texts['common/rtmp_init_inf.c']
for signature,guard in [
 ('VOID RTMPDrvClose(', 'if (!APShutdown(pAd)) return;'),
 ('INT wr_iot_drv_close_checked(', '''if (!APShutdown(pAd)) {
   /* Earlier shutdown side effects are partial. Do not replay stage zero. */
   RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
   pAd->wr_iot_transition.shutdown_stage=3U;
   RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
   return NDIS_STATUS_FAILURE;
  }'''),
]:
 start=s.index(signature);end=s.index('\n}',start)+2;body=s[start:end]
 body=one(body,'APShutdown(pAd);',guard)
 s=s[:start]+body+s[end:]
texts['common/rtmp_init_inf.c']=s
shutil.copytree(src,out)
for name,text in texts.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
out.with_name(out.name+'-ap-shutdown-result.json').write_text(json.dumps({
 'input_sha256':pins,'output_sha256':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in pins},
 'checked_shutdown_callers':2,'checked_close_refusal_stage':3,
 'scope':'APShutdown result into checked driver close; prior effects and legacy outer close remain',
 'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False,
},indent=2)+'\n',encoding='utf-8')
print('Staged APShutdown result and retained checked-close refusal')
