#!/usr/bin/env python3
"""Describe one coherent experimental driver/userspace pair for image assembly."""
import argparse,hashlib,json,re,struct,runpy
from pathlib import Path
selector_verify=runpy.run_path(str(Path(__file__).with_name('verify-generation-selector-link.py')))['verify']
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
 modern_report='runtime-link/modern-iot-candidate.json'
 modern=report(modern_report)
 if modern.get('board')!='WR1200JS' or modern.get('candidate_only') is not True or modern.get('uses_existing_iot_protocol') is not True:
  raise ValueError('Expected isolated Modern IoT source binding')
 if b'modern/modern-iot.js\0' not in read(FILES['usr/sbin/httpd']):
  raise ValueError('Missing linked Modern IoT route')
 modern_files={}
 for name in ('index.html','wifi.js','modern-iot.js'):
  source='runtime-link/modern/'+name
  payload=read(source)
  digest=hashlib.sha256(payload).hexdigest()
  if not payload or digest!=modern.get('sha256',{}).get('trunk/user/www/modern/'+name):
   raise ValueError('Modern IoT candidate asset mismatch: '+name)
  modern_files['www/modern/'+name]={'source':source,'bytes':len(payload),'sha256':digest}
 module=report('ra2-no-host-module/target-result.json')
 driver_source=report('ra2-no-host-module/source-manifest.json')
 api=driver_source.get('linux_open_api',{})
 if any(api.get(name) is not True for name in ('close_busy_pre_mutation','ra2_rekey_counted_bound')):
  raise ValueError('Paired driver CLOSE pre-mutation busy contract/ra2 timer fence required')
 if type(api.get('close_busy_request_opcode')) is not int or api['close_busy_request_opcode']!=21:
  raise ValueError('Explicit driver CLOSE21 contract required')
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
 selector=report('runtime-link/generation-selector-link.json')
 if any(selector.get(name) is not True for name in ('selector_link_provider_verified','selector_caller_relocation_verified','selector_object_strong_definition_verified')) or selector.get('rc_sha256')!=files['sbin/rc']['sha256'] or selector.get('runtime_verified') is not False or selector.get('production_installed') is not False:
  raise ValueError('Strong generation selector link proof for this RC required')
 if selector!=selector_verify(root/'runtime-link',root/'runtime-link/rc'):
  raise ValueError('Selector link report differs from actual evidence/binary')
 if policy.get('board')!='WR1200JS' or not policy.get('iapp_compile_gate_enabled') or policy.get('production_ready') is not False:
  raise ValueError('Paired IAPP policy required')
 runtime=report('runtime-link/iot-runtime-source.json')
 if type(runtime.get('close_busy_request_opcode')) is not int or runtime['close_busy_request_opcode']!=21:
  raise ValueError('Explicit RC CLOSE21 contract required')
 entry=report('runtime-link/iot-restart-entry-source.json')
 edit=report('runtime-link/iot-edit-view-source.json')
 if edit.get('board')!='WR1200JS' or any(edit.get(name) is not True for name in
  ('edit_startup_attempt_prepared','view_startup_attempt_prepared','native_capabilities_verified','http_view_bound','http_edit_bound','http_runtime_toggle_bound','http_bound')) or any(edit.get(name) is not False for name in ('target_verified','runtime_verified','production_ready')):
  raise ValueError('Complete prepared edit/view metadata with explicit acceptance gates required')
 if runtime.get('configuration_flash_bound') is not False or runtime.get('configuration_loaded_promotion_bound') is not False:
  raise ValueError('Current configuration candidate must retain flash/cold-promotion acceptance gates')
 for label,manifest,required in (
  ('runtime',runtime,('normal_shutdown_controller_linked','normal_shutdown_dispatch_bound',
    'normal_shutdown_notification_bound','normal_shutdown_initial_active_arm_bound',
    'normal_shutdown_cold_active_arm_bound','normal_shutdown_cold_routed_handoff_bound',
    'normal_shutdown_mailbox_active_arm_bound','configuration_ram_control_bound','configuration_snapshot_verified','generation_selector_strong_binding_prepared','close_busy_pre_mutation_bound',
    'radio_off_terminal_publication_linked','radio_off_finalizer_retry_observation_linked','initial_off_admission','off_reopen_admission')),
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
         'runtime-link/iot-iapp-policy-source.json','runtime-link/iot-edit-view-source.json','runtime-link/generation-selector-link.json',modern_report]
 return {'board':'WR1200JS','source_revision':revision,'files':files,'modern_files':modern_files,
         'input_sha256':{n:hashlib.sha256(read(n)).hexdigest() for n in inputs},
         'module_romfs_destination_verified':False,'target_pair_hashes_verified':True,'lifecycle_manifest_contract_verified':True,'production_installed':False,
         'trx_inclusion_verified':False,'physical_runtime_verified':False}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('results',type=Path)
 p.add_argument('--revision',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise SystemExit('Refuse existing package manifest')
 a.output.write_text(json.dumps(build(a.results,a.revision),indent=2)+'\n')
 print('PASS paired candidate identities recorded; image assembly and runtime acceptance remain unverified')
