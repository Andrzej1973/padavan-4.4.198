#!/usr/bin/env python3
"""Remove legacy VPN userspace packages from the WR1200JS source build.

Preserve PPP/PPPoE and shared crypto. Runtime/kernel/UI pruning is separate.
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
pending=[]
for name,replacements in changes.items():
 path=root/name;text=path.read_text()
 for old,new in replacements:
  if text.count(old)!=1:raise SystemExit('VPN pruning anchor changed: '+name)
  text=text.replace(old,new,1)
 pending.append((path,text))
for path,text in pending:path.write_text(text,encoding='utf-8',newline='\n')
print('Excluded poptop/xl2tpd and PPTP/L2TP PPP plugins; retained PPPoE/shared dependencies')
