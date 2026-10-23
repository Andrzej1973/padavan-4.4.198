#!/usr/bin/env python3
"""Stage balanced failed-open refs for other shared-count users; no installation."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('source',type=Path); p.add_argument('output',type=Path)
a=p.parse_args(); root=a.source.resolve(); out=a.output.resolve()
if out.exists() or out==root or root in out.parents or out in root.parents: raise SystemExit('New separate output required')
blobs={'ap/ap_apcli_inf.c':'73add46acd6928178f707d5b500aa24829c5ed3f','ap/ap_wds_inf.c':'78a2f2b7393d9726cc072c5ca8589e3862b81944'}
outputs={}
for name,blob in blobs.items():
 data=(root/name).read_bytes()
 if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=blob: raise SystemExit('Unreviewed source: '+name)
 text=data.decode(); old='\tif (VIRTUAL_IF_UP(pAd) != 0)\n\t\treturn -1;'
 if text.count(old)!=1: raise SystemExit('Changed failed-open path: '+name)
 outputs[name]=(data,text.replace(old,'\tif (VIRTUAL_IF_UP(pAd) != 0) {\n\t\tRT_MOD_DEC_USE_COUNT();\n\t\treturn -1;\n\t}',1))
for name,(original,text) in outputs.items():
 if (root/name).read_bytes()!=original: raise SystemExit('Source changed')
 target=out/name; target.parent.mkdir(parents=True,exist_ok=True); target.write_text(text,encoding='utf-8')
(out/'manifest.json').write_text(json.dumps({'production_installed':False,'failed_open_module_refs_balanced':True,'shared_owner_bound':False,'target_compiled':False},indent=2)+'\n')
print('Staged AP-client/WDS failed-open ref repair; shared ownership pending')
