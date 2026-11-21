#!/usr/bin/env python3
"""Read-only independent ELF/hash audit of a downloaded isolated CI candidate."""
import argparse,hashlib,json,struct,zipfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('archive',type=Path);p.add_argument('--expected-sha256',required=True)
p.add_argument('--output',type=Path,required=True);a=p.parse_args()
digest=hashlib.file_digest(a.archive.open('rb'),'sha256').hexdigest()
if digest!=a.expected_sha256:raise SystemExit('Artifact archive digest mismatch')
with zipfile.ZipFile(a.archive) as z:
 names=z.namelist()
 if len(names)!=len(set(names)):raise SystemExit('Duplicate ZIP member')
 results={}
 for name in names:
  if name.endswith('.ko') or name in ('runtime-link/rc','runtime-link/httpd'):
   data=z.read(name)
   if len(data)<52 or data[:6]!=b'\x7fELF\x01\x01' or struct.unpack('<H',data[18:20])[0]!=8:
    raise SystemExit('Expected ELF32 little endian MIPS: '+name)
   results[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'machine':'MIPS','elf_class':32}
 for name in ('runtime-link/rc','runtime-link/httpd','ra2-no-host-module/mt76x3_ap-ra2-no-host.ko'):
  if name not in results:raise SystemExit('Missing candidate '+name)
 manifest=z.read('runtime-link/candidate.sha256').decode().splitlines()
 for name in ('rc','httpd'):
  matches=[line.split()[0] for line in manifest if line.split()[-1].endswith('/'+name)]
  if matches!=[results['runtime-link/'+name]['sha256']]:raise SystemExit('Candidate hash mismatch: '+name)
 for name in ('rc','httpd'):
  closure=json.loads(z.read('runtime-link/'+name+'-dependency-closure.json'))
  if not closure.get('dependency_closure_verified') or closure.get('errors'):
   raise SystemExit('Dependency closure failed: '+name)
  key='candidate:usr/sbin/'+name
  if closure['elf_files'][key]['sha256']!=results['runtime-link/'+name]['sha256']:
   raise SystemExit('Dependency closure does not describe this binary: '+name)
  if closure.get('production_installed') is not False or closure.get('runtime_verified') is not False:
   raise SystemExit('Unexpected acceptance scope: '+name)
 report={'archive_sha256':digest,'independent_elf_and_hash_check':'PASS','files':results,
         'candidate_dependency_reports_match_binaries':True,'production_installed':False,
         'trx_inclusion_verified':False,'physical_runtime_verified':False,
         'scope':'Isolated candidate compilation only. Final image and device acceptance are separate.'}
 a.output.write_text(json.dumps(report,indent=2)+'\n')
 print('PASS independent candidate ZIP digest, ELF32 little endian MIPS, rc/httpd hashes and dependency report identities; no TRX/device claim')
