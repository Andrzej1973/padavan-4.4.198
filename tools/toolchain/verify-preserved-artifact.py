#!/usr/bin/env python3
"""Verify the reviewed source build before copying its artifacts to owned Release."""
import hashlib,importlib.util,json,sys,tarfile
from pathlib import Path
RUN=42467546674
REVISION='5ef6a8577ae24be27d8d81b3fe44a587d8491a16'
ARCHIVES={'mipsel-linux-uclibc-source-candidate.tar.xz','toolchain-build-sources.tar.xz','toolchain-package-sources.tar.xz'}

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def verify(directory,run):
 if (run.get('id')!=RUN or run.get('head_sha')!=REVISION or run.get('conclusion')!='success' or run.get('path')!='.github/workflows/build-owned-toolchain.yml' or run.get('repository',{}).get('full_name')!='Andrzej1973/padavan-4.4.198'):raise ValueError('Unreviewed source workflow provenance')
 report=json.loads((directory/'result.json').read_text())
 spec=importlib.util.spec_from_file_location('installer',Path(__file__).with_name('install-candidate.py'))
 installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)
 installer.validate(report,directory/'mipsel-linux-uclibc-source-candidate.tar.xz')
 if set(report['archives'])!=ARCHIVES:raise ValueError('Missing/unexpected source archives')
 for name,item in report['archives'].items():
  path=directory/name
  if path.is_symlink() or not path.is_file() or path.stat().st_size!=item['bytes'] or digest(path)!=item['sha256']:raise ValueError('Preserved source digest mismatch: '+name)
 with tarfile.open(directory/'mipsel-linux-uclibc-source-candidate.tar.xz') as archive:
  if not any(m.isfile() and m.name.removeprefix('./').startswith('share/licenses/') for m in archive):raise ValueError('Missing compiler license inventory')
 with tarfile.open(directory/'toolchain-build-sources.tar.xz') as archive:
  names={m.name.removeprefix('./') for m in archive}
  if not {'ctng.tar.xz','uClibc-ng-1.0.48.tar.xz','profile.config','effective.config','sources.json'}<=names or not any(n.startswith('source/trunk/linux-4.4.x/') for n in names):raise ValueError('Missing generator/libc/kernel/profile sources')
 # Generate the published manifest from the verified records, not unchecked input.
 (directory/'SHA256SUMS').write_text(''.join(report['archives'][name]['sha256']+'  '+name+'\n' for name in sorted(ARCHIVES)))
 result={'source_run':RUN,'generator_revision':REVISION,'archives':report['archives'],'archive_hashes_verified':True,'license_inventory_present':True,'source_inventory_present':True,'new_compilation_performed':False,'runtime_verified':False,'production_promoted':False}
 (directory/'preservation.json').write_text(json.dumps(result,indent=2)+'\n')
 return result

if __name__=='__main__':
 verify(Path(sys.argv[1]),json.loads(Path(sys.argv[2]).read_text()))
 print('PASS reviewed artifact provenance, all archive hashes, source and license inventory; no rebuild or promotion')
