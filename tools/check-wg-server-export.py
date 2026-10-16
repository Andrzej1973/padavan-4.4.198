#!/usr/bin/env python3
"""Run actual server configuration/export functions against synthetic NVRAM/tools."""
from pathlib import Path
import argparse
import hashlib
import os
import shlex
import shutil
import subprocess
import tempfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--target-root',type=Path,help='Run the shipped script functions with image BusyBox and applets under QEMU')
args=parser.parse_args()
romfs=args.target_root.resolve() if args.target_root else None
source_path=(romfs/'usr/bin/wgs.sh') if romfs else (Path(__file__).resolve().parent.parent/'overlay/padavan-4.4/trunk/user/amneziawg/wgs.sh')
source=source_path.read_text()
helper=source[source.index('wg_awg_options()'):source.index('wg_setconf()')]
configure=source[source.index('wg_setconf()'):source.index('wg_prepare()')]
export=source[source.index('wg_export()'):source.index('\ncase "$1" in\n')]
with tempfile.TemporaryDirectory(prefix='wg-server-export-', dir=Path(__file__).resolve().parent.parent) as temp:
 root=Path(temp);script=root/'run.sh';server=root/'server.conf';client=root/'client.conf'
 prelude='''umask 077
WG=fixture_wg
IF_NAME=synthetic
IF_PRIVATE=CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC=
PORT=51820
WAN_ADDR=example.invalid
EXPORT_CONF="$SAFE_TEMP/client.conf"
nvram(){
 case "$2" in
 vpns_num_x) echo 1;;
 vpns_user_x0) echo client;;
 vpns_pass_x0) echo AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=;;
 vpns_public_x0|vpns_wg_public) echo BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=;;
 vpns_vnet) echo 10.0.0.0;;
 vpns_addr_x0) echo 2;;
 lan_ipaddr) echo 10.0.0.1;;
 vpns_awg_jc) printf '%s' "$JCVALUE";;
 vpns_awg_jmin) printf '%s' "${JMINVALUE:-16}";;
 vpns_awg_jmax) printf '%s' "${JMAXVALUE:-64}";;
 vpns_awg_s1) printf '%s' "${S1VALUE:-10}";;
 vpns_awg_s2) printf '%s' "${S2VALUE:-20}";;
 vpns_awg_h1) printf '%s' "${H1VALUE:-1}";;
 vpns_awg_h2) printf '%s' "${H2VALUE:-2}";;
 vpns_awg_h3) printf '%s' "${H3VALUE:-3}";;
 vpns_awg_h4) printf '%s' "${H4VALUE:-4}";;
 esac
}
is_started(){ return 0; }
log(){ :; }
die(){ return 1; }
fixture_wg(){
 case "$1" in
 pubkey) echo BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=;;
 setconf) cp "$3" "$SAFE_TEMP/server.conf";;
 show) return 0;;
 *) return 1;;
 esac
}
'''
 configure=configure.replace('"/tmp/${IF_NAME}.conf.$$"','"$SAFE_TEMP/config.tmp"')
 script.write_text(prelude+helper+configure+export+'\nwg_setconf && wg_export client\n')
 scenarios=[
  ('amneziawg',{'JCVALUE':'4'},True),
  ('wireguard',{'JCVALUE':'invalid'},True),
  ('amneziawg',{'JCVALUE':'4\nH1=9'},False),
  ('amneziawg',{'JCVALUE':'x'},False),
  ('amneziawg',{'JCVALUE':'1'*11},False),
  ('amneziawg',{'JCVALUE':'129'},False),
  ('amneziawg',{'JCVALUE':'4','JMINVALUE':'64','JMAXVALUE':'64'},False),
  ('amneziawg',{'JCVALUE':'4','S1VALUE':'10','S2VALUE':'66'},False),
  ('amneziawg',{'JCVALUE':'4','H1VALUE':'7','H2VALUE':'7'},False),
  ('amneziawg',{'JCVALUE':'4','H1VALUE':'4294967295'},True),
  ('amneziawg',{'JCVALUE':'4','H1VALUE':'4294967296'},False),
  ('amneziawg',{'JCVALUE':'4','H1VALUE':'0000000007','H2VALUE':'7'},False),
 ]
 shell=[os.environ.get('SH') or shutil.which('sh') or r'C:\Program Files\Git\bin\bash.exe']
 env=dict(os.environ,SAFE_TEMP=str(root))
 if romfs:
  binary=romfs/'bin/busybox'
  qemu=shutil.which('qemu-mipsel-static') or shutil.which('qemu-mipsel')
  if not qemu or not binary.is_file():raise SystemExit('Exact image BusyBox and target QEMU required')
  shell=[qemu,'-L',str(romfs),str(binary),'sh']
  providers=root/'providers';providers.mkdir()
  applets=('awk','cat','chmod','cp','rm','sed','seq','tee','wc')
  inventory=subprocess.run([*shell[:-1],'--list'],capture_output=True,text=True,timeout=15)
  missing=set(applets)-set(inventory.stdout.splitlines())
  if inventory.returncode or missing:raise SystemExit('Required target applets unavailable: '+','.join(sorted(missing)))
  # Host sh only transports exec. No host applet fallback is in PATH.
  for applet in applets:
   wrapper=providers/applet
   wrapper.write_text('#!/bin/sh\nexec '+shlex.join(shell[:-1]+[applet])+' "$@"\n')
   wrapper.chmod(0o700)
  env.update(PATH=str(providers),LC_ALL='C')
  print('TARGET BusyBox SHA256 '+hashlib.sha256(binary.read_bytes()).hexdigest())
  print('Shipped wgs.sh SHA256 '+hashlib.sha256(source_path.read_bytes()).hexdigest())
 for module,values,ok in scenarios:
  for path in [server,client]:
   if path.exists():path.unlink()
  # Module selection is supplied externally only in this isolated fixture.
  result=subprocess.run([*shell,str(script)],env=dict(env,MODULE=module,**values),capture_output=True,text=True,timeout=30)
  assert (result.returncode==0)==ok,(module,values,result.stderr)
  if not ok:
   assert not server.exists() and not client.exists();continue
  supplied=['Jc','Jmin','Jmax','S1','S2','H1','H2','H3','H4']
  expected={'Jc':values.get('JCVALUE',''),'Jmin':values.get('JMINVALUE','16'),'Jmax':values.get('JMAXVALUE','64'),'S1':values.get('S1VALUE','10'),'S2':values.get('S2VALUE','20'),'H1':values.get('H1VALUE','1'),'H2':values.get('H2VALUE','2'),'H3':values.get('H3VALUE','3'),'H4':values.get('H4VALUE','4')}
  for key in supplied:
   line=key+' = '+expected[key]
   assert (line in server.read_text())==(module=='amneziawg')
   assert (line in client.read_text())==(module=='amneziawg')
  assert result.stdout==client.read_text()
 # Exercise actual startup control flow with all network operations mocked.
 startup=source[source.index('wg_start_abort()'):source.index('wg_addclient()')]
 events=root/'events'
 startup_prelude='''IF_NAME=synthetic
IF_ADDR=10.0.0.1
IF_MTU=1420
PORT=51820
MODULE=wireguard
WG=fixture_wg
die(){ exit 1; }
error(){ exit 1; }
log(){ printf 'log %s\\n' "$*" >> "$EVENTS"; }
is_started(){ test "${EXISTING:-0}" = 1; }
wg_prepare(){ :; }
wg_setconf(){ test "${FAIL:-}" != setconf; }
fixture_wg(){ return 0; }
ip(){
 printf '%s\\n' "$*" >> "$EVENTS"
 case "$*" in
 'link add '*) test "${FAIL:-}" != add;;
 'link set dev synthetic mtu '*) test "${FAIL:-}" != mtu;;
 'addr add '*) test "${FAIL:-}" != address;;
 'addr show '*) test "${FAIL:-}" = observe || printf 'inet 10.0.0.1/24\\n'; return 0;;
 'link set synthetic up') test "${FAIL:-}" != up;;
 'link del synthetic') test "${CLEANUP_FAIL:-0}" != 1;;
 *) return 1;;
 esac
}
'''
 script.write_text(startup_prelude+startup+'\nwg_start\n')
 for failure in ('','add','mtu','address','observe','setconf','up'):
  for existing in ('0','1'):
   events.write_text('')
   result=subprocess.run([*shell,str(script)],env=dict(env,EVENTS=str(events),FAIL=failure,EXISTING=existing),capture_output=True,text=True,timeout=30)
   calls=events.read_text().splitlines()
   assert (result.returncode==0)==(not failure and existing=='0'),(failure,existing,result.stderr)
   expected_cleanup=existing=='0' and failure not in ('','add')
   assert ('link del synthetic' in calls)==expected_cleanup,(failure,existing,calls)
   if existing=='1':assert calls==[],calls
 events.write_text('')
 result=subprocess.run([*shell,str(script)],env=dict(env,EVENTS=str(events),FAIL='setconf',CLEANUP_FAIL='1'),capture_output=True,text=True,timeout=30)
 assert result.returncode!=0 and 'log synthetic startup cleanup failed' in events.read_text()
print(('TARGET BusyBox/QEMU: ' if romfs else 'HOST shell: ')+'PASS synthetic server/export functions: AWG validation, WG exclusion and failed-start cleanup; real network lifecycle unverified')
