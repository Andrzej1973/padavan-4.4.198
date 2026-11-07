#!/usr/bin/env python3
"""Host parser/control checks; synthetic TU is NOT the target driver."""
import json,shlex,shutil,subprocess,sys,tempfile
from pathlib import Path
compiler=shutil.which('gcc')
if not compiler:raise SystemExit('Host gcc required')
compiler=Path(compiler).resolve(); script=Path(__file__).with_name('check-task-config.py').resolve()
base=Path(tempfile.mkdtemp(prefix='iot-task-config-controls-'));root=base/'kernel';driver=root/'driver'
(driver/'os/linux').mkdir(parents=True)
source=driver/'os/linux/rt_linux.c'
source.write_text('#define KTHREAD_SUPPORT\n#define OS_ABL_FUNC_SUPPORT 0\n#define WSC_INCLUDED 1\n')
cmd=driver/'.rt_linux.o.cmd'
line='cmd_fixture := '+shlex.quote(compiler.as_posix())+' -c -o ignored.o '+shlex.quote(source.as_posix())+'\n'
cmd.write_text(line)
args=[sys.executable,str(script),'--kernel',str(root),'--driver',str(driver),'--compiler',str(compiler)]
results={}
def run(name,success):
 output=base/(name+'.json')
 r=subprocess.run([*args,'--output',str(output)],capture_output=True,text=True)
 report=json.loads(output.read_text())
 assert (r.returncode==0)==success,(name,r.stdout,r.stderr)
 assert (report['status']=='complete')==success
 results[name]=report
 return report
r=run('valid',True)
assert r['macros']['KTHREAD_SUPPORT'] and r['macros']['OS_ABL_FUNC_SUPPORT'] and not r['macros']['CONFIG_PM']
assert r['target_driver_compiled'] is False
assert Path(r['source_command_artifact']).read_text()==line
assert Path(r['macro_artifact']).is_file()
assert r['preprocess_argv'][-2:]==['-E','-dM']
cmd.unlink();run('missing-command',False);cmd.write_text(line)
extra=driver/'os/.rt_linux.o.cmd';extra.write_text(line);run('ambiguous-command',False);extra.unlink()
cmd.write_text(line.replace(compiler.as_posix(),'wrong-compiler'));run('wrong-compiler',False)
cmd.write_text(line.replace(source.as_posix(),(driver/'wrong.c').as_posix()));run('wrong-source',False)
cmd.write_text(line);source.write_text('#include "definitely-missing-header.h"\n');run('preprocessor-failure',False)
for unit,relative in (('andes_core','mcu/andes_core.c'),('cmm_data_pci','common/cmm_data_pci.c'),('rtmp_init','common/rtmp_init.c'),('mt7603','chips/mt7603.c'),('rtmp_init_inf','common/rtmp_init_inf.c'),('ap_autoChSel','ap/ap_autoChSel.c')):
 source=driver/relative;source.parent.mkdir(parents=True,exist_ok=True)
 source.write_text('#define MT7603 1\n#define MT_MAC 1\n#define RTMP_PCI_SUPPORT 1\n')
 (driver/('.'+unit+'.o.cmd')).write_text('cmd_fixture := '+shlex.quote(compiler.as_posix())+' -c -o ignored.o '+shlex.quote(source.as_posix())+'\n')
 original_args=args;args=[*original_args,'--unit',unit]
 report=run('valid-'+unit,True)
 assert report['macros']['MT7603'] and report['macros']['MT_MAC'] and report['macros']['RTMP_PCI_SUPPORT']
 args=original_args
print('PASS synthetic host task-config controls including channel translation units; not target macro evidence')
bytes_removed=sum(f.stat().st_size for f in base.rglob('*') if f.is_file())
shutil.rmtree(base)
print('Removed phase scratch:',bytes_removed,'bytes')
