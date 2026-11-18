"""Pairing rejects mismatched binaries, closure, policy and kernel evidence."""
from pathlib import Path
import tempfile,runpy,json,hashlib,struct
here=Path(__file__).resolve().parent
module=runpy.run_path(str(here/'package-candidate-pair.py'));build=module['build'];files=module['FILES']
def elf(kind):
 b=bytearray(64);b[:6]=b'\x7fELF\x01\x01';struct.pack_into('<HH',b,16,kind,8);return bytes(b)
with tempfile.TemporaryDirectory(prefix='wr-pair-check-') as d:
 root=Path(d)
 def put(n,b):
  p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 def report(n,r):put(n,json.dumps(r).encode())
 for target,source in files.items():put(source,b'#!/bin/sh\n' if target.endswith('.sh') else elf(1 if target.startswith('driver:') else 2))
 report('ra2-no-host-module/target-result.json',{'target_module_linked':True,'module_sha256':hashlib.sha256(elf(1)).hexdigest(),'production_installed':False,'runtime_verified':False})
 for role in ('rc','httpd'):
  report('runtime-link/'+role+'-dependency-closure.json',{'dependency_closure_verified':True,'errors':[],'production_installed':False,'elf_files':{'candidate:usr/sbin/'+role:{'sha256':hashlib.sha256(elf(2)).hexdigest()}}})
 report('runtime-link/iot-iapp-policy-source.json',{'board':'WR1200JS','iapp_compile_gate_enabled':True,'production_ready':False})
 report('ra2-no-host-module/source-manifest.json',{})
 runtime={'board':'WR1200JS','production_ready':False,'normal_shutdown_controller_linked':True,
  'normal_shutdown_dispatch_bound':True,'normal_shutdown_notification_bound':True,
  'normal_shutdown_initial_active_arm_bound':True,'normal_shutdown_cold_active_arm_bound':True,
  'normal_shutdown_cold_routed_handoff_bound':True,'normal_shutdown_mailbox_active_arm_bound':True,'configuration_ram_control_bound':True,'configuration_snapshot_verified':True,'configuration_flash_bound':False,'configuration_loaded_promotion_bound':False,'initial_off_admission':True,'off_reopen_admission':True}
 entry={'board':'WR1200JS','production_ready':False,'private_restart_hook_bound':True,
  'initial_restart_hook_bound':True,'historical_radio_on_hook_bound':True,
  'cold_radio_on_hook_bound':True,'owned_radio_off_hook_bound':True}
 report('runtime-link/iot-runtime-source.json',runtime)
 report('runtime-link/iot-restart-entry-source.json',entry)
 edit={'board':'WR1200JS','edit_startup_attempt_prepared':True,'view_startup_attempt_prepared':True,
       'native_capabilities_verified':True,'http_view_bound':True,'http_edit_bound':True,'http_runtime_toggle_bound':True,'http_bound':True,
       'target_verified':False,'runtime_verified':False,'production_ready':False}
 report('runtime-link/iot-edit-view-source.json',edit)
 put('ra2-no-host-module/kernel.config',b'# CONFIG_PM is not set\n')
 r=build(root,'a'*40);assert not r['trx_inclusion_verified'] and 'sbin/rc' in r['files'] and r['lifecycle_manifest_contract_verified']
 mutations=[('runtime-link/rc',elf(1)),('ra2-no-host-module/kernel.config',b'CONFIG_PM=y\n'),('runtime-link/httpd',b'bad ELF'),('runtime-link/iot-iapp-policy-source.json',b'{}'),('ra2-no-host-module/target-result.json',b'{}')]
 # Earlier packaging accepted empty lifecycle evidence. Exercise missing,
 # explicitly disabled and truthy-but-untyped bindings before any image stage.
 for n,m in [('runtime-link/iot-runtime-source.json',runtime),('runtime-link/iot-restart-entry-source.json',entry),('runtime-link/iot-edit-view-source.json',edit)]:
  mutations.append((n,b'{}'))
  for field,value in m.items():
   broken=dict(m);broken.pop(field);mutations.append((n,json.dumps(broken).encode()))
   if value is True:
    for invalid in [False,1,'true']:
     broken=dict(m);broken[field]=invalid;mutations.append((n,json.dumps(broken).encode()))
   if value is False:
    for invalid in [True,0,'false']:
     broken=dict(m);broken[field]=invalid;mutations.append((n,json.dumps(broken).encode()))
 for n,blob in mutations:
  previous=(root/n).read_bytes();put(n,blob)
  try:build(root,'a'*40)
  except (ValueError,KeyError):pass
  else:raise AssertionError('Unsafe pair accepted '+n)
  put(n,previous)
 p=root/'runtime-link/rc';p.unlink();p.symlink_to(root/'runtime-link/httpd')
 try:build(root,'a'*40)
 except ValueError:pass
 else:raise AssertionError('symlink accepted')
print('PASS paired package evidence: exact ELF type/hash closure, experimental module/IAPP policy and typed lifecycle manifests, PM refusal, symlink refusal; synthetic inputs, no target/image claim')
