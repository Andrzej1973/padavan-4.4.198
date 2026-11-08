#!/usr/bin/env python3
"""Compile staged CLOSE bindings with the actual rt_main_dev Kbuild flags; no ioctl installation."""
import argparse,hashlib,json,re,shlex,shutil,subprocess,tempfile
from pathlib import Path

def probe_source(driver,local):
 files=[driver/'os/linux/rt_main_dev.c',local/'driver-api-close-finish.h',
        local/'driver-api-close-recovery.h',local/'driver-api-close-enter.inc',
        local/'driver-api-close-finish-binding.inc',local/'driver-api-close-recovery-binding.inc',
        local/'driver-api-close-finish-recovery.inc',local/'driver-api-close-entry.inc']
 if any('"' in str(f) or '\n' in str(f) for f in files):raise ValueError('Unsupported include path')
 return '#include <linux/module.h>\n'+''.join('#include "'+str(f)+'"\n' for f in files)+'''
int wr_iot_close_bindings_target_probe(RTMP_ADAPTER *ad,PNET_DEV dev,
 struct ifreq *rq,unsigned char *wire)
{
 return wr_iot_driver_close_reply(ad,dev,rq,wire);
}
'''

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('kernel','driver','compiler','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();root=a.kernel.resolve();driver=a.driver.resolve();local=Path(__file__).resolve().parent
 report={'status':'failed','scope':'staged CLOSE bindings in actual rt_main_dev TU; not linked or installed','runtime_verified':False,'endpoint_installed':False,'resource_retirement_verified':False}
 a.output.parent.mkdir(parents=True,exist_ok=True)
 try:
  before=(root/'.config').read_bytes();files=list(driver.rglob('.rt_main_dev.o.cmd'))
  if len(files)!=1:raise RuntimeError('Expected exactly one rt_main_dev Kbuild command')
  raw=files[0].read_bytes();lines=re.findall(r'^cmd_.*? := (.+)$',raw.decode(),re.M)
  if len(lines)!=1:raise RuntimeError('Expected one compiler command')
  argv=shlex.split(lines[0])
  if not argv or any(t in (';','&&','||','|','>','<') for t in argv):raise RuntimeError('Unsupported command')
  tool=Path(argv[0])
  if not tool.is_absolute():tool=Path(str(root/tool) if '/' in argv[0] else shutil.which(argv[0]) or '')
  if tool.resolve()!=a.compiler.resolve():raise RuntimeError('Compiler identity mismatch')
  flags=[];sources=[];i=1
  while i<len(argv):
   t=argv[i]
   if t in ('-o','-MF','-MT','-MQ'):i+=2;continue
   if t in ('-c','-MD','-MMD','-MP') or t.startswith(('-Wp,-MD,','-Wp,-MMD,')):i+=1;continue
   if t.endswith('.c'):sources.append(t)
   else:flags.append(t)
   i+=1
  if len(sources)!=1:raise RuntimeError('Expected one C source')
  source=Path(sources[0]);source=source if source.is_absolute() else root/source
  if source.resolve()!=(driver/'os/linux/rt_main_dev.c').resolve():raise RuntimeError('Unexpected source')
  binding_names=('driver-api-close-finish.h','driver-api-close-recovery.h',
                 'driver-api-close-enter.inc','driver-api-close-finish-binding.inc',
                 'driver-api-close-recovery-binding.inc','driver-api-close-finish-recovery.inc',
                 'driver-api-close-entry.inc')
  binding_inputs={name:(local/name).read_bytes() for name in binding_names}
  driver_input=source.read_bytes()
  report.update(command_sha256=hashlib.sha256(raw).hexdigest(),kernel_config_sha256=hashlib.sha256(before).hexdigest(),
                binding_source_sha256={name:hashlib.sha256(data).hexdigest() for name,data in binding_inputs.items()},
                driver_source_sha256=hashlib.sha256(driver_input).hexdigest())
  with tempfile.TemporaryDirectory(prefix='wr-close-target-tu-') as tmp:
   probe=Path(tmp)/'close.c';obj=Path(tmp)/'close.o';probe.write_text(probe_source(driver,local))
   macros=subprocess.run([str(tool.resolve()),*flags,'-E','-dM',str(probe)],cwd=root,capture_output=True,text=True,timeout=60)
   if macros.returncode:raise RuntimeError('CLOSE preprocessing failed: '+macros.stderr[-6000:])
   a.output.with_suffix('.macros.txt').write_text(macros.stdout)
   required=('MT7603','MT_MAC','RTMP_PCI_SUPPORT','CONFIG_AP_SUPPORT')
   if not all(re.search(r'^#define '+n+r'(?:\s|$)',macros.stdout,re.M) for n in required):raise RuntimeError('Missing MT7603 PCI AP macros')
   result=subprocess.run([str(tool.resolve()),*flags,'-c',str(probe),'-o',str(obj)],cwd=root,capture_output=True,text=True,timeout=120)
   if result.returncode:raise RuntimeError('CLOSE target TU failed: '+result.stderr[-6000:])
   blob=obj.read_bytes()
   if blob[:6]!=b'\x7fELF\x01\x01' or int.from_bytes(blob[16:18],'little')!=1 or int.from_bytes(blob[18:20],'little')!=8:raise RuntimeError('Expected ELF32 little-endian MIPS')
   nm=str(a.compiler.resolve())
   if not nm.endswith('gcc'):raise RuntimeError('Expected cross gcc name')
   symbols=subprocess.check_output([nm[:-3]+'nm','-S',str(obj)],text=True)
   row=next((s.split() for s in symbols.splitlines() if s.endswith(' wr_iot_close_bindings_target_probe')),None)
   if not row or len(row)!=4 or row[2].upper()!='T' or int(row[1],16)<=8:raise RuntimeError('Probe missing or optimized to trivial refusal')
   if (root/'.config').read_bytes()!=before:raise RuntimeError('Kernel config changed')
   if source.read_bytes()!=driver_input or any((local/name).read_bytes()!=data for name,data in binding_inputs.items()):raise RuntimeError('CLOSE source changed during target probe')
   a.output.with_suffix('.o').write_bytes(blob)
   report.update(status='passed',object_sha256=hashlib.sha256(blob).hexdigest(),object_bytes=len(blob),probe_symbol_bytes=int(row[1],16),probe_source_sha256=hashlib.sha256(probe.read_bytes()).hexdigest())
 except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as e:report['error']=str(e)
 a.output.write_text(json.dumps(report,indent=2)+'\n');print(report['status']+' staged CLOSE target TU; no link/runtime acceptance')
 return 0 if report['status']=='passed' else 1
if __name__=='__main__':raise SystemExit(main())
