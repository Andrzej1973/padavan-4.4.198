"""Resolve local quoted includes without overwriting earlier generated layers."""
import re
from pathlib import Path

def dependencies(local):
 local=Path(local);seen=set();pending=['driver-api-close-bundle.h']
 while pending:
  name=pending.pop()
  if name in seen:continue
  if Path(name).name!=name:raise ValueError('Nonlocal bundle dependency: '+name)
  path=local/name
  if not path.is_file():raise ValueError('Missing bundle dependency: '+name)
  seen.add(name)
  pending.extend(re.findall(r'^\s*#include "([^"]+)"',path.read_text(),re.M))
 return sorted(seen)


def integrate(changes,source,local,main):
 """Return successor edits after resolving all dependencies; no filesystem writes."""
 source=Path(source);local=Path(local)
 closure=dependencies(local)
 bundle=(local/'driver-api-close-bundle.h').read_text()
 direct=re.findall(r'^#include "([^"]+)"$',bundle,re.M)
 if not direct or len(direct)!=len(set(direct)):
  raise ValueError('Invalid direct CLOSE bundle dependencies')
 entry=changes[main];anchor='#include "driver-api-closed-entry.inc"'
 if entry.count(anchor)!=1 or '#include "driver-api-close-bundle.h"' in entry:
  raise ValueError('CLOSE bundle include anchor changed or already integrated')
 result=dict(changes)
 for name in closure:
  if name in ['driver-api-close-bundle.h',*direct] or (
    'include/'+name not in result and not (source/'include'/name).is_file()):
   result['include/'+name]=(local/name).read_text()
 result[main]=entry.replace(anchor,'#include "driver-api-close-bundle.h"\n'+anchor,1)
 return result

def verified_inputs(driver,local,manifest):
 """Snapshot every compiled bundle dependency against the generator manifest."""
 driver=Path(driver);local=Path(local)
 recorded=manifest.get('merged_driver_sha256',{})
 import hashlib
 result={}
 direct=re.findall(r'^#include "([^"]+)"$',(local/'driver-api-close-bundle.h').read_text(),re.M)
 for name in dependencies(local):
  data=(driver/'include'/name).read_bytes()
  if hashlib.sha256(data).hexdigest()!=recorded.get('include/'+name):
   raise ValueError('Compiled bundle manifest drift: '+name)
  if name in ['driver-api-close-bundle.h',*direct] and data!=(local/name).read_bytes():
   raise ValueError('Compiled bundle reviewed source drift: '+name)
  result[name]=data
 return result
