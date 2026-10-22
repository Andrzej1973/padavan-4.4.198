#!/usr/bin/env python3
"""Merge reviewed MBSS functions, never overwrite another whole-file candidate."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.input.resolve();out=a.output.resolve()
if out.exists() or out==src or src in out.parents or out in src.parents:
    raise SystemExit('Separate new output required')
data=src.read_bytes();original=data.decode()
blob='92d3b01b7be6dd7bcdfe2bc8fbc74b6838ac3b9f'
if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=blob:
    raise SystemExit('Unreviewed MBSS source')
here=Path(__file__).resolve().parent
signatures={
 'init':['VOID MBSS_Init(RTMP_ADAPTER *pAd, RTMP_OS_NETDEV_OP_HOOK *pNetDevOps)'],
 'open-state':['INT32 MBSS_Open(PNET_DEV pDev)'],
 'close':['INT MBSS_Close(PNET_DEV pDev)'],
 'cr':['INT32 mbss_cr_enable(PNET_DEV pDev)','INT mbss_cr_disable(PNET_DEV pDev)'],
}
def function(text,signature):
    if text.count(signature)!=1:raise SystemExit('Changed/duplicated function '+signature)
    start=text.index(signature);end=text.index('\n}',start)+2
    return text[start:end]
out.mkdir(parents=True);stages={};tool_hashes={}
for group in signatures:
    script=here/('prepare-mbss-'+group+'-check.py');tool=script.read_bytes()
    stage=out/group;stage.mkdir()
    subprocess.run([sys.executable,str(script),str(src),str(stage/'candidate.c'),str(stage/'check.c')],check=True)
    if script.read_bytes()!=tool:raise SystemExit('Generator changed during preparation')
    tool_hashes[script.name]=hashlib.sha256(tool).hexdigest()
    stages[group]=(stage/'candidate.c').read_text()
merged=stages['init']
for group in ('open-state','close','cr'):
    remainder=stages[group]
    for signature in signatures[group]:
        old=function(original,signature);new=function(stages[group],signature)
        if merged.count(old)!=1:raise SystemExit('Conflicting function edit: '+signature)
        merged=merged.replace(old,new,1);remainder=remainder.replace(new,old,1)
    if remainder!=original:raise SystemExit('Unreviewed edits outside selected functions')
target=out/'ap/ap_mbss.c';target.parent.mkdir();target.write_text(merged,encoding='utf-8')
fixtures=[]
for group,items in signatures.items():
    fixture=(out/group/'check.c').read_text()
    for signature in items:
        old=function(fixture,signature);new=function(merged,signature)
        fixture=fixture.replace(old,new,1)
    check=out/('check-'+group+'.c');check.write_text(fixture,encoding='utf-8')
    fixtures.append({'path':check.name,'sha256':hashlib.sha256(check.read_bytes()).hexdigest()})
if src.read_bytes()!=data:raise SystemExit('Original source changed')
(out/'manifest.json').write_text(json.dumps({
 'original_git_blob':blob,'candidate_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
 'fixtures':fixtures,'preparers':tool_hashes,'production_installed':False,
 'target_compiled':False,'rf_quiescence_proven':False,'runtime_verified':False,
 'bss_allocation_strategy':None,
},indent=2)+'\n',encoding='utf-8')
print('Merged MBSS init/close/CR candidates and re-extracted final functions into fixtures; no production installation')
