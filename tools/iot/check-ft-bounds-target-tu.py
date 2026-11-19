#!/usr/bin/env python3
"""Compile prepared FT/MLME snapshots using their actual Kbuild commands.

Separate temporary TUs/objects only; no driver module or image replacement.
"""
import argparse,hashlib,json,re,runpy,shlex,shutil,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
for name in ('kernel','driver','compiler','output'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();root=a.kernel.resolve();driver=a.driver.resolve();here=Path(__file__).resolve().parent
unwrap=runpy.run_path(str(here/'kbuild-compiler.py'))['unwrap_ccache']
report={'status':'failed','scope':'Prepared FT RRB/stamped-consumer and explicit native MLME enqueue temporary TUs only','module_installed':False,'runtime_verified':False,'translation_units':{}}
def command(unit):
 commands=list(driver.rglob('.'+unit+'.o.cmd'))
 if len(commands)!=1:raise RuntimeError('Expected exactly one active '+unit+' Kbuild command')
 raw=commands[0].read_bytes();lines=re.findall(r'^cmd_.*? := (.+)$',raw.decode(),re.M)
 if len(lines)!=1:raise RuntimeError('Expected one '+unit+' compiler command')
 argv=unwrap(shlex.split(lines[0]));tool=Path(argv[0])
 if any(x in (';','&&','||','|','>','<') for x in argv):raise RuntimeError('Unsupported compiler command')
 if not tool.is_absolute():tool=Path(str(root/tool) if '/' in argv[0] else shutil.which(argv[0]) or '')
 if tool.resolve()!=a.compiler.resolve():raise RuntimeError(unit+' compiler identity mismatch')
 filtered=[];sources=[];i=1
 while i<len(argv):
  token=argv[i]
  if token in ('-o','-MF','-MT','-MQ'):i+=2;continue
  if token in ('-c','-MD','-MMD','-MP') or token.startswith(('-Wp,-MD,','-Wp,-MMD,')):i+=1;continue
  if token.endswith('.c'):sources.append(token)
  else:filtered.append(token)
  i+=1
 if len(sources)!=1:raise RuntimeError('Expected one '+unit+' source')
 source=Path(sources[0]);source=source if source.is_absolute() else root/source
 if source.resolve()!=(driver/'common'/(unit+'.c')).resolve():raise RuntimeError('Unexpected '+unit+' source identity')
 return raw,tool.resolve(),filtered,source
try:
 commands={unit:command(unit) for unit in ('ft','mlme')}
 originals={unit:entry[3].read_bytes() for unit,entry in commands.items()}
 enqueue=runpy.run_path(str(here/'ft-enqueue-generation-composition.py'))
 mlme,prototype=enqueue['compose'](originals['mlme'].decode())
 ft=runpy.run_path(str(here/'ft-parser-bounds-composition.py'))['compose'](originals['ft'].decode())
 ft=enqueue['bind_ft'](ft,prototype)
 ft,_=runpy.run_path(str(here/'ra2-ft-mutation-composition.py'))['compose'](ft)
 include='#include "rt_config.h"'
 if ft.count(include)!=1:raise RuntimeError('FT configuration include changed')
 ft=ft.replace(include,include+'\n#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)\n#include "ra2-mutation-admission-kernel.h"\n#endif',1)
 with tempfile.TemporaryDirectory(prefix='wr-ft-generation-target-') as td:
  temp=Path(td)
  for name in ('ft-action-bounds.h','ft-ie-span.h','ft-subelement-bounds.h','ft-request-ie-admission.h','ft-peer-generation.h'):
   shutil.copyfile(here/name,temp/name)
  for unit,changed in (('ft',ft),('mlme',mlme)):
   raw,tool,filtered,source=commands[unit]
   candidate=temp/(unit+'.c');obj=temp/(unit+'.o');candidate.write_text(changed)
   flags=[str(tool),'-I'+str(temp),*filtered,str(candidate)]
   macros=subprocess.run([*flags,'-E','-dM'],cwd=root,text=True,capture_output=True,timeout=60)
   if macros.returncode:raise RuntimeError(unit+' preprocessing failed: '+macros.stderr[-2500:])
   required=('DOT11R_FT_SUPPORT','CONFIG_AP_SUPPORT','MT7603','MT_MAC','RTMP_PCI_SUPPORT')
   effective={name:bool(re.search(r'^#define '+name+r'(?:\s|$)',macros.stdout,re.M)) for name in required}
   if not all(effective.values()):raise RuntimeError(unit+' target features inactive: '+str(effective))
   build=subprocess.run([*flags,'-c','-o',str(obj)],cwd=root,text=True,capture_output=True,timeout=120)
   if build.returncode:raise RuntimeError(unit+' target compilation failed: '+build.stderr[-6000:])
   data=obj.read_bytes()
   if data[:6]!=b'\x7fELF\x01\x01' or int.from_bytes(data[18:20],'little')!=8:raise RuntimeError('Expected ELF32 LE MIPS '+unit+' object')
   symbols=subprocess.run(['readelf','-Ws',str(obj)],text=True,capture_output=True,check=True).stdout
   matches=[line for line in symbols.splitlines() if line.split()[-1:] == ['wr_ft_mlme_enqueue_for_recv']]
   if len(matches)!=1:raise RuntimeError(unit+' missing or ambiguous explicit enqueue symbol')
   fields=matches[0].split()
   if fields[4]!='GLOBAL' or (unit=='ft' and fields[6]!='UND') or (unit=='mlme' and not fields[6].isdigit()):
    raise RuntimeError(unit+' unexpected explicit enqueue linkage')
   receipt=dict(effective_macros=effective,command_sha256=hashlib.sha256(raw).hexdigest(),source_sha256=hashlib.sha256(originals[unit]).hexdigest(),prepared_source_sha256=hashlib.sha256(changed.encode()).hexdigest(),object_sha256=hashlib.sha256(data).hexdigest(),object_bytes=len(data),explicit_enqueue_symbol=matches[0].strip())
   report['translation_units'][unit]=receipt
   if unit=='ft':report.update(receipt) # Preserve existing FT-only report fields.
   a.output.parent.mkdir(parents=True,exist_ok=True)
   a.output.with_suffix('.'+unit+'.macros.txt').write_text(macros.stdout)
 for unit,entry in commands.items():
  if entry[3].read_bytes()!=originals[unit]:raise RuntimeError('Original '+unit+' source changed during temporary probe')
 report['status']='passed'
except (OSError,RuntimeError,ValueError,subprocess.SubprocessError) as error:report['error']=str(error)
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
print(report['status']+' prepared FT/MLME generation MIPS TUs; driver/image unchanged')
if report.get('error'):print(report['error'])
raise SystemExit(0 if report['status']=='passed' else 1)
