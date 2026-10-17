#!/usr/bin/env python3
"""Inspect shipped MIPS profile tools and execute data-only validator fixtures."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('romfs',type=Path)
p.add_argument('--output',required=True,type=Path)
p.add_argument('--amneziawg',action='store_true')
a=p.parse_args();root=a.romfs.resolve()
qemu=shutil.which('qemu-mipsel-static') or shutil.which('qemu-mipsel')
if not qemu:raise SystemExit('Target QEMU required')
report={'scope':'MIPS packaging and isolated native parser execution; no profile network lifecycle or physical acceptance',
        'runtime_verified':False,'binaries':{},'cases':[]}
paths={'manager':'usr/sbin/wr-vpn-profile','wireguard':'usr/libexec/wrvpn/validate-wg','amneziawg':'usr/libexec/wrvpn/validate-awg'}
paths.update({'control-wireguard':'usr/libexec/wrvpn/wg','control-amneziawg':'usr/libexec/wrvpn/awg'})
paths.update({'readback-wireguard':'usr/libexec/wrvpn/readback-wg','readback-amneziawg':'usr/libexec/wrvpn/readback-awg'})
paths.update({'service':'usr/sbin/wr-vpn-profiles-service'})
paths.update({'actions':'usr/libexec/wrvpn/action-worker'})
roles=['wireguard']+(['amneziawg'] if a.amneziawg else [])
if not a.amneziawg:
 for role in ('amneziawg','control-amneziawg','readback-amneziawg'):assert not (root/paths[role]).exists(),'unexpected AWG tool'
for role in ['manager','actions',*roles,*['control-'+protocol for protocol in roles],*['readback-'+protocol for protocol in roles]]:
 path=paths[role]
 binary=root/path;data=binary.read_bytes()
 assert data[:6]==b'\x7fELF\x01\x01' and struct.unpack_from('<H',data,18)[0]==8,(role,'not little-endian 32-bit MIPS')
 assert binary.stat().st_mode&0o111,(role,'not executable')
 report['binaries'][role]={'path':path,'sha256':hashlib.sha256(data).hexdigest(),'size':len(data)}
service=root/paths['service']
assert service.exists() and service.stat().st_mode&0o111,('service','not packaged or not executable')
assert service.read_bytes().startswith(b'#!/bin/sh'),('service','not a POSIX shell script')
report['binaries']['service']={'path':paths['service'],
                               'sha256':hashlib.sha256(service.read_bytes()).hexdigest(),
                               'size':service.stat().st_size}
# AWG's legacy /usr/bin/wg alias speaks the amneziawg netlink family. The
# independent manager must use dedicated real binaries for each protocol.
for protocol in roles:
 role='control-'+protocol;binary=root/paths[role]
 assert (protocol+'\0').encode() in binary.read_bytes(),(role,'missing native netlink family')
 result=subprocess.run([qemu,'-L',str(root),str(binary),'--version'],capture_output=True,timeout=15)
 assert result.returncode==0 and result.stdout and not result.stderr,(role,'version invocation failed')
 report['binaries'][role]['version']=result.stdout.decode().strip()
if a.amneziawg:
 assert report['binaries']['control-wireguard']['sha256']!=report['binaries']['control-amneziawg']['sha256'],'protocol controls must be distinct'
key=base64.b64encode(bytes(range(1,33))).decode();public=base64.b64encode(bytes(range(33,65))).decode()
base=f'[Interface]\nPrivateKey = {key}\nAddress = 10.9.0.2/32\nDNS = 1.1.1.1\nMTU = 1420\n[Peer]\nPublicKey = {public}\nEndpoint = never-resolve.invalid:51820\nAllowedIPs = 0.0.0.0/0\n'
awg=base.replace('[Peer]','Jc = 4\nJmin = 16\nJmax = 64\nH1 = 1\n[Peer]')
# Read-only target IPC against the CI host kernel through QEMU, never a router.
# A missing native device must not be reported as matching configuration.
native=base.replace('Address = 10.9.0.2/32\nDNS = 1.1.1.1\nMTU = 1420', 'FwMark = 1465254887').replace('never-resolve.invalid','203.0.113.7')
for protocol in roles:
 for name,interface,index,data in [('missing-device','wrvpn999','4294967295',native),
                                  ('legacy-refused','wg0','1',native),
                                  ('hostname-refused','wrvpn999','1',native.replace('203.0.113.7','never-resolve.invalid'))]:
  r=subprocess.run([qemu,'-L',str(root),str(root/paths['readback-'+protocol]),interface,index],input=data.encode(),capture_output=True,timeout=15)
  assert r.returncode==3 and not r.stdout and not r.stderr,(protocol,name,r.returncode,r.stderr)
  report['cases'].append({'protocol':protocol,'case':'readback-'+name,'accepted':False,'passed':True})
def run(role,name,config,valid):
 r=subprocess.run([qemu,'-L',str(root),str(root/paths[role])],input=config.encode(),capture_output=True,timeout=15)
 assert r.returncode==(0 if valid else 2),(role,name,r.returncode,r.stdout,r.stderr)
 assert r.stderr==b'' and r.stdout==(b'valid client configuration; connectivity unverified\n' if valid else b''),(role,name,'unexpected output')
 report['cases'].append({'protocol':role,'case':name,'accepted':valid,'passed':True})
for role in roles:
 run(role,'ordinary-client',base,True)
 run(role,'AWG-fields',awg,role=='amneziawg')
 run(role,'bad-key',base.replace(key,'invalid'),False)
 run(role,'shell-hook',base.replace('[Peer]','PreUp = touch /must-not-run\n[Peer]'),False)
 run(role,'manual-route-table',base.replace('[Peer]','Table = 51\n[Peer]'),False)
if a.amneziawg:
 for value,valid in [('4294967295',True),('0004294967295',True),('1-4294967295',True),('4294967296',False),('-1',False),('1-4294967296',False),('9-1',False)]:
  run('amneziawg','H1='+value,awg.replace('H1 = 1\n','H1 = '+value+'\n'),valid)
# This runs the shipped CLI without opening a store or creating any profile.
r=subprocess.run([qemu,'-L',str(root),str(root/paths['manager']),'create','../1','wireguard'],capture_output=True,timeout=15)
assert r.returncode==2 and not r.stdout and not r.stderr,('manager invalid-ID gate',r.returncode,r.stderr)
report['manager_invalid_id_passed']=True
a.output.write_text(json.dumps(report,indent=2)+'\n')
print('PASS packaged MIPS profile tools: WG/AWG parser fixtures, 32-bit header limits and CLI input gate; storage/process/network runtime still unverified')
