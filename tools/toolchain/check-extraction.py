#!/usr/bin/env python3
"""Real nested link regression from A/B 42476812968 and hostile tar cases."""
import importlib.util
import io
from pathlib import Path
import sys
import tarfile
import tempfile

sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('installer',Path(__file__).with_name('install-candidate.py'))
installer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

def member(name,kind=tarfile.REGTYPE,target=''):
 item=tarfile.TarInfo(name);item.type=kind;item.linkname=target
 return item

def extract(root,items):
 stream=io.BytesIO()
 with tarfile.open(fileobj=stream,mode='w') as archive:
  for item in items:archive.addfile(item)
 stream.seek(0)
 with tarfile.open(fileobj=stream) as archive:
  archive.extractall(root,filter=installer.candidate_filter)

with tempfile.TemporaryDirectory(prefix='wr-toolchain-extraction-') as temporary:
 root=Path(temporary)
 good=root/'valid';good.mkdir()
 # Exact member and target from the hash-verified source compiler artifact.
 name='lib/bfd-plugins/liblto_plugin'
 target='../../libexec/gcc/mipsel-linux-uclibc/10.5.0/liblto_plugin'
 extract(good,[member(name,tarfile.SYMTYPE,target),member('bin/gcc'),member('bin/cc',tarfile.LNKTYPE,'bin/gcc')])
 assert (good/name).is_symlink() and (good/name).readlink()==Path(target)
 assert (good/name).resolve().is_relative_to(good)
 assert (good/'bin/cc').stat().st_ino==(good/'bin/gcc').stat().st_ino
 bad_cases=[
  [member('../escaped')],
  [member('x',tarfile.SYMTYPE,'/etc/passwd')],
  [member('nested/x',tarfile.SYMTYPE,'../../escaped')],
  [member('x',tarfile.LNKTYPE,'../escaped')],
  [member('x',tarfile.LNKTYPE,'/etc/passwd')],
  [member('device',tarfile.CHRTYPE)],
  [member('.',tarfile.SYMTYPE,'.')],
  # Follow the actual parent symlink, not a lexical normalization of the path.
  [member('parent',tarfile.SYMTYPE,'.'),member('parent/x',tarfile.SYMTYPE,'../escaped')],
  [member('parent',tarfile.SYMTYPE,'..'),member('parent/escaped')],
 ]
 for i,items in enumerate(bad_cases):
  dest=root/str(i);dest.mkdir()
  try:extract(dest,items)
  except tarfile.FilterError:pass
  else:raise AssertionError('Unsafe archive accepted: '+str(i))
 assert not (root/'escaped').exists()
 print('PASS real nested symlink, hardlink semantics; traversal, absolute/escaping links, symlink-parent escape and devices rejected')
