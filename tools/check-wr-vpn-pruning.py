#!/usr/bin/env python3
"""Check prepared WR legacy VPN exclusions and execute generated JS guards.

Uses synthetic DOM fields; does not establish browser, target or device behavior.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
a=p.parse_args();root=a.source/'trunk/user';js=['const assert=require("assert");']
for page,field,allowed,legacy in [
 ('vpncli.asp','vpnc_type',['3'],['0','1','2']),
 ('vpnsrv.asp','vpns_type',['3'],['0','1','2']),
 ('Advanced_WAN_Content.asp','wan_proto',['static','dhcp','pppoe'],['pptp','l2tp'])]:
 text=(root/'www/n56u_ribbon_fixed'/page).read_text()
 selected=re.search(r'<select\b[^>]*name="'+field+r'"[^>]*>(.*?)</select>',text,re.S)
 assert selected,page+' select missing'
 assert re.findall(r'<option value="([^"]+)"',selected.group(1))==allowed,page+' protocol options changed'
 initial=re.search(r'function initial\(\)\{(.*?selectedIndex = -1;)',text,re.S)
 assert initial,page+' stale type guard missing'
 for saved in legacy+allowed:
  code=re.sub(r'<%.*?%>',saved,initial.group(1),flags=re.S)
  js.append('(()=>{const document={form:{'+field+':{selectedIndex:2}}};'+code+
   ';assert.strictEqual(document.form.'+field+'.selectedIndex,'+str(-1 if saved in legacy else 2)+');})();')
 if field!='wan_proto':
  role=field[:-5];protocol=role+'_wg_protocol'
  control=re.search(r'<select\b[^>]*name="'+protocol+r'"[^>]*>(.*?)</select>',text,re.S)
  assert control and re.findall(r'<option value="([^"]*)"',control.group(1))==['','wireguard','amneziawg']
  event='VPNCLI' if role=='vpnc' else 'VPNSVR'
  assert '{"'+protocol+'", "", NULL, EVM_RESTART_'+event+'}' in (root/'httpd/variables.c').read_text()
  assert '{ "'+protocol+'", "" }' in (root/'shared/defaults.c').read_text()
 variable='wan_proto' if field=='wan_proto' else 'mode'
 form=text[text.index('function validForm(){'):]
 guard=re.search(r'var '+variable+r' = document.form.'+field+r'.value;(.*?return false;\s*})',form,re.S)
 assert guard,page+' Apply guard missing'
 for value in ['']+legacy+allowed:
  js.append('(()=>{const document={form:{'+field+':{value:'+json.dumps(value)+',focus(){}}}};'
   'const valid=()=>{'+guard.group(0)+';return true;};assert.strictEqual(valid(),'+str(value in allowed).lower()+');})();')
 blocks='\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.S|re.I))
 blocks=re.sub(r'<%.*?%>','0',blocks,flags=re.S);blocks=re.sub(r'<#.*?#>','message',blocks)
 subprocess.run(['node','--check'],input=blocks,text=True,check=True,timeout=15)
subprocess.run(['node'],input='\n'.join(js),text=True,check=True,timeout=15)
make=(root/'Makefile').read_text()
assert not re.search(r'^dir_y.*\+= (poptop|xl2tpd)$',make,re.M)
assert 'SUBDIRS := rp-pppoe\n' in (root/'pppd/pppd/plugins/Makefile').read_text()
for role in ['client','server']:
 assert 'Legacy VPN protocol excluded from this build' in (root/('rc/vpn_'+role+'.c')).read_text()
assert 'PPTP/L2TP excluded; select a supported uplink' in (root/'rc/net_ppp.c').read_text()
for name in ['EN.footer','UK.dict','RU.dict']:
 text=(root/'www/dict'/name).read_text()
 for key in ['WRVPNExplicitType','WRWANExplicitType']:
  assert len(re.findall(r'^'+key+r'=.+$',text,re.M))==1
print('PASS prepared VPN package choices, stale-type/Apply guards, JS syntax and EN/UK/RU labels; runtime unverified')
