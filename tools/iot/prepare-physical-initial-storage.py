#!/usr/bin/env python3
"""Stage dormant INITIAL_OFF storage/free guards in a new candidate copy."""
import argparse,json,hashlib,runpy,shutil
from pathlib import Path
here=Path(__file__).resolve().parent
compose=runpy.run_path(str(here/'physical-initial-storage.py'))['compose']
def prepare(source,output,bind_main=False,install_endpoint=False):
 source=source.resolve();dest=output.resolve()
 if output.exists() or output.is_symlink() or dest.is_relative_to(source) or source.is_relative_to(dest):
  raise ValueError('Output exists or overlaps source')
 paths=('include/rtmp.h','common/rtmp_init.c','include/wr-iot-raw-recovery-free-fence.inc')
 texts=[]
 for name in paths:
  p=source/name
  if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(source):raise ValueError('Invalid input '+name)
  texts.append(p.read_text())
 changed=compose(*texts)
 # Copy only helpers needed by fields and the raw-free terminal cache. None of
 # the new ioctl/publication/cleanup provider is enabled by this preparation.
 names=['physical-initial-types.h','physical-initial-terminal-types.h','physical-initial-wire.h','physical-initial-terminal.inc']
 main_text=None
 if bind_main:
  main=source/'os/linux/rt_main_dev.c'
  if not main.is_file() or main.is_symlink() or not main.resolve().is_relative_to(source):
   raise ValueError('Invalid Main worker input')
  bind=runpy.run_path(str(here/'physical-initial-main-binding.py'))['compose']
  main_text=bind(main.read_text())
  marker='static int wr_iot_main_recovery_execute('
  if main_text.count(marker)!=1:raise ValueError('Ambiguous Main worker include')
  main_text=main_text.replace(marker,'#include "physical-initial-record.h"\n'+marker,1)
  names+=['physical-initial-record.h','physical-initial-origin.h',
   'precreated-idle-probe.h','precreated-idle-reference.h']
 dispatch_text=None;parent_manifest=None
 if install_endpoint:
  if not bind_main:raise ValueError('Endpoint requires initial Main binding')
  manifest_path=source.with_name(source.name+'.manifest.json')
  if manifest_path.is_symlink() or output.with_name(output.name+'.manifest.json').exists():
   raise ValueError('Unsafe source/output manifest')
  if any(p.is_symlink() for p in source.rglob('*')):raise ValueError('Symlink candidate refused')
  parent_manifest=json.loads(manifest_path.read_text())
  input_hashes={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest()
    for p in source.rglob('*') if p.is_file()}
  if parent_manifest.get('production_installed') is not False or input_hashes!=parent_manifest.get('merged_driver_sha256'):
   raise ValueError('Intact isolated candidate manifest required')
  dispatch=source/'include/driver-api-closed-entry.inc'
  if dispatch.is_symlink() or not dispatch.resolve().is_relative_to(source):raise ValueError('Invalid dispatch')
  dispatch_text=dispatch.read_text()
  if dispatch_text.count('#define WR_IOT_RA2_NO_HOST_MODE 1')!=1:raise ValueError('No-host candidate required')
  dispatch_text=runpy.run_path(str(here/'physical-initial-dispatch.py'))['compose'](dispatch_text)
  names+=['physical-initial-arm-admission.inc','physical-initial-arm-abort.inc',
   'physical-initial-arm-publication.inc','physical-initial-pins.inc',
   'physical-initial-main-completion.inc','physical-initial-query.inc',
   'physical-initial-cleanup.inc','physical-initial-terminal-replace.inc','physical-initial-handler.inc','physical-initial-ioctl.inc']
  dispatch_text+='\n#include "physical-initial-record.h"\n#include "physical-initial-terminal.inc"\n'
  for name in names:
   if name.endswith('.inc') and name!='physical-initial-terminal.inc':
    dispatch_text+='#include "'+name+'"\n'
 payload={name:(here/name).read_bytes() for name in names}
 for name,data in payload.items():
  p=source/'include'/name
  if p.exists() and (p.is_symlink() or p.read_bytes()!=data):raise ValueError('Conflicting helper '+name)
 shutil.copytree(source,output,symlinks=True)
 for name,text in zip(paths,changed):(output/name).write_text(text)
 if main_text is not None:(output/'os/linux/rt_main_dev.c').write_text(main_text)
 for name,data in payload.items():(output/'include'/name).write_bytes(data)
 if dispatch_text is not None:(output/'include/driver-api-closed-entry.inc').write_text(dispatch_text)
 report={'initial_storage_and_retirement_staged':True,'endpoint_installed':bool(install_endpoint),
  'main_worker_initial_bound':bool(bind_main),'production_ready':False,'runtime_verified':False,
  'helpers_sha256':{n:hashlib.sha256(d).hexdigest() for n,d in payload.items()}}
 (output/'initial-storage-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 if parent_manifest is not None:
  hashes={str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
    for p in output.rglob('*') if p.is_file()}
  parent_manifest['merged_driver_sha256']=hashes
  if 'candidate_driver_sha256' in parent_manifest:
   parent_manifest['candidate_driver_sha256'].update(hashes)
  parent_manifest['initial_physical_layer']=dict(report,experimental_only=True,
   request_magic='WPIQ',ioctl_existing='0x89fd',target_compiled=False)
  parent_manifest.update(production_installed=False,target_compiled=False,runtime_verified=False)
  output.with_name(output.name+'.manifest.json').write_text(json.dumps(parent_manifest,indent=2)+'\n')
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);p.add_argument('--bind-main',action='store_true');p.add_argument('--install-endpoint',action='store_true');a=p.parse_args()
 prepare(a.source,a.output,a.bind_main,a.install_endpoint);print('PASS dormant initial storage/free guard staged; Main binding='+str(a.bind_main)+'; endpoint='+str(a.install_endpoint))
