#!/usr/bin/env python3
"""Compile the actual pinned protocol parsers and test the client import adapter."""
import argparse
import base64
from pathlib import Path
import subprocess

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--wg-source',required=True,type=Path)
p.add_argument('--awg-source',required=True,type=Path)
p.add_argument('--output',required=True,type=Path)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
here=Path(__file__).resolve().parent
roots=[('wireguard',a.wg_source,'3ba6527130c502144e7388b900138bca6260f4e8'),
       ('amneziawg',a.awg_source,'ee0f0a9aa34ff0a0da4b3433b9512781cfe02843')]
# Guard the upstream resolver too: this test cannot make a hostname lookup.
guard=a.output/'resolver-guard.c'
guard.write_text('''#include <netdb.h>
#include <stdlib.h>
#include <string.h>
int __real_getaddrinfo(const char *,const char *,const struct addrinfo *,struct addrinfo **);
int __wrap_getaddrinfo(const char *node,const char *service,const struct addrinfo *hints,struct addrinfo **out){
 struct addrinfo h=*hints;
 if(node && strcmp(node,"127.0.0.1")) abort();
 h.ai_flags |= AI_NUMERICHOST|AI_NUMERICSERV;
 return __real_getaddrinfo(node,service,&h,out);
}
''')
key=base64.b64encode(bytes(range(1,33))).decode()
public=base64.b64encode(bytes(range(33,65))).decode()
base=f'''[Interface]
PrivateKey = {key}
Address = 10.4.0.2/32, fd00::2/128
DNS = 1.1.1.1, fd00::53, search.example
MTU = 1420
[Peer]
PublicKey = {public}
Endpoint = never-query-this.invalid:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
'''
awg=base.replace('[Peer]','Jc = 4\nJmin = 16\nJmax = 64\nS1 = 10\nS2 = 20\nH1 = 1\nH2 = 2\nH3 = 3\nH4 = 4\n[Peer]')
for protocol,root,commit in roots:
 actual=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
 assert actual==commit,(protocol,actual)
 src=root.resolve()/'src';prefix=a.output/protocol;objects=[]
 flags=['-std=gnu99','-D_GNU_SOURCE','-Wall','-Wextra','-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(src)]
 units=[src/'config.c',src/'encoding.c',here/'validate-client.c',guard]
 if protocol=='amneziawg':units.append(src/'type.c')
 for index,unit in enumerate(units):
  obj=Path(str(prefix)+'-'+str(index)+'.o');objects.append(str(obj))
  subprocess.run(['gcc',*flags,*(['-Werror'] if unit in (here/'validate-client.c',guard) else []),'-c',str(unit),'-o',str(obj)],check=True)
 subprocess.run(['gcc','-fsanitize=address,undefined',*objects,'-Wl,--wrap=getaddrinfo','-o',str(prefix)],check=True)
 def run(text,valid):
  result=subprocess.run([str(prefix.resolve())],input=text.encode(),capture_output=True,timeout=10)
  assert result.returncode==(0 if valid else 2),(protocol,valid,result.returncode,result.stdout,result.stderr)
  assert result.stderr==b'',(protocol,'unexpected diagnostic')
  assert result.stdout==(b'valid client configuration; connectivity unverified\n' if valid else b'')
 for valid in [base,base.replace('\n','\r\n'),base.replace('never-query-this.invalid:51820','[2001:db8::1]:51820'), '# Український коментар\n'+base]:run(valid,True)
 run(awg,protocol=='amneziawg')
 for invalid in [
  base.replace(key,'not-a-key'),base.replace(public,'not-a-key'),
  base.replace('[Peer]','PreUp = touch /must-not-run\n[Peer]'),
  base.replace('[Peer]','FwMark = 51820\n[Peer]'),
  base.replace('[Peer]','Table = 51\n[Peer]'),
  base.replace('[Peer]','SaveConfig = true\n[Peer]'),
  base.replace('[Peer]',f'PrivateKey = {key}\n[Peer]'),
  base.replace(f'PublicKey = {public}\n',''),
  base.replace('Address = 10.4.0.2/32, fd00::2/128\n',''),
  base.replace('AllowedIPs = 0.0.0.0/0, ::/0\n',''),
  base.replace('AllowedIPs = 0.0.0.0/0, ::/0','AllowedIPs = 999.1.1.1/24'),
  base.replace('never-query-this.invalid:51820','[bad-ipv6]:51820'),
  base.replace('never-query-this.invalid:51820','host.invalid:65536'),
  base.replace('MTU = 1420','MTU = 0'),
  base.replace('DNS = 1.1.1.1, fd00::53, search.example','DNS = 1.1.1.1/24'),
  base.replace('Address = 10.4.0.2/32, fd00::2/128','Address = 10.4.0.2/33'),
  base+'\0',base+'x'*16385,
  base+f'[Peer]\nPublicKey = {public}\nAllowedIPs = 10.2.0.0/16\n',
 ]:run(invalid,False)
 print('PASS '+protocol+' pinned native parser/client adapter: quick fields, keys, protocol distinction, hooks/policy rejection, no DNS or secret output; not target/runtime proof')
