#!/usr/bin/env python3
"""Make MacTabLock adapter-owned; does not prove adapter retirement or clears."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'common/rtmp_init.c':'3cb9c71713b12fbc4c1a80a743bbbb51ca7ba72bc3b7e9fc82c85425252fdc95',
 'ap/ap.c':'2c39a0bec01a1d31d96bfbfebcc0e0df16b3df5f38b22dab2fc4929262691d1a',
 'os/linux/rt_profile.c':'3c5ae56ba5c25e1defc38ccb3261302d0f297b20ee77f949a52e96d213e5beb0'}
texts={}
for name,digest in pins.items():
 if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
 texts[name]=(src/name).read_text()
def one(s,old,new):
 if s.count(old)!=1:p.error('unreviewed anchor: '+old)
 return s.replace(old,new,1)
alloc='NdisAllocateSpinLock(pAd, &pAd->MacTabLock);'
free='NdisFreeSpinLock(&pAd->MacTabLock);'
s=one(texts['common/rtmp_init.c'],alloc,'/* MacTabLock survives UserCfgInit/reopen. */')
s=one(s,free,'/* MacTabLock retired only with the adapter. */')
s=one(s,'/* Last nonfailing initialization before adapter publication. */',
 '/* Last nonfailing initialization before adapter publication. */\n\t\t'+alloc)
texts['common/rtmp_init.c']=s
texts['ap/ap.c']=one(texts['ap/ap.c'],free,'/* MacTabLock remains valid for retained owners and reopen. */')
texts['os/linux/rt_profile.c']=one(texts['os/linux/rt_profile.c'],
 'NdisFreeSpinLock(&pAd->wr_iot_transition_lock);',free+'\n\tNdisFreeSpinLock(&pAd->wr_iot_transition_lock);')
shutil.copytree(src,out)
for name,s in texts.items():(out/name).write_text(s,encoding='utf-8',newline='\n')
out.with_name(out.name+'-peer-lock-lifetime.json').write_text(json.dumps({
 'input_sha256':pins,'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in pins},
 'scope':'single fresh adapter MacTabLock initialization and final teardown only',
 'full_table_clear_owner_bound':False,'adapter_retirement_proven':False,
 'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False},indent=2)+'\n',encoding='utf-8')
print('Staged adapter-owned MacTabLock; clears and retirement still unaccepted')
