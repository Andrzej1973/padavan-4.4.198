#!/usr/bin/env python3
"""Expose reset refusal to direct callers; not an atomic reset or APStop join."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
    p.error('new separate output required')
pins={
 'mgmt/mgmt_entrytb.c':'2876e9cb51ab004b9508ee9645ad204e55b8aeb0086359daf5666e200f377788',
 'include/rtmp.h':'af21f28708b443bf42a33f30f7fdc365d21865d56caf1ffc59b2cb5bd2999bf3',
 'ap/ap.c':'870bc937b71a1647f49dbc069dbda64402f6ef0c1ebdb5afcbfbef34da738c7b',
 'ap/ap_cfg.c':'197e5b6cf873d70164ce74a3fa090d05119fede919e9a460424b447050dda16e',
 'common/cmm_info.c':'7c63c25e3bde70b6965c6cba06b7d8b09c2742fefaddf314ae60f12bfd75463d',
}
for name,digest in pins.items():
    if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:
        p.error('unreviewed predecessor: '+name)
texts={name:(src/name).read_text() for name in pins}
def one(s,old,new):
    if s.count(old)!=1:p.error('unreviewed anchor: '+old)
    return s.replace(old,new,1)
s=texts['mgmt/mgmt_entrytb.c']
for signature in ['VOID MacTableReset(', 'VOID MacTableResetWdev(']:
    start=s.index(signature);end=s.index('\n}',start)+2;body=s[start:end]
    body=one(body,signature,signature.replace('VOID','BOOLEAN',1))
    body=body.replace('return;','return FALSE;')
    if signature=='VOID MacTableReset(':
        pos=body.rindex('return FALSE;')
        body=body[:pos]+body[pos:].replace('return FALSE;','return TRUE;',1)
    else:
        body=body[:-1]+'\treturn TRUE;\n}'
    s=s[:start]+body+s[end:]
texts['mgmt/mgmt_entrytb.c']=s
for name in ['MacTableReset','MacTableResetWdev']:
    texts['include/rtmp.h']=one(texts['include/rtmp.h'],'VOID '+name+'(', 'BOOLEAN '+name+'(')
for call in ['MacTableReset(pAd, 1);','MacTableResetWdev(pAd, wdev_bss);']:
    texts['ap/ap.c']=one(texts['ap/ap.c'],call,'if (!'+call[:-1]+') return;')
texts['ap/ap_cfg.c']=one(texts['ap/ap_cfg.c'],'MacTableReset(pAd, 1);',
                                    'if (!MacTableReset(pAd, 1)) return FALSE;')
s=texts['ap/ap_cfg.c'];start=s.index('INT Set_DisConnectAllSta_Proc(\n');end=s.index('\n}',start)+2
body=s[start:end]
body=one(body,'MacTableDeleteEntry(pAd, pEntry->wcid, pEntry->Addr);',
              'if (!MacTableDeleteEntry(pAd, pEntry->wcid, pEntry->Addr)) return FALSE;')
texts['ap/ap_cfg.c']=s[:start]+body+s[end:]
call='MacTableResetWdev(pAd, pAd->wdev_list[i]);'
if texts['common/cmm_info.c'].count(call)!=2:p.error('unreviewed MAP reset callers')
texts['common/cmm_info.c']=texts['common/cmm_info.c'].replace(call,'if (!'+call[:-1]+') return FALSE;')
# Assert all five direct reset calls are explicitly checked; definitions/prototypes excluded.
for rel,count in [('ap/ap.c',2),('ap/ap_cfg.c',1),('common/cmm_info.c',2)]:
    calls=re.findall(r'if \(!MacTableReset(?:Wdev)?\([^;]+\)\) return(?: FALSE)?;',texts[rel])
    if len(calls)!=count:p.error('direct caller coverage mismatch: '+rel)
shutil.copytree(src,out)
for name,text in texts.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
out.with_name(out.name+'-reset-result.json').write_text(json.dumps({
 'input_sha256':pins,
 'output_sha256':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in pins},
 'direct_reset_callers_checked':5,'disconnect_all_pmf_delete_checked':True,
 'scope':'direct reset result propagation only; prior side effects remain, APStop still VOID',
 'atomic_reset':False,'parent_apstop_result_propagated':False,
 'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False,
},indent=2)+'\n',encoding='utf-8')
print('Staged checked reset results and all five direct reset callers')
