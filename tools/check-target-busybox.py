#!/usr/bin/env python3
"""First BusyBox audit gate: exact-image identity, shell syntax and applet probes.

Does not run service lifecycle scripts or establish hardware/runtime acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('tree',type=Path)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();trunk=a.tree/'trunk';root=(trunk/'romfs').resolve()
binary=root/'bin/busybox';config=trunk/'user/busybox/busybox-1.24.x/.config'
qemu=shutil.which('qemu-mipsel-static') or shutil.which('qemu-mipsel')
if not qemu:raise SystemExit('Target QEMU is required')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(args,**options):
    return subprocess.run([qemu,'-L',str(root),str(binary),*args],
        capture_output=True,timeout=10,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'},**options)
report={'schema':1,'runtime_verified':False,'whole_service_audit_complete':False,
        'busybox_sha256':digest(binary),'config_sha256':digest(config),
        'scope':'image shell syntax and bounded applet probes; service interactions unverified',
        'scripts':[],'other_interpreters':[],'checks':{}}
listing=run(['--list']);applets=listing.stdout.decode(errors='replace').splitlines()
report['applets']=applets;report['checks']['applet_inventory']=listing.returncode==0
report['checks']['shell_type_builtin']=run(['sh','-c','type type >/dev/null 2>&1']).returncode==0
report['checks']['mwan_shell_arithmetic']=run(['sh','-c','i=1; count=$((i-1)); last=$i; j=$((i-1)); test "$count:$last:$j" = "0:1:0"']).returncode==0
report['command_builtin_available']=run(['sh','-c','type command >/dev/null 2>&1']).returncode==0
for directory,dirs,files in os.walk(root,followlinks=False):
    dirs[:]=sorted(name for name in dirs if not (Path(directory)/name).is_symlink())
    for name in sorted(files):
        path=Path(directory)/name
        if path.is_symlink() or not path.is_file():continue
        with path.open('rb') as f:first=f.read(256).split(b'\n',1)[0]
        words=first.split()
        shell=bool(words) and (words[0] in (b'#!/bin/sh',b'#!/bin/ash') or words[:2]==[b'#!/usr/bin/env',b'sh'])
        if first.startswith(b'#!') and not shell:
            report['other_interpreters'].append(str(path.relative_to(root)));continue
        if not shell and path.suffix!='.sh':continue
        if len(report['scripts'])>=512:raise SystemExit('Shell inventory limit exceeded; audit incomplete')
        data=path.read_bytes()
        item={'path':str(path.relative_to(root)),'sha256':hashlib.sha256(data).hexdigest(),
              'command_v_requires_review':b'command -v' in data and not report['command_builtin_available']}
        try:item['syntax_exit']=run(['sh','-n',str(path)]).returncode
        except subprocess.TimeoutExpired:item['syntax_exit']=None
        report['scripts'].append(item)
report['checks']['all_discovered_shell_syntax']=bool(report['scripts']) and all(
    item['syntax_exit']==0 for item in report['scripts'])
report['checks']['command_v_supported_or_avoided']=not any(
    item['command_v_requires_review'] for item in report['scripts'])
with tempfile.TemporaryDirectory(prefix='target-busybox-') as tmp:
    target=Path(tmp)/'canonical';target.mkdir()
    alias=Path(tmp)/'alias';alias.symlink_to(target,target_is_directory=True)
    probe=run(['readlink','-f',str(alias)])
    report['checks']['readlink_follow_exact_options']=probe.returncode==0 and probe.stdout.decode().strip()==str(target.resolve())
    report['checks']['readlink_follow_config']=all(key+'=y' in config.read_text().splitlines() for key in ('CONFIG_READLINK','CONFIG_FEATURE_READLINK_FOLLOW'))
    sample=Path(tmp)/'serial';sample.write_bytes(b'unit-test-only\n')
    probe=run(['hexdump','-v','-n','258','-e','1/1 "%02x"',str(sample)])
    report['checks']['usbip_hexdump_exact_options']=probe.returncode==0 and probe.stdout==sample.read_bytes().hex().encode()
    import fcntl
    lock=Path(tmp)/'lock'
    with lock.open('w+') as held:
        fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with lock.open('r+') as competing:
            probe=run(['flock','-x','-n',str(competing.fileno())],pass_fds=(competing.fileno(),))
            report['checks']['flock_contention_refused']=probe.returncode!=0
        fcntl.flock(held,fcntl.LOCK_UN)
        probe=run(['flock','-x','-n',str(held.fileno())],pass_fds=(held.fileno(),))
        report['checks']['flock_descriptor_options']=probe.returncode==0
report['success']=all(report['checks'].values())
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(('PASS' if report['success'] else 'FAIL')+' target BusyBox audit gate; full service/runtime audit remains open')
raise SystemExit(0 if report['success'] else 1)
