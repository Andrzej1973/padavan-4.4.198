#!/usr/bin/env python3
"""Read actual rt_linux.o Kbuild flags; never infer its macros from another TU."""
import argparse,hashlib,json,re,shlex,shutil,subprocess
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--kernel',type=Path,required=True)
p.add_argument('--driver',type=Path,required=True)
p.add_argument('--compiler',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args(); root=a.kernel.resolve(); driver=a.driver.resolve()
report={'status':'unavailable','scope':'actual rt_linux.c preprocessing only','target_driver_compiled':False,'runtime_verified':False}
try:
 commands=list(driver.rglob('.rt_linux.o.cmd'))
 if len(commands)!=1:raise RuntimeError('Expected exactly one rt_linux Kbuild command')
 data=commands[0].read_bytes(); lines=re.findall(r'^cmd_.*? := (.+)$',data.decode(),re.M)
 if len(lines)!=1:raise RuntimeError('Expected one compiler command')
 argv=shlex.split(lines[0])
 if not argv or any(t in (';','&&','||','|','>','<') for t in argv):raise RuntimeError('Invalid compiler command')
 tool=Path(argv[0])
 if not tool.is_absolute():
  resolved=str(root/tool) if '/' in argv[0] else shutil.which(argv[0])
  if not resolved:raise RuntimeError('Compiler not found')
  tool=Path(resolved)
 if tool.resolve()!=a.compiler.resolve():raise RuntimeError('Compiler differs from requested compiler')
 filtered=[];i=1
 while i<len(argv):
  t=argv[i]
  if t in ('-o','-MF','-MT','-MQ'):i+=2;continue
  if t in ('-c','-MD','-MMD','-MP') or t.startswith(('-Wp,-MD,','-Wp,-MMD,')):i+=1;continue
  filtered.append(t);i+=1
 sources=[t for t in filtered if t.endswith('.c')]
 if len(sources)!=1:raise RuntimeError('Expected one source')
 source=Path(sources[0]);source=source if source.is_absolute() else root/source
 if source.resolve()!=(driver/'os/linux/rt_linux.c').resolve():raise RuntimeError('Unexpected translation unit')
 command=[str(tool.resolve()),*filtered,'-E','-dM']
 a.output.parent.mkdir(parents=True,exist_ok=True)
 command_artifact=a.output.with_suffix('.kbuild.cmd')
 macro_artifact=a.output.with_suffix('.macros.txt')
 command_artifact.write_bytes(data)
 report.update(source_command_artifact=str(command_artifact),command_sha256=hashlib.sha256(data).hexdigest(),preprocess_argv=command)
 run=subprocess.run(command,cwd=root,text=True,capture_output=True,timeout=60)
 macro_artifact.write_text(run.stdout,encoding='utf-8')
 report.update(macro_artifact=str(macro_artifact),macro_sha256=hashlib.sha256(macro_artifact.read_bytes()).hexdigest())
 if run.returncode:raise RuntimeError('Preprocess failed: '+run.stderr[-2000:])
 macros={n:bool(re.search(r'^#define '+n+r'(?:[ \t]|$)',run.stdout,re.M)) for n in ('KTHREAD_SUPPORT','OS_ABL_FUNC_SUPPORT','CONFIG_PM','RTMP_TIMER_TASK_SUPPORT','WSC_INCLUDED')}
 report.update(status='complete',macros=macros,command_sha256=hashlib.sha256(data).hexdigest(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_command=str(commands[0]),compiler=str(tool.resolve()))
except (OSError,RuntimeError,ValueError,subprocess.TimeoutExpired) as e:report['error']=str(e)
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(report,indent=2)+'\n')
print(report['status']+' rt_linux task configuration; not runtime proof')
raise SystemExit(0 if report['status']=='complete' else 1)
