#!/usr/bin/env python3
"""Enable reviewed WR1200JS BusyBox applets in the pinned target config."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
a=p.parse_args();path=a.source/'trunk/configs/boards/busybox.config';lines=path.read_text().splitlines()
for key in ['CONFIG_READLINK','CONFIG_FEATURE_READLINK_FOLLOW','CONFIG_OD']:
 matches=[i for i,line in enumerate(lines) if line==key+'=y' or line=='# '+key+' is not set']
 if len(matches)!=1:raise SystemExit('BusyBox reviewed selector anchor changed: '+key)
 lines[matches[0]]=key+'=y'
path.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
print('Enabled BusyBox readlink -f and compact od; CONFIG_DESKTOP unchanged')
