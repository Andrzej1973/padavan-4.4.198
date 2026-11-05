#!/usr/bin/env python3
"""Bind isolated Method1 hardware/thaw and retained failure stop."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();mp=Path(str(src)+'.manifest.json')
raw=mp.read_bytes();m=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (m.get('production_installed') is not False or m.get('target_compiled') is not False
 or 'mcu_boot_loader_abort' not in m or 'mcu_boot_loader_bind' in m or actual!=m['merged_driver_sha256']):
 p.error('Expected unchanged isolated loader-abort candidate')
name='mcu/andes_mt.c';text=(src/name).read_text()
start=text.index('static NDIS_STATUS AndesMTLoadFwMethod1(')
end=text.index('static NDIS_STATUS AndesMTLoadFwMethod2(',start)
body=text[start:end]
anchor='  ret=wr_iot_mcu_boot_rom_observe(ad,boot,wr_iot_boot_restart_acked);\n  if(ret)goto done;'
if body.count(anchor)!=1:p.error('Changed Method1 ROM observer anchor')
body=body.replace(anchor,anchor+'\n  ret=wr_iot_mcu_boot_hardware_prepare(ad,boot);\n  if(ret)goto done;\n  ret=wr_iot_mcu_boot_thaw(ad,boot);\n  if(ret)goto done;')
anchor='done:\n\tif (ret) Ctl->Stage = FW_NO_INIT;'
if body.count(anchor)!=1:p.error('Changed Method1 cleanup anchor')
body=body.replace(anchor,anchor+'''
#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 if(boot&&ret){
  (void)wr_iot_mcu_boot_loader_abort(ad,boot);
  return ret;
 }
#endif
''')
(src/name).write_text(text[:start]+body+text[end:])
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest()}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_boot_loader_bind']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,
 'target_compiled':False,'runtime_verified':False,'normal_admission':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
