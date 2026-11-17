#!/usr/bin/env python3
"""Describe one coherent experimental driver/userspace pair for image assembly."""
import argparse,hashlib,json,re,struct
from pathlib import Path
FILES={'sbin/rc':'runtime-link/rc','usr/sbin/httpd':'runtime-link/httpd',
       'usr/bin/iappd.sh':'runtime-link/iappd-candidate.sh',
       'driver:mt76x3_ap':'ra2-no-host-module/mt76x3_ap-ra2-no-host.ko'}
def build(root,revision):
 if not re.fullmatch('[0-9a-f]{40}',revision):raise ValueError('Exact source SHA required')
 def read(name):
  p=root/name
  if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()) or not p.is_file():
   raise ValueError('Missing/unsafe input '+name)
  return p.read_bytes()
 def report(name):return json.loads(read(name))
 files={}
 for target,source in FILES.items():
  blob=read(source)
  if not blob:raise ValueError('Empty input '+source)
  if target=='driver:mt76x3_ap' or target in ('sbin/rc','usr/sbin/httpd'):
   if len(blob)<52 or blob[:6]!=b'\x7fELF\x01\x01' or struct.unpack('<H',blob[18:20])[0]!=8:
    raise ValueError('Not ELF32 LE MIPS '+source)
   expected=1 if target=='driver:mt76x3_ap' else 2
   if struct.unpack('<H',blob[16:18])[0]!=expected:raise ValueError('Wrong ELF type '+source)
  files[target]={'source':source,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()}
 module=report('ra2-no-host-module/target-result.json')
 if not module.get('target_module_linked') or module.get('production_installed') is not False or module.get('runtime_verified') is not False:
  raise ValueError('Missing experimental module evidence')
 if module.get('module_sha256')!=files['driver:mt76x3_ap']['sha256']:
  raise ValueError('Module result hash mismatch')
 for role in ('rc','httpd'):
  closure=report('runtime-link/'+role+'-dependency-closure.json')
  if closure.get('errors') or not closure.get('dependency_closure_verified') or closure.get('production_installed') is not False:
   raise ValueError('Missing dependency evidence '+role)
  if closure['elf_files']['candidate:usr/sbin/'+role]['sha256']!=files['sbin/rc' if role=='rc' else 'usr/sbin/httpd']['sha256']:
   raise ValueError('Dependency report hash mismatch '+role)
 policy=report('runtime-link/iot-iapp-policy-source.json')
 if policy.get('board')!='WR1200JS' or not policy.get('iapp_compile_gate_enabled') or policy.get('production_ready') is not False:
  raise ValueError('Paired IAPP policy required')
 runtime=report('runtime-link/iot-runtime-source.json')
 entry=report('runtime-link/iot-restart-entry-source.json')
 for label,manifest,required in (
  ('runtime',runtime,('normal_shutdown_controller_linked','normal_shutdown_dispatch_bound',
    'normal_shutdown_notification_bound','normal_shutdown_initial_active_arm_bound',
    'normal_shutdown_cold_active_arm_bound','normal_shutdown_cold_routed_handoff_bound',
    'normal_shutdown_mailbox_active_arm_bound',
    'initial_off_admission','off_reopen_admission')),
  ('restart',entry,('private_restart_hook_bound','initial_restart_hook_bound',
    'historical_radio_on_hook_bound','cold_radio_on_hook_bound','owned_radio_off_hook_bound'))):
  if manifest.get('board')!='WR1200JS' or manifest.get('production_ready') is not False:
   raise ValueError('Paired experimental '+label+' manifest required')
  if any(manifest.get(name) is not True for name in required):
   raise ValueError('Missing paired '+label+' lifecycle binding')
 kernel=read('ra2-no-host-module/kernel.config').decode()
 if 'CONFIG_PM=y' in kernel:raise ValueError('Unverified PCI suspend binding: CONFIG_PM=y')
 inputs=['ra2-no-host-module/kernel.config','ra2-no-host-module/source-manifest.json',
         'runtime-link/iot-runtime-source.json','runtime-link/iot-restart-entry-source.json',
         'runtime-link/iot-iapp-policy-source.json']
 return {'board':'WR1200JS','source_revision':revision,'files':files,
         'input_sha256':{n:hashlib.sha256(read(n)).hexdigest() for n in inputs},
         'module_romfs_destination_verified':False,'target_pair_hashes_verified':True,'lifecycle_manifest_contract_verified':True,'production_installed':False,
         'trx_inclusion_verified':False,'physical_runtime_verified':False}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('results',type=Path)
 p.add_argument('--revision',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise SystemExit('Refuse existing package manifest')
 a.output.write_text(json.dumps(build(a.results,a.revision),indent=2)+'\n')
 print('PASS paired candidate identities recorded; image assembly and runtime acceptance remain unverified')
