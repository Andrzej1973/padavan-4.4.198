#!/usr/bin/env python3
"""Compile staged CLOSE bindings with the actual rt_main_dev Kbuild flags; no ioctl installation."""
import argparse,hashlib,json,re,shlex,shutil,subprocess,tempfile
from pathlib import Path
import runpy
unwrap_ccache=runpy.run_path(str(Path(__file__).with_name('kbuild-compiler.py')))['unwrap_ccache']

def compiled_bundle_inputs(driver,local,manifest_path):
 if not (driver/'include/driver-api-close-bundle.h').exists():return {}
 if manifest_path is None:
  raise ValueError('Ordinary CLOSE bundle requires an explicit --manifest path')
 manifest=json.loads(Path(manifest_path).read_text())
 return runpy.run_path(str(local/'close-bundle-assets.py'))['verified_inputs'](driver,local,manifest)

def probe_source(driver,local):
 files=[driver/'os/linux/rt_main_dev.c',local/'driver-api-close-finish.h',
        local/'driver-api-close-recovery.h',local/'driver-api-close-progress-match.h',local/'driver-api-close-enter.inc',
        local/'driver-api-close-finish-binding.inc',local/'driver-api-close-recovery-binding.inc',
        local/'driver-api-close-synchronous-put.h',local/'driver-api-close-synchronous-put.inc',
        local/'driver-api-close-finish-recovery.inc',local/'driver-api-close-entry.inc',
        local/'driver-api-close-retirement.h',local/'driver-api-close-retirement-binding.inc',
        local/'driver-api-close-retirement-create.inc',local/'driver-api-close-retirement-cancel.inc',local/'driver-api-close-retirement-start.inc',local/'driver-api-close-retirement-thread-entry.inc',local/'driver-api-close-retirement-thread-body.inc',local/'driver-api-close-retirement-launch.inc',local/'driver-api-close-retirement-reconcile.inc',local/'driver-api-close-progress.inc',local/'driver-api-close-progress-wire.h',local/'driver-api-close-progress-entry.inc',local/'driver-api-close-progress-ioctl.inc']
 if any('"' in str(f) or '\n' in str(f) for f in files):raise ValueError('Unsupported include path')
 return '#include <linux/module.h>\n#include <linux/kthread.h>\n#include <linux/sched.h>\n#include <linux/rtnetlink.h>\n'+'#include "'+str(files[0])+'"\n#ifndef WR_IOT_DRIVER_CLOSE_BUNDLE_H\n'+''.join('#include "'+str(f)+'"\n' for f in files[1:])+'#endif\n'+'''
int wr_iot_close_bindings_target_probe(RTMP_ADAPTER *ad,PNET_DEV dev,
 struct ifreq *rq,unsigned char *wire)
{
 int status=wr_iot_driver_close_reply(ad,dev,rq,wire);
 /* Keep the probe call visible when the real dispatcher also uses this body.
  * An empty register barrier prevents a sibling jump without emitting code
  * for a constant-refusal implementation. The size guard remains effective. */
 asm volatile("" : : "r" (status));
 return status;
}
int wr_iot_close_synchronous_put_target_probe(RTMP_ADAPTER *ad,PNET_DEV dev)
{
 return wr_iot_driver_close_synchronous_put(ad,dev);
}
int wr_iot_close_progress_match_target_probe(RTMP_ADAPTER *ad,PNET_DEV dev,
 const struct wr_iot_driver_close_request *request)
{
 ULONG flags=0;int matched;
 if(!ad)return 0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 matched=wr_iot_driver_close_progress_matches(&ad->wr_iot_close_owner,
  &ad->wr_iot_driver_owner,dev,request);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return matched;
}
/* Compile-only locked designation: actual adapter/work fields checked. */
int wr_iot_close_retirement_target_probe(RTMP_ADAPTER *ad,const void *stopped_task)
{
 ULONG flags=0;int ready;
 if(!ad)return 0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 ready=wr_iot_driver_close_retirement_ready_locked(ad);
 if(ready&&stopped_task)ready=wr_iot_driver_close_retirement_designate_locked(ad,stopped_task);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ready;
}
/* Compile-only prepare: stopped task remains caller-owned on success. */
int wr_iot_close_retirement_prepare_target_probe(RTMP_ADAPTER *ad,
 int (*fn)(void *),struct task_struct **out)
{
 return wr_iot_driver_close_retirement_prepare(ad,fn,out);
}
/* Compile-only stopped-task cancellation; no runtime route. */
int wr_iot_close_retirement_cancel_target_probe(RTMP_ADAPTER *ad,struct task_struct **task)
{
 return wr_iot_driver_close_retirement_cancel(ad,task);
}
/* Compile-only RTNL-guarded wake; never called by driver. */
int wr_iot_close_retirement_start_target_probe(RTMP_ADAPTER *ad,struct task_struct **task)
{
 return wr_iot_driver_close_retirement_start(ad,task);
}
/* Compile-only designated fixed-body entry check. */
int wr_iot_close_retirement_entry_target_probe(RTMP_ADAPTER *ad)
{
 int status=wr_iot_driver_close_retirement_thread_enter(ad);
 if(status)(void)wr_iot_driver_close_retirement_thread_refuse(ad,status);
 return status;
}
int wr_iot_close_retirement_fixed_target_probe(RTMP_ADAPTER *ad,struct task_struct **task)
{
 return wr_iot_driver_close_retirement_prepare_fixed(ad,task);
}
int wr_iot_close_retirement_launch_target_probe(RTMP_ADAPTER *ad,struct task_struct **task)
{
 return wr_iot_driver_close_retirement_launch(ad,task);
}
int wr_iot_close_retirement_reconcile_target_probe(RTMP_ADAPTER *ad,struct task_struct **task)
{
 return wr_iot_driver_close_retirement_reconcile(ad,task);
}
int wr_iot_close_progress_target_probe(RTMP_ADAPTER *ad,PNET_DEV dev,
 const struct wr_iot_driver_close_request *request)
{
 return wr_iot_driver_close_progress(ad,dev,request);
}
int wr_iot_close_progress_reply_target_probe(RTMP_ADAPTER *ad,PNET_DEV dev,
 const unsigned char *wire)
{
 return wr_iot_driver_close_progress_reply(ad,dev,wire);
}
int wr_iot_close_progress_ioctl_target_probe(RTMP_ADAPTER *ad,PNET_DEV dev,
 struct ifreq *rq)
{
 return wr_iot_driver_close_progress_ioctl(ad,dev,rq);
}
/* Compile-only kernel-thread tail; never routed or invoked by firmware. */
int wr_iot_close_module_exit_target_probe(struct task_struct *designated)
{
 if(current!=designated || !(current->flags&PF_KTHREAD) ||
    (current->flags&PF_WQ_WORKER))return -EPERM;
 module_put_and_exit(0);
}
/* Create stopped: an eventual binding must publish exact task ownership
 * before waking it. This compile-only probe is not called by the driver. */
struct task_struct *wr_iot_close_module_create_target_probe(int (*fn)(void *),void *data)
{
 return kthread_create(fn,data,"wr-iot-retire");
}
'''

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('kernel','driver','compiler','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--manifest',type=Path)
 a=p.parse_args();root=a.kernel.resolve();driver=a.driver.resolve();local=Path(__file__).resolve().parent
 report={'status':'failed','scope':'staged CLOSE bindings in actual rt_main_dev TU; not linked or installed','runtime_verified':False,'endpoint_installed':False,'resource_retirement_verified':False}
 a.output.parent.mkdir(parents=True,exist_ok=True)
 try:
  before=(root/'.config').read_bytes();files=list(driver.rglob('.rt_main_dev.o.cmd'))
  if len(files)!=1:raise RuntimeError('Expected exactly one rt_main_dev Kbuild command')
  raw=files[0].read_bytes();lines=re.findall(r'^cmd_.*? := (.+)$',raw.decode(),re.M)
  if len(lines)!=1:raise RuntimeError('Expected one compiler command')
  argv=unwrap_ccache(shlex.split(lines[0]))
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
  binding_names=('driver-api-close-finish.h','driver-api-close-recovery.h','driver-api-close-progress-match.h',
                 'driver-api-close-enter.inc','driver-api-close-finish-binding.inc',
                 'driver-api-close-recovery-binding.inc','driver-api-close-finish-recovery.inc',
                 'driver-api-close-entry.inc','driver-api-close-synchronous-put.h','driver-api-close-synchronous-put.inc','driver-api-close-retirement.h',
                 'driver-api-close-retirement-binding.inc','driver-api-close-retirement-create.inc','driver-api-close-retirement-cancel.inc','driver-api-close-retirement-start.inc','driver-api-close-retirement-thread-entry.inc','driver-api-close-retirement-thread-body.inc','driver-api-close-retirement-launch.inc','driver-api-close-retirement-reconcile.inc','driver-api-close-progress.inc','driver-api-close-progress-wire.h','driver-api-close-progress-entry.inc','driver-api-close-progress-ioctl.inc')
  bundle=(local/'driver-api-close-bundle.h').read_bytes()
  binding_inputs={name:(local/name).read_bytes() for name in binding_names}
  binding_inputs['driver-api-close-bundle.h']=bundle
  compiled_bundle=driver/'include/driver-api-close-bundle.h'
  compiled_inputs=compiled_bundle_inputs(driver,local,a.manifest)
  report['compiled_bundle_source_sha256']={name:hashlib.sha256(data).hexdigest() for name,data in compiled_inputs.items()}
  report['ordinary_driver_bundle_present']=compiled_bundle.exists()
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
   if any((driver/'include'/name).read_bytes()!=data for name,data in compiled_inputs.items()):
    raise RuntimeError('Compiled bundle inputs changed during target probe')
   blob=obj.read_bytes()
   if blob[:6]!=b'\x7fELF\x01\x01' or int.from_bytes(blob[16:18],'little')!=1 or int.from_bytes(blob[18:20],'little')!=8:raise RuntimeError('Expected ELF32 little-endian MIPS')
   nm=str(a.compiler.resolve())
   if not nm.endswith('gcc'):raise RuntimeError('Expected cross gcc name')
   symbols=subprocess.check_output([nm[:-3]+'nm','-S',str(obj)],text=True)
   a.output.with_suffix('.o').write_bytes(blob)
   a.output.with_suffix('.symbols.txt').write_text(symbols)
   row=next((s.split() for s in symbols.splitlines() if s.endswith(' wr_iot_close_bindings_target_probe')),None)
   report['probe_symbol_row']=row
   if not row or len(row)!=4 or row[2].upper()!='T' or int(row[1],16)<=8:raise RuntimeError('Probe missing or optimized to trivial refusal: '+str(row))
   exit_row=next((s.split() for s in symbols.splitlines() if s.endswith(' wr_iot_close_module_exit_target_probe')),None)
   if not exit_row or len(exit_row)!=4 or exit_row[2].upper()!='T':raise RuntimeError('Nonreturning module exit probe missing')
   undefined=subprocess.check_output([nm[:-3]+'nm','-u',str(obj)],text=True)
   if not any(line.split()[-1:] in [['__module_put_and_exit'],['do_exit']] for line in undefined.splitlines()):raise RuntimeError('Expected core module exit relocation')
   if not any(line.split()[-1:]==['kthread_create_on_node'] for line in undefined.splitlines()):raise RuntimeError('Expected stopped kthread-create relocation')
   create_row=next((s.split() for s in symbols.splitlines() if s.endswith(' wr_iot_close_module_create_target_probe')),None)
   if not create_row or len(create_row)!=4 or create_row[2].upper()!='T':raise RuntimeError('Stopped kthread create probe missing')
   retirement_row=next((s.split() for s in symbols.splitlines() if s.endswith(' wr_iot_close_retirement_target_probe')),None)
   if not retirement_row or len(retirement_row)!=4 or retirement_row[2].upper()!='T' or int(retirement_row[1],16)<=8:raise RuntimeError('Retirement locked probe missing or trivial')
   report['retirement_locked_binding_compiled']=True
   report['nonreturning_module_exit_compiled']=True
   report['stopped_kthread_create_compiled']=True
   report['thread_exit_context_checks']='designated current task, PF_KTHREAD, not PF_WQ_WORKER; compile only'
   if (root/'.config').read_bytes()!=before:raise RuntimeError('Kernel config changed')
   if source.read_bytes()!=driver_input or any((local/name).read_bytes()!=data for name,data in binding_inputs.items()):raise RuntimeError('CLOSE source changed during target probe')
   a.output.with_suffix('.o').write_bytes(blob)
   report.update(status='passed',object_sha256=hashlib.sha256(blob).hexdigest(),object_bytes=len(blob),probe_symbol_bytes=int(row[1],16),probe_source_sha256=hashlib.sha256(probe.read_bytes()).hexdigest())
 except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as e:
  report['error']=str(e)
  print('CLOSE target TU error: '+str(e)[-6000:])
 a.output.write_text(json.dumps(report,indent=2)+'\n');print(report['status']+' staged CLOSE target TU; no link/runtime acceptance')
 return 0 if report['status']=='passed' else 1
if __name__=='__main__':raise SystemExit(main())
