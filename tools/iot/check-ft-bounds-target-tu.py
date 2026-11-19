#!/usr/bin/env python3
"""Compile prepared FT parser bounds using actual ft.o Kbuild command.

A separate temporary TU/object only; no driver module or image replacement.
"""
import argparse,hashlib,json,re,runpy,shlex,shutil,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
for name in ('kernel','driver','compiler','output'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();root=a.kernel.resolve();driver=a.driver.resolve();here=Path(__file__).resolve().parent
unwrap=runpy.run_path(str(here/'kbuild-compiler.py'))['unwrap_ccache']
report={'status':'failed','scope':'Prepared common/ft.c bounds and outer association arbitration target TU only','module_installed':False,'runtime_verified':False}
try:
 commands=list(driver.rglob('.ft.o.cmd'))
 if len(commands)!=1:raise RuntimeError('Expected exactly one active FT Kbuild command')
 raw=commands[0].read_bytes();lines=re.findall(r'^cmd_.*? := (.+)$',raw.decode(),re.M)
 if len(lines)!=1:raise RuntimeError('Expected one FT compiler command')
 argv=unwrap(shlex.split(lines[0]));tool=Path(argv[0])
 if any(x in (';','&&','||','|','>','<') for x in argv):raise RuntimeError('Unsupported compiler command')
 if not tool.is_absolute():tool=Path(str(root/tool) if '/' in argv[0] else shutil.which(argv[0]) or '')
 if tool.resolve()!=a.compiler.resolve():raise RuntimeError('FT compiler identity mismatch')
 filtered=[];sources=[];i=1
 while i<len(argv):
  token=argv[i]
  if token in ('-o','-MF','-MT','-MQ'):i+=2;continue
  if token in ('-c','-MD','-MMD','-MP') or token.startswith(('-Wp,-MD,','-Wp,-MMD,')):i+=1;continue
  if token.endswith('.c'):sources.append(token)
  else:filtered.append(token)
  i+=1
 if len(sources)!=1:raise RuntimeError('Expected one FT source')
 source=Path(sources[0]);source=source if source.is_absolute() else root/source
 if source.resolve()!=(driver/'common/ft.c').resolve():raise RuntimeError('Unexpected FT source identity')
 original=source.read_bytes()
 changed=runpy.run_path(str(here/'ft-parser-bounds-composition.py'))['compose'](original.decode())
 changed,_=runpy.run_path(str(here/'ra2-ft-mutation-composition.py'))['compose'](changed)
 include='#include "rt_config.h"'
 if changed.count(include)!=1:raise RuntimeError('FT configuration include changed')
 changed=changed.replace(include,include+'\n#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)\n#include "ra2-mutation-admission-kernel.h"\n#endif',1)
 with tempfile.TemporaryDirectory(prefix='wr-ft-bounds-target-') as td:
  temp=Path(td);candidate=temp/'ft.c';obj=temp/'ft.o';candidate.write_text(changed)
  for name in ('ft-action-bounds.h','ft-ie-span.h','ft-subelement-bounds.h','ft-request-ie-admission.h'):
   shutil.copyfile(here/name,temp/name)
  flags=[str(tool.resolve()),'-I'+str(temp),*filtered,str(candidate)]
  macros=subprocess.run([*flags,'-E','-dM'],cwd=root,text=True,capture_output=True,timeout=60)
  if macros.returncode:raise RuntimeError('Prepared FT preprocessing failed: '+macros.stderr[-2500:])
  required=('DOT11R_FT_SUPPORT','CONFIG_AP_SUPPORT','MT7603','MT_MAC','RTMP_PCI_SUPPORT')
  effective={name:bool(re.search(r'^#define '+name+r'(?:\s|$)',macros.stdout,re.M)) for name in required}
  if not all(effective.values()):raise RuntimeError('FT target features inactive: '+str(effective))
  build=subprocess.run([*flags,'-c','-o',str(obj)],cwd=root,text=True,capture_output=True,timeout=120)
  if build.returncode:raise RuntimeError('Prepared FT target compilation failed: '+build.stderr[-6000:])
  data=obj.read_bytes()
  if data[:6]!=b'\x7fELF\x01\x01' or int.from_bytes(data[18:20],'little')!=8:raise RuntimeError('Expected ELF32 LE MIPS FT object')
  a.output.parent.mkdir(parents=True,exist_ok=True)
  a.output.with_suffix('.macros.txt').write_text(macros.stdout)
  report.update(status='passed',effective_macros=effective,command_sha256=hashlib.sha256(raw).hexdigest(),source_sha256=hashlib.sha256(original).hexdigest(),prepared_source_sha256=hashlib.sha256(changed.encode()).hexdigest(),object_sha256=hashlib.sha256(data).hexdigest(),object_bytes=len(data))
 if source.read_bytes()!=original:raise RuntimeError('Original FT source changed during temporary probe')
except (OSError,RuntimeError,ValueError,subprocess.TimeoutExpired) as error:report['error']=str(error)
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
print(report['status']+' prepared FT bounds MIPS TU; driver/image unchanged')
if report.get('error'):print(report['error'])
raise SystemExit(0 if report['status']=='passed' else 1)
