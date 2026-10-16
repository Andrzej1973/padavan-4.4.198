#!/usr/bin/env python3
"""Port pinned multi-PPPoE helper syntax to the shipped /bin/sh.

Routing/firewall behavior is unchanged and still needs supervised acceptance.
"""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('tree',type=Path);a=p.parse_args()
path=a.tree/'trunk/user/pppoe/detect.sh';text=path.read_text(encoding='utf-8')
for old,new,count in [('#!/bin/bash\n','#!/bin/sh\n',1),
                      ('let count=$i-1','count=$((i-1))',2),
                      ('let last=$i','last=$i',1),('let j=$i-1','j=$((i-1))',1)]:
    if text.count(old)!=count:raise SystemExit('Multi-PPPoE helper anchor changed: '+old)
    text=text.replace(old,new)
path.write_text(text,encoding='utf-8',newline='\n')
print('Prepared multi-PPPoE helper for target sh; routing runtime unverified')
