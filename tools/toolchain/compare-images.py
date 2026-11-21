#!/usr/bin/env python3
"""Compare exact-source control/candidate image evidence; never promote automatically."""
import json,sys
from pathlib import Path

def compare(a,b,review=None):
 if a['source_sha']!=b['source_sha']:raise ValueError('Different firmware source revisions')
 if (a['variant'],b['variant'])!=('pinned','source'):raise ValueError('Wrong lanes')
 if a['target']!=b['target'] or a['target']!='mipsel-linux-uclibc':raise ValueError('Different target ABI')
 config_equal={n:v['sha256'] for n,v in a['configs'].items()}=={n:v['sha256'] for n,v in b['configs'].items()}
 missing=sorted(set(a['elf_files'])-set(b['elf_files']));added=sorted(set(b['elf_files'])-set(a['elf_files']))
 reviewed=[]
 if review is not None:
  expected={f'lib/{name}-1.0.43.so':f'lib/{name}-1.0.48.so' for name in ['ld-uClibc','libthread_db','libuClibc']}
  if review.get('schema')!=1 or review.get('passed') is not True or review.get('source_sha')!=a['source_sha'] or review.get('control_images')!=a['images'] or review.get('source_images')!=b['images']:raise ValueError('Unmatched libc review evidence')
  pairs=review.get('pairs',[])
  if len(pairs)!=3 or {v['control']:v['source'] for v in pairs}!=expected:raise ValueError('Unreviewed libc rename set')
  for lane,r in [('control',a),('source',b)]:
   closure=review.get('closure',{}).get(lane,{})
   if closure.get('errors')!=[] or closure.get('elf_count')!=len(r['elf_files']):raise ValueError('Missing complete image closure')
  for pair in pairs:
   old,new=pair['control'],pair['source']
   if pair.get('abi_equal') is not True or pair.get('removed_exports')!=[] or a['elf_files'][old]['abi']!=b['elf_files'][new]['abi']:raise ValueError('Renamed libc ABI/export drift')
   reviewed.append(pair)
  missing=[n for n in missing if n not in expected]
  added=[n for n in added if n not in expected.values()]
 abi_changed=sorted(n for n in a['elf_files'].keys()&b['elf_files'].keys() if a['elf_files'][n].get('abi')!=b['elf_files'][n].get('abi'))
 return {'reviewed_libc_renames':reviewed,'abi_changed':abi_changed,'source_sha':a['source_sha'],'config_equal':config_equal,'missing_elf':missing,'added_elf':added,'changed_elf':[n for n in a['elf_files'].keys()&b['elf_files'].keys() if a['elf_files'][n]['sha256']!=b['elf_files'][n]['sha256']],'control_images':a['images'],'source_images':b['images'],'control_compiler':a['compiler'],'source_compiler':b['compiler'],'software_comparison_passed':config_equal and not missing and not added and not abi_changed,'runtime_verified':False,'production_promoted':False,'remaining':['Review software evidence before development compiler selection; retain pinned control','Physical runtime acceptance deferred until IoT and new WebUI are ready']}
if __name__=='__main__':
 r=compare(json.loads(Path(sys.argv[1]).read_text()),json.loads(Path(sys.argv[2]).read_text()),json.loads(Path(sys.argv[4]).read_text()) if len(sys.argv)>4 else None);Path(sys.argv[3]).write_text(json.dumps(r,indent=2)+'\n')
 if not r['software_comparison_passed']:raise SystemExit('Configuration or ELF inclusion drift: review comparison report')
 print('PASS same-source/config and ELF inclusion comparison; development promotion requires software review; physical runtime remains unverified')
