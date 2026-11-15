#!/usr/bin/env python3
"""Install paired IAPP policy only in an experimental WR runtime source tree."""
from pathlib import Path
import argparse,json,runpy,hashlib,subprocess
here=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
root=a.source.resolve();report=root/'iot-iapp-policy-source.json'
if report.exists():raise SystemExit('IAPP policy already prepared')
runtime=json.loads((root/'iot-runtime-source.json').read_text())
if runtime.get('board')!='WR1200JS' or runtime.get('production_ready') is not False:
 raise SystemExit('Experimental WR1200JS runtime preparation required')
gate=root/'trunk/user/rc/wr-iot/restart-iapp-policy.h'
if gate.is_symlink() or not gate.resolve().is_relative_to(root) or not gate.is_file() or gate.read_text()!='#define WR_IOT_IAPP_POLICY_PREPARED 0\n':
 raise SystemExit('Exact inactive IAPP policy gate required')
fw=root/'trunk/user/rc/firewall_ex.c';script=root/'trunk/user/ralinkiappd/iappd.sh'
for f in (fw,script):
 if f.is_symlink() or not f.is_file() or not f.resolve().is_relative_to(root):raise SystemExit('Refuse missing/symlink/outside source')
old_fw=fw.read_bytes();old_sh=script.read_bytes()
pair=runpy.run_path(str(here/'prepare-iappd-policy-pair.py'))['prepare_pair']
new_fw,new_sh=pair(old_fw.decode(),old_sh.decode())
# Syntax-check generated script without executing daemon/firewall commands.
subprocess.run(['sh','-n'],input=new_sh.encode(),check=True)
meta={'board':'WR1200JS','production_ready':False,'iapp_root_launch_bound':True,'iapp_compile_gate_enabled':True,
 'firewall_policy_builder_bound':True,'script_firewall_mutation_removed':True,
 'inputs_sha256':{'firewall':hashlib.sha256(old_fw).hexdigest(),'script':hashlib.sha256(old_sh).hexdigest()},
 'outputs_sha256':{'firewall':hashlib.sha256(new_fw.encode()).hexdigest(),'script':hashlib.sha256(new_sh.encode()).hexdigest()}}
# Any filesystem failure invalidates this entire candidate tree; no release
# consumer may accept it without this final manifest and matching output hashes.
fw.write_text(new_fw);script.write_text(new_sh);gate.write_text("#define WR_IOT_IAPP_POLICY_PREPARED 1\n");report.write_text(json.dumps(meta,indent=2)+'\n')
print('PASS experimental paired IAPP policy staged; guarded root launch enabled in candidate; target/runtime remain unverified')
