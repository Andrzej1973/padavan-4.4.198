#!/usr/bin/env python3
"""Run shipped MIPS manager, child validators and store inside an isolated PRoot."""
import argparse
import ast
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('romfs',type=Path)
p.add_argument('--amneziawg',action='store_true')
p.add_argument('--output',required=True,type=Path)
a=p.parse_args();image=a.romfs.resolve()
proot=shutil.which('proot');qemu=shutil.which('qemu-mipsel-static')
if not proot or not qemu:raise SystemExit('PRoot and static target QEMU are required')
report={'scope':'shipped MIPS manager/validator fork-exec and private file integration under QEMU/PRoot; no physical acceptance or network mutations',
        'physical_runtime_verified':False,'cases':[],'binaries':{}}
key=base64.b64encode(bytes(range(1,33))).decode();public=base64.b64encode(bytes(range(33,65))).decode()
base=f'[Interface]\nPrivateKey = {key}\nAddress = 10.9.0.2/32\nDNS = 1.1.1.1\nMTU = 1420\n[Peer]\nPublicKey = {public}\nEndpoint = never-resolve.invalid:51820\nAllowedIPs = 0.0.0.0/0\n'
awg=base.replace('[Peer]','Jc = 4\nJmin = 16\nJmax = 64\n[Peer]')
with tempfile.TemporaryDirectory(prefix='wrvpn-mips-manager-') as temporary:
 jail=Path(temporary)
 # Copy only libraries and the exact shipped binaries. Do not reuse image /etc
 # symlinks, bind host storage, or depend on binfmt_misc registration.
 for relative in ('lib','usr/lib'):
  source=image/relative
  if source.is_dir():shutil.copytree(source,jail/relative,symlinks=True,dirs_exist_ok=True)
 binaries=['usr/sbin/wr-vpn-profile','usr/libexec/wrvpn/validate-wg','bin/busybox']
 if a.amneziawg:binaries.append('usr/libexec/wrvpn/validate-awg')
 for relative in binaries:
  source=image/relative;target=jail/relative;target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(source,target);target.chmod(0o700)
  digest=hashlib.sha256(source.read_bytes()).hexdigest()
  assert hashlib.sha256(target.read_bytes()).hexdigest()==digest
  report['binaries'][relative]=digest
 for relative in ('etc/storage','dev','proc','tmp'):(jail/relative).mkdir(parents=True,exist_ok=True)
 (jail/'etc/storage').chmod(0o700)
 command=[proot,'-r',str(jail),'-q',qemu,'-b','/dev/null','-b','/proc','-w','/','/usr/sbin/wr-vpn-profile']
 env=dict(os.environ,PROOT_NO_SECCOMP='1',LC_ALL='C')
 def run(name,args,data='',expected=0):
  result=subprocess.run([*command,*args],input=data.encode(),capture_output=True,timeout=30,env=env)
  # Synthetic configs only. Avoid including full stdout in assertion messages.
  assert result.returncode==expected,(name,'exit',result.returncode,result.stderr.decode(errors='replace'))
  assert not result.stderr,(name,'unexpected diagnostic',result.stderr.decode(errors='replace'))
  report['cases'].append({'case':name,'passed':True})
  return result.stdout
 protocol='amneziawg' if a.amneziawg else 'wireguard';first=awg if a.amneziawg else base
 assert run('create-first',['create','1',protocol],first)==b'saved\t1\t1\n'
 assert run('create-independent-WG',['create','2','wireguard'],base)==b'saved\t2\t1\n'
 assert run('export-first',['export','1'])==first.encode()
 assert run('export-WG',['export','2'])==base.encode()
 store=jail/'etc/storage/wrvpn'
 before={str(id):(store/str(id)).read_bytes() for id in (1,2)}
 labels={'1\t'+('AWG1' if a.amneziawg else 'WG1')+'\t1','2\tWG2\t1'}
 assert set(run('metadata-list',['list']).decode().splitlines())==labels
 assert not run('duplicate-refused',['create','2','wireguard'],base,5)
 assert not run('invalid-key-refused',['create','3','wireguard'],base.replace(key,'invalid'),2)
 assert not run('hook-refused',['create','3','wireguard'],base.replace('[Peer]','PostUp = must-not-run\n[Peer]'),2)
 assert not (store/'3').exists()
 helper=jail/'usr/libexec/wrvpn/validate-wg';held=helper.with_name('validate-wg-held');helper.rename(held)
 assert not run('missing-helper-refused',['create','3','wireguard'],base,3)
 assert not (store/'3').exists()
 assert all((store/id).read_bytes()==data for id,data in before.items())
 held.rename(helper)
 assert run('first-profile-preserved',['export','1'])==first.encode()
 edited=base.replace('10.9.0.2/32','10.9.0.9/32')
 assert run('edit-WG',['edit','2'],edited)==b'saved\t2\t2\n'
 assert run('export-edited-WG',['export','2'])==edited.encode()
 assert run('delete-first',['delete','1'])==b'deleted\t1\t2\n'
 assert not run('delete-missing',['delete','1'],'',5)
 assert run('list-after-delete',['list'])==b'2\tWG2\t2\n'
 for path in (store/'1',store/'2',store/'.lock'):assert path.stat().st_mode&0o777==0o600
 assert store.stat().st_mode&0o777==0o700
 # File-only storage round trip with the shipped tar, shell and chmod.
 # This operates only on synthetic records in the temporary PRoot jail.
 helper_tree=ast.parse(Path(__file__).with_name('prepare-storage-permissions.py').read_text())
 storage_helper=next(ast.literal_eval(n.value) for n in helper_tree.body
                     if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='HELPER' for t in n.targets))
 shipped_storage=image/'sbin/mtd_storage.sh'
 assert storage_helper.strip() in shipped_storage.read_text(), 'shipped storage helper differs'
 report['storage_script_sha256']=hashlib.sha256(shipped_storage.read_bytes()).hexdigest()
 (jail/'bin/chmod').symlink_to('busybox')
 repair=jail/'tmp/repair.sh'
 repair.write_text(storage_helper+'\nfunc_wrvpn_private /etc/storage\n')
 shell_command=command[:-1]+['/bin/busybox']
 def storage_run(name,arguments):
  result=subprocess.run([*shell_command,*arguments],capture_output=True,timeout=30,
                        env=dict(env,PATH='/bin'))
  assert result.returncode==0 and not result.stderr,(name,result.returncode,result.stderr)
  report['cases'].append({'case':name,'passed':True})
 snapshot={name:(store/name).read_bytes() for name in ('1','2','.lock')}
 storage_run('target-file-only-archive',['sh','-c','cd /etc/storage && /bin/busybox tar cf /tmp/profiles.tar wrvpn/1 wrvpn/2 wrvpn/.lock'])
 shutil.rmtree(store)
 storage_run('target-file-only-extract',['sh','-c','umask 022; /bin/busybox tar xf /tmp/profiles.tar -C /etc/storage'])
 assert store.stat().st_mode&0o777==0o755
 assert not run('unrepaired-store-refused',['list'],'',3)
 storage_run('target-storage-permission-repair',['sh','/tmp/repair.sh'])
 assert store.stat().st_mode&0o777==0o700
 assert all((store/name).read_bytes()==content and (store/name).stat().st_mode&0o777==0o600
            for name,content in snapshot.items())
 assert run('restored-edited-profile-export',['export','2'])==edited.encode()
 assert run('restored-list-retains-deletion',['list'])==b'2\tWG2\t2\n'
 assert not run('restored-tombstone-refuses-reuse',['create','1',protocol],first,5)
 report['private_modes_passed']=True
 report['profiles_unchanged_after_rejections']=True
 report['case_count']=len(report['cases'])
a.output.write_text(json.dumps(report,indent=2)+'\n')
print('PASS shipped MIPS manager: child native validators, independent private records, exact exports, edit/delete revision and tombstone, rejection paths and preserved profiles; QEMU/PRoot, not physical VPN proof')
