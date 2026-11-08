#!/usr/bin/env python3
"""Compare exact-source control/candidate image evidence; never promote automatically."""
import json,sys
from pathlib import Path

def compare(a,b):
 if a['source_sha']!=b['source_sha']:raise ValueError('Different firmware source revisions')
 if (a['variant'],b['variant'])!=('pinned','source'):raise ValueError('Wrong lanes')
 if a['target']!=b['target'] or a['target']!='mipsel-linux-uclibc':raise ValueError('Different target ABI')
 config_equal=all(a['configs'][n]['sha256']==b['configs'][n]['sha256'] for n in a['configs'])
 missing=sorted(set(a['elf_files'])-set(b['elf_files']));added=sorted(set(b['elf_files'])-set(a['elf_files']))
 abi_changed=sorted(n for n in a['elf_files'].keys()&b['elf_files'].keys() if a['elf_files'][n].get('abi')!=b['elf_files'][n].get('abi'))
 return {'abi_changed':abi_changed,'source_sha':a['source_sha'],'config_equal':config_equal,'missing_elf':missing,'added_elf':added,'changed_elf':[n for n in a['elf_files'].keys()&b['elf_files'].keys() if a['elf_files'][n]['sha256']!=b['elf_files'][n]['sha256']],'control_images':a['images'],'source_images':b['images'],'control_compiler':a['compiler'],'source_compiler':b['compiler'],'software_comparison_passed':config_equal and not missing and not added and not abi_changed,'runtime_verified':False,'production_promoted':False,'remaining':['Review full per-file ELF ABI/NEEDED reports and libc ownership','Physical router acceptance under separate authorization before default promotion']}
if __name__=='__main__':
 r=compare(json.loads(Path(sys.argv[1]).read_text()),json.loads(Path(sys.argv[2]).read_text()));Path(sys.argv[3]).write_text(json.dumps(r,indent=2)+'\n')
 if not r['software_comparison_passed']:raise SystemExit('Configuration or ELF inclusion drift: review comparison report')
 print('PASS same-source/config and ELF inclusion comparison; promotion remains blocked pending ABI review and physical acceptance')
