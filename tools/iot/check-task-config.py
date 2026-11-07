#!/usr/bin/env python3
"""Read actual rt_linux.o Kbuild flags; never infer its macros from another TU."""
import argparse,hashlib,json,re,shlex,shutil,subprocess
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--kernel',type=Path,required=True)
p.add_argument('--driver',type=Path,required=True)
p.add_argument('--compiler',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--unit',choices=('rt_linux','rt_rbus_pci_drv','andes_mt','cmm_asic_mt','cmm_mac_pci','cmm_data','andes_core','cmm_data_pci','rtmp_init','mt7603','rtmp_init_inf','ap_autoChSel','ap'),default='rt_linux')
a=p.parse_args(); root=a.kernel.resolve(); driver=a.driver.resolve()
report={'status':'unavailable','scope':'actual '+a.unit+'.c preprocessing only','target_driver_compiled':False,'runtime_verified':False}
try:
 commands=list(driver.rglob('.'+a.unit+'.o.cmd'))
 if len(commands)!=1:raise RuntimeError('Expected exactly one '+a.unit+' Kbuild command')
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
 relative={'rt_linux':'os/linux/rt_linux.c','rt_rbus_pci_drv':'os/linux/rt_rbus_pci_drv.c','andes_mt':'mcu/andes_mt.c','cmm_asic_mt':'hw_ctrl/cmm_asic_mt.c','cmm_mac_pci':'common/cmm_mac_pci.c','cmm_data':'common/cmm_data.c','andes_core':'mcu/andes_core.c','cmm_data_pci':'common/cmm_data_pci.c','rtmp_init':'common/rtmp_init.c','mt7603':'chips/mt7603.c','rtmp_init_inf':'common/rtmp_init_inf.c','ap_autoChSel':'ap/ap_autoChSel.c','ap':'ap/ap.c'}[a.unit]
 if source.resolve()!=(driver/relative).resolve():raise RuntimeError('Unexpected translation unit')
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
 macros={n:bool(re.search(r'^#define '+n+r'(?:[ \t]|$)',run.stdout,re.M)) for n in ('KTHREAD_SUPPORT','OS_ABL_FUNC_SUPPORT','CONFIG_PM','RTMP_TIMER_TASK_SUPPORT','WSC_INCLUDED','WSC_AP_SUPPORT','WSC_V2_SUPPORT','WORKQUEUE_BH','CONFIG_ANDES_SUPPORT','MT7603','MT_MAC','RTMP_PCI_SUPPORT','RESOURCE_PRE_ALLOC','LOAD_FW_ONE_TIME','AIRPLAY_SUPPORT','MBSS_SUPPORT','WH_EZ_SETUP')}
 report.update(status='complete',macros=macros,command_sha256=hashlib.sha256(data).hexdigest(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_command=str(commands[0]),compiler=str(tool.resolve()))
except (OSError,RuntimeError,ValueError,subprocess.TimeoutExpired) as e:report['error']=str(e)
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(report,indent=2)+'\n')
print(report['status']+' '+a.unit+' task configuration; not runtime proof')
raise SystemExit(0 if report['status']=='complete' else 1)
