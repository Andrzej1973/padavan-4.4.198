#!/usr/bin/env python3
"""Run actual server configuration/export functions against synthetic NVRAM/tools."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

source=(Path(__file__).resolve().parent.parent/'overlay/padavan-4.4/trunk/user/amneziawg/wgs.sh').read_text()
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
 ]
 shell=os.environ.get('SH') or shutil.which('sh') or r'C:\Program Files\Git\bin\bash.exe'
 for module,values,ok in scenarios:
  for path in [server,client]:
   if path.exists():path.unlink()
  # Module selection is supplied externally only in this isolated fixture.
  result=subprocess.run([shell,str(script)],env=dict(os.environ,MODULE=module,SAFE_TEMP=str(root),**values),capture_output=True,text=True,timeout=15)
  assert (result.returncode==0)==ok,(module,jc,result.stderr)
  if not ok:
   assert not server.exists() and not client.exists();continue
  supplied=['Jc','Jmin','Jmax','S1','S2','H1','H2','H3','H4']
  expected={'Jc':values.get('JCVALUE',''),'Jmin':values.get('JMINVALUE','16'),'Jmax':values.get('JMAXVALUE','64'),'S1':values.get('S1VALUE','10'),'S2':values.get('S2VALUE','20'),'H1':values.get('H1VALUE','1'),'H2':values.get('H2VALUE','2'),'H3':values.get('H3VALUE','3'),'H4':values.get('H4VALUE','4')}
  for key in supplied:
   line=key+' = '+expected[key]
   assert (line in server.read_text())==(module=='amneziawg')
   assert (line in client.read_text())==(module=='amneziawg')
  assert result.stdout==client.read_text()
print('PASS synthetic actual server/export functions: shared AWG parameters, standard WG exclusion, invalid input refusal')
