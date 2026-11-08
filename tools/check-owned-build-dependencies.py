#!/usr/bin/env python3
import importlib.util,tempfile,hashlib,sys
from pathlib import Path
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('owned',Path(__file__).with_name('prepare-owned-build-dependencies.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
for mode in ['download','cached','corrupt','bad_hash','network']:
 with tempfile.TemporaryDirectory(prefix='wr-owned-deps-') as d:
  root=Path(d);directory=root/'trunk/libs/test';directory.mkdir(parents=True);cache=root/'cache';cache.mkdir();digest=hashlib.sha256(b'valid').hexdigest();name='test.tar.gz';archive=cache/(digest+'-'+name)
  if mode in ['cached','corrupt']:archive.write_bytes(b'valid' if mode=='cached' else b'corrupt')
  calls=[]
  def fetch(url,path):
   calls.append(url);path.write_bytes(b'bad' if mode=='bad_hash' else b'valid')
   if mode=='network':raise OSError('injected download failure')
  try:m.seed(root,cache,[{'directory':'trunk/libs/test','filename':name,'sha256':digest,'url':'owned'}],fetch)
  except (ValueError,OSError):assert mode in ['bad_hash','network']
  else:assert mode not in ['bad_hash','network'] and (directory/name).read_bytes()==b'valid'
  assert len(calls)==(0 if mode=='cached' else 1)
  assert not list(cache.glob('*.part'))
print('PASS owned dependency download/cache/corruption/hash/network refusal and partial cleanup')
