#!/usr/bin/env python3
"""Reject preservation provenance/content errors before any GitHub publication."""
import copy,importlib.util,io,json,tarfile,tempfile,sys
from pathlib import Path
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('preserver',Path(__file__).with_name('verify-preserved-artifact.py'))
preserver=importlib.util.module_from_spec(spec);spec.loader.exec_module(preserver)

def tar(path,names):
 with tarfile.open(path,'w:xz') as archive:
  for name in names:
   item=tarfile.TarInfo(name);item.size=1;archive.addfile(item,io.BytesIO(b'x'))

def fixture(root,*,license=True,kernel=True):
 tar(root/'mipsel-linux-uclibc-source-candidate.tar.xz',['bin/mipsel-linux-uclibc-gcc']+(['share/licenses/COPYING'] if license else []))
 tar(root/'toolchain-build-sources.tar.xz',['ctng.tar.xz','uClibc-ng-1.0.48.tar.xz','profile.config','effective.config','sources.json']+(['source/trunk/linux-4.4.x/COPYING'] if kernel else []))
 tar(root/'toolchain-package-sources.tar.xz',['gcc.tar.xz'])
 report={'project_revision':preserver.REVISION,'relocation_tested':True,'qemu_user_verified':True,'production_promoted':False,'gcc':'10.5.0','libc':'1.0.48','linux_headers':'4.4.198','archives':{p.name:{'sha256':preserver.digest(p),'bytes':p.stat().st_size} for p in root.glob('*.tar.xz')}}
 (root/'result.json').write_text(json.dumps(report));return report
run={'id':preserver.RUN,'head_sha':preserver.REVISION,'conclusion':'success','path':'.github/workflows/build-owned-toolchain.yml','repository':{'full_name':'Andrzej1973/padavan-4.4.198'}}
with tempfile.TemporaryDirectory(prefix='wr-toolchain-preserve-check-') as tmp:
 root=Path(tmp);fixture(root);assert preserver.verify(root,run)['new_compilation_performed'] is False
 for case in ['run','repo','compiler','hash','archive-set','license','kernel']:
  report=fixture(root,license=case!='license',kernel=case!='kernel');metadata=copy.deepcopy(run)
  if case=='run':metadata['head_sha']='a'*40
  if case=='repo':metadata['repository']['full_name']='unreviewed/repo'
  if case=='compiler':report['libc']='1.0.43'
  if case=='hash':(root/'toolchain-package-sources.tar.xz').write_bytes(b'corrupted')
  if case=='archive-set':report['archives']['../unexpected.tar.xz']={}
  (root/'result.json').write_text(json.dumps(report))
  try:preserver.verify(root,metadata)
  except ValueError:pass
  else:raise AssertionError('Accepted '+case)
print('PASS existing-artifact preservation: reviewed provenance, compiler/hash/archive set/license/kernel refusal, no rebuild')
