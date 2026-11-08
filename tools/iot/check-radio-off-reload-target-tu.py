#!/usr/bin/env python3
"""Compile checked-off body excluded by LOAD_FW_ONE_TIME; TU evidence only."""
import argparse,hashlib,json,re,shlex,shutil,subprocess,tempfile
from pathlib import Path
import runpy
unwrap_ccache=runpy.run_path(str(Path(__file__).with_name('kbuild-compiler.py')))['unwrap_ccache']
p=argparse.ArgumentParser(description=__doc__)
for name in ('kernel','driver','compiler','output'):
 p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();root=a.kernel.resolve();driver=a.driver.resolve()
a.output.parent.mkdir(parents=True,exist_ok=True)
report={'status':'failed','scope':'reload-mode hw_ctrl/cmm_asic_mt.c TU only',
        'production_config_changed':False,'full_reload_module_verified':False,
        'firmware_shutdown_verified':False,'runtime_verified':False}
try:
 config_before=(root/'.config').read_bytes()
 report['kernel_config_sha256']=hashlib.sha256(config_before).hexdigest()
 files=list(driver.rglob('.cmm_asic_mt.o.cmd'))
 if len(files)!=1:raise RuntimeError('Expected exactly one ASIC MT Kbuild command')
 raw=files[0].read_bytes();lines=re.findall(r'^cmd_.*? := (.+)$',raw.decode(),re.M)
 if len(lines)!=1:raise RuntimeError('Expected one compiler command')
 argv=unwrap_ccache(shlex.split(lines[0]))
 if not argv or any(t in (';','&&','||','|','>','<') for t in argv):
  raise RuntimeError('Unsupported compiler command')
 tool=Path(argv[0])
 if not tool.is_absolute():tool=Path(str(root/tool) if '/' in argv[0] else shutil.which(argv[0]) or '')
 if tool.resolve()!=a.compiler.resolve():raise RuntimeError('Compiler identity mismatch')
 filtered=[];i=1
 while i<len(argv):
  t=argv[i]
  if t in ('-o','-MF','-MT','-MQ'):i+=2;continue
  if t in ('-c','-MD','-MMD','-MP') or t.startswith(('-Wp,-MD,','-Wp,-MMD,')):i+=1;continue
  if re.match(r'^-[DU]LOAD_FW_ONE_TIME(?:=|$)',t):i+=1;continue
  filtered.append(t);i+=1
 sources=[t for t in filtered if t.endswith('.c')]
 if len(sources)!=1:raise RuntimeError('Expected one source')
 source=Path(sources[0]);source=source if source.is_absolute() else root/source
 if source.resolve()!=(driver/'hw_ctrl/cmm_asic_mt.c').resolve():
  raise RuntimeError('Unexpected translation unit')
 flags=[str(tool.resolve()),*filtered,'-ULOAD_FW_ONE_TIME']
 macro=subprocess.run([*flags,'-E','-dM'],cwd=root,capture_output=True,text=True,timeout=60)
 if macro.returncode:raise RuntimeError('ASIC MT preprocessing failed: '+macro.stderr[-2000:])
 names=('LOAD_FW_ONE_TIME','MT_MAC','RTMP_PCI_SUPPORT','CONFIG_AP_SUPPORT')
 effective={name:bool(re.search(r'^#define '+name+r'(?:\s|$)',macro.stdout,re.M)) for name in names}
 report.update(effective_macros=effective,command_sha256=hashlib.sha256(raw).hexdigest(),
               source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
               macro_sha256=hashlib.sha256(macro.stdout.encode()).hexdigest())
 a.output.with_suffix('.macros.txt').write_text(macro.stdout)
 if effective['LOAD_FW_ONE_TIME'] or not all(effective[n] for n in names[1:]):
  raise RuntimeError('Required reload-mode MT PCI AP macros not effective')
 with tempfile.TemporaryDirectory(prefix='wr-radio-off-reload-tu-') as t:
  obj=Path(t)/'asic-reload.o'
  result=subprocess.run([*flags,'-c','-o',str(obj)],cwd=root,capture_output=True,text=True,timeout=120)
  if result.returncode:raise RuntimeError('ASIC reload TU failed: '+result.stderr[-6000:])
  blob=obj.read_bytes()
  if (blob[:6]!=b'\x7fELF\x01\x01' or int.from_bytes(blob[16:18],'little')!=1 or
      int.from_bytes(blob[18:20],'little')!=8):
   raise RuntimeError('Expected ELF32 little-endian MIPS object')
  nm=str(a.compiler.absolute())
  if not nm.endswith('gcc'):raise RuntimeError('Expected gcc cross-toolchain naming')
  symbols=subprocess.check_output([nm[:-3]+'nm','-S',str(obj)],text=True)
  row=next((s.split() for s in symbols.splitlines() if s.endswith(' wr_iot_mt_radio_off_checked')),None)
  if not row or len(row)!=4 or row[2].upper()!='T' or int(row[1],16)<=8:
   raise RuntimeError('Checked radio-off is absent or still a refusal-sized function')
  if (root/'.config').read_bytes()!=config_before:raise RuntimeError('Production config changed during TU probe')
  report.update(status='passed',object_bytes=len(blob),object_sha256=hashlib.sha256(blob).hexdigest(),
                checked_off_symbol_bytes=int(row[1],16))
except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as e:report['error']=str(e)
a.output.write_text(json.dumps(report,indent=2)+'\n')
print(report['status']+' checked-off reload-mode TU; shutdown/runtime unverified')
raise SystemExit(0 if report['status']=='passed' else 1)
