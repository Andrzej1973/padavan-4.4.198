"""Verify provider/caller link evidence without relying on exported dynsym names."""
import argparse
import hashlib
import json
from pathlib import Path
import re
SYMBOL='wr_iot_generation_profile_request'
INPUTS=('generation-selector-store-symbols.txt','generation-selector-caller-relocations.txt','rc-link-map.txt')
def verify(root,binary):
 def read(name):
  path=root/name
  if path.is_symlink() or not path.is_file():raise ValueError('Missing/linked selector evidence: '+name)
  return path.read_bytes()
 blobs={name:read(name) for name in INPUTS}
 symbols=blobs[INPUTS[0]].decode()
 if not any(row.split()[-2:]==['T',SYMBOL] for row in symbols.splitlines()):
  raise ValueError('Saved store must define a strong selector')
 relocations=blobs[INPUTS[1]].decode()
 if not re.search(r'\bR_[A-Z0-9_]+\s+'+SYMBOL+r'(?:\s|[-+]|$)',relocations):
  raise ValueError('Ralink caller relocation to selector missing')
 linkmap=blobs[INPUTS[2]].decode()
 marker='Cross Reference Table'
 if linkmap.count(marker)!=1:raise ValueError('Unique linker cross-reference table required')
 files=[];found=False
 for line in linkmap.split(marker,1)[1].splitlines():
  match=re.match('^'+SYMBOL+r'\s+(.+?)\s*$',line)
  if match:
   if found:raise ValueError('Duplicate selector cross-reference')
   found=True;files.append(match.group(1));continue
  if found:
   if line[:1].isspace() and line.strip():files.append(line.strip())
   else:break
 names=[Path(name).name for name in files]
 if not names or names[0]!='wr-iot-saved-config-store.o' or 'ralink.o' not in names[1:]:
  raise ValueError('Selector must resolve from saved store to Ralink caller: '+repr(names))
 if binary.is_symlink() or not binary.is_file():raise ValueError('Regular linked RC required')
 return {'selector_link_provider_verified':True,'selector_caller_relocation_verified':True,
         'selector_object_strong_definition_verified':True,'definition_object':names[0],
         'caller_object':'ralink.o','rc_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
         'input_sha256':{n:hashlib.sha256(b).hexdigest() for n,b in blobs.items()},
         'production_installed':False,'runtime_verified':False}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('results',type=Path)
 p.add_argument('--binary',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise SystemExit('Selector report already exists')
 a.output.write_text(json.dumps(verify(a.results,a.binary),indent=2)+'\n')
 print('PASS selector strong object/caller relocation/linker provider and RC hash; no runtime acceptance')
