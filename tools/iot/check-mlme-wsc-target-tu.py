#!/usr/bin/env python3
"""Compile optional WSC/KTHREAD MLME TU using its actual Kbuild command.

A translation-unit feature regression check, not a linked feature module.
"""
import argparse,hashlib,json,re,shlex,shutil,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
for name in ('kernel','driver','compiler','output'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();root=a.kernel.resolve();driver=a.driver.resolve()
a.output.parent.mkdir(parents=True,exist_ok=True)
report={'status':'failed','scope':'WSC/KTHREAD common/mlme.c TU only','full_feature_module_verified':False,'runtime_verified':False}
try:
 files=list(driver.rglob('.mlme.o.cmd'))
 if len(files)!=1:raise RuntimeError('Expected one MLME Kbuild command')
 raw=files[0].read_bytes();lines=re.findall(r'^cmd_.*? := (.+)$',raw.decode(),re.M)
 if len(lines)!=1:raise RuntimeError('Expected one compiler command')
 argv=shlex.split(lines[0])
 if not argv or any(t in (';','&&','||','|','>','<') for t in argv):raise RuntimeError('Unsupported compiler command')
 tool=Path(argv[0]);tool=tool if tool.is_absolute() else Path(str(root/tool) if '/' in argv[0] else shutil.which(argv[0]) or '')
 if tool.resolve()!=a.compiler.resolve():raise RuntimeError('Compiler identity mismatch')
 filtered=[];i=1
 while i<len(argv):
  t=argv[i]
  if t in ('-o','-MF','-MT','-MQ'):i+=2;continue
  if t in ('-c','-MD','-MMD','-MP') or t.startswith(('-Wp,-MD,','-Wp,-MMD,')):i+=1;continue
  if re.match(r'^-[DU](WSC_INCLUDED|WSC_AP_SUPPORT|KTHREAD_SUPPORT)(?:=|$)',t):i+=1;continue
  filtered.append(t);i+=1
 sources=[t for t in filtered if t.endswith('.c')]
 if len(sources)!=1:raise RuntimeError('Expected one source')
 source=Path(sources[0]);source=source if source.is_absolute() else root/source
 if source.resolve()!=(driver/'common/mlme.c').resolve():raise RuntimeError('Unexpected source identity')
 defines=['-DWSC_INCLUDED','-DWSC_AP_SUPPORT','-DKTHREAD_SUPPORT']
 report.update(command_sha256=hashlib.sha256(raw).hexdigest(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),requested_defines=defines)
 with tempfile.TemporaryDirectory(prefix='wr-mlme-wsc-tu-') as tmp:
  obj=Path(tmp)/'mlme-wsc.o'
  command=[str(tool.resolve()),*defines,*filtered,'-c','-o',str(obj)]
  run=subprocess.run(command,cwd=root,text=True,capture_output=True,timeout=120)
  if run.returncode:
   sys.stderr.write(run.stdout+run.stderr)
   raise RuntimeError('WSC/KTHREAD MLME target compilation failed')
  data=obj.read_bytes()
  if data[:6]!=b'\x7fELF\x01\x01' or int.from_bytes(data[18:20],'little')!=8:raise RuntimeError('Expected ELF32 little-endian MIPS object')
  report.update(status='passed',object_sha256=hashlib.sha256(data).hexdigest(),object_bytes=len(data))
except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as e:report['error']=str(e)
a.output.write_text(json.dumps(report,indent=2)+'\n')
print(report['status']+' WSC/KTHREAD MLME target TU; full feature link/runtime unverified')
raise SystemExit(0 if report['status']=='passed' else 1)
