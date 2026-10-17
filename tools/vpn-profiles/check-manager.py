#!/usr/bin/env python3
"""Exercise profile CLI + real pinned validators + real private store files."""
import argparse
import ast
import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--wg-validator',required=True,type=Path)
p.add_argument('--awg-validator',required=True,type=Path)
p.add_argument('--output',required=True,type=Path)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
here=Path(__file__).resolve().parent
key=base64.b64encode(bytes(range(1,33))).decode()
public=base64.b64encode(bytes(range(33,65))).decode()
wg=f'[Interface]\nPrivateKey = {key}\nAddress = 10.8.0.2/32\n[Peer]\nPublicKey = {public}\nEndpoint = test.invalid:51820\nAllowedIPs = 0.0.0.0/0\n'
awg=wg.replace('[Peer]','Jc = 4\nJmin = 16\nJmax = 64\n[Peer]')
env=dict(os.environ,ASAN_OPTIONS='detect_leaks=1:exitcode=98',UBSAN_OPTIONS='halt_on_error=1:exitcode=97')
with tempfile.TemporaryDirectory(prefix='wrvpn-manager-') as temporary:
 root=Path(temporary);store=root/'store';exe=root/'profilectl'
 guard=root/'fd-guard.c'
 guard.write_text('''#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
int main(void){int fd;for(fd=3;fd<4096;fd++){errno=0;if(fcntl(fd,F_GETFD)!=-1 || errno!=EBADF)return 99;}execl(REAL,REAL,(char *)0);return 127;}
''')
 validators={}
 for role,real in [('wg',a.wg_validator),('awg',a.awg_validator)]:
  output=root/('validate-'+role);validators[role]=output
  subprocess.run(['gcc','-std=gnu99','-Wall','-Wextra','-Werror','-DREAL='+json.dumps(str(real.resolve())),str(guard),'-o',str(output)],check=True)
 subprocess.run(['gcc','-std=gnu99','-Wall','-Wextra','-Werror','-g','-fsanitize=address,undefined',
  '-DWR_VPN_STORE_ROOT='+json.dumps(str(store)),
  '-DWR_VPN_RUNTIME_ROOT='+json.dumps(str(root/'run')),
  '-DWR_VPN_VALIDATE_WG='+json.dumps(str(validators['wg'])),
  '-DWR_VPN_VALIDATE_AWG='+json.dumps(str(validators['awg'])),
  '-DWR_VPN_VALIDATE_TIMEOUT_MS=1000',
  str(here/'profilectl.c'),str(here/'validate-process.c'),str(here/'store.c'),str(here/'link-observation.c'),
  str(here/'runtime-state.c'),str(here/'config-transaction.c'),str(here/'config-apply.c'),str(here/'config-plan.c'),
  str(here/'plan-report.c'),str(here/'endpoint-pin.c'),
  str(here/'addr-apply.c'),str(here/'route-apply.c'),str(here/'profile-apply.c'),str(here/'dns-apply.c'),
  str(here/'link-actions.c'),str(here/'link-lifecycle.c'),
  '-o',str(exe)],check=True)
 def run(args,data='',expected=0,fd=None):
  r=subprocess.run([str(exe),*args],input=data.encode(),capture_output=True,timeout=5,env=env,pass_fds=(() if fd is None else (fd,)))
  assert r.returncode==expected,(args,r.returncode,r.stdout,r.stderr)
  assert not r.stderr,(args,r.stderr)
  return r.stdout.decode()
 with (root/'inherited-private-fd').open('w+') as extra:
  assert run(['create','1','amneziawg'],awg,fd=extra.fileno())=='saved\t1\t1\n'
  assert run(['create','2','wireguard'],wg,fd=extra.fileno())=='saved\t2\t1\n'
 assert run(['export','1'])==awg
 assert run(['export','2'])==wg
 before={id:(store/id).read_bytes() for id in ('1','2')}
 for args,data,code in [
  (['create','2','wireguard'],wg,5),(['create','3','wireguard'],awg,2),
  (['create','3','wireguard'],wg.replace(key,'invalid'),2),
   (['create','../../1','wireguard'],wg,2),(['create','3','invalid'],wg,2),
   (['frobnicate','1'], '',2),(['export','999'],'',5),
 ]: assert not run(args,data,code)
 assert set(run(['list']).splitlines())=={'1\tAWG1\t1','2\tWG2\t1'}
 for id in ('1','2'):
  observed=json.loads(run(['observe',id]))
  assert observed=={'id':int(id),'interface_state':'absent','ownership':'unverified','up':None},observed
 assert key not in run(['list']) and 'test.invalid' not in run(['list'])
 assert not (store/'3').exists()
 assert all((store/id).read_bytes()==data for id,data in before.items())
 outside=root/'outside';outside.write_text('unchanged')
 (store/'3').symlink_to(outside)
 assert not run(['create','3','wireguard'],wg,3)
 assert outside.read_text()=='unchanged';(store/'3').unlink()
 (store/'3').write_bytes(b'corrupt');(store/'3').chmod(0o600)
 assert not run(['export','3'],expected=3)
 run(['list'],expected=3);(store/'3').unlink()
 # Editing is a distinct action and bumps the revision; invalid input changes nothing.
 edited=wg.replace('10.8.0.2/32','10.8.0.9/32')
 assert run(['edit','2'],edited)=='saved\t2\t2\n'
 assert run(['export','2'])==edited
 assert not run(['edit','2'],wg.replace(key,'invalid'),2)
 assert run(['export','2'])==edited
 assert run(['edit','999'],wg,5)==''
 before['2']=(store/'2').read_bytes()
 # Configuration rendering uses those same fixed native validation helpers.
 plan_exe=root/'config-plan'
 subprocess.run(['gcc','-std=gnu99','-Wall','-Wextra','-Werror','-g','-fsanitize=address,undefined',
  '-DWR_VPN_VALIDATE_WG='+json.dumps(str(validators['wg'])),
  '-DWR_VPN_VALIDATE_AWG='+json.dumps(str(validators['awg'])),
  str(here/'check-config-plan.c'),str(here/'config-plan.c'),str(here/'validate-process.c'),'-o',str(plan_exe)],check=True)
 def render(protocol,data,expected=0):
  r=subprocess.run([str(plan_exe),protocol],input=data.encode(),capture_output=True,timeout=10,env=env)
  assert r.returncode==expected,(protocol,r.returncode,r.stderr)
  assert not r.stderr
  assert key.encode() not in r.stdout and public.encode() not in r.stdout
  return json.loads(r.stdout) if expected==0 else None
 for protocol,data in [('wireguard',wg),('amneziawg',awg)]:
  assert render(protocol,data)=={'mtu':0,'hostname_endpoints':True,'dns_present':False}
  numeric=data.replace('test.invalid:51820','203.0.113.7:51820')
  numeric=numeric.replace('[Peer]','DNS = 1.1.1.1, search.example\nMTU = 1380\n[Peer]')
  assert render(protocol,numeric)=={'mtu':1380,'hostname_endpoints':False,'dns_present':True}
  assert render(protocol,numeric.replace('203.0.113.7:51820','[2001:db8::7]:51820'))['hostname_endpoints'] is False
  assert render(protocol,numeric.replace('\n','\r\n'))['mtu']==1380
  render(protocol,data.replace('[Peer]','PreUp = must-not-run\n[Peer]'),2)
  render(protocol,data.replace('[Peer]','FwMark = 51\n[Peer]'),2)
  render(protocol,data.replace(key,'invalid'),2)
 print('PASS config plan: real native validation, separate quick fields, profile-owned mark, endpoint resolution flag, no DNS/IPC/network actions or key output')
 # Exercise the actual HTTP create handler against this real manager, pinned
 # native validators and private store. Never call a network lifecycle action.
 http_tree=ast.parse((here/'check-http-export.py').read_text())
 http_prefix=next(ast.literal_eval(n.value) for n in http_tree.body if isinstance(n,ast.Assign)
  and any(isinstance(t,ast.Name) and t.id=='PREFIX' for t in n.targets))
 http_source=root/'http-real-create.c';http_exe=root/'http-real-create'
 runtime_before={str(f.relative_to(root/'run')):f.read_bytes() for f in (root/'run').rglob('*') if f.is_file()}
 http_source.write_text(http_prefix+'\n#include "vpn-profiles.inc"\n#include "vpn-profiles-action.inc"\n#include "vpn-profiles-create.inc"\n'+r'''
static void submit(const char *id,const char *protocol,const char *config,int success)
{
 FILE *input=tmpfile();char body[17000];int size;assert(input);
 size=snprintf(body,sizeof(body),"%s\n%s\n%s\n%s",wr_vpn_csrf,id,protocol,config);
 assert(size>0 && size<(int)sizeof(body));
 assert(fwrite(body,1,(size_t)size,input)==(size_t)size);rewind(input);
 wr_vpn_create_input("",input,size,NULL);fclose(input);wr_vpn_create_output("",NULL);
 assert(strstr(reply,success?"\"saved\":true,\"started\":false":"create_unconfirmed"));
 assert(!wr_vpn_create_size);
}
int main(void)
{
 safe=post=1;strcpy(wr_vpn_csrf,"0123456789abcdef0123456789abcdef");
''' + 'const char *wg='+json.dumps(wg)+';\nconst char *awg='+json.dumps(awg)+';\n'+r'''
 submit("10","wireguard",wg,1);
 submit("11","amneziawg",awg,1);
 submit("10","wireguard",awg,0); /* Existing ID cannot be replaced. */
 submit("12","wireguard",awg,0); /* Native WG rejects AWG-only fields. */
 submit("12","wireguard","invalid configuration\n",0);
 return 0;
}
''')
 subprocess.run(['gcc','-std=gnu99','-Wall','-Wextra','-Werror','-Wno-unused-function',
  '-fsanitize=address,undefined','-I'+str(here/'web'),
  '-DWR_VPN_PROFILE_BIN='+json.dumps(str(exe)),str(http_source),'-o',str(http_exe)],check=True)
 http_result=subprocess.run([str(http_exe)],capture_output=True,timeout=20,env=env)
 assert http_result.returncode==0 and not http_result.stdout and not http_result.stderr,(http_result.returncode,http_result.stderr)
 assert run(['export','10'])==wg and run(['export','11'])==awg
 assert not (store/'12').exists()
 assert all((store/id).read_bytes()==data for id,data in before.items())
 assert {str(f.relative_to(root/'run')):f.read_bytes() for f in (root/'run').rglob('*') if f.is_file()}==runtime_before
 print('PASS real HTTP create to manager/native validators/store: independent WG/AWG records, exact exports, duplicate/invalid refusal, existing records preserved; no activation')
 # Fixed validator path failure must not save or expose a profile.
 validators['wg'].unlink()
 assert not run(['create','3','wireguard'],wg,3)
 validators['wg'].write_text('#!/bin/sh\nexit 7\n');validators['wg'].chmod(0o700)
 assert not run(['create','3','wireguard'],wg,3)
 validators['wg'].write_text('#!/bin/sh\nexec /bin/sleep 10\n')
 began=time.monotonic();assert not run(['create','3','wireguard'],wg,3)
 assert time.monotonic()-began<4
 assert not (store/'3').exists()
 assert all((store/id).read_bytes()==data for id,data in before.items())
 assert run(['export','1'])==awg  # AWG remains independent of failed WG actions.
 # Stop and delete are distinct: an idle profile becomes a tombstone.
 assert run(['delete','1'])=='deleted\t1\t2\n'
 assert run(['export','1'],expected=5)==''
 assert all(line.split('\t',1)[0]!='1' for line in run(['list']).splitlines())
 assert (store/'1').exists()
 assert run(['delete','1'],expected=5)==''
 print('PASS profile manager integration: native validation before isolated create/export/edit, private metadata, FD closure, invalid/failed/timed-out validator, AWG record preservation, distinct stop/delete tombstone; no network lifecycle')
