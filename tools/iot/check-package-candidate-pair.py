"""Pairing rejects mismatched binaries, closure, policy and kernel evidence."""
from pathlib import Path
import tempfile,runpy,json,hashlib,struct
here=Path(__file__).resolve().parent
module=runpy.run_path(str(here/'package-candidate-pair.py'));build=module['build'];files=module['FILES']
def elf(kind):
 b=bytearray(64);b[:6]=b'\x7fELF\x01\x01';struct.pack_into('<HH',b,16,kind,8);return bytes(b)
with tempfile.TemporaryDirectory(prefix='wr-pair-check-') as d:
 root=Path(d)
 def put(n,b):
  p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 def report(n,r):put(n,json.dumps(r).encode())
 for target,source in files.items():put(source,b'#!/bin/sh\n' if target.endswith('.sh') else elf(1 if target.startswith('driver:') else 2))
 report('ra2-no-host-module/target-result.json',{'target_module_linked':True,'module_sha256':hashlib.sha256(elf(1)).hexdigest(),'production_installed':False,'runtime_verified':False})
 for role in ('rc','httpd'):
  report('runtime-link/'+role+'-dependency-closure.json',{'dependency_closure_verified':True,'errors':[],'production_installed':False,'elf_files':{'candidate:usr/sbin/'+role:{'sha256':hashlib.sha256(elf(2)).hexdigest()}}})
 report('runtime-link/iot-iapp-policy-source.json',{'board':'WR1200JS','iapp_compile_gate_enabled':True,'production_ready':False})
 for n in ['ra2-no-host-module/source-manifest.json','runtime-link/iot-runtime-source.json','runtime-link/iot-restart-entry-source.json']:report(n,{})
 put('ra2-no-host-module/kernel.config',b'# CONFIG_PM is not set\n')
 r=build(root,'a'*40);assert not r['trx_inclusion_verified'] and 'sbin/rc' in r['files']
 mutations=[('runtime-link/rc',elf(1)),('ra2-no-host-module/kernel.config',b'CONFIG_PM=y\n'),('runtime-link/httpd',b'bad ELF'),('runtime-link/iot-iapp-policy-source.json',b'{}'),('ra2-no-host-module/target-result.json',b'{}')]
 for n,blob in mutations:
  previous=(root/n).read_bytes();put(n,blob)
  try:build(root,'a'*40)
  except (ValueError,KeyError):pass
  else:raise AssertionError('Unsafe pair accepted '+n)
  put(n,previous)
 p=root/'runtime-link/rc';p.unlink();p.symlink_to(root/'runtime-link/httpd')
 try:build(root,'a'*40)
 except ValueError:pass
 else:raise AssertionError('symlink accepted')
print('PASS paired package evidence: exact ELF type/hash closure, experimental module and IAPP policy, PM refusal, symlink refusal; synthetic inputs, no target/image claim')
