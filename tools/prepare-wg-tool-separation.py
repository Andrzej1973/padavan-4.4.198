#!/usr/bin/env python3
"""Keep standard WireGuard tools alongside the AmneziaWG wg compatibility alias."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
a=p.parse_args();path=a.source/'trunk/user/wireguard-tools/Makefile'
s=path.read_text();anchor='\t$(ROMFSINST) -p +x $(THISDIR)/$(SRC_NAME)/src/wg /usr/bin/wg\n'
if s.count(anchor)!=1 or '/usr/bin/wg-standard' in s:raise SystemExit('WireGuard tools install anchor changed')
s=s.replace(anchor,anchor+'\t$(ROMFSINST) -p +x $(THISDIR)/$(SRC_NAME)/src/wg /usr/bin/wg-standard\n')
path.write_text(s,encoding='utf-8',newline='\n')
print('Preserved standard wg as wg-standard; existing wg/awg compatibility aliases unchanged')
