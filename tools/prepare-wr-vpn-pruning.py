#!/usr/bin/env python3
"""Remove legacy VPN userspace packages from the WR1200JS source build.

Preserve PPP/PPPoE and shared crypto. Legacy start requests are rejected; further kernel/UI pruning is separate.
"""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
a=p.parse_args();root=a.source/'trunk/user'
changes={
 'Makefile': [('dir_y\t\t\t\t\t\t+= poptop\n',''),
              ('dir_y\t\t\t\t\t\t+= xl2tpd\n','')],
 'pppd/pppd/plugins/Makefile': [('SUBDIRS := rp-pppoe pppol2tp pptp','SUBDIRS := rp-pppoe')],
 'pppd/Makefile': [
 ('\t$(ROMFSINST) -d pppd/plugins/pppol2tp/pppol2tp.so /usr/lib/pppd/pppol2tp.so\n',''),
 ('\t$(ROMFSINST) -d pppd/plugins/pptp/pptp.so /usr/lib/pppd/pptp.so\n','')],
}
# Refuse stale legacy requests before side effects; retain saved NVRAM values.
for role,result in [('vpnc','1'),('vpns','0')]:
 old='\tif (nvram_invmatch("'+role+'_enable", "1") || get_ap_mode())\n\t\treturn '+result+';'
 guard='\n\n\tif (nvram_get_int("'+role+'_type") != 3) {\n'
 guard+='\t\tlogmessage('+role.upper()+'_LOG_NAME, "Legacy VPN protocol excluded from this build");\n'
 guard+='\t\treturn 1;\n\t}'
 changes['rc/vpn_'+('client' if role=='vpnc' else 'server')+'.c']=[(old,old+guard)]
changes['rc/vpn_server.c'].append(
 ('reapply_vpn_server(void)\n{\n\tint i_type;',
  'reapply_vpn_server(void)\n{\n\tint i_type;\n'
  '\tif (nvram_get_int("vpns_type") != 3) return;'))
changes['rc/net_ppp.c']=[
 ('\tif (wan_proto == IPV4_WAN_PROTO_PPTP) {',
  '\tif (wan_proto == IPV4_WAN_PROTO_PPTP || wan_proto == IPV4_WAN_PROTO_L2TP) {\n'
  '\t\tlogmessage("WAN", "PPTP/L2TP excluded; select a supported uplink");\n'
  '\t\treturn -1;\n\t}\n\n\tif (wan_proto == IPV4_WAN_PROTO_PPTP) {')]
pending=[]
for name,replacements in changes.items():
 path=root/name;text=path.read_text()
 for old,new in replacements:
  if text.count(old)!=1:raise SystemExit('VPN pruning anchor changed: '+name)
  text=text.replace(old,new,1)
 pending.append((path,text))
for path,text in pending:path.write_text(text,encoding='utf-8',newline='\n')
print('Excluded poptop/xl2tpd and PPTP/L2TP PPP plugins; retained PPPoE/shared dependencies')
