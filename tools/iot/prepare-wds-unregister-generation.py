#!/usr/bin/env python3
"""Stage exact-generation WDS unregister receipt; callback reaper still pending."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new output required')
name='ap/ap_wds.c';raw=(src/name).read_bytes()
if hashlib.sha256(raw).hexdigest()!='8e0bdb003365df0ffd680594979e8f2b14577982c62e1a920dcf97bbe7f0bc87':p.error('unreviewed WDS source')
s=raw.decode();start=s.index('INT WDS_Remove(');end=s.index('\nBOOLEAN WDS_StatsGet(',start);body=s[start:end];original_body=body
old='\tstruct wifi_dev *wdev;';assert body.count(old)==1
body=body.replace(old,old+'\n unsigned long wr_generation=0;')
old='\t\t\tRtmpOSNetDevDetach(wdev->if_dev);';assert body.count(old)==1
capture='            /* Snapshot before unregister while RTNL pins the device. */\n            {\n                ULONG flags;UINT slot;\n                wr_generation=0;\n                RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);\n                for(slot=0;slot<WDEV_NUM_MAX+1;slot++){\n                    const struct wr_iot_interface_ref *r=&pAd->wr_iot_interface_refs[slot];\n                    if(r->device==wdev->if_dev && r->published && r->removing &&\n                       r->phase==WR_REF_IDLE && !r->removal_stage &&\n                       wr_iot_registry_checked_close_terminal(r)){\n                        wr_generation=r->generation;break;\n                    }\n                }\n                RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);\n                if(!wr_generation){RtmpOSNetDevProtect(0);return NDIS_STATUS_FAILURE;}\n            }\n'
body=body.replace(old,capture+old)
old='record->generation, 1);';assert body.count(old)==1
body=body.replace(old,'wr_generation, 1);')
restored=body.replace(capture,'',1).replace('wr_generation, 1);','record->generation, 1);',1).replace('\n unsigned long wr_generation=0;','',1)
assert restored==original_body
changed=s[:start]+body+s[end:]
parent_path=src.with_name(src.name+'.manifest.json')
if parent_path.exists():
 m=json.loads(parent_path.read_text());actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
 assert actual==m['merged_driver_sha256'] and m.get('production_installed') is False
shutil.copytree(src,out);(out/name).write_text(changed)
if parent_path.exists():
 digest=hashlib.sha256((out/name).read_bytes()).hexdigest();m['merged_driver_sha256'][name]=digest;m['candidate_driver_sha256'][name]=digest
 m['production_installed']=False;m['target_compiled']=False;m['runtime_verified']=False
 m['wds_unregister_generation_layer']={'target_compiled':False,'runtime_verified':False}
 out.with_name(out.name+'.manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('Staged pre-unregister generation snapshot; callback retirement remains unbound')
